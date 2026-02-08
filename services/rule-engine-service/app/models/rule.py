"""SQLAlchemy models for Rule Engine Service."""

from datetime import datetime
from enum import Enum
from typing import Optional, List

from sqlalchemy import String, DateTime, Float, Integer, Boolean, Text, ForeignKey, Table, Column
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid

from app.database import Base


class RuleStatus(str, Enum):
    """Rule status enumeration."""
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class RuleScope(str, Enum):
    """Rule scope enumeration."""
    ALL_DEVICES = "all_devices"
    SELECTED_DEVICES = "selected_devices"


class ConditionOperator(str, Enum):
    """Condition operator enumeration."""
    GREATER_THAN = ">"
    LESS_THAN = "<"
    EQUAL = "="
    NOT_EQUAL = "!="
    GREATER_THAN_OR_EQUAL = ">="
    LESS_THAN_OR_EQUAL = "<="


# Association table for many-to-many relationship between rules and devices
rule_devices = Table(
    "rule_devices",
    Base.metadata,
    Column("rule_id", UUID(as_uuid=True), ForeignKey("rules.rule_id", ondelete="CASCADE"), primary_key=True),
    Column("device_id", String(50), ForeignKey("devices.device_id", ondelete="CASCADE"), primary_key=True),
)


class Rule(Base):
    """Rule model for real-time telemetry evaluation.
    
    This model is designed to be multi-tenant ready. The tenant_id field
    is included for future multi-tenant support but is nullable for Phase-1.
    Supports both single-device and multi-device rules.
    """
    
    __tablename__ = "rules"
    
    # Primary key
    rule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    
    # Multi-tenant support (nullable for Phase-1)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    
    # Rule identification
    rule_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Scope configuration
    scope: Mapped[RuleScope] = mapped_column(
        String(50),
        default=RuleScope.SELECTED_DEVICES,
        nullable=False
    )
    
    # Condition configuration
    property: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    condition: Mapped[ConditionOperator] = mapped_column(String(20), nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Status
    status: Mapped[RuleStatus] = mapped_column(
        String(50),
        default=RuleStatus.ACTIVE,
        nullable=False,
        index=True
    )
    
    # Notification configuration
    notification_channels: Mapped[List[str]] = mapped_column(
        ARRAY(String(50)),
        default=list,
        nullable=False
    )
    
    # Cooldown configuration (minutes between notifications)
    cooldown_minutes: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    
    # Track last triggered time for cooldown
    last_triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Soft delete support
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    device_ids: Mapped[List[str]] = mapped_column(
        ARRAY(String(50)),
        default=list,
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<Rule(rule_id={self.rule_id}, name={self.rule_name}, status={self.status})>"
    
    def is_active(self) -> bool:
        """Check if rule is active and not deleted."""
        return self.status == RuleStatus.ACTIVE and self.deleted_at is None
    
    def is_in_cooldown(self) -> bool:
        """Check if rule is in cooldown period."""
        if self.last_triggered_at is None:
            return False
        
        from datetime import timedelta
        cooldown_end = self.last_triggered_at + timedelta(minutes=self.cooldown_minutes)
        return datetime.utcnow() < cooldown_end
    
    def applies_to_device(self, device_id: str) -> bool:
        """Check if rule applies to a specific device."""
        if self.scope == RuleScope.ALL_DEVICES:
            return True
        return device_id in self.device_ids


class Alert(Base):
    """Alert model for storing rule evaluation results.
    
    Stores alerts generated when rules are triggered.
    """
    
    __tablename__ = "alerts"
    
    # Primary key
    alert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Multi-tenant support
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    
    # Relationships
    rule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rules.rule_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    device_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Alert details
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    actual_value: Mapped[float] = mapped_column(Float, nullable=False)
    threshold_value: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        default="open",
        nullable=False,
        index=True
    )
    
    # Acknowledgment
    acknowledged_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<Alert(alert_id={self.alert_id}, rule_id={self.rule_id}, status={self.status})>"
