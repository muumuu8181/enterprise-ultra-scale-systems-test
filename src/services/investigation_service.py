from typing import List
from src.models.investigation import FraudCase

class InvestigationService:
    async def auto_link_transactions(self, case_id: int) -> List[str]:
        # Stub implementation
        return ["tx_123", "tx_456"]

    async def calculate_fraud_loss_rate(self, period: str) -> float:
        # Stub implementation
        return 0.05

    async def prioritize_cases(self) -> List[FraudCase]:
        # Stub implementation
        return []
