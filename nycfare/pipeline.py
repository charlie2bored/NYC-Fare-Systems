"""End-to-end analysis pipeline."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .data import load_master_stations, load_od_pairs
from .distance import Method, compute_distance
from .fare import DistanceFare, breakeven_miles
from .revenue import RevenueResult, annualize, sensitivity


@dataclass
class AnalysisConfig:
    od_path: Path
    stations_path: Path | None = None
    base_fare: float = 2.00
    per_mile_rate: float = 0.24
    flat_fare: float = 2.90
    annual_ridership: float = 1_194_866_357
    distance_method: Method = "haversine"
    output_path: Path | None = None
    run_sensitivity: bool = True


@dataclass
class AnalysisOutput:
    df: pd.DataFrame
    revenue: RevenueResult
    breakeven_mi: float
    sensitivity: pd.DataFrame | None


def run_analysis(cfg: AnalysisConfig) -> AnalysisOutput:
    df = load_od_pairs(cfg.od_path)

    stations: pd.DataFrame | None = None
    if cfg.distance_method == "network":
        if cfg.stations_path is None:
            raise ValueError("network distance requires --stations-path")
        stations = load_master_stations(cfg.stations_path)

    df["distance_mi"] = compute_distance(df, cfg.distance_method, stations)

    fare = DistanceFare(base=cfg.base_fare, per_mile=cfg.per_mile_rate)
    df["proposed_fare"] = fare(df["distance_mi"].to_numpy())

    rev = annualize(
        df,
        proposed_fare_col="proposed_fare",
        flat_fare=cfg.flat_fare,
        ridership_col="estimated_average_ridership",
        annual_total_rides=cfg.annual_ridership,
    )

    be = breakeven_miles(fare, cfg.flat_fare)

    sens_df: pd.DataFrame | None = None
    if cfg.run_sensitivity:
        sens_df = sensitivity(
            df,
            proposed_fare_col="proposed_fare",
            flat_fare=cfg.flat_fare,
            ridership_col="estimated_average_ridership",
            annual_total_rides=cfg.annual_ridership,
        )

    if cfg.output_path:
        df.to_csv(cfg.output_path, index=False)
        print(f"Results saved to: {cfg.output_path}")

    return AnalysisOutput(df=df, revenue=rev, breakeven_mi=be, sensitivity=sens_df)
