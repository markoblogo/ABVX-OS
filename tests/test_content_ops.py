from __future__ import annotations

import contextlib
import io
import json
import hashlib
import runpy
import shutil
import tempfile
import unittest
from unittest.mock import patch
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

    def test_prepare_ready_mn7r_fixture_uses_markdown_consumer_command(self):
        root = self._root_with_content_ops()
        item = prepare_content_item(root, "content/fixtures/mn7r-fast-path-dry-run.json")
        self.assertEqual(item["status"], "PREPARED")
        self.assertEqual(item["adapter"]["id"], "mn7r.post")
        self.assertEqual(item["consumer_operation"]["id"], "mn7r.publish-post")
        self.assertEqual(item["validation"]["tier"], "STANDARD")
        self.assertEqual(item["enrichment"]["structured_data"]["type"], "Article")

    def test_working_story_handoff_preserves_source_and_requires_approval(self):
        root = self._root_with_content_ops()
        item = prepare_content_item(root, "content/fixtures/abvx-working-story-dry-run.json")
        self.assertEqual(item["status"], "PREPARED")
        self.assertEqual(item["validation"]["tier"], "STANDARD")
        self.assertEqual(item["enrichment"]["canonical_path"], "/writing/working-stories/test-only-working-story")
        with self.assertRaises(ValidationError):
            publish_content_item(root, item["id"])
        approve_content_item(root, item["id"])
        result = publish_content_item(root, item["id"])
        packet = json.loads((root / result["packet_path"]).read_text())
        self.assertEqual(packet["payload"], item["payload"])
        self.assertEqual(packet["consumer_operation"]["id"], "abvx.publish-working-story")
        self.assertEqual(packet["mode"], "REPORT_ONLY_HANDOFF")

    def test_working_story_source_tampering_blocks_approval(self):
        root = self._root_with_content_ops()
        file = root / "content/fixtures/abvx-working-story-dry-run.json"
        fixture = json.loads(file.read_text())
        fixture["payload"]["source_markdown"] += "Changed prose."
        file.write_text(json.dumps(fixture))
        item = prepare_content_item(root, str(file))
        self.assertEqual(item["status"], "BLOCKED")
        with self.assertRaises(ValidationError):
            approve_content_item(root, item["id"])

    def test_markdown_intake_preserves_source_and_routes_both_existing_surfaces(self):
        intake = runpy.run_path(str(ROOT / "scripts/prepare_abvx_publication.py"))["publication_fixture"]
        source = json.loads((ROOT / "content/fixtures/abvx-working-story-dry-run.json").read_text())["payload"]["source_markdown"]
        fixture = intake(source, "test-intake", "internal:test", [])
        self.assertEqual(fixture["payload"]["source_markdown"], source)
        self.assertEqual(fixture["payload"]["source_sha256"], hashlib.sha256(source.encode()).hexdigest())
        native = '---\n' + json.dumps({"id": "a-note", "title": "A note", "slug": "a-note", "summary": "Test", "primarySection": "writing", "publishedAt": "2026-10-10", "visibility": "public", "status": "live"}) + '\n---\n\nExact **author text**.\n'
        fixture = intake(native, "test-note", "internal:test", [])
        self.assertEqual(fixture["adapter_id"], "abvx.writing")
        self.assertEqual(fixture["payload"]["body_lines"], ["Exact **author text**."])
        with self.assertRaises(ValidationError):
            intake(native, "../unsafe", "internal:test", [])
        with self.assertRaises(ValidationError):
            intake(native, "test-note", "internal:test", [{"source": "/test.png", "target": "/media/test.png"}])

    def test_working_story_intake_requires_mapping_for_every_referenced_image(self):
        intake = runpy.run_path(str(ROOT / "scripts/prepare_abvx_publication.py"))["publication_fixture"]
        source = json.loads((ROOT / "content/fixtures/abvx-working-story-dry-run.json").read_text())["payload"]["source_markdown"]
        header, body = source.split('\n---\n', 1)
        data = json.loads(header.removeprefix('---\n'))
        data['coverImage'] = {'src': '/media/cover.png', 'alt': 'Cover', 'width': 1, 'height': 1}
        data['illustrations'] = [{'src': '/media/example.png', 'alt': 'Example', 'caption': 'Example',
                                 'width': 1, 'height': 1, 'afterHeading': 'A choice'}]
        source = '---\n' + json.dumps(data) + '\n---\n' + body
        assets = [{'source': '/absolute/site/public' + image['src'], 'target': image['src'], 'sha256': 'a' * 64}
                  for image in [data['coverImage'], *data['illustrations']]]
        for incomplete in ([], assets[:1], [assets[0], assets[0]]):
            with self.assertRaisesRegex(ValidationError, 'every referenced image'):
                intake(source, 'test-media', 'internal:test', incomplete)
        fixture = intake(source, 'test-media', 'internal:test', assets)
        self.assertEqual(fixture['payload']['media_assets'], assets)

    def test_native_full_source_media_and_tampering_gate(self):
        intake = runpy.run_path(str(ROOT / "scripts/prepare_abvx_publication.py"))["publication_fixture"]
        data = {"id": "media-note", "slug": "media-note", "title": "An author title", "seoTitle": "A search title",
                "type": "article", "summary": "Original research", "primarySection": "writing",
                "publishedAt": "2026-10-10", "visibility": "public", "status": "live",
                "media": {"src": "/media/note/cover.png", "alt": "Author cover", "width": 1536, "height": 1024}}
        source = '---\n' + json.dumps(data) + '\n---\n\n```text\n  Preserved indentation\n```\n'
        asset = {"source": "/absolute/cover.png", "target": data["media"]["src"], "sha256": "a" * 64}
        with self.assertRaisesRegex(ValidationError, 'every referenced image'):
            intake(source, "native-media", "internal:test", [])
        fixture = intake(source, "native-media", "internal:test", [asset])
        self.assertEqual(fixture["payload"]["seo_title"], data["seoTitle"])
        self.assertEqual(fixture["payload"]["source_markdown"], source)
        root = self._root_with_content_ops()
        file = root / "content/fixtures/native-media.json"
        fixture["payload"]["source_markdown"] += "Unexpected text."
        file.write_text(json.dumps(fixture))
        item = prepare_content_item(root, str(file))
        self.assertEqual(item["status"], "BLOCKED")
        with self.assertRaises(ValidationError):
            approve_content_item(root, item["id"])

    def test_native_video_requires_matching_thumbnail_and_timezone(self):
        intake = runpy.run_path(str(ROOT / "scripts/prepare_abvx_publication.py"))["publication_fixture"]
        data = {"id": "video-note", "slug": "video-note", "title": "Video with notes", "type": "article",
                "summary": "Author commentary", "primarySection": "writing", "publishedAt": "2026-10-10",
                "visibility": "public", "status": "live", "videoUrl": "https://www.youtube.com/watch?v=6q2JG0gCyDg",
                "videoUploadedAt": "2026-10-10T00:00:00+00:00",
                "media": {"src": "https://i.ytimg.com/vi/6q2JG0gCyDg/hqdefault.jpg", "alt": "Video preview", "width": 480, "height": 360}}
        def source():
            return '---\n' + json.dumps(data) + '\n---\n\nOriginal notes.\n'
        self.assertEqual(intake(source(), "native-video", "internal:test", [])["payload"]["media_assets"], [])
        data["videoUploadedAt"] = "2026-10-10T00:00:00"
        with self.assertRaisesRegex(ValidationError, 'upload date'):
            intake(source(), "native-video", "internal:test", [])
        data["videoUploadedAt"] = "2026-10-10T00:00:00+00:00"
        data["media"]["src"] = "https://i.ytimg.com/vi/aaaaaaaaaaa/hqdefault.jpg"
        with self.assertRaisesRegex(ValidationError, 'matching YouTube'):
            intake(source(), "native-video", "internal:test", [])

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

    def test_video_upload_date_without_url_fails_before_preparation(self):
        intake = runpy.run_path(str(ROOT / "scripts/prepare_abvx_publication.py"))["publication_fixture"]
        data = {"id": "video-note", "slug": "video-note", "title": "Video notes", "summary": "Author notes",
                "primarySection": "writing", "publishedAt": "2026-10-10", "visibility": "public", "status": "live",
                "videoUploadedAt": "2026-10-10T00:00:00Z"}
        source = '---\n' + json.dumps(data) + '\n---\n\nOriginal notes.\n'
        with self.assertRaisesRegex(ValidationError, "provided together"):
            intake(source, "orphan-video", "internal:test", [])

    def test_changed_approved_content_cannot_emit_a_publish_packet(self):
        root = self._root_with_content_ops()
        item = prepare_content_item(root, "content/fixtures/abvx-work-fast-path-dry-run.json")
        approve_content_item(root, item["id"])
        path = root / "content/items" / f"{item['id']}.json"
        changed = json.loads(path.read_text())
        changed["summary"] = "Changed after owner approval"
        path.write_text(json.dumps(changed))
        with self.assertRaisesRegex(ValidationError, "approval.*content"):
            publish_content_item(root, item["id"])
        self.assertFalse((root / "content/publish-packets" / f"{item['id']}.json").exists())

    def test_legacy_approval_requires_review_before_handoff(self):
        root = self._root_with_content_ops()
        item = prepare_content_item(root, "content/fixtures/abvx-work-fast-path-dry-run.json")
        approve_content_item(root, item["id"])
        path = root / "content/items" / f"{item['id']}.json"
        legacy = json.loads(path.read_text())
        del legacy["human_gate"]["approved_content_sha256"]
        path.write_text(json.dumps(legacy))
        self.assertEqual(inspect_content_item(root, item["id"])["status"], "APPROVED")
        with self.assertRaisesRegex(ValidationError, "approve the item again"):
            publish_content_item(root, item["id"])
        approve_content_item(root, item["id"])
        self.assertEqual(publish_content_item(root, item["id"])["status"], "PASS")

    def test_failed_atomic_replacement_preserves_original_and_cleans_tempfile(self):
        from abvx_harness.content_ops import _write_json
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "approval.json"
            _write_json(path, {"state": "APPROVED"})
            original = path.read_bytes()
            with patch("abvx_harness.content_ops.os.replace", side_effect=OSError("disk error")):
                with self.assertRaises(OSError):
                    _write_json(path, {"state": "OTHER"})
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual([p.name for p in path.parent.iterdir()], [path.name])

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
