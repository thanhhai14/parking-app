from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime, timezone

from core.database import get_db_session
from models.card import RfidCard
from models.vehicle import Vehicle, VehicleOwner
from api.deps import get_current_user
from models.user import User

router = APIRouter()

# --- Pydantic Schemas ---
class RfidCardBase(BaseModel):
    card_uid: str
    card_number: Optional[str] = None
    card_type: str = "rfid"
    assigned_vehicle_id: Optional[uuid.UUID] = None
    assigned_owner_id: Optional[uuid.UUID] = None
    expired_at: Optional[datetime] = None
    status: str = "active"
    note: Optional[str] = None

class RfidCardCreate(RfidCardBase):
    pass

class RfidCardResponse(RfidCardBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    issued_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

# --- Endpoints ---
@router.post("/", response_model=RfidCardResponse, status_code=status.HTTP_201_CREATED)
async def create_card(
    data: RfidCardCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    # Check unique UID
    result = await db.execute(select(RfidCard).where(RfidCard.card_uid == data.card_uid))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Card UID already exists"
        )
        
    # Check relation dependencies
    if data.assigned_vehicle_id:
        result = await db.execute(select(Vehicle).where(Vehicle.id == data.assigned_vehicle_id))
        if not result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Assigned vehicle not found"
            )
            
    if data.assigned_owner_id:
        result = await db.execute(select(VehicleOwner).where(VehicleOwner.id == data.assigned_owner_id))
        if not result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Assigned owner not found"
            )
            
    card = RfidCard(
        **data.model_dump(),
        issued_at=datetime.now(timezone.utc) if data.status == "active" else None
    )
    db.add(card)
    await db.flush()
    return card

@router.get("/", response_model=List[RfidCardResponse])
async def list_cards(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(RfidCard))
    return result.scalars().all()

@router.get("/uid/{card_uid}", response_model=RfidCardResponse)
async def get_card_by_uid(
    card_uid: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(RfidCard).where(RfidCard.card_uid == card_uid))
    card = result.scalars().first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Card not found"
        )
    return card

@router.get("/{card_id}", response_model=RfidCardResponse)
async def get_card(
    card_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(RfidCard).where(RfidCard.id == card_id))
    card = result.scalars().first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Card not found"
        )
    return card
