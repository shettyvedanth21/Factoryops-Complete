import os
from typing import Dict

from agent.copilot import CopilotAgent
from agent.intents import IntentClassifier
from agent.memory import ConversationMemory
from agent.ollama_client import OllamaClient
from agent.prompt_builder import PromptBuilder
from agent.router import ToolRouter
from intelligence.anomaly_engine import AnomalyEngine
from intelligence.forecast_engine import ForecastEngine
from intelligence.historical_engine import HistoricalEngine
from intelligence.service import IntelligenceService
from intelligence.whatif_engine import WhatIfEngine
from simulation.engine import FactorySimulationEngine, build_simulation_config
from storage.repository import StorageLayer, build_storage_config


def build_storage(raw_cfg: Dict) -> StorageLayer:
    storage_cfg = build_storage_config(raw_cfg)
    tariff = float(raw_cfg["simulation"]["tariff_inr_per_kwh"])
    return StorageLayer(storage_cfg, tariff)


def build_intelligence(raw_cfg: Dict, storage: StorageLayer) -> IntelligenceService:
    anomaly_cfg = raw_cfg["intelligence"]["anomaly"]
    forecast_cfg = raw_cfg["intelligence"]["forecast"]
    tariff = float(raw_cfg["simulation"]["tariff_inr_per_kwh"])

    return IntelligenceService(
        storage=storage,
        historical_engine=HistoricalEngine(),
        anomaly_engine=AnomalyEngine(
            rolling_window_hours=int(anomaly_cfg["rolling_window_hours"]),
            zscore_threshold=float(anomaly_cfg["zscore_threshold"]),
            pressure_min_bar=float(anomaly_cfg["pressure_min_bar"]),
            pressure_max_bar=float(anomaly_cfg["pressure_max_bar"]),
        ),
        forecast_engine=ForecastEngine(
            alpha=float(forecast_cfg["alpha"]),
            tariff_inr_per_kwh=tariff,
        ),
        whatif_engine=WhatIfEngine(default_tariff_inr_per_kwh=tariff),
    )


def build_agent(raw_cfg: Dict, intelligence: IntelligenceService) -> CopilotAgent:
    agent_cfg = raw_cfg["agent"]

    return CopilotAgent(
        classifier=IntentClassifier(),
        router=ToolRouter(intelligence),
        memory=ConversationMemory(max_turns=int(agent_cfg["memory_turns"])),
        prompt_builder=PromptBuilder(),
        ollama=OllamaClient(
            base_url=os.getenv("OLLAMA_HOST", "http://ollama:11434"),
            model=agent_cfg["model"],
        ),
    )


def build_simulation_engine(raw_cfg: Dict) -> FactorySimulationEngine:
    sim_cfg = build_simulation_config(raw_cfg)
    return FactorySimulationEngine(sim_cfg)
