from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import List

from src.models.openbanking_models import Transaction

class AccessToken:
    def __init__(self, access_token: str, request_id: str):
        self.access_token = access_token
        self.request_id = request_id

class PlaidService:
    async def exchange_token(self, public_token: str) -> AccessToken:
        """
        Exchange a public token for an access token.
        Mock implementation.
        """
        # In a real app, this would call Plaid API
        return AccessToken(
            access_token=f"access-sandbox-{public_token}",
            request_id="mock_request_id"
        )

    async def sync_transactions(self, connection_id: int) -> List[Transaction]:
        """
        Fetch transactions from the bank provider.
        Returns a list of Transaction objects.
        Mock implementation.
        """
        # In a real app, this would call Plaid /transactions/sync or /transactions/get
        # Returning mock data
        now = datetime.now(timezone.utc)

        # Mocking 3 transactions
        t1 = Transaction(
            account_id=1, # Mock account ID
            amount=Decimal("50.00"),
            currency="USD",
            merchant="Uber",
            category="Travel",
            date=now - timedelta(days=1),
            description="Uber Ride",
            enriched_category="Transportation"
        )
        t2 = Transaction(
            account_id=1,
            amount=Decimal("12.50"),
            currency="USD",
            merchant="Starbucks",
            category="Food and Drink",
            date=now - timedelta(hours=5),
            description="Coffee",
            enriched_category="Dining"
        )
        t3 = Transaction(
            account_id=2, # Mock another account ID
            amount=Decimal("100.00"),
            currency="USD",
            merchant="Amazon",
            category="Shopping",
            date=now - timedelta(days=2),
            description="Books",
            enriched_category="Retail"
        )

        return [t1, t2, t3]

    async def categorize_transaction(self, transaction: Transaction) -> str:
        """
        Enrich transaction category using AI or heuristics.
        Mock implementation.
        """
        if not transaction.merchant:
            return "General"

        merchant_lower = transaction.merchant.lower()
        if "uber" in merchant_lower:
            return "Transportation"
        elif "starbucks" in merchant_lower:
            return "Dining"
        elif "amazon" in merchant_lower:
            return "Retail"
        else:
            return "General"
