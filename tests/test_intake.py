from __future__ import annotations

import json
import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from abvx_harness.intake import (
    add_intake_item,
    inspect_intake_item,
    link_intake_items,
    list_intake_items,
    update_clarification,
)
from abvx_harness.__main__ import main


class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_text_intake_preserves_raw_input_and_multi_route_semantics(self):
        item = add_intake_item(self.root, text="Finish POP and later publish a guide and book", item_id="pop-idea", captured_at="2026-08-08T00:00:00Z")
        self.assertEqual(item["raw_input"]["value"], "Finish POP and later publish a guide and book")
        self.assertEqual(item["classification"]["primary_type"], "PROJECT_WORK")
        self.assertIn("CONTENT_OPPORTUNITY", item["classification"]["secondary_types"])
        self.assertGreaterEqual(len(item["possible_routes"]), 3)
        self.assertFalse((self.root / "portfolio" / "state.json").exists())

    def test_url_intake_does_not_fetch_and_classifies_headlands(self):
        item = add_intake_item(self.root, url="https://dev.ua/news/the-headlands-1784625711", context="SSI and 1D3X cultural context opportunity", item_id="headlands", captured_at="2026-08-08T00:00:00Z")
        self.assertEqual(item["input_type"], "URL")
        self.assertEqual(item["raw_input"]["reference"], item["raw_input"]["value"])
        self.assertEqual(item["classification"]["primary_type"], "CONTENT_OPPORTUNITY")
        self.assertEqual(item["provenance"]["source_uri"], item["raw_input"]["value"])

    def test_uncertain_intent_requires_one_clarification(self):
        item = add_intake_item(self.root, text="Interesting", item_id="uncertain", captured_at="2026-08-08T00:00:00Z")
        self.assertEqual(item["status"], "NEEDS_CLARIFICATION")
        self.assertTrue(item["clarification"]["required"])
        self.assertEqual(item["clarification"]["question"], "What should this be related to or used for?")

    def test_human_clarification_is_persisted(self):
        add_intake_item(self.root, text="Interesting", item_id="clarify", captured_at="2026-08-08T00:00:00Z")
        updated = update_clarification(self.root, "clarify", "General reference for future research")
        self.assertFalse(updated["clarification"]["required"])
        self.assertEqual(updated["status"], "PROPOSED")
        self.assertEqual(inspect_intake_item(self.root, "clarify")["clarification"]["answer"], "General reference for future research")

    def test_related_items_are_linked_reciprocally(self):
        add_intake_item(self.root, text="Index", item_id="index", captured_at="2026-08-08T00:00:00Z")
        add_intake_item(self.root, text="POP library", item_id="pop", captured_at="2026-08-08T00:00:00Z")
        link_intake_items(self.root, "index", "pop")
        self.assertEqual(list_intake_items(self.root)[0]["id"], "index")
        self.assertIn("pop", inspect_intake_item(self.root, "index")["related_item_ids"])
        self.assertIn("index", inspect_intake_item(self.root, "pop")["related_item_ids"])

    def test_json_and_human_views_use_same_items(self):
        add_intake_item(self.root, url="https://github.com/jordan-gibbs/hyperresearch", item_id="hyperresearch", captured_at="2026-08-08T00:00:00Z")
        items = list_intake_items(self.root)
        self.assertEqual(json.loads(json.dumps(items))[0]["id"], "hyperresearch")
        self.assertEqual(items[0]["classification"]["primary_type"], "EXTERNAL_OSS")

    def test_cli_json_and_human_list_share_the_same_store(self):
        add_intake_item(self.root, text="A useful reference", item_id="reference", captured_at="2026-08-08T00:00:00Z")
        human = io.StringIO()
        machine = io.StringIO()
        with contextlib.redirect_stdout(human):
            self.assertEqual(main(["intake", "list"], root=self.root), 0)
        with contextlib.redirect_stdout(machine):
            self.assertEqual(main(["intake", "list", "--json"], root=self.root), 0)
        self.assertIn("reference", human.getvalue())
        self.assertEqual(json.loads(machine.getvalue())[0]["id"], "reference")


if __name__ == "__main__":
    unittest.main()
