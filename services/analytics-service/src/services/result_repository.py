"""Result repository interface."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.models.schemas import JobStatus


class ResultRepository(ABC):
    """Abstract interface for analytics result storage."""
    
    @abstractmethod
    async def create_job(
        self,
        job_id: str,
        device_id: str,
        analysis_type: str,
        model_name: str,
        date_range_start: datetime,
        date_range_end: datetime,
        parameters: Optional[Dict[str, Any]],
    ) -> None:
        """Create a new job record."""
        pass
    
    @abstractmethod
    async def get_job(self, job_id: str) -> Any:
        """Get job by ID."""
        pass
    
    @abstractmethod
    async def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        progress: Optional[float] = None,
        message: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Update job status."""
        pass
    
    @abstractmethod
    async def update_job_progress(
        self,
        job_id: str,
        progress: float,
        message: str,
    ) -> None:
        """Update job progress."""
        pass
    
    @abstractmethod
    async def save_results(
        self,
        job_id: str,
        results: Dict[str, Any],
        accuracy_metrics: Optional[Dict[str, float]],
        execution_time_seconds: int,
    ) -> None:
        """Save analytics results."""
        pass
    
    @abstractmethod
    async def list_jobs(
        self,
        status: Optional[str] = None,
        device_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Any]:
        """List jobs with filtering."""
        pass
