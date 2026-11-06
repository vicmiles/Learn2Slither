import contextlib
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from agent import Agent
from main import main, parse_args, summarize


class BonusTests(unittest.TestCase):
    def test_bonus_goals_use_final_length(self):
        rows = [
            dict(length=34, max_length=36, steps=100, green=32, red=1,
                 reason="body"),
            dict(length=40, max_length=40, steps=200, green=37, red=0,
                 reason="body"),
        ]
        report = summarize(rows, Agent(), parse_args([]))
        self.assertEqual(report["best_final_length"], 40)
        self.assertEqual(report["bonus_final_rates"]["35"], 0.5)
        self.assertEqual(report["bonus_peak_rates"]["35"], 1.0)
        self.assertEqual(report["bonus_final_rates"]["30"], 1.0)

    def test_menu_can_run_twice_and_close(self):
        instances = []
        selections = []

        class FakeLobby:
            def __init__(self, args):
                self.args = args

            def show(self):
                selections.append(True)
                return self.args if len(selections) <= 2 else None

        class FakeDisplay:
            def __init__(self, *args):
                self.closed = False
                self.save_requested = False
                self.return_to_menu = True
                instances.append(self)

            def draw(self, *args):
                pass

            def wait(self):
                return True

            def record(self, row):
                pass

            def results(self, report, rows, allow_menu):
                self.report = report
                self.menu_allowed = allow_menu

            def close(self):
                self.closed = True

        modules = {"menu": SimpleNamespace(Lobby=FakeLobby),
                   "display": SimpleNamespace(Display=FakeDisplay)}
        with patch.dict(sys.modules, modules):
            with contextlib.redirect_stdout(io.StringIO()):
                code = main(["--menu", "--quiet", "-dontlearn",
                             "--max-steps", "2"])
        self.assertEqual(code, 0)
        self.assertEqual(len(instances), 2)
        self.assertTrue(all(instance.closed for instance in instances))
        self.assertTrue(all(instance.menu_allowed for instance in instances))
        self.assertTrue(all(instance.report["sessions"] == 1
                            for instance in instances))

    def test_benchmark_uses_same_model_on_different_sizes(self):
        with tempfile.TemporaryDirectory() as directory:
            model = Path(directory) / "model.json"
            output = Path(directory) / "results"
            Agent(seed=42).save(model)
            before = hashlib.sha256(model.read_bytes()).hexdigest()
            script = Path(__file__).resolve().parents[1] / "benchmark.py"
            subprocess.run([
                sys.executable, str(script), "--model", str(model),
                "--sessions", "2", "--sizes", "5", "12",
                "--output", str(output),
            ], check=True, capture_output=True, text=True)
            report = json.loads((output / "summary.json").read_text())
            self.assertEqual(report["sha256"], before)
            self.assertEqual(hashlib.sha256(model.read_bytes()).hexdigest(),
                             before)
            self.assertEqual([r["size"] for r in report["reports"]], [5, 12])
            self.assertTrue(all(not r["learning"] for r in report["reports"]))


if __name__ == "__main__":
    unittest.main()
