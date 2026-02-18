import pytest
from src.services.revenue_service import calculate_proration

def test_upgrade_mid_cycle():
    """
    Test proration logic when upgrading mid-cycle.
    Example:
    - Monthly subscription of $30.
    - Used 15 days out of 30.
    - Expected cost: $15.
    """
    amount = 30.0
    total_days = 30
    days_used = 15

    expected_prorated_amount = 15.0
    result = calculate_proration(amount, total_days, days_used)

    assert result == expected_prorated_amount

def test_upgrade_mid_cycle_leap_year():
    """
    Test proration with 29 days in February (leap year).
    """
    amount = 29.0
    total_days = 29
    days_used = 10

    expected_prorated_amount = 10.0
    result = calculate_proration(amount, total_days, days_used)

    assert result == expected_prorated_amount
