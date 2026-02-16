from typing import List, Dict, Any, Optional
from datetime import datetime
import collections

class TimeSeriesDB:
    def __init__(self):
        # Structure: bucket -> measurement -> time -> data
        self._store = collections.defaultdict(
            lambda: collections.defaultdict(dict)
        )

    def write_point(self, bucket: str, measurement: str, tags: Dict[str, str], fields: Dict[str, Any], time: datetime):
        """Simulates writing a data point to InfluxDB."""
        data_point = {
            "tags": tags,
            "fields": fields,
            "time": time
        }
        # In a real DB, time would be the key if unique, but here we simplify
        self._store[bucket][measurement][time] = data_point
        print(f"[DB] Written to {bucket}.{measurement} at {time}: {fields}")

    def query_points(self, bucket: str, measurement: str, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Simulates querying data points from InfluxDB."""
        points = []
        measurements = self._store.get(bucket, {}).get(measurement, {})

        for time, data in measurements.items():
            if start_time <= time <= end_time:
                points.append(data)

        # Sort by time
        points.sort(key=lambda x: x['time'])
        return points

# Singleton instance for simplicity in this MVP
db_instance = TimeSeriesDB()
