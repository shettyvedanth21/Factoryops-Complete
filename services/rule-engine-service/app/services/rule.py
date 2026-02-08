"""Rule service layer - business logic."""

from typing import Optional, List
from uuid import UUID
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rule import Rule, RuleStatus, RuleScope, ConditionOperator, Alert
from app.repositories.rule import RuleRepository, AlertRepository
from app.schemas.rule import RuleCreate, RuleUpdate, RuleStatus as RuleStatusEnum

logger = logging.getLogger(__name__)


class RuleService:
    """Service layer for rule management business logic.
    
    This service encapsulates all business rules and operations
    related to rule management, providing a clean API for
    the HTTP handlers.
    """
    
    def __init__(self, session: AsyncSession):
        self._session = session
        self._repository = RuleRepository(session)
    
    async def create_rule(self, rule_data: RuleCreate) -> Rule:
        """Create a new rule.
        
        Args:
            rule_data: Rule creation data
            
        Returns:
            Created Rule instance
            
        Raises:
            ValueError: If validation fails
        """
        # Validate device_ids for selected_devices scope
        if rule_data.scope == RuleScope.SELECTED_DEVICES and not rule_data.device_ids:
            raise ValueError("device_ids is required when scope is 'selected_devices'")
        
        # Validate notification channels
        if not rule_data.notification_channels:
            raise ValueError("At least one notification channel is required")
        
        # Create rule entity
        rule = Rule(
            tenant_id=rule_data.tenant_id,
            rule_name=rule_data.rule_name,
            description=rule_data.description,
            scope=RuleScope(rule_data.scope),
            device_ids=rule_data.device_ids,
            property=rule_data.property,
            condition=ConditionOperator(rule_data.condition),
            threshold=rule_data.threshold,
            status=RuleStatus.ACTIVE,
            notification_channels=[ch.value for ch in rule_data.notification_channels],
            cooldown_minutes=rule_data.cooldown_minutes,
        )
        
        # Persist to database
        created_rule = await self._repository.create(rule)
        await self._session.commit()
        
        logger.info(
            "Rule created successfully",
            extra={
                "rule_id": str(created_rule.rule_id),
                "rule_name": created_rule.rule_name,
                "scope": created_rule.scope.value,
                "device_count": len(created_rule.device_ids),
            }
        )
        
        return created_rule
    
    async def get_rule(
        self, 
        rule_id: UUID, 
        tenant_id: Optional[str] = None
    ) -> Optional[Rule]:
        """Get rule by ID.
        
        Args:
            rule_id: Rule identifier
            tenant_id: Optional tenant ID for multi-tenancy
            
        Returns:
            Rule instance or None if not found
        """
        return await self._repository.get_by_id(rule_id, tenant_id)
    
    async def list_rules(
        self,
        tenant_id: Optional[str] = None,
        status: Optional[RuleStatusEnum] = None,
        device_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[Rule], int]:
        """List rules with filtering and pagination.
        
        Args:
            tenant_id: Optional tenant filter
            status: Optional status filter
            device_id: Optional device filter
            page: Page number (1-based)
            page_size: Number of items per page
            
        Returns:
            Tuple of (rules list, total count)
        """
        status_enum = RuleStatus(status.value) if status else None
        
        return await self._repository.list_rules(
            tenant_id=tenant_id,
            status=status_enum,
            device_id=device_id,
            page=page,
            page_size=page_size,
        )
    
    async def update_rule(
        self,
        rule_id: UUID,
        rule_data: RuleUpdate,
        tenant_id: Optional[str] = None,
    ) -> Optional[Rule]:
        """Update an existing rule.
        
        Args:
            rule_id: Rule identifier
            rule_data: Update data
            tenant_id: Optional tenant ID for multi-tenancy
            
        Returns:
            Updated Rule instance or None if not found
        """
        # Fetch existing rule
        rule = await self._repository.get_by_id(rule_id, tenant_id)
        if not rule:
            logger.warning(
                "Attempted to update non-existent rule",
                extra={"rule_id": str(rule_id)}
            )
            return None
        
        # Update only provided fields
        update_data = rule_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if field == "scope" and value:
                value = RuleScope(value)
            elif field == "condition" and value:
                value = ConditionOperator(value)
            elif field == "notification_channels" and value:
                value = [ch.value for ch in value]
            setattr(rule, field, value)
        
        # Validate after update
        if rule.scope == RuleScope.SELECTED_DEVICES and not rule.device_ids:
            raise ValueError("device_ids is required when scope is 'selected_devices'")
        
        # Persist changes
        updated_rule = await self._repository.update(rule)
        await self._session.commit()
        
        logger.info(
            "Rule updated successfully",
            extra={"rule_id": str(updated_rule.rule_id)}
        )
        
        return updated_rule
    
    async def update_rule_status(
        self,
        rule_id: UUID,
        status: RuleStatusEnum,
        tenant_id: Optional[str] = None,
    ) -> Optional[Rule]:
        """Update rule status (pause/resume/archive).
        
        Args:
            rule_id: Rule identifier
            status: New status
            tenant_id: Optional tenant ID for multi-tenancy
            
        Returns:
            Updated Rule instance or None if not found
        """
        rule = await self._repository.update_status(rule_id, RuleStatus(status.value))
        if rule:
            await self._session.commit()
            logger.info(
                "Rule status updated",
                extra={
                    "rule_id": str(rule_id),
                    "new_status": status.value,
                }
            )
        return rule
    
    async def delete_rule(
        self,
        rule_id: UUID,
        tenant_id: Optional[str] = None,
        soft: bool = True,
    ) -> bool:
        """Delete a rule.
        
        Args:
            rule_id: Rule identifier
            tenant_id: Optional tenant ID for multi-tenancy
            soft: If True, performs soft delete; otherwise hard delete
            
        Returns:
            True if deleted successfully, False if not found
        """
        rule = await self._repository.get_by_id(rule_id, tenant_id)
        if not rule:
            return False
        
        await self._repository.delete(rule, soft=soft)
        await self._session.commit()
        
        logger.info(
            "Rule deleted successfully",
            extra={
                "rule_id": str(rule_id),
                "soft_delete": soft,
            }
        )
        
        return True
    
    async def get_active_rules_for_device(
        self,
        device_id: str,
        tenant_id: Optional[str] = None,
    ) -> List[Rule]:
        """Get all active rules applicable to a device.
        
        Args:
            device_id: Device identifier
            tenant_id: Optional tenant ID for multi-tenancy
            
        Returns:
            List of active rules
        """
        return await self._repository.get_active_rules_for_device(device_id, tenant_id)


class AlertService:
    """Service layer for alert management."""
    
    def __init__(self, session: AsyncSession):
        self._session = session
        self._repository = AlertRepository(session)
    
    async def create_alert(
        self,
        rule: Rule,
        device_id: str,
        actual_value: float,
        severity: str = "medium",
    ) -> Alert:
        """Create a new alert for a triggered rule.
        
        Args:
            rule: The rule that was triggered
            device_id: Device identifier
            actual_value: The actual telemetry value
            severity: Alert severity
            
        Returns:
            Created Alert instance
        """
        message = (
            f"Rule '{rule.rule_name}' triggered for device {device_id}: "
            f"{rule.property} {rule.condition.value} {rule.threshold} "
            f"(actual: {actual_value})"
        )
        
        alert = Alert(
            tenant_id=rule.tenant_id,
            rule_id=rule.rule_id,
            device_id=device_id,
            severity=severity,
            message=message,
            actual_value=actual_value,
            threshold_value=rule.threshold,
            status="open",
        )
        
        created_alert = await self._repository.create(alert)
        await self._session.commit()
        
        logger.info(
            "Alert created",
            extra={
                "alert_id": str(created_alert.alert_id),
                "rule_id": str(rule.rule_id),
                "device_id": device_id,
            }
        )
        
        return created_alert
