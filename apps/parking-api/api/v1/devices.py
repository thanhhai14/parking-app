from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime

from core.database import get_db_session
from models.parking_lot import ParkingSite, ParkingZone, ParkingGate
from models.device import Device, Camera
from api.deps import get_current_user, get_current_admin_user
from models.user import User

router = APIRouter()

# --- Pydantic Schemas ---
class SiteBase(BaseModel):
    code: str
    name: str
    address: Optional[str] = None
    timezone: str = "Asia/Ho_Chi_Minh"

class SiteCreate(SiteBase):
    pass

class SiteResponse(SiteBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    is_active: bool
    created_at: datetime

class ZoneBase(BaseModel):
    site_id: uuid.UUID
    code: str
    name: str
    capacity: int = 0
    vehicle_type_id: Optional[uuid.UUID] = None

class ZoneCreate(ZoneBase):
    pass

class ZoneResponse(ZoneBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    current_count: int
    is_active: bool
    created_at: datetime

class GateBase(BaseModel):
    zone_id: uuid.UUID
    code: str
    name: str
    gate_type: str # entry, exit, mixed
    direction: str # in, out, both

class GateCreate(GateBase):
    pass

class GateResponse(GateBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    is_active: bool
    created_at: datetime

class DeviceBase(BaseModel):
    gate_id: Optional[uuid.UUID] = None
    code: str
    name: str
    device_type: str
    connection_type: str
    connection_config: dict = {}
    firmware_version: Optional[str] = None
    agent_id: Optional[str] = None

class DeviceCreate(DeviceBase):
    pass

class DeviceResponse(DeviceBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    status: str
    is_active: bool
    created_at: datetime

class CameraBase(BaseModel):
    gate_id: Optional[uuid.UUID] = None
    code: str
    name: str
    camera_type: str
    stream_url: Optional[str] = None
    snapshot_url: Optional[str] = None
    username: Optional[str] = None
    role: str
    config: dict = {}
    agent_id: Optional[str] = None

class CameraCreate(CameraBase):
    password_secret_key: Optional[str] = None

class CameraResponse(CameraBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    status: str
    is_active: bool
    created_at: datetime

# --- Sites endpoints ---
@router.post("/sites", response_model=SiteResponse, status_code=status.HTTP_201_CREATED)
async def create_site(
    data: SiteCreate, 
    db: AsyncSession = Depends(get_db_session), 
    current_user: User = Depends(get_current_admin_user)
):
    result = await db.execute(select(ParkingSite).where(ParkingSite.code == data.code))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Site code already exists"
        )
    site = ParkingSite(**data.model_dump())
    db.add(site)
    await db.flush()
    return site

@router.get("/sites", response_model=List[SiteResponse])
async def list_sites(
    db: AsyncSession = Depends(get_db_session), 
    current_user: User = Depends(get_current_admin_user)
):
    result = await db.execute(select(ParkingSite))
    return result.scalars().all()

# --- Zones endpoints ---
@router.post("/zones", response_model=ZoneResponse, status_code=status.HTTP_201_CREATED)
async def create_zone(
    data: ZoneCreate, 
    db: AsyncSession = Depends(get_db_session), 
    current_user: User = Depends(get_current_admin_user)
):
    zone = ParkingZone(**data.model_dump())
    db.add(zone)
    await db.flush()
    return zone

@router.get("/zones", response_model=List[ZoneResponse])
async def list_zones(
    db: AsyncSession = Depends(get_db_session), 
    current_user: User = Depends(get_current_admin_user)
):
    result = await db.execute(select(ParkingZone))
    return result.scalars().all()

# --- Gates endpoints ---
@router.post("/gates", response_model=GateResponse, status_code=status.HTTP_201_CREATED)
async def create_gate(
    data: GateCreate, 
    db: AsyncSession = Depends(get_db_session), 
    current_user: User = Depends(get_current_admin_user)
):
    gate = ParkingGate(**data.model_dump())
    db.add(gate)
    await db.flush()
    return gate

@router.get("/gates", response_model=List[GateResponse])
async def list_gates(
    db: AsyncSession = Depends(get_db_session), 
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(ParkingGate))
    return result.scalars().all()

# --- Devices endpoints ---
@router.post("/", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    data: DeviceCreate, 
    db: AsyncSession = Depends(get_db_session), 
    current_user: User = Depends(get_current_admin_user)
):
    result = await db.execute(select(Device).where(Device.code == data.code))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Device code already exists"
        )
    device = Device(**data.model_dump())
    db.add(device)
    await db.flush()
    return device

@router.get("/", response_model=List[DeviceResponse])
async def list_devices(
    db: AsyncSession = Depends(get_db_session), 
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Device))
    return result.scalars().all()

# --- Cameras endpoints ---
@router.post("/cameras", response_model=CameraResponse, status_code=status.HTTP_201_CREATED)
async def create_camera(
    data: CameraCreate, 
    db: AsyncSession = Depends(get_db_session), 
    current_user: User = Depends(get_current_admin_user)
):
    result = await db.execute(select(Camera).where(Camera.code == data.code))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Camera code already exists"
        )
    camera = Camera(**data.model_dump())
    db.add(camera)
    await db.flush()
    return camera

@router.get("/cameras", response_model=List[CameraResponse])
async def list_cameras(
    db: AsyncSession = Depends(get_db_session), 
    current_user: User = Depends(get_current_admin_user)
):
    result = await db.execute(select(Camera))
    return result.scalars().all()


class DeviceControl(BaseModel):
    command: str

@router.post("/{device_id}/control")
async def control_device(
    device_id: uuid.UUID,
    data: DeviceControl,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    # Fetch device details
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Device)
        .options(selectinload(Device.gate).selectinload(ParkingGate.zone))
        .where(Device.id == device_id)
    )
    device = result.scalars().first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
        
    if data.command != "barrier.open":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported control command: {data.command}"
        )
        
    # Build open command payload
    import json
    from datetime import timezone
    from core.redis import redis_client
    
    site_id_str = str(device.gate.zone.site_id) if (device.gate and device.gate.zone) else str(uuid.uuid4())
    gate_id_str = str(device.gate_id) if device.gate_id else str(uuid.uuid4())
    
    barrier_command = {
        "command_id": str(uuid.uuid4()),
        "command_type": "barrier.open.request",
        "target_agent_id": device.agent_id or "device-agent-gate-01",
        "target_device_id": str(device.id),
        "site_id": site_id_str,
        "gate_id": gate_id_str,
        "correlation_id": str(uuid.uuid4()),
        "payload": {
            "duration_ms": 1500
        },
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Publish to Redis commands stream
    await redis_client.redis.xadd("parking.commands", {"data": json.dumps(barrier_command)})
    
    return {
        "status": "success",
        "message": f"Command '{data.command}' sent to agent '{device.agent_id}'",
        "command_id": barrier_command["command_id"]
    }


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: uuid.UUID,
    data: DeviceCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_admin_user)
):
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalars().first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(device, k, v)
    await db.commit()
    
    # Reload from DB to avoid lazy-loading expired state during serialization
    stmt = select(Device).where(Device.id == device.id)
    res = await db.execute(stmt)
    return res.scalars().first()


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    device_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_admin_user)
):
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalars().first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    await db.delete(device)
    await db.commit()
    return None


@router.put("/cameras/{camera_id}", response_model=CameraResponse)
async def update_camera(
    camera_id: uuid.UUID,
    data: CameraCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_admin_user)
):
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalars().first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    for k, v in data.model_dump(exclude_unset=True).items():
        if k == "password_secret_key" and v is not None:
            camera.password_secret_key = v
        else:
            setattr(camera, k, v)
            
    await db.commit()
    
    # Reload from DB to avoid lazy-loading expired state during serialization
    stmt = select(Camera).where(Camera.id == camera.id)
    res = await db.execute(stmt)
    return res.scalars().first()


@router.delete("/cameras/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera(
    camera_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_admin_user)
):
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalars().first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    await db.delete(camera)
    await db.commit()
    return None


