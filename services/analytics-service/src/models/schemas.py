"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class AnalyticsType(str, Enum):
    """Types of analytics supported."""
    ANOMALY = "anomaly"
    PREDICTION = "prediction"
    FORECAST = "forecast"


class JobStatus(str, Enum):
    """Job execution statuses."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalyticsRequest(BaseModel):
    """Request to run analytics job."""
    
    device_id: str = Field(..., description="Device identifier (e.g., D1)")
    start_time: datetime = Field(..., description="Start of analysis period")
    end_time: datetime = Field(..., description="End of analysis period")
    analysis_type: AnalyticsType = Field(..., description="Type of analysis to perform")
    model_name: str = Field(..., description="ML model to use")
    parameters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Model-specific parameters",
    )
    
    @validator("end_time")
    def end_time_after_start(cls, v: datetime, values: Dict[str, Any]) -> datetime:
        """Ensure end_time is after start_time."""
        if "start_time" in values and v <= values["start_time"]:
            raise ValueError("end_time must be after start_time")
        return v
    
    @validator("model_name")
    def validate_model_name(cls, v: str, values: Dict[str, Any]) -> str:
        """Validate model name based on analysis type."""
        analysis_type = values.get("analysis_type")
        
        valid_models = {
            AnalyticsType.ANOMALY: ["isolation_forest", "autoencoder"],
            AnalyticsType.PREDICTION: ["random_forest", "gradient_boosting"],
            AnalyticsType.FORECAST: ["prophet", "arima"],
        }
        
        if analysis_type and v not in valid_models.get(analysis_type, []):
            raise ValueError(
                f"Model '{v}' not supported for {analysis_type}. "
                f"Supported: {valid_models.get(analysis_type, [])}"
            )
        return v


class AnalyticsJobResponse(BaseModel):
    """Response after submitting analytics job."""
    
    job_id: str
    status: JobStatus
    message: str


class JobStatusResponse(BaseModel):
    """Job status response."""
    
    job_id: str
    status: JobStatus
    progress: Optional[float] = Field(None, ge=0, le=100)
    message: Optional[str] = None
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class AnalyticsResultsResponse(BaseModel):
    """Analytics results response."""
    
    job_id: str
    status: JobStatus
    device_id: str
    analysis_type: AnalyticsType
    model_name: str
    date_range_start: datetime
    date_range_end: datetime
    results: Dict[str, Any]
    accuracy_metrics: Optional[Dict[str, float]] = None
    execution_time_seconds: Optional[int] = None
    completed_at: Optional[datetime] = None


class SupportedModelsResponse(BaseModel):
    """Supported models by analysis type."""
    
    anomaly_detection: List[str]
    failure_prediction: List[str]
    forecasting: List[str]


class ErrorResponse(BaseModel):
    """Error response schema."""
    
    success: bool = False
    error: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
