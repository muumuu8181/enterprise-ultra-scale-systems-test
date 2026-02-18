import pytest
from unittest.mock import MagicMock, AsyncMock
from src.services.digital_twin import DigitalTwin
from src.models import Sensor
import datetime
import numpy as np

@pytest.mark.asyncio
async def test_sync_sensor_state():
    mock_db = AsyncMock()
    mock_ts_db = AsyncMock()

    # Mock result for select(Sensor) on db
    mock_result = MagicMock()
    mock_sensor = Sensor(id=1, name="Test Sensor", type="traffic_flow", status="active")
    mock_result.scalar_one_or_none.return_value = mock_sensor
    mock_db.execute.return_value = mock_result

    service = DigitalTwin(mock_db, mock_ts_db)
    reading = await service.sync_sensor_state(1, 10.5)

    assert reading.value == 10.5
    assert reading.sensor_id == 1

    # Check if sensor updated on db
    assert mock_sensor.last_updated is not None
    assert mock_db.add.call_count >= 1

    # Check if reading added to timescale_db
    assert mock_ts_db.add.call_count >= 1

@pytest.mark.asyncio
async def test_predict_anomaly():
    mock_db = AsyncMock()
    mock_ts_db = AsyncMock()

    # Mock active sensors result on db
    mock_sensors_result = MagicMock()
    mock_sensors_result.scalars.return_value.all.return_value = [1]
    mock_db.execute.return_value = mock_sensors_result

    # Mock sensor readings result on timescale_db
    # Values: [14.0, 10.0, 10.0, ...]
    readings = [14.0] + [10.0] * 99

    mock_readings_result = MagicMock()
    mock_readings_result.scalars.return_value.all.return_value = readings
    mock_ts_db.execute.return_value = mock_readings_result

    service = DigitalTwin(mock_db, mock_ts_db)
    anomalies = await service.predict_anomaly()

    assert len(anomalies) == 1
    assert anomalies[0]['sensor_id'] == 1
    assert anomalies[0]['value'] == 14.0
    assert anomalies[0]['z_score'] > 3.0

    # Verify correct DBs were queried
    assert mock_db.execute.called
    assert mock_ts_db.execute.called
