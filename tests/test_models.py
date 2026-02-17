from src.models.map_models import RoadSegment, MapNode, TrafficFlow, IncidentReport

def test_models_exist():
    assert RoadSegment.__tablename__ == "road_segments"
    assert MapNode.__tablename__ == "map_nodes"
    assert TrafficFlow.__tablename__ == "traffic_flows"
    assert IncidentReport.__tablename__ == "incident_reports"
