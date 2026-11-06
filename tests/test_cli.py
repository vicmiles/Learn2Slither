import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from agent import Agent
from main import main, parse_args


class CliTests(unittest.TestCase):
    def test_subject_flags_and_checkpoint_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            with contextlib.redirect_stdout(io.StringIO()):
                result = main([
                    "-visual", "off", "--quiet", "-sessions", "100",
                    "--max-steps", "30", "--checkpoint-dir", directory,
                    "-save", str(Path(directory) / "last.json"),
                ])
            self.assertEqual(result, 0)
            for count in (1, 10, 100):
                model = Agent.load(Path(directory) / f"{count}sessions.json")
                self.assertEqual(model.episodes, count)

    def test_evaluation_preserves_q_values_and_counters(self):
        with tempfile.TemporaryDirectory() as directory:
            original = Path(directory) / "before.json"
            saved = Path(directory) / "after.json"
            report = Path(directory) / "report.json"
            agent = Agent(seed=42)
            agent.update("0", 0, 1.0, "1", False)
            agent.save(original)
            with contextlib.redirect_stdout(io.StringIO()):
                code = main([
                    "-visual", "off", "--quiet", "-dontlearn",
                    "-load", str(original), "-save", str(saved),
                    "-sessions", "5", "--report", str(report),
                    "--max-steps", "20",
                ])
            self.assertEqual(code, 0)
            after = Agent.load(saved)
            self.assertEqual(agent.q, after.q)
            self.assertEqual(agent.updates, after.updates)
            self.assertEqual(agent.episodes, after.episodes)
            self.assertEqual(agent.epsilon, after.epsilon)
            self.assertEqual(json.loads(report.read_text())["sessions"], 5)

    def test_invalid_arguments(self):
        for argv in (["-sessions", "0"], ["--size", "2"],
                     ["--alpha", "nan"], ["--speed", "121"],
                     ["--menu", "-visual", "off"],
                     ["-step-by-step", "-visual", "off"]):
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    parse_args(argv)
                self.assertEqual(error.exception.code, 2)

    def test_missing_model_is_clean_error(self):
        with contextlib.redirect_stderr(io.StringIO()) as output:
            self.assertEqual(main(["-load", "/missing/model.json"]), 1)
        self.assertIn("Error:", output.getvalue())
        self.assertNotIn("Traceback", output.getvalue())


if __name__ == "__main__":
    unittest.main()
