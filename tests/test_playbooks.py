import json
import tempfile
import unittest
from pathlib import Path

from abvx_harness.harness import validate_repository
from abvx_harness.playbooks import load_playbook, replay_playbook, select_validation_tier, validate_required_inputs


ROOT = Path(__file__).resolve().parents[1]


class PlaybookTests(unittest.TestCase):
    def test_repository_validation_covers_playbooks_and_events(self):
        checked = validate_repository(ROOT)
        self.assertIn("playbooks/azurmenton.publish-guide.json", checked)
        self.assertIn("playbooks/replays/azurmenton.attach-guide-images.AZURMENTON-005.json", checked)
        self.assertIn("events/projects/azurmenton/content_published-computer-and-phone-repair-in-menton.json", checked)

    def test_required_inputs_are_enforced(self):
        playbook = load_playbook(ROOT, "azurmenton.publish-guide")
        replay = json.loads((ROOT / "playbooks" / "replays" / "azurmenton.publish-guide.AZURMENTON-005.json").read_text())
        del replay["observed_inputs"]["cover_ready"]
        with self.assertRaisesRegex(ValueError, "missing required inputs"):
            validate_required_inputs(playbook, replay)

    def test_validation_tier_selection_escalates_from_standard_and_quick(self):
        publish = load_playbook(ROOT, "azurmenton.publish-guide")
        attach = load_playbook(ROOT, "azurmenton.attach-guide-images")
        self.assertEqual(select_validation_tier(publish, {"factual_conflict": True}), "FULL")
        self.assertEqual(select_validation_tier(attach, {"ambiguous_asset_match": True}), "FULL")
        self.assertEqual(select_validation_tier(attach, {"security_sensitive": True}), "CRITICAL")

    def test_replay_rejects_portfolio_mutation_scope(self):
        with tempfile.TemporaryDirectory() as temp:
            replay_path = Path(temp) / "replay.json"
            replay = json.loads((ROOT / "playbooks" / "replays" / "azurmenton.publish-guide.AZURMENTON-005.json").read_text())
            replay["scope"] = {"portfolio_mutation_requested": True}
            replay_path.write_text(json.dumps(replay))
            with self.assertRaisesRegex(ValueError, "portfolio mutation is prohibited"):
                replay_playbook(ROOT, "azurmenton.publish-guide", replay_path, output_root=Path(temp))

    def test_publish_replay_emits_compact_event_without_portfolio_mutation(self):
        before = (ROOT / "portfolio" / "state.json").read_text()
        with tempfile.TemporaryDirectory() as temp:
            result = replay_playbook(
                ROOT,
                "azurmenton.publish-guide",
                ROOT / "playbooks" / "replays" / "azurmenton.publish-guide.AZURMENTON-005.json",
                output_root=Path(temp),
            )
            event = json.loads((Path(temp) / result["event_path"]).read_text())
            self.assertEqual(result["validation_tier"], "STANDARD")
            self.assertEqual(event["type"], "CONTENT_PUBLISHED")
            self.assertEqual(event["portfolio_effect"], "NONE")
        self.assertEqual((ROOT / "portfolio" / "state.json").read_text(), before)

    def test_image_replay_is_idempotent_and_emits_compact_event(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            first = replay_playbook(
                ROOT,
                "azurmenton.attach-guide-images",
                ROOT / "playbooks" / "replays" / "azurmenton.attach-guide-images.AZURMENTON-005.json",
                output_root=temp_root,
            )
            second = replay_playbook(
                ROOT,
                "azurmenton.attach-guide-images",
                ROOT / "playbooks" / "replays" / "azurmenton.attach-guide-images.AZURMENTON-005.json",
                output_root=temp_root,
            )
            first_event = json.loads((temp_root / first["event_path"]).read_text())
            second_event = json.loads((temp_root / second["event_path"]).read_text())
            self.assertEqual(first["result"], "PASS")
            self.assertEqual(second["result"], "PASS")
            self.assertEqual(first_event["type"], "MEDIA_ASSETS_ATTACHED")
            self.assertEqual(second_event["type"], "MEDIA_ASSETS_ATTACHED")
            self.assertEqual(first["summary"]["report_only_expectation"]["already_covered"], 5)


if __name__ == "__main__":
    unittest.main()
