import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, func, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base

class ParkingSite(Base):
    __tablename__ = "parking_sites"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timezone: Mapped[str] = mapped_column(String(100), default="Asia/Ho_Chi_Minh", server_default="Asia/Ho_Chi_Minh")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    zones: Mapped[List["ParkingZone"]] = relationship("ParkingZone", back_populates="site", cascade="all, delete-orphan")

class ParkingZone(Base):
    __tablename__ = "parking_zones"
    
    __table_args__ = (
        UniqueConstraint("site_id", "code", name="uq_parking_zones_site_code"),
    )
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("parking_sites.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    current_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    vehicle_type_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True) # Linked to vehicle_types.id in vehicle.py
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    site: Mapped[ParkingSite] = relationship("ParkingSite", back_populates="zones")
    gates: Mapped[List["ParkingGate"]] = relationship("ParkingGate", back_populates="zone", cascade="all, delete-orphan")

class ParkingGate(Base):
    __tablename__ = "parking_gates"
    
    __table_args__ = (
        UniqueConstraint("zone_id", "code", name="uq_parking_gates_zone_code"),
    )
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    zone_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("parking_zones.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    gate_type: Mapped[str] = mapped_column(String(50), nullable=False) # entry, exit, mixed
    direction: Mapped[str] = mapped_column(String(50), nullable=False) # in, out, both
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    zone: Mapped[ParkingZone] = relationship("ParkingZone", back_populates="gates")
