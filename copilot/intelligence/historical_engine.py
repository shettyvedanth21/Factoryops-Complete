from typing import Dict

import pandas as pd


class HistoricalEngine:
    def compute(self, df: pd.DataFrame) -> Dict:
        if df.empty:
            return {
                "status": "no_data",
                "message": "No telemetry data available for selected range.",
                "metrics": {},
            }

        total_energy = float(df["energy_kwh"].sum())
        total_cost = float(df["cost_inr"].sum())
        total_runtime = float(df["runtime_minutes"].sum())
        total_idle = float(df["idle_minutes"].sum())
        total_downtime = float(df["downtime_minutes"].sum())
        total_possible_minutes = float(df["period_hours"].sum()) * 60.0

        idle_waste_pct = (
            total_idle / total_possible_minutes if total_possible_minutes > 0 else 0.0
        )

        return {
            "status": "ok",
            "metrics": {
                "total_energy_kwh": round(total_energy, 3),
                "total_cost_inr": round(total_cost, 3),
                "avg_power_kw": round(float(df["power_kw"].mean()), 3),
                "avg_voltage_v": round(float(df["voltage_v"].mean()), 3),
                "avg_pressure_bar": round(float(df["pressure_bar"].mean()), 3),
                "runtime_minutes": round(total_runtime, 3),
                "idle_minutes": round(total_idle, 3),
                "downtime_minutes": round(total_downtime, 3),
                "idle_waste_pct": round(idle_waste_pct, 6),
            },
        }
