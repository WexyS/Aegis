"""
AEGIS Core Errors — Structured error hierarchy.

Phase 1 scope: base error + intent + config + schema errors.
Guard, execution, model, memory errors will be added in their phases.
"""

from __future__ import annotations

from typing import Any


class AegisError(Exception):
    """Base error for all Aegis exceptions."""

    def __init__(self, message: str, code: str = "AEGIS_ERROR", details: dict[str, Any] | None = None):
        super().__init__(message)
        self.code = code
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": str(self),
            "details": self.details,
        }


# --- Intent Errors ---

class IntentParsingError(AegisError):
    """Failed to parse user intent."""

    def __init__(self, message: str, raw_input: str = "", **kwargs: Any):
        super().__init__(message, code="INTENT_PARSING_ERROR", details={"raw_input": raw_input, **kwargs})


class UnknownIntentError(AegisError):
    """Intent could not be determined — system will NOT guess."""

    def __init__(self, raw_input: str):
        super().__init__(
            f"Could not determine intent for input: {raw_input!r}",
            code="UNKNOWN_INTENT",
            details={"raw_input": raw_input},
        )


# --- Config Errors ---

class ConfigurationError(AegisError):
    """Configuration is invalid or missing."""

    def __init__(self, message: str, **kwargs: Any):
        super().__init__(message, code="CONFIG_ERROR", details=kwargs)


# --- Schema Errors ---

class SchemaValidationError(AegisError):
    """Data failed JSON schema or Pydantic validation."""

    def __init__(self, schema_name: str, errors: list[Any], **kwargs: Any):
        super().__init__(
            f"Schema validation failed for '{schema_name}'",
            code="SCHEMA_VALIDATION_ERROR",
            details={"schema_name": schema_name, "validation_errors": errors, **kwargs},
        )
