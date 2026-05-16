"""Create a small stratified sample of the OD CSV for quick demos / tests.

The sample is stratified by ``origin_borough`` so all five boroughs are
represented even at small sample sizes. Output: ``data/sample_od.csv``.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

SOURCE = Path("data/1M_Stop_Pairings.csv")
TARGET = Path("data/sample_od.csv")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--n", type=int, default=10_000, help="target sample size")
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    if not SOURCE.exists():
        raise SystemExit(
            f"{SOURCE} not found. Run scripts/download_data.py first."
        )

    df = pd.read_csv(SOURCE)
    print(f"Loaded {len(df):,} rows from {SOURCE}")

    if "origin_borough" in df.columns:
        # proportional stratified sample
        frac = args.n / len(df)
        sample = (
            df.groupby("origin_borough", group_keys=False)[df.columns.tolist()]
            .apply(lambda g: g.sample(max(1, int(len(g) * frac)), random_state=args.seed))
            .reset_index(drop=True)
        )
    else:
        sample = df.sample(args.n, random_state=args.seed).reset_index(drop=True)

    sample.to_csv(TARGET, index=False)
    print(f"Wrote {len(sample):,} rows to {TARGET} ({TARGET.stat().st_size/1e6:.2f} MB)")


if __name__ == "__main__":
    main()
