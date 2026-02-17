import pytest
from src.services.fhir_service import check_vital_anomaly

def test_low_spo2_alert():
    """
    Test that SpO2 below 90 triggers an anomaly.
    """
    assert check_vital_anomaly("spo2", 88) is True
    assert check_vital_anomaly("spo2", 95) is False

def test_high_glucose_alert():
    """
    Test that Glucose outside 70-140 range triggers an anomaly.
    """
    assert check_vital_anomaly("glucose", 180) is True  # High
    assert check_vital_anomaly("glucose", 60) is True   # Low
    assert check_vital_anomaly("glucose", 100) is False # Normal
