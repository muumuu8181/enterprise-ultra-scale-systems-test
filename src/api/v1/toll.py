from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel, ConfigDict, Field

from src.models.toll_models import TollTransaction, ETCAccount
from src.database import get_db

router = APIRouter(prefix="/toll", tags=["toll"])

# Pydantic Models
class TollTransactionCreate(BaseModel):
    vehicle_id: str
    gate_id: str
    amount: float
    payment_method: str = "ETC"

class TollTransactionResponse(BaseModel):
    id: int
    vehicle_id: str
    gate_id: str
    amount: float
    payment_method: str
    processed_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ETCAccountResponse(BaseModel):
    vehicle_id: str
    balance: float
    auto_recharge_threshold: float
    auto_recharge_amount: float
    model_config = ConfigDict(from_attributes=True)

class RechargeRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Amount to recharge")

# Endpoints

@router.post("/gates/{gate_id}/vehicles/{vehicle_id}/entry")
async def record_entry(
    gate_id: str = Path(..., description="Gate ID"),
    vehicle_id: str = Path(..., description="Vehicle ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    通行記録 (Entry Record)
    ゲート進入を記録する。現時点ではログ出力のみ。
    """
    # ここにTollGateの存在確認やEntryログ保存ロジックが入る想定
    return {"status": "entry_recorded", "gate_id": gate_id, "vehicle_id": vehicle_id, "timestamp": datetime.now(timezone.utc)}

@router.post("/transactions", response_model=TollTransactionResponse)
async def create_transaction(
    txn: TollTransactionCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    料金徴収 (Toll Collection)
    残高を確認し、不足していれば自動チャージを試みる。
    それでも不足ならエラー。
    """
    if not db:
        raise HTTPException(status_code=500, detail="Database not available")

    # アカウント取得
    stmt = select(ETCAccount).where(ETCAccount.vehicle_id == txn.vehicle_id)
    result = await db.execute(stmt)
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="ETC Account not found")

    # 自動チャージ判定 (支払い前に閾値をチェックしてチャージ)
    if account.balance < account.auto_recharge_threshold:
        account.balance += account.auto_recharge_amount
        # チャージした上で、もしそれでも支払い額に足りない場合はエラーにするか、
        # あるいは「支払い額に足りない場合にもチャージする」ロジックを追加するか。
        # ここではシンプルに閾値判定のみとする。

    # 残高不足チェック
    if account.balance < txn.amount:
        # 閾値判定でチャージされなかったが、今回の支払いで不足する場合
        # 救済措置としてチャージを試みる (オプション)
        # ここでは厳格にチェック
        raise HTTPException(status_code=402, detail="Insufficient balance")

    # 支払い
    account.balance -= txn.amount

    # トランザクション記録
    new_txn = TollTransaction(
        vehicle_id=txn.vehicle_id,
        gate_id=txn.gate_id,
        amount=txn.amount,
        payment_method=txn.payment_method,
        processed_at=datetime.now(timezone.utc)
    )
    db.add(new_txn)
    await db.commit()
    await db.refresh(new_txn)

    return new_txn

@router.get("/accounts/{vehicle_id}/balance", response_model=ETCAccountResponse)
async def get_balance(
    vehicle_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    ETC残高照会
    """
    if not db:
         raise HTTPException(status_code=500, detail="Database not available")

    stmt = select(ETCAccount).where(ETCAccount.vehicle_id == vehicle_id)
    result = await db.execute(stmt)
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="ETC Account not found")

    return account

@router.post("/accounts/{vehicle_id}/recharge", response_model=ETCAccountResponse)
async def recharge_account(
    vehicle_id: str,
    recharge: RechargeRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    チャージ (手動)
    """
    if not db:
         raise HTTPException(status_code=500, detail="Database not available")

    stmt = select(ETCAccount).where(ETCAccount.vehicle_id == vehicle_id)
    result = await db.execute(stmt)
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="ETC Account not found")

    account.balance += recharge.amount
    await db.commit()
    await db.refresh(account)

    return account

@router.get("/history/{vehicle_id}", response_model=List[TollTransactionResponse])
async def get_history(
    vehicle_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    通行履歴照会
    """
    if not db:
         return []

    stmt = select(TollTransaction).where(TollTransaction.vehicle_id == vehicle_id).order_by(TollTransaction.processed_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()
