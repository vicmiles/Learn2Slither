import unittest

from environment import Environment
from interpreter import encode, format_vision


class EnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.board = Environment(seed=42)
        self.board.snake = [(3, 3), (2, 3), (1, 3)]
        self.board.green = {(7, 7), (8, 8)}
        self.board.red = {(9, 9)}

    def test_initial_boards(self):
        for seed in range(100):
            board = Environment(seed=seed)
            self.assertEqual(len(board.snake), 3)
            self.assertEqual(len(set(board.snake)), 3)
            self.assertEqual(len(board.green), 2)
            self.assertEqual(len(board.red), 1)
            occupied = set(board.snake) | board.green | board.red
            self.assertEqual(len(occupied), 6)
            self.assertTrue(all(board.inside(cell) for cell in occupied))
            for first, second in zip(board.snake, board.snake[1:]):
                distance = abs(first[0] - second[0])
                distance += abs(first[1] - second[1])
                self.assertEqual(distance, 1)

    def test_move(self):
        self.assertEqual(self.board.step(3), "move")
        self.assertEqual(self.board.snake, [(4, 3), (3, 3), (2, 3)])
        self.assertEqual(self.board.steps, 1)

    def test_green_grows_and_respawns(self):
        self.board.green = {(4, 3), (8, 8)}
        self.assertEqual(self.board.step(3), "green")
        self.assertEqual(len(self.board.snake), 4)
        self.assertEqual(self.board.snake[-1], (1, 3))
        self.assertEqual(len(self.board.green), 2)
        self.assertFalse(set(self.board.snake) & self.board.green)
        self.assertFalse(self.board.green & self.board.red)

    def test_red_shrinks_and_respawns(self):
        self.board.red = {(4, 3)}
        self.assertEqual(self.board.step(3), "red")
        self.assertEqual(self.board.snake, [(4, 3), (3, 3)])
        self.assertEqual(len(self.board.red), 1)
        self.assertFalse(set(self.board.snake) & self.board.red)

    def test_zero_length(self):
        self.board.snake = [(3, 3)]
        self.board.red = {(4, 3)}
        self.assertEqual(self.board.step(3), "death")
        self.assertEqual(self.board.snake, [])
        self.assertEqual(self.board.reason, "zero length")
        self.assertEqual(self.board.red_eaten, 1)
        self.assertTrue(self.board.done)

    def test_wall(self):
        self.board.snake = [(0, 3), (1, 3), (2, 3)]
        self.assertEqual(self.board.step(1), "death")
        self.assertEqual(self.board.reason, "wall")
        with self.assertRaises(ValueError):
            self.board.step(0)

    def test_body_collision(self):
        self.assertEqual(self.board.step(1), "death")
        self.assertEqual(self.board.reason, "body")

    def test_moving_tail_is_free(self):
        self.board.snake = [(3, 3), (3, 4), (2, 4), (2, 3)]
        self.assertEqual(self.board.step(1), "move")
        self.assertFalse(self.board.done)
        self.assertEqual(len(set(self.board.snake)), 4)

    def test_invalid_actions(self):
        for action in (-1, 4, "UP", None, True, 1.0):
            with self.assertRaises(ValueError):
                self.board.step(action)

    def test_vision(self):
        self.board.snake = [(2, 2), (1, 2), (0, 2)]
        self.board.green = {(2, 0), (4, 2)}
        self.board.red = {(2, 4)}
        self.assertEqual(self.board.vision(), (
            "0GW", "SSW", "0R00000W", "0G00000W"))

    def test_hidden_apple_does_not_change_state(self):
        before = self.board.vision()
        self.board.green = {(1, 1), (2, 2)}
        self.board.red = {(4, 4)}
        self.assertEqual(self.board.vision(), before)
        self.assertEqual(encode(self.board.vision()), encode(before))

    def test_board_filled_does_not_hang(self):
        board = Environment(size=5)
        cells = [(x, y) for y in range(5) for x in range(5)]
        board.snake = [(3, 4)] + [
            c for c in cells if c not in ((3, 4), (4, 4))]
        board.green = {(4, 4)}
        board.red = set()
        self.assertEqual(board.step(3), "green")
        self.assertTrue(board.done)
        self.assertEqual(len(board.snake), 25)

    def test_reset_clears_terminal_state(self):
        self.board.finish("wall")
        self.board.reset()
        self.assertFalse(self.board.done)
        self.assertEqual(self.board.steps, 0)
        self.assertEqual(self.board.reason, "")

    def test_vision_prints_head_and_action(self):
        output = format_vision(("GW", "0W", "RW", "SW"), "UP")
        self.assertEqual(output.splitlines()[2], "W0HSW")
        self.assertIn("Action: UP", output)


if __name__ == "__main__":
    unittest.main()
