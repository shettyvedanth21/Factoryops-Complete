from typing import Dict, List

import numpy as np
import pandas as pd


class AnomalyEngine:
    def __init__(
        self,
        rolling_window_hours: int,
        zscore_threshold: float,
        pressure_min_bar: float,
        pressure_max_bar: float,
    ):
        self.rolling_window_hours = rolling_window_hours
        self.zscore_threshold = zscore_threshold
        self.pressure_min_bar = pressure_min_bar
        self.pressure_max_bar = pressure_max_bar

    def detect(self, df_hourly: pd.DataFrame) -> Dict:
        if df_hourly.empty:
            return {
                "status": "no_data",
                "message": "No hourly data available for anomaly detection.",
                "anomalies": [],
                "summary": {},
            }

        df = df_hourly.sort_values(["machine_id", "timestamp"]).copy()

        anomalies: List[Dict] = []
        for machine_id, group in df.groupby("machine_id"):
            g = group.copy()

            for metric in ["power_kw", "voltage_v"]:
                rolling_mean = g[metric].rolling(
                    window=self.rolling_window_hours,
                    min_periods=self.rolling_window_hours,
                ).mean()
                rolling_std = g[metric].rolling(
                    window=self.rolling_window_hours,
                    min_periods=self.rolling_window_hours,
                ).std(ddof=0)

                z = (g[metric] - rolling_mean) / rolling_std.replace(0, np.nan)
                outlier_idx = z.abs() > self.zscore_threshold

                for _, row in g[outlier_idx].iterrows():
                    idx = row.name
                    anomalies.append(
                        {
                            "timestamp": row["timestamp"].isoformat(),
                            "machine_id": machine_id,
                            "anomaly_type": f"{metric}_zscore",
                            "metric": metric,
                            "value": round(float(row[metric]), 3),
                            "z_score": round(float(z.loc[idx]), 3),
                            "details": f"Absolute z-score > {self.zscore_threshold}",
                        }
                    )

            pressure_breach = (
                (g["pressure_bar"] < self.pressure_min_bar)
                | (g["pressure_bar"] > self.pressure_max_bar)
            )
            for _, row in g[pressure_breach].iterrows():
                anomalies.append(
                    {
                        "timestamp": row["timestamp"].isoformat(),
                        "machine_id": machine_id,
                        "anomaly_type": "pressure_band",
                        "metric": "pressure_bar",
                        "value": round(float(row["pressure_bar"]), 3),
                        "z_score": None,
                        "details": (
                            f"Pressure outside [{self.pressure_min_bar}, {self.pressure_max_bar}] bar"
                        ),
                    }
                )

        type_counts = {}
        for item in anomalies:
            k = item["anomaly_type"]
            type_counts[k] = type_counts.get(k, 0) + 1

        return {
            "status": "ok",
            "anomalies": anomalies,
            "summary": {
                "total_anomalies": len(anomalies),
                "by_type": type_counts,
            },
        }
