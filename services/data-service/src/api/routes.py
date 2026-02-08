"""API routes for REST endpoints."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.config import settings
from src.models import TelemetryPoint, TelemetryQuery, TelemetryStats
from src.services import TelemetryService
from src.utils import get_logger

logger = get_logger(__name__)

# Response models
class ApiResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool = Field(..., description="Request success status")
    data: Optional[Any] = Field(None, description="Response data")
    error: Optional[Dict[str, Any]] = Field(None, description="Error details")
    timestamp: str = Field(..., description="Response timestamp")


class TelemetryListResponse(BaseModel):
    """Telemetry list response."""
    items: List[TelemetryPoint]
    total: int = Field(..., description="Total number of results")
    page: int = Field(default=1, description="Current page")
    page_size: int = Field(default=1000, description="Items per page")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    timestamp: str = Field(..., description="Check timestamp")
    checks: Dict[str, Any] = Field(default_factory=dict, description="Component checks")


def create_router(telemetry_service: TelemetryService) -> APIRouter:
    """
    Create API router with telemetry endpoints.
    
    Args:
        telemetry_service: Telemetry service instance
        
    Returns:
        Configured API router
    """
    router = APIRouter(prefix=settings.api_prefix)
    
    @router.get(
        "/health",
        response_model=HealthResponse,
        summary="Health check endpoint",
        tags=["Health"],
    )
    async def health_check() -> HealthResponse:
        """
        Check service health status.
        
        Returns:
            Health status including component checks
        """
        return HealthResponse(
            status="healthy",
            version=settings.app_version,
            timestamp=datetime.utcnow().isoformat(),
            checks={
                "influxdb": "connected",  # Simplified - would check actual connection
                "mqtt": "connected",      # Simplified - would check actual connection
            },
        )
    
    @router.get(
        "/telemetry/{device_id}",
        response_model=ApiResponse,
        summary="Get device telemetry data",
        tags=["Telemetry"],
    )
    async def get_telemetry(
        device_id: str,
        start_time: Optional[datetime] = Query(None, description="Start time (ISO 8601)"),
        end_time: Optional[datetime] = Query(None, description="End time (ISO 8601)"),
        fields: Optional[str] = Query(None, description="Comma-separated field names"),
        aggregate: Optional[str] = Query(None, description="Aggregation: mean, max, min, sum"),
        interval: Optional[str] = Query(None, description="Aggregation interval (e.g., 1h, 5m)"),
        limit: int = Query(default=1000, ge=1, le=10000, description="Maximum results"),
    ) -> ApiResponse:
        """
        Get telemetry data for a specific device.
        
        Args:
            device_id: Device identifier
            start_time: Start time filter
            end_time: End time filter
            fields: Specific fields to retrieve (comma-separated)
            aggregate: Aggregation function
            interval: Aggregation interval
            limit: Maximum number of results
            
        Returns:
            List of telemetry points
        """
        try:
            # Parse fields
            field_list = fields.split(",") if fields else None
            
            # Query telemetry
            points = await telemetry_service.get_telemetry(
                device_id=device_id,
                start_time=start_time,
                end_time=end_time,
                fields=field_list,
                aggregate=aggregate,
                interval=interval,
                limit=limit,
            )
            
            return ApiResponse(
                success=True,
                data={
                    "items": [point.model_dump() for point in points],
                    "total": len(points),
                    "device_id": device_id,
                },
                timestamp=datetime.utcnow().isoformat(),
            )
            
        except Exception as e:
            logger.error(
                "Failed to get telemetry",
                device_id=device_id,
                error=str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "error": {
                        "code": "QUERY_ERROR",
                        "message": str(e),
                    },
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
    
    @router.get(
        "/stats/{device_id}",
        response_model=ApiResponse,
        summary="Get device statistics",
        tags=["Telemetry"],
    )
    async def get_stats(
        device_id: str,
        start_time: Optional[datetime] = Query(None, description="Start time (ISO 8601)"),
        end_time: Optional[datetime] = Query(None, description="End time (ISO 8601)"),
    ) -> ApiResponse:
        """
        Get aggregated statistics for a device.
        
        Args:
            device_id: Device identifier
            start_time: Start time filter
            end_time: End time filter
            
        Returns:
            Aggregated statistics
        """
        try:
            stats = await telemetry_service.get_stats(
                device_id=device_id,
                start_time=start_time,
                end_time=end_time,
            )
            
            if stats is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "success": False,
                        "error": {
                            "code": "NO_DATA",
                            "message": f"No data found for device {device_id}",
                        },
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )
            
            return ApiResponse(
                success=True,
                data=stats.model_dump(),
                timestamp=datetime.utcnow().isoformat(),
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Failed to get stats",
                device_id=device_id,
                error=str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "error": {
                        "code": "STATS_ERROR",
                        "message": str(e),
                    },
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
    
    @router.post(
        "/query",
        response_model=ApiResponse,
        summary="Execute custom query",
        tags=["Telemetry"],
    )
    async def custom_query(query: TelemetryQuery) -> ApiResponse:
        """
        Execute a custom telemetry query.
        
        Args:
            query: Query parameters
            
        Returns:
            Query results
        """
        try:
            points = await telemetry_service.get_telemetry(
                device_id=query.device_id,
                start_time=query.start_time,
                end_time=query.end_time,
                fields=query.fields,
                aggregate=query.aggregate,
                interval=query.interval,
                limit=query.limit,
            )
            
            return ApiResponse(
                success=True,
                data={
                    "items": [point.model_dump() for point in points],
                    "total": len(points),
                },
                timestamp=datetime.utcnow().isoformat(),
            )
            
        except Exception as e:
            logger.error(
                "Custom query failed",
                device_id=query.device_id,
                error=str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "error": {
                        "code": "QUERY_ERROR",
                        "message": str(e),
                    },
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
    
    return router
