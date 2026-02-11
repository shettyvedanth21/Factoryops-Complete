"""Job runner abstraction for executing analytics jobs."""

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

        self._pipelines = {
            AnalyticsType.ANOMALY: AnomalyDetectionPipeline(),
            AnalyticsType.PREDICTION: FailurePredictionPipeline(),
            AnalyticsType.FORECAST: ForecastingPipeline(),
        }

    async def run_job(self, job_id: str, request: AnalyticsRequest) -> None:
        start_clock = time.time()

        self._logger.info(
            "job_started",
            job_id=job_id,
            analysis_type=request.analysis_type.value,
            model_name=request.model_name,
        )

        try:
            await self._result_repo.update_job_status(
                job_id=job_id,
                status=JobStatus.RUNNING,
                started_at=datetime.utcnow(),
            )

            await self._result_repo.update_job_progress(
                job_id, 10.0, "Loading dataset"
            )

            # -------------------------------------------------------
            # Dataset loading (supports explicit dataset_key)
            # -------------------------------------------------------
            df = await self._dataset_service.load_dataset(
                device_id=request.device_id,
                start_time=request.start_time,
                end_time=request.end_time,
                s3_key=getattr(request, "dataset_key", None),
            )

            pipeline = self._pipelines.get(request.analysis_type)
            if not pipeline:
                raise AnalyticsError(
                    f"Unknown analysis type: {request.analysis_type}"
                )

            await self._result_repo.update_job_progress(
                job_id, 30.0, "Preparing features"
            )

            train_df, test_df = pipeline.prepare_data(
                df, request.parameters
            )

            await self._result_repo.update_job_progress(
                job_id, 50.0, "Training model"
            )

            model = pipeline.train(
                train_df, request.model_name, request.parameters
            )

            await self._result_repo.update_job_progress(
                job_id, 75.0, "Running inference"
            )

            results = pipeline.predict(
                test_df, model, request.parameters
            )

            await self._result_repo.update_job_progress(
                job_id, 90.0, "Calculating metrics"
            )

            metrics = pipeline.evaluate(
                test_df, results, request.parameters
            )

            # ---------------------------------------------------------
            # Attach timestamp aligned points for anomaly jobs
            # ---------------------------------------------------------
            if request.analysis_type == AnalyticsType.ANOMALY:
                self._attach_anomaly_points(results, test_df)

            execution_time = int(time.time() - start_clock)

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

    def _attach_anomaly_points(
        self,
        results: Dict[str, Any],
        test_df: pd.DataFrame,
    ) -> None:
        """
        Attach timestamp-aligned anomaly points to results.

        Produces:
        results["points"] = [
            {
                "timestamp": ...,
                "anomaly_score": ...,
                "is_anomaly": ...
            }
        ]
        """

        # ---------------------------------------------------------
        # Robust timestamp column detection
        # ---------------------------------------------------------
        if "timestamp" in test_df.columns:
            ts_col = "timestamp"
        elif "_time" in test_df.columns:
            ts_col = "_time"
        else:
            raise AnalyticsError(
                "No timestamp column found in dataset (expected 'timestamp' or '_time')"
            )

        anomaly_scores = results.get("anomaly_score")
        is_anomaly = results.get("is_anomaly")

        if anomaly_scores is None or is_anomaly is None:
            raise AnalyticsError(
                "Anomaly results missing 'anomaly_score' or 'is_anomaly'"
            )

        if len(test_df) != len(anomaly_scores):
            raise AnalyticsError(
                "Mismatch between test data length and anomaly result length"
            )

        timestamps = pd.to_datetime(
            test_df[ts_col],
            utc=True,
            errors="coerce",
        )

        if timestamps.isna().any():
            raise AnalyticsError(
                "Invalid timestamp values found in test dataset"
            )

        points = []

        for ts, score, flag in zip(
            timestamps,
            anomaly_scores,
            is_anomaly,
        ):
            points.append(
                {
                    "timestamp": ts.isoformat(),
                    "anomaly_score": float(score),
                    "is_anomaly": bool(flag),
                }
            )

        results["points"] = points