from __future__ import annotations

import contextlib
import io
import hashlib
import runpy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from abvx_harness.__main__ import main
from abvx_harness.content_ops import GenericPublishingAdapter, approve_content_item, inspect_content_item, prepare_content_item, publish_content_item
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

    def test_missing_native_source_is_blocked_before_approval_and_handoff(self):
        root = self._root_with_content_ops()
        file = root / "content/fixtures/abvx-note-fast-path-dry-run.json"
        fixture = json.loads(file.read_text())
        fixture["payload"].pop("source_markdown", None)
        fixture["payload"].pop("source_sha256", None)
        file.write_text(json.dumps(fixture))
        item = prepare_content_item(root, str(file))
        self.assertEqual(item["status"], "BLOCKED")
        with self.assertRaises(ValidationError):
            approve_content_item(root, item["id"])
        adapter = next(entry for entry in json.loads((root / "registries/publishing-adapters.json").read_text())["entries"] if entry["id"] == "abvx.writing")
        with self.assertRaises(ValidationError):
            GenericPublishingAdapter().build_publish_packet(root, item, adapter)

    def test_writing_fixture_replays_through_canonical_markdown_intake(self):
        fixture = json.loads((ROOT / "content/fixtures/abvx-note-fast-path-dry-run.json").read_text())
        payload = fixture["payload"]
        intake = runpy.run_path(str(ROOT / "scripts/prepare_abvx_publication.py"))["publication_fixture"]
        replay = intake(payload["source_markdown"], fixture["id"], "internal:dummy", [])
        self.assertEqual(replay["payload"]["date_published"], "2026-08-10")
        self.assertEqual(payload["date_published"], replay["payload"]["date_published"])
        self.assertEqual(payload["source_sha256"], replay["payload"]["source_sha256"])

    def test_stored_legacy_prepared_item_cannot_be_approved(self):
        root = self._root_with_content_ops()
        path = root / "content/items/content-ops-002-abvx-note-fast-path.json"
        path.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / path.relative_to(root), path)
        before = path.read_bytes()
        with self.assertRaisesRegex(ValidationError, "approved Markdown"):
            approve_content_item(root, path.stem)
        self.assertEqual(path.read_bytes(), before)
        self.assertFalse((root / "content/publish-packets" / path.name).exists())

    def test_native_approval_rechecks_source_without_recording_invalid_approval(self):
        for fixture in ("abvx-note-fast-path-dry-run.json", "abvx-working-story-dry-run.json"):
            for status in ("PREPARED", "APPROVED", "PUBLISH_PACKET_EMITTED"):
                for corruption in ("missing", "tampered"):
                    with self.subTest(fixture=fixture, status=status, corruption=corruption):
                        root = self._root_with_content_ops()
                        item = prepare_content_item(root, "content/fixtures/" + fixture)
                        item["status"] = status
                        if corruption == "missing":
                            item["payload"].pop("source_markdown")
                            item["payload"].pop("source_sha256")
                        else:
                            item["payload"]["source_markdown"] += "Changed after preparation."
                        path = root / "content/items" / (item["id"] + ".json")
                        path.write_text(json.dumps(item))
                        before = path.read_bytes()
                        with self.assertRaisesRegex(ValidationError, "approved Markdown"):
                            approve_content_item(root, item["id"])
                        self.assertEqual(path.read_bytes(), before)

    def test_native_packets_instruct_receipt_import_for_all_members_before_closeout(self):
        root = self._root_with_content_ops()
        for fixture in ["abvx-note-fast-path-dry-run.json", "abvx-working-story-dry-run.json"]:
            item = prepare_content_item(root, "content/fixtures/" + fixture)
            approve_content_item(root, item["id"])
            result = publish_content_item(root, item["id"])
            packet = json.loads((root / result["packet_path"]).read_text())
            steps = packet["required_consumer_steps"]
            imports = [i for i, step in enumerate(steps) if "publication check --item" in step and "--reuse-checks" in step]
            closeouts = [i for i, step in enumerate(steps) if "publication complete-cycle" in step]
            self.assertEqual(len(imports), 1)
            self.assertEqual(len(closeouts), 1)
            self.assertLess(imports[0], closeouts[0])
            self.assertIn("every", steps[imports[0]])

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

    def test_prepare_ready_mn7r_fixture_uses_markdown_consumer_command(self):
        root = self._root_with_content_ops()
        item = prepare_content_item(root, "content/fixtures/mn7r-fast-path-dry-run.json")
        self.assertEqual(item["status"], "PREPARED")
        self.assertEqual(item["adapter"]["id"], "mn7r.post")
        self.assertEqual(item["consumer_operation"]["id"], "mn7r.publish-post")
        self.assertEqual(item["validation"]["tier"], "STANDARD")
        self.assertEqual(item["enrichment"]["structured_data"]["type"], "Article")

    def test_prepare_preserves_explicit_social_description_for_enrichment(self):
        root = self._root_with_content_ops()
        item = prepare_content_item(root, "content/fixtures/mn7r-real-publication-a-good-offer.json")
        self.assertEqual(
            item["enrichment"]["social_preview"]["description"],
            "The minimum data that turns a commodity offer from chat noise into an executable commercial opportunity.",
        )
        self.assertEqual(
            item["enrichment"]["open_graph"]["description"],
            "The minimum data that turns a commodity offer from chat noise into an executable commercial opportunity.",
        )
        self.assertEqual(
            item["payload"]["excerpt"],
            "Why commodity offers need structured data before they can be searched, matched, handed over, and executed.",
        )

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
