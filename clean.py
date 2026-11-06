"""Remove Python cache files and optionally the local virtual environment."""

import argparse
import os
from pathlib import Path
import shutil
import sys


def remove(path):
    if path.is_symlink() or path.is_file():
        path.unlink()
    else:
        shutil.rmtree(path)


def clean(root, full=False):
    root = Path(root)
    skipped = {".venv", ".git", ".agents", ".codex", "models", "results"}
    count = 0
    for folder, directories, files in os.walk(root, topdown=True):
        for name in directories[:]:
            if name in skipped:
                directories.remove(name)
            elif name == "__pycache__":
                remove(Path(folder) / name)
                directories.remove(name)
                count += 1
        for name in files:
            if name.endswith((".pyc", ".pyo")):
                (Path(folder) / name).unlink()
                count += 1
    environment = root / ".venv"
    if full and (environment.exists() or environment.is_symlink()):
        remove(environment)
        count += 1
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full", action="store_true",
                        help="also remove the local .venv directory")
    args = parser.parse_args()
    try:
        count = clean(Path(__file__).resolve().parent, args.full)
        print(f"Removed {count} cache items or environment directories.")
        return 0
    except OSError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
