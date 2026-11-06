"""Command-line entry point and the train/evaluate loop."""

import argparse
import csv
import json
import math
from pathlib import Path
import sys

from agent import Agent
from environment import ACTIONS, Environment
from interpreter import encode, format_vision, reward


def positive(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return number


def probability(value):
    number = float(value)
    if not math.isfinite(number) or not 0 <= number <= 1:
        raise argparse.ArgumentTypeError("must be between 0 and 1")
    return number


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Snake with tabular Q-learning")
    parser.add_argument("-sessions", "--sessions", type=positive, default=1)
    parser.add_argument("-visual", "--visual", choices=("on", "off"),
                        default="on")
    parser.add_argument("--menu", action="store_true",
                        help="open the lobby and configuration panel")
    parser.add_argument("-save", "--save", metavar="FILE")
    parser.add_argument("-load", "--load", metavar="FILE")
    parser.add_argument("-dontlearn", "--dontlearn", action="store_true")
    parser.add_argument("-step-by-step", "--step-by-step",
                        action="store_true")
    parser.add_argument("--speed", type=positive, default=8)
    parser.add_argument("--size", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--quiet", action="store_true",
                        help="hide vision and individual game results")
    parser.add_argument("--max-steps", type=positive, default=3000,
                        help="truncate games after this many moves "
                        "(default 3000)")
    parser.add_argument("--alpha", type=probability, default=0.1)
    parser.add_argument("--gamma", type=probability, default=0.95)
    parser.add_argument("--epsilon", type=probability, default=1.0)
    parser.add_argument("--epsilon-min", type=probability, default=0.03)
    parser.add_argument("--epsilon-decay", type=probability, default=0.9995)
    parser.add_argument("--csv", metavar="FILE", help="per-game results")
    parser.add_argument("--report", metavar="FILE", help="JSON summary")
    parser.add_argument("--checkpoint-dir", metavar="DIR",
                        help="save after a total of 1, 10 and "
                        "100 training games")
    args = parser.parse_args(argv)
    if not 5 <= args.size <= 40:
        parser.error("--size must be between 5 and 40")
    if args.speed > 120:
        parser.error("--speed must be between 1 and 120")
    if args.step_by_step and args.visual == "off":
        parser.error("--step-by-step requires -visual on")
    if args.menu and args.visual == "off":
        parser.error("--menu requires -visual on")
    if args.epsilon_min > args.epsilon and not args.load:
        parser.error("--epsilon-min cannot exceed --epsilon")
    if args.checkpoint_dir and args.dontlearn:
        parser.error("--checkpoint-dir requires learning")
    return args


def summarize(rows, agent, args):
    count = len(rows)
    result = {
        "sessions": count, "seed": args.seed, "size": args.size,
        "max_steps": args.max_steps, "learning": not args.dontlearn,
        "training_episodes": agent.episodes, "q_states": len(agent.q),
        "epsilon": agent.epsilon,
    }
    if count:
        for key in ("length", "max_length", "steps", "green", "red"):
            result["mean_" + key] = sum(r[key] for r in rows) / count
        result["best_length"] = max(r["max_length"] for r in rows)
        result["best_final_length"] = max(r["length"] for r in rows)
        result["longest_life"] = max(r["steps"] for r in rows)
        result["reached_10_rate"] = sum(
            r["max_length"] >= 10 for r in rows) / count
        result["final_10_rate"] = sum(
            r["length"] >= 10 for r in rows) / count
        result["truncated"] = sum(r["reason"] == "step limit" for r in rows)
        result["bonus_final_rates"] = {
            str(goal): sum(r["length"] >= goal for r in rows) / count
            for goal in (15, 20, 25, 30, 35)
        }
        result["bonus_peak_rates"] = {
            str(goal): sum(r["max_length"] >= goal for r in rows) / count
            for goal in (15, 20, 25, 30, 35)
        }
    return result


def save_requested(visual, agent, args):
    if not visual.save_requested:
        return False
    filename = args.save or "models/checkpoint.json"
    agent.save(filename)
    print("Saved " + filename)
    visual.message = "Saved " + filename
    visual.save_requested = False
    return True


def run(args):
    board = Environment(args.size, args.seed)
    if args.load:
        agent = Agent.load(args.load)
        # Evaluation ties are reproducible and independent of training RNG.
        if args.dontlearn:
            agent.random.seed(args.seed + 1)
        print(f"Loaded {args.load} ({agent.episodes} training games)")
    else:
        agent = Agent(args.seed + 1, args.alpha, args.gamma, args.epsilon,
                      args.epsilon_min, args.epsilon_decay)
    visual = None
    if args.visual == "on":
        from display import Display
        visual = Display(args.size, args.speed, args.step_by_step)
    rows = []
    interrupted = False
    saved = False
    args.return_to_menu = False
    try:
        for episode in range(1, args.sessions + 1):
            if episode > 1:
                board.reset()
            if visual:
                visual.last_action = "-"
            while not board.done and board.steps < args.max_steps:
                vision = board.vision()
                state = encode(vision)
                if visual:
                    visual.q_values = agent.q.get(state, [0.0] * 4)
                    visual.draw(board, episode, agent.epsilon,
                                not args.dontlearn)
                    if not visual.wait():
                        interrupted = True
                        break
                    if save_requested(visual, agent, args):
                        continue
                action = agent.choose(state, not args.dontlearn)
                if not args.quiet:
                    print(format_vision(vision, ACTIONS[action]), flush=True)
                event = board.step(action)
                if not args.dontlearn:
                    agent.update(state, action, reward(event),
                                 encode(board.vision()), board.done)
                if visual:
                    visual.q_values = agent.q.get(
                        encode(board.vision()), [0.0] * 4)
                    visual.draw(board, episode, agent.epsilon,
                                not args.dontlearn, ACTIONS[action])
            if interrupted:
                break
            if not args.dontlearn:
                agent.end_episode()
                if args.checkpoint_dir and agent.episodes in (1, 10, 100):
                    target = Path(args.checkpoint_dir)
                    agent.save(target / f"{agent.episodes}sessions.json")
            row = {
                "episode": episode, "length": len(board.snake),
                "max_length": board.max_length, "steps": board.steps,
                "green": board.green_eaten, "red": board.red_eaten,
                "reason": board.reason or "step limit",
            }
            rows.append(row)
            if not args.quiet:
                print(f"Game {episode}: {row['reason']}, "
                      f"length = {row['length']}, "
                      f"max length = {row['max_length']}, "
                      f"duration = {row['steps']}")
            if visual:
                visual.record(row)
                if not board.done:
                    board.reason = "step limit"
                visual.draw(board, episode, agent.epsilon,
                            not args.dontlearn)
                if episode < args.sessions and not visual.wait():
                    break
                save_requested(visual, agent, args)
        if args.save:
            agent.save(args.save)
            saved = True
            print("Saved " + args.save)
        if visual and rows and not visual.closed:
            report = summarize(rows, agent, args)
            report["interrupted"] = interrupted
            visual.results(report, rows, args.menu)
            args.return_to_menu = visual.return_to_menu
    except KeyboardInterrupt:
        interrupted = True
        print("\nInterrupted; keeping completed games and current learning.")
    finally:
        if visual:
            visual.close()
        if args.save and not saved:
            agent.save(args.save)
            print("Saved " + args.save)

    report = summarize(rows, agent, args)
    report["interrupted"] = interrupted
    print(json.dumps(report, indent=2))
    if args.report:
        target = Path(args.report)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=2) + "\n",
                          encoding="utf-8")
    if args.csv and rows:
        target = Path(args.csv)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    return 130 if interrupted else 0


def main(argv=None):
    args = parse_args(argv)
    try:
        while True:
            if args.menu:
                from menu import Lobby
                selection = Lobby(args).show()
                if selection is None:
                    return 0
                args = selection
            code = run(args)
            if not args.menu or not args.return_to_menu:
                return code
    except KeyboardInterrupt:
        print("\nClosed.")
        return 130
    except (OSError, ValueError, csv.Error, ImportError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
