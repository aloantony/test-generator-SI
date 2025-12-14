"""JSON schema validation utilities.

This module provides a thin wrapper around the ``jsonschema`` library
to validate parsed exam documents against the canonical schema. A
custom exception is raised on validation errors to allow callers to
handle them appropriately.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import jsonschema


class SchemaValidationError(Exception):
    """Raised when a JSON document fails schema validation."""
    def __init__(self, message: str, errors: list | None = None) -> None:
        super().__init__(message)
        self.errors = errors or []


def _load_schema(schema_path: Path) -> Dict[str, Any]:
    with schema_path.open("r", encoding="utf-8") as f:
        schema = json.load(f)
    return schema


def validate(data: Dict[str, Any], schema_path: Path) -> None:
    """Validate ``data`` against the JSON schema at ``schema_path``.

    Args:
        data: Parsed JSON document to validate.
        schema_path: Path to the JSON schema file.

    Raises:
        SchemaValidationError: If validation fails.
    """
    schema = _load_schema(schema_path)
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as exc:
        # Collect messages from nested contexts if available
        errors = [exc.message]
        context = getattr(exc, "context", [])
        for e in context:
            errors.append(e.message)
        raise SchemaValidationError("JSON document failed schema validation", errors) from exc