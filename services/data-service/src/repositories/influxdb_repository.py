"""InfluxDB repository for telemetry storage and retrieval."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.client.flux_table import FluxRecord

from src.config import settings
from src.models import EnrichmentStatus, TelemetryPayload, TelemetryPoint, TelemetryStats
from src.utils import get_logger

logger = get_logger(__name__)


class InfluxDBRepository:
    """
    Repository for InfluxDB operations.

    Handles:
    - Writing telemetry data with tags and fields
    - Querying telemetry with time ranges and filters
    - Aggregating statistics
    """

    MEASUREMENT = "device_telemetry"

    def __init__(self, client: Optional[InfluxDBClient] = None):
        self.client = client or InfluxDBClient(
            url=settings.influxdb_url,
            token=settings.influxdb_token,
            org=settings.influxdb_org,
            timeout=settings.influxdb_timeout,
        )

        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.client.query_api()

        logger.info(
            "InfluxDBRepository initialized",
            url=settings.influxdb_url,
            org=settings.influxdb_org,
            bucket=settings.influxdb_bucket,
        )

    # ------------------------------------------------------------------

    def write_telemetry(
        self,
        payload: TelemetryPayload,
        additional_tags: Optional[Dict[str, str]] = None,
    ) -> bool:

        try:
            tags = {
                "device_id": payload.device_id,
                "schema_version": payload.schema_version,
                "enrichment_status": payload.enrichment_status.value,
            }

            if additional_tags:
                tags.update(additional_tags)

            if payload.device_metadata:
                tags["device_type"] = payload.device_metadata.type
                if payload.device_metadata.location:
                    tags["location"] = payload.device_metadata.location

            fields = {
                "voltage": payload.voltage,
                "current": payload.current,
                "power": payload.power,
                "temperature": payload.temperature,
            }

            point = Point(self.MEASUREMENT)

            for k, v in tags.items():
                point = point.tag(k, v)

            for k, v in fields.items():
                point = point.field(k, v)

            point = point.time(payload.timestamp)

            self.write_api.write(
                bucket=settings.influxdb_bucket,
                org=settings.influxdb_org,
                record=point,
            )

            return True

        except Exception as e:
            logger.error(
                "Failed to write telemetry to InfluxDB",
                device_id=payload.device_id,
                error=str(e),
            )
            return False

    # ------------------------------------------------------------------

    def query_telemetry(
        self,
        device_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        fields: Optional[List[str]] = None,
        aggregate: Optional[str] = None,
        interval: Optional[str] = None,
        limit: int = 1000,
    ) -> List[TelemetryPoint]:

        try:
            if start_time is None:
                start_time = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

            if end_time is None:
                end_time = datetime.utcnow()

            flux_query = self._build_query(
                device_id=device_id,
                start_time=start_time,
                end_time=end_time,
                fields=fields,
                aggregate=aggregate,
                interval=interval,
                limit=limit,
            )

            tables = self.query_api.query(
                flux_query,
                org=settings.influxdb_org,
            )

            points: List[TelemetryPoint] = []

            for table in tables:
                for record in table.records:
                    point = self._parse_record_to_point(record)
                    if point:
                        points.append(point)

            return points

        except Exception as e:
            logger.error(
                "Failed to query telemetry",
                device_id=device_id,
                error=str(e),
            )
            return []

    # ------------------------------------------------------------------

    def get_stats(
        self,
        device_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Optional[TelemetryStats]:

        try:
            if start_time is None:
                start_time = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

            if end_time is None:
                end_time = datetime.utcnow()

            start = start_time.isoformat() + "Z" if start_time.tzinfo is None else start_time.isoformat()
            end = end_time.isoformat() + "Z" if end_time.tzinfo is None else end_time.isoformat()

            flux_query = f'''
            from(bucket: "{settings.influxdb_bucket}")
                |> range(start: time(v: "{start}"), stop: time(v: "{end}"))
                |> filter(fn: (r) => r._measurement == "{self.MEASUREMENT}")
                |> filter(fn: (r) => r.device_id == "{device_id}")
            '''

            tables = self.query_api.query(
                flux_query,
                org=settings.influxdb_org,
            )

            stats = self._aggregate_stats(device_id, tables, start_time, end_time)

            return stats

        except Exception as e:
            logger.error(
                "Failed to get telemetry stats",
                device_id=device_id,
                error=str(e),
            )
            return None

    # ------------------------------------------------------------------
    # IMPORTANT FIX IS HERE
    # ------------------------------------------------------------------

    def _build_query(
        self,
        device_id: str,
        start_time: datetime,
        end_time: datetime,
        fields: Optional[List[str]] = None,
        aggregate: Optional[str] = None,
        interval: Optional[str] = None,
        limit: int = 1000,
    ) -> str:

        start = start_time.isoformat() + "Z" if start_time.tzinfo is None else start_time.isoformat()
        end = end_time.isoformat() + "Z" if end_time.tzinfo is None else end_time.isoformat()

        query = f'''
        from(bucket: "{settings.influxdb_bucket}")
            |> range(start: time(v: "{start}"), stop: time(v: "{end}"))
            |> filter(fn: (r) => r._measurement == "{self.MEASUREMENT}")
            |> filter(fn: (r) => r.device_id == "{device_id}")
        '''

        if fields:
            field_filters = " or ".join([f'r._field == "{f}"' for f in fields])
            query += f'|> filter(fn: (r) => {field_filters})\n'

        if aggregate and interval:
            query += f'|> aggregateWindow(every: {interval}, fn: {aggregate}, createEmpty: false)\n'

        # ---- PERMANENT FIX ----
        # convert row-per-field into one row per timestamp
        query += '''
            |> pivot(
                rowKey: ["_time"],
                columnKey: ["_field"],
                valueColumn: "_value"
            )
        '''

        query += f'|> sort(columns: ["_time"], desc: true)\n'
        query += f'|> limit(n: {limit})\n'

        return query

    # ------------------------------------------------------------------

    def _parse_record_to_point(self, record: FluxRecord) -> Optional[TelemetryPoint]:
        """
        Parse pivoted Flux record into TelemetryPoint.
        """

        try:
            values = record.values

            return TelemetryPoint(
                timestamp=record.get_time() or datetime.utcnow(),
                device_id=values.get("device_id", ""),
                voltage=values.get("voltage"),
                current=values.get("current"),
                power=values.get("power"),
                temperature=values.get("temperature"),
                schema_version=values.get("schema_version", "v1"),
                enrichment_status=EnrichmentStatus(
                    values.get("enrichment_status", "pending")
                ),
            )

        except Exception as e:
            logger.error(
                "Failed to parse Flux record",
                error=str(e),
            )
            return None

    # ------------------------------------------------------------------

    def _aggregate_stats(
        self,
        device_id: str,
        tables: List[Any],
        start_time: datetime,
        end_time: datetime,
    ) -> TelemetryStats:

        voltage_values = []
        current_values = []
        power_values = []
        temperature_values = []

        for table in tables:
            for record in table.records:
                field = record.get_field()
                value = record.get_value()

                if value is not None:
                    if field == "voltage":
                        voltage_values.append(value)
                    elif field == "current":
                        current_values.append(value)
                    elif field == "power":
                        power_values.append(value)
                    elif field == "temperature":
                        temperature_values.append(value)

        def calc(values: List[float]):
            if not values:
                return None, None, None
            return min(values), max(values), sum(values) / len(values)

        vmin, vmax, vavg = calc(voltage_values)
        cmin, cmax, cavg = calc(current_values)
        pmin, pmax, pavg = calc(power_values)
        tmin, tmax, tavg = calc(temperature_values)

        return TelemetryStats(
            device_id=device_id,
            start_time=start_time,
            end_time=end_time,
            voltage_min=vmin,
            voltage_max=vmax,
            voltage_avg=vavg,
            current_min=cmin,
            current_max=cmax,
            current_avg=cavg,
            power_min=pmin,
            power_max=pmax,
            power_avg=pavg,
            power_total=sum(power_values) if power_values else None,
            temperature_min=tmin,
            temperature_max=tmax,
            temperature_avg=tavg,
            data_points=len(voltage_values),
        )

    # ------------------------------------------------------------------

    def close(self) -> None:
        try:
            self.write_api.close()
            self.client.close()
            logger.info("InfluxDB client closed")
        except Exception as e:
            logger.error("Error closing InfluxDB client", error=str(e))
