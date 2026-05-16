"""Fare calculation models."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class DistanceFare:
    """Linear distance-based fare: base + rate * miles."""

    base: float = 2.00
    per_mile: float = 0.24

    def __call__(self, miles: np.ndarray) -> np.ndarray:
        return self.base + self.per_mile * miles

    @property
    def breakeven_miles(self) -> float:
        """Trip length at which this model matches a given flat fare.

        Useful for framing winner/loser splits — they're a function of where
        the linear curve crosses the flat line, not an organic finding.
        """
        return float("nan")  # depends on the flat fare; see breakeven() below


def breakeven_miles(distance_fare: DistanceFare, flat_fare: float) -> float:
    """Miles at which ``distance_fare(m) == flat_fare``."""
    if distance_fare.per_mile == 0:
        return float("inf")
    return (flat_fare - distance_fare.base) / distance_fare.per_mile
