"""Subway network graph + shortest-path distance.

Graph construction (from Master_Stations.csv):

1. Nodes are stations (``stop_id``).
2. Within each ``line`` value, connect each station to its k nearest same-line
   neighbors by haversine. k=2 is enough for linear corridors and keeps branch
   junctions reachable from both sides.
3. Stations sharing a ``complex_id`` are connected with a small transfer edge
   (default 0.05 mi) to model in-station transfers.

Limitations: this approximates physical track distance, not service patterns
(express vs. local), and can mis-connect at branches that run physically
parallel (e.g., parts of "8th Av - Fulton"). Adequate for fare-distance
modelling; not adequate for travel-time modelling.
"""
from __future__ import annotations

from dataclasses import dataclass

import networkx as nx
import numpy as np
import pandas as pd

from .distance import haversine


@dataclass
class SubwayGraph:
    graph: nx.Graph
    stations: pd.DataFrame  # indexed 0..n-1, columns: stop_id, lat, lon, ...

    @property
    def coords(self) -> np.ndarray:
        return self.stations[["lat", "lon"]].to_numpy()


def _bridge_components(
    g: nx.Graph,
    st: pd.DataFrame,
    max_bridge_mi: float = 0.5,
) -> None:
    """Connect disconnected components by adding the shortest cross-component
    edge under ``max_bridge_mi``.

    The MTA ``complex_id`` only captures named in-station transfers, not
    track-level merges (Pelham→Lexington at 125 St, Nostrand→Eastern Pky at
    Franklin Av, etc.). This adds the missing physical-merge edges.

    Components still disconnected after this (e.g. Staten Island) stay
    disconnected — that's the correct answer.
    """
    id_to_row = st.set_index("stop_id")
    while True:
        comps = list(nx.connected_components(g))
        if len(comps) == 1:
            return
        comps.sort(key=len, reverse=True)
        main = comps[0]
        main_idx = id_to_row.loc[list(main)]
        m_lat = main_idx["lat"].to_numpy()[None, :]
        m_lon = main_idx["lon"].to_numpy()[None, :]
        m_ids = main_idx.index.to_numpy()

        best: tuple[float, str, str] | None = None
        for comp in comps[1:]:
            sub = id_to_row.loc[list(comp)]
            s_lat = sub["lat"].to_numpy()[:, None]
            s_lon = sub["lon"].to_numpy()[:, None]
            d = haversine(s_lat, s_lon, m_lat, m_lon)
            i, j = np.unravel_index(np.argmin(d), d.shape)
            dist = float(d[i, j])
            if dist <= max_bridge_mi and (best is None or dist < best[0]):
                best = (dist, sub.index[i], m_ids[j])
        if best is None:
            return  # remaining components are truly isolated
        dist, u, v = best
        g.add_edge(u, v, weight=dist, kind="merge")


def build_graph(
    stations: pd.DataFrame,
    k: int = 2,
    transfer_weight_mi: float = 0.05,
    bridge_components: bool = True,
    max_bridge_mi: float = 0.5,
) -> SubwayGraph:
    """Build the subway adjacency graph from Master_Stations data."""
    st = stations.reset_index(drop=True).copy()
    g = nx.Graph()
    for _, row in st.iterrows():
        g.add_node(row["stop_id"], lat=row["lat"], lon=row["lon"])

    # Intra-line edges: k-nearest same-line neighbors.
    for line, group in st.groupby("line"):
        ids = group["stop_id"].to_numpy()
        lats = group["lat"].to_numpy()
        lons = group["lon"].to_numpy()
        n = len(ids)
        if n < 2:
            continue
        # pairwise haversine within the line
        lat1 = lats[:, None]
        lon1 = lons[:, None]
        lat2 = lats[None, :]
        lon2 = lons[None, :]
        d = haversine(lat1, lon1, lat2, lon2)
        np.fill_diagonal(d, np.inf)
        kk = min(k, n - 1)
        nearest = np.argpartition(d, kk - 1, axis=1)[:, :kk]
        for i in range(n):
            for j in nearest[i]:
                w = float(d[i, j])
                u, v = ids[i], ids[j]
                if g.has_edge(u, v):
                    if w < g[u][v]["weight"]:
                        g[u][v]["weight"] = w
                else:
                    g.add_edge(u, v, weight=w, kind="line", line=line)

    # Transfer edges within station complexes.
    for cid, group in st.groupby("complex_id"):
        ids = group["stop_id"].to_list()
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                u, v = ids[i], ids[j]
                if not g.has_edge(u, v):
                    g.add_edge(u, v, weight=transfer_weight_mi, kind="transfer")

    if bridge_components:
        _bridge_components(g, st, max_bridge_mi=max_bridge_mi)

    return SubwayGraph(graph=g, stations=st)


def snap_to_stations(
    lats: np.ndarray,
    lons: np.ndarray,
    sg: SubwayGraph,
) -> np.ndarray:
    """Return the index (into ``sg.stations``) of the nearest station for each
    input coordinate. Uses brute-force haversine — fast enough for ~500
    stations × any practical number of queries.
    """
    s_lats = sg.coords[:, 0][None, :]
    s_lons = sg.coords[:, 1][None, :]
    q_lats = np.asarray(lats)[:, None]
    q_lons = np.asarray(lons)[:, None]
    d = haversine(q_lats, q_lons, s_lats, s_lons)
    return d.argmin(axis=1)


def all_pairs_distance_matrix(sg: SubwayGraph) -> tuple[np.ndarray, dict[str, int]]:
    """Dijkstra all-pairs distance matrix. Returns (matrix, stop_id→index)."""
    ids = sg.stations["stop_id"].to_list()
    idx = {sid: i for i, sid in enumerate(ids)}
    n = len(ids)
    mat = np.full((n, n), np.inf, dtype=float)
    for sid, dists in nx.all_pairs_dijkstra_path_length(sg.graph, weight="weight"):
        i = idx[sid]
        for t, d in dists.items():
            mat[i, idx[t]] = d
    return mat, idx


def network_distance_from_graph(
    df: pd.DataFrame,
    sg: SubwayGraph,
    fallback_to_haversine: bool = True,
) -> np.ndarray:
    """Network distance (miles) for each row of ``df`` using OD lat/lon.

    Origin/destination are snapped to the nearest station, then a precomputed
    all-pairs Dijkstra matrix is indexed. OD pairs whose snapped stations live
    in disconnected components (e.g. Manhattan ↔ Staten Island) are reported
    as ``inf`` unless ``fallback_to_haversine`` is True, in which case those
    rows fall back to crow-flies distance.
    """
    mat, idx = all_pairs_distance_matrix(sg)
    o_lat = df["origin_latitude"].to_numpy()
    o_lon = df["origin_longitude"].to_numpy()
    d_lat = df["destination_latitude"].to_numpy()
    d_lon = df["destination_longitude"].to_numpy()

    o = snap_to_stations(o_lat, o_lon, sg)
    d = snap_to_stations(d_lat, d_lon, sg)
    dist = mat[o, d]

    if fallback_to_haversine:
        unreachable = ~np.isfinite(dist)
        n_bad = int(unreachable.sum())
        if n_bad:
            print(
                f"  {n_bad:,} OD pairs span disconnected components; "
                "falling back to haversine for those."
            )
            dist = dist.copy()
            dist[unreachable] = haversine(
                o_lat[unreachable], o_lon[unreachable],
                d_lat[unreachable], d_lon[unreachable],
            )
    return dist
