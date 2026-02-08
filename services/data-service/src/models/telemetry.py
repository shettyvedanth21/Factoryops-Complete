"""Data models for telemetry and related entities."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, validator


class EnrichmentStatus(str, Enum):
    """Device metadata enrichment status."""
    
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


class DeviceMetadata(BaseModel):
    """Device metadata from device service."""
    
    id: str = Field(..., description="Device ID")
    name: str = Field(..., description="Device name")
    type: str = Field(..., description="Device type")
    location: Optional[str] = Field(None, description="Device location")
    status: str = Field(..., description="Device status")
    health_score: Optional[float] = Field(None, ge=0, le=100, description="Health score")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class TelemetryPayload(BaseModel):
    """
    Telemetry payload from MQTT.
    
    Schema version v1 fields:
    - device_id: Device identifier
    - timestamp: ISO 8601 timestamp
    - voltage: Voltage in V (200-250)
    - current: Current in A (0-2)
    - power: Power in W (0-500)
    - temperature: Temperature in °C (20-80)
    - schema_version: Schema version ("v1")
    """
    
    device_id: str = Field(..., description="Device identifier")
    timestamp: datetime = Field(..., description="Measurement timestamp")
    voltage: float = Field(..., ge=200.0, le=250.0, description="Voltage in V")
    current: float = Field(..., ge=0.0, le=2.0, description="Current in A")
    power: float = Field(..., ge=0.0, le=500.0, description="Power in W")
    temperature: float = Field(..., ge=20.0, le=80.0, description="Temperature in °C")
    schema_version: str = Field(default="v1", description="Schema version")
    
    # Enrichment fields (not part of incoming payload)
    enrichment_status: EnrichmentStatus = Field(
        default=EnrichmentStatus.PENDING,
        description="Metadata enrichment status"
    )
    device_metadata: Optional[DeviceMetadata] = Field(
        None, 
        description="Enriched device metadata"
    )
    enriched_at: Optional[datetime] = Field(
        None, 
        description="When enrichment was completed"
    )
    
    @validator("schema_version")
    def validate_schema_version(cls, v: str) -> str:
        """Validate schema version is supported."""
        if v != "v1":
            raise ValueError(f"Unsupported schema version: {v}. Only 'v1' is supported.")
        return v
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TelemetryPoint(BaseModel):
    """Single telemetry data point for queries."""
    
    timestamp: datetime = Field(..., description="Measurement timestamp")
    device_id: str = Field(..., description="Device ID")
    voltage: Optional[float] = Field(None, description="Voltage in V")
    current: Optional[float] = Field(None, description="Current in A")
    power: Optional[float] = Field(None, description="Power in W")
    temperature: Optional[float] = Field(None, description="Temperature in °C")
    schema_version: str = Field(default="v1", description="Schema version")
    enrichment_status: EnrichmentStatus = Field(
        default=EnrichmentStatus.PENDING,
        description="Enrichment status"
    )


class TelemetryQuery(BaseModel):
    """Query parameters for telemetry data."""
    
    device_id: str = Field(..., description="Device ID")
    start_time: Optional[datetime] = Field(None, description="Start time")
    end_time: Optional[datetime] = Field(None, description="End time")
    fields: Optional[list[str]] = Field(None, description="Fields to retrieve")
    aggregate: Optional[str] = Field(None, description="Aggregation function")
    interval: Optional[str] = Field(None, description="Aggregation interval")
    limit: int = Field(default=1000, ge=1, le=10000, description="Max results")
    
    @validator("end_time")
    def validate_time_range(cls, v: Optional[datetime], values: Dict[str, Any]) -> Optional[datetime]:
        """Validate end_time is after start_time."""
        start_time = values.get("start_time")
        if v and start_time and v <= start_time:
            raise ValueError("end_time must be after start_time")
        return v


class TelemetryStats(BaseModel):
    """Aggregated telemetry statistics."""
    
    device_id: str = Field(..., description="Device ID")
    start_time: datetime = Field(..., description="Stats start time")
    end_time: datetime = Field(..., description="Stats end time")
    
    # Voltage stats
    voltage_min: Optional[float] = Field(None, description="Min voltage")
    voltage_max: Optional[float] = Field(None, description="Max voltage")
    voltage_avg: Optional[float] = Field(None, description="Avg voltage")
    
    # Current stats
    current_min: Optional[float] = Field(None, description="Min current")
    current_max: Optional[float] = Field(None, description="Max current")
    current_avg: Optional[float] = Field(None, description="Avg current")
    
    # Power stats
    power_min: Optional[float] = Field(None, description="Min power")
    power_max: Optional[float] = Field(None, description="Max power")
    power_avg: Optional[float] = Field(None, description="Avg power")
    power_total: Optional[float] = Field(None, description="Total power")
    
    # Temperature stats
    temperature_min: Optional[float] = Field(None, description="Min temperature")
    temperature_max: Optional[float] = Field(None, description="Max temperature")
    temperature_avg: Optional[float] = Field(None, description="Avg temperature")
    
    # Metadata
    data_points: int = Field(..., description="Number of data points")
    

class DLQEntry(BaseModel):
    """Dead Letter Queue entry."""
    
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Entry timestamp")
    original_payload: Dict[str, Any] = Field(..., description="Original message payload")
    error_type: str = Field(..., description="Error classification")
    error_message: str = Field(..., description="Error details")
    retry_count: int = Field(default=0, description="Number of retries attempted")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
