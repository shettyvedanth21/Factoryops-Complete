# Energy Intelligence Platform – Context

Frontend: Next.js (ui-web)

Backend services in use:
- device-service
- data-service
- rule-engine-service

Main flows:

Device telemetry
→ data-service
→ enrichment
→ InfluxDB
→ rule-engine-service (/api/v1/rules/evaluate)

Rules:
- CRUD in rule-engine-service
- evaluation in app/services/evaluator.py
- alerts stored in alerts table

Missing product features:
- Alerts API
- Alerts UI
- Rules UI

Rules backend is already complete.

DO NOT change rule evaluation logic unless required.