"""Small ABVX boundary for an optional long-running mission state provider.

This module owns the contract and integrity checks, not mission orchestration.
The backend is deliberately injected so LoopX-specific state remains outside
the ABVX control plane.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from .harness import ValidationError, load_json, validate


class MissionIntegrityError(RuntimeError):
    """The known mission cannot be read as a valid, attributable state."""


class MissionTerminalError(RuntimeError):
    """A terminal mission was asked to resume or mutate."""


class MissionStateBackend(Protocol):
    """Backend seam; an adapter may translate this to LoopX later."""

    def create(self, state: dict[str, Any]) -> None: ...
    def read(self, mission_id: str) -> dict[str, Any] | None: ...
    def write(self, state: dict[str, Any]) -> None: ...
    def restore(self, state: dict[str, Any]) -> None: ...


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _canonical(value: dict[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


class MissionStateProvider:
    """Normalized, fail-closed provider facade for a mission-state backend."""

    def __init__(self, backend: MissionStateBackend, boundary_dir: Path, schema_path: Path):
        self.backend = backend
        self.boundary_dir = boundary_dir
        self.schema_path = schema_path
        self.known_path = boundary_dir / "known-missions.json"
        self.snapshot_dir = boundary_dir / "snapshots"
        self.evidence_dir = boundary_dir / "recovery-evidence"

    def create_mission(self, *, mission_id: str, objective: str, quota: dict[str, Any] | None = None, max_retries: int = 0) -> dict[str, Any]:
        if mission_id in self._known():
            raise MissionIntegrityError(f"mission already known: {mission_id}")
        state = self._state(mission_id, objective, quota or {}, max_retries)
        self.backend.create(state)
        self._mark_known(mission_id)
        return self._capture_valid(state)

    def inspect_mission(self, mission_id: str) -> dict[str, Any]:
        return self._read_known(mission_id)

    def record_state(self, mission_id: str, changes: dict[str, Any]) -> dict[str, Any]:
        state = self._read_known(mission_id)
        if state["terminal"]:
            raise MissionTerminalError(f"mission is terminal: {mission_id}")
        updated = dict(state)
        updated.update(changes)
        updated["mission_id"] = mission_id
        updated["revision"] = state["revision"] + 1
        self._validate(updated)
        self.backend.write(updated)
        return self._capture_valid(updated)

    def wait_for_gate(self, mission_id: str, gate_id: str) -> dict[str, Any]:
        state = self._read_known(mission_id)
        gates = [dict(gate) for gate in state["gates"]]
        gate = next((item for item in gates if item["id"] == gate_id), None)
        if gate is None:
            gates.append({"id": gate_id, "status": "open", "decision": None})
        state["gates"] = gates
        state["status"] = "waiting_for_human"
        state["waiting_for_human"] = True
        return self.record_state(mission_id, {"gates": gates, "status": state["status"], "waiting_for_human": True})

    def approve_gate(self, mission_id: str, gate_id: str, *, approved: bool) -> dict[str, Any]:
        state = self._read_known(mission_id)
        gates = [dict(gate) for gate in state["gates"]]
        gate = next((item for item in gates if item["id"] == gate_id), None)
        if gate is None:
            raise MissionIntegrityError(f"unknown gate: {gate_id}")
        gate["status"] = "approved" if approved else "rejected"
        gate["decision"] = "approved" if approved else "rejected"
        waiting = any(item["status"] == "open" for item in gates)
        return self.record_state(mission_id, {"gates": gates, "status": "waiting_for_human" if waiting else "active", "waiting_for_human": waiting})

    def resume(self, mission_id: str) -> dict[str, Any]:
        state = self._read_known(mission_id)
        if state["terminal"]:
            raise MissionTerminalError(f"mission is terminal: {mission_id}")
        if any(gate["status"] == "open" for gate in state["gates"]):
            raise MissionIntegrityError(f"mission gate remains open: {mission_id}")
        return self.record_state(mission_id, {"status": "active", "waiting_for_human": False})

    def complete(self, mission_id: str) -> dict[str, Any]:
        return self.record_state(mission_id, {"status": "completed", "terminal": True, "waiting_for_human": False})

    def export_state(self, mission_id: str) -> dict[str, Any]:
        return self._read_known(mission_id)

    def recover(self, mission_id: str) -> dict[str, Any]:
        if mission_id not in self._known():
            raise MissionIntegrityError(f"mission is not known: {mission_id}")
        snapshot = self._latest_valid_snapshot(mission_id)
        if snapshot is None:
            self._record_recovery(mission_id, "failed", None)
            raise MissionIntegrityError(f"no valid recovery snapshot: {mission_id}")
        self.backend.restore(snapshot)
        restored = self._read_known(mission_id)
        evidence = self._record_recovery(mission_id, "succeeded", restored["revision"])
        return {"state": restored, "evidence": evidence}

    def _state(self, mission_id: str, objective: str, quota: dict[str, Any], max_retries: int) -> dict[str, Any]:
        return {"schema_version": "v1", "mission_id": mission_id, "objective": objective, "status": "new", "work_state": {}, "gates": [], "retry": {"attempt": 0, "max_retries": max_retries}, "evidence_refs": [], "quota": quota, "waiting_for_human": False, "terminal": False, "revision": 0}

    def _known(self) -> set[str]:
        if not self.known_path.exists():
            return set()
        try:
            value = load_json(self.known_path)
        except ValidationError as exc:
            raise MissionIntegrityError("known mission index is unreadable") from exc
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise MissionIntegrityError("known mission index is corrupted")
        return set(value)

    def _mark_known(self, mission_id: str) -> None:
        _atomic_json(self.known_path, sorted(self._known() | {mission_id}))

    def _read_known(self, mission_id: str) -> dict[str, Any]:
        if mission_id not in self._known():
            raise MissionIntegrityError(f"mission is not known: {mission_id}")
        try:
            state = self.backend.read(mission_id)
        except Exception as exc:
            raise MissionIntegrityError(f"unreadable mission state: {mission_id}") from exc
        if state is None:
            raise MissionIntegrityError(f"missing mission state: {mission_id}")
        self._validate(state)
        return state

    def _validate(self, state: dict[str, Any]) -> None:
        if not isinstance(state, dict):
            raise MissionIntegrityError("mission state is not an object")
        try:
            validate(state, load_json(self.schema_path), schema_path=self.schema_path, root=self.schema_path.parent.parent, location="mission_state")
        except (ValidationError, OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise MissionIntegrityError(f"mission state failed schema validation: {exc}") from exc

    def _capture_valid(self, state: dict[str, Any]) -> dict[str, Any]:
        self._validate(state)
        digest = hashlib.sha256(_canonical(state)).hexdigest()
        snapshot = {"schema_version": "v1", "mission_id": state["mission_id"], "revision": state["revision"], "sha256": digest, "state": state}
        _atomic_json(self.snapshot_dir / state["mission_id"] / f"{state['revision']:020d}.json", snapshot)
        return state

    def _latest_valid_snapshot(self, mission_id: str) -> dict[str, Any] | None:
        paths = sorted((self.snapshot_dir / mission_id).glob("*.json"), reverse=True)
        for path in paths:
            try:
                snapshot = load_json(path)
                state = snapshot["state"]
                self._validate(state)
                if snapshot["mission_id"] != mission_id or snapshot["sha256"] != hashlib.sha256(_canonical(state)).hexdigest():
                    continue
                return state
            except (OSError, KeyError, TypeError, ValidationError, MissionIntegrityError, json.JSONDecodeError):
                continue
        return None

    def _record_recovery(self, mission_id: str, result: str, revision: int | None) -> str:
        evidence = {"schema_version": "v1", "mission_id": mission_id, "result": result, "revision": revision, "recorded_at": _now(), "source": "abvx-mission-state-integrity-boundary"}
        path = self.evidence_dir / mission_id / f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}-{result}.json"
        _atomic_json(path, evidence)
        return str(path)


class LoopXMissionStateProvider(MissionStateProvider):
    """Conditional LoopX role; the injected backend is the only coupling point."""
