"""Core export logic for telemetry data.

Orchestrates the export pipeline: querying data, writing to S3,
and tracking checkpoints with idempotency guarantees.
"""

import time
from datetime import datetime, timedelta, timezone

from config import Settings
from checkpoint import CheckpointRepository
from data_source import DataSourceClient
from logging_config import get_logger
from models import Checkpoint, ExportBatch, ExportFormat, ExportResult, ExportStatus
from s3_writer import S3Writer

logger = get_logger(__name__)


class TelemetryExporter:
    """Core exporter that coordinates data export pipeline."""
    
    def __init__(
        self,
        settings: Settings,
        data_source: DataSourceClient,
        s3_writer: S3Writer,
        checkpoint_repo: CheckpointRepository,
    ):
        self.settings = settings
        self.data_source = data_source
        self.s3_writer = s3_writer
        self.checkpoint_repo = checkpoint_repo
    
    async def export_device_data(
        self,
        device_id: str,
        force_full: bool = False
    ) -> ExportResult:
        """Export telemetry data for a device.
        
        This method is idempotent - duplicate exports will be skipped
        based on checkpoint tracking.
        
        Args:
            device_id: Device identifier
            force_full: If True, export all data ignoring checkpoints
            
        Returns:
            ExportResult with operation details
        """
        start_time = time.time()
        
        try:
            # Determine export window
            if force_full:
                start_time_export = datetime.now(timezone.utc) - timedelta(
                    hours=self.settings.max_export_window_hours
                )
            else:
                # Get last checkpoint
                checkpoint = await self.checkpoint_repo.get_last_checkpoint(device_id)
                if checkpoint and checkpoint.status == ExportStatus.COMPLETED:
                    start_time_export = checkpoint.last_exported_at
                else:
                    start_time_export = datetime.now(timezone.utc) - timedelta(
                        hours=self.settings.lookback_hours
                    )
            
            end_time_export = datetime.now(timezone.utc)
            
            # Check if there's data to export
            record_count = await self.data_source.count_records(
                device_id, start_time_export, end_time_export
            )
            
            if record_count == 0:
                logger.info(
                    f"No new data to export for device {device_id}",
                    extra={"device_id": device_id}
                )
                return ExportResult(
                    success=True,
                    device_id=device_id,
                    start_time=start_time_export,
                    end_time=end_time_export,
                    record_count=0,
                    format=ExportFormat(self.settings.export_format),
                    duration_seconds=time.time() - start_time,
                )
            
            # Query telemetry data
            records = await self.data_source.query_telemetry(
                device_id=device_id,
                start_time=start_time_export,
                end_time=end_time_export,
                batch_size=self.settings.export_batch_size,
            )
            
            if not records:
                logger.info(
                    f"No records returned for device {device_id}",
                    extra={"device_id": device_id}
                )
                return ExportResult(
                    success=True,
                    device_id=device_id,
                    start_time=start_time_export,
                    end_time=end_time_export,
                    record_count=0,
                    format=ExportFormat(self.settings.export_format),
                    duration_seconds=time.time() - start_time,
                )
            
            # Create checkpoint for in-progress export
            checkpoint = Checkpoint(
                device_id=device_id,
                last_exported_at=records[-1].timestamp,
                status=ExportStatus.IN_PROGRESS,
                record_count=len(records),
            )
            await self.checkpoint_repo.save_checkpoint(checkpoint)
            
            # Create export batch
            batch = ExportBatch(
                device_id=device_id,
                start_time=records[0].timestamp,
                end_time=records[-1].timestamp,
                records=records,
                record_count=len(records),
            )
            
            # Export format
            export_format = ExportFormat(self.settings.export_format)
            
            # Write to S3
            metadata = await self.s3_writer.write_batch(batch, export_format)
            
            # Update checkpoint to completed
            checkpoint.status = ExportStatus.COMPLETED
            checkpoint.s3_key = self.s3_writer._build_s3_key(
                device_id, batch.start_time, export_format
            )
            checkpoint.record_count = len(records)
            await self.checkpoint_repo.save_checkpoint(checkpoint)
            
            duration = time.time() - start_time
            
            logger.info(
                f"Successfully exported {len(records)} records for device {device_id}",
                extra={
                    "device_id": device_id,
                    "record_count": len(records),
                    "s3_key": checkpoint.s3_key,
                    "duration_seconds": duration,
                }
            )
            
            return ExportResult(
                success=True,
                device_id=device_id,
                start_time=batch.start_time,
                end_time=batch.end_time,
                record_count=len(records),
                s3_key=checkpoint.s3_key,
                format=export_format,
                file_size_bytes=metadata.file_size_bytes,
                duration_seconds=duration,
            )
            
        except Exception as e:
            duration = time.time() - start_time
            
            logger.error(
                f"Export failed for device {device_id}: {e}",
                extra={
                    "device_id": device_id,
                    "error": str(e),
                    "duration_seconds": duration,
                }
            )
            
            # Save failed checkpoint
            checkpoint = Checkpoint(
                device_id=device_id,
                last_exported_at=datetime.now(timezone.utc),
                status=ExportStatus.FAILED,
                error_message=str(e),
            )
            await self.checkpoint_repo.save_checkpoint(checkpoint)
            
            return ExportResult(
                success=False,
                device_id=device_id,
                start_time=start_time_export if 'start_time_export' in locals() else datetime.now(timezone.utc),
                end_time=datetime.now(timezone.utc),
                record_count=0,
                format=ExportFormat(self.settings.export_format),
                error_message=str(e),
                duration_seconds=duration,
            )
    
    async def get_export_status(self, device_id: str) -> dict:
        """Get export status for a device.
        
        Args:
            device_id: Device identifier
            
        Returns:
            Dictionary with status information
        """
        checkpoint = await self.checkpoint_repo.get_last_checkpoint(device_id)
        
        if not checkpoint:
            return {
                "device_id": device_id,
                "status": "never_exported",
                "last_exported_at": None,
            }
        
        return {
            "device_id": device_id,
            "status": checkpoint.status.value,
            "last_exported_at": checkpoint.last_exported_at.isoformat(),
            "record_count": checkpoint.record_count,
            "s3_key": checkpoint.s3_key,
            "updated_at": checkpoint.updated_at.isoformat() if checkpoint.updated_at else None,
        }
