import hashlib
import secrets
from typing import Optional, Tuple
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from src.models.card_models import Card, CardStatus, CardTransaction, TransactionStatus
from src.models.account_models import Account

class CardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _generate_card_number(self, bin_prefix: str = "400000") -> str:
        # 16桁のカード番号を生成 (簡略化)
        suffix = "".join([str(secrets.randbelow(10)) for _ in range(16 - len(bin_prefix))])
        return f"{bin_prefix}{suffix}"

    def _generate_cvv(self) -> str:
        # 3桁のCVVを生成
        return "".join([str(secrets.randbelow(10)) for _ in range(3)])

    def _hash_cvv(self, cvv: str) -> str:
        # PBKDF2 + SHA-256 (ソルト付き) でハッシュ化
        # 本番環境ではソルトは環境変数等から取得し、より安全に管理すべきです
        salt = b"fixed_salt_for_banking_core_demo"
        return hashlib.pbkdf2_hmac('sha256', cvv.encode(), salt, 100000).hex()

    async def issue_card(self, account_id: int, card_type: str = "debit") -> Tuple[Card, str, str]:
        """
        カードを発行する
        :return: (Cardオブジェクト, 生のカード番号, 生のCVV)
        """
        # アカウントの存在確認
        stmt = select(Account).where(Account.id == account_id)
        result = await self.db.execute(stmt)
        account = result.scalar_one_or_none()
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        # カードタイプに基づく制限設定 (簡易ロジック)
        daily_limit = 500000.0
        monthly_limit = 2000000.0
        if card_type.lower() == "platinum":
            daily_limit = 1000000.0
            monthly_limit = 5000000.0

        raw_card_number = self._generate_card_number()
        raw_cvv = self._generate_cvv()
        expiry = (datetime.now(timezone.utc) + timedelta(days=365*5)).strftime("%m/%y")

        card = Card(
            account_id=account_id,
            card_number_masked=f"************{raw_card_number[-4:]}",
            expiry_date=expiry,
            cvv_hash=self._hash_cvv(raw_cvv),
            status=CardStatus.ACTIVE,
            daily_limit=daily_limit,
            monthly_limit=monthly_limit
        )
        self.db.add(card)
        await self.db.commit()
        await self.db.refresh(card)

        return card, raw_card_number, raw_cvv

    async def get_card(self, card_id: int) -> Card:
        """カード情報を取得する"""
        stmt = select(Card).where(Card.id == card_id)
        result = await self.db.execute(stmt)
        card = result.scalar_one_or_none()
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")
        return card

    async def freeze_card(self, card_id: int) -> Card:
        """カードを凍結する"""
        card = await self.get_card(card_id)
        card.status = CardStatus.FROZEN
        await self.db.commit()
        await self.db.refresh(card)
        return card

    async def unfreeze_card(self, card_id: int) -> Card:
        """カードの凍結を解除する"""
        card = await self.get_card(card_id)
        card.status = CardStatus.ACTIVE
        await self.db.commit()
        await self.db.refresh(card)
        return card

    async def update_limits(self, card_id: int, daily_limit: Optional[float] = None, monthly_limit: Optional[float] = None) -> Card:
        """利用限度額を更新する"""
        card = await self.get_card(card_id)
        if daily_limit is not None:
            card.daily_limit = daily_limit
        if monthly_limit is not None:
            card.monthly_limit = monthly_limit
        await self.db.commit()
        await self.db.refresh(card)
        return card

    async def issue_virtual_card(self, original_card_id: int) -> Tuple[Card, str, str]:
        """
        既存のカードに紐づくバーチャルカードを発行する
        :return: (Cardオブジェクト, 生のカード番号, 生のCVV)
        """
        original_card = await self.get_card(original_card_id)

        # バーチャルカード用のBIN (例: 411111)
        raw_card_number = self._generate_card_number(bin_prefix="411111")
        raw_cvv = self._generate_cvv()
        expiry = (datetime.now(timezone.utc) + timedelta(days=365*2)).strftime("%m/%y") # 有効期限は短め

        new_card = Card(
            account_id=original_card.account_id,
            card_number_masked=f"************{raw_card_number[-4:]}",
            expiry_date=expiry,
            cvv_hash=self._hash_cvv(raw_cvv),
            status=CardStatus.ACTIVE,
            daily_limit=100000.0, # バーチャルカードは制限を低く設定
            monthly_limit=500000.0
        )
        self.db.add(new_card)
        await self.db.commit()
        await self.db.refresh(new_card)

        return new_card, raw_card_number, raw_cvv

    async def process_payment(self, card_id: int, amount: float, merchant: str, currency: str = "JPY") -> CardTransaction:
        """決済処理を実行する"""
        card = await self.get_card(card_id)

        if card.status != CardStatus.ACTIVE:
            raise HTTPException(status_code=400, detail="Card is not active")

        # 限度額チェック (日次・月次累積)
        if not await self.check_limits(card_id, amount):
             raise HTTPException(status_code=400, detail="Exceeds limit")

        transaction = CardTransaction(
            card_id=card_id,
            merchant=merchant,
            amount=amount,
            currency=currency,
            status=TransactionStatus.COMPLETED # デフォルトで完了とする
        )
        self.db.add(transaction)
        await self.db.commit()
        await self.db.refresh(transaction)
        return transaction

    async def check_limits(self, card_id: int, amount: float) -> bool:
        """限度額をチェックする (日次・月次累積)"""
        card = await self.get_card(card_id)

        # 1. 日次限度額チェック
        now = datetime.now(timezone.utc)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

        stmt_daily = select(func.sum(CardTransaction.amount)).where(
            CardTransaction.card_id == card_id,
            CardTransaction.processed_at >= start_of_day,
            CardTransaction.status == TransactionStatus.COMPLETED
        )
        result_daily = await self.db.execute(stmt_daily)
        daily_total = result_daily.scalar() or 0.0

        if daily_total + amount > card.daily_limit:
            return False

        # 2. 月次限度額チェック
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        stmt_monthly = select(func.sum(CardTransaction.amount)).where(
            CardTransaction.card_id == card_id,
            CardTransaction.processed_at >= start_of_month,
            CardTransaction.status == TransactionStatus.COMPLETED
        )
        result_monthly = await self.db.execute(stmt_monthly)
        monthly_total = result_monthly.scalar() or 0.0

        if monthly_total + amount > card.monthly_limit:
            return False

        return True
