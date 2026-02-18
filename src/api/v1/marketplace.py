from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, ConfigDict

from src.database import get_db
from src.models.nft_models import NFTToken, VirtualLand, Marketplace, Transaction
from src.services.economy_service import EconomyService

router = APIRouter(prefix="/marketplace", tags=["marketplace"])

# --- Schemas ---

class ListingCreate(BaseModel):
    seller_id: str
    asset_id: int
    price_tokens: float
    listing_type: str = "fixed" # fixed or auction
    duration_days: int = 7

class BidCreate(BaseModel):
    bidder_id: str
    amount: float

class BuyCreate(BaseModel):
    buyer_id: str

class ListingResponse(BaseModel):
    id: int
    seller_id: str
    asset_id: int
    price_tokens: float
    listing_type: str
    expires_at: datetime
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class NFTResponse(BaseModel):
    id: int
    token_id: str
    contract_address: str
    owner_address: str
    metadata_uri: str
    last_price_eth: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)

class VirtualLandResponse(BaseModel):
    id: int
    parcel_x: int
    parcel_y: int
    owner_id: str
    development_status: str
    model_config = ConfigDict(from_attributes=True)

class PortfolioResponse(BaseModel):
    user_id: str
    nfts_count: int
    lands_count: int
    nfts: List[NFTResponse]
    lands: List[VirtualLandResponse]
    model_config = ConfigDict(from_attributes=True)

class AssetMintCreate(BaseModel):
    owner_address: str
    token_id: str
    contract_address: str
    metadata_uri: str
    # If virtual land
    is_land: bool = False
    parcel_x: Optional[int] = None
    parcel_y: Optional[int] = None

class TransactionResponse(BaseModel):
    id: int
    buyer_id: str
    listing_id: int
    amount: float
    timestamp: datetime
    status: str
    model_config = ConfigDict(from_attributes=True)

# --- Dependencies ---

async def get_economy_service(db: AsyncSession = Depends(get_db)) -> EconomyService:
    return EconomyService(db)

# --- Endpoints ---

@router.post("/list", response_model=ListingResponse)
async def create_listing(
    listing: ListingCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    マーケットプレイスに出品を作成する
    """
    expires_at = datetime.utcnow() + timedelta(days=listing.duration_days)
    new_listing = Marketplace(
        seller_id=listing.seller_id,
        asset_id=listing.asset_id,
        price_tokens=listing.price_tokens,
        listing_type=listing.listing_type,
        expires_at=expires_at,
        is_active=True,
        created_at=datetime.utcnow()
    )
    db.add(new_listing)
    await db.commit()
    await db.refresh(new_listing)
    return new_listing

@router.get("/listings", response_model=List[ListingResponse])
async def get_listings(
    type: Optional[str] = Query(None, description="Listing type filter (e.g. land)"),
    db: AsyncSession = Depends(get_db)
):
    """
    出品一覧を取得する
    type=land が指定された場合、VirtualLandに関連するNFTのみをフィルタリングします。
    """
    stmt = select(Marketplace).where(Marketplace.is_active == True)

    if type == "land":
        # VirtualLandに関連付けられたNFTのみを結合してフィルタリング
        stmt = stmt.join(NFTToken, Marketplace.asset_id == NFTToken.id)\
                   .join(VirtualLand, NFTToken.id == VirtualLand.nft_token_id)

    result = await db.execute(stmt)
    listings = result.scalars().all()
    return listings

@router.put("/listings/{id}/bid")
async def place_bid(
    id: int,
    bid: BidCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    オークション形式の出品に入札する (未実装 - プレースホルダー)
    """
    raise HTTPException(status_code=501, detail="Auction bidding not implemented yet")

@router.post("/listings/{id}/buy", response_model=TransactionResponse)
async def buy_listing(
    id: int,
    buy_req: BuyCreate,
    service: EconomyService = Depends(get_economy_service)
):
    """
    出品を購入する
    """
    transaction = await service.process_purchase(buy_req.buyer_id, id)
    return transaction

# --- User Assets Endpoints ---
# Note: These might be better under /users router, but placed here as requested

@router.get("/users/{id}/assets", response_model=PortfolioResponse) # The path provided in prompt was /users/{id}/assets, but router prefix is /marketplace. Check prompt.
# Prompt: "GET /users/{id}/assets" -> separate from /marketplace prefix or inside?
# Usually routers are mounted. The prompt lists `POST /marketplace/list` and `GET /users/{id}/assets`.
# This implies two routers or one router with absolute paths? FastAPI routers handle relative paths.
# To satisfy the path `/users/{id}/assets`, I should probably create a separate router or mount this one at root.
# But for simplicity, I will add a separate router for assets/users or use absolute path if possible (not possible in router prefix).
# I will define a second router or just add endpoints with "/users" prefix if the main router has no prefix?
# But I defined `prefix="/marketplace"`.
# I will add a separate router for assets.

async def get_user_assets(
    id: str,
    service: EconomyService = Depends(get_economy_service)
):
    """
    ユーザーの資産ポートフォリオを取得
    """
    portfolio = await service.get_user_portfolio(id)
    return portfolio

@router.post("/assets/mint", response_model=NFTResponse)
async def mint_asset(
    asset: AssetMintCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    NFT資産を作成（ミント）する
    """
    # NFT作成
    new_nft = NFTToken(
        token_id=asset.token_id,
        contract_address=asset.contract_address,
        owner_address=asset.owner_address,
        metadata_uri=asset.metadata_uri,
        last_price_eth=0.0
    )
    db.add(new_nft)
    await db.flush() # ID生成のためflush

    # 土地の場合
    if asset.is_land:
        new_land = VirtualLand(
            parcel_x=asset.parcel_x,
            parcel_y=asset.parcel_y,
            owner_id=asset.owner_address,
            nft_token_id=new_nft.id,
            development_status="undeveloped"
        )
        db.add(new_land)

    await db.commit()
    await db.refresh(new_nft)
    return new_nft

# User and Assets Router
assets_router = APIRouter(tags=["assets"])
assets_router.add_api_route("/users/{id}/assets", get_user_assets, methods=["GET"], response_model=PortfolioResponse)
assets_router.add_api_route("/assets/mint", mint_asset, methods=["POST"], response_model=NFTResponse)
