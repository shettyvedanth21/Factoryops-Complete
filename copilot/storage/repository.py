import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import pandas as pd


LOGGER = logging.getLogger(__name__)


@dataclass
class StorageConfig:
    db_path: str
    parquet_path: str
    tables: Dict[str, str]


class StorageLayer:
    def __init__(self, config: StorageConfig, tariff_inr_per_kwh: float):
        self.config = config
        self.tariff_inr_per_kwh = tariff_inr_per_kwh
        Path(self.config.db_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.config.parquet_path).parent.mkdir(parents=True, exist_ok=True)

    def save_hourly(self, df_hourly: pd.DataFrame) -> None:
        LOGGER.info("Persisting hourly telemetry to SQLite and Parquet")
        frame = df_hourly.copy()
        frame["timestamp"] = pd.to_datetime(frame["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect(self.config.db_path) as conn:
            frame.to_sql(self.config.tables["H"], conn, if_exists="replace", index=False)
        df_hourly.to_parquet(self.config.parquet_path, index=False)

    def build_aggregates(self, df_hourly: pd.DataFrame) -> None:
        LOGGER.info("Building deterministic aggregates for D/W/M/Y")
        hourly = df_hourly.copy()
        hourly["timestamp"] = pd.to_datetime(hourly["timestamp"])

        daily = self._aggregate(hourly, "D")
        weekly = self._aggregate(hourly, "W")
        monthly = self._aggregate(hourly, "M")
        yearly = self._aggregate(hourly, "Y")

        for frame in [daily, weekly, monthly, yearly]:
            frame["timestamp"] = pd.to_datetime(frame["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")

        with sqlite3.connect(self.config.db_path) as conn:
            daily.to_sql(self.config.tables["D"], conn, if_exists="replace", index=False)
            weekly.to_sql(self.config.tables["W"], conn, if_exists="replace", index=False)
            monthly.to_sql(self.config.tables["M"], conn, if_exists="replace", index=False)
            yearly.to_sql(self.config.tables["Y"], conn, if_exists="replace", index=False)

        LOGGER.info("Aggregates stored successfully")

    def _aggregate(self, hourly: pd.DataFrame, granularity: str) -> pd.DataFrame:
        frame = hourly.copy()
        if granularity == "D":
            frame["bucket"] = frame["timestamp"].dt.floor("D")
        elif granularity == "W":
            frame["bucket"] = frame["timestamp"].dt.to_period("W-MON").dt.to_timestamp()
        elif granularity == "M":
            frame["bucket"] = frame["timestamp"].dt.to_period("M").dt.to_timestamp()
        elif granularity == "Y":
            frame["bucket"] = frame["timestamp"].dt.to_period("Y").dt.to_timestamp()
        else:
            raise ValueError(f"Unsupported aggregate granularity: {granularity}")

        agg = (
            frame.groupby(["machine_id", "bucket"], as_index=False)
            .agg(
                power_kw=("power_kw", "mean"),
                voltage_v=("voltage_v", "mean"),
                pressure_bar=("pressure_bar", "mean"),
                runtime_minutes=("runtime_minutes", "sum"),
                idle_minutes=("idle_minutes", "sum"),
                downtime_minutes=("downtime_minutes", "sum"),
                energy_kwh=("energy_kwh", "sum"),
                period_hours=("timestamp", "count"),
            )
            .rename(columns={"bucket": "timestamp"})
        )
        agg["cost_inr"] = agg["energy_kwh"] * self.tariff_inr_per_kwh
        return agg

    def query(
        self,
        machine_id: Optional[str] = None,
        start_ts: Optional[pd.Timestamp] = None,
        end_ts: Optional[pd.Timestamp] = None,
        granularity: str = "H",
    ) -> pd.DataFrame:
        if granularity not in self.config.tables:
            raise ValueError(f"Unsupported granularity: {granularity}")

        table = self.config.tables[granularity]
        query = f"SELECT * FROM {table} WHERE 1=1"
        params = []

        if machine_id and machine_id != "ALL":
            query += " AND machine_id = ?"
            params.append(machine_id)
        if start_ts is not None:
            query += " AND timestamp >= ?"
            params.append(pd.to_datetime(start_ts).strftime("%Y-%m-%d %H:%M:%S"))
        if end_ts is not None:
            query += " AND timestamp <= ?"
            params.append(pd.to_datetime(end_ts).strftime("%Y-%m-%d %H:%M:%S"))

        query += " ORDER BY timestamp ASC"

        with sqlite3.connect(self.config.db_path) as conn:
            df = pd.read_sql_query(query, conn, params=params)

        if df.empty:
            return df

        df["timestamp"] = pd.to_datetime(df["timestamp"])
        if "period_hours" not in df.columns:
            df["period_hours"] = 1
        return df

    def list_machines(self) -> pd.DataFrame:
        with sqlite3.connect(self.config.db_path) as conn:
            return pd.read_sql_query(
                f"SELECT DISTINCT machine_id FROM {self.config.tables['H']} ORDER BY machine_id", conn
            )


def build_storage_config(raw_cfg: Dict) -> StorageConfig:
    paths = raw_cfg["paths"]
    tables = raw_cfg["storage"]
    return StorageConfig(
        db_path=paths["db_path"],
        parquet_path=paths["parquet_path"],
        tables={
            "H": tables["sqlite_table_hourly"],
            "D": tables["sqlite_table_daily"],
            "W": tables["sqlite_table_weekly"],
            "M": tables["sqlite_table_monthly"],
            "Y": tables["sqlite_table_yearly"],
        },
    )
