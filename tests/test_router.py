import pytest
from datetime import time
import networkx as nx
from src.services.router import Router
from src.services.traffic_predictor import TrafficPredictor

def test_router_dijkstra():
    router = Router()
    router.add_edge('A', 'B', 1)
    router.add_edge('B', 'C', 2)
    router.add_edge('A', 'C', 4) # Direct but longer

    path, length = router.dijkstra('A', 'C')
    assert path == ['A', 'B', 'C']
    assert length == 3

def test_router_astar():
    router = Router()
    # Define positions for heuristic
    router.graph.add_node('A', pos=(0, 0))
    router.graph.add_node('B', pos=(1, 0))
    router.graph.add_node('C', pos=(2, 0))

    router.add_edge('A', 'B', 1)
    router.add_edge('B', 'C', 1)

    path, length = router.astar('A', 'C')
    assert path == ['A', 'B', 'C']
    assert length == 2

def test_router_apply_traffic():
    router = Router()
    router.add_edge('A', 'B', 10)

    # Check original weight
    assert router.graph['A']['B']['weight'] == 10

    # Apply 2x traffic
    traffic_data = [{'u': 'A', 'v': 'B', 'factor': 2.0}]
    router.apply_traffic(traffic_data)

    # Check updated weight
    assert router.graph['A']['B']['weight'] == 20

    # Path should reflect updated weight
    path, length = router.dijkstra('A', 'B')
    assert length == 20

def test_router_calculate_eta():
    router = Router()
    router.add_edge('A', 'B', 10) # 10 km

    path = ['A', 'B']
    speed_profile = {('A', 'B'): 60.0} # 60 km/h

    eta = router.calculate_eta(path, speed_profile)
    # 10 km / 60 km/h = 1/6 hours = 10 minutes
    assert abs(eta - 10.0) < 0.01

def test_traffic_predictor():
    predictor = TrafficPredictor()
    origin = (35.0, 139.0)
    dest = (35.1, 139.1) # Roughly 15km apart
    t = time(8, 0) # Rush hour

    time_est = predictor.predict_travel_time(origin, dest, t, 0) # Weekday
    assert time_est > 0

    t_weekend = time(8, 0)
    time_est_weekend = predictor.predict_travel_time(origin, dest, t_weekend, 6) # Sunday
    assert time_est_weekend < time_est # Weekend should be faster
