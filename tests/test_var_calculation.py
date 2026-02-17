import pytest
import numpy as np
from src.services.credit_service import CreditService

@pytest.mark.asyncio
async def test_historical_var():
    # Pass None for db as these methods don't require database access
    service = CreditService(None)

    # Create simple data: 0 to 99.
    data = [float(i) for i in range(100)]

    # 95% confidence level means we look at the 5th percentile (index 5)
    # index = int((1 - 0.95) * 100) = 5
    var_95 = service.calculate_historical_var(data, 0.95)
    assert var_95 == 5.0

    # 99% confidence level -> 1st percentile
    # index = int((1 - 0.99) * 100) = 1
    var_99 = service.calculate_historical_var(data, 0.99)
    assert var_99 == 1.0

@pytest.mark.asyncio
async def test_monte_carlo_convergence():
    service = CreditService(None)

    # Theoretical VaR for N(0,1) at 95% is approx 1.645
    np.random.seed(42)
    # Provide sample data that approximates N(0,1) so the service estimates mean~0, std~1
    sample_data = np.random.normal(0, 1, 1000).tolist()

    # Run MC simulation with sufficient iterations
    var = service.calculate_monte_carlo_var(sample_data, 10000, 0.95)

    expected_var = 1.645
    # Check if result is within reasonable bounds (0.1 tolerance)
    assert abs(var - expected_var) < 0.1
