Device list
GET http://localhost:8000/api/v1/devices

Device details
GET http://localhost:8000/api/v1/devices/{deviceId}

Telemetry list / charts
GET http://localhost:8081/api/data/devices/{deviceId}/telemetry

Stats
GET http://localhost:8081/api/data/devices/{deviceId}/stats
