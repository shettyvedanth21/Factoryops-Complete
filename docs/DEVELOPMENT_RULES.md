# Development Rules & Guidelines
# Energy Intelligence & Analytics Platform

**Version:** 1.0  
**Date:** February 7, 2026  
**Applies To:** All developers, architects, and contributors

---

## Table of Contents

1. [General Principles](#1-general-principles)
2. [Code Standards](#2-code-standards)
3. [Architecture Rules](#3-architecture-rules)
4. [Database Guidelines](#4-database-guidelines)
5. [API Design Rules](#5-api-design-rules)
6. [Security Requirements](#6-security-requirements)
7. [Testing Standards](#7-testing-standards)
8. [DevOps & Deployment](#8-devops--deployment)
9. [Documentation Requirements](#9-documentation-requirements)
10. [Performance Standards](#10-performance-standards)
11. [Monitoring & Logging](#11-monitoring--logging)
12. [Code Review Process](#12-code-review-process)

---

## 1. General Principles

### 1.1 Core Values

**MANDATORY**: All development must align with these principles:

1. **Zero Data Loss**: Telemetry data is critical. Never drop data silently.
2. **Production-Ready from Day 1**: No temporary solutions. Build for scale.
3. **Microservice Independence**: Services must operate independently.
4. **Fail-Safe Architecture**: Graceful degradation over cascading failures.
5. **Security by Design**: Security is not optional or an afterthought.

### 1.2 Development Philosophy

```
✅ DO:
- Write code as if you're building for 1000 devices
- Assume services will fail and plan accordingly
- Document WHY decisions were made, not just WHAT
- Think about observability from the start
- Design for horizontal scalability

❌ DON'T:
- Create Phase-1 specific shortcuts
- Hard-code device IDs or assume single device
- Skip error handling "because it's unlikely"
- Ignore edge cases in data validation
- Write code without considering monitoring
```

### 1.3 Decision Authority

| Decision Type | Authority | Requires Approval |
|---------------|-----------|-------------------|
| Code implementation details | Developer | Peer review |
| API endpoint design | Tech Lead | Architecture review |
| Database schema changes | Tech Lead + DBA | Architecture + Security review |
| New service introduction | Architect | All stakeholders |
| Third-party library addition | Tech Lead | Security audit |
| Infrastructure changes | DevOps Lead | Cost & security review |

---

## 2. Code Standards

### 2.1 Language-Specific Standards

#### 2.1.1 Go Services (Device, Data, Rule Engine)

```go
// MANDATORY: Follow these standards

// ✅ CORRECT: Proper error handling
func GetDevice(id string) (*Device, error) {
    if id == "" {
        return nil, errors.New("device ID cannot be empty")
    }
    
    device, err := repo.FindByID(id)
    if err != nil {
        return nil, fmt.Errorf("failed to fetch device %s: %w", id, err)
    }
    
    return device, nil
}

// ❌ WRONG: Silent error swallowing
func GetDevice(id string) *Device {
    device, _ := repo.FindByID(id) // NEVER ignore errors
    return device
}

// ✅ CORRECT: Context propagation
func ProcessTelemetry(ctx context.Context, data TelemetryPayload) error {
    ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
    defer cancel()
    
    if err := validate(data); err != nil {
        return fmt.Errorf("validation failed: %w", err)
    }
    
    return store.Save(ctx, data)
}

// ❌ WRONG: No context or timeout
func ProcessTelemetry(data TelemetryPayload) error {
    return store.Save(data) // Can hang indefinitely
}
```

**Go Code Rules:**

1. **MUST** use `context.Context` for all I/O operations
2. **MUST** handle ALL errors explicitly (no `_` assignments)
3. **MUST** wrap errors with `fmt.Errorf` and `%w` for traceability
4. **MUST** use structured logging (zerolog or zap)
5. **MUST NOT** use panic except in `init()` or truly unrecoverable situations
6. **MUST** implement graceful shutdown for all services
7. **MUST** use dependency injection (interfaces, not concrete types)
8. **MUST** follow effective Go naming conventions (no snake_case)
9. **MUST** run `go fmt`, `go vet`, and `golangci-lint` before commit
10. **MUST** write table-driven tests for all business logic

#### 2.1.2 Node.js Services (Auth, Notification)

```typescript
// ✅ CORRECT: Async/await with proper error handling
async function authenticateUser(email: string, password: string): Promise<AuthResult> {
    try {
        if (!email || !password) {
            throw new ValidationError('Email and password required');
        }
        
        const user = await userRepository.findByEmail(email);
        if (!user) {
            throw new AuthenticationError('Invalid credentials');
        }
        
        const isValid = await bcrypt.compare(password, user.passwordHash);
        if (!isValid) {
            throw new AuthenticationError('Invalid credentials');
        }
        
        const token = generateJWT(user);
        return { token, user };
        
    } catch (error) {
        logger.error('Authentication failed', { email, error });
        throw error;
    }
}

// ❌ WRONG: Callback hell, no error handling
function authenticateUser(email, password, callback) {
    userRepository.findByEmail(email, (err, user) => {
        bcrypt.compare(password, user.passwordHash, (err, isValid) => {
            callback(generateJWT(user)); // No error handling!
        });
    });
}
```

**Node.js Code Rules:**

1. **MUST** use TypeScript (no plain JavaScript)
2. **MUST** use async/await (NO callback-based code)
3. **MUST** define interfaces for all data structures
4. **MUST** use strict null checks (`strictNullChecks: true`)
5. **MUST** handle promise rejections (no unhandled rejections)
6. **MUST** use ESLint with Airbnb config + TypeScript
7. **MUST** implement proper logging (Winston or Pino)
8. **MUST NOT** use `any` type (use `unknown` if truly unknown)
9. **MUST** validate all inputs with Joi or class-validator
10. **MUST** write unit tests with Jest (>80% coverage)

#### 2.1.3 Python Services (Analytics, Data Export, Reporting)

```python
# ✅ CORRECT: Type hints, error handling, logging
from typing import List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DataExporter:
    def __init__(self, influx_client: InfluxDBClient, s3_client: S3Client):
        self._influx = influx_client
        self._s3 = s3_client
    
    def export_dataset(
        self,
        device_id: str,
        start_time: datetime,
        end_time: datetime,
        features: List[str]
    ) -> str:
        """
        Export telemetry dataset to S3.
        
        Args:
            device_id: Device identifier
            start_time: Start of date range
            end_time: End of date range
            features: List of features to include
            
        Returns:
            S3 key of exported dataset
            
        Raises:
            ValidationError: If inputs are invalid
            ExportError: If export fails
        """
        if not device_id:
            raise ValidationError("device_id is required")
        
        if start_time >= end_time:
            raise ValidationError("start_time must be before end_time")
        
        try:
            data = self._fetch_data(device_id, start_time, end_time)
            s3_key = self._upload_to_s3(data, device_id)
            logger.info(f"Exported dataset for {device_id} to {s3_key}")
            return s3_key
            
        except Exception as e:
            logger.error(f"Export failed for {device_id}: {e}", exc_info=True)
            raise ExportError(f"Failed to export dataset: {e}") from e

# ❌ WRONG: No types, no error handling, no logging
def export_dataset(device_id, start_time, end_time, features):
    data = fetch_data(device_id, start_time, end_time)
    return upload_to_s3(data, device_id)
```

**Python Code Rules:**

1. **MUST** use Python 3.11+
2. **MUST** use type hints for all function signatures
3. **MUST** use dataclasses or Pydantic models for data structures
4. **MUST** follow PEP 8 style guide (use Black formatter)
5. **MUST** write docstrings for all public functions/classes (Google style)
6. **MUST** use logging module (not print statements)
7. **MUST** handle exceptions explicitly (no bare `except:`)
8. **MUST** use virtual environments (poetry or pipenv)
9. **MUST** run mypy for type checking
10. **MUST** write tests with pytest (>80% coverage)

### 2.2 Naming Conventions

#### Variables and Functions

```
✅ GOOD:
- calculateHealthScore()
- deviceTelemetry
- ruleEvaluationLatency
- isActiveDevice

❌ BAD:
- calc()           // Too short, unclear
- deviceData       // Too generic
- temp1            // Meaningless
- flagA            // Not descriptive
```

#### Constants

```go
// Go
const (
    MaxRetryAttempts     = 3
    DefaultTimeout       = 5 * time.Second
    TelemetryTopicPrefix = "devices"
)

// TypeScript
export const MAX_RETRY_ATTEMPTS = 3;
export const DEFAULT_TIMEOUT_MS = 5000;
export const TELEMETRY_TOPIC_PREFIX = 'devices';
```

#### Database Tables and Columns

```sql
-- ✅ GOOD: Singular table names, snake_case columns
CREATE TABLE device (
    id VARCHAR(50) PRIMARY KEY,
    device_type VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ❌ BAD: Plural table, camelCase columns
CREATE TABLE devices (
    id VARCHAR(50) PRIMARY KEY,
    deviceType VARCHAR(100) NOT NULL,
    CreatedAt TIMESTAMP
);
```

### 2.3 File Organization

```
MANDATORY Structure:

service-name/
├── cmd/                    # Application entry points
│   └── server/
│       └── main.go
├── internal/               # Private application code
│   ├── handlers/          # HTTP/gRPC handlers
│   ├── services/          # Business logic
│   ├── repositories/      # Data access
│   ├── models/            # Data models
│   └── middleware/        # Middleware components
├── pkg/                    # Public reusable packages
├── api/                    # API definitions (OpenAPI, Proto)
├── config/                 # Configuration files
├── scripts/                # Build/deployment scripts
├── tests/                  # Integration/E2E tests
├── Dockerfile
├── Makefile
└── README.md
```

### 2.4 Comments and Documentation

```go
// ✅ GOOD: Explains WHY, not WHAT
// Check cooldown to prevent alert spam. Business rule: 
// minimum 15 minutes between notifications for same rule.
if time.Since(rule.LastTriggered) < cooldownPeriod {
    return false
}

// ❌ BAD: States the obvious
// Check if time since last triggered is less than cooldown
if time.Since(rule.LastTriggered) < cooldownPeriod {
    return false
}

// ✅ GOOD: Documents edge cases and assumptions
// extractValue retrieves the telemetry value for a given property.
// Returns 0.0 if property doesn't exist. This is safe because validation
// ensures all required properties are present before calling this function.
func extractValue(telemetry TelemetryPayload, property string) float64 {
    // ...
}
```

---

## 3. Architecture Rules

### 3.1 Microservice Communication

**MANDATORY RULES:**

1. **MUST** use HTTP/REST for synchronous inter-service communication
2. **MUST** use MQTT pub/sub for telemetry streaming
3. **MUST** implement circuit breakers for all external calls (Hystrix pattern)
4. **MUST NOT** make synchronous calls from MQTT message handlers
5. **MUST** implement retry logic with exponential backoff
6. **MUST** set reasonable timeouts on all network calls (default: 5s)

```go
// ✅ CORRECT: Circuit breaker + timeout
type DeviceServiceClient struct {
    httpClient  *http.Client
    breaker     *circuitbreaker.Breaker
    baseURL     string
}

func (c *DeviceServiceClient) GetDevice(ctx context.Context, id string) (*Device, error) {
    ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
    defer cancel()
    
    var device Device
    err := c.breaker.Call(func() error {
        resp, err := c.httpClient.Get(ctx, fmt.Sprintf("%s/devices/%s", c.baseURL, id))
        if err != nil {
            return err
        }
        return json.NewDecoder(resp.Body).Decode(&device)
    })
    
    return &device, err
}

// ❌ WRONG: No timeout, no circuit breaker
func (c *DeviceServiceClient) GetDevice(id string) (*Device, error) {
    resp, _ := http.Get(fmt.Sprintf("%s/devices/%s", c.baseURL, id))
    var device Device
    json.NewDecoder(resp.Body).Decode(&device)
    return &device, nil
}
```

### 3.2 Database Access Patterns

**RULES:**

1. **MUST** use connection pooling
2. **MUST** use prepared statements to prevent SQL injection
3. **MUST** implement transaction management for multi-table operations
4. **MUST** use database migrations (Flyway or golang-migrate)
5. **MUST NOT** execute queries in loops (use batch operations)
6. **MUST** implement proper indexing strategy

```go
// ✅ CORRECT: Prepared statement, transaction
func (r *DeviceRepository) UpdateDeviceHealth(ctx context.Context, deviceID string, healthScore float64) error {
    tx, err := r.db.BeginTx(ctx, nil)
    if err != nil {
        return fmt.Errorf("failed to begin transaction: %w", err)
    }
    defer tx.Rollback()
    
    query := `UPDATE devices SET health_score = $1, updated_at = $2 WHERE id = $3`
    _, err = tx.ExecContext(ctx, query, healthScore, time.Now(), deviceID)
    if err != nil {
        return fmt.Errorf("failed to update device: %w", err)
    }
    
    return tx.Commit()
}
```

### 3.3 Message Queue Patterns

**MQTT Rules:**

1. **MUST** use QoS 1 for telemetry (at least once delivery)
2. **MUST** implement Dead Letter Queue for failed messages
3. **MUST** validate message schema before processing
4. **MUST** use structured topics: `devices/{device_id}/{message_type}`
5. **MUST NOT** block MQTT handlers (process async)

```go
// ✅ CORRECT: Async processing, DLQ
func (h *MQTTHandler) HandleTelemetry(client mqtt.Client, msg mqtt.Message) {
    var payload TelemetryPayload
    
    if err := json.Unmarshal(msg.Payload(), &payload); err != nil {
        h.dlq.Send(msg.Payload(), "parse_error", err.Error())
        return
    }
    
    // Async processing - don't block MQTT handler
    go func() {
        if err := h.processor.Process(context.Background(), payload); err != nil {
            h.dlq.Send(msg.Payload(), "processing_error", err.Error())
        }
    }()
}
```

---

## 4. Database Guidelines

### 4.1 Schema Design Rules

**MANDATORY:**

1. **MUST** use UUIDs for primary keys (except device_id which is business key)
2. **MUST** include `created_at` and `updated_at` timestamps
3. **MUST** use appropriate indexes for query patterns
4. **MUST** use foreign keys with appropriate CASCADE rules
5. **MUST** use JSONB for semi-structured data (not TEXT)
6. **MUST** define CHECK constraints for data validation
7. **MUST NOT** use NULL for boolean flags (use default FALSE)

```sql
-- ✅ CORRECT
CREATE TABLE rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id VARCHAR(50) NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    property VARCHAR(100) NOT NULL,
    threshold NUMERIC(10,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'paused', 'archived')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_rules_device_id ON rules(device_id);
CREATE INDEX idx_rules_status ON rules(status) WHERE status = 'active';

-- ❌ WRONG: No constraints, nullable booleans, no indexes
CREATE TABLE rules (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(50),
    property VARCHAR(100),
    threshold FLOAT,
    is_active BOOLEAN
);
```

### 4.2 Migration Best Practices

```sql
-- migrations/V1__create_devices_table.sql
-- ✅ CORRECT: Idempotent, reversible

-- Up migration
CREATE TABLE IF NOT EXISTS devices (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Add index separately for performance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_devices_type ON devices(type);

-- migrations/V1__create_devices_table_down.sql
-- Down migration
DROP INDEX IF EXISTS idx_devices_type;
DROP TABLE IF EXISTS devices;
```

### 4.3 Query Optimization

**RULES:**

1. **MUST** use EXPLAIN ANALYZE for queries >100ms
2. **MUST** avoid SELECT * (specify columns)
3. **MUST** use LIMIT for unbounded queries
4. **MUST** paginate results for list endpoints
5. **MUST** use appropriate JOIN types

```sql
-- ✅ CORRECT: Selective columns, LIMIT, proper JOIN
SELECT 
    d.id,
    d.name,
    d.health_score,
    COUNT(a.id) as active_alerts
FROM devices d
LEFT JOIN alerts a ON d.id = a.device_id AND a.status = 'open'
WHERE d.status = 'active'
GROUP BY d.id, d.name, d.health_score
ORDER BY d.health_score ASC
LIMIT 50 OFFSET 0;

-- ❌ WRONG: SELECT *, no LIMIT, inefficient
SELECT * 
FROM devices d, alerts a
WHERE d.id = a.device_id;
```

---

## 5. API Design Rules

### 5.1 REST API Standards

**MANDATORY:**

1. **MUST** use RESTful resource naming
2. **MUST** use appropriate HTTP methods (GET, POST, PUT, PATCH, DELETE)
3. **MUST** return correct HTTP status codes
4. **MUST** version APIs (e.g., `/api/v1/devices`)
5. **MUST** implement pagination for list endpoints
6. **MUST** use consistent error response format
7. **MUST** validate all inputs

```typescript
// ✅ CORRECT: RESTful, proper status codes, validation
@Post('/api/v1/devices')
async createDevice(@Body() dto: CreateDeviceDto): Promise<ApiResponse<Device>> {
    // Validate input
    const errors = await validate(dto);
    if (errors.length > 0) {
        throw new BadRequestException({
            success: false,
            error: {
                code: 'VALIDATION_ERROR',
                message: 'Invalid input',
                details: errors
            }
        });
    }
    
    try {
        const device = await this.deviceService.create(dto);
        return {
            success: true,
            data: device,
            timestamp: new Date().toISOString()
        };
    } catch (error) {
        throw new InternalServerErrorException({
            success: false,
            error: {
                code: 'CREATION_FAILED',
                message: 'Failed to create device'
            }
        });
    }
}

// ❌ WRONG: Non-RESTful, inconsistent responses
@Get('/createDevice')  // Wrong method
async createDevice(@Query() id: string) {
    const device = await this.deviceService.create(id);
    return device;  // Inconsistent response format
}
```

### 5.2 Response Format Standards

```json
// ✅ CORRECT: Consistent structure
{
    "success": true,
    "data": {
        "id": "D1",
        "name": "Electric Bulb",
        "type": "bulb",
        "health_score": 87.5
    },
    "timestamp": "2026-02-07T11:26:00Z"
}

// For lists - include pagination
{
    "success": true,
    "data": {
        "items": [...],
        "total": 100,
        "page": 1,
        "page_size": 20,
        "total_pages": 5
    },
    "timestamp": "2026-02-07T11:26:00Z"
}

// For errors
{
    "success": false,
    "error": {
        "code": "DEVICE_NOT_FOUND",
        "message": "Device with ID 'D2' not found",
        "details": {
            "device_id": "D2",
            "attempted_at": "2026-02-07T11:26:00Z"
        }
    },
    "timestamp": "2026-02-07T11:26:00Z"
}
```

### 5.3 HTTP Status Codes

**MUST USE:**

```
200 OK              - Successful GET, PUT, PATCH
201 Created         - Successful POST
204 No Content      - Successful DELETE
400 Bad Request     - Invalid input
401 Unauthorized    - Missing or invalid authentication
403 Forbidden       - Authenticated but not authorized
404 Not Found       - Resource doesn't exist
409 Conflict        - Resource conflict (duplicate)
422 Unprocessable   - Validation failed
429 Too Many Requests - Rate limit exceeded
500 Internal Error  - Server error
503 Service Unavailable - Service down
```

---

## 6. Security Requirements

### 6.1 Authentication & Authorization

**MANDATORY:**

1. **MUST** use JWT for API authentication
2. **MUST** set appropriate token expiration (1 hour)
3. **MUST** implement refresh token mechanism
4. **MUST** hash passwords with bcrypt (min 12 rounds)
5. **MUST** implement RBAC (admin, engineer roles)
6. **MUST** validate tokens on every API request
7. **MUST NOT** store tokens in localStorage (use httpOnly cookies)

```typescript
// ✅ CORRECT: Secure JWT handling
interface JWTPayload {
    userId: string;
    email: string;
    role: 'admin' | 'engineer';
    iat: number;
    exp: number;
}

function generateToken(user: User): string {
    return jwt.sign(
        {
            userId: user.id,
            email: user.email,
            role: user.role
        },
        process.env.JWT_SECRET!,
        {
            expiresIn: '1h',
            issuer: 'energy-platform',
            audience: 'energy-platform-users'
        }
    );
}

function validateToken(token: string): JWTPayload {
    try {
        return jwt.verify(token, process.env.JWT_SECRET!) as JWTPayload;
    } catch (error) {
        throw new UnauthorizedError('Invalid token');
    }
}

// ❌ WRONG: Insecure practices
function generateToken(user: User): string {
    return jwt.sign({ userId: user.id }, 'hardcoded-secret');  // NEVER!
}
```

### 6.2 Input Validation

**RULES:**

1. **MUST** validate ALL user inputs
2. **MUST** sanitize inputs to prevent XSS
3. **MUST** use parameterized queries (prevent SQL injection)
4. **MUST** enforce rate limiting
5. **MUST** validate file uploads (type, size)

```typescript
// ✅ CORRECT: Comprehensive validation
import Joi from 'joi';

const createRuleSchema = Joi.object({
    name: Joi.string().min(3).max(255).required(),
    device_id: Joi.string().pattern(/^[A-Z0-9]+$/).required(),
    property: Joi.string().valid('voltage', 'current', 'power', 'temperature').required(),
    operator: Joi.string().valid('>', '<', '>=', '<=', '=', '!=').required(),
    threshold: Joi.number().min(0).max(1000).required(),
    notification_channels: Joi.array().items(
        Joi.string().valid('email', 'whatsapp', 'telegram')
    ).min(1).required()
});

async function createRule(req: Request, res: Response) {
    const { error, value } = createRuleSchema.validate(req.body);
    if (error) {
        return res.status(400).json({
            success: false,
            error: {
                code: 'VALIDATION_ERROR',
                message: error.details[0].message
            }
        });
    }
    
    // Process validated input
    const rule = await ruleService.create(value);
    res.status(201).json({ success: true, data: rule });
}
```

### 6.3 Secrets Management

**MANDATORY:**

1. **MUST** use environment variables for secrets
2. **MUST** use Kubernetes Secrets for sensitive data
3. **MUST** rotate secrets regularly (every 90 days)
4. **MUST NOT** commit secrets to version control
5. **MUST** use AWS Secrets Manager or HashiCorp Vault in production

```yaml
# ✅ CORRECT: Kubernetes Secret
apiVersion: v1
kind: Secret
metadata:
  name: postgres-credentials
type: Opaque
data:
  username: YWRtaW4=  # base64 encoded
  password: c2VjdXJlLXBhc3N3b3Jk  # base64 encoded

---
# Reference in deployment
env:
  - name: DB_PASSWORD
    valueFrom:
      secretKeyRef:
        name: postgres-credentials
        key: password

# ❌ WRONG: Hardcoded in config
env:
  - name: DB_PASSWORD
    value: "my-password-123"  # NEVER!
```

---

## 7. Testing Standards

### 7.1 Test Coverage Requirements

**MANDATORY:**

- **Unit Tests**: Minimum 80% code coverage
- **Integration Tests**: All API endpoints
- **E2E Tests**: Critical user journeys
- **Load Tests**: Performance benchmarks

### 7.2 Unit Test Standards

```go
// ✅ CORRECT: Table-driven tests, clear names
func TestRuleEvaluator_EvaluateRule(t *testing.T) {
    tests := []struct {
        name        string
        rule        Rule
        telemetry   TelemetryPayload
        expected    bool
        description string
    }{
        {
            name: "temperature exceeds threshold",
            rule: Rule{
                Property:  "temperature",
                Operator:  ">",
                Threshold: 50.0,
            },
            telemetry: TelemetryPayload{
                Temperature: 55.0,
            },
            expected:    true,
            description: "Should trigger when temperature > 50°C",
        },
        {
            name: "temperature below threshold",
            rule: Rule{
                Property:  "temperature",
                Operator:  ">",
                Threshold: 50.0,
            },
            telemetry: TelemetryPayload{
                Temperature: 45.0,
            },
            expected:    false,
            description: "Should not trigger when temperature < 50°C",
        },
    }
    
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            evaluator := NewRuleEvaluator()
            result := evaluator.EvaluateRule(tt.rule, tt.telemetry)
            
            if result != tt.expected {
                t.Errorf("%s: got %v, want %v", tt.description, result, tt.expected)
            }
        })
    }
}
```

### 7.3 Integration Test Standards

```typescript
// ✅ CORRECT: Isolated, repeatable tests
describe('Device API Integration Tests', () => {
    let app: INestApplication;
    let authToken: string;
    
    beforeAll(async () => {
        const moduleRef = await Test.createTestingModule({
            imports: [AppModule],
        }).compile();
        
        app = moduleRef.createNestApplication();
        await app.init();
        
        // Setup: Create test user and get token
        const response = await request(app.getHttpServer())
            .post('/api/auth/login')
            .send({ email: 'test@example.com', password: 'test123' });
        authToken = response.body.token;
    });
    
    afterAll(async () => {
        await app.close();
    });
    
    it('should create a device', async () => {
        const createDeviceDto = {
            id: 'TEST_001',
            name: 'Test Device',
            type: 'bulb',
            location: 'Test Lab'
        };
        
        const response = await request(app.getHttpServer())
            .post('/api/v1/devices')
            .set('Authorization', `Bearer ${authToken}`)
            .send(createDeviceDto)
            .expect(201);
        
        expect(response.body.success).toBe(true);
        expect(response.body.data.id).toBe('TEST_001');
    });
    
    it('should reject invalid device ID', async () => {
        const invalidDto = {
            id: 'invalid id',  // Contains space
            name: 'Test',
            type: 'bulb'
        };
        
        await request(app.getHttpServer())
            .post('/api/v1/devices')
            .set('Authorization', `Bearer ${authToken}`)
            .send(invalidDto)
            .expect(400);
    });
});
```

### 7.4 Test Data Management

**RULES:**

1. **MUST** use fixtures or factories for test data
2. **MUST** clean up test data after each test
3. **MUST** use separate test database
4. **MUST NOT** depend on external services (use mocks)
5. **MUST** make tests deterministic (no random data)

---

## 8. DevOps & Deployment

### 8.1 Containerization Standards

```dockerfile
# ✅ CORRECT: Multi-stage build, non-root user, minimal image
FROM golang:1.21-alpine AS builder

WORKDIR /app

# Cache dependencies
COPY go.mod go.sum ./
RUN go mod download

# Build
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o main ./cmd/server

# Final stage
FROM alpine:3.18

RUN apk --no-cache add ca-certificates

# Create non-root user
RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser

WORKDIR /app

COPY --from=builder /app/main .

# Run as non-root
USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

CMD ["./main"]

# ❌ WRONG: Runs as root, no health check, bloated image
FROM golang:1.21
COPY . /app
WORKDIR /app
RUN go build -o main .
CMD ["./main"]
```

### 8.2 CI/CD Pipeline Requirements

**MANDATORY Steps:**

1. **Build Stage:**
   - Lint code
   - Run unit tests
   - Build Docker image
   - Scan for vulnerabilities (Trivy)

2. **Test Stage:**
   - Run integration tests
   - Run security tests (OWASP)
   - Check code coverage

3. **Deploy Stage:**
   - Deploy to staging
   - Run E2E tests
   - Deploy to production (manual approval)

```yaml
# .github/workflows/ci-cd.yml
# ✅ CORRECT: Comprehensive pipeline
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Go
        uses: actions/setup-go@v4
        with:
          go-version: '1.21'
      
      - name: Lint
        run: |
          go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
          golangci-lint run
      
      - name: Run tests
        run: |
          go test -v -race -coverprofile=coverage.out ./...
          go tool cover -func=coverage.out
      
      - name: Check coverage
        run: |
          coverage=$(go tool cover -func=coverage.out | grep total | awk '{print $3}' | sed 's/%//')
          if (( $(echo "$coverage < 80" | bc -l) )); then
            echo "Coverage is below 80%: $coverage%"
            exit 1
          fi
      
      - name: Build Docker image
        run: docker build -t energy-platform/data-service:${{ github.sha }} .
      
      - name: Scan for vulnerabilities
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: energy-platform/data-service:${{ github.sha }}
          severity: 'CRITICAL,HIGH'
```

### 8.3 Deployment Configuration

```yaml
# k8s/deployment.yaml
# ✅ CORRECT: Resource limits, health checks, security
apiVersion: apps/v1
kind: Deployment
metadata:
  name: data-service
  namespace: energy-platform
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: data-service
  template:
    metadata:
      labels:
        app: data-service
        version: v1.0.0
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
      containers:
      - name: data-service
        image: energy-platform/data-service:latest
        ports:
        - containerPort: 8081
        env:
        - name: LOG_LEVEL
          value: "info"
        envFrom:
        - secretRef:
            name: data-service-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1"
        livenessProbe:
          httpGet:
            path: /health
            port: 8081
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8081
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
```

---

## 9. Documentation Requirements

### 9.1 Code Documentation

**MANDATORY:**

1. **MUST** document all public APIs
2. **MUST** include usage examples
3. **MUST** document error conditions
4. **MUST** keep README.md updated

```go
// ✅ CORRECT: Complete documentation
// ProcessTelemetry validates and stores incoming device telemetry data.
//
// The function performs the following steps:
//   1. Validates the telemetry payload against schema
//   2. Enriches data with device metadata
//   3. Stores in InfluxDB with appropriate tags
//   4. Triggers rule evaluation asynchronously
//
// Parameters:
//   - ctx: Context for cancellation and timeout control
//   - payload: Validated telemetry data from MQTT message
//
// Returns:
//   - error: Returns error if validation fails or storage fails.
//     Possible errors: ValidationError, StorageError
//
// Example:
//   payload := TelemetryPayload{
//       DeviceID: "D1",
//       Timestamp: time.Now(),
//       Voltage: 230.5,
//       Current: 0.85,
//       Power: 195.9,
//       Temperature: 45.2,
//   }
//   err := processor.ProcessTelemetry(ctx, payload)
//   if err != nil {
//       log.Errorf("Failed to process telemetry: %v", err)
//   }
func (p *TelemetryProcessor) ProcessTelemetry(ctx context.Context, payload TelemetryPayload) error {
    // Implementation
}
```

### 9.2 API Documentation

**MUST** use OpenAPI 3.0 specification:

```yaml
# openapi.yaml
openapi: 3.0.0
info:
  title: Energy Platform API
  version: 1.0.0
  description: API for energy intelligence and analytics platform

paths:
  /api/v1/devices:
    get:
      summary: List all devices
      tags: [Devices]
      security:
        - bearerAuth: []
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
        - name: page_size
          in: query
          schema:
            type: integer
            default: 20
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                  data:
                    type: object
                    properties:
                      items:
                        type: array
                        items:
                          $ref: '#/components/schemas/Device'
                      total:
                        type: integer
        '401':
          $ref: '#/components/responses/Unauthorized'

components:
  schemas:
    Device:
      type: object
      required:
        - id
        - name
        - type
      properties:
        id:
          type: string
          example: D1
        name:
          type: string
          example: Electric Bulb
        type:
          type: string
          enum: [bulb, compressor, motor]
        health_score:
          type: number
          format: float
          minimum: 0
          maximum: 100
```

---

## 10. Performance Standards

### 10.1 Response Time SLAs

**MANDATORY Targets:**

| Operation | Target (p95) | Maximum (p99) |
|-----------|--------------|---------------|
| API GET | ≤ 200ms | ≤ 500ms |
| API POST | ≤ 500ms | ≤ 1s |
| Telemetry ingestion | ≤ 2s | ≤ 5s |
| Rule evaluation | ≤ 500ms | ≤ 1s |
| Dashboard load | ≤ 3s | ≤ 5s |

### 10.2 Optimization Rules

**MUST:**

1. Use database connection pooling
2. Implement caching for frequently accessed data
3. Use pagination for large result sets
4. Optimize database queries (use EXPLAIN ANALYZE)
5. Implement lazy loading for heavy resources
6. Use CDN for static assets
7. Compress API responses (gzip)

```go
// ✅ CORRECT: Caching for device metadata
type DeviceService struct {
    repo  DeviceRepository
    cache *redis.Client
}

func (s *DeviceService) GetDevice(ctx context.Context, id string) (*Device, error) {
    // Check cache first
    cacheKey := fmt.Sprintf("device:%s", id)
    cached, err := s.cache.Get(ctx, cacheKey).Result()
    if err == nil {
        var device Device
        json.Unmarshal([]byte(cached), &device)
        return &device, nil
    }
    
    // Cache miss - fetch from database
    device, err := s.repo.FindByID(ctx, id)
    if err != nil {
        return nil, err
    }
    
    // Store in cache (1 hour TTL)
    data, _ := json.Marshal(device)
    s.cache.Set(ctx, cacheKey, data, 1*time.Hour)
    
    return device, nil
}
```

---

## 11. Monitoring & Logging

### 11.1 Logging Standards

**MANDATORY:**

1. **MUST** use structured logging (JSON format)
2. **MUST** include correlation IDs for request tracing
3. **MUST** log at appropriate levels (DEBUG, INFO, WARN, ERROR)
4. **MUST NOT** log sensitive data (passwords, tokens)
5. **MUST** include context in error logs

```go
// ✅ CORRECT: Structured logging with context
import "github.com/rs/zerolog/log"

func ProcessTelemetry(ctx context.Context, payload TelemetryPayload) error {
    logger := log.With().
        Str("device_id", payload.DeviceID).
        Str("correlation_id", getCorrelationID(ctx)).
        Logger()
    
    logger.Info().Msg("Processing telemetry")
    
    if err := validate(payload); err != nil {
        logger.Error().
            Err(err).
            Interface("payload", payload).
            Msg("Validation failed")
        return err
    }
    
    logger.Info().
        Float64("power", payload.Power).
        Float64("temperature", payload.Temperature).
        Msg("Telemetry processed successfully")
    
    return nil
}

// ❌ WRONG: Unstructured logging, no context
func ProcessTelemetry(payload TelemetryPayload) error {
    fmt.Println("Processing telemetry for", payload.DeviceID)
    
    if err := validate(payload); err != nil {
        fmt.Println("Error:", err)  // No context, not searchable
        return err
    }
    
    return nil
}
```

### 11.2 Metrics Collection

**MUST Implement:**

1. Request rate (requests/sec)
2. Error rate (errors/sec)
3. Response time distribution (p50, p95, p99)
4. Resource utilization (CPU, memory)
5. Database query performance
6. Queue depth
7. Cache hit rate

```go
// ✅ CORRECT: Prometheus metrics
import (
    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promauto"
)

var (
    telemetryProcessed = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Name: "telemetry_messages_processed_total",
            Help: "Total number of telemetry messages processed",
        },
        []string{"device_id", "status"},
    )
    
    ruleEvaluationDuration = promauto.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "rule_evaluation_duration_seconds",
            Help:    "Duration of rule evaluation in seconds",
            Buckets: prometheus.DefBuckets,
        },
        []string{"rule_id"},
    )
)

func ProcessTelemetry(payload TelemetryPayload) error {
    start := time.Now()
    defer func() {
        duration := time.Since(start).Seconds()
        ruleEvaluationDuration.WithLabelValues(payload.DeviceID).Observe(duration)
    }()
    
    // Process...
    
    telemetryProcessed.WithLabelValues(payload.DeviceID, "success").Inc()
    return nil
}
```

---

## 12. Code Review Process

### 12.1 Review Checklist

**Before Requesting Review:**

- [ ] Code follows style guide
- [ ] Tests written and passing (>80% coverage)
- [ ] Documentation updated
- [ ] No hardcoded secrets
- [ ] Error handling implemented
- [ ] Logging added
- [ ] Performance considered
- [ ] Security reviewed

### 12.2 Review Standards

**Reviewers MUST Check:**

1. **Functionality**: Does it solve the problem?
2. **Design**: Is it the right approach?
3. **Complexity**: Is it unnecessarily complex?
4. **Tests**: Are edge cases covered?
5. **Naming**: Are names clear and consistent?
6. **Documentation**: Is it adequate?
7. **Security**: Any vulnerabilities?
8. **Performance**: Any bottlenecks?

### 12.3 PR Guidelines

```markdown
## ✅ GOOD Pull Request

### Title
feat(device-service): Add health score calculation

### Description
Implements health score calculation for devices based on:
- Uptime percentage (40% weight)
- Data quality (30% weight)
- Error rate (20% weight)
- Response time (10% weight)

### Changes
- Added `CalculateHealthScore` method to DeviceService
- Implemented background job to update scores every hour
- Added health score column to devices table
- Updated device API to include health score

### Testing
- Unit tests for calculation logic
- Integration tests for background job
- Manual testing with D1 simulator

### Related Issues
Closes #123

### Screenshots
[Dashboard showing health scores]

---

## ❌ BAD Pull Request

### Title
Update

### Description
Changed some stuff

### Changes
- Fixed things
- Made improvements
```

---

## Enforcement

### Violations

**Minor Violations** (Warning):
- Missing tests
- Inadequate documentation
- Style guide deviations

**Major Violations** (PR Rejection):
- Security vulnerabilities
- No error handling
- Hardcoded secrets
- Performance issues

**Critical Violations** (Escalation):
- Data loss potential
- Production outage risk
- Compliance violations

---

## Updates to These Rules

These rules are living documents. Updates require:
1. Proposal via RFC (Request for Comments)
2. Team discussion and consensus
3. Architecture review approval
4. Communication to all team members
5. Grace period for adoption (2 weeks)

---

**Last Updated:** February 7, 2026  
**Version:** 1.0  
**Maintained By:** Architecture Team
