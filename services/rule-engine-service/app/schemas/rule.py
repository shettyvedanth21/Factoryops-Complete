"""Pydantic schemas for Rule Engine Service API."""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


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


class NotificationChannel(str, Enum):
    """Notification channel enumeration."""
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"


# Base schemas
class RuleBase(BaseModel):
    """Base schema with common rule fields."""
    
    rule_name: str = Field(
        ..., 
        min_length=1, 
        max_length=255, 
        description="Human-readable rule name"
    )
    description: Optional[str] = Field(
        None, 
        max_length=1000, 
        description="Rule description"
    )
    scope: RuleScope = Field(
        default=RuleScope.SELECTED_DEVICES,
        description="Rule scope - all devices or selected devices"
    )
    property: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Property to monitor (e.g., temperature, voltage, power)"
    )
    condition: ConditionOperator = Field(
        ...,
        description="Condition operator (>, <, =, !=, >=, <=)"
    )
    threshold: float = Field(
        ...,
        description="Threshold value for condition"
    )
    notification_channels: List[NotificationChannel] = Field(
        default_factory=list,
        min_length=1,
        description="List of notification channels"
    )
    cooldown_minutes: int = Field(
        default=15,
        ge=0,
        le=1440,
        description="Cooldown period in minutes between notifications"
    )


class RuleCreate(RuleBase):
    """Schema for creating a new rule."""
    
    tenant_id: Optional[str] = Field(
        None, 
        max_length=50, 
        description="Tenant ID for multi-tenancy"
    )
    device_ids: List[str] = Field(
        default_factory=list,
        description="List of device IDs for selected_devices scope"
    )


class RuleUpdate(BaseModel):
    """Schema for updating an existing rule."""
    
    rule_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    scope: Optional[RuleScope] = None
    device_ids: Optional[List[str]] = None
    property: Optional[str] = Field(None, min_length=1, max_length=100)
    condition: Optional[ConditionOperator] = None
    threshold: Optional[float] = None
    notification_channels: Optional[List[NotificationChannel]] = None
    cooldown_minutes: Optional[int] = Field(None, ge=0, le=1440)


class RuleStatusUpdate(BaseModel):
    """Schema for updating rule status (pause/resume)."""
    
    status: RuleStatus = Field(
        ...,
        description="New rule status (active, paused, archived)"
    )


class RuleResponse(RuleBase):
    """Schema for rule response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    rule_id: UUID
    tenant_id: Optional[str] = None
    device_ids: List[str]
    status: RuleStatus
    last_triggered_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class RuleListResponse(BaseModel):
    """Schema for paginated rule list response."""
    
    success: bool = True
    data: List[RuleResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class RuleSingleResponse(BaseModel):
    """Schema for single rule response."""
    
    success: bool = True
    data: RuleResponse


class RuleStatusResponse(BaseModel):
    """Schema for rule status update response."""
    
    success: bool = True
    message: str
    rule_id: UUID
    status: RuleStatus


class RuleDeleteResponse(BaseModel):
    """Schema for rule deletion response."""
    
    success: bool = True
    message: str
    rule_id: UUID


# Evaluation schemas
class TelemetryPayload(BaseModel):
    """Schema for telemetry payload from Data Service."""
    
    device_id: str = Field(..., description="Device identifier")
    timestamp: datetime = Field(..., description="Telemetry timestamp")
    voltage: float = Field(..., description="Voltage reading")
    current: float = Field(..., description="Current reading")
    power: float = Field(..., description="Power reading")
    temperature: float = Field(..., description="Temperature reading")
    schema_version: Optional[str] = Field(None, description="Schema version")
    enrichment_status: Optional[str] = Field(None, description="Enrichment status")
    device_type: Optional[str] = Field(None, description="Device type")
    device_location: Optional[str] = Field(None, description="Device location")


class EvaluationRequest(BaseModel):
    """Schema for rule evaluation request."""
    
    device_id: str = Field(..., description="Device identifier")
    timestamp: datetime = Field(..., description="Telemetry timestamp")
    voltage: float = Field(..., description="Voltage reading")
    current: float = Field(..., description="Current reading")
    power: float = Field(..., description="Power reading")
    temperature: float = Field(..., description="Temperature reading")
    schema_version: Optional[str] = Field(None, description="Schema version")
    enrichment_status: Optional[str] = Field(None, description="Enrichment status")
    device_type: Optional[str] = Field(None, description="Device type")
    device_location: Optional[str] = Field(None, description="Device location")


class EvaluationResult(BaseModel):
    """Schema for individual rule evaluation result."""
    
    rule_id: UUID
    rule_name: str
    triggered: bool
    actual_value: float
    threshold: float
    condition: str
    message: Optional[str] = None


class EvaluationResponse(BaseModel):
    """Schema for rule evaluation response."""
    
    success: bool = True
    device_id: str
    evaluated_at: datetime
    rules_evaluated: int
    rules_triggered: int
    triggered_rules: List[EvaluationResult]


# Alert schemas
class AlertBase(BaseModel):
    """Base schema for alerts."""
    
    severity: str = Field(..., max_length=50)
    message: str = Field(...)
    actual_value: float
    threshold_value: float


class AlertResponse(AlertBase):
    """Schema for alert response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    alert_id: UUID
    rule_id: UUID
    device_id: str
    status: str
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime


# Error schema
class ErrorResponse(BaseModel):
    """Schema for error responses."""
    
    success: bool = False
    error: dict
    timestamp: datetime = Field(default_factory=datetime.utcnow)
