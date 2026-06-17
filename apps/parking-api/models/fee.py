import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, func, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base

class FeeRule(Base):
    __tablename__ = "fee_rules"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    vehicle_type_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("vehicle_types.id", ondelete="SET NULL"), nullable=True)
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False) # flat, hourly, daily, monthly, time_range, custom
    config: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    priority: Mapped[int] = mapped_column(Integer, default=10, server_default="10")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    vehicle_type: Mapped[Optional["VehicleType"]] = relationship("VehicleType")
