import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, func, BigInteger, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base

class MediaFile(Base):
    __tablename__ = "media_files"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bucket: Mapped[str] = mapped_column(String(255), nullable=False)
    object_key: Mapped[str] = mapped_column(Text, nullable=False)
    file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    checksum: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    media_type: Mapped[str] = mapped_column(String(50), nullable=False) # image, video, snapshot, thumbnail
    source_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # parking_session, vehicle, owner, camera, audit_log
    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    creator: Mapped[Optional["User"]] = relationship("User")
