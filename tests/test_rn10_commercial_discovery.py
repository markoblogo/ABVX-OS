import json
import unittest
from datetime import date
from pathlib import Path

from abvx_harness.book_radar_discovery import (
    commercial_discovery_decision,
    rank_commercial_candidates,
    validate_listing_package,
    validate_listing_pattern_scan,
)


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
        self.assertEqual(decisions["RN10-010"], "INSUFFICIENT_EVIDENCE")

    def test_final_concepts_match_ranked_cards(self):
        cards = json.loads((RUN / "market-cards.json").read_text())["cards"]
        ranked = rank_commercial_candidates(cards, as_of=date(2026, 9, 8))
        final = json.loads((RUN / "final-concepts.json").read_text())["concepts"]
        self.assertEqual([item["id"] for item in final], [item["id"] for item in ranked])

    def test_user_supplied_rn10_003_is_a_bounded_concept_gate(self):
        concept = json.loads((RUN / "rn10-003-concept-gate.json").read_text())
        self.assertEqual(concept["id"], "RN10-003")
        self.assertEqual(concept["status"], "LISTING_PATTERN_GATE_PASS")
        self.assertFalse(concept["production_authorized"])
        self.assertEqual(len(concept["progression_system"]["primary_stats"]), 5)
        self.assertEqual(len(concept["situation_map"]), 12)
        self.assertEqual(len({item["source_ref"] for item in concept["situation_map"]}), 12)

    def test_rn10_003_listing_package_is_searchable_without_metadata_abuse(self):
        concept = json.loads((RUN / "rn10-003-concept-gate.json").read_text())
        listing = concept["listing_package"]
        self.assertEqual(len(listing["keyword_fields"]), 7)
        self.assertEqual(len(listing["category_targets"]), 3)
        self.assertEqual(listing["alternatives_considered"][0]["title"], "Good Dog, Bad System")
        keyword_text = " ".join(listing["keyword_fields"]).lower()
        self.assertNotIn("kindle unlimited", keyword_text)
        self.assertNotIn("kdp select", keyword_text)
        self.assertNotIn("dungeon crawler carl", keyword_text)

    def test_current_listing_scan_is_bounded_and_noncausal(self):
        scan = json.loads((RUN / "rn10-003-listing-patterns.json").read_text())
        validate_listing_pattern_scan(scan)
        self.assertEqual(len(scan["sampled_listings"]), 12)
        self.assertGreaterEqual(len(scan["detail_checks"]), 2)
        self.assertTrue(all(
            pattern["causal_status"] == "CORRELATIONAL_ONLY"
            for pattern in scan["observed_patterns"]
        ))

    def test_rn10_003_package_clears_the_listing_contract(self):
        concept = json.loads((RUN / "rn10-003-concept-gate.json").read_text())
        scan = json.loads((RUN / "rn10-003-listing-patterns.json").read_text())
        validate_listing_package(concept["listing_package"], scan)
        self.assertFalse(concept["listing_pattern_gate"]["manuscript_allowed"])


if __name__ == "__main__":
    unittest.main()
