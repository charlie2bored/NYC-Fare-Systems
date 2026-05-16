import numpy as np
import pandas as pd
import pytest

from nycfare.network import (
    all_pairs_distance_matrix,
    build_graph,
    network_distance_from_graph,
    snap_to_stations,
)


def _toy_stations():
    # Two perpendicular lines crossing at station C.
    #   Line "NS":  A — B — C — D — E   (along longitude axis)
    #   Line "EW":  F — G — C — H — I   (along latitude axis)
    # Stations C on both lines share complex_id=99 (transfer).
    return pd.DataFrame(
        [
            {"stop_id": "A", "lat": 40.70, "lon": -74.00, "line": "NS", "complex_id": 1, "borough": "M"},
            {"stop_id": "B", "lat": 40.71, "lon": -74.00, "line": "NS", "complex_id": 2, "borough": "M"},
            {"stop_id": "C1","lat": 40.72, "lon": -74.00, "line": "NS", "complex_id": 99, "borough": "M"},
            {"stop_id": "D", "lat": 40.73, "lon": -74.00, "line": "NS", "complex_id": 3, "borough": "M"},
            {"stop_id": "E", "lat": 40.74, "lon": -74.00, "line": "NS", "complex_id": 4, "borough": "M"},
            {"stop_id": "F", "lat": 40.72, "lon": -74.02, "line": "EW", "complex_id": 5, "borough": "M"},
            {"stop_id": "G", "lat": 40.72, "lon": -74.01, "line": "EW", "complex_id": 6, "borough": "M"},
            {"stop_id": "C2","lat": 40.72, "lon": -74.00, "line": "EW", "complex_id": 99, "borough": "M"},
            {"stop_id": "H", "lat": 40.72, "lon": -73.99, "line": "EW", "complex_id": 7, "borough": "M"},
            {"stop_id": "I", "lat": 40.72, "lon": -73.98, "line": "EW", "complex_id": 8, "borough": "M"},
        ]
    )


def test_build_graph_intra_line_edges():
    st = _toy_stations()
    sg = build_graph(st, k=2, transfer_weight_mi=0.05)

    # NS line: A-B, B-C1, C1-D, D-E must all exist.
    for u, v in [("A", "B"), ("B", "C1"), ("C1", "D"), ("D", "E")]:
        assert sg.graph.has_edge(u, v), f"missing edge {u}-{v}"
        assert sg.graph[u][v]["kind"] == "line"
        assert sg.graph[u][v]["weight"] > 0


def test_build_graph_transfer_edge():
    sg = build_graph(_toy_stations())
    assert sg.graph.has_edge("C1", "C2")
    assert sg.graph["C1"]["C2"]["kind"] == "transfer"
    assert sg.graph["C1"]["C2"]["weight"] == pytest.approx(0.05)


def test_all_pairs_distance_uses_transfer():
    sg = build_graph(_toy_stations())
    mat, idx = all_pairs_distance_matrix(sg)
    # A → I must route via the NS line up to C1, transfer to C2, then EW to I.
    d = mat[idx["A"], idx["I"]]
    # Lower bound: straight Haversine A→I is ~1.4 mi; network must be ≥ that.
    assert d > 1.0
    assert np.isfinite(d)


def test_snap_to_nearest_station():
    sg = build_graph(_toy_stations())
    # A point near station G (40.72, -74.01) should snap to G.
    idxs = snap_to_stations(np.array([40.720]), np.array([-74.0099]), sg)
    snapped_id = sg.stations.iloc[idxs[0]]["stop_id"]
    assert snapped_id == "G"


def test_network_distance_end_to_end():
    sg = build_graph(_toy_stations())
    od = pd.DataFrame(
        {
            "origin_latitude": [40.70, 40.72],   # A, F
            "origin_longitude": [-74.00, -74.02],
            "destination_latitude": [40.74, 40.72],  # E, I
            "destination_longitude": [-74.00, -73.98],
        }
    )
    d = network_distance_from_graph(od, sg)
    assert d.shape == (2,)
    assert (d > 0).all()
    assert np.isfinite(d).all()


def test_bridge_components_connects_nearby_lines():
    # Two short, separate lines whose ends are 0.1mi apart (no shared complex).
    st = pd.DataFrame(
        [
            {"stop_id": "P1", "lat": 40.700, "lon": -74.00, "line": "P", "complex_id": 1, "borough": "M"},
            {"stop_id": "P2", "lat": 40.710, "lon": -74.00, "line": "P", "complex_id": 2, "borough": "M"},
            {"stop_id": "Q1", "lat": 40.712, "lon": -74.00, "line": "Q", "complex_id": 3, "borough": "M"},
            {"stop_id": "Q2", "lat": 40.720, "lon": -74.00, "line": "Q", "complex_id": 4, "borough": "M"},
        ]
    )
    import networkx as nx

    sg_off = build_graph(st, bridge_components=False)
    assert nx.number_connected_components(sg_off.graph) == 2

    sg_on = build_graph(st, bridge_components=True, max_bridge_mi=0.5)
    assert nx.number_connected_components(sg_on.graph) == 1
    assert sg_on.graph.has_edge("P2", "Q1")
    assert sg_on.graph["P2"]["Q1"]["kind"] == "merge"


def test_bridge_components_respects_max_bridge_mi():
    # Same fixture but tiny max_bridge_mi — must stay disconnected.
    st = pd.DataFrame(
        [
            {"stop_id": "P1", "lat": 40.700, "lon": -74.00, "line": "P", "complex_id": 1, "borough": "M"},
            {"stop_id": "P2", "lat": 40.710, "lon": -74.00, "line": "P", "complex_id": 2, "borough": "M"},
            {"stop_id": "Q1", "lat": 40.800, "lon": -74.00, "line": "Q", "complex_id": 3, "borough": "M"},
            {"stop_id": "Q2", "lat": 40.810, "lon": -74.00, "line": "Q", "complex_id": 4, "borough": "M"},
        ]
    )
    import networkx as nx

    sg = build_graph(st, bridge_components=True, max_bridge_mi=0.5)
    assert nx.number_connected_components(sg.graph) == 2


def test_network_distance_zero_for_same_origin_dest():
    sg = build_graph(_toy_stations())
    od = pd.DataFrame(
        {
            "origin_latitude": [40.72],
            "origin_longitude": [-74.00],
            "destination_latitude": [40.72],
            "destination_longitude": [-74.00],
        }
    )
    d = network_distance_from_graph(od, sg)
    assert d[0] == pytest.approx(0.0)
