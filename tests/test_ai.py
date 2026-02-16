from hq_system.ai import predict_demand

def test_predict_demand_empty():
    assert predict_demand([]) == 0

def test_predict_demand_basic():
    # Average of 10, 20, 30 is 20
    assert predict_demand([10, 20, 30]) == 20

def test_predict_demand_float():
    # Average of 10, 11 is 10.5 -> 10 (int)
    assert predict_demand([10, 11]) == 10
