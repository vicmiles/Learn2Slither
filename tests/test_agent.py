import copy
import json
from pathlib import Path
import tempfile
import unittest

from agent import Agent
from interpreter import encode


class AgentTests(unittest.TestCase):
    def test_bellman_update(self):
        agent = Agent(alpha=0.5, gamma=0.9)
        agent.q["2"] = [2.0, 4.0, 1.0, 0.0]
        agent.update("1", 0, 3.0, "2", False)
        self.assertAlmostEqual(agent.q["1"][0], 3.3)

    def test_terminal_update_does_not_bootstrap(self):
        agent = Agent(alpha=0.5)
        agent.q["2"] = [1000.0] * 4
        agent.update("1", 0, -40.0, "2", True)
        self.assertEqual(agent.q["1"][0], -20.0)

    def test_exploitation_ignores_epsilon(self):
        agent = Agent(epsilon=1.0)
        agent.q["1"] = [0.0, 0.0, 8.0, 0.0]
        for _ in range(100):
            self.assertEqual(agent.choose("1", learn=False), 2)

    def test_unknown_evaluation_state_does_not_change_q_table(self):
        agent = Agent()
        before = copy.deepcopy(agent.q)
        agent.choose("123", learn=False)
        self.assertEqual(agent.q, before)
        self.assertEqual(agent.updates, 0)

    def test_features(self):
        state = int(encode(("W", "0G0W", "RW", "SGW")))
        self.assertEqual(state, 1 | 8 | (1 << 5) | (1 << 10))

    def test_save_load_preserves_learning_and_rng(self):
        original = Agent(seed=8)
        original.update("1", 2, 10.0, "2", False)
        original.end_episode()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model.json"
            original.save(path)
            restored = Agent.load(path)
        self.assertEqual(original.q, restored.q)
        self.assertEqual(original.episodes, restored.episodes)
        self.assertEqual(original.updates, restored.updates)
        self.assertEqual(original.epsilon, restored.epsilon)
        self.assertEqual([original.choose("1") for _ in range(30)],
                         [restored.choose("1") for _ in range(30)])

    def test_invalid_models_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model.json"
            Agent().save(path)
            valid = json.loads(path.read_text())
            invalid = [[], {}, dict(valid, state_version="unknown"),
                       dict(valid, alpha=float("nan")),
                       dict(valid, q={"1": [1.0]}),
                       dict(valid, q={"4096": [0.0] * 4}),
                       dict(valid, episodes=-1)]
            for data in invalid:
                path.write_text(json.dumps(data))
                with self.assertRaises(ValueError):
                    Agent.load(path)


if __name__ == "__main__":
    unittest.main()
