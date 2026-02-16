from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import pandas as pd

from intelligence.anomaly_engine import AnomalyEngine
from intelligence.forecast_engine import ForecastEngine
from intelligence.historical_engine import HistoricalEngine
from intelligence.whatif_engine import WhatIfEngine
from storage.repository import StorageLayer


@dataclass
class IntelligenceService:
    storage: StorageLayer
    historical_engine: HistoricalEngine
    anomaly_engine: AnomalyEngine
    forecast_engine: ForecastEngine
    whatif_engine: WhatIfEngine

    def historical(self, machine_id: str, start_ts, end_ts, granularity: str) -> Dict:
        df = self.storage.query(machine_id, start_ts, end_ts, granularity)
        return {
            "query": {
                "machine_id": machine_id,
                "start_ts": str(start_ts),
                "end_ts": str(end_ts),
                "granularity": granularity,
            },
            "result": self.historical_engine.compute(df),
        }

    def anomalies(self, machine_id: str, start_ts, end_ts) -> Dict:
        df = self.storage.query(machine_id, start_ts, end_ts, "H")
        return {
            "query": {
                "machine_id": machine_id,
                "start_ts": str(start_ts),
                "end_ts": str(end_ts),
                "granularity": "H",
            },
            "result": self.anomaly_engine.detect(df),
        }

    def forecast(self, machine_id: str, start_ts, end_ts, horizon_days: int) -> Dict:
        df_monthly = self.storage.query(machine_id, start_ts, end_ts, "M")
        return {
            "query": {
                "machine_id": machine_id,
                "start_ts": str(start_ts),
                "end_ts": str(end_ts),
                "granularity": "M",
                "horizon_days": horizon_days,
            },
            "result": self.forecast_engine.forecast_monthly(df_monthly, horizon_days),
        }

    def whatif(
        self,
        machine_id: str,
        start_ts,
        end_ts,
        idle_reduction_pct: float,
        new_tariff_inr: Optional[float],
        efficiency_gain_pct: float,
        downtime_range: Optional[Tuple[float, float]],
    ) -> Dict:
        df_hourly = self.storage.query(machine_id, start_ts, end_ts, "H")
        return {
            "query": {
                "machine_id": machine_id,
                "start_ts": str(start_ts),
                "end_ts": str(end_ts),
                "granularity": "H",
            },
            "result": self.whatif_engine.simulate(
                df_hourly,
                idle_reduction_pct=idle_reduction_pct,
                new_tariff_inr=new_tariff_inr,
                efficiency_gain_pct=efficiency_gain_pct,
                downtime_range=downtime_range,
            ),
        }

    def compare(self, machine_a: str, machine_b: str, start_ts, end_ts, granularity: str) -> Dict:
        a = self.storage.query(machine_a, start_ts, end_ts, granularity)
        b = self.storage.query(machine_b, start_ts, end_ts, granularity)
        a_hist = self.historical_engine.compute(a)
        b_hist = self.historical_engine.compute(b)
        return {
            "query": {
                "machine_a": machine_a,
                "machine_b": machine_b,
                "start_ts": str(start_ts),
                "end_ts": str(end_ts),
                "granularity": granularity,
            },
            "result": {
                "machine_a": a_hist,
                "machine_b": b_hist,
            },
        }

    def optimize(self, machine_id: str, start_ts, end_ts) -> Dict:
        hist = self.historical(machine_id, start_ts, end_ts, "D")
        anom = self.anomalies(machine_id, start_ts, end_ts)

        metrics = hist.get("result", {}).get("metrics", {})
        idle_waste_pct = metrics.get("idle_waste_pct", 0)
        total_anomalies = anom.get("result", {}).get("summary", {}).get("total_anomalies", 0)

        suggestions = []
        if idle_waste_pct > 0.20:
            suggestions.append("Idle time is high. Reduce idle minutes with improved shift planning.")
        if total_anomalies > 0:
            suggestions.append("Address detected power/voltage/pressure anomalies to avoid efficiency losses.")
        if not suggestions:
            suggestions.append("Current operations are stable. Focus on preventive maintenance and energy audits.")

        return {
            "query": {
                "machine_id": machine_id,
                "start_ts": str(start_ts),
                "end_ts": str(end_ts),
            },
            "result": {
                "historical_metrics": metrics,
                "anomaly_summary": anom.get("result", {}).get("summary", {}),
                "recommendations": suggestions,
            },
        }
