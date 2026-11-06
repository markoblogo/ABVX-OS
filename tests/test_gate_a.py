import json
import unittest
from unittest.mock import patch

from abvx_harness.gate_a import PACKETS, transition
from abvx_harness.protected_snapshots import create_snapshot
from abvx_harness.harness import ValidationError
import test_book_three_orchestrator as fixture


class GateATests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture.BookThreeOrchestratorTests()
        self.fixture.setUp()
        self.project = self.fixture.project
        self.root = self.project.parents[1]
        self.auth = "gate-a-owner.md"
        (self.project / self.auth).write_text("GATE_A_START_AUTHORIZED: YES\nNo drafting authorized.\n")
        files = [str((self.project / name).relative_to(self.root)) for name in
                 (fixture.CANON.name, "GOOD_DOG_BOOK_THREE_STATE_V1.json", "GOOD_DOG_BOOK_THREE_EVENT_LEDGER_V1.jsonl")]
        self.snapshot = str(create_snapshot(self.root, "gate-a-test", files))
        self.before = (self.project / "GOOD_DOG_BOOK_THREE_EVENT_LEDGER_V1.jsonl").read_bytes()

    def tearDown(self):
        self.fixture.tearDown()

    def start(self):
        return transition(self.root, "start", self.auth, self.snapshot)

    def test_start_is_not_engine_or_draft_approval(self):
        self.assertEqual(self.start()["current_gate"], "A_IN_PROGRESS")
        state = self.fixture.load_state()
        self.assertEqual(state["gates"]["A"], "PENDING")
        self.assertEqual(state["workflow"]["draft"], "NOT_STARTED")
        self.assertTrue((self.project / "GOOD_DOG_BOOK_THREE_EVENT_LEDGER_V1.jsonl").read_bytes().startswith(self.before))
        self.assertEqual(fixture.evaluate(self.project, "canon")["overall"], "PASS")

    def test_missing_snapshot_refuses_start(self):
        with self.assertRaises(ValueError):
            transition(self.root, "start", self.auth, "absent.json")

    def test_changed_canon_refuses_start(self):
        (self.project / fixture.CANON.name).write_text("changed")
        with self.assertRaisesRegex(ValidationError, "protected input"):
            self.start()

    def test_missing_owner_evidence_refuses_start(self):
        (self.project / self.auth).write_text("No authorization")
        with self.assertRaisesRegex(ValidationError, "explicit"):
            self.start()

    def test_duplicate_start_refused(self):
        self.start()
        with self.assertRaises(ValidationError):
            self.start()

    def test_review_requires_all_packets(self):
        self.start()
        with self.assertRaisesRegex(ValidationError, "missing Gate A output"):
            transition(self.root, "review", self.auth, self.snapshot)

    def test_review_keeps_owner_selection_pending(self):
        self.start()
        for name in PACKETS:
            (self.project / name).write_text("Synthetic Gate A packet\n")
        result = transition(self.root, "review", self.auth, self.snapshot)
        self.assertEqual(result["current_gate"], "A_OWNER_REVIEW")
        self.assertEqual(result["gates_A"], "PENDING")
        self.assertEqual(fixture.evaluate(self.project, "canon")["overall"], "PASS")

    def test_failed_append_rolls_back_exact_bytes(self):
        state_path = self.project / "GOOD_DOG_BOOK_THREE_STATE_V1.json"
        before = state_path.read_bytes()
        with patch("abvx_harness.gate_a.os.fsync", side_effect=OSError("synthetic write failure")):
            with self.assertRaises(OSError):
                self.start()
        self.assertEqual(state_path.read_bytes(), before)
        self.assertEqual((self.project / "GOOD_DOG_BOOK_THREE_EVENT_LEDGER_V1.jsonl").read_bytes(), self.before)

    def selection_ready(self):
        self.start()
        for name in PACKETS:
            (self.project / name).write_text("Synthetic Gate A packet\n")
        transition(self.root, "review", self.auth, self.snapshot)
        self.auth = "engine-owner.md"
        (self.project / self.auth).write_text(
            "ENGINE_SELECTION: C_WITH_A_ACCIDENT_CLAIM\n"
            "ARCHITECTURE_DEVELOPMENT_AUTHORIZED: YES\nPROSE_DRAFTING_AUTHORIZED: NO\n")
        (self.project / "GOOD_DOG_BOOK_THREE_STORY_ENGINE_LOCK_V1.md").write_text("Synthetic selected engine\n")
        files = [str((self.project / name).relative_to(self.root)) for name in
                 (fixture.CANON.name, "GOOD_DOG_BOOK_THREE_STATE_V1.json", "GOOD_DOG_BOOK_THREE_EVENT_LEDGER_V1.jsonl", *PACKETS)]
        self.selection_snapshot = str(create_snapshot(self.root, "selection-test", files))

    def test_selection_authorizes_architecture_not_full_gate_or_draft(self):
        self.selection_ready()
        result = transition(self.root, "select", self.auth, self.selection_snapshot)
        self.assertEqual(result["gates_A"], "PENDING")
        state = self.fixture.load_state()
        self.assertEqual(state["workflow"]["concept"], "PASS")
        self.assertEqual(state["workflow"]["architecture"], "IN_PROGRESS")
        self.assertEqual(state["workflow"]["draft"], "NOT_STARTED")
        self.assertEqual(fixture.evaluate(self.project, "canon")["overall"], "PASS")

    def test_architecture_review_never_authorizes_prose_or_compound_gate(self):
        self.selection_ready()
        transition(self.root, "select", self.auth, self.selection_snapshot)
        (self.project / "GOOD_DOG_BOOK_THREE_CAUSAL_ARCHITECTURE_V1.md").write_text("Synthetic architecture\n")
        (self.project / "GOOD_DOG_BOOK_THREE_ARCHITECTURE_QA_V1.md").write_text("ARCHITECTURE_QA: PASS\n")
        result = transition(self.root, "architecture-review", self.auth, self.selection_snapshot)
        self.assertEqual(result["current_gate"], "A_OWNER_REVIEW")
        self.assertEqual(result["gates_A"], "PENDING")
        state = self.fixture.load_state()
        self.assertEqual(state["workflow"]["architecture"], "PASS")
        self.assertEqual(state["workflow"]["draft"], "NOT_STARTED")
        self.assertEqual(fixture.evaluate(self.project, "canon")["overall"], "PASS")

    def test_architecture_without_pass_evidence_is_refused(self):
        self.selection_ready()
        transition(self.root, "select", self.auth, self.selection_snapshot)
        (self.project / "GOOD_DOG_BOOK_THREE_CAUSAL_ARCHITECTURE_V1.md").write_text("Synthetic architecture\n")
        (self.project / "GOOD_DOG_BOOK_THREE_ARCHITECTURE_QA_V1.md").write_text("ARCHITECTURE_QA: HOLD\n")
        with self.assertRaisesRegex(ValidationError, "QA"):
            transition(self.root, "architecture-review", self.auth, self.selection_snapshot)

    def test_changed_engine_lock_is_refused(self):
        self.selection_ready()
        transition(self.root, "select", self.auth, self.selection_snapshot)
        (self.project / "GOOD_DOG_BOOK_THREE_STORY_ENGINE_LOCK_V1.md").write_text("changed\n")
        with self.assertRaisesRegex(ValidationError, "mismatch|changed"):
            transition(self.root, "architecture-review", self.auth, self.selection_snapshot)
