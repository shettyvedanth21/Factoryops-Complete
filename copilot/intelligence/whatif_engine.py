from typing import Dict, Optional, Tuple

import pandas as pd


class WhatIfEngine:
    def __init__(self, default_tariff_inr_per_kwh: float):
        self.default_tariff = default_tariff_inr_per_kwh

    def simulate(
        self,
        df_hourly: pd.DataFrame,
        idle_reduction_pct: float = 0.0,
        new_tariff_inr: Optional[float] = None,
        efficiency_gain_pct: float = 0.0,
        downtime_range: Optional[Tuple[float, float]] = None,
    ) -> Dict:
        if df_hourly.empty:
            return {
                "status": "no_data",
                "message": "No hourly data available for what-if simulation.",
            }

        base_energy = float(df_hourly["energy_kwh"].sum())
        base_idle_minutes = float(df_hourly["idle_minutes"].sum())
        base_downtime_minutes = float(df_hourly["downtime_minutes"].sum())
        base_tariff = self.default_tariff
        base_cost = base_energy * base_tariff

        total_minutes = float((df_hourly.get("period_hours", pd.Series([1] * len(df_hourly))).sum()) * 60)
        idle_ratio = (base_idle_minutes / total_minutes) if total_minutes else 0.0

        idle_reduction_factor = max(0.0, min(100.0, idle_reduction_pct)) / 100.0
        efficiency_factor = max(0.0, min(100.0, efficiency_gain_pct)) / 100.0

        energy_after_idle = base_energy * (1 - idle_ratio * idle_reduction_factor)
        energy_after_efficiency = energy_after_idle * (1 - efficiency_factor)

        downtime_adjustment_factor = 0.0
        if downtime_range is not None:
            low, high = downtime_range
            midpoint = (float(low) + float(high)) / 2.0
            if base_downtime_minutes > 0:
                downtime_adjustment_factor = midpoint / base_downtime_minutes

        adjusted_energy = energy_after_efficiency * (1 + downtime_adjustment_factor * 0.05)
        tariff = float(new_tariff_inr) if new_tariff_inr is not None else base_tariff
        adjusted_cost = adjusted_energy * tariff

        return {
            "status": "ok",
            "inputs": {
                "idle_reduction_pct": idle_reduction_pct,
                "new_tariff_inr": tariff,
                "efficiency_gain_pct": efficiency_gain_pct,
                "downtime_range": downtime_range,
            },
            "baseline": {
                "energy_kwh": round(base_energy, 3),
                "cost_inr": round(base_cost, 3),
                "idle_minutes": round(base_idle_minutes, 3),
                "downtime_minutes": round(base_downtime_minutes, 3),
            },
            "scenario": {
                "energy_kwh": round(adjusted_energy, 3),
                "cost_inr": round(adjusted_cost, 3),
            },
            "impact": {
                "energy_delta_kwh": round(adjusted_energy - base_energy, 3),
                "cost_delta_inr": round(adjusted_cost - base_cost, 3),
                "cost_saving_inr": round(base_cost - adjusted_cost, 3),
            },
        }
