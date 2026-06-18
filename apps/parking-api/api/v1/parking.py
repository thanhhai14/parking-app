from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
import uuid
import random
from datetime import datetime, timezone
from pydantic import BaseModel
from typing import Optional, List

from core.database import get_db_session
from models.card import RfidCard
from models.parking_lot import ParkingGate, ParkingZone, ParkingSite
from models.session import ParkingSession
from models.vehicle import Vehicle, VehicleType
from models.fee import FeeRule
from services.pricing_service import PricingEngine

router = APIRouter()

# --- Pydantic Schemas ---
class CheckInRequest(BaseModel):
    card_uid: str
    plate_number: Optional[str] = None
    gate_code: str
    overview_image_id: Optional[uuid.UUID] = None
    plate_image_id: Optional[uuid.UUID] = None

class CheckOutRequest(BaseModel):
    card_uid: str
    plate_number: Optional[str] = None
    gate_code: str
    overview_image_id: Optional[uuid.UUID] = None
    plate_image_id: Optional[uuid.UUID] = None

class SessionResponse(BaseModel):
    id: uuid.UUID
    session_code: str
    card_uid: str
    entry_time: datetime
    exit_time: Optional[datetime] = None
    entry_plate_number: Optional[str] = None
    exit_plate_number: Optional[str] = None
    calculated_fee: float
    status: str
    payment_status: str

# --- Helper to generate session code ---
def generate_session_code() -> str:
    now_str = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    rand_num = random.randint(1000, 9999)
    return f"PK-{now_str}-{rand_num}"

# --- Endpoints ---
@router.post("/check-in", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def check_in(
    data: CheckInRequest,
    db: AsyncSession = Depends(get_db_session)
):
    # 1. Fetch active card details
    card_query = await db.execute(
        select(RfidCard)
        .options(selectinload(RfidCard.assigned_vehicle))
        .where(RfidCard.card_uid == data.card_uid)
    )
    card = card_query.scalars().first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Card not found"
        )
    if card.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Card is not active (status: {card.status})"
        )
        
    # 2. Fetch gate details
    gate_query = await db.execute(
        select(ParkingGate)
        .options(selectinload(ParkingGate.zone).selectinload(ParkingZone.site))
        .where(ParkingGate.code == data.gate_code)
    )
    gate = gate_query.scalars().first()
    if not gate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Gate not found"
        )
    if gate.direction not in ["in", "both"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Gate is not an entry gate"
        )
        
    # 3. Check for existing active session to prevent double check-in
    active_session_query = await db.execute(
        select(ParkingSession)
        .where(ParkingSession.entry_card_id == card.id)
        .where(ParkingSession.status == "active")
    )
    if active_session_query.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Card is already checked in"
        )
        
    # 4. Resolve vehicle details
    vehicle_id = None
    vehicle_type_id = None
    owner_id = None
    
    if card.assigned_vehicle:
        vehicle_id = card.assigned_vehicle.id
        vehicle_type_id = card.assigned_vehicle.vehicle_type_id
        owner_id = card.assigned_vehicle.owner_id
    elif card.assigned_owner_id:
        owner_id = card.assigned_owner_id
        
    # 5. Create Parking Session
    session = ParkingSession(
        session_code=generate_session_code(),
        site_id=gate.zone.site_id,
        zone_id=gate.zone_id,
        gate_entry_id=gate.id,
        vehicle_id=vehicle_id,
        vehicle_type_id=vehicle_type_id,
        owner_id=owner_id,
        entry_card_id=card.id,
        entry_time=datetime.now(timezone.utc),
        entry_plate_number=data.plate_number,
        entry_overview_image_id=data.overview_image_id,
        entry_plate_image_id=data.plate_image_id,
        status="active"
    )
    db.add(session)
    await db.flush()
    
    return SessionResponse(
        id=session.id,
        session_code=session.session_code,
        card_uid=card.card_uid,
        entry_time=session.entry_time,
        entry_plate_number=session.entry_plate_number,
        calculated_fee=0.0,
        status=session.status,
        payment_status=session.payment_status
    )

@router.post("/check-out", response_model=SessionResponse)
async def check_out(
    data: CheckOutRequest,
    db: AsyncSession = Depends(get_db_session)
):
    # 1. Fetch card details
    card_query = await db.execute(
        select(RfidCard).where(RfidCard.card_uid == data.card_uid)
    )
    card = card_query.scalars().first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Card not found"
        )
        
    # 2. Fetch gate details
    gate_query = await db.execute(
        select(ParkingGate).where(ParkingGate.code == data.gate_code)
    )
    gate = gate_query.scalars().first()
    if not gate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Gate not found"
        )
    if gate.direction not in ["out", "both"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Gate is not an exit gate"
        )
        
    # 3. Fetch active session
    session_query = await db.execute(
        select(ParkingSession)
        .where(ParkingSession.entry_card_id == card.id)
        .where(ParkingSession.status == "active")
    )
    session = session_query.scalars().first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="No active parking session found for this card"
        )
        
    # 4. Calculate fee
    exit_time = datetime.now(timezone.utc)
    
    # Resolve pricing rule (search matching rule for vehicle type)
    rule_type = "hourly"
    rule_config = {
        "free_grace_minutes": 15,
        "first_hours": 4,
        "first_amount": 5000.0,
        "next_hour_amount": 2000.0,
        "max_daily_amount": 30000.0
    }
    
    if session.vehicle_type_id:
        rule_query = await db.execute(
            select(FeeRule)
            .where(FeeRule.vehicle_type_id == session.vehicle_type_id)
            .where(FeeRule.is_active == True)
            .order_repr(FeeRule.priority.desc()) if hasattr(FeeRule, 'priority') else select(FeeRule).where(FeeRule.vehicle_type_id == session.vehicle_type_id)
        )
        # Order by priority descending if exists
        rule_query = await db.execute(
            select(FeeRule)
            .where(FeeRule.vehicle_type_id == session.vehicle_type_id)
            .where(FeeRule.is_active == True)
            .order_by(FeeRule.priority.desc())
        )
        rule = rule_query.scalars().first()
        if rule:
            rule_type = rule.rule_type
            rule_config = rule.config
            session.fee_rule_id = rule.id
            
    # Calculate fee using the pricing engine
    fee = PricingEngine.calculate_fee(
        entry_time=session.entry_time,
        exit_time=exit_time,
        rule_type=rule_type,
        config=rule_config
    )
    
    # 5. Update Parking Session
    session.exit_time = exit_time
    session.gate_exit_id = gate.id
    session.exit_plate_number = data.plate_number
    session.exit_overview_image_id = data.overview_image_id
    session.exit_plate_image_id = data.plate_image_id
    session.exit_card_id = card.id
    session.calculated_fee = fee
    session.status = "completed"
    session.payment_status = "paid" if fee == 0.0 else "unpaid"
    
    return SessionResponse(
        id=session.id,
        session_code=session.session_code,
        card_uid=card.card_uid,
        entry_time=session.entry_time,
        exit_time=session.exit_time,
        entry_plate_number=session.entry_plate_number,
        exit_plate_number=session.exit_plate_number,
        calculated_fee=session.calculated_fee,
        status=session.status,
        payment_status=session.payment_status
    )


@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(
    plate_number: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
):
    query = select(ParkingSession)
    if plate_number:
        query = query.where(
            (ParkingSession.entry_plate_number.ilike(f"%{plate_number}%")) |
            (ParkingSession.exit_plate_number.ilike(f"%{plate_number}%"))
        )
    if status:
        query = query.where(ParkingSession.status == status)
        
    query = query.order_by(ParkingSession.entry_time.desc())
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    response_items = []
    for s in sessions:
        # Resolve card_uid from entry_card_id
        card_uid = "unknown"
        if s.entry_card_id:
            card_query = await db.execute(select(RfidCard).where(RfidCard.id == s.entry_card_id))
            card = card_query.scalars().first()
            if card:
                card_uid = card.card_uid
                
        response_items.append(
            SessionResponse(
                id=s.id,
                session_code=s.session_code,
                card_uid=card_uid,
                entry_time=s.entry_time,
                exit_time=s.exit_time,
                entry_plate_number=s.entry_plate_number,
                exit_plate_number=s.exit_plate_number,
                calculated_fee=float(s.calculated_fee),
                status=s.status,
                payment_status=s.payment_status
            )
        )
    return response_items

