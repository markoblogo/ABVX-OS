#!/usr/bin/env python3
"""Fixture-specific mission-control comparison; not a reusable orchestration layer."""

from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


MISSION_ID = "mission-control-001"
INTERRUPTED = 75
STEPS = ["audio-input", "live-transcription", "context-loading", "suggested-response", "fallback-path"]


def emit(payload: dict, code: int = 0) -> int:
    print(json.dumps(payload, sort_keys=True))
    return code


def run_child(provider: str, phase: str) -> tuple[int, dict]:
    command = [sys.executable, __file__, "--provider", provider, "--phase", phase, "--child"]
    completed = subprocess.run(command, capture_output=True, text=True, env=os.environ.copy(), check=False)
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    payload = json.loads(lines[-1]) if lines else {"stdout": completed.stdout, "stderr": completed.stderr}
    return completed.returncode, payload


def native_paths() -> tuple[Path, Path]:
    run_dir = Path(os.environ["ABVX_HARNESS_RUN_DIR"])
    state_dir = run_dir / "native-state"
    return state_dir, state_dir / "state.json"


def native_initial() -> dict:
    return {"schema_version": "mission-control-fixture-v1", "mission_id": MISSION_ID, "status": "active", "gate": "none", "steps": {step: {"status": "open", "attempts": 0, "evidence": []} for step in STEPS}, "budget": {"max_retries": 1, "token_budget": None, "cost_budget": None}, "side_effects": [], "events": []}


def write_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def load_state(path: Path) -> dict:
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"native checkpoint unreadable: {exc}") from exc
    if state.get("mission_id") != MISSION_ID or not isinstance(state.get("steps"), dict):
        raise RuntimeError("native checkpoint incomplete")
    return state


def native_step(state: dict, step: str, *, evidence: str, effect: str) -> None:
    item = state["steps"][step]
    if item["status"] == "pass":
        return
    item["attempts"] += 1
    item["status"] = "pass"
    item["evidence"].append(evidence)
    if effect not in state["side_effects"]:
        state["side_effects"].append(effect)
    state["events"].append({"step": step, "status": "pass", "attempt": item["attempts"], "evidence": evidence})


def native_child(phase: str) -> int:
    state_dir, state_path = native_paths()
    if phase == "interrupt":
        state = native_initial()
        native_step(state, "audio-input", evidence="simulated-audio-pass", effect="audio-check")
        write_state(state_path, state)
        return emit({"phase": phase, "state_mutated": True, "interrupted_before": "live-transcription"}, INTERRUPTED)
    state = load_state(state_path)
    if phase == "resume":
        native_step(state, "audio-input", evidence="resume-found-existing-pass", effect="audio-check")
        item = state["steps"]["live-transcription"]
        if item["status"] != "pass":
            item["attempts"] += 1
            item["status"] = "fail"
            item["evidence"].append("simulated-realtime-failure")
            state["events"].append({"step": "live-transcription", "status": "fail", "attempt": item["attempts"]})
            write_state(state_path, state)
            if item["attempts"] > state["budget"]["max_retries"]:
                raise RuntimeError("retry budget exhausted")
            item["attempts"] += 1
            item["status"] = "pass"
            item["evidence"].append("simulated-realtime-retry-pass")
            state["events"].append({"step": "live-transcription", "status": "pass", "attempt": item["attempts"]})
        native_step(state, "context-loading", evidence="simulated-context-pass", effect="context-check")
        native_step(state, "suggested-response", evidence="simulated-response-pass", effect="response-check")
        state["steps"]["fallback-path"]["status"] = "blocked_pending_human_decision"
        state["gate"] = "pending"
        state["events"].append({"step": "fallback-path", "status": "blocked_pending_human_decision"})
        write_state(state_path, state)
        return emit({"phase": phase, "gate": state["gate"], "continued_past_gate": False, "retry_passed": state["steps"]["live-transcription"]["attempts"] == 2})
    if phase == "inspect":
        return emit({"phase": phase, "gate": state["gate"], "unauthorized_continuation": state["steps"]["fallback-path"]["status"] != "blocked_pending_human_decision"})
    if phase == "approve":
        state["gate"] = "approved"
        state["events"].append({"step": "human-decision", "status": "approved", "evidence": "simulated-owner-approval"})
        write_state(state_path, state)
        return emit({"phase": phase, "gate": state["gate"]})
    if phase == "resume-after-approval":
        if state["gate"] != "approved":
            raise RuntimeError("resume attempted without approval")
        native_step(state, "fallback-path", evidence="simulated-fallback-pass-after-approval", effect="fallback-check")
        state["status"] = "completed"
        state["events"].extend([{ "step": "evidence", "status": "pass" }, {"step": "complete", "status": "pass"}])
        write_state(state_path, state)
        return emit({"phase": phase, "status": state["status"]})
    if phase == "rerun":
        before = copy.deepcopy(state["side_effects"])
        native_step(state, "audio-input", evidence="rerun-noop", effect="audio-check")
        write_state(state_path, state)
        return emit({"phase": phase, "duplicate_side_effect": before != state["side_effects"]})
    if phase == "corrupt":
        corrupted = state_path.with_name("corrupt-state.json")
        corrupted.write_text("{broken", encoding="utf-8")
        try:
            load_state(corrupted)
        except RuntimeError:
            corrupted.unlink()
            return emit({"phase": phase, "corruption_rejected": True})
        raise RuntimeError("corrupt state was accepted")
    if phase == "cleanup":
        shutil.rmtree(state_dir)
        return emit({"phase": phase, "cleaned": not state_dir.exists()})
    raise RuntimeError(f"unknown native phase: {phase}")


def loopx_source() -> Path:
    value = os.environ.get("ABVX_LOOPX_SOURCE")
    if not value:
        raise RuntimeError("ABVX_LOOPX_SOURCE is required for LoopX fixture")
    return Path(value)


def loopx_context() -> tuple[Path, Path, Path]:
    run_dir = Path(os.environ["ABVX_HARNESS_RUN_DIR"])
    project = run_dir / "loopx-project"
    runtime = run_dir / "loopx-runtime"
    registry = project / ".loopx" / "registry.json"
    return project, runtime, registry


def loopx_call(arguments: list[str], *, allow_failure: bool = False) -> dict:
    project, runtime, registry = loopx_context()
    command = [sys.executable, "-c", "from loopx.entrypoint import main; raise SystemExit(main())", "--format", "json", "--registry", str(registry), "--runtime-root", str(runtime), *arguments]
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(loopx_source())
    completed = subprocess.run(command, cwd=project if project.exists() else None, env=environment, capture_output=True, text=True, check=False)
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        lines = [line for line in completed.stdout.splitlines() if line.strip()]
        payload = json.loads(lines[-1]) if lines and lines[-1].lstrip().startswith("{") else {"stdout": completed.stdout, "stderr": completed.stderr}
    if completed.returncode != 0 and not allow_failure:
        raise RuntimeError(f"LoopX command failed: {arguments}: {payload}")
    payload["returncode"] = completed.returncode
    return payload


def loopx_state() -> Path:
    project, _, _ = loopx_context()
    return project / ".codex" / "goals" / MISSION_ID / "ACTIVE_GOAL_STATE.md"


def loopx_todos() -> list[dict]:
    payload = loopx_call(["todo", "list", "--goal-id", MISSION_ID, "--state-file", str(loopx_state()), "--project", str(loopx_context()[0])])
    return payload.get("todos", [])


def loopx_todo(text: str, role: str = "agent") -> dict:
    for item in loopx_todos():
        if item.get("text") == text:
            return item
    arguments = ["todo", "add", "--goal-id", MISSION_ID, "--role", role, "--text", text, "--state-file", str(loopx_state()), "--project", str(loopx_context()[0])]
    arguments += ["--task-class", "user_gate" if role == "user" else "advancement_task"]
    if role == "user":
        arguments += ["--decision-scope", "direction:action:fallback_strategy"]
    return loopx_call(arguments)


def loopx_complete(item: dict, evidence: str, *, decision: str | None = None) -> dict:
    arguments = ["todo", "complete", "--goal-id", MISSION_ID, "--todo-id", item["todo_id"], "--role", item.get("role", "agent"), "--evidence", evidence, "--state-file", str(loopx_state()), "--project", str(loopx_context()[0])]
    if decision:
        arguments += ["--decision-outcome", decision]
    return loopx_call(arguments)


def loopx_child(phase: str) -> int:
    project, runtime, registry = loopx_context()
    if phase == "interrupt":
        project.mkdir(parents=True, exist_ok=True)
        loopx_call(["bootstrap", "--project", str(project), "--goal-id", MISSION_ID, "--objective", "Make CoqPi call-ready for a real professional call.", "--domain", "development", "--no-onboarding-scan", "--no-global-sync"])
        loopx_todo("Verify audio input")
        loopx_todo("Verify live transcription")
        loopx_todo("Verify company/person context loading")
        loopx_todo("Verify suggested-response path")
        loopx_complete(loopx_todo("Verify audio input"), "simulated-audio-pass")
        return emit({"phase": phase, "state_mutated": True, "interrupted_before": "live-transcription"}, INTERRUPTED)
    if phase == "resume":
        audio = loopx_todo("Verify audio input")
        before = loopx_complete(audio, "resume-found-existing-pass", decision=None)
        transcription = loopx_todo("Verify live transcription")
        loopx_call(["todo", "update", "--goal-id", MISSION_ID, "--todo-id", transcription["todo_id"], "--role", "agent", "--status", "blocked", "--reason", "simulated-realtime-failure", "--evidence", "attempt-1-fail", "--state-file", str(loopx_state()), "--project", str(project)])
        loopx_call(["todo", "update", "--goal-id", MISSION_ID, "--todo-id", transcription["todo_id"], "--role", "agent", "--status", "open", "--note", "bounded retry", "--state-file", str(loopx_state()), "--project", str(project)])
        loopx_complete(loopx_todo("Verify live transcription"), "simulated-realtime-retry-pass")
        loopx_complete(loopx_todo("Verify company/person context loading"), "simulated-context-pass")
        loopx_complete(loopx_todo("Verify suggested-response path"), "simulated-response-pass")
        loopx_todo("Approve a proposed fallback strategy", role="user")
        transcription_status = next((item.get("status") for item in loopx_todos() if item.get("text") == "Verify live transcription"), None)
        return emit({"phase": phase, "gate": "pending", "continued_past_gate": False, "retry_passed": transcription_status == "done", "rerun_completed": before.get("status")})
    if phase == "inspect":
        todos = loopx_todos()
        gates = [item for item in todos if item.get("role") == "user" and item.get("status") == "open"]
        return emit({"phase": phase, "gate": "pending" if gates else "missing", "unauthorized_continuation": not bool(gates)})
    if phase == "approve":
        gate = loopx_todo("Approve a proposed fallback strategy", role="user")
        loopx_complete(gate, "simulated-owner-approval", decision="approve")
        return emit({"phase": phase, "gate": "approved"})
    if phase == "resume-after-approval":
        if not any(item.get("status") == "done" and item.get("text") == "Approve a proposed fallback strategy" for item in loopx_todos()):
            raise RuntimeError("LoopX gate was not approved")
        fallback = loopx_todo("Verify fallback path when realtime transcription fails")
        loopx_complete(fallback, "simulated-fallback-pass-after-approval")
        evidence = loopx_todo("Attach evidence and complete mission")
        loopx_complete(evidence, "simulated-complete-evidence")
        return emit({"phase": phase, "status": "completed"})
    if phase == "rerun":
        audio = loopx_todo("Verify audio input")
        repeat = loopx_complete(audio, "rerun-noop")
        return emit({"phase": phase, "duplicate_side_effect": repeat.get("status") not in {"done", "already_done"}, "response": repeat.get("status")})
    if phase == "corrupt":
        corrupted = loopx_state().with_name("corrupt-state.md")
        corrupted.write_text("not valid loopx state\n", encoding="utf-8")
        payload = loopx_call(["todo", "list", "--goal-id", MISSION_ID, "--state-file", str(corrupted), "--project", str(project)], allow_failure=True)
        corrupted.unlink()
        return emit({"phase": phase, "corruption_rejected": payload.get("returncode") != 0, "corruption_result": payload.get("todo_count")})
    if phase == "cleanup":
        shutil.rmtree(project)
        shutil.rmtree(runtime, ignore_errors=True)
        return emit({"phase": phase, "cleaned": not project.exists() and not runtime.exists()})
    raise RuntimeError(f"unknown LoopX phase: {phase}")


def parent(provider: str) -> int:
    records: dict[str, object] = {"provider": provider, "mission_id": MISSION_ID, "fresh_process_resume": True, "checks": {}}
    code, _ = run_child(provider, "interrupt")
    records["interruption_exit_status"] = code
    if code != INTERRUPTED:
        raise RuntimeError(f"expected simulated interruption {INTERRUPTED}, got {code}")
    for phase in ("resume", "inspect"):
        code, payload = run_child(provider, phase)
        if code != 0:
            raise RuntimeError(f"{phase} failed: {payload}")
        if phase == "inspect":
            records["checks"]["gate_blocks_unauthorized_continuation"] = payload.get("unauthorized_continuation") is False
            records["gate_state"] = payload.get("gate")
        if phase == "resume":
            records["checks"]["retry_correctness"] = payload.get("retry_passed") is True
    code, _ = run_child(provider, "approve")
    if code != 0:
        raise RuntimeError("approval phase failed")
    code, payload = run_child(provider, "resume-after-approval")
    if code != 0:
        raise RuntimeError("resume-after-approval phase failed")
    records["checks"]["clean_completion"] = payload.get("status") == "completed"
    code, payload = run_child(provider, "rerun")
    if code != 0:
        raise RuntimeError("rerun phase failed")
    records["checks"]["no_duplicate_side_effect_after_resume"] = payload.get("duplicate_side_effect") is False
    code, payload = run_child(provider, "corrupt")
    if code != 0:
        raise RuntimeError("corruption phase failed")
    records["checks"]["corrupted_state_handling"] = payload.get("corruption_rejected") is True
    code, payload = run_child(provider, "cleanup")
    if code != 0:
        raise RuntimeError("cleanup phase failed")
    records["checks"]["cleanup"] = payload.get("cleaned") is True
    records["result"] = "PASS" if all(records["checks"].values()) else "INCONCLUSIVE"
    records["budget"] = {"max_retries": 1, "token_budget": None, "cost_budget": None}
    records["evidence"] = ["stdout phase reports", "candidate state files", "fresh-process exit and resume observations"]
    return emit(records)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["native", "loopx"], required=True)
    parser.add_argument("--phase", default="run", choices=["run", "interrupt", "resume", "inspect", "approve", "resume-after-approval", "rerun", "corrupt", "cleanup"])
    parser.add_argument("--child", action="store_true")
    args = parser.parse_args()
    try:
        if not args.child:
            return parent(args.provider)
        return native_child(args.phase) if args.provider == "native" else loopx_child(args.phase)
    except (OSError, RuntimeError, KeyError, json.JSONDecodeError) as exc:
        return emit({"ok": False, "error": str(exc)}, 1)


if __name__ == "__main__":
    raise SystemExit(main())
