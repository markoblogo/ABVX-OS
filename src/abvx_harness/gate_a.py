"""Bounded GD3 concept start/review transitions; never approve Gate A or drafting."""
from __future__ import annotations

import copy
import fcntl
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from . import book_three as gd3
from .harness import ValidationError, load_json
from .protected_snapshots import recheck_snapshot
from .schema_validation import load_draft_2020_12_validator


PACKETS = ("GOOD_DOG_BOOK_THREE_CANONICAL_CONTEXT_V1.md",
           "GOOD_DOG_BOOK_THREE_STORY_ENGINES_V1.md",
           "GOOD_DOG_BOOK_THREE_GATE_A_DECISION_PACKET_V1.md")
ENGINE_LOCK = "GOOD_DOG_BOOK_THREE_STORY_ENGINE_LOCK_V1.md"
ARCHITECTURE = "GOOD_DOG_BOOK_THREE_CAUSAL_ARCHITECTURE_V1.md"
ARCHITECTURE_QA = "GOOD_DOG_BOOK_THREE_ARCHITECTURE_QA_V1.md"


def transition(root: Path, action: str, authorization: str, snapshot: str) -> dict:
    if action not in {"start", "review", "select", "architecture-review"}:
        raise ValidationError("unsupported bounded Gate A action")
    project = root / "books" / "rn10-003"
    proof = gd3._local_file(project, authorization)
    if proof is None or not proof.is_file():
        raise ValidationError("local owner authorization evidence required")
    required = ("GATE_A_START_AUTHORIZED: YES",) if action in {"start", "review"} else (
        "ENGINE_SELECTION: C_WITH_A_ACCIDENT_CLAIM", "ARCHITECTURE_DEVELOPMENT_AUTHORIZED: YES",
        "PROSE_DRAFTING_AUTHORIZED: NO")
    if any(marker not in proof.read_text().splitlines() for marker in required):
        raise ValidationError("authorization evidence lacks explicit bounded permission")
    lock_dir = root / ".tmp"
    lock_dir.mkdir(exist_ok=True)
    with (lock_dir / "gd3-gate-a.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        return _transition_locked(root, project, action, authorization, snapshot)


def _transition_locked(root, project, action, authorization, snapshot):
    checked = recheck_snapshot(root, snapshot)
    entries = {item["path"]: item for item in checked["files"]}
    prefix = "books/rn10-003/"
    mutable = {prefix + gd3.STATE_NAME, prefix + gd3.EVENT_NAME}
    if not mutable.issubset(entries):
        raise ValidationError("snapshot must include canonical GD3 state and ledger")
    if any(item["status"] != "UNCHANGED" for path, item in entries.items() if path not in mutable):
        raise ValidationError("immutable protected input changed or missing")
    if action in {"start", "select"} and any(item["status"] != "UNCHANGED" for item in entries.values()):
        raise ValidationError("pre-run snapshot must match every protected file at start")
    state_path, ledger_path = project / gd3.STATE_NAME, project / gd3.EVENT_NAME
    before_state, before_ledger = state_path.read_bytes(), ledger_path.read_bytes()
    state = json.loads(before_state)
    events = gd3._read_events(project)
    state_validator = load_draft_2020_12_validator(gd3._state_schema_path(project))
    state_validator.validate(state)
    if events[-1]["new_state"] != gd3.state_projection(state) or events[-1]["event_id"] != state["event_cursor"]:
        raise ValidationError("canonical state/ledger mismatch; no transition permitted")
    if not before_ledger.endswith(b"\n"):
        raise ValidationError("ledger must retain its final newline")
    now = datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
    snapshot_data = load_json(root / snapshot)
    if snapshot_data["captured_at"] > now:
        raise ValidationError("pre-run snapshot is later than transition start")
    next_state = copy.deepcopy(state)
    evidence = [{"path": authorization, "sha256": gd3.sha256_file(project / authorization)}]
    actor, stage = "orchestrator", "CONCEPT_DEVELOPMENT"
    outputs = []
    decision = "Owner-authorized concept development; Gate A selection remains pending."
    if action == "start":
        if (state["current_stage"], state["current_gate"]) != ("NOT_STARTED", "A_PENDING"):
            raise ValidationError("Gate A start requires NOT_STARTED/A_PENDING")
        next_state.update(current_stage="CONCEPT_DEVELOPMENT", current_gate="A_IN_PROGRESS", book_status="IN_PROGRESS")
        next_state["workflow"]["concept"] = "IN_PROGRESS"
        next_state["instrumentation"].update(stage_started_at=now, revision_count=0,
                                             generation_attempt_count=0, qa_rerun_count=0,
                                             api_calls=0, api_cost_usd=0)
        next_state["owner_action_required"] = "NONE DURING AUTHORIZED CONCEPT DEVELOPMENT"
        next_state["next_allowed_action"] = "DEVELOP THREE STORY ENGINES; PRESENT OWNER DECISION PACKET"
        event_type = "GATE_A_STARTED"
        notes = json.dumps({"snapshot": snapshot, "snapshot_sha256": gd3.sha256_file(root / snapshot),
                            "previous_state_file_sha256": gd3.sha256_bytes(before_state),
                            "previous_ledger_sha256": gd3.sha256_bytes(before_ledger),
                            "agent_runs": 1, "measurement_basis": "PROSPECTIVE",
                            "scope": "Start permission only; no engine approval or drafting permission."}, sort_keys=True)
    elif action == "review":
        if state["current_gate"] != "A_IN_PROGRESS" or events[-1]["event_type"] != "GATE_A_STARTED":
            raise ValidationError("review requires a recorded Gate A start; no inferred historical transition")
        start_notes = json.loads(events[-1]["notes"])
        if start_notes["snapshot"] != snapshot or start_notes["snapshot_sha256"] != gd3.sha256_file(root / snapshot):
            raise ValidationError("start snapshot provenance mismatch")
        original = {item["path"]: item["sha256"] for item in snapshot_data["files"]}
        start_line = before_ledger.splitlines(keepends=True)[-1]
        if (gd3.sha256_bytes(before_ledger[:-len(start_line)]) != original[prefix + gd3.EVENT_NAME]
                or start_notes["previous_state_file_sha256"] != original[prefix + gd3.STATE_NAME]):
            raise ValidationError("historical protected state/ledger provenance mismatch")
        for name in PACKETS:
            path = project / name
            if not path.is_file() or not path.read_text().strip():
                raise ValidationError(f"missing Gate A output: {name}")
            evidence.append({"path": name, "sha256": gd3.sha256_file(path)})
        next_state.update(current_gate="A_OWNER_REVIEW", book_status="REVIEW_REQUIRED")
        next_state["continuity_packet"] = {**evidence[1], "status": "PASS"}
        next_state["instrumentation"].update(owner_requested_at=now, generation_attempt_count=1,
                                             qa_rerun_count=1)
        next_state["owner_action_required"] = "SELECT A / B / C / REQUEST BOUNDED HYBRID / REQUEST REVISION"
        next_state["next_allowed_action"] = "AWAIT OWNER ENGINE DECISION; NO ARCHITECTURE LOCK OR DRAFTING"
        event_type = "GATE_A_OWNER_REVIEW_REQUESTED"
        notes = json.dumps({"snapshot": snapshot, "agent_runs": 1, "qa_runs": 1,
                            "generation_attempt_count": 1, "revision_count": 0,
                            "measurement_basis": "PROSPECTIVE", "api_calls": 0, "api_cost": 0,
                            "api_scope": "No separately invoked paid/model API; chat billing unknown."}, sort_keys=True)
        outputs = list(PACKETS)
    else:
        stage = "CAUSAL_ARCHITECTURE"
        if action == "select":
            if state["current_gate"] != "A_OWNER_REVIEW" or events[-1]["event_type"] != "GATE_A_OWNER_REVIEW_REQUESTED":
                raise ValidationError("selection requires the recorded owner decision boundary")
            required_files = (ENGINE_LOCK,)
        else:
            if events[-1]["event_type"] != "STORY_ENGINE_SELECTED" or state["workflow"]["architecture"] != "IN_PROGRESS":
                raise ValidationError("architecture review requires recorded engine selection")
            prior = json.loads(events[-1]["notes"])
            original = {item["path"]: item["sha256"] for item in snapshot_data["files"]}
            last_line = before_ledger.splitlines(keepends=True)[-1]
            if (prior["snapshot"] != snapshot or prior["snapshot_sha256"] != gd3.sha256_file(root / snapshot)
                    or prior["previous_state_file_sha256"] != original[prefix + gd3.STATE_NAME]
                    or gd3.sha256_bytes(before_ledger[:-len(last_line)]) != original[prefix + gd3.EVENT_NAME]):
                raise ValidationError("selection snapshot provenance mismatch")
            locked = state["workflow_evidence"]["concept"]
            if gd3.sha256_file(project / locked["path"]) != locked["sha256"]:
                raise ValidationError("selected engine lock changed")
            required_files = (ARCHITECTURE, ARCHITECTURE_QA)
        for name in required_files:
            path = project / name
            if not path.is_file() or not path.read_text().strip():
                raise ValidationError(f"missing selected-engine output: {name}")
            evidence.append({"path": name, "sha256": gd3.sha256_file(path)})
        next_state.update(current_stage=stage, current_gate="GATE_A", book_status="IN_PROGRESS")
        if action == "select":
            actor, event_type = "owner", "STORY_ENGINE_SELECTED"
            next_state["workflow"].update(concept="PASS", architecture="IN_PROGRESS")
            next_state.setdefault("workflow_evidence", {})["concept"] = evidence[1]
            next_state["instrumentation"].update(stage_started_at=now, owner_approved_at=now,
                owner_requested_at=None, stage_completed_at=None, generation_attempt_count=0, revision_count=0, qa_rerun_count=0)
            next_state["owner_action_required"] = "NONE DURING AUTHORIZED ARCHITECTURE DEVELOPMENT"
            next_state["next_allowed_action"] = "BUILD CAUSAL ARCHITECTURE FOR LOCKED C/A HYBRID; NO PROSE"
            notes = json.dumps({"snapshot": snapshot, "snapshot_sha256": gd3.sha256_file(root / snapshot),
                "previous_state_file_sha256": gd3.sha256_bytes(before_state),
                "previous_ledger_sha256": gd3.sha256_bytes(before_ledger), "agent_runs": 1,
                "scope": "Concept selected; architecture development authorized; compound Gate A and drafting NOT approved."}, sort_keys=True)
        else:
            if "ARCHITECTURE_QA: PASS" not in (project / ARCHITECTURE_QA).read_text().splitlines():
                raise ValidationError("architecture QA must record its bounded PASS")
            event_type = "CAUSAL_ARCHITECTURE_REVIEW_REQUESTED"
            next_state.update(current_gate="A_OWNER_REVIEW", book_status="REVIEW_REQUIRED")
            next_state["workflow"]["architecture"] = "PASS"
            next_state["workflow_evidence"]["architecture"] = evidence[1]
            next_state["instrumentation"].update(stage_completed_at=now, owner_requested_at=now,
                generation_attempt_count=1, qa_rerun_count=1)
            next_state["owner_action_required"] = "REVIEW CAUSAL ARCHITECTURE; ENGINE ALREADY SELECTED; PROSE NOT AUTHORIZED"
            next_state["next_allowed_action"] = "AWAIT ARCHITECTURE ACCEPTANCE AND EXPLICIT DRAFT AUTHORIZATION"
            notes = json.dumps({"snapshot": snapshot, "agent_runs": 1, "generation_attempt_count": 1,
                "revision_count": 0, "qa_runs": 1, "scope": "Local architecture QA only; no owner architecture or draft approval."}, sort_keys=True)
        outputs = list(required_files)
        decision = "C selected with one A accident-loss claim; no hearing/climax from A, no B-1/network, no prose."
    next_state["revision"] += 1
    next_state["event_cursor"] = f"gd3-{len(events)+1:04d}"
    # Compound owner gates, production, metadata and draft remain untouched.
    state_validator.validate(next_state)
    event = {"book_id": "gd3", "event_id": next_state["event_cursor"], "timestamp": now,
             "stage": stage, "event_type": event_type, "actor": actor,
             "input_refs": [authorization], "output_refs": [gd3.STATE_NAME] + outputs,
             "decision": decision,
             "previous_state": events[-1]["new_state"], "new_state": gd3.state_projection(next_state),
             "owner_gate": "A", "evidence": evidence, "notes": notes}
    load_draft_2020_12_validator(gd3._event_schema_path(project)).validate(event)
    encoded_state = (json.dumps(next_state, ensure_ascii=False, indent=2) + "\n").encode()
    encoded_event = (json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()
    # Exclusive cooperating-writer lock; failed writes roll back exact original bytes.
    # A process crash between files is detected as a mismatch, never auto-repaired.
    try:
        with state_path.open("wb") as output:
            output.write(encoded_state)
            output.flush()
            os.fsync(output.fileno())
        with ledger_path.open("ab") as output:
            output.write(encoded_event)
            output.flush()
            os.fsync(output.fileno())
        gd3._read_events(project)
    except BaseException:
        state_path.write_bytes(before_state)
        ledger_path.write_bytes(before_ledger)
        raise
    return {"current_stage": next_state["current_stage"], "current_gate": next_state["current_gate"],
            "event_id": next_state["event_cursor"], "gates_A": next_state["gates"]["A"]}
