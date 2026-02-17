from typing import List, Optional
from datetime import datetime, time, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from src.core.event_sourcing import EventModel

class FraudAlert(BaseModel):
    alert_id: str
    transaction_id: str
    severity: str  # "HIGH", "MEDIUM", "LOW"
    reason: str
    timestamp: datetime
    score: int

class TransactionContext(BaseModel):
    """
    不正検知のための取引コンテキスト
    """
    transaction_id: str
    source_account_id: str
    destination_account_id: str
    amount: float
    timestamp: datetime

class FraudDetectionEngine:
    """
    不正検知エンジン。
    リアルタイムで取引を分析し、リスクスコアを算出して疑わしい取引をブロックする。
    """

    HIGH_AMOUNT_THRESHOLD = 1_000_000  # 100万円以上は高額
    RAPID_TRANSACTION_LIMIT = 3        # 1分間に3回以上
    RAPID_TRANSACTION_WINDOW = 60      # 秒

    def __init__(self, session: AsyncSession):
        self.session = session

    async def analyze_transaction(self, context: TransactionContext) -> int:
        """
        取引を分析し、リスクスコアを返す。

        Args:
            context (TransactionContext): 取引コンテキスト

        Returns:
            int: リスクスコア (0-100)
        """
        # データ収集 (Async)
        recent_count = await self._count_recent_transactions(
            context.source_account_id,
            context.timestamp
        )
        is_new_recipient = await self._is_new_recipient(
            context.source_account_id,
            context.destination_account_id
        )

        # スコア計算 (Sync)
        final_score, reasons = self.calculate_risk_score(
            context, recent_count, is_new_recipient
        )

        if final_score >= 80: # 高リスクならアラート生成
            await self.create_fraud_alert(context, final_score, reasons)
            # 自動ブロックロジックを呼び出すか、呼び出し元に任せるか。
            # block_suspicious_transactionは例外を投げるなどの実装が考えられる
            if final_score >= 90:
                self.block_suspicious_transaction(context, reasons)

        return final_score

    def calculate_risk_score(self, context: TransactionContext, recent_count: int, is_new_recipient: bool) -> tuple[int, List[str]]:
        """
        リスクスコアと理由を計算する。

        Args:
            context: 取引コンテキスト
            recent_count: 直近の取引数
            is_new_recipient: 新規受取人フラグ

        Returns:
            (int, List[str]): スコアと理由のリスト
        """
        score = 0
        reasons = []

        # 1. 異常時間帯チェック (23:00 - 05:00)
        t = context.timestamp.time()
        if t >= time(23, 0) or t < time(5, 0):
            score += 30
            reasons.append("Late night transaction")

        # 2. 高額取引チェック
        if context.amount >= self.HIGH_AMOUNT_THRESHOLD:
            score += 40
            reasons.append("High amount transaction")

        # 3. 急速連続取引チェック
        if recent_count >= self.RAPID_TRANSACTION_LIMIT:
            score += 50
            reasons.append("Rapid successive transactions")

        # 4. 新規受取口座チェック
        if is_new_recipient:
            score += 20
            reasons.append("New recipient")

        return min(100, score), reasons

    def block_suspicious_transaction(self, context: TransactionContext, reasons: List[str]):
        """
        疑わしい取引をブロックする。

        Args:
            context: 取引コンテキスト
            reasons: ブロック理由

        Raises:
            ValueError: 取引ブロック時に発生させる例外
        """
        reason_str = ", ".join(reasons)
        raise ValueError(f"Transaction blocked due to high fraud risk: {reason_str}")

    async def create_fraud_alert(self, context: TransactionContext, score: int, reasons: List[str]):
        """
        不正アラートを生成し、通知（今回はログ出力やDB保存のモック）を行う。
        """
        alert = FraudAlert(
            alert_id=f"ALERT-{context.transaction_id}",
            transaction_id=context.transaction_id,
            severity="HIGH" if score >= 90 else "MEDIUM",
            reason=", ".join(reasons),
            timestamp=datetime.now(),
            score=score
        )
        # 実装ではDBのalertsテーブルに保存したり、Slack通知したりする
        # ここではprintで代用
        print(f"[FRAUD ALERT] {alert}")

    async def _count_recent_transactions(self, account_id: str, current_time: datetime) -> int:
        """過去1分間の取引数をカウントする"""
        # EventModelから検索する (TransferInitiatedイベントを探す)
        # Note: EventModelのpayloadの中身を検索するのはSQLAlchemyのJSON演算が必要。
        # ここでは簡易的に、イベントタイプとaggregate_idで絞り込み、メモリ上でタイムスタンプチェックする
        # ※本来はDB側で絞り込むべき

        window_start = current_time - timedelta(seconds=self.RAPID_TRANSACTION_WINDOW)

        # aggregate_idがsource_account_idと一致すると仮定
        stmt = select(EventModel).where(
            EventModel.aggregate_id == account_id,
            EventModel.event_type == "TransferInitiated",
            EventModel.timestamp >= window_start,
            EventModel.timestamp < current_time
        )

        result = await self.session.execute(stmt)
        events = result.scalars().all()
        return len(events)

    async def _is_new_recipient(self, source_id: str, dest_id: str) -> bool:
        """過去にこの受取人への送金があるかチェック"""
        # 過去の全履歴を検索するのは重いが、要件のため実装。
        # TransferInitiatedイベントのpayload -> to_account_id をチェック

        # PostgresのJSONB演算子を使うのがベストだが、DB依存度を下げるため
        # ここでは "TransferInitiated" イベントを取得して確認
        # ※実運用では専用の projection table (beneficiaries) を使うべき

        stmt = select(EventModel).where(
            EventModel.aggregate_id == source_id,
            EventModel.event_type == "TransferInitiated"
        )
        result = await self.session.execute(stmt)
        events = result.scalars().all()

        for event in events:
            # payloadはdictとして取得できる想定
            payload = event.payload
            if payload.get("to_account_id") == dest_id:
                return False # 過去に見つかった

        return True # 初めて
