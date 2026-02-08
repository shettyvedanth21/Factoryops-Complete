"""S3 writer for exporting datasets to Amazon S3.

Handles upload of telemetry datasets in Parquet or CSV format
with proper partitioning and metadata.
"""

import io
from datetime import datetime, timezone
from typing import Optional

import aioboto3
import pandas as pd
from botocore.exceptions import ClientError

from config import Settings
from logging_config import get_logger
from models import DatasetMetadata, ExportBatch, ExportFormat, TelemetryData

logger = get_logger(__name__)


class S3Writer:
    """Async S3 writer for telemetry datasets."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self._session: Optional[aioboto3.Session] = None
    
    def initialize(self) -> None:
        """Initialize S3 session."""
        self._session = aioboto3.Session(
            aws_access_key_id=self.settings.aws_access_key_id or None,
            aws_secret_access_key=self.settings.aws_secret_access_key or None,
            region_name=self.settings.s3_region,
        )
        logger.info(
            "S3 session initialized",
            extra={
                "bucket": self.settings.s3_bucket,
                "region": self.settings.s3_region,
            }
        )
    
    async def close(self) -> None:
        """Close S3 session."""
        logger.info("S3 writer closed")
    
    def _build_s3_key(
        self,
        device_id: str,
        timestamp: datetime,
        format: ExportFormat
    ) -> str:
        """Build S3 key with partitioning scheme.
        
        Partition structure: s3://bucket/prefix/device_id/YYYY/MM/DD/data.parquet
        
        Args:
            device_id: Device identifier
            timestamp: Export timestamp for partitioning
            format: Export format
            
        Returns:
            S3 key string
        """
        date_partition = timestamp.strftime("%Y/%m/%d")
        timestamp_str = timestamp.strftime("%H%M%S")
        extension = "parquet" if format == ExportFormat.PARQUET else "csv"
        
        return (
            f"{self.settings.s3_prefix}/"
            f"device_id={device_id}/"
            f"date={date_partition}/"
            f"export_{timestamp_str}.{extension}"
        )
    
    def _convert_to_dataframe(self, records: list[TelemetryData]) -> pd.DataFrame:
        """Convert telemetry records to DataFrame.
        
        Args:
            records: List of telemetry data points
            
        Returns:
            Pandas DataFrame
        """
        data = []
        for record in records:
            data.append({
                "timestamp": record.timestamp,
                "device_id": record.device_id,
                "device_type": record.device_type,
                "location": record.location,
                "voltage": record.voltage,
                "current": record.current,
                "power": record.power,
                "temperature": record.temperature,
            })
        
        df = pd.DataFrame(data)
        
        # Add derived features for analytics
        df["hour"] = df["timestamp"].dt.hour
        df["day_of_week"] = df["timestamp"].dt.dayofweek
        df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
        
        # Calculate power factor if voltage and current exist
        if "voltage" in df.columns and "current" in df.columns and "power" in df.columns:
            apparent_power = df["voltage"] * df["current"]
            df["power_factor"] = (df["power"] / apparent_power).clip(0, 1)
        
        return df
    
    async def write_batch(
        self,
        batch: ExportBatch,
        format: ExportFormat = ExportFormat.PARQUET
    ) -> DatasetMetadata:
        """Write a batch of telemetry data to S3.
        
        Args:
            batch: Export batch containing telemetry records
            format: Export format (parquet or csv)
            
        Returns:
            DatasetMetadata with upload details
        """
        if not batch.records:
            raise ValueError("Cannot write empty batch")
        
        # Convert to DataFrame
        df = self._convert_to_dataframe(batch.records)
        
        # Build S3 key with partitioning
        s3_key = self._build_s3_key(batch.device_id, batch.start_time, format)
        
        # Convert DataFrame to bytes
        buffer = io.BytesIO()
        
        if format == ExportFormat.PARQUET:
            df.to_parquet(buffer, engine="pyarrow", compression="snappy", index=False)
        else:
            df.to_csv(buffer, index=False)
        
        buffer.seek(0)
        file_size = buffer.getbuffer().nbytes
        
        # Upload to S3
        async with self._session.client(
            "s3",
            endpoint_url=self.settings.s3_endpoint_url or None
        ) as s3_client:
            try:
                await s3_client.put_object(
                    Bucket=self.settings.s3_bucket,
                    Key=s3_key,
                    Body=buffer.getvalue(),
                    ContentType=(
                        "application/octet-stream" if format == ExportFormat.PARQUET
                        else "text/csv"
                    ),
                    Metadata={
                        "device_id": batch.device_id,
                        "record_count": str(batch.record_count),
                        "start_time": batch.start_time.isoformat(),
                        "end_time": batch.end_time.isoformat(),
                        "export_timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )
                
                logger.info(
                    f"Uploaded {batch.record_count} records to S3",
                    extra={
                        "device_id": batch.device_id,
                        "s3_key": s3_key,
                        "file_size_bytes": file_size,
                        "format": format.value,
                    }
                )
                
                return DatasetMetadata(
                    device_id=batch.device_id,
                    date_partition=batch.start_time.strftime("%Y-%m-%d"),
                    format=format,
                    record_count=batch.record_count,
                    start_time=batch.start_time,
                    end_time=batch.end_time,
                    columns=list(df.columns),
                    file_size_bytes=file_size,
                )
                
            except ClientError as e:
                logger.error(
                    f"Failed to upload to S3: {e}",
                    extra={
                        "device_id": batch.device_id,
                        "s3_key": s3_key,
                        "error": str(e),
                    }
                )
                raise
    
    async def health_check(self) -> bool:
        """Check S3 connectivity.
        
        Returns:
            True if S3 is accessible
        """
        async with self._session.client(
            "s3",
            endpoint_url=self.settings.s3_endpoint_url or None
        ) as s3_client:
            try:
                await s3_client.head_bucket(Bucket=self.settings.s3_bucket)
                return True
            except ClientError as e:
                logger.error(f"S3 health check failed: {e}")
                raise
