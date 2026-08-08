#!/usr/bin/env python3
"""Bounded CoqPi onboarding pilot through the ABVX mission-state boundary.

This is fixture-specific evidence code, not a reusable orchestrator.  LoopX is
invoked only for mission-local state; the ABVX provider owns integrity checks,
gates, normalized export, and recovery evidence.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from abvx_harness.mission_state import (  # noqa: E402
    LoopXMissionStateProvider,
    MissionIntegrityError,
    MissionTerminalError,
)


MISSION_ID = "COQPI-CALL-READY-001"
OBJECTIVE = "Make CoqPi call-ready for a real professional call."
GATE_ID = "human-review-of-live-call-risk"
SLICE = "Prevent readiness UI from claiming real-mic readiness before the realtime path is ready."


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


class LoopXTodoBackend:
    """Small adapter translating LoopX todos to the ABVX normalized contract."""

    def __init__(self, run_dir: Path):
        source = os.environ.get("ABVX_LOOPX_SOURCE")
        if not source:
            raise RuntimeError("ABVX_LOOPX_SOURCE is required")
        self.run_dir = run_dir
        self.project = run_dir / "loopx-project"
        self.runtime = run_dir / "loopx-runtime"
        self.registry = self.project / ".loopx" / "registry.json"
        self.state_file = self.project / ".codex" / "goals" / MISSION_ID / "ACTIVE_GOAL_STATE.md"
        self.meta_path = run_dir / "adapter-metadata.json"
        self.raw_snapshot_dir = run_dir / "loopx-state-snapshots"
        self.source = Path(source)

    def call(self, arguments: list[str], *, allow_failure: bool = False) -> dict[str, Any]:
        command = [
            sys.executable,
            "-c",
            "from loopx.entrypoint import main; raise SystemExit(main())",
            "--format",
            "json",
            "--registry",
            str(self.registry),
            "--runtime-root",
            str(self.runtime),
            *arguments,
        ]
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(self.source)
        completed = subprocess.run(
            command,
            cwd=self.project if self.project.exists() else None,
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        try:
            payload = json.loads(completed.stdout) if completed.stdout.strip() else {}
        except json.JSONDecodeError as exc:
            lines = [line for line in completed.stdout.splitlines() if line.strip()]
            try:
                payload = json.loads(lines[-1]) if lines else {}
            except json.JSONDecodeError:
                payload = {"stdout": completed.stdout, "stderr": completed.stderr}
                if not allow_failure:
                    raise RuntimeError(f"LoopX returned non-JSON output: {payload}") from exc
        if completed.returncode != 0 and not allow_failure:
            raise RuntimeError(f"LoopX command failed: {arguments}: {payload}")
        payload["returncode"] = completed.returncode
        return payload

    def assert_raw_state(self) -> None:
        try:
            raw = self.state_file.read_text(encoding="utf-8")
        except OSError as exc:
            raise MissionIntegrityError(f"LoopX state is unreadable: {self.state_file}") from exc
        required = ("# Active Goal State", "## Objective", "adapter_id:")
        if not all(marker in raw for marker in required) or MISSION_ID not in raw:
            raise MissionIntegrityError("LoopX state failed the adapter structure check")

    def todos(self) -> list[dict[str, Any]]:
        self.assert_raw_state()
        payload = self.call(
            [
                "todo",
                "list",
                "--goal-id",
                MISSION_ID,
                "--state-file",
                str(self.state_file),
                "--project",
                str(self.project),
            ]
        )
        return payload.get("todos", [])

    def save_raw_snapshot(self, revision: int) -> None:
        self.raw_snapshot_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.state_file, self.raw_snapshot_dir / f"{revision:020d}.md")

    def metadata(self) -> dict[str, Any]:
        if not self.meta_path.exists():
            return {"revision": 0, "status": "new", "gates": [], "terminal": False, "waiting_for_human": False}
        return json.loads(self.meta_path.read_text(encoding="utf-8"))

    def normalized_todos(self) -> list[dict[str, Any]]:
        return [
            {
                "id": item.get("todo_id"),
                "text": item.get("text"),
                "role": item.get("role", "agent"),
                "status": item.get("status"),
                "evidence": item.get("evidence", []),
            }
            for item in self.todos()
        ]

    def create(self, state: dict[str, Any]) -> None:
        self.project.mkdir(parents=True, exist_ok=True)
        self.call(
            [
                "bootstrap",
                "--project",
                str(self.project),
                "--goal-id",
                MISSION_ID,
                "--objective",
                OBJECTIVE,
                "--domain",
                "development",
                "--no-onboarding-scan",
                "--no-global-sync",
            ]
        )
        self.write(state)

    def read(self, mission_id: str) -> dict[str, Any] | None:
        self.assert_raw_state()
        meta = self.metadata()
        normalized = self.normalized_todos()
        gates = [dict(gate) for gate in meta.get("gates", [])]
        status = "completed" if meta.get("terminal") else ("waiting_for_human" if meta.get("waiting_for_human") else meta.get("status", "active"))
        return {
            "schema_version": "v1",
            "mission_id": mission_id,
            "objective": OBJECTIVE,
            "status": status,
            "work_state": {"todos": normalized},
            "gates": gates,
            "retry": {"attempt": 0, "max_retries": 1},
            "evidence_refs": meta.get("evidence_refs", []),
            "quota": {"timeout_seconds": 900, "token_budget": None, "cost_budget": None},
            "waiting_for_human": bool(meta.get("waiting_for_human")),
            "terminal": bool(meta.get("terminal")),
            "revision": int(meta.get("revision", 0)),
        }

    def ensure_todo(self, text: str, role: str = "agent") -> dict[str, Any]:
        for item in self.todos():
            if item.get("text") == text:
                return item
        arguments = [
            "todo",
            "add",
            "--goal-id",
            MISSION_ID,
            "--role",
            role,
            "--text",
            text,
            "--state-file",
            str(self.state_file),
            "--project",
            str(self.project),
            "--task-class",
            "user_gate" if role == "user" else "advancement_task",
        ]
        if role == "user":
            arguments += ["--decision-scope", "direction:action:call_readiness"]
        result = self.call(arguments)
        self.save_raw_snapshot(self.metadata().get("revision", 0))
        return result

    def complete_todo(self, item: dict[str, Any], evidence: str, decision: str | None = None) -> None:
        arguments = [
            "todo",
            "complete",
            "--goal-id",
            MISSION_ID,
            "--todo-id",
            item["todo_id"],
            "--role",
            item.get("role", "agent"),
            "--evidence",
            evidence,
            "--state-file",
            str(self.state_file),
            "--project",
            str(self.project),
        ]
        if decision:
            arguments += ["--decision-outcome", decision]
        self.call(arguments)

    def write(self, state: dict[str, Any]) -> None:
        for gate in state.get("gates", []):
            if gate["id"] == GATE_ID:
                item = self.ensure_todo("Human review of live-call risk", role="user")
                if gate["status"] == "approved":
                    if item.get("status") != "done":
                        self.complete_todo(item, "human approval recorded by ABVX boundary", "approve")
                elif gate["status"] == "rejected" and item.get("status") != "done":
                    self.call(
                        [
                            "todo",
                            "update",
                            "--goal-id",
                            MISSION_ID,
                            "--todo-id",
                            item["todo_id"],
                            "--role",
                            "user",
                            "--status",
                            "blocked",
                            "--reason",
                            "human rejected",
                            "--state-file",
                            str(self.state_file),
                            "--project",
                            str(self.project),
                        ]
                    )
        revision = int(state["revision"])
        metadata = {
            "revision": revision,
            "status": state["status"],
            "gates": state.get("gates", []),
            "terminal": state["terminal"],
            "waiting_for_human": state["waiting_for_human"],
            "evidence_refs": state.get("evidence_refs", []),
        }
        atomic_json(self.meta_path, metadata)
        self.assert_raw_state()
        self.save_raw_snapshot(revision)

    def restore(self, state: dict[str, Any]) -> None:
        candidates = sorted(self.raw_snapshot_dir.glob("*.md"), reverse=True)
        if not candidates:
            raise MissionIntegrityError("LoopX adapter has no raw recovery snapshot")
        shutil.copy2(candidates[0], self.state_file)
        self.write(state)

    def corrupt_raw_state(self) -> None:
        self.state_file.write_text("corrupted LoopX state\n", encoding="utf-8")


def main() -> int:
    run_dir = Path(os.environ.get("ABVX_HARNESS_RUN_DIR", Path.cwd() / ".pilot-run"))
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True)
    boundary = run_dir / "abvx-boundary"
    schema = ROOT / "schemas" / "mission_state_export.schema.json"
    backend = LoopXTodoBackend(run_dir)
    provider = LoopXMissionStateProvider(backend, boundary, schema)
    checks: dict[str, bool] = {}

    created = provider.create_mission(mission_id=MISSION_ID, objective=OBJECTIVE, quota={"timeout_seconds": 900}, max_retries=1)
    checks["fresh_mission"] = created["status"] == "new"
    backend.ensure_todo("Verify the corrected real-mic readiness gate")
    recorded = provider.record_state(
        MISSION_ID,
        {
            "work_state": {"technical_slice": SLICE, "test_commands": ["pnpm test:pass2-live-smoke-readiness", "pnpm typecheck"]},
            "evidence_refs": ["coqpi-readiness-regression", "coqpi-targeted-tests"],
        },
    )
    checks["normalized_work_state"] = recorded["work_state"]["technical_slice"] == SLICE

    waiting = provider.wait_for_gate(MISSION_ID, GATE_ID)
    try:
        provider.resume(MISSION_ID)
    except MissionIntegrityError:
        checks["gate_blocks_resume"] = True
    else:
        checks["gate_blocks_resume"] = False

    backend.corrupt_raw_state()
    try:
        provider.inspect_mission(MISSION_ID)
    except MissionIntegrityError:
        checks["corruption_fails_closed"] = True
    else:
        checks["corruption_fails_closed"] = False
    recovery = provider.recover(MISSION_ID)
    checks["recovery_succeeds"] = recovery["state"]["gates"][0]["status"] == "open"
    checks["gate_remains_closed_after_recovery"] = False
    try:
        provider.resume(MISSION_ID)
    except MissionIntegrityError:
        checks["gate_remains_closed_after_recovery"] = True

    provider.approve_gate(MISSION_ID, GATE_ID, approved=True)
    provider.resume(MISSION_ID)
    completed = provider.complete(MISSION_ID)
    checks["complete"] = completed["terminal"] and completed["status"] == "completed"
    try:
        provider.resume(MISSION_ID)
    except MissionTerminalError:
        checks["terminal_cannot_restart"] = True
    else:
        checks["terminal_cannot_restart"] = False

    exported = provider.export_state(MISSION_ID)
    def export_keys(value: Any) -> set[str]:
        if isinstance(value, dict):
            return set(value) | {key for item in value.values() for key in export_keys(item)}
        if isinstance(value, list):
            return {key for item in value for key in export_keys(item)}
        return set()

    checks["export_is_normalized"] = not {"todo_id", "state_file", "registry"} & export_keys(exported)
    payload = {
        "schema_version": "v1",
        "mission_id": MISSION_ID,
        "candidate": "loopx",
        "provider_boundary": "abvx.LoopXMissionStateProvider",
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "recovery_evidence": recovery["evidence"],
        "export": exported,
        "external_execution": "not_run",
        "stop_state": "STOP_FOR_HUMAN_DECISION",
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
