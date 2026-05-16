import numpy as np
import pandas as pd
import pytest

from nycfare.distance import compute_distance, haversine, network_distance


def test_haversine_zero_distance():
    assert haversine(40.7, -74.0, 40.7, -74.0) == pytest.approx(0.0, abs=1e-9)


def test_haversine_known_pair():
    # Times Sq (40.7580, -73.9855) → Grand Central (40.7527, -73.9772): ~0.5 mi
    d = haversine(40.7580, -73.9855, 40.7527, -73.9772)
    assert 0.3 < d < 0.7


def test_haversine_vectorized():
    lats1 = np.array([40.7, 40.8])
    lons1 = np.array([-74.0, -74.0])
    lats2 = np.array([40.7, 40.9])
    lons2 = np.array([-74.0, -74.0])
    d = haversine(lats1, lons1, lats2, lons2)
    assert d.shape == (2,)
    assert d[0] == pytest.approx(0.0, abs=1e-9)
    assert d[1] > 0


def test_compute_distance_haversine_dispatch():
    df = pd.DataFrame(
        {
            "origin_latitude": [40.7580],
            "origin_longitude": [-73.9855],
            "destination_latitude": [40.7527],
            "destination_longitude": [-73.9772],
        }
    )
    d = compute_distance(df, method="haversine")
    assert len(d) == 1
    assert 0.3 < d[0] < 0.7


def test_network_distance_requires_stations():
    df = pd.DataFrame(
        {
            "origin_latitude": [40.7],
            "origin_longitude": [-74.0],
            "destination_latitude": [40.7],
            "destination_longitude": [-74.0],
        }
    )
    with pytest.raises(ValueError):
        from nycfare.distance import compute_distance
        compute_distance(df, method="network", stations=None)


def test_unknown_method_raises():
    df = pd.DataFrame({"x": [1]})
    with pytest.raises(ValueError):
        compute_distance(df, method="teleport")  # type: ignore[arg-type]
