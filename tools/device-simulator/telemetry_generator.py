"""Telemetry data generator with realistic patterns and fault injection."""
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class TelemetryPoint:
    """Single telemetry data point.
    
    Attributes:
        device_id: Device identifier
        timestamp: ISO-8601 formatted UTC timestamp
        schema_version: Schema version string
        voltage: Voltage in Volts (200-250)
        current: Current in Amperes (0-2)
        power: Power in Watts (0-500)
        temperature: Temperature in Celsius (20-80)
    """
    device_id: str
    timestamp: str
    schema_version: str
    voltage: float
    current: float
    power: float
    temperature: float
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "device_id": self.device_id,
            "timestamp": self.timestamp,
            "schema_version": self.schema_version,
            "voltage": round(self.voltage, 2),
            "current": round(self.current, 3),
            "power": round(self.power, 2),
            "temperature": round(self.temperature, 2)
        }


class TelemetryGenerator:
    """Generate realistic telemetry data with time-series patterns.
    
    This generator creates smooth, realistic variations in sensor readings
    with configurable noise levels and optional fault injection for testing.
    """
    
    # Baseline values for normal operation
    BASELINE_VOLTAGE = 230.0
    BASELINE_CURRENT = 0.85
    BASELINE_POWER = 195.5  # Calculated: V * I * PF (power factor ~1)
    BASELINE_TEMPERATURE = 45.0
    
    # Valid ranges (per PRD specification)
    VOLTAGE_MIN = 200.0
    VOLTAGE_MAX = 250.0
    CURRENT_MIN = 0.0
    CURRENT_MAX = 2.0
    POWER_MIN = 0.0
    POWER_MAX = 500.0
    TEMPERATURE_MIN = 20.0
    TEMPERATURE_MAX = 80.0
    
    def __init__(
        self,
        device_id: str,
        fault_mode: str = "none",
        noise_factor: float = 0.02
    ):
        """Initialize telemetry generator.
        
        Args:
            device_id: Device identifier
            fault_mode: Fault injection mode ('none', 'spike', 'drop', 'overheating')
            noise_factor: Amount of random noise (0.0 to 1.0)
        """
        self._device_id = device_id
        self._fault_mode = fault_mode
        self._noise_factor = noise_factor
        
        # Current state (for smooth transitions)
        self._voltage = self.BASELINE_VOLTAGE
        self._current = self.BASELINE_CURRENT
        self._temperature = self.BASELINE_TEMPERATURE
        
        # Fault injection state
        self._fault_counter = 0
        self._in_fault_state = False
    
    def generate(self) -> TelemetryPoint:
        """Generate next telemetry data point.
        
        Returns:
            TelemetryPoint with realistic sensor values
        """
        # Generate smooth variations
        self._voltage = self._update_value(
            self._voltage,
            self.BASELINE_VOLTAGE,
            max_delta=2.0,
            noise_scale=1.0
        )
        
        self._current = self._update_value(
            self._current,
            self.BASELINE_CURRENT,
            max_delta=0.1,
            noise_scale=0.05
        )
        
        # Power is derived: P = V * I (assuming power factor of 1 for simplicity)
        power = self._voltage * self._current
        
        # Temperature has some lag and correlation with power
        target_temp = self.BASELINE_TEMPERATURE + (power - self.BASELINE_POWER) * 0.05
        self._temperature = self._update_value(
            self._temperature,
            target_temp,
            max_delta=0.5,
            noise_scale=0.3
        )
        
        # Apply fault injection if enabled
        if self._fault_mode != "none":
            self._voltage, self._current, power, self._temperature = self._apply_fault(
                self._voltage, self._current, power, self._temperature
            )
        
        # Clamp values to valid ranges
        self._voltage = max(self.VOLTAGE_MIN, min(self.VOLTAGE_MAX, self._voltage))
        self._current = max(self.CURRENT_MIN, min(self.CURRENT_MAX, self._current))
        power = max(self.POWER_MIN, min(self.POWER_MAX, power))
        self._temperature = max(self.TEMPERATURE_MIN, min(self.TEMPERATURE_MAX, self._temperature))
        
        return TelemetryPoint(
            device_id=self._device_id,
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            schema_version="v1",
            voltage=self._voltage,
            current=self._current,
            power=power,
            temperature=self._temperature
        )
    
    def _update_value(
        self,
        current: float,
        target: float,
        max_delta: float,
        noise_scale: float
    ) -> float:
        """Update value with smooth transition towards target plus noise.
        
        Args:
            current: Current value
            target: Target value to drift towards
            max_delta: Maximum change per update
            noise_scale: Scale of random noise
            
        Returns:
            Updated value
        """
        # Drift towards target
        drift = (target - current) * 0.1
        drift = max(-max_delta, min(max_delta, drift))
        
        # Add noise
        noise = random.gauss(0, noise_scale) * self._noise_factor
        
        return current + drift + noise
    
    def _apply_fault(
        self,
        voltage: float,
        current: float,
        power: float,
        temperature: float
    ) -> tuple[float, float, float, float]:
        """Apply fault injection patterns.
        
        Args:
            voltage: Current voltage value
            current: Current current value
            power: Current power value
            temperature: Current temperature value
            
        Returns:
            Tuple of (voltage, current, power, temperature) with fault applied
        """
        self._fault_counter += 1
        
        if self._fault_mode == "spike":
            # Random voltage spikes
            if random.random() < 0.1:  # 10% chance
                voltage += random.uniform(20, 50)
                self._in_fault_state = True
            elif self._in_fault_state and random.random() < 0.3:
                self._in_fault_state = False
                
        elif self._fault_mode == "drop":
            # Random power drops (current drops to near zero)
            if random.random() < 0.05:  # 5% chance
                current = random.uniform(0.01, 0.1)
                power = voltage * current
                self._in_fault_state = True
            elif self._in_fault_state and random.random() < 0.5:
                self._in_fault_state = False
                
        elif self._fault_mode == "overheating":
            # Gradual temperature increase
            if self._fault_counter % 20 == 0:  # Every 20 readings
                temperature += random.uniform(2, 5)
                self._in_fault_state = True
            elif temperature > 70:
                # Gradual cool down after reaching high temp
                temperature -= random.uniform(0.5, 1.5)
                if temperature < 50:
                    self._in_fault_state = False
                    self._fault_counter = 0
        
        return voltage, current, power, temperature
