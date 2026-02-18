from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Body, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from src.models.v2x_models import OTAPackage

router = APIRouter(prefix="/ota", tags=["ota"])

async def get_db():
    yield None

@router.post("/packages", status_code=status.HTTP_201_CREATED)
async def register_package(
    package_data: dict = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """
    OTAパッケージ登録 (version, target_ecu, checksum)
    """
    if db:
        pkg = OTAPackage(
            version=package_data.get("version"),
            target_ecu=package_data.get("target_ecu"),
            checksum=package_data.get("checksum"),
            status="pending",
            created_at=datetime.now(timezone.utc)
        )
        db.add(pkg)
        await db.commit()
        await db.refresh(pkg)
        return pkg

    return {"status": "registered (mock)", "version": package_data.get("version")}

@router.get("/packages/{vehicle_id}/pending")
async def get_pending_packages(
    vehicle_id: str = Path(...),
    target_ecu: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    待機中パッケージ一覧
    """
    if db:
        stmt = select(OTAPackage).where(OTAPackage.status == "pending")
        if target_ecu:
            stmt = stmt.where(OTAPackage.target_ecu == target_ecu)

        result = await db.execute(stmt)
        return result.scalars().all()

    return []

@router.post("/packages/{package_id}/deploy")
async def deploy_package(
    package_id: int = Path(...),
    db: AsyncSession = Depends(get_db)
):
    """
    デプロイ開始
    """
    if db:
        stmt = select(OTAPackage).where(OTAPackage.id == package_id)
        result = await db.execute(stmt)
        pkg = result.scalar_one_or_none()

        if not pkg:
            raise HTTPException(status_code=404, detail="Package not found")

        pkg.status = "deploying"
        await db.commit()
        return {"status": "deploying", "package_id": package_id}

    return {"status": "deploying (mock)"}

@router.put("/packages/{package_id}/status")
async def update_package_status(
    package_id: int = Path(...),
    status_data: dict = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """
    更新状態報告 (downloading/installing/completed/failed)
    """
    new_status = status_data.get("status")
    if not new_status:
        raise HTTPException(status_code=400, detail="status is required")

    if db:
        stmt = select(OTAPackage).where(OTAPackage.id == package_id)
        result = await db.execute(stmt)
        pkg = result.scalar_one_or_none()

        if not pkg:
            raise HTTPException(status_code=404, detail="Package not found")

        pkg.status = new_status
        await db.commit()
        return {"status": new_status}

    return {"status": new_status + " (mock)"}

@router.get("/packages/{package_id}/progress")
async def get_package_progress(
    package_id: int = Path(...),
    db: AsyncSession = Depends(get_db)
):
    """
    進捗確認
    """
    if db:
        stmt = select(OTAPackage).where(OTAPackage.id == package_id)
        result = await db.execute(stmt)
        pkg = result.scalar_one_or_none()

        if not pkg:
            raise HTTPException(status_code=404, detail="Package not found")

        return {"package_id": pkg.id, "status": pkg.status}

    return {"package_id": package_id, "status": "unknown (mock)"}
