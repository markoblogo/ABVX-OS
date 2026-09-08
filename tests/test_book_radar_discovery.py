import unittest

from abvx_harness.book_radar_discovery import (
    EVIDENCE_DIMENSIONS,
    independent_publishers,
    recommend_decision,
    validate_buyer_situation,
)
from abvx_harness.harness import ValidationError


def statuses(**overrides):
    value = {name: "SUPPORTED" for name in EVIDENCE_DIMENSIONS}
    value.update(overrides)
    return value


class BookRadarDiscoveryTests(unittest.TestCase):
    def test_problem_exists_does_not_prove_spending(self):
        self.assertEqual(
            recommend_decision(statuses(spending_evidence="UNKNOWN")),
            "INSUFFICIENT_EVIDENCE",
        )

    def test_paid_service_does_not_prove_book_demand(self):
        self.assertEqual(
            recommend_decision(statuses(book_format_demand="UNKNOWN")),
            "INSUFFICIENT_EVIDENCE",
        )

    def test_missing_data_is_not_negative_data(self):
        self.assertEqual(
            recommend_decision(statuses(competitive_gap="UNKNOWN")),
            "INSUFFICIENT_EVIDENCE",
        )
        self.assertEqual(
            recommend_decision(statuses(competitive_gap="NEGATIVE")),
            "REJECTED_ON_EVIDENCE",
        )

    def test_strong_competitor_only_rejects_when_advantage_is_absent(self):
        self.assertEqual(recommend_decision(statuses()), "READY_FOR_VALIDATION")
        self.assertEqual(
            recommend_decision(statuses(competitive_gap="NEGATIVE")),
            "REJECTED_ON_EVIDENCE",
        )

    def test_real_market_outside_delivery_boundary_is_not_called_no_demand(self):
        self.assertEqual(
            recommend_decision(statuses(), outside_delivery_boundary=True),
            "ATTRACTIVE_BUT_NOT_FOR_US",
        )

    def test_multiple_pages_from_one_seller_count_once(self):
        records = [{"publisher": "Seller A"}, {"publisher": "seller a"}, {"publisher": "Agency B"}]
        self.assertEqual(independent_publishers(records), 2)

    def test_candidate_requires_all_evidence_dimensions(self):
        with self.assertRaises(ValidationError):
            validate_buyer_situation({"buyer": "x"})


if __name__ == "__main__":
    unittest.main()
