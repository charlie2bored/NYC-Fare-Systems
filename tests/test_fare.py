import numpy as np
import pandas as pd
import pytest

from nycfare.fare import DistanceFare, breakeven_miles
from nycfare.revenue import annualize, sensitivity


def test_distance_fare_basic():
    f = DistanceFare(base=2.0, per_mile=0.24)
    assert f(np.array([0.0, 1.0, 10.0])).tolist() == pytest.approx([2.0, 2.24, 4.4])


def test_breakeven_default_model():
    # 2.0 + 0.24 * m == 2.90  =>  m == 3.75
    f = DistanceFare(base=2.0, per_mile=0.24)
    assert breakeven_miles(f, 2.90) == pytest.approx(3.75)


def test_breakeven_zero_rate():
    f = DistanceFare(base=2.0, per_mile=0.0)
    assert breakeven_miles(f, 2.90) == float("inf")


def _toy_df():
    # Two trips: 1 mi (under breakeven) and 10 mi (over).
    return pd.DataFrame(
        {
            "distance_mi": [1.0, 10.0],
            "proposed_fare": [2.0 + 0.24 * 1.0, 2.0 + 0.24 * 10.0],
            "estimated_average_ridership": [100.0, 100.0],
        }
    )


def test_annualize_balances():
    df = _toy_df()
    res = annualize(
        df,
        proposed_fare_col="proposed_fare",
        flat_fare=2.90,
        ridership_col="estimated_average_ridership",
        annual_total_rides=2_000_000.0,
    )
    # 200 sample rides → 2M annual → scale = 10_000
    assert res.scale_factor == pytest.approx(10_000.0)
    # flat: 2.90 * 200 * 10_000 = 5.8M
    assert res.flat_total == pytest.approx(5_800_000.0)
    # proposed: (2.24 + 4.40) * 100 * 10_000 = 6.64M
    assert res.proposed_total == pytest.approx(6_640_000.0)
    assert res.winners == 1
    assert res.losers == 1
    assert res.neutral == 0


def test_sensitivity_shape_and_baseline():
    df = _toy_df()
    sens = sensitivity(
        df,
        proposed_fare_col="proposed_fare",
        flat_fare=2.90,
        ridership_col="estimated_average_ridership",
        annual_total_rides=2_000_000.0,
        short_trip_threshold_mi=2.0,
        weight_grid=(0.5, 1.0, 1.5),
    )
    assert list(sens.columns) == [
        "short_trip_weight",
        "proposed_total",
        "flat_total",
        "delta",
        "pct_change",
    ]
    assert len(sens) == 3
    # weight=1.0 row must match annualize()'s baseline delta
    baseline = sens.loc[sens["short_trip_weight"] == 1.0].iloc[0]
    assert baseline["delta"] == pytest.approx(6_640_000.0 - 5_800_000.0)
