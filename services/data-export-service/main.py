"""Data Export Service - Main FastAPI Application.

Provides minimal health/readiness endpoints and manages the continuous
export worker lifecycle.
"""

import asyncio
import signal
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from config import Settings, get_settings
from logging_config import get_logger, setup_logging
from worker import ExportWorker

# Setup structured logging
setup_logging()
logger = get_logger(__name__)

# Global worker instance
_worker: ExportWorker | None = None


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    version: str
    timestamp: str


class ReadyResponse(BaseModel):
    """Readiness check response model."""
    ready: bool
    checks: dict


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    global _worker
    
    settings = get_settings()
    logger.info(
        "Starting Data Export Service",
        extra={
            "version": settings.service_version,
            "environment": settings.environment,
        }
    )
    
    # Initialize and start export worker
    _worker = ExportWorker(settings)
    await _worker.start()
    logger.info("Export worker started successfully")
    
    yield
    
    # Graceful shutdown
    logger.info("Shutting down Data Export Service...")
    if _worker:
        await _worker.stop()
    logger.info("Data Export Service shutdown complete")


app = FastAPI(
    title="Data Export Service",
    description="Continuous telemetry data export to S3 for analytics",
    version="1.0.0",
    docs_url=None,  # Disable docs for minimal API surface
    redoc_url=None,
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Liveness probe endpoint.
    
    Returns:
        HealthResponse with service status
    """
    from datetime import datetime, timezone
    
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        version=settings.service_version,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/ready", response_model=ReadyResponse)
async def readiness_check() -> ReadyResponse:
    """Readiness probe endpoint.
    
    Returns:
        ReadyResponse indicating if service is ready to handle work
    """
    checks = {
        "worker_running": _worker is not None and _worker.is_running(),
        "checkpoint_store_connected": await _check_checkpoint_store(),
        "s3_accessible": await _check_s3_access(),
    }
    
    ready = all(checks.values())
    
    if not ready:
        raise HTTPException(
            status_code=503,
            detail={"ready": False, "checks": checks}
        )
    
    return ReadyResponse(ready=True, checks=checks)


async def _check_checkpoint_store() -> bool:
    """Check if checkpoint store is accessible."""
    if not _worker:
        return False
    try:
        await _worker.checkpoint_store.health_check()
        return True
    except Exception as e:
        logger.warning(f"Checkpoint store health check failed: {e}")
        return False


async def _check_s3_access() -> bool:
    """Check if S3 is accessible."""
    if not _worker:
        return False
    try:
        await _worker.s3_writer.health_check()
        return True
    except Exception as e:
        logger.warning(f"S3 health check failed: {e}")
        return False


def _signal_handler(sig: int, frame) -> None:
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {sig}, initiating graceful shutdown...")
    sys.exit(0)


# Register signal handlers
signal.signal(signal.SIGTERM, _signal_handler)
signal.signal(signal.SIGINT, _signal_handler)


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        access_log=False,  # Use structured logging instead
    )
