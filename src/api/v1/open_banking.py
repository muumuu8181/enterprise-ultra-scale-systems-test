import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.services.openbanking_service import OpenBankingService

router = APIRouter(prefix="/openbanking", tags=["open-banking"])
service = OpenBankingService()

# Pydantic Schemas
class ConsentCreate(BaseModel):
    scopes: Dict[str, Any]
    redirect_uri: Optional[str] = None
    client_id: str
    customer_id: str

class ConsentResponse(BaseModel):
    id: uuid.UUID
    status: str
    scopes: Dict[str, Any]
    created_at: datetime
    expires_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# Endpoints
@router.post("/consents", response_model=ConsentResponse, status_code=status.HTTP_201_CREATED)
async def create_consent(
    consent_data: ConsentCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new consent for open banking access.
    """
    ip_address = request.client.host if request.client else "0.0.0.0"
    consent = await service.create_consent(
        db=db,
        client_id=consent_data.client_id,
        customer_id=consent_data.customer_id,
        scopes=consent_data.scopes,
        ip_address=ip_address
    )
    return consent

@router.delete("/consents/{consent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_consent(
    consent_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Revoke an existing consent.
    """
    ip_address = request.client.host if request.client else "0.0.0.0"
    success = await service.revoke_consent(db, consent_id, ip_address=ip_address)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consent not found or already revoked"
        )
    return None

@router.get("/accounts/{consent_id}")
async def get_accounts(
    consent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get accounts associated with the consent.
    """
    consent = await service.validate_consent(db, consent_id)
    if not consent:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired consent"
        )

    # Mock data return
    return [
        {"id": "acc_12345", "type": "CHECKING", "balance": 1000.00, "currency": "USD"},
        {"id": "acc_67890", "type": "SAVINGS", "balance": 5000.50, "currency": "USD"}
    ]

@router.get("/transactions/{consent_id}")
async def get_transactions(
    consent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get transactions associated with the consent.
    """
    consent = await service.validate_consent(db, consent_id)
    if not consent:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired consent"
        )

    # Mock data return
    return [
        {"id": "tx_001", "account_id": "acc_12345", "amount": -50.00, "description": "Grocery Store", "date": "2023-10-26T10:00:00Z"},
        {"id": "tx_002", "account_id": "acc_12345", "amount": -20.00, "description": "Coffee Shop", "date": "2023-10-26T14:30:00Z"}
    ]
