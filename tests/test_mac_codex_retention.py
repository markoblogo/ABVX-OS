"""Synthetic test fixtures: never inspect or modify the owner's Codex directories."""
import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

from abvx_harness import mac_codex_retention as retention
from abvx_harness import mac_operator


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                          text=True, check=True)


class CodexRetentionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "Codex"
        self.repo = self.root / "2026-01-01" / "new-chat" / "work" / "sample"
        self.repo.mkdir(parents=True)
        git(self.repo, "init", "-q")
        (self.repo / ".gitignore").write_text("node_modules/\n.next/\n")
        (self.repo / "package-lock.json").write_text('{"lockfileVersion":3}')
        (self.repo / "README.md").write_text("preserve me")
        git(self.repo, "add", ".")
        git(self.repo, "-c", "user.name=Fixture", "-c",
            "user.email=fixture@example.test", "commit", "-qm", "fixture")
        self.modules = self.repo / "node_modules"
        self.modules.mkdir()
        (self.modules / "dependency.txt").write_text("regenerable")
        self.build = self.repo / "apps" / "site" / ".next"
        self.build.mkdir(parents=True)
        (self.build / "cache").write_text("regenerable")
        self.now = time.time() + 30 * 86400

    def inspect(self, **kwargs):
        with patch.object(retention, "_paths_in_use", return_value=([], [])):
            return retention.preview(self.root, now=self.now, seconds=30, **kwargs)

    def test_old_clean_repo_is_review_only_and_preserves_all_files(self):
        result = self.inspect()
        self.assertEqual(result["mode"], "PREVIEW_ONLY")
        self.assertFalse(result["deletion_authorized"])
        self.assertEqual(result["review_eligible_count"], 2)
        self.assertEqual({c["kind"] for c in result["candidates"]},
                         {"node_modules", ".next"})
        self.assertTrue(self.modules.is_dir())
        self.assertTrue(self.build.is_dir())
        self.assertTrue((self.repo / ".git").exists())
        self.assertEqual((self.repo / "README.md").read_text(), "preserve me")

    def test_recent_repo_never_eligible(self):
        with patch.object(retention, "_paths_in_use", return_value=([], [])):
            result = retention.preview(self.root, now=time.time() + 86400)
        self.assertTrue(all(c["status"] == "RECENT_ACTIVITY" for c in result["candidates"]))

    def test_dirty_repo_never_eligible(self):
        (self.repo / "README.md").write_text("changed")
        result = self.inspect()
        self.assertTrue(all(c["status"] == "DIRTY_REPOSITORY" for c in result["candidates"]))

    def test_process_activity_protects_candidates(self):
        with patch.object(retention, "_paths_in_use",
                          return_value=(["node server " + str(self.repo)], [])):
            result = retention.preview(self.root, now=self.now)
        self.assertTrue(all(c["status"] == "ACTIVE_PROCESS" for c in result["candidates"]))

    def test_unknown_process_state_fails_closed(self):
        with patch.object(retention, "_paths_in_use", return_value=None):
            result = retention.preview(self.root, now=self.now)
        self.assertEqual(result["process_check"], "UNAVAILABLE")
        self.assertTrue(all(c["status"] == "ACTIVITY_UNKNOWN" for c in result["candidates"]))

    def test_no_lockfile_fails_closed(self):
        (self.repo / "package-lock.json").unlink()
        result = self.inspect()
        self.assertEqual(result["review_eligible_count"], 0)

    def test_symlink_target_not_discovered(self):
        (self.repo / "apps" / "site" / "node_modules").symlink_to(self.modules,
                                                                 target_is_directory=True)
        result = self.inspect()
        self.assertEqual(result["candidate_count"], 2)

    def test_measurement_partial_never_eligible(self):
        with patch.object(retention, "measure", return_value={
            "allocated_bytes": 123, "entries": 2, "complete": False}):
            result = self.inspect()
        self.assertTrue(all(c["status"] == "MEASUREMENT_PARTIAL" for c in result["candidates"]))
        self.assertTrue(result["partial"])
        self.assertEqual(result["measurement_incomplete_count"], 2)

    def test_budgets_report_partial(self):
        result = self.inspect(max_candidates=1)
        self.assertTrue(result["partial"])
        self.assertEqual(result["candidate_count"], 1)

    def test_existing_operator_routes_read_only_preview(self):
        with tempfile.TemporaryDirectory() as state, patch.object(mac_operator, "STATE", Path(state)):
            with patch.object(mac_operator.mac_codex_retention, "preview",
                              return_value={"mode": "PREVIEW_ONLY", "deletion_authorized": False}) as mock:
                result = mac_operator.execute("codex-retention", "unit-retention-01")
                self.assertFalse(result["deletion_authorized"])
                self.assertTrue((Path(state) / "codex-retention-preview.json").exists())
                self.assertEqual(mac_operator.execute("codex-retention", "unit-retention-01")["status"],
                                 "DUPLICATE")
                mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
