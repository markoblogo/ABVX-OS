import json
import tempfile
import unittest
from pathlib import Path

from abvx_harness.harness import run_bakeoff, validate_repository


ROOT = Path(__file__).resolve().parents[1]


class HarnessTests(unittest.TestCase):
    def test_repository_documents_validate(self):
        checked = validate_repository(ROOT)
        self.assertIn("registries/projects.json", checked)
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


if __name__ == "__main__":
    unittest.main()
