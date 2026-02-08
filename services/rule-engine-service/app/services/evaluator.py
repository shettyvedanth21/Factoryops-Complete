"""Rule evaluation engine for real-time telemetry processing."""

import logging
from typing import List, Optional, Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rule import Rule, ConditionOperator
from app.schemas.rule import EvaluationRequest, EvaluationResult, TelemetryPayload
from app.services.rule import RuleService, AlertService
from app.repositories.rule import RuleRepository
from app.notifications.adapter import NotificationAdapter

logger = logging.getLogger(__name__)


class RuleEvaluator:
    """Real-time rule evaluation engine.
    
    Evaluates telemetry data against active rules and triggers
    notifications when conditions are met.
    """
    
    def __init__(self, session: AsyncSession):
        self._session = session
        self._rule_service = RuleService(session)
        self._alert_service = AlertService(session)
        self._rule_repository = RuleRepository(session)
        self._notification_adapter = NotificationAdapter()
    
    async def evaluate_telemetry(
        self,
        telemetry: TelemetryPayload,
        tenant_id: Optional[str] = None,
    ) -> tuple[int, int, List[EvaluationResult]]:
        """Evaluate telemetry data against all applicable rules.
        
        Args:
            telemetry: Telemetry payload from device
            tenant_id: Optional tenant ID for multi-tenancy
            
        Returns:
            Tuple of (total rules evaluated, rules triggered, evaluation results)
        """
        device_id = telemetry.device_id
        
        # Get all active rules for this device
        rules = await self._rule_service.get_active_rules_for_device(
            device_id=device_id,
            tenant_id=tenant_id,
        )
        
        if not rules:
            logger.debug(
                "No active rules for device",
                extra={"device_id": device_id}
            )
            return 0, 0, []
        
        logger.debug(
            "Evaluating rules for device",
            extra={
                "device_id": device_id,
                "rule_count": len(rules),
            }
        )
        
        triggered_rules: List[EvaluationResult] = []
        
        for rule in rules:
            # Skip if in cooldown period
            if rule.is_in_cooldown():
                logger.debug(
                    "Rule in cooldown, skipping",
                    extra={
                        "rule_id": str(rule.rule_id),
                        "device_id": device_id,
                    }
                )
                continue
            
            # Evaluate the rule
            result = await self._evaluate_single_rule(rule, telemetry)
            
            if result.triggered:
                triggered_rules.append(result)
                
                # Create alert
                await self._alert_service.create_alert(
                    rule=rule,
                    device_id=device_id,
                    actual_value=result.actual_value,
                    severity=self._determine_severity(rule, result.actual_value),
                )
                
                # Update last triggered timestamp
                await self._rule_repository.update_last_triggered(rule.rule_id)
                
                # Send notifications (async)
                await self._send_notifications(rule, device_id, result)
        
        await self._session.commit()
        
        logger.info(
            "Rule evaluation completed",
            extra={
                "device_id": device_id,
                "rules_evaluated": len(rules),
                "rules_triggered": len(triggered_rules),
            }
        )
        
        return len(rules), len(triggered_rules), triggered_rules
    
    async def _evaluate_single_rule(
        self,
        rule: Rule,
        telemetry: TelemetryPayload,
    ) -> EvaluationResult:
        """Evaluate a single rule against telemetry data.
        
        Args:
            rule: Rule to evaluate
            telemetry: Telemetry data
            
        Returns:
            Evaluation result
        """
        # Extract the property value from telemetry
        actual_value = self._extract_property_value(telemetry, rule.property)
        
        # Evaluate condition
        triggered = self._evaluate_condition(
            actual_value=actual_value,
            threshold=rule.threshold,
            operator=rule.condition,
        )
        
        message = None
        if triggered:
            message = (
                f"{rule.property} is {actual_value} "
                f"(threshold: {rule.condition.value} {rule.threshold})"
            )
        
        return EvaluationResult(
            rule_id=rule.rule_id,
            rule_name=rule.rule_name,
            triggered=triggered,
            actual_value=actual_value,
            threshold=rule.threshold,
            condition=rule.condition.value,
            message=message,
        )
    
    def _extract_property_value(
        self,
        telemetry: TelemetryPayload,
        property_name: str,
    ) -> float:
        """Extract property value from telemetry payload.
        
        Args:
            telemetry: Telemetry payload
            property_name: Property name to extract
            
        Returns:
            Property value as float
            
        Raises:
            ValueError: If property not found
        """
        property_map = {
            "voltage": telemetry.voltage,
            "current": telemetry.current,
            "power": telemetry.power,
            "temperature": telemetry.temperature,
        }
        
        if property_name not in property_map:
            raise ValueError(f"Unknown property: {property_name}")
        
        return property_map[property_name]
    
    def _evaluate_condition(
        self,
        actual_value: float,
        threshold: float,
        operator: ConditionOperator,
    ) -> bool:
        """Evaluate condition against actual value.
        
        Args:
            actual_value: Actual telemetry value
            threshold: Threshold value from rule
            operator: Comparison operator
            
        Returns:
            True if condition is met
        """
        operators = {
            ConditionOperator.GREATER_THAN: lambda a, t: a > t,
            ConditionOperator.LESS_THAN: lambda a, t: a < t,
            ConditionOperator.EQUAL: lambda a, t: a == t,
            ConditionOperator.NOT_EQUAL: lambda a, t: a != t,
            ConditionOperator.GREATER_THAN_OR_EQUAL: lambda a, t: a >= t,
            ConditionOperator.LESS_THAN_OR_EQUAL: lambda a, t: a <= t,
        }
        
        if operator not in operators:
            raise ValueError(f"Unknown operator: {operator}")
        
        return operators[operator](actual_value, threshold)
    
    def _determine_severity(self, rule: Rule, actual_value: float) -> str:
        """Determine alert severity based on how far threshold is exceeded.
        
        Args:
            rule: The triggered rule
            actual_value: Actual telemetry value
            
        Returns:
            Severity level (low, medium, high, critical)
        """
        # Calculate percentage deviation from threshold
        if rule.threshold == 0:
            deviation = abs(actual_value)
        else:
            deviation = abs((actual_value - rule.threshold) / rule.threshold)
        
        if deviation > 0.5:  # > 50% deviation
            return "critical"
        elif deviation > 0.25:  # > 25% deviation
            return "high"
        elif deviation > 0.1:  # > 10% deviation
            return "medium"
        else:
            return "low"
    
    async def _send_notifications(
        self,
        rule: Rule,
        device_id: str,
        result: EvaluationResult,
    ) -> None:
        """Send notifications through configured channels.
        
        Args:
            rule: The triggered rule
            device_id: Device identifier
            result: Evaluation result
        """
        if not rule.notification_channels:
            return
        
        message = (
            f"🚨 Alert: {rule.rule_name}\n"
            f"Device: {device_id}\n"
            f"Condition: {rule.property} {rule.condition.value} {rule.threshold}\n"
            f"Actual: {result.actual_value}\n"
            f"Time: {datetime.utcnow().isoformat()}"
        )
        
        for channel in rule.notification_channels:
            try:
                await self._notification_adapter.send(
                    channel=channel,
                    message=message,
                    rule=rule,
                    device_id=device_id,
                )
                logger.info(
                    "Notification sent",
                    extra={
                        "channel": channel,
                        "rule_id": str(rule.rule_id),
                        "device_id": device_id,
                    }
                )
            except Exception as e:
                logger.error(
                    "Failed to send notification",
                    extra={
                        "channel": channel,
                        "rule_id": str(rule.rule_id),
                        "error": str(e),
                    }
                )
