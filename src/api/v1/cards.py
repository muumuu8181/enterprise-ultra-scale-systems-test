from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.services.card_service import CardService
from src.models.card_models import CardStatus

router = APIRouter(prefix="/cards", tags=["cards"])

# --- Schemas ---

class CardCreate(BaseModel):
    account_id: int
    card_type: str = Field(..., description="debit, credit, platinum, etc.")

class CardResponse(BaseModel):
    id: int
    account_id: int
    card_number_masked: str
    expiry_date: str
    status: CardStatus
    daily_limit: float
    monthly_limit: float

    model_config = ConfigDict(from_attributes=True)

class LimitUpdate(BaseModel):
    daily_limit: Optional[float] = None
    monthly_limit: Optional[float] = None

class CardIssueResponse(CardResponse):
    pan: str
    cvv: str

class VirtualCardResponse(CardResponse):
    pan: str
    cvv: str

# --- Endpoints ---

@router.post("/issue", response_model=CardIssueResponse, status_code=status.HTTP_201_CREATED)
async def issue_card(request: CardCreate, db: AsyncSession = Depends(get_db)):
    """
    新規カード発行API
    """
    service = CardService(db)
    card, pan, cvv = await service.issue_card(request.account_id, request.card_type)

    # 簡略化のため、CardオブジェクトとPAN/CVVを手動でマージ
    return CardIssueResponse(
        id=card.id,
        account_id=card.account_id,
        card_number_masked=card.card_number_masked,
        expiry_date=card.expiry_date,
        status=card.status,
        daily_limit=card.daily_limit,
        monthly_limit=card.monthly_limit,
        pan=pan,
        cvv=cvv
    )

@router.get("/{card_id}", response_model=CardResponse)
async def get_card(card_id: int, db: AsyncSession = Depends(get_db)):
    """
    カード情報取得API
    """
    service = CardService(db)
    return await service.get_card(card_id)

@router.post("/{card_id}/freeze", response_model=CardResponse)
async def freeze_card(card_id: int, db: AsyncSession = Depends(get_db)):
    """
    カード凍結API
    """
    service = CardService(db)
    return await service.freeze_card(card_id)

@router.post("/{card_id}/unfreeze", response_model=CardResponse)
async def unfreeze_card(card_id: int, db: AsyncSession = Depends(get_db)):
    """
    カード凍結解除API
    """
    service = CardService(db)
    return await service.unfreeze_card(card_id)

@router.put("/{card_id}/limits", response_model=CardResponse)
async def update_limits(card_id: int, limits: LimitUpdate, db: AsyncSession = Depends(get_db)):
    """
    利用限度額更新API
    """
    service = CardService(db)
    return await service.update_limits(card_id, limits.daily_limit, limits.monthly_limit)

@router.post("/{card_id}/virtual", response_model=VirtualCardResponse, status_code=status.HTTP_201_CREATED)
async def issue_virtual_card(card_id: int, db: AsyncSession = Depends(get_db)):
    """
    バーチャルカード発行API
    """
    service = CardService(db)
    card, pan, cvv = await service.issue_virtual_card(card_id)

    return VirtualCardResponse(
        id=card.id,
        account_id=card.account_id,
        card_number_masked=card.card_number_masked,
        expiry_date=card.expiry_date,
        status=card.status,
        daily_limit=card.daily_limit,
        monthly_limit=card.monthly_limit,
        pan=pan,
        cvv=cvv
    )
