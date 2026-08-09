import json
import tempfile
import unittest
from pathlib import Path

from abvx_harness.harness import run_bakeoff, validate_repository
from abvx_harness.mission_state import (
    LoopXMissionStateProvider,
    MissionIntegrityError,
    MissionTerminalError,
)


ROOT = Path(__file__).resolve().parents[1]


class HarnessTests(unittest.TestCase):
    def test_repository_documents_validate(self):
        checked = validate_repository(ROOT)
        self.assertIn("registries/projects.json", checked)
        self.assertIn("registries/donor-capability-matrix.json", checked)
        self.assertIn("registries/capability-gaps.json", checked)
        self.assertIn("observations/analytics/platform-sensors-001-targets.json", checked)
        self.assertIn("fixtures/bakeoffs/foundation-002-baseline/hello-local.json", checked)

    def test_baseline_run_captures_evidence_and_is_reproducible(self):
        with tempfile.TemporaryDirectory() as temp:
            first = run_bakeoff(ROOT, "foundation-002-baseline", Path(temp) / "evidence")
            result = json.loads((first / "result.json").read_text())
            evidence = json.loads(next(first.glob("*.evidence.json")).read_text())
            stdout = next(first.glob("*.stdout")).read_text()
            self.assertEqual(result["result"], "PASS")
            self.assertEqual(result["decision_state"], "STOP_FOR_HUMAN_DECISION")
            self.assertEqual(evidence["result"], "PASS")
            self.assertEqual(evidence["metrics"]["exit_status"], 0)
            self.assertIn("stdout_ref", evidence)
            self.assertIn("stderr_ref", evidence)
            self.assertEqual(stdout, "ABVX-OS FOUNDATION-002 baseline\n")
            second = run_bakeoff(ROOT, "foundation-002-baseline", Path(temp) / "evidence")
            self.assertNotEqual(first, second)
            self.assertEqual(json.loads((second / "result.json").read_text())["result"], "PASS")


class FakeLoopXBackend:
    def __init__(self, path: Path):
        self.path = path

    def create(self, state):
        self.write(state)

    def read(self, mission_id):
        if not self.path.exists():
            return None
        value = json.loads(self.path.read_text())
        if value.get("mission_id") != mission_id:
            return None
        return value

    def write(self, state):
        self.path.write_text(json.dumps(state, sort_keys=True))

    def restore(self, state):
        self.write(state)


class MissionStateProviderTests(unittest.TestCase):
    def provider(self, temp: str):
        root = Path(temp)
        return LoopXMissionStateProvider(
            FakeLoopXBackend(root / "loopx-state.json"),
            root / "boundary",
            ROOT / "schemas" / "mission_state_export.schema.json",
        )

    def test_fresh_and_healthy_state_export_is_normalized(self):
        with tempfile.TemporaryDirectory() as temp:
            provider = self.provider(temp)
            fresh = provider.create_mission(mission_id="mission-1", objective="Test objective", max_retries=2)
            healthy = provider.inspect_mission("mission-1")
            self.assertEqual(fresh["status"], "new")
            self.assertEqual(healthy["mission_id"], "mission-1")
            self.assertNotIn("loopx", json.dumps(provider.export_state("mission-1")).lower())

    def test_corrupt_and_missing_known_state_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            provider = self.provider(temp)
            provider.create_mission(mission_id="mission-1", objective="Test objective")
            state_path = Path(temp) / "loopx-state.json"
            state_path.write_text("not json")
            with self.assertRaises(MissionIntegrityError):
                provider.inspect_mission("mission-1")
            state_path.unlink()
            with self.assertRaises(MissionIntegrityError):
                provider.inspect_mission("mission-1")

    def test_recovery_is_explicit_and_gate_stays_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            provider = self.provider(temp)
            provider.create_mission(mission_id="mission-1", objective="Test objective")
            provider.wait_for_gate("mission-1", "human-approval")
            state_path = Path(temp) / "loopx-state.json"
            state_path.write_text("{}")
            recovered = provider.recover("mission-1")
            self.assertEqual(recovered["state"]["status"], "waiting_for_human")
            self.assertTrue(recovered["state"]["waiting_for_human"])
            self.assertEqual(recovered["state"]["gates"][0]["status"], "open")
            self.assertTrue(Path(recovered["evidence"]).exists())
            with self.assertRaises(MissionIntegrityError):
                provider.resume("mission-1")

    def test_failed_recovery_is_observable_and_stops(self):
        with tempfile.TemporaryDirectory() as temp:
            provider = self.provider(temp)
            provider.create_mission(mission_id="mission-1", objective="Test objective")
            snapshots = Path(temp) / "boundary" / "snapshots" / "mission-1"
            for snapshot in snapshots.glob("*.json"):
                snapshot.write_text("corrupt")
            (Path(temp) / "loopx-state.json").unlink()
            with self.assertRaises(MissionIntegrityError):
                provider.recover("mission-1")
            evidence = list((Path(temp) / "boundary" / "recovery-evidence" / "mission-1").glob("*.json"))
            self.assertEqual(json.loads(evidence[-1].read_text())["result"], "failed")

    def test_terminal_mission_cannot_restart(self):
        with tempfile.TemporaryDirectory() as temp:
            provider = self.provider(temp)
            provider.create_mission(mission_id="mission-1", objective="Test objective")
            provider.complete("mission-1")
            with self.assertRaises(MissionTerminalError):
                provider.resume("mission-1")


if __name__ == "__main__":
    unittest.main()
