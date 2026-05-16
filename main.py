"""CLI for the MTA distance-based fare analysis.

Examples
--------
    python main.py
    python main.py --rate 0.30 --base 1.75
    python main.py --distance-method network --stations data/All_Stops.csv
    python main.py --no-sensitivity --output mta_final_analysis.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path

from nycfare.pipeline import AnalysisConfig, run_analysis


def parse_args() -> AnalysisConfig:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--od-path",
        type=Path,
        default=Path("data/1M_Stop_Pairings.csv"),
        help="origin-destination CSV (default: data/1M_Stop_Pairings.csv)",
    )
    p.add_argument(
        "--stations-path",
        type=Path,
        default=Path("data/Master_Stations.csv"),
        help="station list CSV. For --distance-method network this must be "
        "Master_Stations.csv (has line + complex_id).",
    )
    p.add_argument("--base", type=float, default=2.00, help="base fare in dollars")
    p.add_argument("--rate", type=float, default=0.24, help="per-mile rate in dollars")
    p.add_argument("--flat-fare", type=float, default=2.90, help="current flat fare to compare against")
    p.add_argument(
        "--annual-ridership",
        type=float,
        default=1_194_866_357,
        help="annual MTA ridership for scaling (default: 2024 actual)",
    )
    p.add_argument(
        "--distance-method",
        choices=["haversine", "network"],
        default="haversine",
    )
    p.add_argument(
        "--output",
        type=Path,
        default=None,
        help="if set, write per-row results to this CSV",
    )
    p.add_argument("--no-sensitivity", action="store_true")
    args = p.parse_args()

    return AnalysisConfig(
        od_path=args.od_path,
        stations_path=args.stations_path,
        base_fare=args.base,
        per_mile_rate=args.rate,
        flat_fare=args.flat_fare,
        annual_ridership=args.annual_ridership,
        distance_method=args.distance_method,
        output_path=args.output,
        run_sensitivity=not args.no_sensitivity,
    )


def main() -> None:
    cfg = parse_args()
    print(
        f"Running analysis: distance={cfg.distance_method}, "
        f"fare=${cfg.base_fare:.2f} + ${cfg.per_mile_rate:.2f}/mi, "
        f"flat=${cfg.flat_fare:.2f}"
    )
    out = run_analysis(cfg)

    print(out.revenue.pretty())
    print(
        f"\nBreakeven vs flat fare: {out.breakeven_mi:.2f} mi "
        f"(trips longer than this pay more by construction)"
    )

    if out.sensitivity is not None:
        print("\nSensitivity to short-trip sampling weight:")
        print(out.sensitivity.to_string(index=False))


if __name__ == "__main__":
    main()
