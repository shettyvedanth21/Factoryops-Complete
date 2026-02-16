from typing import Dict, Optional, Tuple

from agent.intents import Intent
from intelligence.service import IntelligenceService


class ToolRouter:
    def __init__(self, intelligence: IntelligenceService):
        self.intelligence = intelligence

    def route(
        self,
        intent: Intent,
        user_query: str,
        machine_id: str,
        start_ts,
        end_ts,
        granularity: str,
        compare_machine: Optional[str] = None,
        forecast_days: int = 90,
        whatif_inputs: Optional[Dict] = None,
    ) -> Dict:
        whatif_inputs = whatif_inputs or {}

        if intent == Intent.WHATIF_QUERY:
            return self.intelligence.whatif(
                machine_id=machine_id,
                start_ts=start_ts,
                end_ts=end_ts,
                idle_reduction_pct=float(whatif_inputs.get("idle_reduction_pct", 0.0)),
                new_tariff_inr=whatif_inputs.get("new_tariff_inr"),
                efficiency_gain_pct=float(whatif_inputs.get("efficiency_gain_pct", 0.0)),
                downtime_range=whatif_inputs.get("downtime_range"),
            )

        if intent == Intent.FORECAST_QUERY:
            return self.intelligence.forecast(
                machine_id=machine_id,
                start_ts=start_ts,
                end_ts=end_ts,
                horizon_days=forecast_days,
            )

        if intent == Intent.OPTIMISE_QUERY:
            return self.intelligence.optimize(machine_id, start_ts, end_ts)

        if intent == Intent.ANOMALY_QUERY:
            return self.intelligence.anomalies(machine_id, start_ts, end_ts)

        if intent == Intent.COMPARE_QUERY and compare_machine:
            return self.intelligence.compare(
                machine_id, compare_machine, start_ts, end_ts, granularity
            )

        if intent in (Intent.HISTORICAL_QUERY, Intent.GENERAL_QUERY, Intent.COMPARE_QUERY):
            return self.intelligence.historical(machine_id, start_ts, end_ts, granularity)

        return {
            "result": {
                "status": "no_data",
                "message": "Unable to route request.",
            }
        }
