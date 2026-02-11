"""Database models for SQLAlchemy."""

from uuid import uuid4

from sqlalchemy import Column, DateTime, Float, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class AnalyticsJob(Base):
    """Analytics job model."""

    __tablename__ = "analytics_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    job_id = Column(String(100), unique=True, nullable=False, index=True)
    device_id = Column(String(50), nullable=False, index=True)
    analysis_type = Column(String(50), nullable=False)
    model_name = Column(String(100), nullable=False)

    date_range_start = Column(DateTime(timezone=True), nullable=False)
    date_range_end = Column(DateTime(timezone=True), nullable=False)

    parameters = Column(JSONB, nullable=True)

    # Execution status
    status = Column(String(50), nullable=False, default="pending")
    progress = Column(Float, nullable=True)
    message = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    # Results
    results = Column(JSONB, nullable=True)
    accuracy_metrics = Column(JSONB, nullable=True)
    execution_time_seconds = Column(Integer, nullable=True)

    # ✅ PERMANENT FIX — DB must generate timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        Index("idx_analytics_jobs_status", "status"),
        Index("idx_analytics_jobs_created_at", "created_at"),
    )