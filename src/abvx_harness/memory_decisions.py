"""Owner-governed local overlay for correcting read-only retrieved memory."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .harness import ValidationError, load_json


def _directory(root: Path) -> Path:
    return root / "evidence" / "memory-decisions"


def record_memory_decision(
    root: Path,
    *,
    action: str,
    target_refs: list[dict[str, str]],
    privacy_domain: str,
    rationale: str,
    provenance: dict[str, Any],
    chosen_ref: dict[str, str] | None = None,
    decision_id: str | None = None,
    decided_at: str | None = None,
) -> dict[str, Any]:
    """Append an explicit local invalidation or conflict-resolution decision."""
    action = action.upper()
    if action not in {"INVALIDATE", "RESOLVE_CONFLICT"}:
        raise ValidationError("memory decision action must be INVALIDATE or RESOLVE_CONFLICT")
    if not privacy_domain.strip() or not rationale.strip() or not provenance:
        raise ValidationError("privacy domain, rationale, and provenance are required")
    if not target_refs or any(not _valid_ref(ref) for ref in target_refs):
        raise ValidationError("each target must include provider and id")
    unique_refs = {(ref["provider"], ref["id"]) for ref in target_refs}
    if len(unique_refs) != len(target_refs):
        raise ValidationError("duplicate target references are not allowed")
    if action == "INVALIDATE" and (len(target_refs) != 1 or chosen_ref is not None):
        raise ValidationError("invalidation requires exactly one target and no chosen_ref")
    if action == "RESOLVE_CONFLICT":
        if len(target_refs) < 2 or not _valid_ref(chosen_ref):
            raise ValidationError("conflict resolution requires multiple targets and one chosen_ref")
        if (chosen_ref["provider"], chosen_ref["id"]) not in unique_refs:
            raise ValidationError("chosen_ref must be one of the conflict targets")
    decision_id = decision_id or f"memory-decision-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}"
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,119}", decision_id):
        raise ValidationError("decision_id may contain only letters, numbers, dot, underscore, and hyphen")
    directory = _directory(root)
    path = directory / f"{decision_id}.json"
    if path.exists():
        raise ValidationError(f"memory decision already exists: {decision_id}")
    record = {
        "schema_version": "v1",
        "decision_id": decision_id,
        "action": action,
        "target_refs": sorted(target_refs, key=lambda ref: (ref["provider"], ref["id"])),
        "chosen_ref": chosen_ref,
        "privacy_domain": privacy_domain,
        "rationale": rationale.strip(),
        "provenance": provenance,
        "decided_at": decided_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "write_back": False,
    }
    directory.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return record


def apply_memory_decisions(
    root: Path, items: list[dict[str, Any]], *, privacy_domain: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Filter matching retrieved items using only decisions from same privacy domain."""
    suppressed: set[tuple[str, str]] = set()
    matched: list[dict[str, Any]] = []
    for path in sorted(_directory(root).glob("*.json")) if _directory(root).is_dir() else []:
        decision = load_json(path)
        if decision.get("schema_version") != "v1" or not decision.get("provenance"):
            raise ValidationError(f"invalid memory decision record: {path.name}")
        if decision.get("privacy_domain") != privacy_domain:
            continue
        refs = {(ref["provider"], ref["id"]) for ref in decision["target_refs"]}
        if decision["action"] == "INVALIDATE":
            suppressed.update(refs)
        elif decision["action"] == "RESOLVE_CONFLICT":
            chosen = decision["chosen_ref"]
            suppressed.update(refs - {(chosen["provider"], chosen["id"])})
        else:
            raise ValidationError(f"unsupported stored memory decision: {path.name}")
        if any((item.get("provider"), item.get("id")) in refs for item in items):
            matched.append(decision)
    return (
        [item for item in items if (item.get("provider"), item.get("id")) not in suppressed],
        matched,
    )


def _valid_ref(ref: Any) -> bool:
    return isinstance(ref, dict) and isinstance(ref.get("provider"), str) and bool(ref["provider"].strip()) and isinstance(ref.get("id"), str) and bool(ref["id"].strip())
