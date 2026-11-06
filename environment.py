"""The board owns the full game state. The agent never receives this object."""

import random


ACTIONS = ("UP", "LEFT", "DOWN", "RIGHT")
DIRECTIONS = ((0, -1), (-1, 0), (0, 1), (1, 0))


class Environment:
    def __init__(self, size=10, seed=None):
        if not isinstance(size, int) or not 5 <= size <= 40:
            raise ValueError("Board size must be between 5 and 40")
        self.size = size
        self.random = random.Random(seed)
        self.reset()

    def reset(self):
        dx, dy = self.random.choice(DIRECTIONS)
        while True:
            x = self.random.randrange(self.size)
            y = self.random.randrange(self.size)
            snake = [(x - i * dx, y - i * dy) for i in range(3)]
            if all(self.inside(cell) for cell in snake):
                break
        self.snake = snake
        self.green = set()
        self.red = set()
        self.done = False
        self.reason = ""
        self.steps = 0
        self.max_length = 3
        self.green_eaten = 0
        self.red_eaten = 0
        self.spawn(self.green)
        self.spawn(self.green)
        self.spawn(self.red)

    def inside(self, cell):
        x, y = cell
        return 0 <= x < self.size and 0 <= y < self.size

    def spawn(self, apples):
        occupied = set(self.snake) | self.green | self.red
        free = [(x, y) for y in range(self.size)
                for x in range(self.size) if (x, y) not in occupied]
        if free:
            apples.add(self.random.choice(free))

    def step(self, action):
        """Return an event; the interpreter converts it to a reward."""
        if self.done:
            raise ValueError("This game has ended; call reset first")
        if type(action) is not int or action not in range(4):
            raise ValueError("Action must be an integer from 0 to 3")
        self.steps += 1
        x, y = self.snake[0]
        dx, dy = DIRECTIONS[action]
        head = (x + dx, y + dy)
        if not self.inside(head):
            return self.finish("wall")

        change = int(head in self.green) - int(head in self.red)
        length = len(self.snake) + change
        if length == 0:
            self.red.remove(head)
            self.red_eaten += 1
            self.snake = []
            self.spawn(self.red)
            return self.finish("zero length")

        # Cells removed by this move are free to enter, including the tail.
        remaining = self.snake[:length - 1]
        if head in remaining:
            return self.finish("body")
        self.snake = [head] + remaining
        self.max_length = max(self.max_length, length)

        event = "move"
        if change == 1:
            self.green.remove(head)
            self.green_eaten += 1
            event = "green"
        elif change == -1:
            self.red.remove(head)
            self.red_eaten += 1
            event = "red"

        # Refill every missing apple when space becomes available.
        while len(self.green) < 2:
            before = len(self.green)
            self.spawn(self.green)
            if len(self.green) == before:
                break
        if not self.red:
            self.spawn(self.red)
        if length == self.size ** 2:
            self.done = True
            self.reason = "board filled"
        return event

    def finish(self, reason):
        self.done = True
        self.reason = reason
        return "death"

    def vision(self):
        """Four full rays in UP, LEFT, DOWN, RIGHT order, ending at walls."""
        if not self.snake:
            return ("W",) * 4
        body = set(self.snake[1:])
        head_x, head_y = self.snake[0]
        rays = []
        for dx, dy in DIRECTIONS:
            ray = []
            x, y = head_x + dx, head_y + dy
            while self.inside((x, y)):
                cell = (x, y)
                if cell in body:
                    ray.append("S")
                elif cell in self.green:
                    ray.append("G")
                elif cell in self.red:
                    ray.append("R")
                else:
                    ray.append("0")
                x, y = x + dx, y + dy
            ray.append("W")
            rays.append("".join(ray))
        return tuple(rays)
