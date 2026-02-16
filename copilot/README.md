# CITAGENT FactoryOps AI Copilot

Deterministic-first local industrial decision system.

## Architecture

- `simulation` - deterministic factory telemetry generation
- `storage` - SQLite + Parquet persistence and H/D/W/M/Y aggregates
- `intelligence` - deterministic historical, anomaly, forecast, and what-if engines
- `agent` - intent routing, governed prompting, local Ollama explanation
- `dashboard` - Streamlit monitoring and chat UI

## Governance Rules

- AI receives only structured deterministic results.
- AI never computes cost, forecast, or anomaly outputs.
- AI never accesses database directly.
- Anomaly detection runs on hourly data only (168-hour rolling baseline).
- Forecasting is monthly only using exponential smoothing (`alpha=0.3`).

## Setup

```bash
pip install -r requirements.txt
python main.py
```

Optional bootstrap only:

```bash
python main.py --no-dashboard
```

## Ollama

Use local Ollama with model:

- `llama3:8b`

Example:

```bash
ollama pull llama3:8b
ollama serve
```
