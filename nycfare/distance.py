"""Distance metrics between origin-destination coordinate pairs.

Two metrics are exposed via ``compute_distance(df, method=...)``:

- ``haversine``: great-circle distance. Fast, vectorized, but ignores the actual
  subway network. Systematically *under*-estimates true travel distance.
- ``network``: shortest-path distance along the actual MTA subway graph.
  Implemented in :mod:`nycfare.network` (graph build + Dijkstra). Trips spanning
  disconnected components fall back to haversine. See ``network_distance``.
"""
from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd

EARTH_RADIUS_MILES = 3958.8

Method = Literal["haversine", "network"]


def haversine(lat1, lon1, lat2, lon2) -> np.ndarray:
    """Great-circle distance in miles. Inputs may be scalars or arrays."""
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * np.arcsin(np.sqrt(a)) * EARTH_RADIUS_MILES


def network_distance(df: pd.DataFrame, stations: pd.DataFrame) -> np.ndarray:
    """Shortest-path distance along the subway network (miles).

    ``stations`` must follow the normalized Master_Stations schema produced by
    :func:`nycfare.data.load_master_stations` (columns ``stop_id, lat, lon,
    line, complex_id``).
    """
    # Local import to avoid pulling networkx unless this path is used.
    from .network import build_graph, network_distance_from_graph

    sg = build_graph(stations)
    return network_distance_from_graph(df, sg)


def compute_distance(
    df: pd.DataFrame,
    method: Method = "haversine",
    stations: pd.DataFrame | None = None,
) -> np.ndarray:
    """Dispatch to the chosen distance metric."""
    if method == "haversine":
        return haversine(
            df["origin_latitude"],
            df["origin_longitude"],
            df["destination_latitude"],
            df["destination_longitude"],
        )
    if method == "network":
        if stations is None:
            raise ValueError("network distance requires a stations DataFrame")
        return network_distance(df, stations)
    raise ValueError(f"unknown distance method: {method}")
