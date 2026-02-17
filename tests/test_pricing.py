from src.services.dynamic_pricing import DynamicPricingService
import pytest

def test_calculate_surge():
    service = DynamicPricingService()
    assert service.calculate_surge(100, 100) == 1.0  # ratio 1.0 -> 1.0
    assert service.calculate_surge(120, 100) == 1.2  # ratio 1.2 -> 1.2
    assert service.calculate_surge(151, 100) == 1.5  # ratio 1.51 > 1.5 -> 1.5
    assert service.calculate_surge(50, 100) == 1.0   # ratio 0.5 <= 1.0 -> 1.0
    assert service.calculate_surge(100, 0) == 2.0    # supply 0 -> 2.0

def test_seasonal_adjustment():
    service = DynamicPricingService()
    assert service.seasonal_adjustment("high") == 1.5
    assert service.seasonal_adjustment("peak") == 2.0
    assert service.seasonal_adjustment("low") == 0.8
    assert service.seasonal_adjustment("standard") == 1.0
    assert service.seasonal_adjustment("unknown") == 1.0

def test_discount_long_term():
    service = DynamicPricingService()
    assert service.discount_long_term(7) == 0.10
    assert service.discount_long_term(10) == 0.10
    assert service.discount_long_term(6) == 0.0

def test_calculate_excess_mileage():
    service = DynamicPricingService()
    assert service.calculate_excess_mileage(100, 50) == 25.0 # (100-50)*0.5 = 25
    assert service.calculate_excess_mileage(50, 100) == 0.0
