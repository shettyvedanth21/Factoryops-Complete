"""Dataset access service - reads from S3 only."""

import io
from datetime import datetime
from typing import Optional

import pandas as pd
import structlog

from src.infrastructure.s3_client import S3Client
from src.utils.exceptions import DatasetNotFoundError, DatasetReadError

logger = structlog.get_logger()


class DatasetService:
    """Service for accessing datasets from S3."""
    
    def __init__(self, s3_client: S3Client):
        self._s3 = s3_client
        self._logger = logger.bind(service="DatasetService")
    
    async def load_dataset(
        self,
        device_id: str,
        start_time: datetime,
        end_time: datetime,
        s3_key: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Load dataset from S3.
        
        Args:
            device_id: Device identifier
            start_time: Start of date range
            end_time: End of date range
            s3_key: Optional specific S3 key, otherwise constructed from params
            
        Returns:
            DataFrame with telemetry data
            
        Raises:
            DatasetNotFoundError: If dataset doesn't exist in S3
            DatasetReadError: If reading dataset fails
        """
        if s3_key is None:
            s3_key = self._construct_s3_key(device_id, start_time, end_time)
        
        self._logger.info(
            "loading_dataset",
            device_id=device_id,
            s3_key=s3_key,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
        )
        
        try:
            data = await self._s3.download_file(s3_key)
            
            # Read parquet from bytes
            df = pd.read_parquet(io.BytesIO(data))
            
            self._logger.info(
                "dataset_loaded",
                device_id=device_id,
                rows=len(df),
                columns=list(df.columns),
            )
            
            return df
            
        except Exception as e:
            self._logger.error(
                "dataset_load_failed",
                device_id=device_id,
                s3_key=s3_key,
                error=str(e),
            )
            if "Not Found" in str(e) or "NoSuchKey" in str(e):
                raise DatasetNotFoundError(f"Dataset not found: {s3_key}")
            raise DatasetReadError(f"Failed to read dataset: {e}") from e
    
    def _construct_s3_key(
        self,
        device_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> str:
        """Construct S3 key from parameters."""
        return (
            f"datasets/{device_id}/"
            f"{start_time.strftime('%Y%m%d')}_{end_time.strftime('%Y%m%d')}.parquet"
        )
    
    async def list_available_datasets(
        self,
        device_id: str,
        prefix: Optional[str] = None,
    ) -> list:
        """List available datasets for a device."""
        if prefix is None:
            prefix = f"datasets/{device_id}/"
        
        return await self._s3.list_objects(prefix)
