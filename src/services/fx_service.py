from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.fx_models import FXRate, FXOrder, OrderType, OrderStatus

class FXService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_latest_rate(self, base_currency: str, quote_currency: str) -> Optional[FXRate]:
        """
        最新の為替レートを取得する
        """
        query = select(FXRate).where(
            and_(
                FXRate.base_currency == base_currency,
                FXRate.quote_currency == quote_currency
            )
        ).order_by(FXRate.timestamp.desc()).limit(1)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def execute_market_order(self, customer_id: str, from_currency: str, to_currency: str, amount: Decimal) -> FXOrder:
        """
        成行注文を実行する
        """
        # レート取得 (from/to の方向を確認)
        # ここでは単純化のため、ベース通貨/クオート通貨のマッチングロジックは簡易的に実装
        # 実際は通貨ペアの方向性(Direct/Indirect)を考慮する必要があるが、
        # 今回は from_currency = base, to_currency = quote と仮定してレートを探す、あるいは逆

        rate = await self.get_latest_rate(from_currency, to_currency)
        executed_price = Decimal("0")

        if rate:
            # base -> quote (Sell Base, Buy Quote) -> Use Bid? No, bank sells at Ask, buys at Bid.
            # Customer sells `from_currency`.
            # If pair is USD/JPY.
            # Case 1: Sell USD (from), Buy JPY (to). Bank buys USD at Bid. Rate = Bid.
            # Case 2: Buy USD (to), Sell JPY (from). Bank sells USD at Ask. Rate = Ask.

            # This logic depends on pair convention. Assuming rate is for `from_currency`/`to_currency`.
            # If rate exists for FROM/TO:
            # Customer Sells FROM. Bank Buys FROM at BID.
            executed_price = rate.bid
        else:
            # Try inverse pair
            inverse_rate = await self.get_latest_rate(to_currency, from_currency)
            if inverse_rate:
                # Pair is TO/FROM.
                # Customer Buys TO (from inverse perspective). Bank Sells TO at ASK.
                # So executed price (in terms of TO) is ASK.
                # But we need price in terms of... wait.
                # Amount is in FROM currency? Or TO? usually amount is base currency.
                # Let's assume amount is in `from_currency`.

                # Simplified: Just use `mid` or explicit bid/ask if direct match found.
                # If no rate found, raise error (or return None handling).
                raise ValueError(f"No rate found for {from_currency}/{to_currency}")

        order = FXOrder(
            customer_id=customer_id,
            from_currency=from_currency,
            to_currency=to_currency,
            amount=amount,
            order_type=OrderType.MARKET,
            status=OrderStatus.FILLED,
            executed_rate=executed_price,
            created_at=datetime.now(timezone.utc)
        )

        self.db.add(order)
        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def place_limit_order(self, customer_id: str, from_currency: str, to_currency: str, amount: Decimal, limit_rate: Decimal) -> FXOrder:
        """
        指値注文を配置する (即時マッチング確認を含む)
        """
        # 現在のレートを確認して即時約定できるかチェック
        rate = await self.get_latest_rate(from_currency, to_currency)
        initial_status = OrderStatus.PENDING
        executed_price = None

        if rate and rate.bid >= limit_rate:
            initial_status = OrderStatus.FILLED
            executed_price = rate.bid

        order = FXOrder(
            customer_id=customer_id,
            from_currency=from_currency,
            to_currency=to_currency,
            amount=amount,
            order_type=OrderType.LIMIT,
            limit_rate=limit_rate,
            status=initial_status,
            executed_rate=executed_price,
            created_at=datetime.now(timezone.utc)
        )

        self.db.add(order)
        await self.db.commit()
        await self.db.refresh(order)

        return order

    async def match_limit_orders(self) -> List[FXOrder]:
        """
        指値注文のマッチング処理を行う (一括処理)
        """
        # PENDING状態の注文を取得
        query = select(FXOrder).where(FXOrder.status == OrderStatus.PENDING)
        result = await self.db.execute(query)
        pending_orders = result.scalars().all()

        if not pending_orders:
            return []

        # 必要な通貨ペアのリストを作成
        needed_pairs = set((o.from_currency, o.to_currency) for o in pending_orders)

        # レートを一括取得 (N+1回避)
        rates_map = {}
        for base, quote in needed_pairs:
            rate = await self.get_latest_rate(base, quote)
            if rate:
                rates_map[(base, quote)] = rate

        matched_orders = []

        for order in pending_orders:
            rate = rates_map.get((order.from_currency, order.to_currency))
            if not rate:
                continue

            # 売り注文 (Sell Base): Limit price is minimum acceptable (>= limit).
            # Market Bid >= Limit.

            if rate.bid >= order.limit_rate:
                order.status = OrderStatus.FILLED
                order.executed_rate = rate.bid
                matched_orders.append(order)

        if matched_orders:
            await self.db.commit()
            for order in matched_orders:
                await self.db.refresh(order)

        return matched_orders
