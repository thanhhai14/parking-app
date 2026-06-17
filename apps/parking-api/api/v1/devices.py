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
from api.deps import get_current_user
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
    current_user: User = Depends(get_current_user)
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
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(ParkingSite))
    return result.scalars().all()

# --- Zones endpoints ---
@router.post("/zones", response_model=ZoneResponse, status_code=status.HTTP_201_CREATED)
async def create_zone(
    data: ZoneCreate, 
    db: AsyncSession = Depends(get_db_session), 
    current_user: User = Depends(get_current_user)
):
    zone = ParkingZone(**data.model_dump())
    db.add(zone)
    await db.flush()
    return zone

@router.get("/zones", response_model=List[ZoneResponse])
async def list_zones(
    db: AsyncSession = Depends(get_db_session), 
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(ParkingZone))
    return result.scalars().all()

# --- Gates endpoints ---
@router.post("/gates", response_model=GateResponse, status_code=status.HTTP_201_CREATED)
async def create_gate(
    data: GateCreate, 
    db: AsyncSession = Depends(get_db_session), 
    current_user: User = Depends(get_current_user)
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
    current_user: User = Depends(get_current_user)
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
    current_user: User = Depends(get_current_user)
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
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Camera))
    return result.scalars().all()
