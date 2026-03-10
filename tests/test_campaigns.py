import pytest
from src.models.campaign_models import VaccinationCampaign
from src.services.appointment_service import book_appointment, calculate_herd_immunity

@pytest.mark.asyncio
async def test_campaign_models():
    campaign = VaccinationCampaign(name="Test Campaign", target_population=100)
    assert campaign.name == "Test Campaign"
    assert campaign.target_population == 100

@pytest.mark.asyncio
async def test_appointment_service_imports():
    assert callable(book_appointment)
    assert callable(calculate_herd_immunity)
