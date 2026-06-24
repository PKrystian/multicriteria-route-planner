from __future__ import annotations

import argparse

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from route_planner.benchmark import run_benchmark


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the algorithm benchmark and write CSVs.")
    parser.add_argument("--pairs", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--min-km", type=float, default=0.5)
    parser.add_argument("--max-km", type=float, default=5.0)
    args = parser.parse_args()

    print(f"Running benchmark: pairs={args.pairs} seed={args.seed} "
          f"distance {args.min_km}-{args.max_km} km")
    paths = run_benchmark(
        n_pairs=args.pairs, seed=args.seed, min_km=args.min_km, max_km=args.max_km
    )
    print("Wrote:")
    for name, path in paths.items():
        print(f"  {name:8s} {path}")


if __name__ == "__main__":
    main()
