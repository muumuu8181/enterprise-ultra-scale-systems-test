from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any
from datetime import datetime

from src.db.session import get_db, AsyncSessionLocal
from src.models.audit_models import SmartContract, AuditReport, Vulnerability, Chain, AuditStatus, RiskLevel, VulnType, Severity
from src.services.analysis_service import generate_audit_report

router = APIRouter()

# Schemas
class SmartContractCreate(BaseModel):
    chain: Chain
    address: Optional[str] = None
    abi: Optional[Any] = None
    source_code: str
    compiler_version: str

class SmartContractResponse(BaseModel):
    id: int
    chain: Chain
    address: Optional[str]
    submitted_at: datetime
    model_config = ConfigDict(from_attributes=True)

class AuditReportResponse(BaseModel):
    id: int
    contract_id: int
    status: AuditStatus
    vulnerabilities_found: int
    risk_level: Optional[RiskLevel]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class VulnerabilityResponse(BaseModel):
    id: int
    vuln_type: VulnType
    severity: Severity
    line_number: int
    description: str
    recommendation: str
    is_false_positive: bool
    model_config = ConfigDict(from_attributes=True)

class AuditReportWithVulns(AuditReportResponse):
    vulnerabilities: List[VulnerabilityResponse] = []

# Background Task Helper
async def run_audit_task(contract_id: int):
    async with AsyncSessionLocal() as db:
        await generate_audit_report(contract_id, db)

# Endpoints

@router.post("/contracts/submit", response_model=SmartContractResponse)
async def submit_contract(
    contract_data: SmartContractCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    contract = SmartContract(**contract_data.model_dump())
    db.add(contract)
    await db.commit()
    await db.refresh(contract)

    background_tasks.add_task(run_audit_task, contract.id)

    return contract

@router.get("/contracts/{id}/audit-status")
async def get_audit_status(id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(AuditReport).where(AuditReport.contract_id == id).order_by(AuditReport.created_at.desc())
    result = await db.execute(stmt)
    report = result.scalars().first()

    if not report:
        raise HTTPException(status_code=404, detail="Audit report not found for this contract")

    return {"status": report.status}

@router.get("/contracts/{id}/report", response_model=AuditReportWithVulns)
async def get_audit_report(id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(AuditReport).options(selectinload(AuditReport.vulnerabilities)).where(AuditReport.contract_id == id).order_by(AuditReport.created_at.desc())
    result = await db.execute(stmt)
    report = result.scalars().first()

    if not report:
        raise HTTPException(status_code=404, detail="Audit report not found")

    return report

@router.get("/contracts/search", response_model=List[SmartContractResponse])
async def search_contracts(chain: Chain = Query(...), db: AsyncSession = Depends(get_db)):
    stmt = select(SmartContract).where(SmartContract.chain == chain)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/vulnerabilities/{id}/details", response_model=VulnerabilityResponse)
async def get_vulnerability(id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Vulnerability).where(Vulnerability.id == id)
    result = await db.execute(stmt)
    vuln = result.scalar_one_or_none()

    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")

    return vuln

@router.post("/vulnerabilities/{id}/false-positive")
async def mark_false_positive(id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Vulnerability).where(Vulnerability.id == id)
    result = await db.execute(stmt)
    vuln = result.scalar_one_or_none()

    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")

    vuln.is_false_positive = True
    await db.commit()
    return {"message": "Marked as false positive"}
