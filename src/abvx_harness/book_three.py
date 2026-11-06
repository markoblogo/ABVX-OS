from __future__ import annotations

import json
import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import __version__
from .book_core import BookAdapter, HEX_SHA256, RESULT_STATES, make_legacy_validator_result, sha256_bytes, sha256_file
from .harness import ValidationError, load_json, validate


BOOK_ID = "gd3"
STATE_NAME = "GOOD_DOG_BOOK_THREE_STATE_V1.json"
EVENT_NAME = "GOOD_DOG_BOOK_THREE_EVENT_LEDGER_V1.jsonl"
CANON_NAME = "GOOD_DOG_SERIES_PRODUCTION_CANON_V1.md"
STATUS_NAMES = {"NOT_STARTED", "UNKNOWN", "UNDECIDED", "NOT_APPLICABLE", "LOCAL_QA_PASS", "KDP_PREVIEW_PENDING", "KDP_PREVIEW_PASS", "SUBMISSION_AUTHORIZED", "SUBMITTED", "IN_REVIEW", "PUBLISHING", "LIVE", "REJECTED", "HOLD"}
STAGES = {"all", "canon", "text", "illustrations", "kindle", "print", "metadata", "retailer"}
SERIES_MANIFEST = "GOOD_DOGS_CANONICAL_MANIFEST_V6.json"
WORKFLOW_FIELDS = ("concept", "architecture", "draft", "developmental", "compression_integrity", "line_edit", "metadata")
MEASUREMENTS = ("stage_started_at", "stage_completed_at", "owner_requested_at", "owner_approved_at",
                "revision_count", "generation_attempt_count", "qa_rerun_count", "api_calls", "api_cost_usd")
RETAILER_TRANSITIONS = {
    "NOT_STARTED": {"LOCAL_QA_PASS", "HOLD"},
    "LOCAL_QA_PASS": {"KDP_PREVIEW_PENDING", "HOLD"},
    "KDP_PREVIEW_PENDING": {"KDP_PREVIEW_PASS", "REJECTED", "HOLD"},
    "KDP_PREVIEW_PASS": {"SUBMISSION_AUTHORIZED", "HOLD"},
    "SUBMISSION_AUTHORIZED": {"SUBMITTED", "HOLD"},
    "SUBMITTED": {"IN_REVIEW", "PUBLISHING", "LIVE", "REJECTED", "HOLD"},
    "IN_REVIEW": {"PUBLISHING", "LIVE", "REJECTED", "HOLD"},
    "PUBLISHING": {"LIVE", "REJECTED", "HOLD"},
    "LIVE": {"HOLD"}, "REJECTED": {"KDP_PREVIEW_PENDING", "HOLD"},
    "HOLD": {"LOCAL_QA_PASS", "KDP_PREVIEW_PENDING"},
}
def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _local_file(project_root: Path, raw_path: Any) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path:
        return None
    path = (project_root / raw_path).resolve()
    try:
        path.relative_to(project_root.resolve())
    except ValueError:
        return None
    return path


def _parse_canon_table(project_root: Path) -> dict[str, tuple[str, str]]:
    path = project_root / CANON_NAME
    rows: dict[str, tuple[str, str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [part.strip() for part in line.strip().strip("|").split("|")]
        if len(cells) == 3 and cells[0] not in {"Field", "---"} and not cells[0].startswith(":"):
            rows[cells[0]] = (cells[1].strip("`"), cells[2])
    required = {"Series", "Series type/order", "Subtitle pattern", "Book-facing author", "Amazon author", "Kindle", "Paperback"}
    missing = required - rows.keys()
    if missing:
        raise ValidationError(f"{CANON_NAME}: missing canonical rows: {sorted(missing)}")
    return rows


def _inherit(value: Any, authority: str, state: str) -> dict[str, Any]:
    return {"value": value, "authority": authority, "state": state}


def initial_state(project_root: Path) -> dict[str, Any]:
    rows = _parse_canon_table(project_root)
    series_name, series_authority = rows["Series"]
    order_text, order_authority = rows["Series type/order"]
    subtitle_pattern, subtitle_authority = rows["Subtitle pattern"]
    book_author, book_author_authority = rows["Book-facing author"]
    amazon_author, amazon_author_authority = rows["Amazon author"]
    kindle, kindle_authority = rows["Kindle"]
    paperback, print_authority = rows["Paperback"]
    return {
        "schema_version": "good-dog-book-three-state/v1",
        "book_id": BOOK_ID,
        "revision": 1,
        "series": {
            "name": _inherit(series_name, f"{CANON_NAME}#Series", "RECOVERED"),
            "type": _inherit("ORDERED" if order_text.startswith("Ordered") else "UNKNOWN", f"{CANON_NAME}#Series type/order", "OWNER_DEFAULT"),
            "position": _inherit(3 if "position 3" in order_text else None, f"{CANON_NAME}#Series type/order", "OWNER_DEFAULT"),
        },
        "series_position": 3 if "position 3" in order_text else "UNKNOWN",
        "inherited_defaults": {
            "subtitle_pattern": _inherit(subtitle_pattern, f"{CANON_NAME}#Subtitle pattern", "OWNER_DEFAULT"),
            "kindle_route": _inherit("DIRECT_DOCX_REFLOWABLE", f"{CANON_NAME}#Kindle", "OWNER_DEFAULT"),
            "kindle_price_usd": _inherit(4.99 if "$4.99" in kindle else None, f"{CANON_NAME}#Kindle", "OWNER_DEFAULT"),
            "kdp_select": _inherit("YES_UNLESS_OWNER_CHANGES" if "KDP Select YES" in kindle else "UNKNOWN", f"{CANON_NAME}#Kindle", "OWNER_DEFAULT"),
            "print_trim_in": _inherit([5.5, 8.5] if "5.5×8.5" in paperback else None, f"{CANON_NAME}#Paperback", "OWNER_DEFAULT"),
            "print_ink": _inherit("BLACK_AND_WHITE" if "Black & White" in paperback else "UNKNOWN", f"{CANON_NAME}#Paperback", "OWNER_DEFAULT"),
            "print_paper": _inherit("CREAM" if "Cream" in paperback else "UNKNOWN", f"{CANON_NAME}#Paperback", "OWNER_DEFAULT"),
            "print_bleed": _inherit("NO_BLEED" if "No Bleed" in paperback else "UNKNOWN", f"{CANON_NAME}#Paperback", "OWNER_DEFAULT"),
            "cover_finish": _inherit("MATTE" if "Matte" in paperback else "UNKNOWN", f"{CANON_NAME}#Paperback", "OWNER_DEFAULT"),
            "paperback_price_usd": _inherit(18.99 if "$18.99" in paperback else None, f"{CANON_NAME}#Paperback", "OWNER_DEFAULT"),
            "ai_disclosure": _inherit("AI_GENERATED_TEXT_AND_IMAGES" if "AI-generated text AND images" in rows["Rights/AI"][0] else "AI_GENERATED_TEXT_AND_IMAGES", f"{CANON_NAME}#Rights/AI", "OWNER_DEFAULT"),
        },
        "metadata": {
            "title": _inherit("UNKNOWN", "Owner metadata decision before export; not required at Gate A", "UNKNOWN"),
            "subtitle": _inherit("UNKNOWN", "Owner metadata decision; series convention remains available", "UNKNOWN"),
            "author_display": _inherit(book_author, f"{CANON_NAME}#Book-facing author", "OWNER_DEFAULT"),
            "amazon_author": _inherit(amazon_author, f"{CANON_NAME}#Amazon author", "OWNER_DEFAULT"),
            "isbn": _inherit(None, "Paperback publication decision", "UNKNOWN"),
            "release_date": _inherit(None, "Publication decision", "UNKNOWN"),
            "rights_confirmed": _inherit(None, "Owner confirmation required for Book Three inputs", "UNKNOWN"),
            "ai_disclosure_completed": _inherit(None, "Live KDP workflow evidence required", "UNKNOWN"),
        },
        "current_stage": "NOT_STARTED",
        "current_gate": "A_PENDING",
        "book_status": "NOT_STARTED",
        "publication": "NOT_STARTED",
        "owner_action_required": "AUTHORIZE GATE A — CONCEPT + ARCHITECTURE DEVELOPMENT",
        "next_allowed_action": "BUILD CANONICAL BOOK THREE CONTEXT PACKET AND DEVELOP CONCEPT OPTIONS",
        "workflow": {name: "NOT_STARTED" for name in WORKFLOW_FIELDS},
        "continuity_packet": {"path": None, "sha256": None, "status": "NOT_STARTED"},
        "drafting_model": {"manuscript": "ONE_CANONICAL_CONTINUOUS_MANUSCRIPT", "causal_checkpoints": 3, "boundaries": "ARCHITECTURE_DEPENDENT"},
        "instrumentation": {name: None for name in MEASUREMENTS},
        "series_publication_source": {"path": SERIES_MANIFEST, "sha256": sha256_file(project_root / SERIES_MANIFEST)},
        "retailer_constraints": [],
        "production_config": {
            "kindle_route": "DIRECT_DOCX_REFLOWABLE", "kindle_primary_source": "DOCX",
            "print_safe_area": {"state": "UNKNOWN", "safe_box_pt": None, "clearance_pt": None, "authority": None},
            "safe_area_required_before_local_print_pass": True,
            "author_surfaces": {"book": "Sminx Jonahtan J.", "amazon": "Sminx Jonahtan"},
        },
        "chapter_count": "UNKNOWN",
        "word_count": "UNKNOWN",
        "text_lock": {"status": "NONE", "path": None, "sha256": None},
        "illustrations": {"status": "NOT_STARTED", "manifest_path": None, "manifest_sha256": None},
        "cover": {"status": "NOT_STARTED", "front_cover_sha256": None, "wrap_sha256": None},
        "contents_navigation": {
            "kindle": {"digital_navigation_required": True, "digital_navigation": {"state": "UNKNOWN", "evidence_path": None}, "contents_parity": {"enabled": None, "state": "UNKNOWN"}},
            "paperback": {"visible_contents": {"enabled": None, "state": "UNKNOWN"}, "contents_parity": {"enabled": None, "state": "UNKNOWN"}},
        },
        "formats": {
            fmt: {
                "local_qa": {"state": "NOT_STARTED", "evidence_path": None, "output_sha256": None},
                "kdp_preview": {"state": "NOT_STARTED", "evidence_path": None, "upload_sha256": None},
                "submission": {"state": "NOT_STARTED", "evidence_path": None, "upload_sha256": None},
                "publication": {"state": "NOT_STARTED", "evidence_path": None, "observed_at": None, "upload_sha256": None},
                "retailer_state": "NOT_STARTED",
            }
            for fmt in ("kindle", "paperback")
        },
        "gates": {letter: "PENDING" for letter in "ABCDEF"},
        "gate_model": {"path": "GOOD_DOG_BOOK_THREE_GATE_MODEL_V1.json", "sha256": sha256_file(project_root / "GOOD_DOG_BOOK_THREE_GATE_MODEL_V1.json")},
        "canon_source": {"path": CANON_NAME, "sha256": sha256_file(project_root / CANON_NAME)},
        "event_cursor": "gd3-0001",
    }


def state_projection(state: dict[str, Any]) -> dict[str, Any]:
    projection = {key: state[key] for key in ("revision", "current_stage", "current_gate", "book_status") if key in state}
    if state.get("revision", 0) >= 1:
        values = {key: value for key, value in state.items() if key != "event_cursor"}
        projection["state_sha256"] = sha256_bytes(json.dumps(values, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode())
        projection["retailer_states"] = {fmt: value["retailer_state"] for fmt, value in state["formats"].items()}
    return projection


def _state_schema_path(project_root: Path) -> Path:
    return project_root / "schemas" / "book_three_state.schema.json"


def _event_schema_path(project_root: Path) -> Path:
    return project_root / "schemas" / "book_three_event.schema.json"


def _result_schema_path(project_root: Path) -> Path:
    return project_root / "schemas" / "validator_result.schema.json"


def make_validator_result(check_id: str, state: str, *, evidence_path: str | None,
                          input_sha256: list[str] | None = None, output_sha256: list[str] | None = None,
                          observed: Any = None, expected: Any = None,
                          tool_version: str | None = None, exception_owner: str | None = None,
                          exception_reason: str | None = None, evidence_available: bool = False) -> dict[str, Any]:
    return make_legacy_validator_result(check_id, state, evidence_path=evidence_path,
                                        input_sha256=input_sha256, output_sha256=output_sha256,
                                        observed=observed, expected=expected, tool_version=tool_version,
                                        exception_owner=exception_owner, exception_reason=exception_reason,
                                        evidence_available=evidence_available, timestamp=now_iso(),
                                        default_tool_version=f"abvx-os/{__version__}")


def _result(project_root: Path, check_id: str, state: str, *, input_path: Path | None = None,
            evidence_path: Path | None = None, observed: Any = None, expected: Any = None) -> dict[str, Any]:
    inputs: list[str] = []
    if input_path and input_path.is_file():
        inputs.append(sha256_file(input_path))
    evidence = str(evidence_path.resolve().relative_to(project_root.resolve())) if evidence_path and evidence_path.is_file() else None
    result = make_validator_result(check_id, state, evidence_path=evidence, input_sha256=inputs,
                                   observed=observed, expected=expected, evidence_available=bool(evidence))
    validate(result, load_json(_result_schema_path(project_root)), schema_path=_result_schema_path(project_root),
             root=project_root, location=f"validator:{check_id}")
    return result


def _read_events(project_root: Path) -> list[dict[str, Any]]:
    path = project_root / EVENT_NAME
    if not path.is_file():
        raise ValidationError(f"missing event ledger: {path}")
    events: list[dict[str, Any]] = []
    ids: set[str] = set()
    schema_path = _event_schema_path(project_root)
    schema = load_json(schema_path)
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            raise ValidationError(f"event ledger line {index}: blank lines are not permitted")
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"event ledger line {index}: {exc}") from exc
        try:
            validate(event, schema, schema_path=schema_path, root=project_root, location=f"event[{index}]")
            timestamp = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
            if timestamp.tzinfo is None:
                raise ValidationError("event timestamp requires a timezone")
        except (ValueError, TypeError) as exc:
            raise ValidationError(f"event ledger line {index}: {exc}") from exc
        if index > 1 and event.get("book_id") != BOOK_ID:
            raise ValidationError("new ledger records must identify gd3")
        if event["event_id"] != f"gd3-{index:04d}":
            raise ValidationError(f"event ledger line {index}: event_id must be gd3-{index:04d}")
        if index > 1 and event["previous_state"] != events[-1]["new_state"]:
            raise ValidationError(f"event ledger line {index}: previous_state does not continue the prior snapshot")
        for evidence in event["evidence"]:
            evidence_path = (project_root / evidence["path"]).resolve()
            try:
                evidence_path.relative_to(project_root.resolve())
            except ValueError as exc:
                raise ValidationError(f"event ledger line {index}: evidence path escapes project root") from exc
            if not evidence_path.is_file() or not HEX_SHA256.fullmatch(evidence["sha256"]) or sha256_file(evidence_path) != evidence["sha256"]:
                raise ValidationError(f"event ledger line {index}: evidence missing or SHA-256 mismatch: {evidence['path']}")
        if event["event_id"] in ids:
            raise ValidationError(f"duplicate event_id: {event['event_id']}")
        if index > 1:
            old = event["previous_state"].get("retailer_states", {fmt: "NOT_STARTED" for fmt in ("kindle", "paperback")})
            new = event["new_state"].get("retailer_states", old)
            for fmt in ("kindle", "paperback"):
                if old[fmt] != new[fmt]:
                    validate_retailer_transition(old[fmt], new[fmt], evidence_available=bool(event["evidence"]),
                                                 owner_authorized=event["owner_gate"] == "F" and event["actor"].lower() == "owner" and event.get("format") == fmt)
        ids.add(event["event_id"])
        events.append(event)
    if not events:
        raise ValidationError("event ledger is empty")
    return events


def validate_retailer_transition(previous: str, current: str, *, evidence_available: bool,
                                 owner_authorized: bool = False) -> None:
    """Validate one recorded step; this function never changes state or contacts KDP."""
    if previous not in RETAILER_TRANSITIONS or current not in RETAILER_TRANSITIONS:
        raise ValidationError("unknown retailer state")
    if previous == current:
        if current in {"LOCAL_QA_PASS", "KDP_PREVIEW_PASS", "SUBMISSION_AUTHORIZED", "SUBMITTED", "IN_REVIEW", "PUBLISHING", "LIVE"} and not evidence_available:
            raise ValidationError(f"{current} requires recorded evidence even when unchanged")
        return
    if current not in RETAILER_TRANSITIONS[previous]:
        raise ValidationError(f"invalid retailer transition: {previous} -> {current}")
    if current not in {"HOLD", "KDP_PREVIEW_PENDING"} and not evidence_available:
        raise ValidationError(f"{current} requires separately recorded evidence")
    if current == "SUBMISSION_AUTHORIZED" and not owner_authorized:
        raise ValidationError("submission authorization requires owner Gate F evidence")


def _verified_ref(project_root: Path, ref: Any) -> Path | None:
    if not isinstance(ref, dict):
        return None
    path = _local_file(project_root, ref.get("path"))
    digest = ref.get("sha256")
    if path and path.is_file() and isinstance(digest, str) and HEX_SHA256.fullmatch(digest) and sha256_file(path) == digest:
        return path
    return None


def _recorded_evidence(project_root: Path, raw_path: Any) -> Path | None:
    path = _local_file(project_root, raw_path)
    if not path or not path.is_file():
        return None
    digest = sha256_file(path)
    try:
        return path if any(_local_file(project_root, ref["path"]) == path and ref["sha256"] == digest
                           for event in _read_events(project_root) for ref in event["evidence"]) else None
    except (ValidationError, OSError, KeyError):
        return None


def external_action_allowed(state: dict[str, Any], fmt: str) -> bool:
    """An observed limit stays active until an explicit clearing observation is recorded."""
    return not any(item["format"] == fmt and item["status"] == "ACTIVE" for item in state["retailer_constraints"])


def image_safe_area(placements: list[dict[str, Any]], safe_box_pt: list[float], clearance_pt: float) -> list[dict[str, Any]]:
    """Reuse Book Two's safe-box geometry, supplied explicitly per future build."""
    if len(safe_box_pt) != 4 or not all(math.isfinite(v) for v in safe_box_pt) or not math.isfinite(clearance_pt) or clearance_pt < 0:
        raise ValidationError("invalid safe box or clearance")
    sx, sy, sw, sh = safe_box_pt
    if sw <= 0 or sh <= 0:
        raise ValidationError("safe box dimensions must be positive")
    results = []
    for item in placements:
        x, y, w, h = item["bbox_pt"]
        if not all(math.isfinite(v) for v in (x, y, w, h)) or w <= 0 or h <= 0:
            raise ValidationError("invalid image bounding box")
        clearances = [x - sx, y - sy, sx + sw - x - w, sy + sh - y - h]
        results.append({"page": item["page"], "bbox_pt": [x, y, w, h], "limits_pt": safe_box_pt,
                        "clearance_pt": clearances, "state": "PASS" if min(clearances) > clearance_pt else "FAIL"})
    return results


def _series_publication_check(project_root: Path, state: dict[str, Any], state_path: Path) -> dict[str, Any]:
    try:
        source = _verified_ref(project_root, state["series_publication_source"])
        if not source:
            raise ValidationError("pinned current series manifest is missing or its hash changed")
        manifest = load_json(source)
        canon_path = _local_file(project_root, manifest["book_two_publication_canon"])
        if not canon_path or not canon_path.is_file():
            raise ValidationError("declared publication canon is unavailable")
        canon = load_json(canon_path)
        observed = {"book_one": manifest["current_state"]["book_one"],
                    "kindle": canon["book_two"]["kindle"]["status"], "kindle_asin": canon["book_two"]["kindle"]["asin"],
                    "paperback": canon["book_two"]["paperback"]["status"], "paperback_asin": canon["book_two"]["paperback"]["asin"],
                    "series": canon["series_retailer_state"]["status"], "book_three": canon["book_three"]["status"]}
        expected = {"book_one": "PRESERVED_UNCHANGED", "kindle": "LIVE", "kindle_asin": "B0HLJ9VMWB",
                    "paperback": "LIVE", "paperback_asin": "B0HLLKRHRW", "series": "LIVE", "book_three": "NOT_STARTED"}
        if observed != expected:
            raise ValidationError(f"current series baseline conflict: {observed}")
        for record in (canon["book_two"]["kindle"], canon["book_two"]["paperback"], canon["series_retailer_state"], manifest["retailer_observation"]):
            if not _verified_ref(project_root, {"path": record["evidence_path"], "sha256": record["evidence_sha256"]}):
                raise ValidationError("current series LIVE evidence is missing or changed")
        return _result(project_root, "current-series-publication-baseline", "PASS", input_path=source,
                       evidence_path=canon_path, observed=observed, expected=expected)
    except (ValidationError, OSError, KeyError, TypeError) as exc:
        return _result(project_root, "current-series-publication-baseline", "FAIL", input_path=state_path,
                       evidence_path=state_path, observed=str(exc), expected="declared V6/V4 baseline and retailer screenshot hashes match")


def _owner_gate_check(project_root: Path, state: dict[str, Any], state_path: Path) -> dict[str, Any]:
    problems = []
    try:
        events = _read_events(project_root)
        for gate, status in state["gates"].items():
            if status == "APPROVED" and not any(e["event_type"] == "OWNER_GATE_APPROVED" and e["owner_gate"] == gate
                                               and e["actor"].lower() == "owner" and e["evidence"] for e in events):
                problems.append(f"Gate {gate} approval lacks owner evidence")
        workflow = state["workflow"]
        concept_started = workflow["concept"] != "NOT_STARTED"
        start_authorized = any(e["event_type"] == "GATE_A_STARTED" and e["owner_gate"] == "A"
                               and e["evidence"] for e in events)
        if concept_started and state["gates"]["A"] != "APPROVED" and not start_authorized:
            problems.append("concept requires recorded Gate A start authorization")
        engine_selected = any(e["event_type"] == "STORY_ENGINE_SELECTED" and e["owner_gate"] == "A"
                              and e["actor"] == "owner" and e["evidence"] for e in events)
        if workflow["architecture"] != "NOT_STARTED" and state["gates"]["A"] != "APPROVED" and not engine_selected:
            problems.append("architecture requires recorded owner engine selection")
        if workflow["draft"] != "NOT_STARTED" and state["gates"]["A"] != "APPROVED":
            problems.append("draft requires approved Gate A")
        if workflow["developmental"] != "NOT_STARTED" and state["gates"]["B"] != "APPROVED":
            problems.append("developmental work requires approved Gate B")
        if state["cover"]["status"] == "APPROVED":
            digest = state["cover"]["front_cover_sha256"]
            if state["gates"]["E"] != "APPROVED" or not digest or not any(ref["sha256"] == digest for event in events for ref in event["evidence"]):
                problems.append("cover approval requires Gate E and hash-recorded front-cover evidence")
        for earlier, later in (("developmental", "compression_integrity"), ("compression_integrity", "line_edit")):
            if workflow[later] != "NOT_STARTED" and workflow[earlier] != "PASS":
                problems.append(f"{later} requires {earlier} PASS")
        for name, status in workflow.items():
            if status == "PASS" and not _verified_ref(project_root, state.get("workflow_evidence", {}).get(name)):
                problems.append(f"{name} PASS lacks hash-verified evidence")
    except (ValidationError, OSError, KeyError) as exc:
        problems.append(str(exc))
    return _result(project_root, "owner-gates-and-editorial-order", "FAIL" if problems else "PASS", input_path=state_path,
                   evidence_path=state_path, observed=problems or "six gates pending; editorial functions remain separate", expected="explicit owner evidence and separate editorial prerequisites")


def _canon_conflicts(project_root: Path, state: dict[str, Any]) -> list[str]:
    rows = _parse_canon_table(project_root)
    expected_name = rows["Series"][0]
    order_text = rows["Series type/order"][0]
    checks = [
        (state["series"]["name"]["value"] == expected_name, "series name conflicts with canonical source"),
        (state["series"]["type"]["value"] == ("ORDERED" if order_text.startswith("Ordered") else "UNKNOWN"), "series type conflicts with canonical source"),
        (state["series"]["position"]["value"] == (3 if "position 3" in order_text else None), "series position conflicts with canonical source"),
        (state["series_position"] == (3 if "position 3" in order_text else "UNKNOWN"), "series_position conflicts with canonical source"),
        (state["metadata"]["author_display"]["value"] == rows["Book-facing author"][0], "book-facing author mapping conflicts with canonical source"),
        (state["metadata"]["amazon_author"]["value"] == rows["Amazon author"][0], "Amazon author mapping conflicts with canonical source"),
        (state["inherited_defaults"]["subtitle_pattern"]["value"] == rows["Subtitle pattern"][0], "subtitle pattern conflicts with canonical source"),
    ]
    baseline = initial_state(project_root)
    for key, value in baseline["inherited_defaults"].items():
        checks.append((state["inherited_defaults"][key] == value, f"inherited {key} conflicts with canonical source"))
    source_path = project_root / CANON_NAME
    if state["canon_source"]["sha256"] != sha256_file(source_path):
        checks.append((False, "canonical source hash changed; explicit state reconciliation required"))
    model_path = project_root / state["gate_model"]["path"]
    if not model_path.is_file() or state["gate_model"]["sha256"] != sha256_file(model_path):
        checks.append((False, "owner gate model hash changed or is missing"))
    return [message for valid, message in checks if not valid]


def _schema_check(project_root: Path, state: dict[str, Any], state_path: Path) -> dict[str, Any]:
    schema_path = _state_schema_path(project_root)
    try:
        validate(state, load_json(schema_path), schema_path=schema_path, root=project_root, location="book_three_state")
        # The shared small schema validator does not implement pattern/maxItems.
        def check_fields(value):
            if isinstance(value, dict):
                for key, item in value.items():
                    if (key == "sha256" or key.endswith("_sha256")) and item is not None and (not isinstance(item, str) or not HEX_SHA256.fullmatch(item)):
                        raise ValidationError(f"{key}: invalid SHA-256")
                    check_fields(item)
            elif isinstance(value, list):
                for item in value:
                    check_fields(item)
            elif isinstance(value, float) and not math.isfinite(value):
                raise ValidationError("non-finite numeric value")
        check_fields(state)
        safe_box = state["production_config"]["print_safe_area"]["safe_box_pt"]
        if safe_box is not None and len(safe_box) != 4:
            raise ValidationError("safe_box_pt requires exactly four numbers")
        return _result(project_root, "state-schema", "PASS", input_path=state_path, evidence_path=state_path,
                       observed="schema valid", expected="book_three_state.schema.json")
    except (ValidationError, OSError, ValueError, TypeError) as exc:
        return _result(project_root, "state-schema", "FAIL", input_path=state_path, evidence_path=state_path,
                       observed=str(exc), expected="valid Book Three state")


def _event_check(project_root: Path, state: dict[str, Any], state_path: Path) -> dict[str, Any]:
    try:
        events = _read_events(project_root)
        latest = events[-1]
        if state.get("event_cursor") != latest["event_id"] or latest["new_state"] != state_projection(state):
            return _result(project_root, "event-state-consistency", "FAIL", input_path=state_path,
                           evidence_path=project_root / EVENT_NAME,
                           observed={"cursor": state.get("event_cursor"), "latest_event": latest["event_id"], "event_state": latest["new_state"], "state": state_projection(state)},
                           expected="state event_cursor and latest event snapshot agree")
        return _result(project_root, "event-state-consistency", "PASS", input_path=state_path,
                       evidence_path=project_root / EVENT_NAME, observed=latest["event_id"], expected="latest event matches current state")
    except (ValidationError, OSError, KeyError) as exc:
        return _result(project_root, "event-state-consistency", "FAIL", input_path=state_path,
                       evidence_path=project_root / EVENT_NAME, observed=str(exc), expected="valid append-only ledger consistent with state")


def _canon_check(project_root: Path, state: dict[str, Any], state_path: Path) -> dict[str, Any]:
    try:
        problems = _canon_conflicts(project_root, state)
    except (ValidationError, OSError, KeyError) as exc:
        problems = [str(exc)]
    return _result(project_root, "series-canon", "FAIL" if problems else "PASS", input_path=state_path,
                   evidence_path=project_root / CANON_NAME, observed=problems or "inherited values match source",
                   expected="series position 3 and inherited defaults match canonical record")


def _text_check(project_root: Path, state: dict[str, Any], state_path: Path) -> dict[str, Any]:
    lock = state["text_lock"]
    if lock["status"] == "NONE":
        return _result(project_root, "text-lock", "NOT_APPLICABLE", input_path=state_path, evidence_path=state_path,
                       observed="no Book Three Text Lock exists", expected="locked source and matching SHA-256 before production")
    if lock["status"] != "LOCKED":
        return _result(project_root, "text-lock", "FAIL", input_path=state_path, evidence_path=state_path,
                       observed=lock["status"], expected="Text Lock must be LOCKED before production")
    lock_path = (project_root / lock["path"]).resolve()
    try:
        lock_path.relative_to(project_root.resolve())
    except ValueError:
        return _result(project_root, "text-lock", "FAIL", input_path=state_path, evidence_path=state_path, observed="Text Lock path escapes project root", expected="project-local immutable Text Lock")
    if not lock_path.is_file() or not HEX_SHA256.fullmatch(str(lock["sha256"])):
        return _result(project_root, "text-lock", "FAIL", input_path=state_path, evidence_path=state_path, observed="locked path or SHA is missing/invalid", expected="existing file and valid SHA-256")
    actual = sha256_file(lock_path)
    events = _read_events(project_root)
    recorded = any(event["event_type"] == "TEXT_LOCKED" and any(ref["path"] == lock["path"] and ref["sha256"] == actual for ref in event["evidence"]) for event in events)
    approved = state["gates"]["C"] == "APPROVED" and state["workflow"]["line_edit"] == "PASS"
    return _result(project_root, "text-lock", "PASS" if actual == lock["sha256"] and recorded and approved else "FAIL", input_path=state_path,
                   evidence_path=lock_path, observed=actual, expected=lock["sha256"])


def _retailer_checks(project_root: Path, state: dict[str, Any], state_path: Path, fmt: str) -> list[dict[str, Any]]:
    record = state["formats"][fmt]
    results = []
    for section, successful in (("kdp_preview", {"KDP_PREVIEW_PASS"}), ("submission", {"SUBMISSION_AUTHORIZED", "SUBMITTED", "IN_REVIEW", "PUBLISHING", "LIVE"}), ("publication", {"SUBMITTED", "IN_REVIEW", "PUBLISHING", "LIVE"})):
        item = record[section]
        evidence = _recorded_evidence(project_root, item.get("evidence_path"))
        status = item["state"]
        result_state = "NOT_APPLICABLE" if status == "NOT_STARTED" else "UNKNOWN"
        if status in successful:
            result_state = "PASS" if evidence else "FAIL"
            if section == "kdp_preview" and (not HEX_SHA256.fullmatch(str(item.get("upload_sha256"))) or record["local_qa"]["state"] != "LOCAL_QA_PASS" or item["upload_sha256"] != record["local_qa"]["output_sha256"]):
                result_state = "FAIL"
            if section == "submission" and (state["gates"]["F"] != "APPROVED" or record["kdp_preview"]["state"] != "KDP_PREVIEW_PASS"):
                result_state = "FAIL"
            if section == "submission":
                authorized = any(e["event_type"] == "OWNER_GATE_APPROVED" and e["owner_gate"] == "F" and e["actor"].lower() == "owner" and e.get("format") == fmt and e["evidence"] for e in _read_events(project_root))
                if not authorized or state["metadata"]["rights_confirmed"]["value"] is not True or state["metadata"]["ai_disclosure_completed"]["value"] is not True or state["workflow"]["metadata"] != "PASS":
                    result_state = "FAIL"
            if section == "publication" and not item.get("observed_at"):
                result_state = "FAIL"
        results.append(_result(project_root, f"{fmt}-{section}", result_state, input_path=state_path,
                               evidence_path=evidence or state_path, observed=item, expected="distinct, dated, hash-recorded retailer evidence"))
    publication = record["publication"]
    if publication["state"] != "NOT_STARTED":
        known = bool(HEX_SHA256.fullmatch(str(publication.get("upload_sha256"))))
        results.append(_result(project_root, f"{fmt}-upload-binary-provenance", "PASS" if known else "UNKNOWN", input_path=state_path,
                               evidence_path=state_path, observed=publication.get("upload_sha256"), expected="exact upload hash if independently known; LIVE evidence does not establish it"))
    retailer = record["retailer_state"]
    section_for = {"LOCAL_QA_PASS": "local_qa", "KDP_PREVIEW_PENDING": "kdp_preview", "KDP_PREVIEW_PASS": "kdp_preview",
                   "SUBMISSION_AUTHORIZED": "submission", "SUBMITTED": "submission", "IN_REVIEW": "publication", "PUBLISHING": "publication", "LIVE": "publication"}
    consistent = retailer not in section_for or record[section_for[retailer]]["state"] == retailer
    if retailer == "NOT_STARTED":
        consistent = all(record[key]["state"] == "NOT_STARTED" for key in ("local_qa", "kdp_preview", "submission", "publication"))
    results.append(_result(project_root, f"{fmt}-retailer-state-consistency", "PASS" if consistent else "FAIL", input_path=state_path,
                           evidence_path=state_path, observed=retailer, expected="retailer phase agrees with the independent format records"))
    for constraint in state["retailer_constraints"]:
        if constraint["format"] == fmt:
            proof = _verified_ref(project_root, constraint["evidence"])
            results.append(_result(project_root, f"{fmt}-KDP_TITLE_CREATION_LIMIT", "PASS" if proof else "FAIL", input_path=state_path,
                                   evidence_path=proof or state_path, observed={"classification": constraint["classification"], "external_action_allowed": external_action_allowed(state, fmt),
                                                                             "reset_at": constraint["reset_at"]},
                                   expected="external block only; reset requires an explicit clearing observation"))
    return results


def _production_checks(project_root: Path, state: dict[str, Any], state_path: Path, fmt: str) -> list[dict[str, Any]]:
    record = state["formats"][fmt]
    local = record["local_qa"]
    proof = _recorded_evidence(project_root, local.get("evidence_path"))
    code = "NOT_APPLICABLE" if local["state"] == "NOT_STARTED" else "UNKNOWN"
    if local["state"] == "LOCAL_QA_PASS":
        code = "FAIL"
        if proof and HEX_SHA256.fullmatch(str(local.get("output_sha256"))) and _text_check(project_root, state, state_path)["state"] == "PASS":
            evidence_record = load_json(proof)
            output = _verified_ref(project_root, evidence_record.get("output_ref"))
            code = "PASS" if output and evidence_record["output_ref"]["sha256"] == local["output_sha256"] else "FAIL"
    elif local["state"] in {"FAIL", "HOLD"}:
        code = "FAIL"
    results = [_result(project_root, f"{fmt}-local-qa", code, input_path=state_path, evidence_path=proof or state_path,
                       observed=local, expected="locked source, recorded QA and matching output binary")]
    config = state["production_config"]
    if fmt == "kindle":
        valid = config["kindle_route"] == "DIRECT_DOCX_REFLOWABLE" and config["kindle_primary_source"] == "DOCX"
        exception = config.get("kindle_route_exception", {})
        exception_proof = _verified_ref(project_root, exception.get("evidence"))
        result = _result(project_root, "GOOD_DOGS_KINDLE_ROUTE", "PASS" if valid else "FAIL", input_path=state_path,
                         evidence_path=state_path, observed=config["kindle_route"], expected="normal adaptive/reflowable DOCX")
        if not valid and exception_proof and exception.get("owner") and exception.get("reason"):
            result.update(state="OWNER_ACCEPTED_EXCEPTION", exception_owner=exception["owner"], exception_reason=exception["reason"],
                          evidence_path=str(exception_proof.resolve().relative_to(project_root.resolve())))
        results.append(result)
        nav = state["contents_navigation"]["kindle"]
        results.append(_result(project_root, "DIGITAL_NAVIGATION_REQUIRED", "PASS" if nav["digital_navigation_required"] else "FAIL",
                               input_path=state_path, evidence_path=state_path, observed=nav["digital_navigation_required"], expected=True))
        nav_proof = _recorded_evidence(project_root, nav["digital_navigation"].get("evidence_path"))
        nav_code = "NOT_APPLICABLE" if local["state"] == "NOT_STARTED" else "PASS" if nav["digital_navigation"]["state"] == "PASS" and nav_proof else "FAIL" if local["state"] == "LOCAL_QA_PASS" else "UNKNOWN"
        results.append(_result(project_root, "DIGITAL_NAVIGATION", nav_code, input_path=state_path, evidence_path=nav_proof or state_path,
                               observed=nav["digital_navigation"], expected="independent digital navigation proof"))
    else:
        spec = config["print_safe_area"]
        geom_path = _verified_ref(project_root, config.get("print_geometry_evidence"))
        safe_state = "NOT_APPLICABLE" if local["state"] == "NOT_STARTED" else "UNKNOWN"
        observed = spec
        if local["state"] == "LOCAL_QA_PASS":
            safe_state = "FAIL"
            if spec["state"] == "APPROVED" and spec["authority"] and geom_path:
                geometry = load_json(geom_path)
                output = _verified_ref(project_root, geometry.get("output_ref"))
                if output and geometry["output_ref"]["sha256"] == local["output_sha256"] and geometry.get("image_inventory_complete") is True:
                    if geometry.get("trim_pt") != [396, 612]:
                        raise ValidationError("print geometry has wrong inherited trim")
                    sx, sy, sw, sh = spec["safe_box_pt"]
                    if sx < 0 or sy < 0 or sx + sw > 396 or sy + sh > 612:
                        raise ValidationError("approved safe rectangle lies outside inherited trim")
                    observed = image_safe_area(geometry["placements"], spec["safe_box_pt"], spec["clearance_pt"])
                    safe_state = "PASS" if all(item["state"] == "PASS" for item in observed) else "FAIL"
        results.append(_result(project_root, "KDP_NON_BLEED_IMAGE_SAFE_AREA_CHECK", safe_state, input_path=state_path,
                               evidence_path=geom_path or state_path, observed=observed, expected="all PDF image CTM boxes strictly inside the explicitly approved safe rectangle"))
    nav_config = state["contents_navigation"][fmt]
    if fmt == "paperback":
        visible = nav_config["visible_contents"]
        visible_proof = _recorded_evidence(project_root, visible.get("evidence_path"))
        visible_code = "UNKNOWN" if visible["enabled"] is None else "NOT_APPLICABLE" if visible["enabled"] is False or local["state"] == "NOT_STARTED" else "PASS" if visible["state"] == "PASS" and visible_proof else "FAIL" if local["state"] == "LOCAL_QA_PASS" else "UNKNOWN"
        if visible["enabled"] is None and local["state"] == "LOCAL_QA_PASS":
            visible_code = "FAIL"
        results.append(_result(project_root, "VISIBLE_CONTENTS", visible_code, input_path=state_path, evidence_path=visible_proof or state_path,
                               observed=visible, expected="explicit format-specific requirement and independent proof"))
    parity = nav_config["contents_parity"]
    required = parity["enabled"] is True or (fmt == "paperback" and nav_config["visible_contents"]["enabled"] is True)
    proof = _recorded_evidence(project_root, parity.get("evidence_path"))
    parity_code = "NOT_APPLICABLE" if local["state"] == "NOT_STARTED" or not required else "PASS" if parity["enabled"] is True and parity["state"] == "PASS" and proof else "FAIL" if local["state"] == "LOCAL_QA_PASS" else "UNKNOWN"
    results.append(_result(project_root, f"{fmt}-CONTENTS_PARITY", parity_code, input_path=state_path, evidence_path=proof or state_path,
                           observed=parity, expected="separate parity proof whenever this format requires visible contents"))
    return results


def _metadata_checks(project_root: Path, state: dict[str, Any], state_path: Path) -> list[dict[str, Any]]:
    problems = _canon_conflicts(project_root, state)
    surfaces = state["production_config"]["author_surfaces"]
    if surfaces != {"book": state["metadata"]["author_display"]["value"], "amazon": state["metadata"]["amazon_author"]["value"]}:
        problems.append("wrong author on an output surface")
    result = _result(project_root, "author-surface-mapping", "FAIL" if problems else "PASS", input_path=state_path,
                     evidence_path=project_root / CANON_NAME, observed=problems or {"book": state["metadata"]["author_display"]["value"], "amazon": state["metadata"]["amazon_author"]["value"]},
                     expected="book-facing and Amazon author values match separate canonical fields")
    missing = [key for key in ("title", "subtitle") if state["metadata"][key]["state"] == "UNKNOWN"]
    for key in ("rights_confirmed", "ai_disclosure_completed"):
        if state["metadata"][key]["value"] is not True:
            missing.append(key)
    title_result = _result(project_root, "book-specific-metadata", "NOT_APPLICABLE" if state["workflow"]["metadata"] == "NOT_STARTED" else "FAIL" if missing and state["workflow"]["metadata"] == "PASS" else "UNKNOWN" if missing else "PASS", input_path=state_path,
                           evidence_path=state_path, observed={"unknown": missing}, expected="Gate A may leave book-specific metadata unknown until approved")
    return [result, title_result]


def dialogue_findings(project_root: Path, locked_text: str, lines: list[dict[str, Any]]) -> list[str]:
    findings = []
    for line in lines:
        label = f"{line.get('asset_id')} / panel {line.get('panel')} / {line.get('speaker')}"
        span = line.get("source_span", {})
        start, end = span.get("start"), span.get("end")
        text = span.get("text")
        if not line.get("speaker") or not line.get("asset_id") or not line.get("panel") or not isinstance(start, int) or not isinstance(end, int) or not (0 <= start < end <= len(locked_text)) or locked_text[start:end] != text or sha256_bytes(str(text).encode()) != span.get("sha256"):
            findings.append(f"{label}: Text Lock source span mismatch")
            continue
        species, channel = line.get("species"), line.get("channel")
        if species == "HUMAN" and channel != "ENGLISH":
            findings.append(f"{label}: HUMAN speech must remain ENGLISH")
        elif species == "SYSTEM" and channel != "SYSTEM_ENGLISH":
            findings.append(f"{label}: SYSTEM requires established English typography")
        elif species == "DOG":
            if channel != "PICTIQ":
                exception = line.get("exception", {})
                if not exception.get("owner") or not exception.get("reason") or not _verified_ref(project_root, exception.get("evidence")):
                    findings.append(f"{label}: DOG speech requires PICTIQ or an explicit owner exception")
                continue
            composer = line.get("composer", {})
            output = _verified_ref(project_root, composer.get("output_ref"))
            approval = _verified_ref(project_root, composer.get("approval_ref"))
            if not output or not approval:
                findings.append(f"{label}: PICTIQ_HOLD — approved Composer evidence missing")
                continue
            decision = load_json(approval)
            expected = {"approved": True, "owner": "owner", "asset_id": line["asset_id"], "panel": line["panel"],
                        "speaker": line["speaker"], "source_span_sha256": span["sha256"], "composer_sha256": composer["output_ref"]["sha256"]}
            if any(decision.get(key) != value for key, value in expected.items()):
                findings.append(f"{label}: PICTIQ_HOLD — Composer approval mapping mismatch")
        elif species not in {"HUMAN", "SYSTEM"}:
            findings.append(f"{label}: speaker/species missing or unsupported")
    return findings


def _illustration_check(project_root: Path, state: dict[str, Any], state_path: Path) -> dict[str, Any]:
    record = state["illustrations"]
    if record["status"] in {"NOT_STARTED", "UNDECIDED"}:
        return _result(project_root, "illustrations", "NOT_APPLICABLE", input_path=state_path, evidence_path=state_path,
                       observed=record["status"], expected="no Book Three art is authorized")
    proof = _verified_ref(project_root, {"path": record["manifest_path"], "sha256": record["manifest_sha256"]})
    problems = []
    if not proof or _text_check(project_root, state, state_path)["state"] != "PASS":
        problems.append("illustration lock lacks a matching manifest or approved Text Lock")
    else:
        manifest = load_json(proof)
        if record["status"] not in {"LOCKED", "OWNER_APPROVED"} or manifest.get("inventory_complete") is not True or not isinstance(manifest.get("assets"), list) or not isinstance(manifest.get("dialogue"), list):
            raise ValidationError("illustration inventory/status is incomplete")
        text = (project_root / state["text_lock"]["path"]).read_text(encoding="utf-8")
        if manifest.get("text_lock_sha256") != state["text_lock"]["sha256"]:
            problems.append("illustration manifest Text Lock hash mismatch")
        assets = manifest.get("assets", [])
        if not isinstance(assets, list) or any(not _verified_ref(project_root, asset.get("source_ref")) for asset in assets):
            problems.append("illustration source hash mismatch")
        lines = manifest.get("dialogue", [])
        asset_ids = {asset["id"] for asset in assets}
        if len(asset_ids) != len(assets) or any(line.get("asset_id") not in asset_ids for line in lines):
            problems.append("asset/panel mapping does not resolve")
        problems.extend(dialogue_findings(project_root, text, lines))
        if any(line.get("species") == "DOG" and line.get("channel") == "PICTIQ" for line in lines) and state["gates"]["D"] != "APPROVED":
            problems.append("PICTIQ_HOLD — conditional Gate D is unapproved")
    return _result(project_root, "illustrations", "FAIL" if problems else "PASS", input_path=state_path, evidence_path=proof or state_path,
                   observed=problems or "hashes and dialogue source/Composer mappings match", expected="Text Lock → speaker/species → Composer approval → asset/panel mapping")


def evaluate(project_root: Path, stage: str = "all") -> dict[str, Any]:
    if stage not in STAGES:
        raise ValidationError(f"unknown validation stage {stage!r}; expected {sorted(STAGES)}")
    state_path = project_root / STATE_NAME
    try:
        state = load_json(state_path)
    except (ValidationError, OSError) as exc:
        return {"stage": stage, "checks": [_result(project_root, "state-schema", "FAIL", observed=str(exc), expected="readable canonical Book Three state")], "overall": "FAIL"}
    schema = _schema_check(project_root, state, state_path)
    if schema["state"] == "FAIL":
        return {"stage": stage, "checks": [schema], "overall": "FAIL"}
    checks = [schema, _canon_check(project_root, state, state_path), _event_check(project_root, state, state_path),
              _owner_gate_check(project_root, state, state_path)]
    try:
        if stage in {"all", "canon"}:
            checks.append(_series_publication_check(project_root, state, state_path))
        if stage in {"all", "text"}:
            checks.append(_text_check(project_root, state, state_path))
            for name in WORKFLOW_FIELDS[:-1]:
                proof = _verified_ref(project_root, state.get("workflow_evidence", {}).get(name))
                code = "NOT_APPLICABLE" if state["workflow"][name] == "NOT_STARTED" else "PASS" if state["workflow"][name] == "PASS" and proof else "FAIL" if state["workflow"][name] == "HOLD" else "UNKNOWN"
                checks.append(_result(project_root, name, code, input_path=state_path, evidence_path=proof or state_path,
                                      observed=state["workflow"][name], expected="separate editorial function, supported by its own evidence"))
        if stage in {"all", "illustrations"}:
            checks.append(_illustration_check(project_root, state, state_path))
        for fmt, routed in (("kindle", "kindle"), ("paperback", "print")):
            if stage in {"all", routed}:
                checks.extend(_production_checks(project_root, state, state_path, fmt))
            if stage in {"all", routed, "retailer"}:
                checks.extend(_retailer_checks(project_root, state, state_path, fmt))
        if stage in {"all", "metadata"}:
            checks.extend(_metadata_checks(project_root, state, state_path))
    except (ValidationError, OSError, KeyError, TypeError, ValueError) as exc:
        checks.append(_result(project_root, f"{stage}-input-integrity", "FAIL", input_path=state_path, evidence_path=state_path,
                              observed=str(exc), expected="valid local evidence and contract fields"))
    overall = "FAIL" if any(check["state"] == "FAIL" for check in checks) else "REVIEW" if any(check["state"] == "UNKNOWN" for check in checks) else "PASS"
    return {"stage": stage, "checks": checks, "overall": overall}


def render_status(project_root: Path) -> str:
    try:
        state = load_json(project_root / STATE_NAME)
        report = evaluate(project_root, "all")
        failures = [check["check_id"] for check in report["checks"] if check["state"] == "FAIL"]
        if failures:
            return "BOOK: BLOCKED\nBLOCKERS: " + ", ".join(failures) + "\nOWNER ACTION REQUIRED: Repair canonical state evidence.\nNEXT ALLOWED ACTION: ./bin/abvx book validate gd3"
        workflow, formats = state["workflow"], state["formats"]
        values = [
            ("BOOK", "Good Dogs of the Apocalypse — Book Three"),
            ("SERIES", state["series"]["name"]["value"]), ("SERIES POSITION", state["series_position"]),
            ("CURRENT STAGE", state["current_stage"]), ("CURRENT GATE", state["current_gate"]),
            ("CANON", "PASS"), ("CONCEPT", workflow["concept"]), ("ARCHITECTURE", workflow["architecture"]),
            ("DRAFT", workflow["draft"]), ("DEVELOPMENTAL", workflow["developmental"]),
            ("COMPRESSION INTEGRITY", workflow["compression_integrity"]), ("LINE EDIT", workflow["line_edit"]),
            ("TEXT LOCK", state["text_lock"]["status"]), ("ILLUSTRATIONS", state["illustrations"]["status"]),
            ("KINDLE", formats["kindle"]["local_qa"]["state"]), ("PAPERBACK", formats["paperback"]["local_qa"]["state"]),
            ("COVER", state["cover"]["status"]), ("METADATA", workflow["metadata"]),
            ("KDP KINDLE PREVIEW", formats["kindle"]["kdp_preview"]["state"]),
            ("KDP PRINT PREVIEW", formats["paperback"]["kdp_preview"]["state"]), ("PUBLICATION", state["publication"]),
            ("BLOCKERS", "NONE BEFORE GATE A" if state["current_stage"] == "NOT_STARTED" else "Run stage validation for current production findings"),
            ("OWNER ACTION REQUIRED", state["owner_action_required"]), ("NEXT ALLOWED ACTION", state["next_allowed_action"]),
        ]
        return "\n".join(f"{label}: {value}" for label, value in values)
    except (ValidationError, OSError, KeyError, TypeError) as exc:
        return f"BOOK: BLOCKED\nBLOCKERS: canonical state unavailable or invalid ({exc})\nOWNER ACTION REQUIRED: Repair canonical state evidence.\nNEXT ALLOWED ACTION: ./bin/abvx book validate gd3"


def core_adapter(project_root: Path, stage: str = "all") -> BookAdapter:
    """Expose the legacy GD3 record through the generic read-only facade."""
    return BookAdapter(BOOK_ID, "SERIES_FICTION", lambda: render_status(project_root),
                       lambda: evaluate(project_root, stage))


def append_event(project_root: Path, event: dict[str, Any]) -> None:
    path = project_root / EVENT_NAME
    events = _read_events(project_root)
    if any(item["event_id"] == event.get("event_id") for item in events):
        raise ValidationError(f"event_id already exists: {event.get('event_id')}")
    expected_id = f"gd3-{len(events) + 1:04d}"
    if event.get("event_id") != expected_id:
        raise ValidationError(f"next event_id must be {expected_id}")
    state = load_json(project_root / STATE_NAME)
    if event.get("book_id") != BOOK_ID or state.get("event_cursor") != expected_id:
        raise ValidationError("new event must identify gd3 and the canonical state event_cursor")
    if event.get("previous_state") != events[-1]["new_state"] or event.get("new_state") != state_projection(state):
        raise ValidationError("append-only event must reference the current state snapshot; state transitions are not implemented in this foundation")
    schema_path = _event_schema_path(project_root)
    validate(event, load_json(schema_path), schema_path=schema_path, root=project_root, location="new_event")
    for ref in event["evidence"]:
        if not _verified_ref(project_root, ref):
            raise ValidationError("refusing append: missing or changed evidence")
    old = event["previous_state"].get("retailer_states", {fmt: "NOT_STARTED" for fmt in ("kindle", "paperback")})
    for fmt, new in event["new_state"].get("retailer_states", old).items():
        validate_retailer_transition(old[fmt], new, evidence_available=bool(event["evidence"]),
                                     owner_authorized=event["owner_gate"] == "F" and event["actor"].lower() == "owner" and event.get("format") == fmt)
    encoded = (json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    if path.read_bytes() and not path.read_bytes().endswith(b"\n"):
        raise ValidationError("event ledger lacks final newline; refusing append to preserve line integrity")
    fd = os.open(path, os.O_WRONLY | os.O_APPEND)
    try:
        if os.write(fd, encoded) != len(encoded):
            raise OSError("partial ledger append; validation will fail closed")
        os.fsync(fd)
    finally:
        os.close(fd)


def build_id(book_id: str, *, text_lock_sha256: str, asset_manifest_sha256: str,
             production_config: dict[str, Any], tool_version: str) -> str:
    for name, value in (("text_lock_sha256", text_lock_sha256), ("asset_manifest_sha256", asset_manifest_sha256)):
        if not HEX_SHA256.fullmatch(value):
            raise ValidationError(f"{name} must be a lowercase SHA-256")
    if book_id != BOOK_ID or not tool_version:
        raise ValidationError("invalid book_id or empty tool_version")
    fingerprint = {"book_id": book_id, "text_lock_sha256": text_lock_sha256,
                   "asset_manifest_sha256": asset_manifest_sha256,
                   "production_config": production_config, "tool_version": tool_version}
    canonical = json.dumps(fingerprint, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return f"{book_id}-{sha256_bytes(canonical)}"


def build_directory(project_root: Path, build_id_value: str) -> Path:
    if not re.fullmatch(r"gd3-[a-f0-9]{64}", build_id_value):
        raise ValidationError("build_id must be gd3- followed by the full deterministic SHA-256 fingerprint")
    return project_root / "production" / "book-three" / "builds" / build_id_value


def create_build_directory(project_root: Path, book_id: str, *, text_lock_sha256: str,
                           asset_manifest_sha256: str, production_config: dict[str, Any],
                           tool_version: str) -> Path:
    value = build_id(book_id, text_lock_sha256=text_lock_sha256,
                     asset_manifest_sha256=asset_manifest_sha256,
                     production_config=production_config, tool_version=tool_version)
    destination = build_directory(project_root, value)
    destination.mkdir(parents=True, exist_ok=False)
    return destination


def make_build_record(project_root: Path, *, text_lock_ref: dict[str, str], asset_manifest_ref: dict[str, str],
                      production_config: dict[str, Any], tool_version: str,
                      output_refs: list[dict[str, str]], validator_records: list[dict[str, Any]]) -> dict[str, Any]:
    """Describe a future immutable build; never creates outputs or claims KDP success."""
    refs = [text_lock_ref, asset_manifest_ref, *output_refs]
    if not output_refs or not validator_records or any(not _verified_ref(project_root, ref) for ref in refs):
        raise ValidationError("build record requires existing hash-verified inputs, outputs and validators")
    for result in validator_records:
        validate(result, load_json(_result_schema_path(project_root)), schema_path=_result_schema_path(project_root), root=project_root)
        if result["state"] in {"PASS", "OWNER_ACCEPTED_EXCEPTION"}:
            proof = _local_file(project_root, result["evidence_path"])
            if not proof or not proof.is_file() or not result["input_sha256"] or not all(HEX_SHA256.fullmatch(v) for v in result["input_sha256"] + result["output_sha256"]):
                raise ValidationError("build validator cannot claim PASS without evidence and input hashes")
    value = build_id(BOOK_ID, text_lock_sha256=text_lock_ref["sha256"], asset_manifest_sha256=asset_manifest_ref["sha256"],
                     production_config=production_config, tool_version=tool_version)
    return {"schema_version": "good-dog-build/v1", "build_id": value, "text_lock": text_lock_ref,
            "asset_manifest": asset_manifest_ref, "production_config": production_config,
            "production_config_sha256": sha256_bytes(json.dumps(production_config, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()),
            "tool_version": tool_version, "outputs": output_refs, "validators": validator_records}
