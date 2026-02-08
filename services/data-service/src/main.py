"""
Data Service Main Application

Entry point for the Data Service that handles telemetry ingestion,
validation, enrichment, and persistence.
"""



import asyncio
import signal
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.handlers import MQTTHandler
from src.services import TelemetryService
from src.api import create_router, create_websocket_router
from src.utils import configure_logging, get_logger

# Configure logging
configure_logging(settings.log_level)
logger = get_logger(__name__)


class ApplicationState:
    """Global application state management."""
    
    def __init__(self):
        """Initialize application state."""
        self.telemetry_service: TelemetryService = None
        self.mqtt_handler: MQTTHandler = None
        self._shutdown_event = asyncio.Event()
    
    async def startup(self) -> None:
        """Initialize all services."""
        logger.info(
            "Starting Data Service",
            version=settings.app_version,
            environment=settings.environment,
        )
        
        # Initialize telemetry service
        self.telemetry_service = TelemetryService()
        await self.telemetry_service.start()
        
        # Initialize and connect MQTT handler
        self.mqtt_handler = MQTTHandler(
            telemetry_service=self.telemetry_service,
        )
        self.mqtt_handler.connect()
        
        logger.info("Data Service startup complete")
    
    async def shutdown(self) -> None:
        """Gracefully shutdown all services."""
        logger.info("Shutting down Data Service...")
        
        # Disconnect MQTT
        if self.mqtt_handler:
            self.mqtt_handler.disconnect()
        
        # Close telemetry service
        if self.telemetry_service:
            await self.telemetry_service.close()
        
        # Signal shutdown complete
        self._shutdown_event.set()
        
        logger.info("Data Service shutdown complete")
    
    async def wait_for_shutdown(self) -> None:
        """Wait for shutdown signal."""
        await self._shutdown_event.wait()


# Global application state
app_state = ApplicationState()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    FastAPI lifespan context manager for startup/shutdown.
    
    Args:
        app: FastAPI application instance
    """
    # Startup
    await app_state.startup()
    yield
    # Shutdown
    await app_state.shutdown()


def create_application() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="Data Service",
        description="Telemetry ingestion, validation, and persistence service",
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routes
    api_router = create_router(app_state.telemetry_service)
    app.include_router(api_router)

    from src.api.telemetry import router as telemetry_router
    app.include_router(telemetry_router, prefix=settings.api_prefix)


    # Include WebSocket routes
    ws_router = create_websocket_router()
    app.include_router(ws_router)
    
    return app


def handle_signal(sig: int, frame) -> None:
    """
    Handle shutdown signals gracefully.
    
    Args:
        sig: Signal number
        frame: Current stack frame
    """
    logger.info(
        "Received shutdown signal",
        signal=sig,
    )
    # Signal shutdown
    asyncio.create_task(app_state.shutdown())


# Create FastAPI application
app = create_application()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Data Service",
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
    }


# Register signal handlers
signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)


if __name__ == "__main__":
    import uvicorn
    
    logger.info(
        "Starting Data Service server",
        host=settings.host,
        port=settings.port,
    )
    
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        reload=settings.environment == "development",
    )
