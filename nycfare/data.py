"""Data loading and validation for MTA fare analysis."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

OD_REQUIRED_COLS = [
    "origin_latitude",
    "origin_longitude",
    "destination_latitude",
    "destination_longitude",
    "estimated_average_ridership",
]


def load_od_pairs(path: str | Path) -> pd.DataFrame:
    """Load and validate the origin-destination ridership table.

    Drops rows with missing coordinates or non-positive ridership.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"OD file not found at {path}.\n"
            f"  - For a quick run: --od-path data/sample_od.csv (10k stratified rows)\n"
            f"  - For the full dataset: python scripts/download_data.py"
        )
    df = pd.read_csv(path)

    missing = [c for c in OD_REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in {path}: {missing}")

    initial = len(df)
    df = df.dropna(subset=OD_REQUIRED_COLS).copy()
    df["estimated_average_ridership"] = pd.to_numeric(
        df["estimated_average_ridership"], errors="coerce"
    )
    df = df[df["estimated_average_ridership"] > 0]

    print(f"Loaded {len(df):,}/{initial:,} OD pairs from {path}")
    return df.reset_index(drop=True)


def load_stations(path: str | Path) -> pd.DataFrame:
    """Load the station list (All_Stops.csv schema)."""
    path = Path(path)
    df = pd.read_csv(path)
    required = ["stop_id", "stop_lat", "stop_lon"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in {path}: {missing}")
    return df


def load_master_stations(path: str | Path) -> pd.DataFrame:
    """Load Master_Stations.csv and normalize the columns we need.

    Returns a DataFrame with: ``stop_id, lat, lon, line, complex_id, borough``.
    """
    path = Path(path)
    df = pd.read_csv(path)
    required = [
        "gtfs_stop_id",
        "gtfs_latitude",
        "gtfs_longitude",
        "line",
        "complex_id",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in {path}: {missing}")

    out = df.rename(
        columns={
            "gtfs_stop_id": "stop_id",
            "gtfs_latitude": "lat",
            "gtfs_longitude": "lon",
        }
    )[["stop_id", "lat", "lon", "line", "complex_id", "borough"]].copy()
    out = out.dropna(subset=["lat", "lon", "line"]).reset_index(drop=True)
    return out
