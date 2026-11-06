"""Tabular Q-learning with epsilon-greedy exploration."""

import json
import math
import os
from pathlib import Path
import random
import tempfile

from interpreter import STATE_VERSION


class Agent:
    def __init__(self, seed=None, alpha=0.1, gamma=0.95, epsilon=1.0,
                 epsilon_min=0.03, epsilon_decay=0.9995):
        self.q = {}
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.episodes = 0
        self.updates = 0
        self.random = random.Random(seed)

    def choose(self, state, learn=True):
        if learn and self.random.random() < self.epsilon:
            return self.random.randrange(4)
        values = self.q.get(state, [0.0] * 4)
        best = max(values)
        choices = [i for i, value in enumerate(values) if value == best]
        return self.random.choice(choices)

    def update(self, state, action, value, next_state, done):
        values = self.q.setdefault(state, [0.0] * 4)
        target = value
        if not done:
            target += self.gamma * max(self.q.get(next_state, [0.0] * 4))
        values[action] += self.alpha * (target - values[action])
        self.updates += 1

    def end_episode(self):
        self.episodes += 1
        self.epsilon = max(self.epsilon_min,
                           self.epsilon * self.epsilon_decay)

    def save(self, filename):
        data = {
            "format": 1, "state_version": STATE_VERSION,
            "alpha": self.alpha, "gamma": self.gamma,
            "epsilon": self.epsilon, "epsilon_min": self.epsilon_min,
            "epsilon_decay": self.epsilon_decay,
            "episodes": self.episodes, "updates": self.updates,
            "random_state": self.random.getstate(), "q": self.q,
        }
        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(
                    mode="w", dir=path.parent, delete=False,
                    encoding="utf-8") as stream:
                temporary = stream.name
                json.dump(data, stream, allow_nan=False)
                stream.write("\n")
            os.replace(temporary, path)
        finally:
            if temporary and os.path.exists(temporary):
                os.unlink(temporary)

    @classmethod
    def load(cls, filename):
        with open(filename, encoding="utf-8") as stream:
            data = json.load(stream)
        if not isinstance(data, dict):
            raise ValueError("Model must be a JSON object")
        try:
            if data["format"] != 1 or data["state_version"] != STATE_VERSION:
                raise ValueError("Unsupported model format or state encoding")
            agent = cls()
            for name in ("alpha", "gamma", "epsilon", "epsilon_min",
                         "epsilon_decay"):
                value = data[name]
                if (type(value) not in (int, float)
                        or not math.isfinite(value) or not 0 <= value <= 1):
                    raise ValueError("Invalid model parameter: " + name)
                setattr(agent, name, value)
            for name in ("episodes", "updates"):
                value = data[name]
                if type(value) is not int or value < 0:
                    raise ValueError("Invalid model counter: " + name)
                setattr(agent, name, value)
            if not isinstance(data["q"], dict):
                raise ValueError("Q table must be an object")
            for state, values in data["q"].items():
                if (not state.isdigit() or str(int(state)) != state
                        or not 0 <= int(state) < 4096
                        or not isinstance(values, list) or len(values) != 4
                        or any(type(v) not in (int, float)
                               or not math.isfinite(v) for v in values)):
                    raise ValueError("Invalid Q table entry")
            agent.q = data["q"]
            state = data["random_state"]
            agent.random.setstate((state[0], tuple(state[1]), state[2]))
            return agent
        except (KeyError, TypeError, IndexError, OverflowError) as error:
            raise ValueError("Invalid model file") from error
