"""Analytics repository for accessing ML results from PostgreSQL."""

from datetime import datetime
from typing import List, Optional
import asyncpg

from src.config import settings
from src.utils.exceptions import DatabaseError, AnalyticsLoadError
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class AnalyticsRepository:
    """Repository for accessing analytics results from PostgreSQL."""
    
    def __init__(self):
        """Initialize analytics repository."""
        self.pool: Optional[asyncpg.Pool] = None
        self.connection_url = settings.postgres_async_url
    
    async def connect(self) -> None:
        """Create database connection pool."""
        try:
            self.pool = await asyncpg.create_pool(
                self.connection_url,
                min_size=5,
                max_size=settings.postgres_pool_size
            )
            logger.info("Connected to analytics database")
        except Exception as e:
            logger.error("Failed to connect to database", error=str(e))
            raise DatabaseError(f"Failed to connect: {str(e)}", operation="connect")
    
    async def disconnect(self) -> None:
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Disconnected from analytics database")
    
    async def get_analytics_results(
        self,
        device_id: str,
        analysis_type: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[dict]:
        """Fetch analytics results for a device and time range.
        
        Args:
            device_id: Device identifier
            analysis_type: Type of analysis (anomaly, prediction, forecast)
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            List of analytics result records
            
        Raises:
            AnalyticsLoadError: If query fails
        """
        if not self.pool:
            raise DatabaseError("Not connected to database", operation="query")
        
        query = """
            SELECT 
                id,
                job_id,
                device_id,
                analysis_type,
                model_name,
                date_range_start,
                date_range_end,
                results,
                accuracy_metrics,
                status,
                created_at,
                completed_at
            FROM analytics_results
            WHERE device_id = $1
                AND analysis_type = $2
                AND created_at >= $3
                AND created_at <= $4
                AND status = 'completed'
            ORDER BY created_at DESC
        """
        
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, device_id, analysis_type, start_time, end_time)
                
                results = [dict(row) for row in rows]
                
                logger.info(
                    "Fetched analytics results",
                    device_id=device_id,
                    analysis_type=analysis_type,
                    result_count=len(results)
                )
                
                return results
                
        except Exception as e:
            logger.error(
                "Failed to fetch analytics results",
                error=str(e),
                device_id=device_id,
                analysis_type=analysis_type
            )
            raise AnalyticsLoadError(
                f"Failed to load analytics: {str(e)}",
                device_id=device_id,
                analysis_type=analysis_type
            )
    
    async def get_all_analytics_for_devices(
        self,
        device_ids: List[str],
        start_time: datetime,
        end_time: datetime
    ) -> dict:
        """Fetch all analytics results for multiple devices.
        
        Args:
            device_ids: List of device identifiers
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            Dictionary mapping analysis types to results
        """
        results = {
            "anomaly": [],
            "prediction": [],
            "forecast": []
        }
        
        for device_id in device_ids:
            for analysis_type in ["anomaly", "prediction", "forecast"]:
                try:
                    device_results = await self.get_analytics_results(
                        device_id, analysis_type, start_time, end_time
                    )
                    results[analysis_type].extend(device_results)
                except AnalyticsLoadError as e:
                    logger.warning(
                        "Failed to load analytics for device",
                        device_id=device_id,
                        analysis_type=analysis_type,
                        error=str(e)
                    )
                    continue
        
        return results
    
    async def health_check(self) -> bool:
        """Check database connectivity.
        
        Returns:
            True if database is accessible
        """
        if not self.pool:
            return False
        
        try:
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception:
            return False