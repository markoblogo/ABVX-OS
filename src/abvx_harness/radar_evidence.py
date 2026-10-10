"""Small policy helpers for versioned Book Radar evidence records."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .harness import ValidationError, validate

COLLECTION_STATUSES = frozenset({
    "SUCCESS", "NO_RESULT", "COLLECTION_FAILED", "BLOCKED", "CAPTCHA",
    "UNSUPPORTED_MARKETPLACE", "AUTH_REQUIRED", "RATE_LIMITED", "UNKNOWN_FAILURE",
})
FAILED_COLLECTION_STATUSES = COLLECTION_STATUSES - {"SUCCESS", "NO_RESULT"}
TRANSLATION_OUTCOMES = frozenset({
    "NO_COMPLETE_TRANSLATION_FOUND", "COMPLETE_TRANSLATION_EXISTS", "UNCERTAIN",
})


def validate_evidence_record(
    record: dict[str, Any], schema: dict[str, Any], *, schema_path: Path | None = None, root: Path | None = None
) -> None:
    """Validate the evidence envelope and fail closed on status/value contradictions."""
    validate(
        record,
        schema,
        schema_path=schema_path or Path("radar_evidence.schema.json"),
        root=root or Path.cwd(),
    )
    status = record["status"]
    value = record["normalized_value"]
    if status not in COLLECTION_STATUSES:
        raise ValidationError(f"evidence status is unsupported: {status}")
    if status in FAILED_COLLECTION_STATUSES and value.get("collection_result") in {"SUCCESS", "NO_RESULT"}:
        raise ValidationError("failed collection cannot carry a successful normalized result")
    if status == "NO_RESULT" and value.get("collection_result") == "SUCCESS":
        raise ValidationError("NO_RESULT cannot be normalized as SUCCESS")
    if status in FAILED_COLLECTION_STATUSES and not record.get("error_class"):
        raise ValidationError("failed collection requires error_class")


def resolve_local_raw_pointer(root: Path, pointer: str) -> Any:
    """Resolve a local `path.json#/json/pointer` reference; reject path escape."""
    path_text, marker, fragment = pointer.partition("#")
    if not marker or not path_text or not fragment.startswith("/"):
        raise ValidationError("raw evidence pointer must use path.json#/json/pointer form")
    path = (root / path_text).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValidationError("raw evidence pointer is outside the repository or missing")
    import json

    value: Any = json.loads(path.read_text(encoding="utf-8"))
    for part in fragment.lstrip("/").split("/"):
        token = part.replace("~1", "/").replace("~0", "~")
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value


def bibliographic_translation_outcome(searches: list[dict[str, Any]]) -> str:
    """Aggregate searched records without treating collector failure as absence."""
    if not searches:
        return "UNCERTAIN"
    if any(item.get("status") not in {"SUCCESS", "NO_RESULT"} for item in searches):
        return "UNCERTAIN"
    if any(item.get("complete_work_found") is True for item in searches):
        return "COMPLETE_TRANSLATION_EXISTS"
    if any(item.get("exhaustive") is not True for item in searches):
        return "UNCERTAIN"
    return "NO_COMPLETE_TRANSLATION_FOUND"


def is_organic_discovery(observation: dict[str, Any]) -> bool:
    """Sponsored, personalized, unknown-context, and failed rows are not organic discovery."""
    excluded_modules = {
        "PREVIOUSLY_VIEWED_MODULE", "SPONSORED", "RECOMMENDATION_MODULE",
    }
    return (
        observation.get("status") == "SUCCESS"
        and observation.get("placement_type") == "ORGANIC"
        and isinstance(observation.get("organic_position"), int)
        and not isinstance(observation.get("organic_position"), bool)
        and observation["organic_position"] > 0
        and observation.get("personalized_state") == "FALSE"
        and observation.get("module_type") not in excluded_modules
        and not excluded_modules.intersection(observation.get("personalized_modules", []))
    )
