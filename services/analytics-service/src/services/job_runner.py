"""Job runner abstraction for executing analytics jobs."""

import asyncio
import time
from datetime import datetime
from typing import Any, Dict

import pandas as pd
import structlog

from src.models.schemas import AnalyticsRequest, AnalyticsType, JobStatus
from src.services.analytics.anomaly_detection import AnomalyDetectionPipeline
from src.services.analytics.failure_prediction import FailurePredictionPipeline
from src.services.analytics.forecasting import ForecastingPipeline
from src.services.dataset_service import DatasetService
from src.services.result_repository import ResultRepository
from src.utils.exceptions import AnalyticsError

logger = structlog.get_logger()


class JobRunner:
    """Runner for executing analytics jobs."""
    
    def __init__(
        self,
        dataset_service: DatasetService,
        result_repository: ResultRepository,
    ):
        self._dataset_service = dataset_service
        self._result_repo = result_repository
        self._logger = logger.bind(service="JobRunner")
        
        # Initialize pipelines
        self._pipelines = {
            AnalyticsType.ANOMALY: AnomalyDetectionPipeline(),
            AnalyticsType.PREDICTION: FailurePredictionPipeline(),
            AnalyticsType.FORECAST: ForecastingPipeline(),
        }
    
    async def run_job(self, job_id: str, request: AnalyticsRequest) -> None:
        """
        Execute an analytics job.
        
        Args:
            job_id: Unique job identifier
            request: Analytics request parameters
        """
        start_time = time.time()
        
        self._logger.info(
            "job_started",
            job_id=job_id,
            analysis_type=request.analysis_type.value,
            model_name=request.model_name,
        )
        
        try:
            # Update status to running
            await self._result_repo.update_job_status(
                job_id=job_id,
                status=JobStatus.RUNNING,
                started_at=datetime.utcnow(),
            )
            
            # Load dataset from S3
            await self._result_repo.update_job_progress(job_id, 10.0, "Loading dataset")
            df = await self._dataset_service.load_dataset(
                device_id=request.device_id,
                start_time=request.start_time,
                end_time=request.end_time,
            )
            
            # Get appropriate pipeline
            pipeline = self._pipelines.get(request.analysis_type)
            if not pipeline:
                raise AnalyticsError(
                    f"Unknown analysis type: {request.analysis_type}"
                )
            
            # Run analytics pipeline
            await self._result_repo.update_job_progress(job_id, 30.0, "Preparing features")
            
            # Split data for train/test
            train_df, test_df = pipeline.prepare_data(df, request.parameters)
            
            await self._result_repo.update_job_progress(job_id, 50.0, "Training model")
            model = pipeline.train(train_df, request.model_name, request.parameters)
            
            await self._result_repo.update_job_progress(job_id, 75.0, "Running inference")
            results = pipeline.predict(test_df, model, request.parameters)
            
            await self._result_repo.update_job_progress(job_id, 90.0, "Calculating metrics")
            metrics = pipeline.evaluate(test_df, results, request.parameters)
            
            # Save results
            execution_time = int(time.time() - start_time)
            await self._result_repo.save_results(
                job_id=job_id,
                results=results,
                accuracy_metrics=metrics,
                execution_time_seconds=execution_time,
            )
            
            await self._result_repo.update_job_status(
                job_id=job_id,
                status=JobStatus.COMPLETED,
                completed_at=datetime.utcnow(),
                progress=100.0,
                message="Analysis completed successfully",
            )
            
            self._logger.info(
                "job_completed",
                job_id=job_id,
                execution_time_seconds=execution_time,
            )
            
        except Exception as e:
            self._logger.error(
                "job_failed",
                job_id=job_id,
                error=str(e),
                exc_info=True,
            )
            
            await self._result_repo.update_job_status(
                job_id=job_id,
                status=JobStatus.FAILED,
                completed_at=datetime.utcnow(),
                message="Job failed",
                error_message=str(e),
            )
            
            raise AnalyticsError(f"Job execution failed: {e}") from e
