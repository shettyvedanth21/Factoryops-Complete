from datetime import datetime
from typing import Dict, List

import pandas as pd


class ForecastEngine:
    def __init__(self, alpha: float, tariff_inr_per_kwh: float):
        self.alpha = alpha
        self.tariff = tariff_inr_per_kwh

    def forecast_monthly(self, df_monthly: pd.DataFrame, horizon_days: int) -> Dict:
        if df_monthly.empty:
            return {
                "status": "no_data",
                "message": "No monthly data available for forecasting.",
                "forecast": [],
            }

        horizon_months = self._days_to_months(horizon_days)
        series = df_monthly.sort_values("timestamp")["energy_kwh"].tolist()

        level = float(series[0])
        for value in series[1:]:
            level = self.alpha * float(value) + (1 - self.alpha) * level

        last_ts = pd.to_datetime(df_monthly["timestamp"].max())
        next_month_start = (last_ts + pd.offsets.MonthBegin(1)).to_pydatetime()

        results: List[Dict] = []
        for i in range(horizon_months):
            forecast_ts = pd.Timestamp(next_month_start) + pd.DateOffset(months=i)
            energy_kwh = round(level, 3)
            cost_inr = round(energy_kwh * self.tariff, 3)
            results.append(
                {
                    "month": forecast_ts.strftime("%Y-%m"),
                    "forecast_energy_kwh": energy_kwh,
                    "forecast_cost_inr": cost_inr,
                }
            )

        return {
            "status": "ok",
            "horizon_days": horizon_days,
            "horizon_months": horizon_months,
            "method": "exponential_smoothing_alpha_0.3",
            "forecast": results,
        }

    @staticmethod
    def _days_to_months(days: int) -> int:
        if days <= 30:
            return 1
        if days <= 90:
            return 3
        return 6
