"""Revenue annualization and sensitivity analysis.

The annual revenue figure depends on a scaling factor that extrapolates the
sample OD ridership to the MTA's annual total. That factor assumes the sample
is *representative* of the year. If short trips or off-peak trips are
under-/over-sampled, the revenue delta moves accordingly. ``sensitivity``
quantifies that.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class RevenueResult:
    proposed_total: float
    flat_total: float
    delta: float
    pct_change: float
    scale_factor: float
    winners: int
    losers: int
    neutral: int

    def pretty(self) -> str:
        return (
            "=" * 50
            + "\nFINAL REVENUE PROJECTION\n"
            + "=" * 50
            + f"\nProposed Model Total: ${self.proposed_total:,.2f}"
            + f"\nCurrent Flat Total:   ${self.flat_total:,.2f}"
            + f"\nAnnual Delta:         ${self.delta:,.2f}"
            + f"\nPercentage Change:    {self.pct_change:+.1f}%"
            + f"\nScaling factor:       {self.scale_factor:,.2f}x"
            + "\n"
            + "=" * 50
            + "\nFare Impact Analysis:"
            + f"\nWinners (pay less): {self.winners:,}"
            + f"\nLosers (pay more):  {self.losers:,}"
            + f"\nNeutral (same):     {self.neutral:,}"
        )


def annualize(
    df: pd.DataFrame,
    proposed_fare_col: str,
    flat_fare: float,
    ridership_col: str,
    annual_total_rides: float,
) -> RevenueResult:
    """Scale sample-period revenue to an annual figure.

    The scaling factor is ``annual_total_rides / sum(sample_ridership)``. This
    is only valid if the sample's fare-mix mirrors the annual fare-mix; see
    ``sensitivity`` for a robustness check.
    """
    sample_sum = df[ridership_col].sum()
    if sample_sum <= 0:
        raise ValueError("sample ridership sum must be > 0")
    scale = annual_total_rides / sample_sum

    proposed_total = (df[proposed_fare_col] * df[ridership_col]).sum() * scale
    flat_total = (flat_fare * df[ridership_col]).sum() * scale

    winners = int((df[proposed_fare_col] < flat_fare).sum())
    losers = int((df[proposed_fare_col] > flat_fare).sum())
    neutral = int((df[proposed_fare_col] == flat_fare).sum())

    return RevenueResult(
        proposed_total=proposed_total,
        flat_total=flat_total,
        delta=proposed_total - flat_total,
        pct_change=(proposed_total - flat_total) / flat_total * 100,
        scale_factor=scale,
        winners=winners,
        losers=losers,
        neutral=neutral,
    )


def sensitivity(
    df: pd.DataFrame,
    proposed_fare_col: str,
    flat_fare: float,
    ridership_col: str,
    annual_total_rides: float,
    short_trip_threshold_mi: float = 2.0,
    distance_col: str = "distance_mi",
    weight_grid: tuple[float, ...] = (0.5, 0.75, 1.0, 1.25, 1.5),
) -> pd.DataFrame:
    """Re-weight short trips by each factor in ``weight_grid`` and report the
    revenue delta. Tests how robust the headline number is to under-/over-
    sampling of short trips.
    """
    short = df[distance_col] < short_trip_threshold_mi
    rows = []
    for w in weight_grid:
        weighted = df[ridership_col].where(~short, df[ridership_col] * w)
        sample_sum = weighted.sum()
        scale = annual_total_rides / sample_sum
        proposed = (df[proposed_fare_col] * weighted).sum() * scale
        flat = (flat_fare * weighted).sum() * scale
        rows.append(
            {
                "short_trip_weight": w,
                "proposed_total": proposed,
                "flat_total": flat,
                "delta": proposed - flat,
                "pct_change": (proposed - flat) / flat * 100,
            }
        )
    return pd.DataFrame(rows)
