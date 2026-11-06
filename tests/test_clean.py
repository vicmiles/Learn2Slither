from pathlib import Path
import tempfile
import unittest

from clean import clean


class CleanTests(unittest.TestCase):
    def test_clean_preserves_models_results_and_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("__pycache__/main.pyc", "tests/__pycache__/test.pyc",
                         "old.pyc", "old.pyo", "main.py",
                         "models/best.json", "results/report.json",
                         ".venv/lib/__pycache__/package.pyc",
                         ".git/objects/keep.pyc"):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(name)
            clean(root)
            self.assertFalse((root / "__pycache__").exists())
            self.assertFalse((root / "tests/__pycache__").exists())
            self.assertFalse((root / "old.pyc").exists())
            self.assertFalse((root / "old.pyo").exists())
            for name in ("main.py", "models/best.json", "results/report.json",
                         ".venv/lib/__pycache__/package.pyc",
                         ".git/objects/keep.pyc"):
                self.assertEqual((root / name).read_text(), name)

    def test_fclean_removes_environment_and_can_be_repeated(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".venv/bin").mkdir(parents=True)
            (root / ".venv/bin/python").write_text("test")
            (root / "snake").write_text("launcher")
            clean(root, full=True)
            self.assertFalse((root / ".venv").exists())
            self.assertEqual((root / "snake").read_text(), "launcher")
            self.assertEqual(clean(root, full=True), 0)

    def test_symlinks_do_not_delete_external_files(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            root = parent / "project"
            root.mkdir()
            outside = parent / "outside"
            outside.mkdir()
            (outside / "keep.pyc").write_text("keep")
            (root / ".venv").symlink_to(outside, target_is_directory=True)
            (root / "__pycache__").symlink_to(outside,
                                              target_is_directory=True)
            clean(root, full=True)
            self.assertEqual((outside / "keep.pyc").read_text(), "keep")
            self.assertFalse((root / ".venv").is_symlink())
            self.assertFalse((root / "__pycache__").is_symlink())


if __name__ == "__main__":
    unittest.main()
