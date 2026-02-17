from typing import Dict, Any
from src.models.insurance_models import UnderwritingDecision

async def calculate_risk_score(applicant_data: Dict[str, Any]) -> float:
    """
    Calculates a risk score between 0.0 (low risk) and 1.0 (high risk).
    """
    age = applicant_data.get("age", 30)
    income = applicant_data.get("income", 50000)
    history_claims = applicant_data.get("history_claims", 0)

    score = 0.1  # Base risk

    # Age factor
    if age < 25:
        score += 0.2
    elif age > 60:
        score += 0.3

    # Income factor (inverse)
    if income < 30000:
        score += 0.2

    # History factor
    if history_claims > 0:
        score += 0.1 * history_claims

    return min(score, 1.0)

async def auto_underwrite(policy_data: Dict[str, Any]) -> UnderwritingDecision:
    """
    Determines the underwriting decision based on policy data.
    """
    applicant_data = policy_data.get("applicant_data", {})
    risk_score = await calculate_risk_score(applicant_data)

    if risk_score > 0.7:
        return UnderwritingDecision.REJECTED
    elif risk_score > 0.4:
        return UnderwritingDecision.MANUAL_REVIEW
    else:
        return UnderwritingDecision.APPROVED
