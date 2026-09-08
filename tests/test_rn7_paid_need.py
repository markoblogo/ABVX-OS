import json
import unittest
from pathlib import Path

from abvx_harness.book_radar_discovery import validate_buyer_situation


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "book-radar" / "runs" / "rn7-paid-need"


class RN7PaidNeedTests(unittest.TestCase):
    def load(self, name):
        return json.loads((RUN / name).read_text())

    def test_bounded_run_and_evidence_first_shape(self):
        data = self.load("buyer-situations.json")
        known_sources = {item["id"] for item in self.load("evidence-ledger.json")["sources"]}
        self.assertLessEqual(data["count"], 20)
        self.assertEqual(data["count"], len(data["situations"]))
        for item in data["situations"]:
            validate_buyer_situation(item)
            used = {source for dimension in item["evidence_dimensions"].values() for source in dimension["source_ids"]}
            self.assertFalse(used - known_sources)

    def test_deep_and_hypothesis_limits(self):
        self.assertLessEqual(self.load("deep-checks.json")["count"], 5)
        hypotheses = self.load("commercial-hypotheses.json")
        self.assertLessEqual(hypotheses["count"], 2)
        self.assertFalse(hypotheses["production_authorized"])
        self.assertFalse(hypotheses["external_tests_launched"])

    def test_rn6_and_original_rn7_are_preserved(self):
        self.assertEqual(json.loads((ROOT/"book-radar/runs/rn6/investment-gates.json").read_text())["final_decision"], "NO_PRODUCT")
        self.assertTrue((ROOT/"book-radar/runs/rn7/broad-opportunities.json").is_file())
        self.assertEqual(self.load("buyer-situations.json")["run_id"], "RN7-PAID-NEED")

    def test_no_production_artifacts_exist(self):
        forbidden = {"pdf", "epub", "docx", "png", "jpg", "jpeg"}
        self.assertFalse([p for p in RUN.rglob("*") if p.suffix.lower().lstrip(".") in forbidden])

    def test_ready_for_validation_never_authorizes_production(self):
        ready = [x for x in self.load("buyer-situations.json")["situations"] if x["decision_state"] == "READY_FOR_VALIDATION"]
        self.assertEqual([x["id"] for x in ready], ["RN7R-009"])
        decisions = self.load("book-radar-import.json")["decisions"]
        self.assertTrue(all(item["production_authorized"] is False for item in decisions))

    def test_retained_gates_and_similarity_are_explicit(self):
        gates = self.load("retained-gates.json")
        self.assertFalse(gates["production_authorized"])
        self.assertTrue(gates["portfolio_similarity"]["production_eligible"])
        self.assertIn(gates["portfolio_similarity"]["classification"], {"NOVEL", "ADJACENT"})
        self.assertEqual({gates[key]["status"] for key in ("rights","language","format","anton_attention")}, {"PASS"})


if __name__ == "__main__":
    unittest.main()
