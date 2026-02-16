import pytest
from datetime import datetime
from smart_grid.supply_demand.forecasting import DemandForecaster
from smart_grid.core.database import TimeSeriesDB

def test_forecasting_logic():
    forecaster = DemandForecaster()

    # Base case: 20C, 50% humidity -> Base demand (1000)
    weather_base = {'temperature': 20.0, 'humidity': 50.0}
    prediction = forecaster.predict(weather_base)
    assert prediction == 1000.0

    # Case 2: 25C (cooling load) -> +250
    # temp_diff = 5, factor = 50 -> 250
    weather_hot = {'temperature': 25.0, 'humidity': 50.0}
    prediction = forecaster.predict(weather_hot)
    assert prediction == 1250.0

    # Case 3: 15C (heating load) -> +250
    # temp_diff = 5, factor = 50 -> 250
    weather_cold = {'temperature': 15.0, 'humidity': 50.0}
    prediction = forecaster.predict(weather_cold)
    assert prediction == 1250.0

    # Case 4: Humidity effect
    # Humidity 60% -> (60-50)*2 = 20
    weather_humid = {'temperature': 20.0, 'humidity': 60.0}
    prediction = forecaster.predict(weather_humid)
    assert prediction == 1020.0

def test_forecast_integration():
    db = TimeSeriesDB()
    forecaster = DemandForecaster(db=db)

    current_time = datetime(2023, 10, 27, 10, 5, 0)
    weather = {'temperature': 22.0, 'humidity': 55.0}

    # Predict
    # Temp diff = 2 -> 100
    # Hum diff = 5 -> 10
    # Expected = 1110

    pred_val, target_time = forecaster.generate_and_save_forecast(weather, current_time)

    assert pred_val == 1110.0
    assert target_time == datetime(2023, 10, 27, 10, 15, 0)

    # Check DB
    points = db.query_points("energy_data", "demand_forecast", target_time, target_time)
    assert len(points) == 1
    assert points[0]['fields']['predicted_mw'] == 1110.0
