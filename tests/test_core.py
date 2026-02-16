import pytest
from datetime import datetime
from smart_grid.core.utils import get_current_15min_interval, get_next_15min_interval
from smart_grid.core.database import TimeSeriesDB

def test_utils_time_intervals():
    # Test case 1: 10:05 -> 10:00
    dt1 = datetime(2023, 10, 27, 10, 5, 30)
    assert get_current_15min_interval(dt1) == datetime(2023, 10, 27, 10, 0, 0)

    # Test case 2: 10:14:59 -> 10:00
    dt2 = datetime(2023, 10, 27, 10, 14, 59)
    assert get_current_15min_interval(dt2) == datetime(2023, 10, 27, 10, 0, 0)

    # Test case 3: 10:15 -> 10:15
    dt3 = datetime(2023, 10, 27, 10, 15, 0)
    assert get_current_15min_interval(dt3) == datetime(2023, 10, 27, 10, 15, 0)

    # Test next interval
    assert get_next_15min_interval(dt1) == datetime(2023, 10, 27, 10, 15, 0)

def test_database_write_read():
    db = TimeSeriesDB()
    bucket = "test_bucket"
    measurement = "test_measurement"
    time1 = datetime(2023, 10, 27, 10, 0, 0)
    time2 = datetime(2023, 10, 27, 10, 15, 0)

    db.write_point(bucket, measurement, {"tag": "v1"}, {"val": 100}, time1)
    db.write_point(bucket, measurement, {"tag": "v1"}, {"val": 200}, time2)

    # Query exact range
    points = db.query_points(bucket, measurement, time1, time2)
    assert len(points) == 2
    assert points[0]['fields']['val'] == 100
    assert points[1]['fields']['val'] == 200

    # Query subset
    points_subset = db.query_points(bucket, measurement, time1, time1)
    assert len(points_subset) == 1
    assert points_subset[0]['fields']['val'] == 100
