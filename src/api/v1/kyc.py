from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from src.core.database import get_db
from src.services.kyc_service import KYCService
from src.models.kyc_models import KYCStatus

router = APIRouter(prefix="/kyc", tags=["kyc"])

# --- Pydantic Models ---

class KYCSubmitRequest(BaseModel):
    """KYC申請リクエストモデル"""
    customer_id: str = Field(..., description="顧客ID")
    name: str = Field(..., description="氏名")
    dob: str = Field(..., description="生年月日 (YYYY-MM-DD)")
    address: str = Field(..., description="住所")
    id_number: str = Field(..., description="本人確認書類番号")

class KYCVerifyRequest(BaseModel):
    """KYC確認・承認/拒否リクエストモデル"""
    customer_id: str = Field(..., description="顧客ID")
    approved: bool = Field(..., description="承認する場合はTrue, 拒否する場合はFalse")
    rejection_reason: Optional[str] = Field(None, description="拒否理由 (拒否する場合に必須)")

class KYCResponse(BaseModel):
    """KYC申請レスポンスモデル"""
    id: str
    customer_id: str
    status: KYCStatus
    submitted_at: datetime
    verified_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    documents: dict

    model_config = ConfigDict(from_attributes=True)

# --- Dependency ---

async def get_kyc_service(db: AsyncSession = Depends(get_db)) -> KYCService:
    return KYCService(db)

async def verify_admin():
    """
    管理者権限を確認するスタブ依存関係
    実際の実装では、認証トークンの検証やロールの確認を行う
    """
    # スタブ実装: 何もしない (常に許可)
    return True

# --- Endpoints ---

@router.post("/submit", response_model=KYCResponse, status_code=status.HTTP_201_CREATED)
async def submit_kyc(
    request: KYCSubmitRequest,
    service: KYCService = Depends(get_kyc_service)
):
    """
    KYC申請を提出する
    """
    kyc_app = await service.submit_kyc(
        customer_id=request.customer_id,
        name=request.name,
        dob=request.dob,
        address=request.address,
        id_number=request.id_number
    )
    return kyc_app

@router.get("/status/{customer_id}", response_model=KYCResponse)
async def get_kyc_status(
    customer_id: str,
    service: KYCService = Depends(get_kyc_service)
):
    """
    指定された顧客IDのKYCステータスを取得する
    """
    kyc_app = await service.get_kyc_status(customer_id)
    if not kyc_app:
        raise HTTPException(status_code=404, detail="KYC Application not found")
    return kyc_app

@router.put("/verify", response_model=KYCResponse)
async def verify_kyc(
    request: KYCVerifyRequest,
    service: KYCService = Depends(get_kyc_service),
    is_admin: bool = Depends(verify_admin)
):
    """
    KYC申請を承認または拒否する (管理者用)
    """
    if request.approved:
        kyc_app = await service.verify_kyc(request.customer_id)
    else:
        if not request.rejection_reason:
            raise HTTPException(status_code=400, detail="Rejection reason is required when rejecting")
        kyc_app = await service.reject_kyc(request.customer_id, request.rejection_reason)

    if not kyc_app:
        raise HTTPException(status_code=404, detail="KYC Application not found")

    return kyc_app

@router.get("/pending", response_model=List[KYCResponse])
async def get_pending_applications(
    skip: int = Query(0, description="スキップ数"),
    limit: int = Query(10, description="取得件数"),
    service: KYCService = Depends(get_kyc_service),
    is_admin: bool = Depends(verify_admin)
):
    """
    保留中のKYC申請一覧を取得する (管理者用)
    """
    return await service.get_pending_applications(skip=skip, limit=limit)
