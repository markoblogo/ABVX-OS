import copy
import json
import unittest
from datetime import date
from pathlib import Path

from abvx_harness.book_radar_discovery import (
    book_demand_supported,
    demand_window_viable,
    diagnose_zero_sales,
    early_discovery_decision,
    eligible_for_new_book,
    rights_ready,
    validate_evidence_card,
    validate_book_buying_situation,
)


BASE = {
    "buyer": "Narrow buyer",
    "payer": "Buyer",
    "purchase_trigger": "Recurring event",
    "job_to_be_done": "Use a book at the event",
    "deadline": "Weeks",
    "current_solution": "Existing books",
    "current_spend": "Books",
    "unmet_need": "Specific scenario is weakly served",
    "publishing_format_fit": "Paperback reference",
    "discovery_channel": "Amazon exact query",
    "evidence_dimensions": {
        name: {"status": "SUPPORTED", "source_ids": ["S1"]}
        for name in (
            "problem_evidence",
            "spending_evidence",
            "book_format_demand",
            "competitive_gap",
            "reachability",
            "delivery_fit",
        )
    },
    "decision_state": "READY_FOR_VALIDATION",
    "discovery_source": "EXISTING_BOOK_DEMAND",
    "book_demand_evidence": {
        "type": "CURRENT_BOOK_TRACTION_PROXY",
        "strength": "MODERATE",
        "source_ids": ["S1"],
    },
    "discovery_path": "Exact Amazon query to paperback",
    "unmet_scenario": "Use during a bounded event",
    "external_trigger": {"description": "Annual event", "confidence": "CONFIRMED", "source_ids": ["S2"]},
    "demand_window": {"opens": "2026-09-01", "closes": "2027-06-30", "preparation_days": 30},
    "existing_asset_fit": {"status": "NO_FIT", "asset_id": None, "reason": "No relevant content"},
    "uncertainties": ["conversion"],
    "next_decision": "VALIDATE_NEW_BOOK",
}

EVIDENCE_CARD = {
    "buyer": "New RV owner",
    "purchase_reason": "Protect warranty records and know what is due",
    "specific_task": "Build a usable maintenance evidence trail",
    "comparable_book_purchase_evidence": {
        "status": "SUPPORTED",
        "source_ids": ["BUYER-REVIEW"],
    },
    "unmet_scenario": "Existing log is too blank and has too little guidance",
    "accessible_gap": {"status": "SUPPORTED", "source_ids": ["BUYER-REVIEW"]},
    "book_format": "PAPERBACK_WORKBOOK",
    "format_reason": "Stored with vehicle records and written in during service",
    "discovery_query_or_channel": "RV maintenance log book",
    "observations": [
        {
            "source_id": "BUYER-REVIEW",
            "independence_key": "buyer-a",
            "observed_at": "2026-04-30",
            "observation": "Buyer says they purchased a log for a new RV",
            "interpretation": "Physical log is natural for this task",
            "alternative_explanation": "One buyer may not represent the market",
        },
        {
            "source_id": "DIRECT-REQUEST",
            "independence_key": "buyer-b",
            "observed_at": "2025-09-08",
            "observation": "Another buyer asks which maintenance book to buy",
            "interpretation": "The book-buying job recurs",
            "alternative_explanation": "A free manual may satisfy the request",
        },
    ],
    "source_independence": {"minimum_independent_sources": 2, "rationale": "Different buyers and pages"},
    "freshness": {"as_of": "2026-09-08", "window_closes": None, "preparation_days": 45},
    "production_constraints": ["Do not invent maintenance intervals"],
    "main_uncertainty": "Accessible demand at the target price",
    "rights_status": "CLEAR",
    "expertise_status": "SOURCE_DEPENDENT_OK",
}


class BookDemandV4Tests(unittest.TestCase):
    def test_valid_extended_candidate(self):
        validate_book_buying_situation(copy.deepcopy(BASE))

    def test_trend_is_not_book_demand(self):
        evidence = {"type": "TREND_ONLY", "strength": "STRONG", "source_ids": ["TREND"]}
        self.assertFalse(book_demand_supported(evidence))

    def test_public_domain_original_does_not_cover_unknown_translation(self):
        self.assertFalse(rights_ready(original_public_domain=True, translation_rights="UNKNOWN"))
        self.assertTrue(rights_ready(original_public_domain=True, translation_rights="ORIGINAL_TRANSLATION"))

    def test_zero_sales_without_visibility_is_inconclusive(self):
        self.assertEqual(
            diagnose_zero_sales(sales=0, impressions=None, live_verified=True),
            "INSUFFICIENT_VISIBILITY_DATA",
        )
        self.assertEqual(
            diagnose_zero_sales(sales=0, impressions=None, live_verified=False),
            "PUBLIC_AVAILABILITY_UNVERIFIED",
        )

    def test_small_niche_is_not_an_automatic_rejection(self):
        candidate = copy.deepcopy(BASE)
        candidate["market_size"] = "SMALL"
        self.assertTrue(eligible_for_new_book(candidate, as_of=date(2026, 9, 8)))

    def test_existing_asset_does_not_rescue_weak_need(self):
        candidate = copy.deepcopy(BASE)
        candidate["existing_asset_fit"] = {
            "status": "PACKAGING_AUDIT",
            "asset_id": "existing-book",
            "reason": "Content exists",
        }
        candidate["book_demand_evidence"] = {
            "type": "LISTING_ONLY",
            "strength": "WEAK",
            "source_ids": ["LISTING"],
        }
        self.assertFalse(eligible_for_new_book(candidate, as_of=date(2026, 9, 8)))

    def test_temporary_window_accounts_for_preparation(self):
        self.assertFalse(
            demand_window_viable(
                {"opens": "2026-09-01", "closes": "2026-09-20", "preparation_days": 20},
                as_of=date(2026, 9, 8),
            )
        )

    def test_rn8_run_stays_within_bounded_limits(self):
        root = Path(__file__).resolve().parents[1]
        situations = json.loads((root / "book-radar/runs/rn8/buyer-situations.json").read_text())
        deep = json.loads((root / "book-radar/runs/rn8/deep-checks.json").read_text())
        actions = json.loads((root / "book-radar/runs/rn8/final-actions.json").read_text())
        watch = json.loads((root / "book-radar/runs/rn8/watchlist.json").read_text())
        self.assertLessEqual(len(situations["situations"]), 25)
        self.assertLessEqual(len(deep["checks"]), 6)
        self.assertLessEqual(len(actions["actions"]), 3)
        self.assertLessEqual(len(watch["items"]), 5)
        self.assertFalse(actions["production_authorized"])

    def test_rn7r_009_is_reserved_and_excluded(self):
        root = Path(__file__).resolve().parents[1]
        payload = json.loads((root / "book-radar/runs/rn8/buyer-situations.json").read_text())
        self.assertNotIn("RN7R-009", {item["id"] for item in payload["situations"]})
        self.assertEqual(payload["excluded"][0]["id"], "RN7R-009")

    def test_evidence_card_requires_purchase_scenario_and_accessible_gap(self):
        validate_evidence_card(copy.deepcopy(EVIDENCE_CARD))
        self.assertEqual(early_discovery_decision(EVIDENCE_CARD, as_of=date(2026, 9, 8)), "DEEP_SCAN_ELIGIBLE")

    def test_direct_request_without_purchase_evidence_stops_early(self):
        card = copy.deepcopy(EVIDENCE_CARD)
        card["comparable_book_purchase_evidence"] = {"status": "UNKNOWN", "source_ids": []}
        self.assertEqual(early_discovery_decision(card, as_of=date(2026, 9, 8)), "INSUFFICIENT_EVIDENCE")

    def test_repeated_pages_from_same_origin_are_not_independent(self):
        card = copy.deepcopy(EVIDENCE_CARD)
        card["observations"][1]["independence_key"] = "buyer-a"
        self.assertEqual(early_discovery_decision(card, as_of=date(2026, 9, 8)), "INSUFFICIENT_EVIDENCE")

    def test_clear_demand_does_not_override_rights_or_expertise(self):
        rights = copy.deepcopy(EVIDENCE_CARD)
        rights["rights_status"] = "BLOCKED"
        self.assertEqual(early_discovery_decision(rights, as_of=date(2026, 9, 8)), "REJECTED_ON_EVIDENCE")
        expertise = copy.deepcopy(EVIDENCE_CARD)
        expertise["expertise_status"] = "UNAVAILABLE"
        self.assertEqual(early_discovery_decision(expertise, as_of=date(2026, 9, 8)), "ATTRACTIVE_BUT_NOT_FOR_US")

    def test_expired_window_stops_before_deep_scan(self):
        card = copy.deepcopy(EVIDENCE_CARD)
        card["freshness"] = {"as_of": "2026-09-08", "window_closes": "2026-09-20", "preparation_days": 20}
        self.assertEqual(early_discovery_decision(card, as_of=date(2026, 9, 8)), "REJECTED_ON_EVIDENCE")

    def test_rn9_run_stays_bounded_and_does_not_authorize_production(self):
        root = Path(__file__).resolve().parents[1]
        cards = json.loads((root / "book-radar/runs/rn9/evidence-cards.json").read_text())
        deep = json.loads((root / "book-radar/runs/rn9/deep-checks.json").read_text())
        final = json.loads((root / "book-radar/runs/rn9/final-concepts.json").read_text())
        self.assertLessEqual(len(cards["cards"]), 20)
        self.assertLessEqual(len(deep["checks"]), 5)
        self.assertLessEqual(len(final["concepts"]), 2)
        self.assertFalse(final["production_authorized"])
        self.assertTrue({item["status"] for item in final["concepts"]} <= {"EVIDENCE_BACKED_CONCEPT", "WATCH", "INSUFFICIENT_EVIDENCE", "NO PRODUCT"})

    def test_rn9_uses_portfolio_for_duplication_only(self):
        root = Path(__file__).resolve().parents[1]
        audit = json.loads((root / "book-radar/runs/rn9/portfolio-similarity-audit.json").read_text())
        self.assertEqual(audit["scope"], "DUPLICATION_CHECK_ONLY")
        self.assertFalse(audit["portfolio_audit_performed"])
        self.assertTrue(all(item["classification"] == "NOVEL" for item in audit["checks"]))


if __name__ == "__main__":
    unittest.main()
