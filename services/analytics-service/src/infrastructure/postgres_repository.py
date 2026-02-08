"""PostgreSQL implementation of result repository."""

from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.database import AnalyticsJob
from src.models.schemas import JobStatus
from src.services.result_repository import ResultRepository
from src.utils.exceptions import JobNotFoundError

logger = structlog.get_logger()


class PostgresResultRepository(ResultRepository):
    """PostgreSQL implementation of result repository."""
    
    def __init__(self, session: AsyncSession):
        self._session = session
        self._logger = logger.bind(repository="PostgresResultRepository")
    
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
        job = AnalyticsJob(
            job_id=job_id,
            device_id=device_id,
            analysis_type=analysis_type,
            model_name=model_name,
            date_range_start=date_range_start,
            date_range_end=date_range_end,
            parameters=parameters,
            status=JobStatus.PENDING.value,
            progress=0.0,
        )
        
        self._session.add(job)
        await self._session.commit()
        
        self._logger.info("job_created", job_id=job_id, device_id=device_id)
    
    async def get_job(self, job_id: str) -> AnalyticsJob:
        """Get job by ID."""
        result = await self._session.execute(
            select(AnalyticsJob).where(AnalyticsJob.job_id == job_id)
        )
        job = result.scalar_one_or_none()
        
        if not job:
            raise JobNotFoundError(f"Job {job_id} not found")
        
        return job
    
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
        job = await self.get_job(job_id)
        
        job.status = status.value
        
        if started_at:
            job.started_at = started_at
        if completed_at:
            job.completed_at = completed_at
        if progress is not None:
            job.progress = progress
        if message:
            job.message = message
        if error_message:
            job.error_message = error_message
        
        await self._session.commit()
        
        self._logger.debug(
            "job_status_updated",
            job_id=job_id,
            status=status.value,
            progress=progress,
        )
    
    async def update_job_progress(
        self,
        job_id: str,
        progress: float,
        message: str,
    ) -> None:
        """Update job progress."""
        job = await self.get_job(job_id)
        
        job.progress = progress
        job.message = message
        
        await self._session.commit()
    
    async def save_results(
        self,
        job_id: str,
        results: Dict[str, Any],
        accuracy_metrics: Optional[Dict[str, float]],
        execution_time_seconds: int,
    ) -> None:
        """Save analytics results."""
        job = await self.get_job(job_id)
        
        job.results = results
        job.accuracy_metrics = accuracy_metrics
        job.execution_time_seconds = execution_time_seconds
        
        await self._session.commit()
        
        self._logger.info(
            "results_saved",
            job_id=job_id,
            execution_time_seconds=execution_time_seconds,
        )
    
    async def list_jobs(
        self,
        status: Optional[str] = None,
        device_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[AnalyticsJob]:
        """List jobs with filtering."""
        query = select(AnalyticsJob).order_by(AnalyticsJob.created_at.desc())
        
        if status:
            query = query.where(AnalyticsJob.status == status)
        if device_id:
            query = query.where(AnalyticsJob.device_id == device_id)
        
        query = query.limit(limit).offset(offset)
        
        result = await self._session.execute(query)
        return list(result.scalars().all())
