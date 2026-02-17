from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException
from src.models.inventory_models import Item, UserInventory, TradeOffer
from src.models.user import User

class InventoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_item(self, user_id: int, item_id: int, quantity: int):
        """
        ユーザーにアイテムを追加する
        """
        stmt = select(UserInventory).where(UserInventory.user_id == user_id, UserInventory.item_id == item_id)
        result = await self.db.execute(stmt)
        inventory = result.scalar_one_or_none()

        if inventory:
            inventory.quantity += quantity
        else:
            inventory = UserInventory(user_id=user_id, item_id=item_id, quantity=quantity)
            self.db.add(inventory)

        # We don't commit here, let the controller handle transaction?
        # Usually service methods might be part of larger transaction.
        # But if simple action, we can flush.
        # I'll rely on the caller to commit.

    async def remove_item(self, user_id: int, item_id: int, quantity: int):
        """
        ユーザーからアイテムを削除（消費）する
        """
        stmt = select(UserInventory).where(UserInventory.user_id == user_id, UserInventory.item_id == item_id)
        result = await self.db.execute(stmt)
        inventory = result.scalar_one_or_none()

        if not inventory or inventory.quantity < quantity:
            raise HTTPException(status_code=400, detail="Insufficient item quantity")

        inventory.quantity -= quantity
        # If quantity 0, we could delete, but keeping it is safer for history unless specified.

    async def use_item(self, user_id: int, item_id: int, quantity: int):
        """
        アイテムを使用する
        """
        # "Use" logic might involve effects, but here we just consume.
        await self.remove_item(user_id, item_id, quantity)

    async def sell_item(self, user_id: int, item_id: int, quantity: int, price: int):
        """
        アイテムを売却する
        """
        # Validate ownership and deduct item
        await self.remove_item(user_id, item_id, quantity)

        # Add currency to user
        user_stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(user_stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Price is total price or unit price?
        # Assuming total price based on typical API signatures "quantity, price" (price for the batch or price per unit?)
        # Let's assume 'price' is the total amount to receive.
        user.currency += price

    async def create_trade_offer(self, from_user_id: int, to_user_id: int, offer_items: dict, request_items: dict):
        """
        トレードオファーを作成する
        """
        # Validate that from_user has the items and quantity
        for item_id, qty in offer_items.items():
            # item_id is str in JSON usually, convert to int
            item_id_int = int(item_id)
            qty_int = int(qty)

            stmt = select(UserInventory).where(UserInventory.user_id == from_user_id, UserInventory.item_id == item_id_int)
            result = await self.db.execute(stmt)
            inv = result.scalar_one_or_none()

            if not inv or inv.quantity < qty_int:
                 raise HTTPException(status_code=400, detail=f"Insufficient inventory for item {item_id}")
            if inv.is_locked:
                 raise HTTPException(status_code=400, detail=f"Item {item_id} is locked")

            # Lock the items? For simple offer, maybe not lock yet until accepted?
            # Or lock immediately?
            # Prompt doesn't specify. Standard MMO trade locks items on offer creation (or puts them in escrow).
            # I will lock them to prevent double spending.
            inv.is_locked = True
            # Note: partial locking (locking quantity) requires splitting inventory rows or a "locked_quantity" column.
            # UserInventory only has 'is_locked' boolean.
            # If 'is_locked' is boolean, we lock the WHOLE stack or row.
            # If user has 10 items and trades 1, locking the row locks 10.
            # This is a limitation of the model `is_locked` boolean.
            # I will proceed with locking the row.

        trade = TradeOffer(
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            offer_items=offer_items,
            request_items=request_items,
            status="pending"
        )
        self.db.add(trade)
        return trade

    async def validate_trade(self, trade_id: int):
        """
        トレードの有効性を確認する
        """
        stmt = select(TradeOffer).where(TradeOffer.id == trade_id)
        result = await self.db.execute(stmt)
        trade = result.scalar_one_or_none()

        if not trade:
            raise HTTPException(status_code=404, detail="Trade not found")

        if trade.status != "pending":
            return False

        return True
