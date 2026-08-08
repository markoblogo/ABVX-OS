#!/usr/bin/env python3
"""Record the deferred COQPI-002 pre-live gate through the ABVX boundary."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from abvx_harness.mission_state import MissionStateProvider  # noqa: E402


MISSION_ID = "COQPI-002"
OBJECTIVE = "Complete the CoqPi pre-live readiness pass and defer the first human-consented live smoke to Monday."


class NativeFileBackend:
    """Fixture-local native baseline backend; no orchestration or daemon."""

    def __init__(self, state_path: Path):
        self.state_path = state_path

    def create(self, state: dict[str, Any]) -> None:
        self.write(state)

    def read(self, mission_id: str) -> dict[str, Any] | None:
        if not self.state_path.exists():
            return None
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def write(self, state: dict[str, Any]) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.state_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(self.state_path)

    def restore(self, state: dict[str, Any]) -> None:
        self.write(state)


def main() -> int:
    output_path = Path(os.environ.get("ABVX_PRELIVE_OUTPUT", ROOT / "evidence/onboarding/project-onboarding-001/mission/COQPI-002/state-export.json"))
    boundary_dir = output_path.parent / "boundary"
    state_path = boundary_dir / "native-state.json"
    provider = MissionStateProvider(
        NativeFileBackend(state_path),
        boundary_dir,
        ROOT / "schemas/mission_state_export.schema.json",
    )
    provider.create_mission(
        mission_id=MISSION_ID,
        objective=OBJECTIVE,
        quota={"timeout_seconds": 900, "scheduled_not_before": "2026-08-10"},
        max_retries=0,
    )
    provider.record_state(
        MISSION_ID,
        {
            "work_state": {
                "readiness_status": "READY_FOR_LIVE_VALIDATION",
                "mission_status": "WAITING_FOR_HUMAN",
                "scheduled_not_before": "2026-08-10",
                "live_smoke_started": False,
                "audio_transmitted": False,
                "pre_live_blockers": [],
                "live_validation_required": [
                    "human confirms system-default input/output",
                    "one 30-90 second synthetic-speech smoke",
                    "one recoverable interruption test",
                ],
                "post_live": [
                    "classify READY_FOR_CONTROLLED_REAL_CALL, CONDITIONALLY_READY, or NOT_READY",
                ],
            },
            "evidence_refs": [
                "evidence/onboarding/project-onboarding-001/coqpi-002-pre-live.evidence.json",
                "docs/checklists/coqpi-002-monday-live.md",
            ],
        },
    )
    state = provider.wait_for_gate(MISSION_ID, "human-consented-live-microphone-smoke")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "mission_id": MISSION_ID,
        "provider_boundary": "abvx.MissionStateProvider",
        "status": state["status"],
        "readiness_status": state["work_state"]["readiness_status"],
        "scheduled_not_before": state["work_state"]["scheduled_not_before"],
        "live_smoke_started": state["work_state"]["live_smoke_started"],
        "audio_transmitted": state["work_state"]["audio_transmitted"],
        "gate": state["gates"][0],
        "output": str(output_path.relative_to(ROOT)),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
