import argparse
import logging
import subprocess
import sys
from pathlib import Path

from bootstrap import build_agent, build_intelligence, build_simulation_engine, build_storage
from core import load_config, setup_logging


LOGGER = logging.getLogger(__name__)


def bootstrap_system(config_path: str = "config.yaml"):
    cfg = load_config(config_path)
    setup_logging(cfg["paths"]["log_path"])

    LOGGER.info("Startup Step 1/7: Generate telemetry")
    simulator = build_simulation_engine(cfg)
    df_hourly = simulator.run()

    LOGGER.info("Startup Step 2/7: Store in SQLite and Parquet")
    storage = build_storage(cfg)
    storage.save_hourly(df_hourly)

    LOGGER.info("Startup Step 3/7: Build aggregates")
    storage.build_aggregates(df_hourly)

    LOGGER.info("Startup Step 4/7: Initialize intelligence layer")
    intelligence = build_intelligence(cfg, storage)

    LOGGER.info("Startup Step 5/7: Health check Ollama")
    agent = build_agent(cfg, intelligence)
    ollama_ok = agent.ollama.health_check()
    if not ollama_ok:
        LOGGER.warning(
            "Ollama model %s not available. Start Ollama and pull the model for full AI responses.",
            cfg["agent"]["model"],
        )

    return cfg, agent


def launch_dashboard(cfg):
    LOGGER.info("Startup Step 6/7: Launch Streamlit dashboard")
    cmd = [sys.executable, "-m", "streamlit", "run", "dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
    LOGGER.info("Running command: %s", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main():
    parser = argparse.ArgumentParser(description="CITAGENT FactoryOps AI Copilot")
    parser.add_argument("--no-dashboard", action="store_true", help="Prepare data/services without launching Streamlit")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    args = parser.parse_args()

    cfg, _agent = bootstrap_system(args.config)
    LOGGER.info("Startup Step 7/7: AI agent ready")

    if args.no_dashboard:
        LOGGER.info("--no-dashboard enabled, bootstrap completed.")
        return

    launch_dashboard(cfg)


if __name__ == "__main__":
    main()
