import logging
from dataclasses import dataclass
from typing import Dict, List

import numpy as np
import pandas as pd


LOGGER = logging.getLogger(__name__)


@dataclass
class SimulationConfig:
    start_date: str
    days: int
    machines: List[str]
    tariff_inr_per_kwh: float
    seed: int


class FactorySimulationEngine:
    def __init__(self, config: SimulationConfig):
        self.config = config

    def run(self) -> pd.DataFrame:
        LOGGER.info("Starting telemetry simulation")

        hours = self.config.days * 24
        timestamps = pd.date_range(
            start=self.config.start_date,
            periods=hours,
            freq="H",
            inclusive="left",
        )

        all_frames = []
        for idx, machine_id in enumerate(self.config.machines):
            machine_seed = self.config.seed + idx * 17
            rng = np.random.default_rng(machine_seed)
            frame = self._simulate_machine(machine_id, timestamps, rng)
            all_frames.append(frame)

        df = pd.concat(all_frames, ignore_index=True)
        df["cost_inr"] = df["energy_kwh"] * self.config.tariff_inr_per_kwh

        LOGGER.info(
            "Simulation complete | rows=%d | machines=%d",
            len(df),
            len(self.config.machines),
        )
        return df

    def _simulate_machine(
        self, machine_id: str, timestamps: pd.DatetimeIndex, rng: np.random.Generator
    ) -> pd.DataFrame:
        n = len(timestamps)
        hour_of_day = timestamps.hour.values
        day_of_week = timestamps.dayofweek.values

        base_power = {"M1": 48.0, "M2": 53.0, "M3": 44.0}[machine_id]
        voltage_base = {"M1": 415.0, "M2": 418.0, "M3": 412.0}[machine_id]
        pressure_base = {"M1": 7.0, "M2": 7.2, "M3": 6.8}[machine_id]

        daily_cycle = 6.0 * np.sin(2 * np.pi * hour_of_day / 24)
        weekly_cycle = 3.0 * np.cos(2 * np.pi * day_of_week / 7)

        power_kw = base_power + daily_cycle + weekly_cycle + rng.normal(0, 1.2, n)
        power_kw = np.clip(power_kw, 15.0, None)

        voltage_v = voltage_base + rng.normal(0, 3.0, n)
        pressure_bar = pressure_base + 0.3 * np.sin(2 * np.pi * hour_of_day / 24) + rng.normal(0, 0.15, n)

        outage_flag = rng.random(n) < 0.03
        downtime_minutes = np.where(outage_flag, rng.integers(10, 46, n), rng.integers(0, 8, n))
        runtime_minutes = np.clip(60 - downtime_minutes - rng.integers(0, 10, n), 0, 60)
        idle_minutes = np.clip(60 - runtime_minutes - downtime_minutes, 0, 60)

        utilization = runtime_minutes / 60.0
        energy_kwh = power_kw * utilization

        df = pd.DataFrame(
            {
                "timestamp": timestamps,
                "machine_id": machine_id,
                "power_kw": np.round(power_kw, 3),
                "voltage_v": np.round(voltage_v, 3),
                "pressure_bar": np.round(pressure_bar, 3),
                "runtime_minutes": runtime_minutes.astype(int),
                "idle_minutes": idle_minutes.astype(int),
                "downtime_minutes": downtime_minutes.astype(int),
                "energy_kwh": np.round(energy_kwh, 3),
            }
        )
        return df


def build_simulation_config(raw_cfg: Dict) -> SimulationConfig:
    sim = raw_cfg["simulation"]
    return SimulationConfig(
        start_date=sim["start_date"],
        days=int(sim["days"]),
        machines=list(sim["machines"]),
        tariff_inr_per_kwh=float(sim["tariff_inr_per_kwh"]),
        seed=int(sim["seed"]),
    )
