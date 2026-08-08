from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .harness import ValidationError, load_json


INTAKE_TYPES = {
    "IDEA", "CONTENT_SOURCE", "CONTENT_OPPORTUNITY", "EXTERNAL_PROJECT", "EXTERNAL_OSS",
    "PROJECT_WORK", "OPPORTUNITY", "RESEARCH_SOURCE", "REFERENCE", "UNKNOWN",
}
ROUTES = {
    "PORTFOLIO", "PROJECT", "MEDIA_RESOURCE", "OPPORTUNITY_ENGINE", "EXTERNAL_CANDIDATE_REGISTRY",
    "CORTEX_KNOWLEDGE", "RESEARCH", "HYPOTHESIS_REGISTRY", "IGNORE_ARCHIVE",
}
CLARIFICATION_QUESTION = "What should this be related to or used for?"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _items_dir(root: Path) -> Path:
    return root / "intake" / "items"


def _write_item(root: Path, item: dict[str, Any]) -> None:
    directory = _items_dir(root)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{item['id']}.json"
    path.write_text(json.dumps(item, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _entity(kind: str, entity_id: str, confidence: str) -> dict[str, str]:
    return {"kind": kind, "id": entity_id, "confidence": confidence}


def _classification(value: str, secondary: list[str], confidence: float, entities: list[dict[str, str]], routes: list[str], actions: list[str], clarification: bool = False) -> dict[str, Any]:
    if value not in INTAKE_TYPES or any(item not in INTAKE_TYPES for item in secondary):
        raise ValidationError(f"unsupported intake type: {value}")
    if any(route not in ROUTES for route in routes):
        raise ValidationError("unsupported intake route")
    return {
        "primary_type": value,
        "secondary_types": secondary,
        "confidence": confidence,
        "related_entities": entities,
        "possible_routes": routes,
        "suggested_actions": actions,
        "needs_clarification": clarification,
    }


def _infer(value: str, input_type: str, context: str | None, explicit_type: str | None) -> dict[str, Any]:
    text = f"{value} {context or ''}".lower()
    if explicit_type:
        if explicit_type not in INTAKE_TYPES:
            raise ValidationError(f"unsupported intake type: {explicit_type}")
        return _classification(explicit_type, [], 0.7, [], ["PROJECT"], ["Review the item and choose an approved destination"])
    if "the-headlands" in text or "headlands" in text:
        return _classification("CONTENT_OPPORTUNITY", [], 0.95, [_entity("PROJECT", "ssi", "HIGH"), _entity("PROJECT", "1d3x", "MEDIUM")], ["MEDIA_RESOURCE", "PROJECT"], ["Prepare a short SSI/context post proposal; do not publish"])
    if "cig-index" in text or "cigarette index" in text:
        return _classification("EXTERNAL_PROJECT", ["REFERENCE"], 0.95, [_entity("PROJECT", "pop", "HIGH"), _entity("PROJECT", "1d3x", "HIGH")], ["EXTERNAL_CANDIDATE_REGISTRY", "PROJECT"], ["Record as a candidate Alternative Index Library entry; do not integrate"])
    if "hyperresearch" in text:
        return _classification("EXTERNAL_OSS", ["RESEARCH_SOURCE"], 0.98, [_entity("CANDIDATE", "hyperresearch", "HIGH")], ["EXTERNAL_CANDIDATE_REGISTRY", "RESEARCH"], ["Retain deep-research provider pattern; defer pilot"])
    if "pop" in text and any(word in text for word in ("finish", "database", "ingestion", "embed", "announce", "book", "indices")):
        return _classification("PROJECT_WORK", ["CONTENT_OPPORTUNITY", "OPPORTUNITY", "REFERENCE"], 0.92, [_entity("PROJECT", "pop", "HIGH"), _entity("PROJECT", "1d3x", "HIGH")], ["PROJECT", "MEDIA_RESOURCE", "OPPORTUNITY_ENGINE", "PORTFOLIO", "CORTEX_KNOWLEDGE"], ["Preserve as a multi-route POP development idea; do not create a roadmap"])
    return _classification("UNKNOWN", [], 0.2, [], [], [], True)


def add_intake_item(root: Path, *, text: str | None = None, url: str | None = None, context: str | None = None, title: str | None = None, summary: str | None = None, explicit_type: str | None = None, item_id: str | None = None, captured_at: str | None = None) -> dict[str, Any]:
    if (text is None) == (url is None):
        raise ValidationError("provide exactly one of text or url")
    value = text or url
    assert value is not None
    input_type = "TEXT" if text is not None else "URL"
    captured = captured_at or _now()
    inferred = _infer(value, input_type, context, explicit_type)
    item = {
        "schema_version": "v1",
        "id": item_id or f"intake-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}",
        "created_at": captured,
        "source": {"kind": "MANUAL" if input_type == "TEXT" else "URL", "label": "owner"},
        "input_type": input_type,
        "raw_input": {"value": value, "reference": value if input_type == "URL" else None},
        "title": title,
        "summary": summary or context,
        "classification": {"primary_type": inferred["primary_type"], "secondary_types": inferred["secondary_types"], "confidence": inferred["confidence"]},
        "related_entities": inferred["related_entities"],
        "possible_routes": inferred["possible_routes"],
        "suggested_actions": inferred["suggested_actions"],
        "clarification": {"required": inferred["needs_clarification"], "question": CLARIFICATION_QUESTION if inferred["needs_clarification"] else None, "answer": None, "answered_at": None},
        "related_item_ids": [],
        "status": "NEEDS_CLARIFICATION" if inferred["needs_clarification"] else "PROPOSED",
        "provenance": {"recorded_by": "abvx-intake", "captured_at": captured, "source_uri": value if input_type == "URL" else None},
    }
    _write_item(root, item)
    return item


def inspect_intake_item(root: Path, item_id: str) -> dict[str, Any]:
    path = _items_dir(root) / f"{item_id}.json"
    if not path.is_file():
        raise ValidationError(f"intake item not found: {item_id}")
    return load_json(path)


def list_intake_items(root: Path) -> list[dict[str, Any]]:
    return sorted((load_json(path) for path in _items_dir(root).glob("*.json")), key=lambda item: (item["created_at"], item["id"]))


def update_clarification(root: Path, item_id: str, answer: str) -> dict[str, Any]:
    if not answer.strip():
        raise ValidationError("clarification answer cannot be empty")
    item = inspect_intake_item(root, item_id)
    if not item["clarification"]["required"]:
        raise ValidationError(f"intake item does not require clarification: {item_id}")
    item["clarification"].update({"required": False, "answer": answer, "answered_at": _now()})
    item["status"] = "PROPOSED"
    _write_item(root, item)
    return item


def link_intake_items(root: Path, item_id: str, related_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    if item_id == related_id:
        raise ValidationError("an intake item cannot link to itself")
    item = inspect_intake_item(root, item_id)
    related = inspect_intake_item(root, related_id)
    if related_id not in item["related_item_ids"]:
        item["related_item_ids"].append(related_id)
        item["related_item_ids"].sort()
    if item_id not in related["related_item_ids"]:
        related["related_item_ids"].append(item_id)
        related["related_item_ids"].sort()
    _write_item(root, item)
    _write_item(root, related)
    return item, related
