import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base

class RfidCard(Base):
    __tablename__ = "rfid_cards"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    card_uid: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    card_number: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    card_type: Mapped[str] = mapped_column(String(50), default="rfid", server_default="rfid") # rfid, barcode, qr, nfc, magnetic
    assigned_vehicle_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True)
    assigned_owner_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("vehicle_owners.id", ondelete="SET NULL"), nullable=True)
    issued_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expired_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active", server_default="active") # active, blocked, lost, expired, returned, inactive
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    assigned_vehicle: Mapped[Optional["Vehicle"]] = relationship("Vehicle")
    assigned_owner: Mapped[Optional["VehicleOwner"]] = relationship("VehicleOwner")
