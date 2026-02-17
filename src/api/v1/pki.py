from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Body, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.v2x_models import PKICertificate
from src.services.pki_manager import PKIManager

router = APIRouter(prefix="/pki", tags=["pki"])

# Dependency Injection
async def get_db():
    yield None

# Service
pki_manager = PKIManager()

@router.post("/certificates/enroll")
async def enroll_certificate(
    request: dict = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """
    証明書発行 (vehicle_id, cert_type)
    """
    vehicle_id = request.get("vehicle_id")
    cert_type = request.get("cert_type", "enrollment")

    if not vehicle_id:
        raise HTTPException(status_code=400, detail="vehicle_id is required")

    if db:
        cert = await pki_manager.issue_certificate(db, vehicle_id, cert_type)
        return {
            "vehicle_id": cert.vehicle_id,
            "serial_number": cert.serial_number,
            "valid_until": cert.valid_until
        }

    # Mock return if no DB
    return {"status": "enrolled (mock)", "vehicle_id": vehicle_id}

@router.post("/certificates/rotate")
async def rotate_pseudonym(
    request: dict = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """
    擬似名ローテーション (15分ごとなどに呼ばれる想定)
    """
    vehicle_id = request.get("vehicle_id")
    if not vehicle_id:
        raise HTTPException(status_code=400, detail="vehicle_id is required")

    if db:
        cert = await pki_manager.rotate_pseudonym(db, vehicle_id)
        return {
            "vehicle_id": cert.vehicle_id,
            "serial_number": cert.serial_number,
            "valid_until": cert.valid_until,
            "message": "Pseudonym rotated"
        }

    return {
        "status": "rotated (mock)",
        "vehicle_id": vehicle_id,
        "serial_number": "mock-serial",
        "valid_until": datetime.now(timezone.utc)
    }

@router.post("/certificates/revoke")
async def revoke_certificate(
    request: dict = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """
    証明書失効
    """
    serial_number = request.get("serial_number")
    if not serial_number:
        raise HTTPException(status_code=400, detail="serial_number is required")

    if db:
        success = await pki_manager.revoke_certificate(db, serial_number)
        if not success:
            raise HTTPException(status_code=404, detail="Certificate not found")
        return {"status": "revoked"}

    return {"status": "revoked (mock)"}

@router.get("/certificates/{vehicle_id}/valid")
async def check_valid_certificate(
    vehicle_id: str = Path(...),
    db: AsyncSession = Depends(get_db)
):
    """
    有効証明書確認
    """
    if db:
        stmt = select(PKICertificate).where(
            PKICertificate.vehicle_id == vehicle_id,
            PKICertificate.revoked == False,
            PKICertificate.valid_until > datetime.now(timezone.utc)
        )
        result = await db.execute(stmt)
        certs = result.scalars().all()
        return [{"serial_number": c.serial_number, "valid_until": c.valid_until} for c in certs]

    return []

@router.post("/crl/update")
async def update_crl(
    db: AsyncSession = Depends(get_db)
):
    """
    CRL更新
    """
    # 実際にはCRLを生成して配信するロジック
    return {"status": "CRL updated", "timestamp": datetime.now(timezone.utc)}
