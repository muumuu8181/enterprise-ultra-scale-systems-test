from typing import List, Optional
from datetime import datetime, date
from uuid import uuid4
import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

# 依存関係としてイベントモデルなどをインポート
from src.core.event_sourcing import EventModel

router = APIRouter()

# ------------------------------------------------------------------
# Models
# ------------------------------------------------------------------

class TransactionStatement(BaseModel):
    transaction_id: str
    date: datetime
    type: str # DEPOSIT, WITHDRAW, TRANSFER
    amount: float
    balance_after: float
    description: str

class DailySummary(BaseModel):
    date: date
    total_transactions: int
    total_amount: float

class FraudAlertResponse(BaseModel):
    alert_id: str
    severity: str
    reason: str
    timestamp: datetime
    status: str

class ExportJobStatus(BaseModel):
    job_id: str
    status: str # PENDING, PROCESSING, COMPLETED, FAILED
    download_url: Optional[str] = None

# ------------------------------------------------------------------
# Dependencies (Mock)
# ------------------------------------------------------------------

async def get_session() -> AsyncSession:
    # 実際の実装ではDB接続を返す
    # ここでは型ヒントのためだけのダミー
    raise NotImplementedError("Database dependency not injected")

# ------------------------------------------------------------------
# Logic / Helpers
# ------------------------------------------------------------------

async def generate_large_report(job_id: str):
    """
    非同期で大規模レポートを生成するタスク（モック）
    """
    # 時間がかかる処理をシミュレート
    await asyncio.sleep(5)
    print(f"Report {job_id} generation completed.")
    # 実装ではここでステータスをDB更新し、ファイルをS3などにアップロードする

# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------

@router.get("/reports/account/{account_id}/statement", response_model=List[TransactionStatement])
async def get_account_statement(
    account_id: str,
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    format: str = Query("json", regex="^(json|csv)$"),
    session: AsyncSession = Depends(get_session)
):
    """
    口座明細を取得する。

    Args:
        account_id: 口座ID
        start_date: 開始日時
        end_date: 終了日時
        format: 出力形式 (json/csv)
    """
    # EventStoreからイベントを取得して明細を構築する
    # EventModel.aggregate_id == account_id
    stmt = select(EventModel).where(
        EventModel.aggregate_id == account_id,
        EventModel.timestamp >= start_date,
        EventModel.timestamp <= end_date
    ).order_by(EventModel.timestamp)

    result = await session.execute(stmt)
    events = result.scalars().all()

    statement = []
    balance = 0.0 # 本来はスナップショットから初期残高を計算すべき

    for event in events:
        # payloadはdict前提
        amount = 0.0
        tx_type = event.event_type
        desc = ""

        payload = event.payload
        if tx_type == "MoneyDeposited":
            amount = payload.get("amount", 0)
            balance += amount
            desc = "Deposit"
        elif tx_type == "MoneyWithdrawn":
            amount = -payload.get("amount", 0)
            balance += amount
            desc = "Withdrawal"
        elif tx_type == "TransferInitiated":
            amount = -payload.get("amount", 0)
            balance += amount
            desc = f"Transfer to {payload.get('to_account_id')}"

        statement.append(TransactionStatement(
            transaction_id=event.id or str(uuid4()),
            date=event.timestamp,
            type=tx_type,
            amount=amount,
            balance_after=balance,
            description=desc
        ))

    if format == "csv":
        from fastapi.responses import StreamingResponse
        import io
        import csv

        # CSVデータをメモリ上で生成（大量データの場合はジェネレータ推奨）
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["transaction_id", "date", "type", "amount", "balance_after", "description"])

        for tx in statement:
            writer.writerow([
                tx.transaction_id,
                tx.date.isoformat(),
                tx.type,
                tx.amount,
                tx.balance_after,
                tx.description
            ])

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=statement_{account_id}.csv"}
        )

    return statement

@router.get("/reports/transaction/daily-summary", response_model=DailySummary)
async def get_daily_summary(
    date: date = Query(...),
    session: AsyncSession = Depends(get_session)
):
    """
    日次集計レポートを取得する。
    指定された日の取引総数と総額を返す。
    """
    # 日付の範囲設定
    start_dt = datetime.combine(date, datetime.min.time())
    end_dt = datetime.combine(date, datetime.max.time())

    # 取引イベント（TransferInitiated）を集計
    # payload内のamountを集計するのはJSONクエリが必要で複雑なため、
    # ここでは件数のみ正確に出し、金額はモック（または全取得して計算）とする

    stmt = select(EventModel).where(
        EventModel.event_type == "TransferInitiated",
        EventModel.timestamp >= start_dt,
        EventModel.timestamp <= end_dt
    )
    result = await session.execute(stmt)
    events = result.scalars().all()

    total_amount = sum(e.payload.get("amount", 0) for e in events)

    return DailySummary(
        date=date,
        total_transactions=len(events),
        total_amount=total_amount
    )

@router.get("/reports/fraud/alerts", response_model=List[FraudAlertResponse])
async def get_fraud_alerts(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session)
):
    """
    不正アラート一覧を取得する。
    """
    # アラートテーブルがないため、モックデータを返す
    return [
        FraudAlertResponse(
            alert_id="ALERT-001",
            severity="HIGH",
            reason="Rapid successive transactions",
            timestamp=datetime.now(),
            status="OPEN"
        ),
         FraudAlertResponse(
            alert_id="ALERT-002",
            severity="MEDIUM",
            reason="New recipient",
            timestamp=datetime.now(),
            status="INVESTIGATING"
        )
    ]

@router.post("/reports/export/async", status_code=202)
async def export_report_async(
    background_tasks: BackgroundTasks,
    report_type: str = Query(..., regex="^(statement|fraud|summary)$")
):
    """
    非同期でレポート生成を開始する（大容量対応）。
    """
    job_id = str(uuid4())
    # バックグラウンドタスクに追加
    background_tasks.add_task(generate_large_report, job_id)

    return {
        "message": "Report generation started",
        "job_id": job_id,
        "status_url": f"/reports/export/{job_id}/status"
    }

@router.get("/reports/export/{job_id}/status", response_model=ExportJobStatus)
async def get_export_status(job_id: str):
    """
    レポート生成の進捗状況を確認する。
    """
    # 実際はDBやRedisでジョブ状態を確認
    return ExportJobStatus(
        job_id=job_id,
        status="PROCESSING", # モック
        download_url=None
    )
