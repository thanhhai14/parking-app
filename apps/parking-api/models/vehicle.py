import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base

class VehicleType(Base):
    __tablename__ = "vehicle_types"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    default_fee_rule_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True) # Linked to fee_rules.id in fee.py
    color: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    vehicles: Mapped[List["Vehicle"]] = relationship("Vehicle", back_populates="vehicle_type")

class VehicleOwner(Base):
    __tablename__ = "vehicle_owners"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_code: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_type: Mapped[str] = mapped_column(String(50), nullable=False) # employee, resident, customer, etc.
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    identity_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    avatar_media_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    vehicles: Mapped[List["Vehicle"]] = relationship("Vehicle", back_populates="owner")

class Vehicle(Base):
    __tablename__ = "vehicles"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("vehicle_owners.id", ondelete="SET NULL"), nullable=True)
    vehicle_type_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("vehicle_types.id", ondelete="RESTRICT"), nullable=False)
    plate_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    normalized_plate_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    brand: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_media_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    vehicle_type: Mapped[VehicleType] = relationship("VehicleType", back_populates="vehicles")
    owner: Mapped[Optional[VehicleOwner]] = relationship("VehicleOwner", back_populates="vehicles")
