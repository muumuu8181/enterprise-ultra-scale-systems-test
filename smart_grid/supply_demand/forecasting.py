from datetime import datetime
from typing import Dict, Any, Tuple
from smart_grid.core.database import db_instance
from smart_grid.core.utils import get_next_15min_interval

class DemandForecaster:
    def __init__(self, db=None):
        self.db = db or db_instance
        self.base_demand = 1000.0  # MW base load

    def predict(self, current_weather: Dict[str, float]) -> float:
        """
        Predicts demand for the next 15-minute interval based on current weather.

        Args:
            current_weather: Dict containing 'temperature' (C) and 'humidity' (%).

        Returns:
            Predicted demand in MW.
        """
        temp = current_weather.get('temperature', 20.0)
        humidity = current_weather.get('humidity', 50.0)

        # Simplified logic for MVP:
        # Base demand + deviation caused by temperature (Heating/Cooling) + Humidity effect
        # If temp > 20, cooling demand increases. If temp < 20, heating demand increases.
        temp_deviation = abs(temp - 20.0)
        temp_effect = temp_deviation * 50.0

        humidity_effect = (humidity - 50.0) * 2.0

        predicted_demand = self.base_demand + temp_effect + humidity_effect

        # Ensure non-negative
        return round(max(predicted_demand, 0.0), 2)

    def generate_and_save_forecast(self, current_weather: Dict[str, float], current_time: datetime) -> Tuple[float, datetime]:
        """
        Generates a forecast for the next interval and saves it to the database.

        Args:
            current_weather: Weather data.
            current_time: The time at which the forecast is being made.

        Returns:
            Tuple of (predicted_demand, target_time)
        """
        prediction = self.predict(current_weather)
        target_time = get_next_15min_interval(current_time)

        self.db.write_point(
            bucket="energy_data",
            measurement="demand_forecast",
            tags={"region": "main_grid", "model": "mvp_linear"},
            fields={"predicted_mw": prediction},
            time=target_time
        )

        return prediction, target_time
