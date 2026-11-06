"""Reduce only visible cells to a small state, and assign rewards."""


REWARDS = {"move": -0.05, "green": 20.0, "red": -15.0,
           "death": -40.0}
STATE_VERSION = "rays-12bits-v1"


def encode(vision):
    """12 bits: adjacent danger, visible green, adjacent red, per ray.

    A green behind a body segment is not considered directly reachable.
    No coordinates, snake length, direction or hidden apples are used.
    """
    state = 0
    for direction, ray in enumerate(vision):
        if ray[0] in "WS":
            state |= 1 << direction
        for cell in ray:
            if cell in "WS":
                break
            if cell == "G":
                state |= 1 << (direction + 4)
                break
        if ray[0] == "R":
            state |= 1 << (direction + 8)
    return str(state)


def reward(event):
    return REWARDS[event]


def format_vision(vision, action):
    up, left, down, right = vision
    padding = " " * len(left)
    lines = [padding + cell for cell in reversed(up)]
    lines.append(left[::-1] + "H" + right)
    lines.extend(padding + cell for cell in down)
    lines.append("Action: " + action)
    return "\n".join(lines)
