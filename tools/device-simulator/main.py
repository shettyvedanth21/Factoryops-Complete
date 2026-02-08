"""CLI entry point for device simulator."""
import argparse
import json
import logging
import sys
from typing import Optional

from config import SimulatorConfig
from simulator import DeviceSimulator


def setup_logging(log_level: str) -> None:
    """Configure structured JSON logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Create console handler with JSON formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, log_level.upper()))
    
    # Use JSON formatter for structured logging
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    # Add handler to root logger
    logger.addHandler(handler)
    
    # Suppress paho-mqtt debug logs unless DEBUG level
    if log_level.upper() != "DEBUG":
        logging.getLogger("paho").setLevel(logging.WARNING)


def parse_arguments() -> SimulatorConfig:
    """Parse command line arguments.
    
    Returns:
        SimulatorConfig with parsed values
    """
    parser = argparse.ArgumentParser(
        description="Energy Intelligence Platform - Device Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --device-id D1 --interval 5
  python main.py --device-id D1 --broker mqtt.example.com --port 1883
  python main.py --device-id D1 --interval 2 --fault-mode overheating
        """
    )
    
    parser.add_argument(
        "--device-id",
        type=str,
        required=True,
        help="Device identifier (e.g., D1)"
    )
    
    parser.add_argument(
        "--interval",
        type=float,
        default=5.0,
        help="Publish interval in seconds (default: 5)"
    )
    
    parser.add_argument(
        "--broker",
        type=str,
        default="localhost",
        help="MQTT broker host (default: localhost)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=1883,
        help="MQTT broker port (default: 1883)"
    )
    
    parser.add_argument(
        "--fault-mode",
        type=str,
        default="none",
        choices=["none", "spike", "drop", "overheating"],
        help="Fault injection mode for testing (default: none)"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    return SimulatorConfig(
        device_id=args.device_id,
        publish_interval=args.interval,
        broker_host=args.broker,
        broker_port=args.port,
        fault_mode=args.fault_mode,
        log_level=args.log_level
    )


def main() -> int:
    """Main entry point.
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        # Parse arguments
        config = parse_arguments()
        
        # Setup logging
        setup_logging(config.log_level)
        
        # Create and start simulator
        simulator = DeviceSimulator(config)
        simulator.start()
        
        return 0
        
    except ValueError as e:
        logging.error(f"Configuration error: {e}")
        return 1
    except KeyboardInterrupt:
        logging.info("Interrupted by user")
        return 0
    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
