import asyncio
from typing import List
from src.models.legal_models import Clause, RiskLevel

async def extract_clauses(document_id: int) -> List[Clause]:
    """
    Simulates clause extraction from a document.
    """
    await asyncio.sleep(0.5) # Simulate processing time
    # Mock data using SQLAlchemy models
    return [
        Clause(
            clause_type="confidentiality",
            text="The receiving party shall keep all information confidential.",
            is_standard=True,
            risk_level=RiskLevel.LOW
        ),
        Clause(
            clause_type="termination",
            text="Either party may terminate this agreement with 30 days notice.",
            is_standard=False,
            risk_level=RiskLevel.MEDIUM
        ),
        Clause(
            clause_type="liability",
            text="The provider shall not be liable for any damages.",
            is_standard=False,
            risk_level=RiskLevel.HIGH
        )
    ]

async def calculate_risk_score(contract_id: int) -> float:
    """
    Simulates calculating a risk score for a contract.
    """
    await asyncio.sleep(0.3)
    # Mock calculation
    return 75.5

async def suggest_revisions(clause_id: int) -> str:
    """
    Simulates generating a revision suggestion for a clause.
    """
    await asyncio.sleep(0.4)
    return "Consider adding 'mutual' to the confidentiality clause and extending termination notice to 60 days."
