from __future__ import annotations

import json
import platform
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import __version__
from .providers import LocalCommandProvider


class ValidationError(ValueError):
    pass


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Any:
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"{path}: {exc}") from exc


def _pointer(root: dict[str, Any], pointer: str) -> Any:
    value: Any = root
    for part in pointer.lstrip("/").split("/"):
        value = value[part.replace("~1", "/").replace("~0", "~")]
    return value


def validate(instance: Any, schema: dict[str, Any], *, schema_path: Path, root: Path, location: str = "$", root_schema: dict[str, Any] | None = None) -> None:
    root_schema = root_schema or schema
    if "$ref" in schema:
        ref = schema["$ref"]
        ref_file, _, pointer = ref.partition("#")
        target_schema = root_schema
        target_path = schema_path
        if ref_file:
            target_path = (schema_path.parent / ref_file).resolve()
            target_schema = load_json(target_path)
        if pointer:
            target_schema = _pointer(target_schema, pointer)
        validate(instance, target_schema, schema_path=target_path, root=root, location=location, root_schema=target_schema)
        return
    if "const" in schema and instance != schema["const"]:
        raise ValidationError(f"{location}: expected {schema['const']!r}")
    if "enum" in schema and instance not in schema["enum"]:
        raise ValidationError(f"{location}: expected one of {schema['enum']!r}")
    expected = schema.get("type")
    if expected:
        types = expected if isinstance(expected, list) else [expected]
        type_ok = any(
            (kind == "null" and instance is None)
            or (kind == "object" and isinstance(instance, dict))
            or (kind == "array" and isinstance(instance, list))
            or (kind == "string" and isinstance(instance, str))
            or (kind == "integer" and isinstance(instance, int) and not isinstance(instance, bool))
            or (kind == "number" and isinstance(instance, (int, float)) and not isinstance(instance, bool))
            or (kind == "boolean" and isinstance(instance, bool))
            for kind in types
        )
        if not type_ok:
            raise ValidationError(f"{location}: expected {expected}, got {type(instance).__name__}")
    if isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0):
            raise ValidationError(f"{location}: shorter than minLength")
        if schema.get("format") == "date-time":
            datetime.fromisoformat(instance.replace("Z", "+00:00"))
    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if instance < schema.get("minimum", instance) or instance > schema.get("maximum", instance):
            raise ValidationError(f"{location}: outside numeric bounds")
    if isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0):
            raise ValidationError(f"{location}: fewer than minItems")
        if "items" in schema:
            for index, item in enumerate(instance):
                validate(item, schema["items"], schema_path=schema_path, root=root, location=f"{location}[{index}]", root_schema=root_schema)
    if isinstance(instance, dict):
        for required in schema.get("required", []):
            if required not in instance:
                raise ValidationError(f"{location}: missing required property {required!r}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            unknown = set(instance) - set(properties)
            if unknown:
                raise ValidationError(f"{location}: unexpected properties {sorted(unknown)!r}")
        for key, value in instance.items():
            if key in properties:
                validate(value, properties[key], schema_path=schema_path, root=root, location=f"{location}.{key}", root_schema=root_schema)


def validate_repository(root: Path) -> list[str]:
    schema_paths = sorted((root / "schemas").glob("*.schema.json"))
    for path in schema_paths:
        schema = load_json(path)
        if not isinstance(schema, dict) or "$schema" not in schema or "$id" not in schema:
            raise ValidationError(f"{path}: not a versioned schema document")
    registry_schema_path = root / "schemas" / "registry.schema.json"
    registry_schema = load_json(registry_schema_path)
    checked: list[str] = []
    for path in sorted((root / "registries").rglob("*.json")):
        validate(load_json(path), registry_schema, schema_path=registry_schema_path, root=root, location=str(path))
        checked.append(str(path.relative_to(root)))
    portfolio_schemas = {
        "strategy.json": root / "schemas" / "project_strategy.schema.json",
        "state.json": root / "schemas" / "portfolio_state.schema.json",
        "human-queue.json": root / "schemas" / "human_queue.schema.json",
        "lessons.json": root / "schemas" / "platform_lesson.schema.json",
        "considerations.json": root / "schemas" / "portfolio_consideration.schema.json",
    }
    for path in sorted((root / "portfolio").glob("*.json")):
        schema_path = portfolio_schemas.get(path.name)
        if schema_path is None:
            raise ValidationError(f"{path}: unknown portfolio document")
        validate(load_json(path), load_json(schema_path), schema_path=schema_path, root=root, location=str(path))
        checked.append(str(path.relative_to(root)))
    collection_schemas = {
        root / "content" / "opportunities.json": root / "schemas" / "content_opportunity.schema.json",
        root / "references" / "items.json": root / "schemas" / "reference_collection.schema.json",
    }
    for path, schema_path in collection_schemas.items():
        if path.is_file():
            validate(load_json(path), load_json(schema_path), schema_path=schema_path, root=root, location=str(path))
            checked.append(str(path.relative_to(root)))
    intake_schema_path = root / "schemas" / "intake_item.schema.json"
    for path in sorted((root / "intake" / "items").glob("*.json")):
        validate(load_json(path), load_json(intake_schema_path), schema_path=intake_schema_path, root=root, location=str(path))
        checked.append(str(path.relative_to(root)))
    for path in sorted((root / "fixtures").rglob("*.json")):
        fixture_schema_path = root / "schemas" / "fixture.schema.json"
        value = load_json(path)
        if path.name == "manifest.json":
            if not isinstance(value, dict) or value.get("schema_version") != "v1":
                raise ValidationError(f"{path}: invalid fixture manifest")
        elif path.name == "mission.json":
            mission_schema_path = root / "schemas" / "mission_fixture.schema.json"
            validate(value, load_json(mission_schema_path), schema_path=mission_schema_path, root=root, location=str(path))
        else:
            validate(value, load_json(fixture_schema_path), schema_path=fixture_schema_path, root=root, location=str(path))
        checked.append(str(path.relative_to(root)))
    evidence_schema_path = root / "schemas" / "evidence_record.schema.json"
    result_schema_path = root / "schemas" / "bakeoff_result.schema.json"
    decision_schema_path = root / "schemas" / "bakeoff_decision.schema.json"
    recovery_schema_path = root / "schemas" / "mission_state_recovery.schema.json"
    export_schema_path = root / "schemas" / "mission_state_export.schema.json"
    for path in sorted((root / "evidence").rglob("*.json")):
        if path.name.endswith(".evidence.json"):
            validate(load_json(path), load_json(evidence_schema_path), schema_path=evidence_schema_path, root=root, location=str(path))
        elif path.name == "result.json":
            validate(load_json(path), load_json(result_schema_path), schema_path=result_schema_path, root=root, location=str(path))
        elif path.name == "decision.json":
            validate(load_json(path), load_json(decision_schema_path), schema_path=decision_schema_path, root=root, location=str(path))
        elif path.name.endswith("-succeeded.json") or path.name.endswith("-failed.json"):
            validate(load_json(path), load_json(recovery_schema_path), schema_path=recovery_schema_path, root=root, location=str(path))
        elif path.name == "state-export.json":
            validate(load_json(path), load_json(export_schema_path), schema_path=export_schema_path, root=root, location=str(path))
        else:
            continue
        checked.append(str(path.relative_to(root)))
    playbook_schema_path = root / "schemas" / "playbook.schema.json"
    replay_schema_path = root / "schemas" / "playbook_replay.schema.json"
    event_schema_path = root / "schemas" / "project_event.schema.json"
    for path in sorted((root / "playbooks").glob("*.json")):
        validate(load_json(path), load_json(playbook_schema_path), schema_path=playbook_schema_path, root=root, location=str(path))
        checked.append(str(path.relative_to(root)))
    for path in sorted((root / "playbooks" / "replays").glob("*.json")):
        validate(load_json(path), load_json(replay_schema_path), schema_path=replay_schema_path, root=root, location=str(path))
        checked.append(str(path.relative_to(root)))
    for path in sorted((root / "events" / "projects").rglob("*.json")):
        validate(load_json(path), load_json(event_schema_path), schema_path=event_schema_path, root=root, location=str(path))
        checked.append(str(path.relative_to(root)))
    context_request_schema_path = root / "schemas" / "context_request.schema.json"
    if context_request_schema_path.is_file():
        for path in sorted((root / "context" / "requests").glob("*.json")):
            validate(load_json(path), load_json(context_request_schema_path), schema_path=context_request_schema_path, root=root, location=str(path))
            checked.append(str(path.relative_to(root)))
    context_pack_schema_path = root / "schemas" / "context_pack.schema.json"
    if context_pack_schema_path.is_file():
        for path in sorted((root / "evidence" / "context-packs").glob("*.json")):
            validate(load_json(path), load_json(context_pack_schema_path), schema_path=context_pack_schema_path, root=root, location=str(path))
            checked.append(str(path.relative_to(root)))
    return checked


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_bakeoff(root: Path, bakeoff_id: str, evidence_root: Path | None = None) -> Path:
    bakeoff_dir = root / "fixtures" / "bakeoffs" / bakeoff_id
    manifest = load_json(bakeoff_dir / "manifest.json")
    if manifest.get("id") != bakeoff_id:
        raise ValidationError(f"manifest id does not match {bakeoff_id}")
    evidence_root = evidence_root or (root / "evidence")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run_dir = evidence_root / "bakeoffs" / bakeoff_id / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    provider = LocalCommandProvider()
    evidence_refs: list[str] = []
    results: list[str] = []
    run_started_at = now_iso()
    for fixture_id in manifest["fixture_ids"]:
        fixture = load_json(bakeoff_dir / f"{fixture_id}.json")
        started_at = now_iso()
        prepared = provider.prepare({"root": str(root), "run_dir": str(run_dir), "timeout_seconds": manifest["budget"]["timeout_seconds"]})
        try:
            attempts = manifest["budget"]["max_retries"] + 1
            result = None
            for _ in range(attempts):
                result = provider.collect(prepared, provider.run(prepared, fixture))
                if result.timed_out or result.exit_status == fixture["expected_exit_status"]:
                    break
            assert result is not None
        finally:
            provider.cleanup(prepared)
        stdout_path = run_dir / f"{fixture_id}.stdout"
        stderr_path = run_dir / f"{fixture_id}.stderr"
        stdout_path.write_bytes(result.stdout)
        stderr_path.write_bytes(result.stderr)
        outcome = "TIMEOUT" if result.timed_out else ("PASS" if result.exit_status == fixture["expected_exit_status"] else "FAIL")
        results.append(outcome)
        artifact_refs: list[str] = []
        for relative_artifact in fixture.get("artifact_paths", []):
            artifact_path = (root / relative_artifact).resolve()
            if root.resolve() not in artifact_path.parents:
                raise ValidationError(f"{fixture_id}: artifact path escapes repository: {relative_artifact}")
            if artifact_path.is_file():
                destination = run_dir / "artifacts" / relative_artifact
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(artifact_path, destination)
                artifact_refs.append(str(destination.relative_to(evidence_root)))
        evidence = {
            "id": f"{bakeoff_id}-{run_id}-{fixture_id}", "source": "local-command-provider", "timestamp": started_at,
            "candidate": fixture.get("candidate", manifest["candidate"]), "fixture": fixture_id, "result": outcome,
            "metrics": {"duration_ms": result.duration_ms, "exit_status": result.exit_status, "timeout_seconds": manifest["budget"]["timeout_seconds"], "max_retries": manifest["budget"]["max_retries"]},
            "stdout_ref": str(stdout_path.relative_to(evidence_root)), "stderr_ref": str(stderr_path.relative_to(evidence_root)), "artifact_refs": artifact_refs,
            "provenance": {"recorded_by": "abvx-harness", "source_uri": None, "observed_at": started_at},
            "environment": {"python": platform.python_version(), "platform": platform.platform(), "harness_version": __version__},
        }
        validate(evidence, load_json(root / "schemas" / "evidence_record.schema.json"), schema_path=root / "schemas" / "evidence_record.schema.json", root=root, location="evidence")
        evidence_path = run_dir / f"{fixture_id}.evidence.json"
        _write_json(evidence_path, evidence)
        evidence_refs.append(str(evidence_path.relative_to(evidence_root)))
    final = "PASS" if all(item == "PASS" for item in results) else ("FAIL" if "FAIL" in results or "TIMEOUT" in results else "INCONCLUSIVE")
    result_doc = {"bakeoff_id": bakeoff_id, "candidate": manifest["candidate"], "result": final, "recommendation": "Retain the bounded fixture/evidence pattern; do not adopt a provider automatically.", "evidence_refs": evidence_refs, "retained_patterns": ["fixture-owned argv", "explicit budget", "stdout/stderr references", "environment provenance"], "risks": ["local command availability may differ by machine"], "unresolved_questions": ["Which provider should fill the next experimental role?"], "decision_state": "STOP_FOR_HUMAN_DECISION"}
    validate(result_doc, load_json(root / "schemas" / "bakeoff_result.schema.json"), schema_path=root / "schemas" / "bakeoff_result.schema.json", root=root, location="result")
    _write_json(run_dir / "result.json", result_doc)
    _write_json(run_dir / "manifest.json", {"run_id": run_id, "bakeoff_id": bakeoff_id, "candidate": manifest["candidate"], "fixtures": manifest["fixture_ids"], "result": final, "evidence_refs": evidence_refs, "budget": manifest["budget"], "started_at": run_started_at, "completed_at": now_iso()})
    return run_dir
