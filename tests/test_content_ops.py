from __future__ import annotations

import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from abvx_harness.__main__ import main
from abvx_harness.content_ops import approve_content_item, inspect_content_item, prepare_content_item, publish_content_item
from abvx_harness.harness import ValidationError, validate_repository


ROOT = Path(__file__).resolve().parents[1]


class ContentOpsTests(unittest.TestCase):
    def _root_with_content_ops(self) -> Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        shutil.copytree(ROOT / "schemas", root / "schemas")
        shutil.copytree(ROOT / "content" / "fixtures", root / "content" / "fixtures")
        shutil.copytree(ROOT / "events", root / "events")
        shutil.copytree(ROOT / "evidence", root / "evidence")
        shutil.copytree(ROOT / "registries", root / "registries")
        return root

    def test_repository_validation_covers_content_fixtures_and_adapter_registry(self):
        checked = validate_repository(ROOT)
        self.assertIn("content/fixtures/ssi-fast-path-dry-run.json", checked)
        self.assertIn("registries/publishing-adapters.json", checked)

    def test_prepare_ready_fixture_creates_prepared_item(self):
        root = self._root_with_content_ops()
        item = prepare_content_item(root, "content/fixtures/ssi-fast-path-dry-run.json")
        self.assertEqual(item["status"], "PREPARED")
        self.assertEqual(item["adapter"]["id"], "ssi.short-post")
        self.assertEqual(item["consumer_operation"]["id"], "index.publish-post")
        self.assertEqual(item["validation"]["tier"], "QUICK")
        self.assertEqual(item["enrichment"]["structured_data"]["type"], "BlogPosting")
        self.assertEqual(inspect_content_item(root, item["id"])["title"], item["title"])

    def test_prepare_ready_abvx_writing_fixture_uses_quick_tier(self):
        root = self._root_with_content_ops()
        item = prepare_content_item(root, "content/fixtures/abvx-note-fast-path-dry-run.json")
        self.assertEqual(item["status"], "PREPARED")
        self.assertEqual(item["validation"]["tier"], "QUICK")
        self.assertEqual(item["consumer_operation"]["id"], "abvx.publish-writing")

    def test_publish_requires_approval(self):
        root = self._root_with_content_ops()
        item = prepare_content_item(root, "content/fixtures/1d3x-fast-path-dry-run.json")
        with self.assertRaises(ValidationError):
            publish_content_item(root, item["id"])

    def test_publish_emits_packet_evidence_and_event(self):
        root = self._root_with_content_ops()
        item = prepare_content_item(root, "content/fixtures/abvx-work-fast-path-dry-run.json")
        approve_content_item(root, item["id"])
        result = publish_content_item(root, item["id"])
        self.assertEqual(result["result"], "CONDITIONAL_PASS")
        packet = json.loads((root / result["packet_path"]).read_text())
        event = json.loads((root / result["event_path"]).read_text())
        updated = inspect_content_item(root, item["id"])
        self.assertEqual(packet["item_id"], item["id"])
        self.assertEqual(packet["consumer_operation"]["id"], "abvx.publish-project")
        self.assertEqual(packet["enrichment"]["slug"], item["slug"])
        self.assertEqual(event["type"], "CONTENT_PUBLISHED")
        self.assertEqual(updated["status"], "PUBLISH_PACKET_EMITTED")
        self.assertEqual(updated["publication"]["event_ref"], result["event_path"])

    def test_cli_content_commands_share_the_same_store(self):
        root = self._root_with_content_ops()
        human = io.StringIO()
        machine = io.StringIO()
        with contextlib.redirect_stdout(human):
            self.assertEqual(main(["content", "prepare", "--file", "content/fixtures/azurmenton-fast-path-dry-run.json"], root=root), 0)
        with contextlib.redirect_stdout(machine):
            self.assertEqual(main(["content", "inspect", "content-ops-002-azur-fast-path", "--json"], root=root), 0)
        self.assertIn("content-ops-002-azur-fast-path", human.getvalue())
        self.assertEqual(json.loads(machine.getvalue())["adapter"]["id"], "azurmenton.guide")


if __name__ == "__main__":
    unittest.main()
