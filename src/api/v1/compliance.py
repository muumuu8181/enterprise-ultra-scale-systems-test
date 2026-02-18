from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.session import get_db
from src.services.compliance_service import ComplianceService
from src.schemas.compliance import (
    SanctionsCheckResponse,
    SARRequest,
    SARResponse,
    AMLScoreResponse
)
from typing import List, Dict, Any

router = APIRouter(prefix="/compliance", tags=["Compliance"])

async def get_compliance_service(db: AsyncSession = Depends(get_db)) -> ComplianceService:
    return ComplianceService(db)

@router.get("/sanctions-check/{customer_id}", response_model=SanctionsCheckResponse)
async def check_sanctions(
    customer_id: str,
    service: ComplianceService = Depends(get_compliance_service)
):
    """
    顧客の制裁リスト照合を実行する
    """
    return await service.check_sanctions_list(customer_id)

@router.post("/sar/generate", response_model=SARResponse)
async def generate_sar(
    request: SARRequest,
    service: ComplianceService = Depends(get_compliance_service)
):
    """
    SAR (疑わしい取引報告書) を生成する
    """
    return await service.generate_sar(request.customer_id, request.transaction_ids)

@router.get("/reports/aml-summary", response_model=List[AMLScoreResponse])
async def get_aml_summary(
    service: ComplianceService = Depends(get_compliance_service)
):
    """
    AMLリスクサマリーレポートを取得する (日次/月次)
    """
    # モック: 数人の顧客のスコアを返す
    customers = ["user_123", "bad_guy", "high_risk_user"]
    results = []
    for cid in customers:
        score_data = await service.calculate_aml_score(cid)
        results.append(score_data)
    return results
