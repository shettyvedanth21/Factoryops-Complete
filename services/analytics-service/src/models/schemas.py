"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator


class AnalyticsType(str, Enum):
    ANOMALY = "anomaly"
    PREDICTION = "prediction"
    FORECAST = "forecast"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalyticsRequest(BaseModel):
    """
    Analytics job request.

    Either:
      - dataset_key
    OR
      - start_time + end_time
    must be provided.
    """

    device_id: str

    # NEW
    dataset_key: Optional[str] = None

    # Old mode (still supported)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    analysis_type: AnalyticsType
    model_name: str
    parameters: Optional[Dict[str, Any]] = None

    @model_validator(mode="after")
    def validate_dataset_or_timerange(self):
        has_dataset = self.dataset_key is not None
        has_range = self.start_time is not None and self.end_time is not None

        if has_dataset and has_range:
            raise ValueError(
                "Provide either dataset_key OR start_time/end_time, not both"
            )

        if not has_dataset and not has_range:
            raise ValueError(
                "Either dataset_key or start_time/end_time must be provided"
            )

        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValueError("end_time must be after start_time")

        return self


class AnalyticsJobResponse(BaseModel):
    job_id: str
    status: JobStatus
    message: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: Optional[float] = Field(None, ge=0, le=100)
    message: Optional[str] = None
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class AnalyticsResultsResponse(BaseModel):
    job_id: str
    status: JobStatus
    device_id: str
    analysis_type: AnalyticsType
    model_name: str

    date_range_start: Optional[datetime]
    date_range_end: Optional[datetime]

    results: Dict[str, Any]
    accuracy_metrics: Optional[Dict[str, float]] = None
    execution_time_seconds: Optional[int] = None
    completed_at: Optional[datetime] = None


class SupportedModelsResponse(BaseModel):
    anomaly_detection: List[str]
    failure_prediction: List[str]
    forecasting: List[str]


class ErrorResponse(BaseModel):
    success: bool = False
    error: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)