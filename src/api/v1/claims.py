from fastapi import APIRouter, HTTPException, Path, Query, File, UploadFile
from typing import List, Optional
from pydantic import BaseModel

from src.models.claims_models import Claim
from src.services.fraud_detection import score_claim_fraud, extract_document_data, calculate_loss_ratio, FraudAssessment

router = APIRouter()

# Pydantic models
class DocumentResponse(BaseModel):
    document_id: int
    extracted_data: dict

class PayoutRequest(BaseModel):
    amount: float
    currency: str = "USD"
    notes: Optional[str] = None

class PayoutResponse(BaseModel):
    transaction_id: str
    status: str

# Endpoints

@router.get("/analytics/loss-ratio")
async def get_loss_ratio(
    product_type: str = Query(..., alias="product_type"),
    period: str = Query("current_year", alias="period")
):
    ratio = await calculate_loss_ratio(product_type, period)
    return {"product_type": product_type, "period": period, "loss_ratio": ratio}

@router.post("/{claim_id}/documents", response_model=DocumentResponse)
async def upload_document(
    claim_id: int = Path(..., title="The ID of the claim"),
    file: UploadFile = File(...)
):
    # In a real app, save file to Minio here
    file_path = f"s3://claims/{claim_id}/{file.filename}"

    extracted = await extract_document_data(file_path)

    # Save to DB logic would go here

    return {"document_id": 123, "extracted_data": extracted}

@router.get("/{claim_id}/fraud-score", response_model=FraudAssessment)
async def get_fraud_score(
    claim_id: int = Path(..., title="The ID of the claim")
):
    # Mock retrieving claim from DB
    claim = Claim(id=claim_id) # Placeholder for DB fetch

    assessment = await score_claim_fraud(claim)
    return assessment

@router.post("/{claim_id}/payout", response_model=PayoutResponse)
async def process_payout(
    payout_req: PayoutRequest,
    claim_id: int = Path(..., title="The ID of the claim")
):
    # Logic to process payout via payment gateway
    return {"transaction_id": "txn_123456789", "status": "PROCESSED"}
