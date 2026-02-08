"""API endpoints for rule evaluation."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.rule import (
    EvaluationRequest,
    EvaluationResponse,
    ErrorResponse,
)
from app.services.evaluator import RuleEvaluator
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/evaluate",
    response_model=EvaluationResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def evaluate_rules(
    request: EvaluationRequest,
    tenant_id: Optional[str] = Query(None, description="Tenant ID for multi-tenancy"),
    db: AsyncSession = Depends(get_db),
) -> EvaluationResponse:
    """Evaluate telemetry data against all applicable rules.
    
    This endpoint is called by the Data Service when new telemetry arrives.
    It evaluates the telemetry against all active rules and triggers
    notifications if conditions are met.
    
    - **device_id**: Device identifier
    - **timestamp**: Telemetry timestamp
    - **voltage**: Voltage reading
    - **current**: Current reading
    - **power**: Power reading
    - **temperature**: Temperature reading
    - **tenant_id**: Optional tenant ID for multi-tenancy
    """
    evaluator = RuleEvaluator(db)
    
    try:
        total_evaluated, total_triggered, triggered_rules = await evaluator.evaluate_telemetry(
            telemetry=request,
            tenant_id=tenant_id,
        )
        
        return EvaluationResponse(
            device_id=request.device_id,
            evaluated_at=datetime.utcnow(),
            rules_evaluated=total_evaluated,
            rules_triggered=total_triggered,
            triggered_rules=triggered_rules,
        )
        
    except ValueError as e:
        logger.warning(
            "Evaluation failed",
            extra={
                "device_id": request.device_id,
                "error": str(e),
            }
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "EVALUATION_ERROR",
                    "message": str(e),
                },
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
    except Exception as e:
        logger.error(
            "Unexpected error during rule evaluation",
            extra={
                "device_id": request.device_id,
                "error": str(e),
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred during evaluation",
                },
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
