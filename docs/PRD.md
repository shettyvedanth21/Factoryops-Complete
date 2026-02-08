# Perpexility

# Energy Intelligence & Analytics Platform PRD (FINAL v2.0)

*Production-Ready | All Questions Resolved | LLD Phase Handover | February 7, 2026*

---

## Executive Summary

The **Energy Intelligence & Analytics Platform** is a **cloud-native, microservice-based SaaS** platform for **industrial energy telemetry ingestion, real-time rule evaluation, ML analytics, and operational reporting**.

**Phase-1 Scope**: Single simulated **electric bulb + energy meter (D1)** publishing realistic MQTT telemetry (voltage/current/power/temperature).

**Production Architecture**: Day-one scalability for multi-device industrial fleets (compressors/machines) without refactoring.

**Tech Stack**: AWS EKS -  EMQX MQTT -  InfluxDB -  PostgreSQL -  S3 -  React SPA -  scikit-learn/Prophet ML.

**Key Differentiators**:

- Zero telemetry loss - Real-time rules - ML on historical datasets - Multi-device ready from Phase-1

---

## Problem Statement

**Industrial Challenge**: No unified platform exists that delivers:

- Reliable high-frequency telemetry ingestion
- Real-time operational rules + alerting
- ML-driven anomaly detection + failure prediction
- Structured reporting for operations + management

**Current Solutions Fail**:

- Tight coupling of ingestion/analytics
- Poor streaming + ML pipeline separation
- Cannot scale from pilot → production
- Drop unstructured telemetry fields

**This Platform Delivers**: Decoupled microservices + MQTT backbone + dataset export → ML pipeline.

---

## Goals & Success Metrics

## Phase-1 Goals

`text✅ 100% simulator telemetry ingestion (no drops)
✅ Real-time dashboards + rules for D1  
✅ ML analytics on simulator history
✅ Multi-device architecture (1 active)
✅ Zero temporary/patch architecture`

## Production Metrics

| Metric | Target (p95) |
| --- | --- |
| Telemetry ingestion latency | ≤ 2s |
| Rule evaluation latency | ≤ 500ms |
| Dataset export latency | ≤ 2min |
| Dashboard refresh | ≤ 5s |
| Analytics job (7-day data) | ≤ 10min |
| Uptime | 99.9% |

---

## User Personas & Journeys

| Persona | Role | Key Journey |
| --- | --- | --- |
| **Operations Engineer** | Live monitoring | Login → Dashboard → D1 details → Live charts |
| **Plant Manager** | KPIs/Reports | Dashboard → Efficiency metrics → PDF report |
| **Maintenance Engineer** | Predictive | Analytics → Anomaly list → Failure predictions |
| **Energy Manager** | Optimization | Reports → 30-day consumption forecast |
| **Admin** | Configuration | Devices → Rules → Create temp>50°C alert |

**Core Navigation**: Dashboard -  Devices -  Rules -  Live Analytics -  Reporting

---

## Functional Requirements

## 1. Authentication

`text- Email/password + JWT (1h expiry)
- RBAC: Admin/Engineer
- Phase-1: Single tenant`

## 2. Dashboard

`textAggregates: Total devices • Active alerts • System health • Avg efficiency
Device Cards: D1 (status/health/efficiency/power)
→ Click → Device Details: Live KPIs + streaming charts`

## 3. Devices Module

`textPhase-1: D1 (bulb/meter)
Profile: ID=D1, type=bulb, location=Plant-A
UI: Multi-device list/table ready`

## 4. Rules Module

`textFilters: Search • Status • Device
Rule Form:
  Name: "Bulb Overheat"
  Scope: D1
  Property: temperature
  Condition: >
  Threshold: 50°C
  Notify: WhatsApp/Email/Telegram
  Status: Active/Paused

Execution: Real-time eval → Immediate trigger`

## 5. Live Analytics

`textInputs: Date range • D1 • Model • Type
Models (Phase-1):
├── Anomaly: IsolationForest + S-H-ESD
├── Prediction: XGBoost + RandomForest  
└── Forecast: Prophet + LSTM

Outputs: Anomalies • Failure prob • Time-to-failure`

## 6. Reporting

`textInputs: D1 • 7days • Anomaly • PDF
Output: Downloadable PDF/Excel/JSON`

---

## Phase-1 Simulator Specification

## Device D1: Electric Bulb + Energy Meter

`text**MQTT Topic**: devices/D1/telemetry
**Payload Schema** (JSON - STRICT):
{
  "device_id": "D1",
  "timestamp": "2026-02-07T11:26:00Z",
  "voltage": 230.5,      // V (200-250)
  "current": 0.85,       // A (0-2)
  "power": 195.9,        // W (0-500)
  "temperature": 45.2    // °C (20-80)
}`

## Simulator Behavior

`text- Publish interval: 5s (configurable)
- Realistic time-series patterns
- Fault injection capability (future anomalies)
- Treated as PRODUCTION device`

---

## System Architecture

`textPRODUCTION ARCHITECTURE (Phase-1 Ready)

Simulator(D1)
  ↓ MQTT 5s
EMQX Broker (Clustered)
  ↓ Fan-out Pub/Sub
 ┌─────────────────────────────────────────────────────┐
 │ Device Service    → PostgreSQL (metadata)           │
 │ Data Service      → InfluxDB (telemetry)            │
 │ Rule Engine       → PostgreSQL (rules) + Alerts     │
 │ Data Export       → S3 (historical datasets)        │
 └─────────────────────────────────────────────────────┘
           ↓ Near-RT Export (<2min)
    ┌──────────────┬─────────────────┐
    │ Analytics    │ Reporting       │
    │ Jobs (K8s)   │ Service         │
    └──────┬───────┘                 │
           ↓                         │
       ML Results ←──────────────────┘
             ↓
React SPA ← API Gateway + Auth (JWT)
(WebSocket Live)`

---

## Microservice Responsibilities

| Service | Storage | Core Function |
| --- | --- | --- |
| **Device** | PostgreSQL | Device CRUD + metadata enrichment |
| **Data** | **InfluxDB** | Telemetry parse/validate/store/query |
| **Rule Engine** | PostgreSQL | Real-time eval + notification trigger |
| **Data Export** | **S3** | Streaming TS → analytics datasets |
| **Analytics** | S3 | ML jobs: anomaly/forecast/predict |
| **Notification** | External | Twilio/WhatsApp + AWS SES + Telegram |
| **Auth** | PostgreSQL | JWT + RBAC |

---

## Telemetry Pipeline (Critical)

`textRaw MQTT → JSON Schema Validation → Parse → Normalize → Enrich → Storage

Validation Rules (Phase-1 STRICT):
├── Required: device_id=D1 + timestamp + V/A/P/T
├── Ranges: V(200-250), A(0-2), P(0-500), T(20-80)
├── Invalid → Dead Letter Queue (no drops)
└── Schema Evolution: Future pressure/vibration OK

CRITICAL: 100% field preservation for rules/analytics`

---

## ML Pipeline (Phase-1 Models)

| Analysis Type | Models | Input | Output |
| --- | --- | --- | --- |
| **Anomaly** | IsolationForest, S-H-ESD, Autoencoder | S3 TS datasets | Anomaly scores + timestamps |
| **Failure Prediction** | XGBoost, RandomForest, Survival (Cox) | Labeled failures | Failure prob + RUL |
| **Forecasting** | Prophet, LSTM, ARIMA/SARIMA | Historical KPIs | 24h/7d predictions |

**Execution**: Kubernetes Jobs (Argo Workflows) -  Free Docker containers -  SageMaker Studio Lab prototyping.

---

## Notifications (Production Providers)

| Channel | Provider | Config |
| --- | --- | --- |
| **Email** | **AWS SES** | SMTP + templates |
| **WhatsApp** | **Twilio** | API keys + WhatsApp Business |
| **Telegram** | Bot API | Bot token + chat IDs |

---

## Storage & Retention

`text**InfluxDB (Raw Telemetry)**: 90 days hot
├── Continuous Queries → 1h/1d aggregates
└── Auto-downsample older data

**S3 (Analytics Datasets)**: 90-day lifecycle
├── 0-30d: Standard
├── 30-90d: Glacier  
└── >90d: EXPIRE

**PostgreSQL**: Manual pruning (rules/devices)`

---

## Security Design (Phase-1)

`text**Implemented**:
├── Auth: Email/password → JWT (1h)
├── API: HTTPS + rate-limit
├── MQTT: TLS + ACL (devices/D1/*)
├── Data: KMS encryption at-rest
└── RBAC: Admin/Engineer

**Design Ready** (Phase-2):
├── Multi-tenant logical isolation
├── Audit logs (rules/reports)
└── Advanced IAM`

---

## Scalability & Reliability

`text**Scale**:
├── EKS HPA (CPU/requests)
├── EMQX clustering
├── InfluxDB sharding (future)
└── S3 partitioning

**Resilience**:
├── Istio circuit breakers
├── Dead letter queues
├── Multi-AZ EKS
├── Keda event-driven scaling
└── Centralized observability (Prometheus/Grafana/CloudWatch)`

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Simulator lacks real anomalies | Medium | Configurable fault injection |
| ML accuracy on Phase-1 data | High | Pre-trained baselines + synthetic augmentation |
| Notification costs | Low | Rate limits + batching |
| Export latency spikes | Medium | Dedicated export workers + backpressure |

**Assumptions**:

- AWS Free Tier sufficient Phase-1
- External simulator management
- Single tenant initially

---