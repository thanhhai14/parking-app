import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base

class Device(Base):
    __tablename__ = "devices"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gate_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("parking_gates.id", ondelete="SET NULL"), nullable=True)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    device_type: Mapped[str] = mapped_column(String(50), nullable=False) # rfid_reader, barrier, loop_detector, display_board, etc.
    connection_type: Mapped[str] = mapped_column(String(50), nullable=False) # serial, tcp, http, mqtt, Wiegrand, SDK, mock
    connection_config: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    status: Mapped[str] = mapped_column(String(50), default="offline", server_default="offline")
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    firmware_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    agent_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    gate: Mapped[Optional["ParkingGate"]] = relationship("ParkingGate")

class Camera(Base):
    __tablename__ = "cameras"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gate_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("parking_gates.id", ondelete="SET NULL"), nullable=True)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    camera_type: Mapped[str] = mapped_column(String(50), nullable=False) # rtsp, http_snapshot, usb, mock
    stream_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    snapshot_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    password_secret_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False) # overview, plate, driver, entry, exit
    status: Mapped[str] = mapped_column(String(50), default="offline", server_default="offline")
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    agent_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    config: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    gate: Mapped[Optional["ParkingGate"]] = relationship("ParkingGate")
