import numpy as np
from datetime import datetime, time

class TrafficPredictor:
    def __init__(self):
        # Mock historical data or coefficients
        # Time of day factors (0-23 hours). Higher means more traffic.
        self.time_factors = {
            7: 1.5, 8: 1.8, 9: 1.6,  # Morning rush
            17: 1.6, 18: 1.9, 19: 1.7, # Evening rush
        }
        self.base_speed_kmh = 30.0 # Average city speed

    def _haversine(self, lat1, lon1, lat2, lon2):
        R = 6371.0  # Earth radius in km
        phi1, phi2 = np.radians(lat1), np.radians(lat2)
        dphi = np.radians(lat2 - lat1)
        dlambda = np.radians(lon2 - lon1)
        a = np.sin(dphi / 2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
        return R * c

    def predict_travel_time(self, origin: tuple[float, float], destination: tuple[float, float],
                            time_of_day: time, day_of_week: int) -> float:
        """
        Predict travel time in minutes.
        origin, destination: (lat, lon)
        time_of_day: datetime.time object
        day_of_week: 0 (Monday) - 6 (Sunday)
        """
        distance_km = self._haversine(origin[0], origin[1], destination[0], destination[1])

        # Base time
        if distance_km == 0:
            return 0.0

        base_time_hours = distance_km / self.base_speed_kmh

        # Apply congestion factor
        hour = time_of_day.hour
        factor = self.time_factors.get(hour, 1.0)

        # Weekend adjustment (less traffic)
        if day_of_week >= 5:
            factor *= 0.8

        predicted_time_hours = base_time_hours * factor
        return predicted_time_hours * 60 # Return in minutes
