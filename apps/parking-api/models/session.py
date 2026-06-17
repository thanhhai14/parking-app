import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, func, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base

class ParkingSession(Base):
    __tablename__ = "parking_sessions"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    site_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("parking_sites.id", ondelete="RESTRICT"), nullable=False)
    zone_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("parking_zones.id", ondelete="SET NULL"), nullable=True)
    gate_entry_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("parking_gates.id", ondelete="RESTRICT"), nullable=False)
    gate_exit_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("parking_gates.id", ondelete="RESTRICT"), nullable=True)
    
    vehicle_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True)
    vehicle_type_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("vehicle_types.id", ondelete="RESTRICT"), nullable=True)
    owner_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("vehicle_owners.id", ondelete="SET NULL"), nullable=True)
    
    entry_card_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("rfid_cards.id", ondelete="SET NULL"), nullable=True)
    exit_card_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("rfid_cards.id", ondelete="SET NULL"), nullable=True)
    
    entry_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    exit_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    entry_plate_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    exit_plate_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    entry_plate_confidence: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    exit_plate_confidence: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    
    entry_overview_image_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("media_files.id", ondelete="SET NULL"), nullable=True)
    entry_plate_image_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("media_files.id", ondelete="SET NULL"), nullable=True)
    exit_overview_image_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("media_files.id", ondelete="SET NULL"), nullable=True)
    exit_plate_image_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("media_files.id", ondelete="SET NULL"), nullable=True)
    
    entry_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    exit_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    status: Mapped[str] = mapped_column(String(50), default="active", server_default="active")
    
    fee_rule_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("fee_rules.id", ondelete="SET NULL"), nullable=True)
    calculated_fee: Mapped[float] = mapped_column(Numeric(18, 2), default=0.0, server_default="0.0")
    paid_amount: Mapped[float] = mapped_column(Numeric(18, 2), default=0.0, server_default="0.0")
    payment_status: Mapped[str] = mapped_column(String(50), default="unpaid", server_default="unpaid")
    
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    warning_flags: Mapped[list] = mapped_column(JSONB, default=list, server_default="[]")
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    site: Mapped["ParkingSite"] = relationship("ParkingSite")
    zone: Mapped[Optional["ParkingZone"]] = relationship("ParkingZone")
    gate_entry: Mapped["ParkingGate"] = relationship("ParkingGate", foreign_keys=[gate_entry_id])
    gate_exit: Mapped[Optional["ParkingGate"]] = relationship("ParkingGate", foreign_keys=[gate_exit_id])
    vehicle: Mapped[Optional["Vehicle"]] = relationship("Vehicle")
    vehicle_type: Mapped[Optional["VehicleType"]] = relationship("VehicleType")
    owner: Mapped[Optional["VehicleOwner"]] = relationship("VehicleOwner")
    entry_card: Mapped[Optional["RfidCard"]] = relationship("RfidCard", foreign_keys=[entry_card_id])
    exit_card: Mapped[Optional["RfidCard"]] = relationship("RfidCard", foreign_keys=[exit_card_id])
    
    entry_overview_image: Mapped[Optional["MediaFile"]] = relationship("MediaFile", foreign_keys=[entry_overview_image_id])
    entry_plate_image: Mapped[Optional["MediaFile"]] = relationship("MediaFile", foreign_keys=[entry_plate_image_id])
    exit_overview_image: Mapped[Optional["MediaFile"]] = relationship("MediaFile", foreign_keys=[exit_overview_image_id])
    exit_plate_image: Mapped[Optional["MediaFile"]] = relationship("MediaFile", foreign_keys=[exit_plate_image_id])
    
    entry_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[entry_user_id])
    exit_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[exit_user_id])
    fee_rule: Mapped[Optional["FeeRule"]] = relationship("FeeRule")

class Payment(Base):
    __tablename__ = "payments"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parking_session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("parking_sessions.id", ondelete="CASCADE"), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False) # cash, qr_pay, card, app, e_wallet
    payment_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    reference_code: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    parking_session: Mapped[ParkingSession] = relationship("ParkingSession")
    creator: Mapped[Optional["User"]] = relationship("User")
