"""Evaluate one unchanged model on different board sizes and bonus goals."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="models/best.json")
    parser.add_argument("--sessions", type=int, default=200)
    parser.add_argument("--sizes", type=int, nargs="+",
                        default=[5, 10, 15, 20])
    parser.add_argument("--seed", type=int, default=2027)
    parser.add_argument("--output", default="results/bonuses")
    args = parser.parse_args()
    if args.sessions < 1 or any(not 5 <= size <= 40 for size in args.sizes):
        parser.error("sessions must be positive; "
                     "sizes must be between 5 and 40")
    model = Path(args.model).resolve()
    try:
        original = hashlib.sha256(model.read_bytes()).hexdigest()
        output = Path(args.output)
        output.mkdir(parents=True, exist_ok=True)
        reports = []
        for size in args.sizes:
            path = output / f"size-{size}.json"
            subprocess.run([
                sys.executable, str(Path(__file__).with_name("main.py")),
                "-visual", "off", "--quiet", "-dontlearn", "-load", str(model),
                "-sessions", str(args.sessions), "--seed", str(args.seed),
                "--size", str(size), "--report", str(path),
                "--csv", str(output / f"size-{size}.csv"),
            ], check=True, stdout=subprocess.DEVNULL)
            reports.append(json.loads(path.read_text(encoding="utf-8")))
            print(f"{size}x{size}: mean final length "
                  f"{reports[-1]['mean_length']:.2f}, "
                  f"final >=35: {reports[-1]['bonus_final_rates']['35']:.1%}")
        if hashlib.sha256(model.read_bytes()).hexdigest() != original:
            raise ValueError("Model changed during evaluation")
        summary = {"model": args.model, "sha256": original,
                   "model_unchanged": True, "reports": reports}
        (output / "summary.json").write_text(
            json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print("Saved " + str(output / "summary.json"))
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
