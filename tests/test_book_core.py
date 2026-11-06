from __future__ import annotations

import contextlib
import hashlib
import io
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from book_test_fixtures import initial_book_three
from abvx_harness import book_three
from abvx_harness.book_core import (
    BookAdapter, canonical_bytes, sha256_bytes, sha256_file, status_book, validate_book,
    validate_events, validate_identity, validate_locks, validate_metrics, validate_modules,
    validate_ref, validate_result, validate_state, validate_state_events,
)
from abvx_harness.harness import ValidationError


NOW = "2026-09-30T12:00:00Z"


def identity(book_id="synthetic-translation", book_type="CONVENTIONAL_TRANSLATION"):
    return {
        "book_id": book_id, "book_type": book_type, "title": "UNKNOWN",
        "source_type": "TRANSLATION", "source_refs": [],
        "languages": {"source": "fr", "target": "en"}, "series": None,
        "rights_status": "UNKNOWN", "target_formats": ["REFLOWABLE_KINDLE_DOCX"],
        "target_retailers": ["KDP"], "created_at": NOW,
    }


def state(book_id="synthetic-translation"):
    return {"schema_version": "abvx-book-state/v1", "identity": identity(book_id),
            "revision": 1, "event_cursor": "e1", "current_stage": "UNKNOWN", "current_gate": "NOT_STARTED",
            "locks": [], "artifacts": [], "validations": [], "formats": [], "owner_gates": [], "extensions": {}}


def ref(root: Path, name: str, payload=b"proof", scope="PROJECT"):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return {"path": name, "sha256": hashlib.sha256(payload).hexdigest(), "scope": scope}


def lock(root, lock_id="l1", kind="SOURCE_LOCK", payload=b"source", supersedes=None):
    source = ref(root, f"{lock_id}.bin", payload)
    accept = ref(root, f"{lock_id}-accept.json", b"accepted")
    result = {"lock_id": lock_id, "kind": kind, "ref": source, "created_at": NOW,
              "authority": "OWNER", "acceptance_ref": accept, "dependencies": []}
    if supersedes is not None:
        result["supersedes_lock_id"] = supersedes
    return result


def event(book_id, sequence, state_after, previous=None, event_id=None, event_type="OBSERVATION", refs=None):
    item = {"schema_version": "abvx-book-event/v1", "book_id": book_id,
            "event_id": event_id or f"e{sequence}", "sequence": sequence,
            "previous_event_sha256": previous, "state_after": state_after,
            "state_after_sha256": sha256_bytes(canonical_bytes(state_after)), "actor": "SYSTEM",
            "event_type": event_type, "timestamp": NOW, "evidence_refs": refs or []}
    item["event_sha256"] = sha256_bytes(canonical_bytes(item))
    return item


class BookCoreTests(unittest.TestCase):
    def test_valid_gd3_compatibility_load_and_status(self):
        with tempfile.TemporaryDirectory() as directory:
            project = initial_book_three(Path(directory))
            state_path = project / book_three.STATE_NAME
            ledger_path = project / book_three.EVENT_NAME
            protected_hashes = (sha256_file(state_path), sha256_file(ledger_path))
            adapter = book_three.core_adapter(project)
            rendered = status_book("gd3", {"gd3": adapter})
            current = json.loads(state_path.read_text())
            self.assertIn(f"CURRENT GATE: {current['current_gate']}", rendered)
            self.assertIn(f"OWNER ACTION REQUIRED: {current['owner_action_required']}", rendered)
            self.assertIn("TEXT LOCK: NONE", rendered)
            self.assertEqual(validate_book("gd3", {"gd3": adapter})["overall"], "REVIEW")
            self.assertEqual(protected_hashes, (sha256_file(state_path), sha256_file(ledger_path)))
    def test_synthetic_translation_identity_loads_without_fiction_fields(self):
        fixture = Path(__file__).parent / "fixtures" / "book_core" / "conventional_translation" / "identity.json"
        value = json.loads(fixture.read_text(encoding="utf-8"))
        validate_identity(value)

    def test_synthetic_translation_lock_policy_keeps_unknown_and_na_distinct(self):
        fixture_root = Path(__file__).parent / "fixtures" / "book_core" / "conventional_translation"
        value = json.loads((fixture_root / "identity.json").read_text(encoding="utf-8"))
        policy = json.loads((fixture_root / "lock-policy.json").read_text(encoding="utf-8"))
        result = state(value["book_id"])
        result["identity"] = value
        locks = validate_state(result, applicability=policy)
        self.assertEqual(locks["TEXT_LOCK"], "UNKNOWN")
        self.assertEqual(locks["CANON_LOCK"], "NOT_APPLICABLE")

    def test_synthetic_translation_uses_generic_read_only_facades(self):
        fixture = Path(__file__).parent / "fixtures" / "book_core" / "conventional_translation" / "identity.json"
        value = json.loads(fixture.read_text(encoding="utf-8"))
        policy = json.loads((fixture.parent / "lock-policy.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            snapshot = state(value["book_id"])
            snapshot["identity"] = value
            ledger = [event(value["book_id"], 1, snapshot)]
            (root / "state.json").write_text(json.dumps(snapshot, sort_keys=True), encoding="utf-8")
            (root / "events.jsonl").write_text(json.dumps(ledger[0], sort_keys=True) + "\n", encoding="utf-8")
            adapter = BookAdapter(value["book_id"], value["book_type"], lambda: "FIXTURE STATUS",
                                  lambda: {"checks": [{"state": "UNKNOWN"}], "overall": "REVIEW"},
                                  value, root, "state.json", "events.jsonl", policy)
            registry = {adapter.book_id: adapter}
            self.assertEqual(status_book(adapter.book_id, registry), "FIXTURE STATUS")
            report = validate_book(adapter.book_id, registry)
            self.assertEqual(report["overall"], "REVIEW")
            self.assertEqual(next(c["state"] for c in report["checks"] if c.get("check_id") == "core-state-events"), "PASS")
            self.assertIn({"check_id": "lock:TEXT_LOCK", "state": "UNKNOWN"}, report["checks"])

    def test_generic_facade_fails_when_registered_ledger_hash_is_broken(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            value = identity()
            snapshot = state(value["book_id"])
            snapshot["identity"] = value
            item = event(value["book_id"], 1, snapshot)
            (root / "state.json").write_text(json.dumps(snapshot, sort_keys=True), encoding="utf-8")
            item["event_sha256"] = "f" * 64
            (root / "events.jsonl").write_text(json.dumps(item, sort_keys=True) + "\n", encoding="utf-8")
            policy = {kind: "NOT_APPLICABLE" for kind in ("SOURCE_LOCK", "CANON_LOCK", "TRANSLATION_LOCK",
                                                            "TEXT_LOCK", "ILLUSTRATION_LOCK", "RENDER_INPUT_LOCK",
                                                            "PRODUCTION_BUILD_LOCK")}
            adapter = BookAdapter(value["book_id"], value["book_type"], lambda: "FIXTURE",
                                  lambda: {"checks": [], "overall": "PASS"}, value, root,
                                  "state.json", "events.jsonl", policy)
            report = validate_book(adapter.book_id, {adapter.book_id: adapter})
            self.assertEqual(report["overall"], "FAIL")

    def test_registered_series_fiction_profile_is_gd3_only_and_composable(self):
        path = Path(__file__).parent / "fixtures" / "book_core" / "series_fiction" / "profile.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        validate_modules(value["book_type"], value["modules"])
        self.assertEqual(value["compatibility_consumer"], "gd3")

    def test_unknown_title_is_valid_explicit_identity(self):
        validate_identity(identity())

    def test_unknown_state_remains_explicit(self):
        value = state()
        value["current_stage"] = "UNKNOWN"
        validate_state(value)
        self.assertEqual(value["current_stage"], "UNKNOWN")

    def test_required_state_envelope_fails_closed(self):
        value = state()
        del value["event_cursor"]
        with self.assertRaisesRegex(ValidationError, "required envelope|required property"):
            validate_state(value)

    def test_format_pass_requires_evidence(self):
        value = state()
        value["formats"] = [{"target_id": "kindle", "format_module": "REFLOWABLE_KINDLE_DOCX",
                             "adapter_version": "v1", "config": {}, "eligibility": "PASS"}]
        with self.assertRaisesRegex(ValidationError, "eligibility evidence|eligibility_evidence"):
            validate_state(value)

    def test_not_applicable_lock_is_not_pass(self):
        statuses = validate_locks([], project_root=None, applicability={"TEXT_LOCK": "NOT_APPLICABLE"})
        self.assertEqual(statuses["TEXT_LOCK"], "NOT_APPLICABLE")
        self.assertNotEqual(statuses["TEXT_LOCK"], "PASS")

    def test_missing_evidence_cannot_produce_pass(self):
        with self.assertRaises(ValidationError):
            validate_result({"state": "PASS", "input_refs": [], "evidence_refs": []})

    def test_bad_project_hash_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            r = ref(Path(directory), "source.txt")
            r["sha256"] = "0" * 64
            with self.assertRaisesRegex(ValidationError, "hash mismatch"):
                validate_ref(r, Path(directory))

    def test_duplicate_event_id_fails(self):
        s = state()
        a = event("synthetic-translation", 1, s)
        b = event("synthetic-translation", 2, s, a["event_sha256"], event_id="e1")
        with self.assertRaisesRegex(ValidationError, "duplicate"):
            validate_events([a, b], book_id="synthetic-translation")

    def test_event_sequence_gap_fails(self):
        a = event("synthetic-translation", 2, state())
        with self.assertRaisesRegex(ValidationError, "sequence gap"):
            validate_events([a], book_id="synthetic-translation")

    def test_broken_predecessor_hash_fails(self):
        a = event("synthetic-translation", 1, state())
        b = event("synthetic-translation", 2, state(), "f" * 64)
        with self.assertRaisesRegex(ValidationError, "predecessor"):
            validate_events([a, b], book_id="synthetic-translation")

    def test_wrong_book_in_event_fails(self):
        a = event("other-book", 1, state("other-book"))
        with self.assertRaisesRegex(ValidationError, "wrong schema or book_id"):
            validate_events([a], book_id="synthetic-translation")

    def test_invalid_state_after_hash_fails(self):
        a = event("synthetic-translation", 1, state())
        a["state_after_sha256"] = "a" * 64
        a["event_sha256"] = sha256_bytes(canonical_bytes({k: v for k, v in a.items() if k != "event_sha256"}))
        with self.assertRaisesRegex(ValidationError, "state-after hash"):
            validate_events([a], book_id="synthetic-translation")

    def test_owner_decision_needs_trusted_evidence_not_actor_label(self):
        untrusted = {"path": "owner-decision.json", "sha256": "a" * 64, "scope": "APPROVED_EXTERNAL_READONLY"}
        a = event("synthetic-translation", 1, state(), event_type="OWNER_DECISION", refs=[untrusted])
        a["actor"] = "OWNER"
        a["event_sha256"] = sha256_bytes(canonical_bytes({k: v for k, v in a.items() if k != "event_sha256"}))
        with self.assertRaisesRegex(ValidationError, "trusted owner-decision evidence"):
            validate_events([a], book_id="synthetic-translation")

    def test_changed_bytes_under_active_lock_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            item = lock(root)
            (root / "l1.bin").write_bytes(b"changed")
            with self.assertRaisesRegex(ValidationError, "hash mismatch"):
                validate_locks([item], project_root=root, applicability={"SOURCE_LOCK": "REQUIRED"})

    def test_successor_lock_supersedes_without_mutating_old(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old = lock(root, "old")
            old_bytes = (root / "old.bin").read_bytes()
            new = lock(root, "new", payload=b"new source", supersedes="old")
            validate_locks([old, new], project_root=root, applicability={"SOURCE_LOCK": "REQUIRED"})
            self.assertEqual(old_bytes, (root / "old.bin").read_bytes())

    def test_inapplicable_lock_need_not_exist(self):
        self.assertEqual(validate_locks([], project_root=None, applicability={"TEXT_LOCK": "NOT_APPLICABLE"})["TEXT_LOCK"],
                         "NOT_APPLICABLE")

    def test_required_missing_lock_is_unknown(self):
        states = validate_locks([], project_root=None, applicability={"TRANSLATION_LOCK": "REQUIRED"})
        self.assertEqual(states["TRANSLATION_LOCK"], "UNKNOWN")

    def test_owner_exception_requires_scope_risk_and_proof(self):
        with self.assertRaises(ValidationError):
            validate_result({"state": "OWNER_ACCEPTED_EXCEPTION", "input_refs": [], "evidence_refs": []})
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            proof = ref(root, "owner.json")
            result = {"state": "OWNER_ACCEPTED_EXCEPTION", "input_refs": [proof], "evidence_refs": [proof],
                      "exception": {"scope": "one format", "accepted_risk": "known", "owner_decision_ref": proof}}
            validate_result(result, root)

    def test_translation_does_not_require_fiction_architecture(self):
        validate_modules("CONVENTIONAL_TRANSLATION", ["CONVENTIONAL_TRANSLATION"])

    def test_fiction_module_is_not_required_for_translation_locks(self):
        validate_modules("CONVENTIONAL_TRANSLATION", ["CONVENTIONAL_TRANSLATION"])
        self.assertEqual(validate_locks([], project_root=None, applicability={"TRANSLATION_LOCK": "REQUIRED"})["TRANSLATION_LOCK"], "UNKNOWN")

    def test_fiction_profile_can_extend_original_fiction(self):
        validate_modules("SERIES_FICTION", ["ORIGINAL_FICTION", "SERIES_FICTION"])

    def test_toki_pona_module_is_not_activated(self):
        with self.assertRaisesRegex(ValidationError, "not activated"):
            validate_modules("CONVENTIONAL_TRANSLATION", ["CONVENTIONAL_TRANSLATION", "TOKI_PONA_TRANSLATION"])

    def test_pictiq_is_optional_for_series_fiction(self):
        validate_modules("SERIES_FICTION", ["ORIGINAL_FICTION", "SERIES_FICTION"])
        validate_modules("SERIES_FICTION", ["ORIGINAL_FICTION", "SERIES_FICTION", "PICTIQ"])

    def test_unknown_extension_cannot_certify_pass(self):
        value = state()
        value["extensions"] = {"unknown.module": {"state": "PASS"}}
        with self.assertRaisesRegex(ValidationError, "cannot certify PASS"):
            validate_state(value)

    def test_unknown_book_fails_without_filesystem_guessing(self):
        with self.assertRaisesRegex(ValidationError, "unknown registered book"):
            status_book("not-registered", {})

    def test_null_metrics_remain_null(self):
        result = validate_metrics({})
        self.assertIsNone(result["actual_cost"])
        self.assertIsNone(result["owner_minutes"])

    def test_metrics_hook_is_accepted_as_optional_state_lane(self):
        value = state()
        value["metrics"] = [{"stage_id": "concept", "measurement_basis": "UNKNOWN", "api_calls": None}]
        validate_state(value)

    def test_historical_timestamps_do_not_become_owner_effort(self):
        result = validate_metrics({"stage_started_at": NOW, "stage_completed_at": NOW})
        self.assertIsNone(result["owner_minutes"])

    def test_state_event_agreement_checks_cursor_and_revision(self):
        s = state()
        e = event("synthetic-translation", 1, s)
        self.assertEqual(validate_state_events(s, [e])["TEXT_LOCK"], "UNKNOWN")
        s["event_cursor"] = "wrong"
        e["state_after"] = s
        e["state_after_sha256"] = sha256_bytes(canonical_bytes(s))
        e["event_sha256"] = sha256_bytes(canonical_bytes({k: v for k, v in e.items() if k != "event_sha256"}))
        with self.assertRaisesRegex(ValidationError, "projection/cursor"):
            validate_state_events(s, [e])

    def test_translation_lock_policy_is_distinct_from_fiction(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            src, trans = lock(root, "src", "SOURCE_LOCK"), lock(root, "trans", "TRANSLATION_LOCK")
            statuses = validate_locks([src, trans], project_root=root,
                                      applicability={"SOURCE_LOCK": "REQUIRED", "TRANSLATION_LOCK": "REQUIRED",
                                                     "TEXT_LOCK": "UNKNOWN"})
            self.assertEqual(statuses["SOURCE_LOCK"], "PASS")
            self.assertEqual(statuses["TRANSLATION_LOCK"], "PASS")
            self.assertEqual(statuses["TEXT_LOCK"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
