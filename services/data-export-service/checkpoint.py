"""Checkpoint repository for tracking export progress.

Stores and retrieves export checkpoints in PostgreSQL to ensure
idempotent, at-least-once delivery semantics.
"""

from datetime import datetime, timezone
from typing import Optional

import asyncpg

from config import Settings
from logging_config import get_logger
from models import Checkpoint, ExportStatus

logger = get_logger(__name__)


class CheckpointRepository:
    """PostgreSQL-backed checkpoint repository."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._pool: asyncpg.Pool | None = None

    async def initialize(self) -> None:
        """Initialize database connection pool and create tables."""
        try:
            self._pool = await asyncpg.create_pool(
                dsn=self.settings.get_checkpoint_db_url(),
                min_size=2,
                max_size=10,
            )
            await self._create_table()
            logger.info("Checkpoint repository initialized")
        except Exception as e:
            logger.error(f"Failed to initialize checkpoint repository: {e}")
            raise

    async def close(self) -> None:
        """Close database connection pool."""
        if self._pool:
            await self._pool.close()
            logger.info("Checkpoint repository closed")

    async def _create_table(self) -> None:
        """Create checkpoint table if not exists."""
        query = f"""
            CREATE TABLE IF NOT EXISTS {self.settings.checkpoint_table} (
                id SERIAL PRIMARY KEY,
                device_id VARCHAR(50) NOT NULL,
                last_exported_at TIMESTAMP WITH TIME ZONE NOT NULL,
                last_sequence INTEGER DEFAULT 0,
                status VARCHAR(50) NOT NULL,
                s3_key VARCHAR(500),
                record_count INTEGER DEFAULT 0,
                error_message TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(device_id, last_exported_at)
            );

            CREATE INDEX IF NOT EXISTS idx_checkpoint_device_id
                ON {self.settings.checkpoint_table}(device_id);

            CREATE INDEX IF NOT EXISTS idx_checkpoint_status
                ON {self.settings.checkpoint_table}(status);

            CREATE INDEX IF NOT EXISTS idx_checkpoint_updated
                ON {self.settings.checkpoint_table}(updated_at);
        """

        if not self._pool:
            raise RuntimeError("Checkpoint repository not initialized")

        async with self._pool.acquire() as conn:
            await conn.execute(query)

    async def get_last_checkpoint(self, device_id: str) -> Optional[Checkpoint]:
        """Get the most recent checkpoint for a device."""
        query = f"""
            SELECT id, device_id, last_exported_at, last_sequence, status,
                   s3_key, record_count, error_message, created_at, updated_at
            FROM {self.settings.checkpoint_table}
            WHERE device_id = $1
            ORDER BY last_exported_at DESC
            LIMIT 1
        """

        if not self._pool:
            raise RuntimeError("Checkpoint repository not initialized")

        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, device_id)

            if row:
                return Checkpoint(
                    id=str(row["id"]),
                    device_id=row["device_id"],
                    last_exported_at=row["last_exported_at"],
                    last_sequence=row["last_sequence"],
                    status=ExportStatus(row["status"]),
                    s3_key=row["s3_key"],
                    record_count=row["record_count"],
                    error_message=row["error_message"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )

            return None

    async def save_checkpoint(self, checkpoint: Checkpoint) -> Checkpoint:
        """Save a checkpoint to the database."""
        query = f"""
            INSERT INTO {self.settings.checkpoint_table}
                (device_id, last_exported_at, last_sequence, status, s3_key,
                 record_count, error_message, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, CURRENT_TIMESTAMP)
            ON CONFLICT (device_id, last_exported_at) DO UPDATE SET
                last_sequence = EXCLUDED.last_sequence,
                status = EXCLUDED.status,
                s3_key = EXCLUDED.s3_key,
                record_count = EXCLUDED.record_count,
                error_message = EXCLUDED.error_message,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id, created_at, updated_at
        """

        if not self._pool:
            raise RuntimeError("Checkpoint repository not initialized")

        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                checkpoint.device_id,
                checkpoint.last_exported_at,
                checkpoint.last_sequence,
                checkpoint.status.value,
                checkpoint.s3_key,
                checkpoint.record_count,
                checkpoint.error_message,
            )

            checkpoint.id = str(row["id"])
            checkpoint.created_at = row["created_at"]
            checkpoint.updated_at = row["updated_at"]

            logger.info(
                "Checkpoint saved",
                extra={
                    "device_id": checkpoint.device_id,
                    "checkpoint_id": checkpoint.id,
                    "status": checkpoint.status.value,
                    "record_count": checkpoint.record_count,
                }
            )

            return checkpoint

    async def health_check(self) -> bool:
        """Check database connectivity."""
        if not self._pool:
            raise RuntimeError("Checkpoint repository not initialized")

        try:
            async with self._pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Checkpoint repository health check failed: {e}")
            raise