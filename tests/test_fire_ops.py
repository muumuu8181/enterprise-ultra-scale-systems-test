import pytest
from src.schemas.fire_ops_schemas import IncidentCreate, IncidentType, Priority
from datetime import datetime

def test_incident_schema():
    incident_data = {
        "incident_type": IncidentType.FIRE,
        "priority": Priority.HIGH,
        "location": {"type": "Point", "coordinates": [-122.4194, 37.7749]}
    }
    incident = IncidentCreate(**incident_data)
    assert incident.incident_type == IncidentType.FIRE
    assert incident.priority == Priority.HIGH
    assert incident.location["type"] == "Point"

def test_import_models():
    from src.models.fire_ops_models import Incident, FireStation, Apparatus
    assert Incident is not None
    assert FireStation is not None
    assert Apparatus is not None
