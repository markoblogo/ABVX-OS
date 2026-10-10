"""Bounded, read-only universal book contracts (Phase 1).

This module deliberately does not render books, migrate history, or infer
applicability.  Adapters provide legacy/current validators and status views.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from ..harness import ValidationError
from ..schema_validation import validate_draft_2020_12

SCHEMA_VERSION = "abvx-book-state/v1"
LOCK_KINDS = frozenset({"SOURCE_LOCK", "CANON_LOCK", "TRANSLATION_LOCK", "TEXT_LOCK",
                        "ILLUSTRATION_LOCK", "RENDER_INPUT_LOCK", "PRODUCTION_BUILD_LOCK"})
EVIDENCE_REQUIRED_EVENTS = frozenset({"OWNER_DECISION", "LOCK_CREATED", "VALIDATION_PASS", "BUILD_CREATED",
                                      "ASSET_APPROVED", "RETAILER_PREVIEW_PASS", "SUBMITTED", "LIVE_OBSERVED"})
RESULT_STATES = frozenset({"PASS", "FAIL", "UNKNOWN", "NOT_APPLICABLE", "OWNER_ACCEPTED_EXCEPTION"})
REF_SCOPES = frozenset({"PROJECT", "APPROVED_EXTERNAL_READONLY"})
PROFILES = {
    "SERIES_FICTION": {"ORIGINAL_FICTION", "SERIES_FICTION"},
    "CONVENTIONAL_TRANSLATION": {"CONVENTIONAL_TRANSLATION"},
}
PHASE1_MODULES = frozenset({"ORIGINAL_FICTION", "SERIES_FICTION", "CONVENTIONAL_TRANSLATION", "PICTIQ"})
METRIC_FIELDS = (
    "stage_id", "measurement_basis", "started_at", "completed_at", "evidence_refs", "builds", "retailer_warnings", "submission_attempts",
    "stage_started_at", "stage_completed_at", "owner_requested_at", "owner_approved_at",
    "calendar_seconds", "owner_wait_seconds", "owner_minutes", "owner_interventions",
    "agent_runs", "revision_count", "generation_attempts", "qa_runs", "qa_failures",
    "escaped_defects", "api_calls", "input_tokens", "output_tokens", "estimated_cost",
    "actual_cost", "currency",
)
HASH_RE = re.compile(r"^[a-f0-9]{64}$")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
HEX_SHA256 = HASH_RE


def canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                          allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"value is not canonical JSON: {exc}") from exc


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _timestamp(value: Any, label: str) -> None:
    if not isinstance(value, str):
        raise ValidationError(f"{label} must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError(f"{label} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValidationError(f"{label} must include a timezone")


def validate_ref(ref: Any, project_root: Path | None = None) -> None:
    if not isinstance(ref, dict) or not isinstance(ref.get("path"), str) or not ref["path"].strip():
        raise ValidationError("reference requires a non-empty path")
    if not isinstance(ref.get("sha256"), str) or not HASH_RE.fullmatch(ref["sha256"]):
        raise ValidationError(f"reference has invalid SHA-256: {ref.get('path')}")
    scope = ref.get("scope", "PROJECT")
    if scope not in REF_SCOPES:
        raise ValidationError(f"reference has invalid scope: {scope}")
    if scope == "APPROVED_EXTERNAL_READONLY":
        return
    if project_root is None:
        return
    root = project_root.resolve()
    path = (root / ref["path"]).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValidationError(f"PROJECT reference escapes project root: {ref['path']}") from exc
    if not path.is_file() or sha256_file(path) != ref["sha256"]:
        raise ValidationError(f"PROJECT reference missing or hash mismatch: {ref['path']}")


def validate_identity(identity: Any, project_root: Path | None = None) -> None:
    required = {"book_id", "book_type", "title", "source_type", "source_refs", "languages",
                "rights_status", "target_formats", "target_retailers", "created_at"}
    missing = required - set(identity) if isinstance(identity, dict) else required
    if missing:
        raise ValidationError(f"identity missing required fields: {sorted(missing)}")
    if not isinstance(identity["book_id"], str) or not ID_RE.fullmatch(identity["book_id"]):
        raise ValidationError("identity.book_id is invalid")
    for key in ("book_type", "title"):
        if not isinstance(identity[key], str) or not identity[key].strip():
            raise ValidationError(f"identity.{key} must be a non-empty string (use UNKNOWN explicitly)")
    if not isinstance(identity["source_type"], str) or not identity["source_type"]:
        raise ValidationError("identity.source_type is required")
    if not isinstance(identity["source_refs"], list):
        raise ValidationError("identity.source_refs must be an array")
    for ref in identity["source_refs"]:
        validate_ref(ref, project_root)
    languages = identity["languages"]
    if not isinstance(languages, dict) or not isinstance(languages.get("target"), str) or not languages["target"]:
        raise ValidationError("identity.languages.target is required")
    if languages.get("source") is not None and not isinstance(languages["source"], str):
        raise ValidationError("identity.languages.source must be a string or null")
    series = identity.get("series")
    if series is not None and (not isinstance(series, dict) or not isinstance(series.get("series_id"), str)
                               or not series["series_id"]):
        raise ValidationError("identity.series must be null or contain series_id")
    if series and series.get("position") is not None and (not isinstance(series["position"], int) or series["position"] < 1):
        raise ValidationError("identity.series.position must be a positive integer or null")
    if identity.get("rights_status") not in {"UNKNOWN", "REVIEW_REQUIRED", "OWNER_ATTESTED", "EVIDENCED", "NOT_CLEARED"}:
        raise ValidationError("identity.rights_status is invalid")
    for key in ("target_formats", "target_retailers"):
        value = identity[key]
        if not isinstance(value, list) or any(not isinstance(x, str) or not x for x in value) or len(set(value)) != len(value):
            raise ValidationError(f"identity.{key} must contain unique non-empty strings")
    _timestamp(identity["created_at"], "identity.created_at")


def validate_modules(book_type: str, modules: Sequence[str]) -> None:
    if book_type not in PROFILES:
        raise ValidationError(f"unsupported Phase 1 book_type: {book_type}")
    if len(set(modules)) != len(modules):
        raise ValidationError("module list contains duplicates")
    unknown = set(modules) - PHASE1_MODULES
    if unknown:
        raise ValidationError(f"module not activated in Phase 1: {sorted(unknown)}")
    required = PROFILES[book_type]
    if not required.issubset(set(modules)):
        raise ValidationError(f"{book_type} requires modules: {sorted(required)}")
    if book_type == "CONVENTIONAL_TRANSLATION" and ({"ORIGINAL_FICTION", "SERIES_FICTION"} & set(modules)):
        raise ValidationError("translation profile cannot activate fiction-only modules")


def validate_result(result: Any, project_root: Path | None = None) -> None:
    if not isinstance(result, dict) or result.get("state") not in RESULT_STATES:
        raise ValidationError("validator result has invalid state")
    state = result["state"]
    evidence = result.get("evidence_refs", [])
    inputs = result.get("input_refs", [])
    if not isinstance(evidence, list) or not isinstance(inputs, list):
        raise ValidationError("validator result refs must be arrays")
    outputs = result.get("output_refs", [])
    if not isinstance(outputs, list):
        raise ValidationError("validator result output_refs must be an array")
    for ref in (*evidence, *inputs, *outputs):
        validate_ref(ref, project_root)
    if state == "PASS" and (not evidence or not inputs):
        raise ValidationError("PASS requires input and evidence refs")
    if state in {"UNKNOWN", "NOT_APPLICABLE"} and not (isinstance(result.get("reason"), str) and result["reason"].strip()):
        raise ValidationError(f"{state} requires a reason")
    if "observed_at" in result:
        _timestamp(result["observed_at"], "validator result observed_at")
    if state == "NOT_APPLICABLE" and result.get("evidence_refs"):
        # Evidence may explain an N/A decision, but it cannot turn N/A into PASS.
        pass
    if state == "OWNER_ACCEPTED_EXCEPTION":
        exc = result.get("exception")
        if not isinstance(exc, dict) or not all(isinstance(exc.get(k), str) and exc[k].strip()
                                                for k in ("scope", "accepted_risk")):
            raise ValidationError("OWNER_ACCEPTED_EXCEPTION requires scope and accepted risk")
        validate_ref(exc.get("owner_decision_ref"), project_root)
        if exc["owner_decision_ref"].get("scope", "PROJECT") != "PROJECT":
            raise ValidationError("owner decision proof must be a trusted PROJECT reference")


def make_validator_result(check_id: str, state: str, *, input_refs: Sequence[dict[str, Any]] = (),
                          evidence_refs: Sequence[dict[str, Any]] = (), output_refs: Sequence[dict[str, Any]] = (),
                          reason: str | None = None, exception: dict[str, Any] | None = None,
                          observed: Any = None, expected: Any = None, observed_at: str | None = None) -> dict[str, Any]:
    from datetime import timezone
    if state not in RESULT_STATES:
        raise ValidationError(f"invalid validator result state: {state}")
    result = {"check_id": check_id, "validator_version": "book-core/v1", "state": state,
              "input_refs": list(input_refs), "output_refs": list(output_refs), "evidence_refs": list(evidence_refs),
              "observed": observed, "expected": expected,
              "observed_at": observed_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}
    if reason is not None:
        result["reason"] = reason
    if exception is not None:
        result["exception"] = exception
    validate_result(result)
    return result


def make_legacy_validator_result(check_id: str, state: str, *, evidence_path: str | None,
                                 input_sha256: list[str] | None = None,
                                 output_sha256: list[str] | None = None, observed: Any = None,
                                 expected: Any = None, tool_version: str | None = None,
                                 exception_owner: str | None = None, exception_reason: str | None = None,
                                 evidence_available: bool = False, timestamp: str,
                                 default_tool_version: str) -> dict[str, Any]:
    """Compatibility serialization for the existing GD3 validator-result schema."""
    inputs, outputs = input_sha256 or [], output_sha256 or []
    if state not in RESULT_STATES:
        state = "FAIL"
    valid_digests = all(isinstance(value, str) and HASH_RE.fullmatch(value) for value in inputs + outputs)
    if state == "PASS" and (not evidence_path or not evidence_available or not inputs or not valid_digests):
        state = "UNKNOWN"
    return {"check_id": check_id, "state": state, "input_sha256": inputs, "output_sha256": outputs,
            "observed": observed, "expected": expected, "evidence_path": evidence_path,
            "timestamp": timestamp, "tool_version": tool_version or default_tool_version,
            "exception_owner": exception_owner, "exception_reason": exception_reason}


def validate_locks(locks: Any, *, project_root: Path | None,
                   applicability: Mapping[str, str]) -> dict[str, str]:
    if not isinstance(locks, list):
        raise ValidationError("locks must be an array")
    ids: dict[str, dict[str, Any]] = {}
    latest_by_kind: dict[str, dict[str, Any]] = {}
    states: dict[str, str] = {kind: "UNKNOWN" for kind in LOCK_KINDS}
    for lock in locks:
        if not isinstance(lock, dict):
            raise ValidationError("lock must be an object")
        required = ("lock_id", "kind", "ref", "created_at", "authority", "acceptance_ref", "dependencies")
        if any(k not in lock for k in required):
            raise ValidationError("lock record missing required fields")
        lock_id, kind = lock["lock_id"], lock["kind"]
        if not isinstance(lock_id, str) or not lock_id or lock_id in ids:
            raise ValidationError(f"duplicate or invalid lock_id: {lock_id}")
        if kind not in LOCK_KINDS:
            raise ValidationError(f"invalid lock kind: {kind}")
        validate_ref(lock["ref"], project_root)
        validate_ref(lock["acceptance_ref"], project_root)
        _timestamp(lock["created_at"], f"lock {lock_id}.created_at")
        if lock["authority"] not in {"OWNER", "APPROVED_POLICY"}:
            raise ValidationError(f"invalid lock authority: {lock_id}")
        if not isinstance(lock["dependencies"], list):
            raise ValidationError(f"lock dependencies must be an array: {lock_id}")
        for dependency in lock["dependencies"]:
            if not isinstance(dependency, dict) or not isinstance(dependency.get("node_id"), str) or not HASH_RE.fullmatch(str(dependency.get("sha256", ""))):
                raise ValidationError(f"invalid lock dependency: {lock_id}")
        prev_id = lock.get("supersedes_lock_id")
        if prev_id is not None and (prev_id not in ids or ids[prev_id]["kind"] != kind):
            raise ValidationError(f"supersedes must point to an existing same-kind lock: {lock_id}")
        ids[lock_id] = lock
        latest_by_kind[kind] = lock
        states[kind] = "PASS"
    for kind, status in applicability.items():
        if kind not in LOCK_KINDS or status not in {"REQUIRED", "NOT_APPLICABLE", "UNKNOWN"}:
            raise ValidationError(f"invalid applicability policy for lock: {kind}")
        present = kind in latest_by_kind
        if status == "REQUIRED" and not present:
            states[kind] = "UNKNOWN"
        elif status == "NOT_APPLICABLE" and present:
            raise ValidationError(f"lock exists although policy says NOT_APPLICABLE: {kind}")
        elif status == "NOT_APPLICABLE":
            states[kind] = "NOT_APPLICABLE"
        elif status == "UNKNOWN" and not present:
            states[kind] = "UNKNOWN"
    return states


def validate_events(events: Any, *, book_id: str, project_root: Path | None = None,
                    trusted_owner_decisions: set[str] | None = None) -> None:
    if not isinstance(events, list) or not events:
        raise ValidationError("event ledger must be a non-empty array")
    seen: set[str] = set()
    previous_digest: str | None = None
    trusted = trusted_owner_decisions or set()
    for sequence, event in enumerate(events, start=1):
        if not isinstance(event, dict):
            raise ValidationError(f"event {sequence} must be an object")
        required = {"schema_version", "book_id", "event_id", "sequence", "previous_event_sha256",
                    "state_after", "state_after_sha256", "actor", "event_type", "timestamp", "evidence_refs", "event_sha256"}
        if required - set(event):
            raise ValidationError(f"event {sequence} missing fields: {sorted(required - set(event))}")
        if event["schema_version"] != "abvx-book-event/v1" or event["book_id"] != book_id:
            raise ValidationError(f"event {sequence} has wrong schema or book_id")
        event_id = event["event_id"]
        if not isinstance(event_id, str) or not event_id or event_id in seen:
            raise ValidationError(f"duplicate or invalid event_id: {event_id}")
        seen.add(event_id)
        if type(event["sequence"]) is not int or event["sequence"] != sequence:
            raise ValidationError(f"event sequence gap at {sequence}")
        if event["previous_event_sha256"] != previous_digest:
            raise ValidationError(f"event {sequence} has broken predecessor hash")
        _timestamp(event["timestamp"], f"event {sequence}.timestamp")
        if not isinstance(event["actor"], str) or not event["actor"] or not isinstance(event["event_type"], str) or not event["event_type"]:
            raise ValidationError(f"event {sequence} requires actor and event_type")
        refs = event["evidence_refs"]
        if not isinstance(refs, list):
            raise ValidationError(f"event {sequence} evidence_refs must be an array")
        for ref in refs:
            validate_ref(ref, project_root)
        if event["event_type"] in EVIDENCE_REQUIRED_EVENTS and not refs:
            raise ValidationError(f"{event['event_type']} requires evidence refs")
        if event["event_type"] == "OWNER_DECISION":
            if not refs or not any(ref.get("path") in trusted and ref.get("scope", "PROJECT") == "PROJECT" for ref in refs):
                raise ValidationError("OWNER_DECISION lacks trusted owner-decision evidence")
        if not isinstance(event["state_after"], dict) or sha256_bytes(canonical_bytes(event["state_after"])) != event["state_after_sha256"]:
            raise ValidationError(f"event {sequence} state-after hash mismatch")
        body = {k: v for k, v in event.items() if k != "event_sha256"}
        digest = sha256_bytes(canonical_bytes(body))
        if event["event_sha256"] != digest:
            raise ValidationError(f"event {sequence} hash mismatch")
        previous_digest = digest


def validate_state(state: Any, *, project_root: Path | None = None,
                   applicability: Mapping[str, str] | None = None,
                   active_extensions: set[str] | None = None) -> dict[str, str]:
    schema_path = Path(__file__).resolve().parents[3] / "ABVX_BOOK_CORE_STATE_SCHEMA_V1.json"
    schema_errors = validate_draft_2020_12(state, schema_path)
    if schema_errors:
        first = schema_errors[0]
        raise ValidationError(f"state Draft 2020-12 schema failure at {first['path']}: {first['message']}")
    required = {"schema_version", "identity", "revision", "event_cursor", "current_stage", "current_gate",
                "locks", "artifacts", "validations", "formats", "owner_gates", "extensions"}
    if not isinstance(state, dict) or required - set(state):
        missing = sorted(required - set(state)) if isinstance(state, dict) else sorted(required)
        raise ValidationError(f"state missing required envelope fields: {missing}")
    if state["schema_version"] != SCHEMA_VERSION:
        raise ValidationError("unsupported book-state schema_version")
    validate_identity(state["identity"], project_root)
    if type(state["revision"]) is not int or state["revision"] < 0:
        raise ValidationError("revision must be a non-negative integer")
    if state["event_cursor"] is not None and (not isinstance(state["event_cursor"], str) or not state["event_cursor"]):
        raise ValidationError("event_cursor must be a non-empty string or null")
    for key in ("current_stage", "current_gate"):
        if not isinstance(state[key], str) or not state[key]:
            raise ValidationError(f"{key} must be an explicit non-empty state")
    for key in ("artifacts", "validations", "formats", "owner_gates"):
        if not isinstance(state[key], list):
            raise ValidationError(f"{key} must be an array")
    for item in state["formats"]:
        required_format = {"target_id", "format_module", "adapter_version", "config", "eligibility"}
        if not isinstance(item, dict) or required_format - set(item):
            raise ValidationError("format target missing required contract fields")
        if item["eligibility"] not in {"PASS", "FAIL", "UNKNOWN", "NOT_APPLICABLE"}:
            raise ValidationError("format target has invalid eligibility")
        if item["eligibility"] == "PASS" and not item.get("eligibility_evidence"):
            raise ValidationError("format PASS requires eligibility evidence")
        evidence_refs = item.get("eligibility_evidence", [])
        if not isinstance(evidence_refs, list):
            raise ValidationError("format eligibility_evidence must be an array")
        for ref in evidence_refs:
            validate_ref(ref, project_root)
    for gate in state["owner_gates"]:
        if not isinstance(gate, dict) or not all(isinstance(gate.get(k), str) and gate[k] for k in ("gate_id", "scope", "state")):
            raise ValidationError("owner gate requires gate_id, scope, and explicit state")
        if gate["state"] == "APPROVED":
            if not gate.get("approved_at") or not gate.get("decision_ref"):
                raise ValidationError("approved owner gate requires timestamp and decision proof")
            _timestamp(gate["approved_at"], "owner gate approved_at")
            validate_ref(gate["decision_ref"], project_root)
    if not isinstance(state["extensions"], dict):
        raise ValidationError("extensions must be an object")
    active = active_extensions or set()
    for namespace, payload in state["extensions"].items():
        if not isinstance(namespace, str) or not re.fullmatch(r"[a-z][a-z0-9_-]*\.[a-z][a-z0-9_-]*", namespace) or not isinstance(payload, dict):
            raise ValidationError(f"invalid extension namespace/payload: {namespace}")
        if namespace not in active:
            raise ValidationError(f"unknown registered extension cannot certify PASS: {namespace}")
        if payload.get("state") == "PASS":
            raise ValidationError(f"extension {namespace} has no Phase 1 semantic validator; it cannot certify PASS")
    lock_states = validate_locks(state["locks"], project_root=project_root, applicability=applicability or {})
    for result in state["validations"]:
        validate_result(result, project_root)
    if "metrics" in state:
        if not isinstance(state["metrics"], list):
            raise ValidationError("metrics must be an array")
        for metric in state["metrics"]:
            validate_metrics(metric)
    return lock_states


def validate_metrics(metrics: Any) -> dict[str, Any]:
    if not isinstance(metrics, dict) or set(metrics) - set(METRIC_FIELDS):
        raise ValidationError("metrics contains unsupported fields")
    result = {name: metrics.get(name) for name in METRIC_FIELDS}
    if result["stage_id"] is not None and (not isinstance(result["stage_id"], str) or not result["stage_id"]):
        raise ValidationError("metric stage_id must be non-empty or null")
    if result["measurement_basis"] not in {None, "PROSPECTIVE", "RETAINED_ACTUAL", "UNKNOWN"}:
        raise ValidationError("invalid metric measurement_basis")
    counters = set(METRIC_FIELDS) & {"calendar_seconds", "owner_wait_seconds", "owner_minutes", "owner_interventions",
                                     "agent_runs", "revision_count", "generation_attempts", "qa_runs", "qa_failures",
                                     "escaped_defects", "api_calls", "input_tokens", "output_tokens"}
    for key in counters:
        value = result[key]
        if value is not None and (type(value) not in {int, float} or not math.isfinite(value) or value < 0):
            raise ValidationError(f"metric {key} must be a non-negative finite number or null")
    for key in ("estimated_cost", "actual_cost"):
        value = result[key]
        if value is not None and (type(value) not in {int, float} or not math.isfinite(value) or value < 0):
            raise ValidationError(f"metric {key} must be a non-negative finite number or null")
    for key in ("stage_started_at", "stage_completed_at", "started_at", "completed_at", "owner_requested_at", "owner_approved_at"):
        if result[key] is not None:
            _timestamp(result[key], f"metric {key}")
    if result["currency"] is not None and (not isinstance(result["currency"], str) or not result["currency"]):
        raise ValidationError("metric currency must be non-empty or null")
    return result


@dataclass(frozen=True)
class BookAdapter:
    book_id: str
    book_type: str
    status: Callable[[], str]
    validate: Callable[[], Mapping[str, Any]]
    identity: Mapping[str, Any] | None = None
    project_root: Path | None = None
    state_path: str | None = None
    events_path: str | None = None
    applicability: Mapping[str, str] = field(default_factory=dict)
    active_extensions: set[str] = field(default_factory=set)
    trusted_owner_decisions: set[str] = field(default_factory=set)


def _adapter_path(root: Path, relative: str, kind: str) -> Path:
    base = root.resolve()
    path = (base / relative).resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise ValidationError(f"adapter {kind} path escapes project root: {relative}") from exc
    if not path.is_file():
        raise ValidationError(f"adapter {kind} file is missing: {relative}")
    return path


def _load_core_snapshot(adapter: BookAdapter) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    if not adapter.project_root or not adapter.state_path or not adapter.events_path:
        raise ValidationError("generic adapter requires project_root, state_path, and events_path together")
    root = adapter.project_root
    state_file = _adapter_path(root, adapter.state_path, "state")
    events_file = _adapter_path(root, adapter.events_path, "events")
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
        lines = events_file.read_text(encoding="utf-8").splitlines()
        if not lines or any(not line.strip() for line in lines):
            raise ValueError("event ledger must contain non-empty JSONL lines")
        events = [json.loads(line) for line in lines]
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValidationError(f"adapter snapshot cannot be parsed: {exc}") from exc
    if not isinstance(state, dict) or not isinstance(state.get("identity"), dict):
        raise ValidationError("adapter state has no canonical identity")
    if state["identity"].get("book_id") != adapter.book_id:
        raise ValidationError("adapter state book_id disagrees with registered identity")
    if adapter.identity is not None and canonical_bytes(adapter.identity) != canonical_bytes(state["identity"]):
        raise ValidationError("registered adapter identity disagrees with canonical state identity")
    state_ref = {"path": str(state_file.relative_to(root.resolve())), "sha256": sha256_file(state_file), "scope": "PROJECT"}
    events_ref = {"path": str(events_file.relative_to(root.resolve())), "sha256": sha256_file(events_file), "scope": "PROJECT"}
    validate_ref(state_ref, root)
    validate_ref(events_ref, root)
    return state, events, state_ref, events_ref


def status_book(book_id: str, registry: Mapping[str, BookAdapter]) -> str:
    adapter = registry.get(book_id)
    if adapter is None:
        raise ValidationError(f"unknown registered book: {book_id}")
    if adapter.book_id != book_id:
        raise ValidationError("adapter identity does not match registry key")
    if adapter.identity is not None:
        validate_identity(dict(adapter.identity))
    return adapter.status()


def validate_book(book_id: str, registry: Mapping[str, BookAdapter]) -> dict[str, Any]:
    adapter = registry.get(book_id)
    if adapter is None:
        raise ValidationError(f"unknown registered book: {book_id}")
    if adapter.book_id != book_id:
        raise ValidationError("adapter identity does not match registry key")
    if adapter.identity is not None:
        validate_identity(dict(adapter.identity))
    report = dict(adapter.validate())
    checks = report.get("checks")
    if not isinstance(checks, list):
        raise ValidationError("adapter validate result must contain checks")
    if adapter.state_path or adapter.events_path or adapter.project_root:
        try:
            state, events, state_ref, events_ref = _load_core_snapshot(adapter)
            lock_states = validate_state_events(
                state, events, project_root=adapter.project_root, applicability=adapter.applicability,
                active_extensions=adapter.active_extensions,
                trusted_owner_decisions=adapter.trusted_owner_decisions,
            )
            core_result = make_validator_result(
                "core-state-events", "PASS", input_refs=[state_ref, events_ref],
                evidence_refs=[state_ref, events_ref], observed="state/event projection, refs and locks verified",
                expected="canonical state agrees with append-only ledger",
            )
            validate_result(core_result, adapter.project_root)
            checks.append(core_result)
            checks.extend({"check_id": f"lock:{kind}", "state": value} for kind, value in sorted(lock_states.items()))
        except (OSError, ValueError, ValidationError) as exc:
            checks.append({"check_id": "core-state-events", "state": "FAIL", "observed": str(exc)})
    states = [check.get("state") for check in checks if isinstance(check, dict)]
    if "FAIL" in states:
        report["overall"] = "FAIL"
    elif "UNKNOWN" in states and report.get("overall") == "PASS":
        report["overall"] = "REVIEW"
    report["checks"] = checks
    return report


def validate_state_events(state: Mapping[str, Any], events: Any, *, project_root: Path | None = None,
                          applicability: Mapping[str, str] | None = None,
                          active_extensions: set[str] | None = None,
                          trusted_owner_decisions: set[str] | None = None) -> dict[str, str]:
    lock_states = validate_state(dict(state), project_root=project_root, applicability=applicability,
                                 active_extensions=active_extensions)
    validate_events(events, book_id=state["identity"]["book_id"], project_root=project_root,
                    trusted_owner_decisions=trusted_owner_decisions)
    latest = events[-1]
    if type(state["revision"]) is not int or state["revision"] != latest["sequence"]:
        raise ValidationError("state revision disagrees with latest event sequence")
    if state["event_cursor"] != latest["event_id"] or canonical_bytes(state) != canonical_bytes(latest["state_after"]):
        raise ValidationError("state projection/cursor disagrees with latest event")
    return lock_states


__all__ = ["BookAdapter", "HEX_SHA256", "METRIC_FIELDS", "canonical_bytes", "make_legacy_validator_result",
           "make_validator_result", "sha256_bytes",
           "sha256_file", "status_book", "validate_book", "validate_events", "validate_identity",
           "validate_locks", "validate_metrics", "validate_modules", "validate_ref", "validate_result",
           "validate_state", "validate_state_events"]
