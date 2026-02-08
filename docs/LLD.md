# Low-Level Design Document
# Energy Intelligence & Analytics Platform

**Version:** 1.0  
**Date:** February 7, 2026  
**Phase:** Phase-1 (Single Device D1)  
**Based On:** PRD v2.0

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Technology Stack](#2-technology-stack)
3. [Database Schemas](#3-database-schemas)
4. [Microservices Architecture](#4-microservices-architecture)
5. [API Specifications](#5-api-specifications)
6. [MQTT & Telemetry Pipeline](#6-mqtt--telemetry-pipeline)
7. [Real-Time Rule Engine](#7-real-time-rule-engine)
8. [ML Analytics Pipeline](#8-ml-analytics-pipeline)
9. [Frontend Architecture](#9-frontend-architecture)
10. [Security Implementation](#10-security-implementation)
11. [Deployment Architecture](#11-deployment-architecture)
12. [Monitoring & Observability](#12-monitoring--observability)

---

## 1. System Overview

### 1.1 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                          │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  React SPA (Vite + TypeScript)                             │    │
│  │  - Redux Toolkit (State)                                    │    │
│  │  - React Query (Server State)                               │    │
│  │  - WebSocket Client (Live Updates)                          │    │
│  └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓ HTTPS
┌─────────────────────────────────────────────────────────────────────┐
│                         API GATEWAY LAYER                           │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  Kong Gateway / AWS API Gateway                             │    │
│  │  - JWT Validation                                           │    │
│  │  - Rate Limiting (100 req/min)                              │    │
│  │  - Request/Response Logging                                 │    │
│  └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      MICROSERVICES LAYER (EKS)                      │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │   Auth       │  │   Device     │  │    Data      │             │
│  │   Service    │  │   Service    │  │   Service    │             │
│  │   (Node.js)  │  │   (Go)       │  │   (Go)       │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │ Rule Engine  │  │ Data Export  │  │ Analytics    │             │
│  │   (Go)       │  │   (Python)   │  │   (Python)   │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐                                │
│  │ Notification │  │  Reporting   │                                │
│  │   (Node.js)  │  │   (Python)   │                                │
│  └──────────────┘  └──────────────┘                                │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         MESSAGE BROKER                              │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  EMQX (MQTT 5.0 Cluster)                                    │    │
│  │  - Topic: devices/D1/telemetry                              │    │
│  │  - QoS: 1 (at least once)                                   │    │
│  │  - Fan-out to multiple subscribers                          │    │
│  └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                    ↑                           ↓
┌──────────────────┐              ┌──────────────────────────────────┐
│  IoT Simulator   │              │       DATA STORAGE LAYER         │
│  (Python)        │              │                                  │
│  Device: D1      │              │  ┌────────────┐  ┌────────────┐ │
│  Interval: 5s    │              │  │ PostgreSQL │  │ InfluxDB   │ │
│                  │              │  │ (Metadata) │  │(Telemetry) │ │
└──────────────────┘              │  └────────────┘  └────────────┘ │
                                  │  ┌────────────┐                 │
                                  │  │  AWS S3    │                 │
                                  │  │ (Datasets) │                 │
                                  │  └────────────┘                 │
                                  └──────────────────────────────────┘
```

### 1.2 Data Flow

1. **Telemetry Ingestion**: Simulator → MQTT → Data Service → InfluxDB
2. **Real-Time Rules**: Data Service → Rule Engine → Notification Service
3. **Analytics**: Data Export → S3 → Analytics Jobs → Results Storage
4. **Dashboard**: Frontend → API Gateway → Services → WebSocket (Live)

---

## 2. Technology Stack

### 2.1 Backend Services

| Service | Language | Framework | Purpose |
|---------|----------|-----------|---------|
| Auth Service | Node.js 20 | Express.js | Authentication & Authorization |
| Device Service | Go 1.21 | Gin | Device management & metadata |
| Data Service | Go 1.21 | Gin | Telemetry ingestion & querying |
| Rule Engine | Go 1.21 | Gin | Real-time rule evaluation |
| Data Export | Python 3.11 | FastAPI | Dataset preparation for ML |
| Analytics | Python 3.11 | FastAPI | ML model execution |
| Notification | Node.js 20 | Express.js | Multi-channel alerting |
| Reporting | Python 3.11 | FastAPI | Report generation |

### 2.2 Infrastructure

- **Container Orchestration**: Kubernetes (AWS EKS 1.28)
- **Message Broker**: EMQX 5.3 (MQTT)
- **API Gateway**: Kong Gateway 3.4
- **Service Mesh**: Istio 1.20 (optional Phase-2)

### 2.3 Databases

- **PostgreSQL 15**: Device metadata, users, rules, analytics results
- **InfluxDB 2.7**: Time-series telemetry data
- **Redis 7**: Session cache, rate limiting

### 2.4 Storage

- **AWS S3**: ML datasets, reports, backups

### 2.5 Frontend

- **Framework**: React 18.2 + TypeScript 5.3
- **Build Tool**: Vite 5.0
- **State Management**: Redux Toolkit + React Query
- **UI Library**: Material-UI (MUI) 5.14
- **Charting**: Recharts, Apache ECharts
- **WebSocket**: Socket.io-client

### 2.6 ML/Analytics

- **Libraries**: scikit-learn, Prophet, XGBoost, PyTorch
- **Execution**: Kubernetes Jobs via Argo Workflows
- **Development**: Jupyter notebooks, SageMaker Studio Lab

### 2.7 Monitoring

- **Metrics**: Prometheus + Grafana
- **Logs**: Fluent Bit → CloudWatch Logs
- **Tracing**: Jaeger (optional)
- **Uptime**: AWS CloudWatch Alarms

---

## 3. Database Schemas

### 3.1 PostgreSQL Schema

#### 3.1.1 Users Table

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'engineer')),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
```

#### 3.1.2 Devices Table

```sql
CREATE TABLE devices (
    id VARCHAR(50) PRIMARY KEY,  -- e.g., 'D1'
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL,  -- 'bulb', 'compressor', etc.
    location VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'maintenance', 'error')),
    metadata JSONB,  -- Flexible storage for device-specific attributes
    health_score NUMERIC(5,2),  -- 0-100
    last_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_devices_type ON devices(type);
CREATE INDEX idx_devices_status ON devices(status);
CREATE INDEX idx_devices_last_seen ON devices(last_seen);
```

#### 3.1.3 Rules Table

```sql
CREATE TABLE rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    device_id VARCHAR(50) REFERENCES devices(id) ON DELETE CASCADE,
    property VARCHAR(100) NOT NULL,  -- 'temperature', 'power', etc.
    operator VARCHAR(20) NOT NULL CHECK (operator IN ('>', '<', '>=', '<=', '=', '!=')),
    threshold NUMERIC(10,2) NOT NULL,
    severity VARCHAR(50) DEFAULT 'medium' CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'paused', 'archived')),
    notification_channels TEXT[],  -- ['email', 'whatsapp', 'telegram']
    cooldown_minutes INTEGER DEFAULT 15,  -- Min time between notifications
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_triggered TIMESTAMP
);

CREATE INDEX idx_rules_device_id ON rules(device_id);
CREATE INDEX idx_rules_status ON rules(status);
CREATE INDEX idx_rules_property ON rules(property);
```

#### 3.1.4 Alerts Table

```sql
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id UUID REFERENCES rules(id) ON DELETE CASCADE,
    device_id VARCHAR(50) REFERENCES devices(id) ON DELETE CASCADE,
    severity VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    actual_value NUMERIC(10,2),
    threshold_value NUMERIC(10,2),
    status VARCHAR(50) DEFAULT 'open' CHECK (status IN ('open', 'acknowledged', 'resolved', 'suppressed')),
    acknowledged_by UUID REFERENCES users(id),
    acknowledged_at TIMESTAMP,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_alerts_device_id ON alerts(device_id);
CREATE INDEX idx_alerts_rule_id ON alerts(rule_id);
CREATE INDEX idx_alerts_status ON alerts(status);
CREATE INDEX idx_alerts_created_at ON alerts(created_at DESC);
```

#### 3.1.5 Analytics Results Table

```sql
CREATE TABLE analytics_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id VARCHAR(100) UNIQUE NOT NULL,
    device_id VARCHAR(50) REFERENCES devices(id) ON DELETE CASCADE,
    analysis_type VARCHAR(50) NOT NULL CHECK (analysis_type IN ('anomaly', 'prediction', 'forecast')),
    model_name VARCHAR(100) NOT NULL,
    date_range_start TIMESTAMP NOT NULL,
    date_range_end TIMESTAMP NOT NULL,
    results JSONB NOT NULL,  -- Flexible storage for model outputs
    accuracy_metrics JSONB,  -- Precision, recall, RMSE, etc.
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    error_message TEXT,
    execution_time_seconds INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_analytics_device_id ON analytics_results(device_id);
CREATE INDEX idx_analytics_type ON analytics_results(analysis_type);
CREATE INDEX idx_analytics_created_at ON analytics_results(created_at DESC);
```

#### 3.1.6 Notification Logs Table

```sql
CREATE TABLE notification_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id UUID REFERENCES alerts(id) ON DELETE CASCADE,
    channel VARCHAR(50) NOT NULL,  -- 'email', 'whatsapp', 'telegram'
    recipient VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed', 'bounced')),
    provider_response JSONB,
    attempts INTEGER DEFAULT 1,
    sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_notification_logs_alert_id ON notification_logs(alert_id);
CREATE INDEX idx_notification_logs_status ON notification_logs(status);
```

### 3.2 InfluxDB Schema

#### 3.2.1 Measurement: device_telemetry

```
Measurement: device_telemetry

Tags:
  - device_id (string): Device identifier (e.g., "D1")
  - device_type (string): Device type (e.g., "bulb")
  - location (string): Physical location

Fields:
  - voltage (float): Voltage in V
  - current (float): Current in A
  - power (float): Power in W
  - temperature (float): Temperature in °C

Timestamp: RFC3339 format (nanosecond precision)

Example:
device_telemetry,device_id=D1,device_type=bulb,location=Plant-A voltage=230.5,current=0.85,power=195.9,temperature=45.2 1707307560000000000
```

#### 3.2.2 Continuous Queries

```flux
// Hourly aggregates
option task = {name: "hourly_aggregates", every: 1h}

from(bucket: "telemetry")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "device_telemetry")
  |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
  |> to(bucket: "telemetry_hourly", org: "energy-platform")

// Daily aggregates
option task = {name: "daily_aggregates", every: 1d}

from(bucket: "telemetry")
  |> range(start: -1d)
  |> filter(fn: (r) => r._measurement == "device_telemetry")
  |> aggregateWindow(every: 1d, fn: mean, createEmpty: false)
  |> to(bucket: "telemetry_daily", org: "energy-platform")
```

#### 3.2.3 Retention Policies

```
Bucket: telemetry (default)
  - Retention: 90 days
  - Shard duration: 1 day

Bucket: telemetry_hourly
  - Retention: 365 days
  - Shard duration: 7 days

Bucket: telemetry_daily
  - Retention: 1825 days (5 years)
  - Shard duration: 30 days
```

---

## 4. Microservices Architecture

### 4.1 Auth Service (Node.js)

#### 4.1.1 Responsibilities
- User authentication (login/logout)
- JWT token generation and validation
- Password hashing (bcrypt)
- Role-based access control (RBAC)

#### 4.1.2 Endpoints

```typescript
POST   /api/auth/login          // User login
POST   /api/auth/logout         // User logout
POST   /api/auth/refresh        // Refresh JWT token
GET    /api/auth/validate       // Validate JWT token
POST   /api/auth/register       // User registration (admin only)
```

#### 4.1.3 Technology Stack
- **Framework**: Express.js 4.18
- **Auth**: jsonwebtoken, bcrypt
- **Validation**: Joi
- **Database**: PostgreSQL (pg library)

#### 4.1.4 Key Components

```typescript
// src/models/User.ts
export interface User {
  id: string;
  email: string;
  passwordHash: string;
  fullName: string;
  role: 'admin' | 'engineer';
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
  lastLogin?: Date;
}

// src/services/AuthService.ts
export class AuthService {
  async login(email: string, password: string): Promise<{ token: string; user: User }>;
  async validateToken(token: string): Promise<User>;
  async refreshToken(refreshToken: string): Promise<string>;
  async logout(userId: string): Promise<void>;
}

// src/middleware/authMiddleware.ts
export const authenticateJWT = async (req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).json({ error: 'No token provided' });
  
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    req.user = decoded;
    next();
  } catch (error) {
    res.status(403).json({ error: 'Invalid token' });
  }
};

export const authorizeRoles = (...roles: string[]) => {
  return (req, res, next) => {
    if (!roles.includes(req.user.role)) {
      return res.status(403).json({ error: 'Insufficient permissions' });
    }
    next();
  };
};
```

#### 4.1.5 Configuration

```yaml
# config/auth-service.yaml
server:
  port: 3001
  
jwt:
  secret: ${JWT_SECRET}
  expiresIn: 1h
  refreshExpiresIn: 7d
  
database:
  host: postgres-service
  port: 5432
  database: energy_platform
  user: ${DB_USER}
  password: ${DB_PASSWORD}
  
redis:
  host: redis-service
  port: 6379
  ttl: 3600
```

---

### 4.2 Device Service (Go)

#### 4.2.1 Responsibilities
- Device CRUD operations
- Device metadata management
- Device health score calculation
- Device status monitoring

#### 4.2.2 Endpoints

```go
GET    /api/devices              // List all devices
GET    /api/devices/:id          // Get device details
POST   /api/devices              // Register new device (admin)
PUT    /api/devices/:id          // Update device
DELETE /api/devices/:id          // Delete device (admin)
GET    /api/devices/:id/health   // Get device health metrics
GET    /api/devices/:id/status   // Get device current status
```

#### 4.2.3 Data Models

```go
// models/device.go
package models

import (
    "time"
    "github.com/google/uuid"
)

type Device struct {
    ID          string                 `json:"id" db:"id"`
    Name        string                 `json:"name" db:"name"`
    Type        string                 `json:"type" db:"type"`
    Location    string                 `json:"location" db:"location"`
    Status      DeviceStatus           `json:"status" db:"status"`
    Metadata    map[string]interface{} `json:"metadata" db:"metadata"`
    HealthScore float64                `json:"health_score" db:"health_score"`
    LastSeen    *time.Time             `json:"last_seen" db:"last_seen"`
    CreatedAt   time.Time              `json:"created_at" db:"created_at"`
    UpdatedAt   time.Time              `json:"updated_at" db:"updated_at"`
}

type DeviceStatus string

const (
    DeviceStatusActive      DeviceStatus = "active"
    DeviceStatusInactive    DeviceStatus = "inactive"
    DeviceStatusMaintenance DeviceStatus = "maintenance"
    DeviceStatusError       DeviceStatus = "error"
)

type DeviceHealth struct {
    DeviceID       string    `json:"device_id"`
    HealthScore    float64   `json:"health_score"`
    UptimePercent  float64   `json:"uptime_percent"`
    AvgResponseMs  float64   `json:"avg_response_ms"`
    ErrorRate      float64   `json:"error_rate"`
    LastCalculated time.Time `json:"last_calculated"`
}
```

#### 4.2.4 Service Layer

```go
// services/device_service.go
package services

import (
    "context"
    "github.com/your-org/energy-platform/models"
)

type DeviceService interface {
    GetAllDevices(ctx context.Context) ([]models.Device, error)
    GetDeviceByID(ctx context.Context, id string) (*models.Device, error)
    CreateDevice(ctx context.Context, device *models.Device) error
    UpdateDevice(ctx context.Context, device *models.Device) error
    DeleteDevice(ctx context.Context, id string) error
    CalculateHealthScore(ctx context.Context, deviceID string) (float64, error)
    UpdateLastSeen(ctx context.Context, deviceID string) error
}

type deviceService struct {
    repo DeviceRepository
    dataService DataServiceClient
}

func (s *deviceService) CalculateHealthScore(ctx context.Context, deviceID string) (float64, error) {
    // Get telemetry stats from last 24h
    stats, err := s.dataService.GetDeviceStats(ctx, deviceID, 24)
    if err != nil {
        return 0, err
    }
    
    // Calculate health score based on:
    // - Uptime: 40%
    // - Data quality (missing points): 30%
    // - Error rate: 20%
    // - Response time: 10%
    
    uptime := stats.UptimePercent * 0.4
    dataQuality := (1 - stats.MissingDataRate) * 0.3
    errorScore := (1 - stats.ErrorRate) * 0.2
    responseScore := calculateResponseScore(stats.AvgResponseMs) * 0.1
    
    healthScore := uptime + dataQuality + errorScore + responseScore
    
    return healthScore * 100, nil
}

func calculateResponseScore(avgMs float64) float64 {
    if avgMs <= 1000 {
        return 1.0
    } else if avgMs <= 2000 {
        return 0.8
    } else if avgMs <= 5000 {
        return 0.5
    }
    return 0.2
}
```

---

### 4.3 Data Service (Go)

#### 4.3.1 Responsibilities
- MQTT subscription and message handling
- Telemetry validation and parsing
- InfluxDB write operations
- Telemetry query API
- Dead letter queue management

#### 4.3.2 Endpoints

```go
GET    /api/data/telemetry/:deviceId      // Get device telemetry (with filters)
GET    /api/data/telemetry/:deviceId/live // WebSocket for real-time data
GET    /api/data/stats/:deviceId           // Get aggregated statistics
POST   /api/data/query                     // Custom InfluxDB query
```

#### 4.3.3 MQTT Handler

```go
// handlers/mqtt_handler.go
package handlers

import (
    "encoding/json"
    "log"
    mqtt "github.com/eclipse/paho.mqtt.golang"
    influxdb2 "github.com/influxdata/influxdb-client-go/v2"
)

type TelemetryPayload struct {
    DeviceID    string  `json:"device_id" validate:"required"`
    Timestamp   string  `json:"timestamp" validate:"required"`
    Voltage     float64 `json:"voltage" validate:"required,min=200,max=250"`
    Current     float64 `json:"current" validate:"required,min=0,max=2"`
    Power       float64 `json:"power" validate:"required,min=0,max=500"`
    Temperature float64 `json:"temperature" validate:"required,min=20,max=80"`
}

type MQTTHandler struct {
    influxClient influxdb2.Client
    writeAPI     influxdb2.WriteAPI
    validator    *validator.Validate
    dlq          DeadLetterQueue
    ruleEngine   RuleEngineClient
}

func (h *MQTTHandler) HandleTelemetry(client mqtt.Client, msg mqtt.Message) {
    var payload TelemetryPayload
    
    // Parse JSON
    if err := json.Unmarshal(msg.Payload(), &payload); err != nil {
        log.Printf("Failed to parse telemetry: %v", err)
        h.dlq.Send(msg.Payload(), "parse_error", err.Error())
        return
    }
    
    // Validate payload
    if err := h.validator.Struct(payload); err != nil {
        log.Printf("Validation failed: %v", err)
        h.dlq.Send(msg.Payload(), "validation_error", err.Error())
        return
    }
    
    // Write to InfluxDB
    if err := h.writeToInfluxDB(payload); err != nil {
        log.Printf("Failed to write to InfluxDB: %v", err)
        h.dlq.Send(msg.Payload(), "write_error", err.Error())
        return
    }
    
    // Trigger rule evaluation (async)
    go h.ruleEngine.EvaluateRules(payload)
    
    log.Printf("Telemetry processed: device=%s, power=%.2fW", payload.DeviceID, payload.Power)
}

func (h *MQTTHandler) writeToInfluxDB(payload TelemetryPayload) error {
    p := influxdb2.NewPoint(
        "device_telemetry",
        map[string]string{
            "device_id":   payload.DeviceID,
            "device_type": "bulb",
            "location":    "Plant-A",
        },
        map[string]interface{}{
            "voltage":     payload.Voltage,
            "current":     payload.Current,
            "power":       payload.Power,
            "temperature": payload.Temperature,
        },
        parseTimestamp(payload.Timestamp),
    )
    
    h.writeAPI.WritePoint(p)
    return nil
}
```

#### 4.3.4 Query Service

```go
// services/query_service.go
package services

import (
    "context"
    "fmt"
    "time"
    influxdb2 "github.com/influxdata/influxdb-client-go/v2"
)

type TelemetryQuery struct {
    DeviceID  string    `json:"device_id"`
    StartTime time.Time `json:"start_time"`
    EndTime   time.Time `json:"end_time"`
    Fields    []string  `json:"fields"`
    Aggregate string    `json:"aggregate"` // mean, max, min, sum
    Interval  string    `json:"interval"`  // 1m, 5m, 1h
}

type QueryService struct {
    influxClient influxdb2.Client
}

func (s *QueryService) QueryTelemetry(ctx context.Context, query TelemetryQuery) ([]TelemetryPoint, error) {
    queryAPI := s.influxClient.QueryAPI("")
    
    fluxQuery := fmt.Sprintf(`
        from(bucket: "telemetry")
          |> range(start: %s, stop: %s)
          |> filter(fn: (r) => r._measurement == "device_telemetry")
          |> filter(fn: (r) => r.device_id == "%s")
          |> filter(fn: (r) => %s)
          |> aggregateWindow(every: %s, fn: %s, createEmpty: false)
    `, 
        query.StartTime.Format(time.RFC3339),
        query.EndTime.Format(time.RFC3339),
        query.DeviceID,
        buildFieldFilter(query.Fields),
        query.Interval,
        query.Aggregate,
    )
    
    result, err := queryAPI.Query(ctx, fluxQuery)
    if err != nil {
        return nil, err
    }
    
    return parseQueryResult(result), nil
}
```

---

### 4.4 Rule Engine Service (Go)

#### 4.4.1 Responsibilities
- Real-time rule evaluation
- Alert generation
- Cooldown management
- Integration with notification service

#### 4.4.2 Endpoints

```go
GET    /api/rules              // List all rules
GET    /api/rules/:id          // Get rule details
POST   /api/rules              // Create new rule
PUT    /api/rules/:id          // Update rule
DELETE /api/rules/:id          // Delete rule
PATCH  /api/rules/:id/status   // Activate/pause rule
POST   /api/rules/evaluate     // Manual rule evaluation
```

#### 4.4.3 Rule Evaluator

```go
// engine/rule_evaluator.go
package engine

import (
    "context"
    "time"
    "github.com/your-org/energy-platform/models"
)

type RuleEvaluator struct {
    ruleRepo         RuleRepository
    alertRepo        AlertRepository
    notificationSvc  NotificationServiceClient
    deviceSvc        DeviceServiceClient
}

func (e *RuleEvaluator) EvaluateRules(ctx context.Context, telemetry TelemetryPayload) error {
    // Get active rules for this device
    rules, err := e.ruleRepo.GetActiveRulesByDevice(ctx, telemetry.DeviceID)
    if err != nil {
        return err
    }
    
    for _, rule := range rules {
        if e.shouldEvaluate(rule) {
            if triggered := e.evaluateRule(rule, telemetry); triggered {
                e.handleRuleTrigger(ctx, rule, telemetry)
            }
        }
    }
    
    return nil
}

func (e *RuleEvaluator) evaluateRule(rule models.Rule, telemetry TelemetryPayload) bool {
    actualValue := e.extractValue(telemetry, rule.Property)
    threshold := rule.Threshold
    
    switch rule.Operator {
    case ">":
        return actualValue > threshold
    case "<":
        return actualValue < threshold
    case ">=":
        return actualValue >= threshold
    case "<=":
        return actualValue <= threshold
    case "=":
        return actualValue == threshold
    case "!=":
        return actualValue != threshold
    default:
        return false
    }
}

func (e *RuleEvaluator) shouldEvaluate(rule models.Rule) bool {
    if rule.Status != "active" {
        return false
    }
    
    // Check cooldown period
    if rule.LastTriggered != nil {
        cooldownExpiry := rule.LastTriggered.Add(time.Duration(rule.CooldownMinutes) * time.Minute)
        if time.Now().Before(cooldownExpiry) {
            return false
        }
    }
    
    return true
}

func (e *RuleEvaluator) handleRuleTrigger(ctx context.Context, rule models.Rule, telemetry TelemetryPayload) {
    // Create alert
    alert := &models.Alert{
        RuleID:         rule.ID,
        DeviceID:       rule.DeviceID,
        Severity:       rule.Severity,
        Message:        e.buildAlertMessage(rule, telemetry),
        ActualValue:    e.extractValue(telemetry, rule.Property),
        ThresholdValue: rule.Threshold,
        Status:         "open",
        CreatedAt:      time.Now(),
    }
    
    if err := e.alertRepo.Create(ctx, alert); err != nil {
        log.Printf("Failed to create alert: %v", err)
        return
    }
    
    // Update rule last_triggered
    e.ruleRepo.UpdateLastTriggered(ctx, rule.ID, time.Now())
    
    // Send notifications (async)
    go e.notificationSvc.SendAlertNotifications(alert, rule.NotificationChannels)
}

func (e *RuleEvaluator) buildAlertMessage(rule models.Rule, telemetry TelemetryPayload) string {
    actualValue := e.extractValue(telemetry, rule.Property)
    return fmt.Sprintf(
        "Alert: %s - Device %s %s is %.2f (threshold: %s %.2f)",
        rule.Name,
        telemetry.DeviceID,
        rule.Property,
        actualValue,
        rule.Operator,
        rule.Threshold,
    )
}

func (e *RuleEvaluator) extractValue(telemetry TelemetryPayload, property string) float64 {
    switch property {
    case "voltage":
        return telemetry.Voltage
    case "current":
        return telemetry.Current
    case "power":
        return telemetry.Power
    case "temperature":
        return telemetry.Temperature
    default:
        return 0
    }
}
```

---

### 4.5 Data Export Service (Python)

#### 4.5.1 Responsibilities
- Export telemetry data from InfluxDB to S3
- Dataset preparation for ML models
- Scheduled and on-demand exports
- Data transformation and feature engineering

#### 4.5.2 Endpoints

```python
# FastAPI endpoints
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime

app = FastAPI()

class ExportRequest(BaseModel):
    device_id: str
    start_time: datetime
    end_time: datetime
    format: str = "parquet"  # csv, parquet, json
    features: list[str] = ["voltage", "current", "power", "temperature"]

@app.post("/api/export/dataset")
async def export_dataset(request: ExportRequest, background_tasks: BackgroundTasks):
    """Export dataset to S3 for ML processing"""
    job_id = generate_job_id()
    background_tasks.add_task(process_export, job_id, request)
    return {"job_id": job_id, "status": "queued"}

@app.get("/api/export/status/{job_id}")
async def get_export_status(job_id: str):
    """Get export job status"""
    pass

@app.get("/api/export/download/{job_id}")
async def download_export(job_id: str):
    """Get S3 presigned URL for download"""
    pass
```

#### 4.5.3 Export Worker

```python
# workers/export_worker.py
import pandas as pd
from influxdb_client import InfluxDBClient
import boto3
from typing import List
import logging

class DataExporter:
    def __init__(self, influx_client: InfluxDBClient, s3_client: boto3.client):
        self.influx = influx_client
        self.s3 = s3_client
        self.bucket_name = "energy-platform-datasets"
        
    def export_dataset(self, 
                       device_id: str, 
                       start_time: datetime, 
                       end_time: datetime,
                       features: List[str]) -> str:
        """
        Export telemetry data and prepare for ML
        Returns: S3 key of exported dataset
        """
        # Query InfluxDB
        query = f'''
        from(bucket: "telemetry")
          |> range(start: {start_time.isoformat()}, stop: {end_time.isoformat()})
          |> filter(fn: (r) => r._measurement == "device_telemetry")
          |> filter(fn: (r) => r.device_id == "{device_id}")
          |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        '''
        
        # Execute query and convert to DataFrame
        result = self.influx.query_api().query_data_frame(query)
        df = pd.DataFrame(result)
        
        # Feature engineering
        df = self._engineer_features(df, features)
        
        # Data quality checks
        df = self._clean_data(df)
        
        # Export to S3
        s3_key = self._upload_to_s3(df, device_id, start_time, end_time)
        
        logging.info(f"Exported {len(df)} records to {s3_key}")
        return s3_key
    
    def _engineer_features(self, df: pd.DataFrame, features: List[str]) -> pd.DataFrame:
        """Add derived features for ML"""
        # Time-based features
        df['hour'] = df['_time'].dt.hour
        df['day_of_week'] = df['_time'].dt.dayofweek
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        # Rolling statistics (5-minute window)
        for feature in features:
            if feature in df.columns:
                df[f'{feature}_rolling_mean'] = df[feature].rolling(window=60).mean()
                df[f'{feature}_rolling_std'] = df[feature].rolling(window=60).std()
        
        # Power factor
        if 'voltage' in df.columns and 'current' in df.columns and 'power' in df.columns:
            df['power_factor'] = df['power'] / (df['voltage'] * df['current'])
            df['power_factor'] = df['power_factor'].clip(0, 1)
        
        # Rate of change
        for feature in features:
            if feature in df.columns:
                df[f'{feature}_rate'] = df[feature].diff()
        
        return df
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove outliers and handle missing values"""
        # Remove duplicate timestamps
        df = df.drop_duplicates(subset=['_time'])
        
        # Handle missing values
        df = df.fillna(method='ffill').fillna(method='bfill')
        
        # Remove statistical outliers (Z-score > 3)
        from scipy import stats
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        z_scores = np.abs(stats.zscore(df[numeric_cols]))
        df = df[(z_scores < 3).all(axis=1)]
        
        return df
    
    def _upload_to_s3(self, df: pd.DataFrame, device_id: str, start: datetime, end: datetime) -> str:
        """Upload DataFrame to S3"""
        s3_key = f"datasets/{device_id}/{start.strftime('%Y%m%d')}_{end.strftime('%Y%m%d')}.parquet"
        
        # Convert to Parquet
        parquet_buffer = io.BytesIO()
        df.to_parquet(parquet_buffer, engine='pyarrow', compression='snappy')
        parquet_buffer.seek(0)
        
        # Upload to S3
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key=s3_key,
            Body=parquet_buffer,
            Metadata={
                'device_id': device_id,
                'start_time': start.isoformat(),
                'end_time': end.isoformat(),
                'record_count': str(len(df))
            }
        )
        
        return s3_key
```

---

### 4.6 Analytics Service (Python)

#### 4.6.1 Responsibilities
- ML model training and inference
- Anomaly detection
- Failure prediction
- Energy forecasting
- Model versioning and tracking

#### 4.6.2 ML Models Implementation

```python
# models/anomaly_detection.py
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import numpy as np
import pandas as pd

class AnomalyDetector:
    def __init__(self, contamination=0.1):
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        self.scaler = StandardScaler()
        
    def train(self, df: pd.DataFrame, features: List[str]):
        """Train anomaly detection model"""
        X = df[features].values
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        
    def predict(self, df: pd.DataFrame, features: List[str]) -> pd.DataFrame:
        """Detect anomalies in new data"""
        X = df[features].values
        X_scaled = self.scaler.transform(X)
        
        # Get anomaly scores (-1 for anomalies, 1 for normal)
        predictions = self.model.predict(X_scaled)
        anomaly_scores = self.model.decision_function(X_scaled)
        
        df['is_anomaly'] = predictions == -1
        df['anomaly_score'] = anomaly_scores
        
        return df

# models/failure_prediction.py
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_recall_fscore_support

class FailurePredictor:
    def __init__(self):
        self.model = XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42
        )
        
    def train(self, df: pd.DataFrame, features: List[str], target: str):
        """Train failure prediction model"""
        X = df[features].values
        y = df[target].values
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_test, y_pred, average='binary'
        )
        
        return {
            'precision': precision,
            'recall': recall,
            'f1_score': f1
        }
    
    def predict_failure_probability(self, df: pd.DataFrame, features: List[str]) -> pd.DataFrame:
        """Predict probability of failure"""
        X = df[features].values
        failure_prob = self.model.predict_proba(X)[:, 1]
        
        df['failure_probability'] = failure_prob
        df['predicted_failure'] = failure_prob > 0.5
        
        # Estimate time to failure based on trend
        df['time_to_failure_hours'] = self._estimate_ttf(df, failure_prob)
        
        return df
    
    def _estimate_ttf(self, df: pd.DataFrame, failure_prob: np.ndarray) -> np.ndarray:
        """Estimate time to failure based on probability trend"""
        ttf = np.zeros(len(failure_prob))
        
        for i in range(len(failure_prob)):
            if failure_prob[i] > 0.8:
                ttf[i] = 1  # Critical - 1 hour
            elif failure_prob[i] > 0.6:
                ttf[i] = 6  # High risk - 6 hours
            elif failure_prob[i] > 0.4:
                ttf[i] = 24  # Moderate - 24 hours
            else:
                ttf[i] = -1  # Low risk - unknown
        
        return ttf

# models/forecasting.py
from prophet import Prophet
import pandas as pd

class EnergyForecaster:
    def __init__(self):
        self.model = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=False
        )
        
    def train(self, df: pd.DataFrame):
        """Train forecasting model"""
        # Prophet requires 'ds' (timestamp) and 'y' (value) columns
        prophet_df = pd.DataFrame({
            'ds': df['_time'],
            'y': df['power']
        })
        
        self.model.fit(prophet_df)
        
    def forecast(self, periods: int = 168) -> pd.DataFrame:
        """Forecast next 'periods' hours (default: 7 days)"""
        future = self.model.make_future_dataframe(periods=periods, freq='H')
        forecast = self.model.predict(future)
        
        return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
```

#### 4.6.3 Analytics API

```python
# api/analytics_api.py
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

app = FastAPI()

class AnalyticsRequest(BaseModel):
    device_id: str
    start_time: datetime
    end_time: datetime
    analysis_type: str  # 'anomaly', 'prediction', 'forecast'
    model_name: str
    parameters: Optional[dict] = {}

class AnalyticsJob:
    def __init__(self, job_id: str, request: AnalyticsRequest):
        self.job_id = job_id
        self.request = request
        self.status = "pending"
        self.results = None
        
    async def execute(self):
        """Execute analytics job"""
        self.status = "running"
        
        try:
            # Load dataset from S3
            dataset = await load_dataset(
                self.request.device_id,
                self.request.start_time,
                self.request.end_time
            )
            
            # Run appropriate model
            if self.request.analysis_type == "anomaly":
                results = await run_anomaly_detection(dataset, self.request.model_name)
            elif self.request.analysis_type == "prediction":
                results = await run_failure_prediction(dataset, self.request.model_name)
            elif self.request.analysis_type == "forecast":
                results = await run_forecasting(dataset, self.request.model_name)
            else:
                raise ValueError(f"Unknown analysis type: {self.request.analysis_type}")
            
            self.results = results
            self.status = "completed"
            
            # Save results to database
            await save_analytics_results(self.job_id, results)
            
        except Exception as e:
            self.status = "failed"
            self.error = str(e)
            logging.error(f"Analytics job {self.job_id} failed: {e}")

@app.post("/api/analytics/run")
async def run_analytics(request: AnalyticsRequest, background_tasks: BackgroundTasks):
    """Submit analytics job"""
    job_id = generate_job_id()
    job = AnalyticsJob(job_id, request)
    background_tasks.add_task(job.execute)
    
    return {"job_id": job_id, "status": "queued"}

@app.get("/api/analytics/results/{job_id}")
async def get_analytics_results(job_id: str):
    """Get analytics results"""
    results = await fetch_analytics_results(job_id)
    if not results:
        raise HTTPException(status_code=404, detail="Results not found")
    return results
```

---

### 4.7 Notification Service (Node.js)

#### 4.7.1 Implementation

```typescript
// services/NotificationService.ts
import { SES } from '@aws-sdk/client-ses';
import twilio from 'twilio';
import TelegramBot from 'node-telegram-bot-api';

export class NotificationService {
  private ses: SES;
  private twilioClient: any;
  private telegramBot: TelegramBot;
  
  constructor() {
    this.ses = new SES({ region: 'us-east-1' });
    this.twilioClient = twilio(
      process.env.TWILIO_ACCOUNT_SID,
      process.env.TWILIO_AUTH_TOKEN
    );
    this.telegramBot = new TelegramBot(process.env.TELEGRAM_BOT_TOKEN);
  }
  
  async sendEmail(alert: Alert, recipients: string[]): Promise<void> {
    const params = {
      Source: 'alerts@energy-platform.com',
      Destination: { ToAddresses: recipients },
      Message: {
        Subject: { Data: `Alert: ${alert.severity} - ${alert.message}` },
        Body: {
          Html: { Data: this.buildEmailTemplate(alert) }
        }
      }
    };
    
    await this.ses.sendEmail(params);
  }
  
  async sendWhatsApp(alert: Alert, phoneNumbers: string[]): Promise<void> {
    const message = this.buildWhatsAppMessage(alert);
    
    for (const phone of phoneNumbers) {
      await this.twilioClient.messages.create({
        from: 'whatsapp:+14155238886',
        to: `whatsapp:${phone}`,
        body: message
      });
    }
  }
  
  async sendTelegram(alert: Alert, chatIds: string[]): Promise<void> {
    const message = this.buildTelegramMessage(alert);
    
    for (const chatId of chatIds) {
      await this.telegramBot.sendMessage(chatId, message, {
        parse_mode: 'Markdown'
      });
    }
  }
}
```

---

## 5. API Specifications

### 5.1 API Gateway Configuration

```yaml
# kong.yaml
_format_version: "3.0"

services:
  - name: auth-service
    url: http://auth-service:3001
    routes:
      - name: auth-routes
        paths:
          - /api/auth
        strip_path: false
    plugins:
      - name: rate-limiting
        config:
          minute: 20
          policy: local

  - name: device-service
    url: http://device-service:8080
    routes:
      - name: device-routes
        paths:
          - /api/devices
        strip_path: false
    plugins:
      - name: jwt
        config:
          secret_is_base64: false
          key_claim_name: sub
      - name: rate-limiting
        config:
          minute: 100

  - name: data-service
    url: http://data-service:8081
    routes:
      - name: data-routes
        paths:
          - /api/data
        strip_path: false
    plugins:
      - name: jwt
      - name: rate-limiting
        config:
          minute: 200
```

### 5.2 Complete API Reference

#### Authentication Endpoints

```
POST   /api/auth/login
Request: { "email": "user@example.com", "password": "password" }
Response: { "token": "jwt-token", "user": { ...userObject } }

POST   /api/auth/logout
Headers: Authorization: Bearer <token>
Response: { "message": "Logged out successfully" }

POST   /api/auth/refresh
Request: { "refresh_token": "refresh-token" }
Response: { "token": "new-jwt-token" }
```

#### Device Endpoints

```
GET    /api/devices?type=bulb&status=active
Response: { "devices": [...], "total": 10, "page": 1 }

GET    /api/devices/D1
Response: { "id": "D1", "name": "Electric Bulb", ... }

POST   /api/devices
Request: { "id": "D2", "name": "Compressor", "type": "compressor", ... }
Response: { "id": "D2", ... }
```

#### Telemetry Endpoints

```
GET    /api/data/telemetry/D1?start=2026-02-01T00:00:00Z&end=2026-02-07T23:59:59Z&fields=power,temperature
Response: { "data": [...telemetryPoints], "count": 1000 }

WebSocket: ws://api.energy-platform.com/api/data/telemetry/D1/live
Message: { "device_id": "D1", "timestamp": "...", "voltage": 230.5, ... }
```

#### Rule Endpoints

```
GET    /api/rules?device_id=D1&status=active
Response: { "rules": [...], "total": 5 }

POST   /api/rules
Request: {
  "name": "Bulb Overheat",
  "device_id": "D1",
  "property": "temperature",
  "operator": ">",
  "threshold": 50,
  "notification_channels": ["email", "whatsapp"]
}
Response: { "id": "uuid", "name": "Bulb Overheat", ... }
```

---

## 6. MQTT & Telemetry Pipeline

### 6.1 EMQX Configuration

```hocon
# emqx.conf
node {
  name = "emqx@emqx-0"
  cookie = "emqxsecretcookie"
  data_dir = "/opt/emqx/data"
}

cluster {
  discovery_strategy = k8s
  k8s {
    apiserver = "https://kubernetes.default.svc:443"
    service_name = "emqx-headless"
    address_type = hostname
    namespace = "energy-platform"
  }
}

listeners.tcp.default {
  bind = "0.0.0.0:1883"
  max_connections = 1024000
  max_conn_rate = 1000
}

listeners.ssl.default {
  bind = "0.0.0.0:8883"
  max_connections = 512000
  ssl_options {
    cacertfile = "/etc/emqx/certs/ca.pem"
    certfile = "/etc/emqx/certs/server.pem"
    keyfile = "/etc/emqx/certs/server-key.pem"
    verify = verify_peer
  }
}

mqtt {
  max_packet_size = 1MB
  max_clientid_len = 65535
  max_topic_levels = 128
  max_qos_allowed = 1
  max_topic_alias = 65535
  retain_available = true
  wildcard_subscription = true
  shared_subscription = true
}

authorization {
  sources = [
    {
      type = postgresql
      server = "postgres-service:5432"
      database = "energy_platform"
      username = "${DB_USER}"
      password = "${DB_PASSWORD}"
      query = "SELECT allow FROM mqtt_acl WHERE username = ${username} AND topic = ${topic}"
    }
  ]
}
```

### 6.2 IoT Simulator (Python)

```python
# simulator/device_simulator.py
import paho.mqtt.client as mqtt
import json
import time
import random
from datetime import datetime, timezone
import numpy as np

class DeviceSimulator:
    def __init__(self, device_id: str, broker_host: str, broker_port: int = 1883):
        self.device_id = device_id
        self.client = mqtt.Client(client_id=f"simulator_{device_id}")
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.running = False
        
        # Baseline values for realistic simulation
        self.baseline_voltage = 230.0
        self.baseline_current = 0.85
        self.baseline_temperature = 40.0
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"Connected to MQTT broker: {self.broker_host}:{self.broker_port}")
        else:
            print(f"Failed to connect, return code {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        print(f"Disconnected from MQTT broker, return code {rc}")
    
    def connect(self):
        """Connect to MQTT broker"""
        self.client.connect(self.broker_host, self.broker_port, 60)
        self.client.loop_start()
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        self.running = False
        self.client.loop_stop()
        self.client.disconnect()
    
    def generate_telemetry(self, inject_fault: bool = False) -> dict:
        """Generate realistic telemetry data"""
        # Add random variation to simulate real-world conditions
        voltage = self.baseline_voltage + random.gauss(0, 5)  # ±5V variation
        current = self.baseline_current + random.gauss(0, 0.05)  # ±0.05A variation
        
        # Power = V × I with realistic power factor
        power_factor = random.uniform(0.95, 1.0)
        power = voltage * current * power_factor
        
        # Temperature varies with power and ambient conditions
        temperature = self.baseline_temperature + (power - 195) * 0.05 + random.gauss(0, 2)
        
        # Fault injection for testing anomaly detection
        if inject_fault:
            fault_type = random.choice(['overheat', 'voltage_spike', 'current_surge'])
            if fault_type == 'overheat':
                temperature = random.uniform(60, 75)
            elif fault_type == 'voltage_spike':
                voltage = random.uniform(245, 255)
            elif fault_type == 'current_surge':
                current = random.uniform(1.5, 2.0)
                power = voltage * current
        
        # Ensure values within valid ranges
        voltage = np.clip(voltage, 200, 250)
        current = np.clip(current, 0, 2)
        power = np.clip(power, 0, 500)
        temperature = np.clip(temperature, 20, 80)
        
        return {
            "device_id": self.device_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "voltage": round(voltage, 2),
            "current": round(current, 2),
            "power": round(power, 2),
            "temperature": round(temperature, 2)
        }
    
    def publish_telemetry(self, interval_seconds: int = 5, fault_probability: float = 0.0):
        """Continuously publish telemetry data"""
        self.running = True
        topic = f"devices/{self.device_id}/telemetry"
        
        print(f"Starting telemetry publishing for {self.device_id} every {interval_seconds}s")
        
        while self.running:
            inject_fault = random.random() < fault_probability
            telemetry = self.generate_telemetry(inject_fault=inject_fault)
            
            payload = json.dumps(telemetry)
            result = self.client.publish(topic, payload, qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"Published: {payload}")
            else:
                print(f"Failed to publish: {result.rc}")
            
            time.sleep(interval_seconds)

# Main execution
if __name__ == "__main__":
    simulator = DeviceSimulator(
        device_id="D1",
        broker_host="emqx-service.energy-platform.svc.cluster.local",
        broker_port=1883
    )
    
    try:
        simulator.connect()
        time.sleep(2)  # Wait for connection
        simulator.publish_telemetry(interval_seconds=5, fault_probability=0.05)
    except KeyboardInterrupt:
        print("\nShutting down simulator...")
        simulator.disconnect()
```

---

## 7. Real-Time Rule Engine

### 7.1 Rule Evaluation Architecture

```
Telemetry → Data Service → Rule Engine Service
                              ↓
                    ┌─────────┴─────────┐
                    │  Rule Evaluator   │
                    │  - Load Rules     │
                    │  - Check Cooldown │
                    │  - Evaluate       │
                    └─────────┬─────────┘
                              ↓
                    ┌─────────┴─────────┐
                    │  Alert Manager    │
                    │  - Create Alert   │
                    │  - Update Rule    │
                    └─────────┬─────────┘
                              ↓
                    ┌─────────┴─────────┐
                    │ Notification Svc  │
                    │ - Email           │
                    │ - WhatsApp        │
                    │ - Telegram        │
                    └───────────────────┘
```

### 7.2 Rule Processing Pseudocode

```
FUNCTION EvaluateRulesForTelemetry(telemetry):
    rules = GetActiveRulesByDevice(telemetry.device_id)
    
    FOR EACH rule IN rules:
        IF ShouldEvaluate(rule):
            actualValue = ExtractValue(telemetry, rule.property)
            isTriggered = Compare(actualValue, rule.operator, rule.threshold)
            
            IF isTriggered:
                alert = CreateAlert(rule, telemetry, actualValue)
                SaveAlert(alert)
                UpdateRuleLastTriggered(rule.id, NOW())
                SendNotifications(alert, rule.notification_channels)
```

---

## 8. ML Analytics Pipeline

### 8.1 Pipeline Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    ML ANALYTICS PIPELINE                         │
└──────────────────────────────────────────────────────────────────┘

Step 1: Data Export
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  InfluxDB    │────▶│ Data Export  │────▶│  S3 Bucket   │
│  Telemetry   │     │   Service    │     │   (Parquet)  │
└──────────────┘     └──────────────┘     └──────────────┘

Step 2: Feature Engineering
┌──────────────┐     ┌───────────────────────────────────┐
│  S3 Dataset  │────▶│  Feature Engineering              │
│              │     │  - Rolling stats                  │
│              │     │  - Time features                  │
│              │     │  - Derived metrics                │
└──────────────┘     └───────────────────────────────────┘

Step 3: Model Execution (Kubernetes Job)
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Features    │────▶│  ML Models   │────▶│   Results    │
│              │     │  - Anomaly   │     │   (JSON)     │
│              │     │  - Forecast  │     │              │
│              │     │  - Predict   │     │              │
└──────────────┘     └──────────────┘     └──────────────┘

Step 4: Results Storage
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Results    │────▶│  PostgreSQL  │────▶│   Frontend   │
│   (JSON)     │     │   Analytics  │     │   Dashboard  │
│              │     │   Results    │     │              │
└──────────────┘     └──────────────┘     └──────────────┘
```

### 8.2 Kubernetes Job Template

```yaml
# analytics-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: analytics-anomaly-{{ .JobID }}
  namespace: energy-platform
spec:
  ttlSecondsAfterFinished: 3600
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: analytics
        image: energy-platform/analytics:latest
        env:
        - name: JOB_ID
          value: "{{ .JobID }}"
        - name: DEVICE_ID
          value: "{{ .DeviceID }}"
        - name: START_TIME
          value: "{{ .StartTime }}"
        - name: END_TIME
          value: "{{ .EndTime }}"
        - name: ANALYSIS_TYPE
          value: "anomaly"
        - name: MODEL_NAME
          value: "isolation_forest"
        - name: S3_BUCKET
          value: "energy-platform-datasets"
        - name: POSTGRES_HOST
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: host
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
```

---

## 9. Frontend Architecture

### 9.1 React Application Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── Footer.tsx
│   │   ├── dashboard/
│   │   │   ├── DashboardOverview.tsx
│   │   │   ├── DeviceCard.tsx
│   │   │   ├── SystemHealth.tsx
│   │   │   └── AlertsSummary.tsx
│   │   ├── devices/
│   │   │   ├── DeviceList.tsx
│   │   │   ├── DeviceDetails.tsx
│   │   │   └── DeviceLiveChart.tsx
│   │   ├── rules/
│   │   │   ├── RuleList.tsx
│   │   │   ├── RuleForm.tsx
│   │   │   └── RuleCard.tsx
│   │   ├── analytics/
│   │   │   ├── AnalyticsForm.tsx
│   │   │   ├── AnomalyChart.tsx
│   │   │   ├── PredictionChart.tsx
│   │   │   └── ForecastChart.tsx
│   │   └── common/
│   │       ├── Button.tsx
│   │       ├── Input.tsx
│   │       ├── Select.tsx
│   │       └── Chart.tsx
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── Devices.tsx
│   │   ├── Rules.tsx
│   │   ├── Analytics.tsx
│   │   ├── Reports.tsx
│   │   └── Login.tsx
│   ├── store/
│   │   ├── slices/
│   │   │   ├── authSlice.ts
│   │   │   ├── devicesSlice.ts
│   │   │   ├── rulesSlice.ts
│   │   │   └── analyticsSlice.ts
│   │   └── store.ts
│   ├── services/
│   │   ├── api.ts
│   │   ├── websocket.ts
│   │   └── auth.ts
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useDevices.ts
│   │   ├── useLiveTelemetry.ts
│   │   └── useAnalytics.ts
│   ├── types/
│   │   ├── device.ts
│   │   ├── rule.ts
│   │   ├── telemetry.ts
│   │   └── analytics.ts
│   ├── utils/
│   │   ├── formatters.ts
│   │   ├── validators.ts
│   │   └── constants.ts
│   ├── App.tsx
│   └── main.tsx
├── package.json
├── vite.config.ts
└── tsconfig.json
```

### 9.2 Key Frontend Components

#### Dashboard Component

```typescript
// pages/Dashboard.tsx
import React, { useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { Grid, Card, CardContent, Typography } from '@mui/material';
import { fetchDevices } from '../store/slices/devicesSlice';
import DeviceCard from '../components/dashboard/DeviceCard';
import SystemHealth from '../components/dashboard/SystemHealth';

const Dashboard: React.FC = () => {
  const dispatch = useDispatch();
  const { devices, loading } = useSelector((state: RootState) => state.devices);
  const { activeAlerts } = useSelector((state: RootState) => state.alerts);
  
  useEffect(() => {
    dispatch(fetchDevices());
  }, [dispatch]);
  
  if (loading) return <div>Loading...</div>;
  
  return (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <SystemHealth />
      </Grid>
      
      <Grid item xs={12} md={6} lg={3}>
        <Card>
          <CardContent>
            <Typography variant="h6">Total Devices</Typography>
            <Typography variant="h3">{devices.length}</Typography>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} md={6} lg={3}>
        <Card>
          <CardContent>
            <Typography variant="h6">Active Alerts</Typography>
            <Typography variant="h3" color="error">{activeAlerts}</Typography>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12}>
        <Typography variant="h5" gutterBottom>Devices</Typography>
        <Grid container spacing={2}>
          {devices.map(device => (
            <Grid item xs={12} md={6} lg={4} key={device.id}>
              <DeviceCard device={device} />
            </Grid>
          ))}
        </Grid>
      </Grid>
    </Grid>
  );
};

export default Dashboard;
```

#### Live Telemetry Hook

```typescript
// hooks/useLiveTelemetry.ts
import { useEffect, useState } from 'react';
import io from 'socket.io-client';

interface TelemetryPoint {
  timestamp: string;
  voltage: number;
  current: number;
  power: number;
  temperature: number;
}

export const useLiveTelemetry = (deviceId: string) => {
  const [telemetry, setTelemetry] = useState<TelemetryPoint[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  
  useEffect(() => {
    const socket = io(`ws://api.energy-platform.com/data/telemetry/${deviceId}/live`, {
      auth: {
        token: localStorage.getItem('token')
      }
    });
    
    socket.on('connect', () => {
      setIsConnected(true);
      console.log('WebSocket connected');
    });
    
    socket.on('disconnect', () => {
      setIsConnected(false);
      console.log('WebSocket disconnected');
    });
    
    socket.on('telemetry', (data: TelemetryPoint) => {
      setTelemetry(prev => [...prev.slice(-100), data]); // Keep last 100 points
    });
    
    return () => {
      socket.disconnect();
    };
  }, [deviceId]);
  
  return { telemetry, isConnected };
};
```

---

## 10. Security Implementation

### 10.1 JWT Authentication

```typescript
// auth/jwt.ts
import jwt from 'jsonwebtoken';

export interface JWTPayload {
  userId: string;
  email: string;
  role: string;
}

export function generateToken(payload: JWTPayload): string {
  return jwt.sign(payload, process.env.JWT_SECRET!, {
    expiresIn: '1h',
    issuer: 'energy-platform',
    audience: 'energy-platform-users'
  });
}

export function verifyToken(token: string): JWTPayload {
  return jwt.verify(token, process.env.JWT_SECRET!) as JWTPayload;
}
```

### 10.2 MQTT ACL (PostgreSQL)

```sql
CREATE TABLE mqtt_acl (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    topic VARCHAR(500) NOT NULL,
    action VARCHAR(10) NOT NULL CHECK (action IN ('subscribe', 'publish', 'all')),
    allow BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Allow D1 simulator to publish to its topic
INSERT INTO mqtt_acl (username, topic, action, allow) 
VALUES ('simulator_D1', 'devices/D1/telemetry', 'publish', true);

-- Allow data service to subscribe to all device topics
INSERT INTO mqtt_acl (username, topic, action, allow) 
VALUES ('data-service', 'devices/+/telemetry', 'subscribe', true);

CREATE INDEX idx_mqtt_acl_username ON mqtt_acl(username);
CREATE INDEX idx_mqtt_acl_topic ON mqtt_acl(topic);
```

---

## 11. Deployment Architecture

### 11.1 Kubernetes Deployment

#### Auth Service Deployment

```yaml
# k8s/auth-service-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auth-service
  namespace: energy-platform
spec:
  replicas: 2
  selector:
    matchLabels:
      app: auth-service
  template:
    metadata:
      labels:
        app: auth-service
    spec:
      containers:
      - name: auth-service
        image: energy-platform/auth-service:latest
        ports:
        - containerPort: 3001
        env:
        - name: NODE_ENV
          value: "production"
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: auth-secrets
              key: jwt-secret
        - name: DB_HOST
          value: postgres-service
        - name: DB_PORT
          value: "5432"
        - name: DB_NAME
          value: energy_platform
        - name: DB_USER
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: username
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: password
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 3001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 3001
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: auth-service
  namespace: energy-platform
spec:
  selector:
    app: auth-service
  ports:
  - port: 3001
    targetPort: 3001
  type: ClusterIP
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: auth-service-hpa
  namespace: energy-platform
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: auth-service
  minReplicas: 2
  maxReplicas: 5
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

#### Data Service Deployment

```yaml
# k8s/data-service-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: data-service
  namespace: energy-platform
spec:
  replicas: 3
  selector:
    matchLabels:
      app: data-service
  template:
    metadata:
      labels:
        app: data-service
    spec:
      containers:
      - name: data-service
        image: energy-platform/data-service:latest
        ports:
        - containerPort: 8081
        env:
        - name: EMQX_BROKER_URL
          value: "tcp://emqx-service:1883"
        - name: INFLUXDB_URL
          value: "http://influxdb-service:8086"
        - name: INFLUXDB_TOKEN
          valueFrom:
            secretKeyRef:
              name: influxdb-credentials
              key: token
        - name: INFLUXDB_ORG
          value: "energy-platform"
        - name: INFLUXDB_BUCKET
          value: "telemetry"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1"
```

### 11.2 Infrastructure as Code (Terraform)

```hcl
# terraform/main.tf
provider "aws" {
  region = "us-east-1"
}

# EKS Cluster
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = "energy-platform-cluster"
  cluster_version = "1.28"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  eks_managed_node_groups = {
    general = {
      desired_size = 3
      min_size     = 2
      max_size     = 5

      instance_types = ["t3.medium"]
      capacity_type  = "ON_DEMAND"
    }
  }
}

# S3 Bucket for ML Datasets
resource "aws_s3_bucket" "datasets" {
  bucket = "energy-platform-datasets"
  
  lifecycle_rule {
    enabled = true
    
    transition {
      days          = 30
      storage_class = "GLACIER"
    }
    
    expiration {
      days = 90
    }
  }
}

# RDS PostgreSQL
resource "aws_db_instance" "postgres" {
  identifier           = "energy-platform-db"
  engine              = "postgres"
  engine_version      = "15.4"
  instance_class      = "db.t3.medium"
  allocated_storage   = 100
  storage_encrypted   = true
  
  db_name  = "energy_platform"
  username = "admin"
  password = random_password.db_password.result
  
  backup_retention_period = 7
  multi_az               = true
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
}
```

---

## 12. Monitoring & Observability

### 12.1 Prometheus Metrics

```yaml
# k8s/prometheus-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
    
    scrape_configs:
      - job_name: 'auth-service'
        kubernetes_sd_configs:
          - role: pod
        relabel_configs:
          - source_labels: [__meta_kubernetes_pod_label_app]
            regex: auth-service
            action: keep
      
      - job_name: 'data-service'
        kubernetes_sd_configs:
          - role: pod
        relabel_configs:
          - source_labels: [__meta_kubernetes_pod_label_app]
            regex: data-service
            action: keep
      
      - job_name: 'emqx'
        static_configs:
          - targets: ['emqx-service:18083']
```

### 12.2 Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Energy Platform - System Overview",
    "panels": [
      {
        "title": "Telemetry Ingestion Rate",
        "targets": [
          {
            "expr": "rate(telemetry_messages_total[5m])",
            "legendFormat": "{{device_id}}"
          }
        ]
      },
      {
        "title": "Rule Evaluation Latency",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(rule_evaluation_duration_seconds_bucket[5m]))",
            "legendFormat": "p95"
          }
        ]
      },
      {
        "title": "Active Alerts",
        "targets": [
          {
            "expr": "sum(alerts_active) by (severity)",
            "legendFormat": "{{severity}}"
          }
        ]
      }
    ]
  }
}
```

### 12.3 CloudWatch Alarms

```yaml
# cloudwatch-alarms.yaml
Alarms:
  - Name: HighCPUUtilization
    MetricName: CPUUtilization
    Namespace: AWS/EKS
    Statistic: Average
    Period: 300
    EvaluationPeriods: 2
    Threshold: 80
    ComparisonOperator: GreaterThanThreshold
    AlarmActions:
      - !Ref SNSTopic
  
  - Name: HighMemoryUtilization
    MetricName: MemoryUtilization
    Namespace: AWS/EKS
    Statistic: Average
    Period: 300
    EvaluationPeriods: 2
    Threshold: 85
    ComparisonOperator: GreaterThanThreshold
```

---

## Appendix

### A. Environment Variables

```bash
# Auth Service
JWT_SECRET=your-secret-key
JWT_EXPIRES_IN=1h
DB_HOST=postgres-service
DB_PORT=5432
DB_NAME=energy_platform
DB_USER=admin
DB_PASSWORD=secure-password
REDIS_HOST=redis-service
REDIS_PORT=6379

# Data Service
EMQX_BROKER_URL=tcp://emqx-service:1883
INFLUXDB_URL=http://influxdb-service:8086
INFLUXDB_TOKEN=your-influxdb-token
INFLUXDB_ORG=energy-platform
INFLUXDB_BUCKET=telemetry

# Analytics Service
S3_BUCKET=energy-platform-datasets
AWS_REGION=us-east-1
MODEL_STORAGE_PATH=/models

# Notification Service
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
AWS_SES_REGION=us-east-1
TELEGRAM_BOT_TOKEN=your-telegram-token
```

### B. API Response Formats

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "timestamp": "2026-02-07T11:26:00Z"
}

{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid device ID",
    "details": { ... }
  },
  "timestamp": "2026-02-07T11:26:00Z"
}
```

---

**End of Low-Level Design Document**
