from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from src.models.nft_models import NFTToken, VirtualLand, Marketplace, Transaction
from fastapi import HTTPException
from datetime import datetime
from typing import Dict, Any, List

class EconomyService:
    """
    経済システムサービス
    NFTの売買、ポートフォリオ管理などを担当
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_purchase(self, buyer_id: str, listing_id: int) -> Transaction:
        """
        購入処理を実行する
        - 出品情報の確認
        - 所有権の移転
        - 取引履歴の作成
        """
        # 出品情報を取得
        stmt = select(Marketplace).where(Marketplace.id == listing_id, Marketplace.is_active == True)
        result = await self.db.execute(stmt)
        listing = result.scalar_one_or_none()

        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found or inactive")

        if listing.expires_at < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Listing has expired")

        # 資産の取得 (NFTToken または VirtualLand)
        # ここではasset_idがNFTToken.idと仮定しているが、実際はListingTypeなどで分岐が必要
        # 簡易化のためNFTTokenとして扱う
        asset_stmt = select(NFTToken).options(selectinload(NFTToken.virtual_land)).where(NFTToken.id == listing.asset_id)
        asset_result = await self.db.execute(asset_stmt)
        nft = asset_result.scalar_one_or_none()

        if not nft:
             raise HTTPException(status_code=404, detail="Asset not found")

        # 所有権の移転
        old_owner = nft.owner_address
        nft.owner_address = buyer_id
        nft.last_price_eth = listing.price_tokens # トークン価格をETH価格として記録 (単位は要調整)

        # VirtualLandの場合も所有者を更新
        if nft.virtual_land:
            nft.virtual_land.owner_id = buyer_id

        # 出品を終了
        listing.is_active = False

        # 取引履歴の作成
        transaction = Transaction(
            buyer_id=buyer_id,
            listing_id=listing.id,
            amount=listing.price_tokens,
            timestamp=datetime.utcnow(),
            status="completed"
        )
        self.db.add(transaction)

        await self.db.commit()
        await self.db.refresh(transaction)

        return transaction

    async def get_user_portfolio(self, user_id: str) -> Dict[str, Any]:
        """
        ユーザーのポートフォリオ（所有資産）を取得する
        """
        # 所有するNFTを取得
        nft_stmt = select(NFTToken).options(selectinload(NFTToken.virtual_land)).where(NFTToken.owner_address == user_id)
        nft_result = await self.db.execute(nft_stmt)
        nfts = nft_result.scalars().all()

        # 所有する土地を取得 (NFTに紐づかない土地がある場合も考慮)
        land_stmt = select(VirtualLand).where(VirtualLand.owner_id == user_id)
        land_result = await self.db.execute(land_stmt)
        lands = land_result.scalars().all()

        return {
            "user_id": user_id,
            "nfts_count": len(nfts),
            "lands_count": len(lands),
            "nfts": nfts,
            "lands": lands
        }

    async def get_nearby_lands(self, x: int, y: int, radius: int) -> List[VirtualLand]:
        """
        指定された座標周辺の土地を取得する (グリッドベース)
        """
        stmt = select(VirtualLand).where(
            VirtualLand.parcel_x >= x - radius,
            VirtualLand.parcel_x <= x + radius,
            VirtualLand.parcel_y >= y - radius,
            VirtualLand.parcel_y <= y + radius
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
