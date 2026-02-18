from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from src.database import get_db
from src.deps import get_current_user_id
from src.services.inventory_service import InventoryService
from src.models.inventory_models import UserInventory, Item, TradeOffer

router = APIRouter()

# Pydantic Schemas
class ItemBase(BaseModel):
    id: int
    name: str
    rarity: int
    type: str
    description: Optional[str] = None
    icon_url: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class InventoryItemResponse(BaseModel):
    item_id: int
    quantity: int
    is_locked: bool
    item: ItemBase
    model_config = ConfigDict(from_attributes=True)

class UseItemRequest(BaseModel):
    item_id: int
    quantity: int = 1

class SellItemRequest(BaseModel):
    item_id: int
    quantity: int = 1
    price: int

class TradeRequest(BaseModel):
    target_user_id: int
    offer: Dict[str, int] # item_id -> quantity
    request: Dict[str, int] # item_id -> quantity

class TradeResponse(BaseModel):
    id: int
    status: str
    from_user_id: int
    to_user_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Endpoints

@router.get("/{user_id}", response_model=List[InventoryItemResponse])
async def get_inventory(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    指定ユーザーのインベントリを取得する
    """
    stmt = select(UserInventory).where(UserInventory.user_id == user_id).options(selectinload(UserInventory.item))
    result = await db.execute(stmt)
    inventories = result.scalars().all()
    return inventories

@router.post("/use")
async def use_item(
    request: UseItemRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    アイテムを使用する
    """
    service = InventoryService(db)
    await service.use_item(user_id, request.item_id, request.quantity)
    await db.commit()
    return {"message": "Item used successfully"}

@router.post("/sell")
async def sell_item(
    request: SellItemRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    アイテムを売却する
    """
    service = InventoryService(db)
    await service.sell_item(user_id, request.item_id, request.quantity, request.price)
    await db.commit()
    return {"message": "Item sold successfully"}

@router.post("/trade", response_model=TradeResponse)
async def create_trade(
    request: TradeRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    トレードオファーを作成する
    """
    service = InventoryService(db)
    trade = await service.create_trade_offer(
        from_user_id=user_id,
        to_user_id=request.target_user_id,
        offer_items=request.offer,
        request_items=request.request
    )
    await db.commit()
    await db.refresh(trade)
    # Convert datetime to str for response if Pydantic doesn't handle automatically?
    # Pydantic v2 handles datetime. But I put `str` type hint.
    # I should change type hint to datetime or let Pydantic handle it.
    # To be safe, I'll remove `created_at` from manual serialization or use default Pydantic behavior.
    return trade
