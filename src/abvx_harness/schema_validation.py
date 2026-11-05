"""Draft 2020-12 structural validation; domain semantics remain ABVX-owned."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class SchemaDependencyError(RuntimeError):
    pass


def draft_2020_12_validator(schema: dict[str, Any]):
    """Construct a checked Draft 2020-12 validator, including internal refs."""
    try:
        from jsonschema import Draft202012Validator, FormatChecker
        from referencing import Registry
        from referencing.exceptions import NoSuchResource
    except ImportError as error:
        raise SchemaDependencyError(
            "python-jsonschema is required; install pinned development/runtime requirements"
        ) from error
    if not isinstance(schema, dict) or schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise ValueError("schema must declare Draft 2020-12 explicitly")
    Draft202012Validator.check_schema(schema)
    def reject_remote(uri):
        raise NoSuchResource(ref=uri)
    return Draft202012Validator(schema, format_checker=FormatChecker(),
                               registry=Registry(retrieve=reject_remote))


def load_draft_2020_12_validator(schema_path: Path):
    """Load and check a local Draft 2020-12 schema with standard format checks."""
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot load JSON Schema {schema_path}: {error}") from error
    return draft_2020_12_validator(schema)


def validate_draft_2020_12(instance: Any, schema_path: Path) -> list[dict[str, str]]:
    """Return sorted shape errors; resolution failures remain explicit exceptions."""
    validator = load_draft_2020_12_validator(schema_path)
    errors = sorted(validator.iter_errors(instance), key=lambda item: (list(map(str, item.absolute_path)), item.message))
    return [{"path": "/" + "/".join(map(str, error.absolute_path)), "message": error.message}
            for error in errors]
