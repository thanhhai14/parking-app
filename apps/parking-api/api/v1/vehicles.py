from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime

from core.database import get_db_session
from models.vehicle import Vehicle, VehicleType, VehicleOwner
from api.deps import get_current_user
from models.user import User

router = APIRouter()

# --- Pydantic Schemas ---
class VehicleTypeBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    color: Optional[str] = None

class VehicleTypeCreate(VehicleTypeBase):
    pass

class VehicleTypeResponse(VehicleTypeBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    is_active: bool
    created_at: datetime

class VehicleOwnerBase(BaseModel):
    owner_code: Optional[str] = None
    full_name: str
    owner_type: str
    phone: Optional[str] = None
    email: Optional[str] = None
    identity_number: Optional[str] = None
    address: Optional[str] = None
    note: Optional[str] = None

class VehicleOwnerCreate(VehicleOwnerBase):
    pass

class VehicleOwnerResponse(VehicleOwnerBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    is_active: bool
    created_at: datetime

class VehicleBase(BaseModel):
    vehicle_type_id: uuid.UUID
    owner_id: Optional[uuid.UUID] = None
    plate_number: str
    brand: Optional[str] = None
    model: Optional[str] = None
    color: Optional[str] = None
    description: Optional[str] = None

class VehicleCreate(VehicleBase):
    pass

class VehicleResponse(VehicleBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    normalized_plate_number: str
    is_active: bool
    created_at: datetime
    vehicle_type: VehicleTypeResponse
    owner: Optional[VehicleOwnerResponse] = None

# --- Vehicle Types endpoints ---
@router.post("/types", response_model=VehicleTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle_type(
    data: VehicleTypeCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(VehicleType).where(VehicleType.code == data.code))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Vehicle type code already exists"
        )
    
    vtype = VehicleType(**data.model_dump())
    db.add(vtype)
    await db.flush()
    return vtype

@router.get("/types", response_model=List[VehicleTypeResponse])
async def list_vehicle_types(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(VehicleType).where(VehicleType.is_active == True))
    return result.scalars().all()

# --- Vehicle Owners endpoints ---
@router.post("/owners", response_model=VehicleOwnerResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle_owner(
    data: VehicleOwnerCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    if data.owner_code:
        result = await db.execute(select(VehicleOwner).where(VehicleOwner.owner_code == data.owner_code))
        if result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Owner code already exists"
            )
            
    owner = VehicleOwner(**data.model_dump())
    db.add(owner)
    await db.flush()
    return owner

@router.get("/owners", response_model=List[VehicleOwnerResponse])
async def list_vehicle_owners(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(VehicleOwner).where(VehicleOwner.is_active == True))
    return result.scalars().all()

# --- Vehicles endpoints ---
@router.post("/", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    data: VehicleCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    # Check dependencies
    result = await db.execute(select(VehicleType).where(VehicleType.id == data.vehicle_type_id))
    if not result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Vehicle type not found"
        )
        
    if data.owner_id:
        result = await db.execute(select(VehicleOwner).where(VehicleOwner.id == data.owner_id))
        if not result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Vehicle owner not found"
            )
            
    # Normalize plate number
    normalized = "".join(c for c in data.plate_number if c.isalnum()).upper()
    
    vehicle = Vehicle(
        **data.model_dump(),
        normalized_plate_number=normalized
    )
    db.add(vehicle)
    await db.flush()
    
    # Reload relation to return populated response
    stmt = select(Vehicle).where(Vehicle.id == vehicle.id)
    res = await db.execute(stmt)
    return res.scalars().first()

@router.get("/", response_model=List[VehicleResponse])
async def list_vehicles(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Vehicle).where(Vehicle.is_active == True))
    return result.scalars().all()
