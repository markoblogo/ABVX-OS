from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .harness import ValidationError, load_json, now_iso, validate


def _schema_path(root: Path, name: str) -> Path:
    return root / "schemas" / name


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_playbook(root: Path, playbook_id: str) -> dict[str, Any]:
    path = root / "playbooks" / f"{playbook_id}.json"
    if not path.is_file():
        raise ValidationError(f"unknown playbook: {playbook_id}")
    value = load_json(path)
    validate(value, load_json(_schema_path(root, "playbook.schema.json")), schema_path=_schema_path(root, "playbook.schema.json"), root=root, location=str(path))
    return value


def load_replay(root: Path, path: Path) -> dict[str, Any]:
    value = load_json(path)
    validate(value, load_json(_schema_path(root, "playbook_replay.schema.json")), schema_path=_schema_path(root, "playbook_replay.schema.json"), root=root, location=str(path))
    return value


def required_input_names(playbook: dict[str, Any]) -> list[str]:
    return [entry["name"] for entry in playbook["required_inputs"] if entry["required"]]


def validate_required_inputs(playbook: dict[str, Any], replay: dict[str, Any]) -> None:
    observed = replay["observed_inputs"]
    missing = [name for name in required_input_names(playbook) if name not in observed]
    if missing:
        raise ValidationError(f"{playbook['id']}: missing required inputs {missing}")


def select_validation_tier(playbook: dict[str, Any], flags: dict[str, Any]) -> str:
    for trigger in playbook["validation"]["escalate_to_critical_on"]:
        if flags.get(trigger):
            return "CRITICAL"
    for trigger in playbook["validation"]["escalate_to_full_on"]:
        if flags.get(trigger):
            return "FULL"
    return playbook["validation"]["default_tier"]


def _ensure_replay_scope(playbook: dict[str, Any], replay: dict[str, Any]) -> None:
    if not replay.get("dry_run"):
        raise ValidationError(f"{playbook['id']}: replay only supports dry_run=true")
    if replay["project"] != playbook["project"]:
        raise ValidationError(f"{playbook['id']}: replay project mismatch")
    if replay.get("scope", {}).get("portfolio_mutation_requested"):
        raise ValidationError(f"{playbook['id']}: portfolio mutation is prohibited for routine events")
    if replay.get("scope", {}).get("production_mutation_requested"):
        raise ValidationError(f"{playbook['id']}: production mutation is prohibited during replay")


def _event_id(kind: str, replay: dict[str, Any]) -> str:
    return f"{replay['project']}-{kind.lower()}-{replay['object']['id']}-{replay['replay_id'].lower()}"


def _evidence_path(output_root: Path, playbook_id: str, replay_id: str) -> Path:
    return output_root / "evidence" / "playbooks" / "platform-cost-001" / f"{playbook_id}.{replay_id}.replay.evidence.json"


def _event_path(output_root: Path, project: str, event_type: str, object_id: str) -> Path:
    return output_root / "events" / "projects" / project / f"{event_type.lower()}-{object_id}.json"


def _publish_replay(root: Path, playbook: dict[str, Any], replay: dict[str, Any], *, output_root: Path) -> dict[str, Any]:
    evidence_path = Path(replay["source_refs"]["outcome_evidence"])
    event_candidate_path = Path(replay["source_refs"]["media_event_candidate"])
    registry_path = Path(replay["source_refs"]["project_registry"])
    outcome = load_json(root / evidence_path)
    event_candidate = load_json(root / event_candidate_path)
    registry = load_json(root / registry_path)
    if outcome["fixture"] != replay["replay_id"]:
        raise ValidationError("publish replay fixture mismatch")
    if outcome["metrics"]["guide_slug"] != replay["object"]["id"]:
        raise ValidationError("publish replay guide mismatch")
    if registry["entries"][0]["id"] != replay["project"]:
        raise ValidationError("publish replay project registry mismatch")
    if event_candidate["url_path"].endswith(replay["object"]["id"]) is False:
        raise ValidationError("publish replay media event mismatch")
    return {
        "result": "CONDITIONAL_PASS",
        "operation_timestamp": outcome["timestamp"],
        "artifact_refs": [
            str(evidence_path),
            str(event_candidate_path),
            "references/items.json"
        ],
        "summary": {
            "languages": outcome["metrics"]["publication_languages"],
            "cover_integrated": outcome["metrics"]["cover_integrated"],
            "media_event_candidate": str(event_candidate_path)
        },
        "skipped_checks": [
            "broad web research",
            "full repository build",
            "full repository tests",
            "portfolio reasoning"
        ]
    }


def _image_replay(root: Path, playbook: dict[str, Any], replay: dict[str, Any], *, output_root: Path) -> dict[str, Any]:
    evidence_path = Path(replay["source_refs"]["outcome_evidence"])
    registry_path = Path(replay["source_refs"]["project_registry"])
    outcome = load_json(root / evidence_path)
    registry = load_json(root / registry_path)
    if registry["entries"][0]["id"] != replay["project"]:
        raise ValidationError("image replay project registry mismatch")
    expected = replay["observed_inputs"]["current_report_only_expectation"]
    previous = replay["observed_inputs"]["previous_run"]
    if previous["matched"] != 5 or previous["unmatched"] != 0:
        raise ValidationError("image replay previous run summary mismatch")
    return {
        "result": "PASS",
        "operation_timestamp": outcome["timestamp"],
        "artifact_refs": [
            str(evidence_path),
            "docs/audits/azurmenton-005-second-pass-image-todo.md"
        ],
        "summary": {
            "published_guide": replay["observed_inputs"]["published_guide"],
            "prepared_images_count": replay["observed_inputs"]["prepared_images_count"],
            "report_only_expectation": expected
        },
        "skipped_checks": [
            "guide body checks",
            "broad portfolio analysis",
            "full repository build",
            "external repo mutation"
        ]
    }


def replay_playbook(root: Path, playbook_id: str, replay_path: Path, *, output_root: Path | None = None) -> dict[str, Any]:
    started = time.perf_counter()
    output_root = output_root or root
    playbook = load_playbook(root, playbook_id)
    replay = load_replay(root, replay_path)
    if replay["playbook_id"] != playbook_id:
        raise ValidationError(f"replay targets {replay['playbook_id']}, expected {playbook_id}")
    validate_required_inputs(playbook, replay)
    _ensure_replay_scope(playbook, replay)
    tier = select_validation_tier(playbook, replay["exception_flags"])
    if playbook_id == "azurmenton.publish-guide":
        operation = _publish_replay(root, playbook, replay, output_root=output_root)
    elif playbook_id == "azurmenton.attach-guide-images":
        operation = _image_replay(root, playbook, replay, output_root=output_root)
    else:
        raise ValidationError(f"no replay handler for {playbook_id}")
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    evidence_doc = {
        "id": f"{playbook_id}-{replay['replay_id']}-replay",
        "source": f"{playbook_id} replay",
        "timestamp": now_iso(),
        "candidate": playbook_id,
        "fixture": replay["replay_id"],
        "result": operation["result"],
        "metrics": {
            "execution_mode": "PLAYBOOK",
            "validation_tier": tier,
            "elapsed_ms": elapsed_ms,
            "reasoning_steps": 1,
            "approx_agent_model_usage": "not_metered_locally",
            "dry_run": True,
            "checks_run": playbook["validation"]["checks"][tier],
            "skipped_checks": operation["skipped_checks"]
        },
        "stdout_ref": "internal:none",
        "stderr_ref": "internal:none",
        "artifact_refs": operation["artifact_refs"],
        "provenance": {
            "recorded_by": "PLATFORM-COST-001",
            "source_uri": None,
            "observed_at": operation["operation_timestamp"]
        },
        "environment": {
            "repository_path": str(root),
            "production_mutation": False,
            "portfolio_mutation": False,
            "replay_mode": "DRY_RUN"
        }
    }
    validate(evidence_doc, load_json(_schema_path(root, "evidence_record.schema.json")), schema_path=_schema_path(root, "evidence_record.schema.json"), root=root, location="playbook_replay_evidence")
    evidence_path = _evidence_path(output_root, playbook_id, replay["replay_id"])
    _write_json(evidence_path, evidence_doc)
    event_doc = {
        "schema_version": "v1",
        "id": _event_id(playbook["evidence"]["event_type"], replay),
        "type": playbook["evidence"]["event_type"],
        "project": replay["project"],
        "object": {
          "kind": replay["object"]["kind"],
          "id": replay["object"]["id"],
          "locator": f"{replay['object']['kind']}:{replay['object']['id']}"
        },
        "timestamp": operation["operation_timestamp"],
        "origin": "PLAYBOOK_REPLAY",
        "result": operation["result"],
        "execution_mode": "PLAYBOOK",
        "validation_tier": tier,
        "portfolio_effect": "NONE",
        "artifact_refs": operation["artifact_refs"],
        "evidence_ref": str(evidence_path.relative_to(output_root)),
        "media_event_candidate": playbook["evidence"]["media_event_candidate"],
        "provenance": {
            "recorded_by": "PLATFORM-COST-001",
            "source_uri": None,
            "observed_at": now_iso()
        }
    }
    validate(event_doc, load_json(_schema_path(root, "project_event.schema.json")), schema_path=_schema_path(root, "project_event.schema.json"), root=root, location="playbook_replay_event")
    event_path = _event_path(output_root, replay["project"], playbook["evidence"]["event_type"], replay["object"]["id"])
    _write_json(event_path, event_doc)
    return {
        "status": "PASS",
        "playbook_id": playbook_id,
        "replay_id": replay["replay_id"],
        "validation_tier": tier,
        "event_path": str(event_path.relative_to(output_root)),
        "evidence_path": str(evidence_path.relative_to(output_root)),
        "result": operation["result"],
        "summary": operation["summary"]
    }
