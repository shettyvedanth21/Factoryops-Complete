# """
# Validation utilities for telemetry data.
# """

# from typing import Any, Dict, List, Optional, Tuple
# from datetime import datetime

# from src.config import settings
# from src.models import TelemetryPayload


# class ValidationError(Exception):
#     """Raised when telemetry validation fails."""

#     def __init__(self, message: str, field: Optional[str] = None):
#         """
#         Initialize validation error.

#         Args:
#             message: Error message
#             field: Field that failed validation (optional)
#         """
#         self.message = message
#         self.field = field
#         super().__init__(message)


# class TelemetryValidator:
#     """Validator for telemetry payloads."""

#     REQUIRED_FIELDS = [
#         "device_id",
#         "timestamp",
#         "voltage",
#         "current",
#         "power",
#         "temperature",
#     ]

#     NUMERIC_RANGES = {
#         "voltage": (
#             settings.telemetry_min_voltage,
#             settings.telemetry_max_voltage,
#         ),
#         "current": (
#             settings.telemetry_min_current,
#             settings.telemetry_max_current,
#         ),
#         "power": (
#             settings.telemetry_min_power,
#             settings.telemetry_max_power,
#         ),
#         "temperature": (
#             settings.telemetry_min_temperature,
#             settings.telemetry_max_temperature,
#         ),
#     }

#     @classmethod
#     def validate_payload(
#         cls, payload: Dict[str, Any]
#     ) -> Tuple[bool, Optional[str], Optional[str]]:
#         """
#         Validate raw payload dictionary.

#         Args:
#             payload: Raw telemetry payload

#         Returns:
#             Tuple of (is_valid, error_type, error_message)
#         """
#         try:
#             # 1. Required fields
#             missing_fields = cls._check_required_fields(payload)
#             if missing_fields:
#                 return (
#                     False,
#                     "missing_required_fields",
#                     f"Missing required fields: {missing_fields}",
#                 )

#             # 2. Schema version
#             schema_version = payload.get("schema_version", "v1")
#             if schema_version != settings.telemetry_schema_version:
#                 return (
#                     False,
#                     "unsupported_schema_version",
#                     f"Unsupported schema version: {schema_version}. "
#                     f"Only '{settings.telemetry_schema_version}' is supported.",
#                 )

#             # 3. Numeric ranges
#             range_errors = cls._check_numeric_ranges(payload)
#             if range_errors:
#                 return (
#                     False,
#                     "range_validation_failed",
#                     f"Range validation failed: {range_errors}",
#                 )

#             # 4. Timestamp
#             timestamp_error = cls._validate_timestamp(payload.get("timestamp"))
#             if timestamp_error:
#                 return False, "invalid_timestamp", timestamp_error

#             # 5. Final schema validation (Pydantic)
#             TelemetryPayload(**payload)

#             return True, None, None

#         except Exception as e:
#             return False, "validation_error", str(e)

#     @classmethod
#     def _check_required_fields(cls, payload: Dict[str, Any]) -> List[str]:
#         """
#         Check for missing required fields.

#         Args:
#             payload: Raw payload

#         Returns:
#             List of missing field names
#         """
#         return [field for field in cls.REQUIRED_FIELDS if field not in payload]

#     @classmethod
#     def _check_numeric_ranges(cls, payload: Dict[str, Any]) -> List[str]:
#         """
#         Check numeric fields are within valid ranges.

#         Args:
#             payload: Raw payload

#         Returns:
#             List of range validation errors
#         """
#         errors: List[str] = []

#         for field, (min_val, max_val) in cls.NUMERIC_RANGES.items():
#             if field not in payload:
#                 continue

#             try:
#                 value = float(payload[field])

#                 if value < min_val or value > max_val:
#                     errors.append(
#                         f"{field}={value} is outside range "
#                         f"[{min_val}, {max_val}]"
#                     )

#             except (ValueError, TypeError):
#                 errors.append(
#                     f"{field} is not a valid number: {payload[field]}"
#                 )

#         return errors

#     @classmethod
#     def _validate_timestamp(cls, timestamp: Any) -> Optional[str]:
#         """
#         Validate timestamp format.

#         Args:
#             timestamp: Timestamp value

#         Returns:
#             Error message if invalid, None if valid
#         """
#         if timestamp is None:
#             return "Timestamp is required"

#         try:
#             if isinstance(timestamp, str):
#                 # ISO 8601
#                 datetime.fromisoformat(
#                     timestamp.replace("Z", "+00:00")
#                 )

#             elif isinstance(timestamp, (int, float)):
#                 # Unix timestamp
#                 datetime.fromtimestamp(timestamp)

#             elif not isinstance(timestamp, datetime):
#                 return f"Invalid timestamp type: {type(timestamp)}"

#         except (ValueError, OSError) as e:
#             return f"Invalid timestamp format: {e}"

#         return None

#     @classmethod
#     def validate_and_parse(cls, payload: Dict[str, Any]) -> TelemetryPayload:
#         """
#         Validate and parse payload into TelemetryPayload model.

#         Args:
#             payload: Raw telemetry payload

#         Returns:
#             Validated TelemetryPayload

#         Raises:
#             ValidationError: If validation fails
#         """
#         is_valid, error_type, error_message = cls.validate_payload(payload)

#         if not is_valid:
#             raise ValidationError(
#                 error_message or "Validation failed",
#                 error_type,
#             )

#         try:
#             return TelemetryPayload(**payload)

#         except Exception as e:
#             raise ValidationError(
#                 f"Failed to parse payload: {e}",
#                 "parse_error",
#             )






#GPT GENERATED CODE - FIXED ABOVE VERSIONED
"""
Validation utilities for telemetry data.
"""

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from src.config import settings
from src.models import TelemetryPayload


class ValidationError(Exception):
    """Raised when telemetry validation fails."""

    def __init__(self, message: str, field: Optional[str] = None):
        """
        Initialize validation error.

        Args:
            message: Error message
            field: Field that failed validation (optional)
        """
        self.message = message
        self.field = field
        super().__init__(message)


class TelemetryValidator:
    """Validator for telemetry payloads."""

    REQUIRED_FIELDS = [
        "device_id",
        "timestamp",
        "voltage",
        "current",
        "power",
        "temperature",
        "schema_version",
    ]

    NUMERIC_RANGES = {
        "voltage": (
            settings.telemetry_min_voltage,
            settings.telemetry_max_voltage,
        ),
        "current": (
            settings.telemetry_min_current,
            settings.telemetry_max_current,
        ),
        "power": (
            settings.telemetry_min_power,
            settings.telemetry_max_power,
        ),
        "temperature": (
            settings.telemetry_min_temperature,
            settings.telemetry_max_temperature,
        ),
    }

    @classmethod
    def validate_payload(
        cls,
        payload: Dict[str, Any],
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate raw payload dictionary.

        Args:
            payload: Raw telemetry payload

        Returns:
            Tuple of (is_valid, error_type, error_message)
        """
        try:
            # ---------------------------------------------------------
            # Required fields
            # ---------------------------------------------------------
            missing_fields = cls._check_required_fields(payload)
            if missing_fields:
                return (
                    False,
                    "missing_required_fields",
                    f"Missing required fields: {missing_fields}",
                )

            # ---------------------------------------------------------
            # Schema version (strict)
            # ---------------------------------------------------------
            schema_version = payload.get("schema_version")

            if schema_version is None:
                return (
                    False,
                    "missing_schema_version",
                    "Missing required field: schema_version",
                )

            if schema_version != settings.telemetry_schema_version:
                return (
                    False,
                    "unsupported_schema_version",
                    f"Unsupported schema version: {schema_version}. "
                    f"Only '{settings.telemetry_schema_version}' is supported.",
                )

            # ---------------------------------------------------------
            # Numeric ranges
            # ---------------------------------------------------------
            range_errors = cls._check_numeric_ranges(payload)
            if range_errors:
                return (
                    False,
                    "range_validation_failed",
                    f"Range validation failed: {range_errors}",
                )

            # ---------------------------------------------------------
            # Timestamp validation
            # ---------------------------------------------------------
            timestamp_error = cls._validate_timestamp(payload.get("timestamp"))
            if timestamp_error:
                return (
                    False,
                    "invalid_timestamp",
                    timestamp_error,
                )

            # ---------------------------------------------------------
            # Final structural validation via Pydantic model
            # ---------------------------------------------------------
            TelemetryPayload(**payload)

            return True, None, None

        except Exception as e:
            return False, "validation_error", str(e)

    @classmethod
    def _check_required_fields(
        cls,
        payload: Dict[str, Any],
    ) -> List[str]:
        """
        Check for missing required fields.

        Args:
            payload: Raw payload

        Returns:
            List of missing field names
        """
        missing: List[str] = []
        for field in cls.REQUIRED_FIELDS:
            if field not in payload:
                missing.append(field)
        return missing

    @classmethod
    def _check_numeric_ranges(
        cls,
        payload: Dict[str, Any],
    ) -> List[str]:
        """
        Check numeric fields are within valid ranges.

        Args:
            payload: Raw payload

        Returns:
            List of range validation errors
        """
        errors: List[str] = []

        for field, (min_val, max_val) in cls.NUMERIC_RANGES.items():
            if field in payload:
                try:
                    value = float(payload[field])
                    if value < min_val or value > max_val:
                        errors.append(
                            f"{field}={value} is outside range "
                            f"[{min_val}, {max_val}]"
                        )
                except (ValueError, TypeError):
                    errors.append(
                        f"{field} is not a valid number: {payload[field]}"
                    )

        return errors

    @classmethod
    def _validate_timestamp(
        cls,
        timestamp: Any,
    ) -> Optional[str]:
        """
        Validate timestamp format.

        Args:
            timestamp: Timestamp value

        Returns:
            Error message if invalid, None if valid
        """
        if timestamp is None:
            return "Timestamp is required"

        try:
            if isinstance(timestamp, str):
                # ISO 8601 (allow Z)
                datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            elif isinstance(timestamp, (int, float)):
                # Unix timestamp
                datetime.fromtimestamp(timestamp)
            elif isinstance(timestamp, datetime):
                pass
            else:
                return f"Invalid timestamp type: {type(timestamp)}"
        except (ValueError, OSError) as e:
            return f"Invalid timestamp format: {e}"

        return None

    @classmethod
    def validate_and_parse(
        cls,
        payload: Dict[str, Any],
    ) -> TelemetryPayload:
        """
        Validate and parse payload into TelemetryPayload model.

        Args:
            payload: Raw telemetry payload

        Returns:
            Validated TelemetryPayload

        Raises:
            ValidationError: If validation fails
        """
        is_valid, error_type, error_message = cls.validate_payload(payload)

        if not is_valid:
            raise ValidationError(
                error_message or "Validation failed",
                error_type,
            )

        try:
            return TelemetryPayload(**payload)
        except Exception as e:
            raise ValidationError(
                f"Failed to parse payload: {e}",
                "parse_error",
            )