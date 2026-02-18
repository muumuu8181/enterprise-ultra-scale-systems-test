from typing import List, Optional, Dict, Any
from datetime import datetime, date
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, Column, String, Integer, DateTime, Float, Enum
from sqlalchemy.orm import declarative_base
from pydantic import BaseModel

# 循環参照を避けるため、必要なモデルをここで定義するか、コアからインポート
# ここではバッチ専用のモデルを定義
from src.core.event_sourcing import EventStore, TransferInitiated, TransferFailed, MoneyDeposited, Base

class ScheduledTransferModel(Base):
    __tablename__ = "scheduled_transfers"

    id = Column(String, primary_key=True)
    source_account_id = Column(String, nullable=False)
    destination_account_id = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    scheduled_date = Column(DateTime, nullable=False) # 実行予定日
    status = Column(String, default="PENDING") # PENDING, COMPLETED, FAILED
    error_message = Column(String, nullable=True)

class BatchReport(BaseModel):
    batch_id: str
    execution_date: datetime
    total_processed: int
    success_count: int
    failure_count: int
    errors: List[Dict[str, Any]]

class TransferBatchProcessor:
    """
    振込バッチ処理クラス。
    未来日付の振込予約、全銀ファイルの処理、バッチ実行などを担当。
    """
    def __init__(self, session: AsyncSession, event_store: EventStore):
        self.session = session
        self.event_store = event_store

    async def schedule_transfer(self, source_id: str, dest_id: str, amount: float, scheduled_date: date) -> str:
        """
        未来日付の振込を予約する。

        Args:
            source_id: 送金元口座ID
            dest_id: 送金先口座ID
            amount: 金額
            scheduled_date: 振込指定日

        Returns:
            str: 予約ID
        """
        transfer_id = str(uuid4())
        # 時間は当日の9:00とする
        exec_time = datetime.combine(scheduled_date, datetime.min.time()).replace(hour=9)

        scheduled = ScheduledTransferModel(
            id=transfer_id,
            source_account_id=source_id,
            destination_account_id=dest_id,
            amount=amount,
            scheduled_date=exec_time,
            status="PENDING"
        )
        self.session.add(scheduled)
        await self.session.flush()
        return transfer_id

    async def process_scheduled_transfers(self) -> BatchReport:
        """
        当日実行すべき振込予約を処理する (毎営業日9時実行想定)。
        """
        now = datetime.now()
        # 実行予定時刻を過ぎていて、かつPENDINGのものを取得
        stmt = select(ScheduledTransferModel).where(
            ScheduledTransferModel.status == "PENDING",
            ScheduledTransferModel.scheduled_date <= now
        )
        result = await self.session.execute(stmt)
        transfers = result.scalars().all()

        report = BatchReport(
            batch_id=str(uuid4()),
            execution_date=now,
            total_processed=len(transfers),
            success_count=0,
            failure_count=0,
            errors=[]
        )

        for transfer in transfers:
            try:
                # 振込処理 (イベント発行)
                # ここではTransferInitiatedイベントを発行し、実際の残高更新はEventConsumerが行う想定だが、
                # バッチ処理として一貫性を保つため、ここでイベントを保存する。
                event = TransferInitiated(
                    aggregate_id=transfer.source_account_id,
                    to_account_id=transfer.destination_account_id,
                    amount=transfer.amount
                )
                # バージョン管理は自動採番を使用
                await self.event_store.append_event(event, version=None)

                transfer.status = "COMPLETED"
                report.success_count += 1

            except Exception as e:
                transfer.status = "FAILED"
                transfer.error_message = str(e)
                report.failure_count += 1
                report.errors.append({"id": transfer.id, "error": str(e)})
                # 振込処理自体が失敗（イベント保存失敗）したため、補償トランザクションは不要
                # 単に失敗ステータスとして記録する

        await self.session.flush() # 状態更新を保存
        return report

    async def process_zengin_file(self, file_content: str) -> BatchReport:
        """
        全銀フォーマットファイルを処理する。
        """
        lines = file_content.strip().split('\n')
        processed_count = 0
        success_count = 0
        failure_count = 0
        errors = []

        # 簡易的な全銀フォーマット解析 (固定長ではなくCSVライクな想定で実装、本来はバイト位置指定)
        # 行種別: 1=ヘッダ, 2=データ, 8=トレーラ, 9=エンド

        for line in lines:
            if not line: continue
            record_type = line[0] # 先頭1桁が区分

            if record_type == '2': # データレコード
                processed_count += 1
                try:
                    # 想定フォーマット: 2,送金元ID,送金先ID,金額,振込指定日
                    parts = line.split(',')
                    if len(parts) < 4:
                        raise ValueError("Invalid record format")

                    source_id = parts[1]
                    dest_id = parts[2]
                    amount = float(parts[3])

                    # 即時実行として扱う
                    event = TransferInitiated(
                        aggregate_id=source_id,
                        to_account_id=dest_id,
                        amount=amount
                    )
                    await self.event_store.append_event(event, version=None)
                    success_count += 1

                except Exception as e:
                    failure_count += 1
                    errors.append({"line": line, "error": str(e)})
                    # ここでの補償は「何もしない（実行しなかった）」で済む場合が多いが、
                    # もし一部処理が進んでいた場合はhandle_batch_errorsを呼ぶ

        return BatchReport(
            batch_id=str(uuid4()),
            execution_date=datetime.now(),
            total_processed=processed_count,
            success_count=success_count,
            failure_count=failure_count,
            errors=errors
        )

    async def generate_batch_report(self, batch_id: str) -> Dict[str, Any]:
        """
        実行結果レポートを生成する。
        本来はDBに保存されたレポートを取得するが、ここではモック実装。
        """
        # 実装では batch_reports テーブルなどから取得
        return {
            "batch_id": batch_id,
            "status": "COMPLETED",
            "generated_at": datetime.now().isoformat()
        }

    async def handle_batch_errors(self, transfer: ScheduledTransferModel, reason: str):
        """
        エラー時の補償トランザクションを実行する。
        例: 失敗イベントの記録、あるいは仮押さえしていた資金の返金など。
        """
        # TransferFailedイベントを記録
        failed_event = TransferFailed(
            aggregate_id=transfer.source_account_id,
            reason=f"Batch processing failed: {reason}"
        )
        # バージョンは無視
        await self.event_store.append_event(failed_event, version=0)

        # もし送金処理で残高が引かれていた場合（この実装ではTransferInitiatedで引かれる想定）、
        # 返金イベント(MoneyDeposited)を発行して補償する
        # ここでは「失敗したので返金」という簡易ロジック
        refund_event = MoneyDeposited(
            aggregate_id=transfer.source_account_id,
            amount=transfer.amount,
            currency="JPY"
        )
        await self.event_store.append_event(refund_event, version=0)
