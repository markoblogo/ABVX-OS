import json
import unittest
from pathlib import Path

from abvx_harness.portfolio import inspect_portfolio, render_portfolio


ROOT = Path(__file__).resolve().parents[1]


class PortfolioTests(unittest.TestCase):
    def test_high_priority_waiting_project_is_not_actionable(self):
        portfolio = inspect_portfolio(ROOT)
        self.assertEqual([item["project"] for item in portfolio["actionable"]], ["azurmenton"])
        self.assertEqual(portfolio["waiting_for_human"][0]["project"], "coqpi")

    def test_not_before_human_item_stays_deferred(self):
        portfolio = inspect_portfolio(ROOT, today="2026-08-08")
        item = portfolio["human_queue"][0]
        self.assertEqual(item["status"], "WAITING")
        self.assertFalse(item["eligible_today"])

    def test_human_queue_contains_only_owner_gated_items(self):
        portfolio = inspect_portfolio(ROOT)
        self.assertEqual(len(portfolio["human_queue"]), 1)
        self.assertEqual(portfolio["human_queue"][0]["project"], "coqpi")

    def test_json_and_human_rendering_use_same_state(self):
        portfolio = inspect_portfolio(ROOT)
        rendered = render_portfolio(portfolio)
        self.assertIn("AzurMenton", rendered)
        self.assertIn("next: Expand bounded source/verification automation", rendered)
        self.assertIn("WAITING FOR YOU", rendered)
        self.assertIn("CoqPi", rendered)
        self.assertEqual(portfolio["actionable"][0]["next_action"], "Expand bounded source/verification automation to the next high-volatility guide set")

    def test_first_capability_occurrence_remains_candidate(self):
        lessons = json.loads((ROOT / "portfolio" / "lessons.json").read_text())
        event_lesson = next(item for item in lessons["entries"] if item["candidate_capability"] == "event_freshness")
        self.assertEqual(event_lesson["classification"], "CAPABILITY_CANDIDATE")
        self.assertEqual(event_lesson["status"], "recorded")


if __name__ == "__main__":
    unittest.main()
