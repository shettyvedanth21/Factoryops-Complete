"""Configuration management for device simulator."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class SimulatorConfig:
    """Configuration for device simulator.
    
    Attributes:
        device_id: Unique device identifier
        publish_interval: Time between telemetry messages in seconds
        broker_host: MQTT broker hostname or IP
        broker_port: MQTT broker port number
        fault_mode: Fault injection mode for testing
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    device_id: str
    publish_interval: float = 5.0
    broker_host: str = "localhost"
    broker_port: int = 1883
    fault_mode: str = "none"
    log_level: str = "INFO"
    
    def __post_init__(self):
        """Validate configuration parameters."""
        if not self.device_id:
            raise ValueError("device_id cannot be empty")
        if self.publish_interval <= 0:
            raise ValueError("publish_interval must be positive")
        if self.broker_port <= 0 or self.broker_port > 65535:
            raise ValueError("broker_port must be between 1 and 65535")
        valid_fault_modes = {"none", "spike", "drop", "overheating"}
        if self.fault_mode not in valid_fault_modes:
            raise ValueError(f"fault_mode must be one of {valid_fault_modes}")
    
    @property
    def topic(self) -> str:
        """Generate MQTT topic for this device."""
        return f"devices/{self.device_id}/telemetry"
