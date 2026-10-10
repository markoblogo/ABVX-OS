from __future__ import annotations

import json
import io
import stat
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from abvx_harness.__main__ import main
from abvx_harness.protected_snapshots import (
    create_snapshot,
    gate_status,
    recheck_snapshot,
)


class ProtectedSnapshotTests(unittest.TestCase):
    def started_after(self, root, snapshot):
        record = json.loads((root / snapshot).read_text(encoding="utf-8"))
        return record["captured_at"]

    def test_explicit_file_snapshot_rechecks_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "protected.txt").write_text("stable", encoding="utf-8")
            snapshot = create_snapshot(root, "unit-test", ["protected.txt"])
            self.assertEqual((root / snapshot).stat().st_mode & stat.S_IWUSR, 0)
            result = recheck_snapshot(root, snapshot)
            self.assertEqual([entry["status"] for entry in result["files"]], ["UNCHANGED"])
            self.assertEqual(gate_status("PASS", True, snapshot, "REVIEW", root=root,
                                         run_started_at=self.started_after(root, snapshot)), "PASS")

    def test_changed_protected_file_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "protected.txt"
            target.write_text("before", encoding="utf-8")
            snapshot = create_snapshot(root, "changed", ["protected.txt"])
            target.write_text("after", encoding="utf-8")
            result = recheck_snapshot(root, snapshot)
            self.assertEqual(result["files"][0]["status"], "CHANGED")
            self.assertEqual(gate_status("PASS", True, snapshot, "REVIEW", root=root,
                                         run_started_at=self.started_after(root, snapshot)), "HOLD")

    def test_missing_protected_file_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "protected.txt"
            target.write_text("before", encoding="utf-8")
            snapshot = create_snapshot(root, "missing", ["protected.txt"])
            target.unlink()
            self.assertEqual(recheck_snapshot(root, snapshot)["files"][0]["status"], "MISSING")
            self.assertEqual(gate_status("PASS", True, snapshot, "REVIEW", root=root,
                                         run_started_at=self.started_after(root, snapshot)), "HOLD")

    def test_required_snapshot_missing_downgrades_to_policy_status(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(gate_status("PASS", True, None, "REVIEW", root=root), "REVIEW")
            self.assertEqual(gate_status("PASS", True, None, "HOLD", root=root), "HOLD")
            self.assertEqual(gate_status("FAIL", True, None, "REVIEW", root=root), "FAIL")

    def test_snapshot_created_after_run_start_is_not_eligible_for_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "protected.txt").write_text("stable", encoding="utf-8")
            snapshot = create_snapshot(root, "late", ["protected.txt"])
            self.assertEqual(gate_status("PASS", True, snapshot, "REVIEW", root=root,
                                         run_started_at="2000-01-01T00:00:00Z"), "REVIEW")

    def test_missing_at_snapshot_cannot_become_clean_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            snapshot = create_snapshot(root, "initially-missing", ["protected.txt"])
            record = json.loads((root / snapshot).read_text(encoding="utf-8"))
            self.assertEqual(record["files"][0]["sha256"], None)
            self.assertEqual(recheck_snapshot(root, snapshot)["files"][0]["status"], "MISSING")
            self.assertEqual(gate_status("PASS", True, snapshot, "REVIEW", root=root,
                                         run_started_at=self.started_after(root, snapshot)), "HOLD")

    def test_empty_or_implicit_scope_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                create_snapshot(Path(directory), "no-files", [])

    def test_cli_snapshot_and_recheck_use_only_explicit_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "keep.txt").write_text("keep", encoding="utf-8")
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(main(["protect", "snapshot", "cli", "keep.txt"], root=root), 0)
            snapshot = output.getvalue().strip()
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(main(["protect", "recheck", snapshot], root=root), 0)
            self.assertEqual(output.getvalue().strip(), "UNCHANGED: keep.txt")

    def test_cli_required_gate_without_snapshot_cannot_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            output = io.StringIO()
            with redirect_stdout(output):
                result = main(["protect", "gate", "PASS", "--required", "true",
                               "--missing-policy", "HOLD", "--started-at", "2026-09-30T18:30:14Z"], root=Path(directory))
            self.assertEqual(result, 1)
            self.assertEqual(output.getvalue().strip(), "FINAL STATUS: HOLD")


if __name__ == "__main__":
    unittest.main()
