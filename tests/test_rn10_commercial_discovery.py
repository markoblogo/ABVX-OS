import json
import unittest
from datetime import date
from pathlib import Path

from abvx_harness.book_radar_discovery import commercial_discovery_decision, rank_commercial_candidates


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "book-radar/runs/rn10"


class RN10CommercialDiscoveryTests(unittest.TestCase):
    def test_external_trend_sensor_cannot_authorize_commercial_claims(self):
        assessment = json.loads(
            (ROOT / "book-radar/audits/last30days-skill-assessment.json").read_text()
        )
        strategy = json.loads(
            (ROOT / "book-radar/strategies/candidate-generation-v5-commercial-first.json").read_text()
        )
        self.assertEqual(assessment["decision"], "ADMIT_AS_OPTIONAL_DISCOVERY_SENSOR")
        self.assertEqual(assessment["radar_contract"]["stage"], "NOMINATION_BEFORE_MARKET_CARD")
        self.assertIn("commercial tier", assessment["radar_contract"]["may_not_support_alone"])
        self.assertIn("do not by themselves establish book purchases",
                      strategy["fresh_demand_sensor"]["evidence_boundary"])

    def test_run_is_bounded_and_does_not_authorize_production(self):
        cards = json.loads((RUN / "market-cards.json").read_text())["cards"]
        deep = json.loads((RUN / "deep-checks.json").read_text())["checks"]
        final = json.loads((RUN / "final-concepts.json").read_text())
        self.assertLessEqual(len(cards), 20)
        self.assertLessEqual(len(deep), 5)
        self.assertLessEqual(len(final["concepts"]), 2)
        self.assertFalse(final["production_authorized"])

    def test_every_source_reference_resolves(self):
        sources = {item["id"] for item in json.loads((RUN / "source-ledger.json").read_text())["sources"]}
        cards = json.loads((RUN / "market-cards.json").read_text())["cards"]
        for card in cards:
            for observation in card["observations"]:
                self.assertIn(observation["source_id"], sources)
            for claim in card["claims"].values():
                self.assertTrue(set(claim["source_ids"]) <= sources)

    def test_only_two_cards_clear_the_commercial_gate(self):
        cards = json.loads((RUN / "market-cards.json").read_text())["cards"]
        ranked = rank_commercial_candidates(cards, as_of=date(2026, 9, 8))
        self.assertEqual([item["id"] for item in ranked], ["RN10-002", "RN10-001"])
        decisions = {item["id"]: commercial_discovery_decision(item, as_of=date(2026, 9, 8)) for item in cards}
        self.assertEqual(decisions["RN10-009"], "REJECTED_ON_EVIDENCE")
        self.assertEqual(decisions["RN10-003"], "INSUFFICIENT_EVIDENCE")

    def test_final_concepts_match_ranked_cards(self):
        cards = json.loads((RUN / "market-cards.json").read_text())["cards"]
        ranked = rank_commercial_candidates(cards, as_of=date(2026, 9, 8))
        final = json.loads((RUN / "final-concepts.json").read_text())["concepts"]
        self.assertEqual([item["id"] for item in final], [item["id"] for item in ranked])


if __name__ == "__main__":
    unittest.main()
