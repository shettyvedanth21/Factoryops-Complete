from fastapi import APIRouter, Query, Depends
from datetime import datetime
from typing import Optional

from src.services.telemetry_service import TelemetryService


router = APIRouter()


def get_telemetry_service() -> TelemetryService:
    # Lazy import to avoid circular import
    from src.main import app_state
    return app_state.telemetry_service


@router.get("/devices/{device_id}/telemetry")
async def get_device_telemetry(
    device_id: str,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    limit: int = Query(100),
    telemetry_service: TelemetryService = Depends(get_telemetry_service),
):
    return await telemetry_service.query_telemetry(
        device_id=device_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )




@router.get("/devices/{device_id}/stats")
async def get_device_stats(
    device_id: str,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    telemetry_service: TelemetryService = Depends(get_telemetry_service),
):
    return await telemetry_service.get_stats(
        device_id=device_id,
        start_time=start_time,
        end_time=end_time,
    )
