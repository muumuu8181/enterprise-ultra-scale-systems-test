from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional
from datetime import datetime, timezone

from src.models.security_models import MisbehaviorReport
from src.services.misbehavior_detector import MisbehaviorDetector
from src.models.v2x_models import PKICertificate

router = APIRouter(prefix="/security", tags=["security"])
detector = MisbehaviorDetector()

# Dependency Injection Placeholder
async def get_db():
    yield None

@router.post("/misbehavior/report")
async def report_misbehavior(
    report_data: dict = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Report a misbehaving vehicle.

    Expected JSON body:
    {
        "vehicle_id": "string",
        "evidence": {},
        "reporter_id": "string",
        "attack_type": "string" (optional, default: unknown)
    }
    """
    vehicle_id = report_data.get("vehicle_id")
    evidence = report_data.get("evidence", {})
    reporter_id = report_data.get("reporter_id")
    attack_type = report_data.get("attack_type", "unknown")

    if not vehicle_id or not reporter_id:
        raise HTTPException(status_code=400, detail="Missing vehicle_id or reporter_id")

    # Calculate impact based on attack type
    impact = 0.0
    if attack_type == "spoofing":
        impact = 20.0
    elif attack_type == "replay":
        impact = 10.0
    elif attack_type == "sybil":
        impact = 30.0
    else:
        impact = 5.0

    # Save to DB if available
    if db:
        report = MisbehaviorReport(
            vehicle_id=vehicle_id,
            attack_type=attack_type,
            evidence=evidence,
            trust_impact=impact,
            reporter_id=reporter_id,
            reported_at=datetime.now(timezone.utc)
        )
        db.add(report)
        await db.commit()

    return {
        "status": "reported",
        "trust_impact": impact,
        "vehicle_id": vehicle_id
    }

@router.get("/misbehavior/reports")
async def list_reports(db: AsyncSession = Depends(get_db)):
    """
    List all misbehavior reports.
    """
    if not db:
        return []

    # stmt = select(MisbehaviorReport)
    # result = await db.execute(stmt)
    # return result.scalars().all()

    # Return placeholder if no DB logic connected
    return []

@router.post("/vehicles/{vehicle_id}/revoke")
async def revoke_vehicle(vehicle_id: str, db: AsyncSession = Depends(get_db)):
    """
    Revoke a vehicle's PKI certificate.
    """
    if db:
        # Check if certificate exists (placeholder logic)
        stmt = select(PKICertificate).where(PKICertificate.vehicle_id == vehicle_id)
        result = await db.execute(stmt)
        cert = result.scalars().first()

        if cert:
            cert.revoked = True
            await db.commit()
        else:
            # If not found, maybe create a dummy one or ignore
            pass

    return {"status": "revoked", "vehicle_id": vehicle_id}

@router.get("/threat-level")
async def get_threat_level(db: AsyncSession = Depends(get_db)):
    """
    Get the current V2X system threat level.
    """
    # Logic: Count recent high-severity reports
    # Placeholder: Always return LOW or based on mock count

    return {"level": "LOW", "active_threats": 0}
