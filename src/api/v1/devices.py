from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from geoalchemy2.elements import WKTElement
from src.database import get_db
from src.models.signage_models import SignageDevice, ContentPlaylist, Orientation
from src.services.content_service import ContentService
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

router = APIRouter(prefix="/devices", tags=["signage-devices"])
content_service = ContentService()

# Schemas
class DeviceCreate(BaseModel):
    serial: str
    latitude: float
    longitude: float
    screen_size: float
    orientation: Orientation
    os_version: str
    groups: Optional[List[str]] = []

class DeviceResponse(BaseModel):
    id: int
    serial: str
    screen_size: float
    orientation: str
    os_version: str
    status: str
    last_heartbeat: Optional[datetime] = None
    groups: List[str]
    model_config = ConfigDict(from_attributes=True)

class DeviceStatus(BaseModel):
    id: int
    status: str
    last_heartbeat: Optional[datetime] = None

class ContentResponse(BaseModel):
    content_name: str
    type: str

class PlaylistAssignRequest(BaseModel):
    group_name: str
    playlist_id: int

# Endpoints

@router.post("/register", response_model=DeviceResponse)
async def register_device(device: DeviceCreate, db: AsyncSession = Depends(get_db)):
    """
    Register a new signage device.
    """
    # Create point from lat/lon
    point = f"POINT({device.longitude} {device.latitude})"

    db_device = SignageDevice(
        serial=device.serial,
        location=WKTElement(point, srid=4326),
        screen_size=device.screen_size,
        orientation=device.orientation,
        os_version=device.os_version,
        status="offline", # Default
        groups=device.groups
    )

    db.add(db_device)
    try:
        await db.commit()
        await db.refresh(db_device)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Registration failed: {str(e)}")

    return db_device

@router.get("/{id}/status", response_model=DeviceStatus)
async def get_device_status(id: int, db: AsyncSession = Depends(get_db)):
    """
    Get device status.
    """
    device = await db.get(SignageDevice, id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    return DeviceStatus(id=device.id, status=device.status, last_heartbeat=device.last_heartbeat)

@router.get("/{id}/current-content", response_model=ContentResponse)
async def get_current_content(id: int, db: AsyncSession = Depends(get_db)):
    """
    Get current content playing on the device (Simulated).
    """
    device = await db.get(SignageDevice, id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Simulate content
    if device.status == "online":
        return ContentResponse(content_name="Demo Video", type="video")
    else:
        return ContentResponse(content_name="Offline Placeholder", type="image")

@router.post("/{id}/reboot")
async def reboot_device(id: int, db: AsyncSession = Depends(get_db)):
    """
    Reboot device (Simulated).
    """
    device = await db.get(SignageDevice, id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    device.status = "rebooting"
    await db.commit()

    # Simulate reboot completion logic
    device.status = "online"
    device.last_heartbeat = datetime.now(timezone.utc)
    await db.commit()

    return {"message": "Device rebooted", "status": device.status}

@router.get("/fleet/online-count")
async def get_online_count(db: AsyncSession = Depends(get_db)):
    """
    Get count of online devices.
    """
    query = select(func.count(SignageDevice.id)).where(SignageDevice.status == "online")
    result = await db.execute(query)
    count = result.scalar()
    return {"online_count": count}

@router.post("/groups/assign-playlist")
async def assign_playlist_to_group(request: PlaylistAssignRequest, db: AsyncSession = Depends(get_db)):
    """
    Assign playlist to a group of devices.
    """
    # Verify playlist exists
    playlist = await db.get(ContentPlaylist, request.playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    # Find devices in group
    query = select(SignageDevice)
    result = await db.execute(query)
    devices = result.scalars().all()

    target_devices = [d for d in devices if request.group_name in (d.groups or [])]

    results = []
    for device in target_devices:
        push_result = await content_service.push_playlist(device.id, playlist.id, db)
        results.append(push_result)

    return {"message": f"Assigned playlist to {len(target_devices)} devices", "details": results}
