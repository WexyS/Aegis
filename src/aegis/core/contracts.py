"""
AEGIS Core Contracts — JSON Schema validator utility.

Validates data against the JSON schemas in the schemas/ directory.
This is the enforcement layer — every data structure that crosses
a boundary (API ↔ core, core ↔ tool, etc.) must pass validation.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import jsonschema
from jsonschema import Draft7Validator, ValidationError

from aegis.core.config import SCHEMAS_DIR
from aegis.core.errors import SchemaValidationError


# ---------------------------------------------------------------------------
# Schema loading
# ---------------------------------------------------------------------------

@lru_cache(maxsize=32)
def _load_schema(schema_name: str) -> dict[str, Any]:
    """Load and cache a JSON schema by name.

    Args:
        schema_name: Schema filename without extension (e.g., "intent").

    Returns:
        Parsed JSON schema dict.
    """
    path = SCHEMAS_DIR / f"{schema_name}.schema.json"
    if not path.exists():
        raise SchemaValidationError(
            schema_name=schema_name,
            errors=[f"Schema file not found: {path}"],
        )

    with open(path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    # Pre-compile to catch schema errors early
    Draft7Validator.check_schema(schema)
    return schema


@lru_cache(maxsize=32)
def _get_validator(schema_name: str) -> Draft7Validator:
    """Get a cached, compiled validator for a schema."""
    schema = _load_schema(schema_name)

    # Create a resolver that can handle $ref to sibling schemas
    resolver = jsonschema.RefResolver(
        base_uri=f"file:///{SCHEMAS_DIR.as_posix()}/",
        referrer=schema,
    )

    return Draft7Validator(schema, resolver=resolver)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate(data: dict[str, Any], schema_name: str) -> None:
    """Validate data against a named schema.

    Args:
        data: The data dict to validate.
        schema_name: Schema name (e.g., "intent", "tool_call", "guard_decision").

    Raises:
        SchemaValidationError: If validation fails.
    """
    validator = _get_validator(schema_name)
    errors = list(validator.iter_errors(data))

    if errors:
        formatted = [
            {
                "path": ".".join(str(p) for p in e.absolute_path),
                "message": e.message,
                "validator": e.validator,
            }
            for e in errors
        ]
        raise SchemaValidationError(schema_name=schema_name, errors=formatted)


def is_valid(data: dict[str, Any], schema_name: str) -> bool:
    """Check if data is valid against a named schema (no exception).

    Args:
        data: The data dict to validate.
        schema_name: Schema name.

    Returns:
        True if valid, False otherwise.
    """
    try:
        validate(data, schema_name)
        return True
    except SchemaValidationError:
        return False


def get_schema(schema_name: str) -> dict[str, Any]:
    """Get a raw schema dict by name. Useful for introspection / API docs."""
    return _load_schema(schema_name)


def list_schemas() -> list[str]:
    """List all available schema names."""
    return sorted(
        p.stem.replace(".schema", "")
        for p in SCHEMAS_DIR.glob("*.schema.json")
    )
