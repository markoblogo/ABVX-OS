from __future__ import annotations

import contextlib
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from book_test_fixtures import initial_book_three
from abvx_harness.book_three import (
    append_event,
    build_id,
    create_build_directory,
    evaluate,
    initial_state,
    make_validator_result,
    render_status,
    state_projection,
    validate_retailer_transition,
    image_safe_area,
    external_action_allowed,
    dialogue_findings,
    make_build_record,
)
from abvx_harness.__main__ import main as cli_main


ROOT = Path(__file__).resolve().parents[1]
CANON_NAME = "GOOD_DOG_SERIES_PRODUCTION_CANON_V1.md"
CANON = Path(CANON_NAME)  # Name compatibility for Gate A synthetic fixtures.


class BookThreeOrchestratorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.project = Path(self.temp.name) / "books" / "rn10-003"
        initial_book_three(self.project)

    def tearDown(self):
        self.temp.cleanup()

    def load_state(self):
        path = self.project / "GOOD_DOG_BOOK_THREE_STATE_V1.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def save_state(self, value):
        (self.project / "GOOD_DOG_BOOK_THREE_STATE_V1.json").write_text(json.dumps(value), encoding="utf-8")

    def evidence(self, name, content):
        path = self.project / name
        path.write_text(json.dumps(content), encoding="utf-8")
        return {"path": name, "sha256": sha(path)}

    def record(self, state, *, event_type="CHECK_RECORDED", evidence=None, gate="NONE", actor="system", fmt=None):
        path = self.project / "GOOD_DOG_BOOK_THREE_EVENT_LEDGER_V1.jsonl"
        events = [json.loads(line) for line in path.read_text().splitlines()]
        event_id = f"gd3-{len(events) + 1:04d}"
        state["event_cursor"] = event_id
        self.save_state(state)
        event = {**events[-1], "book_id": "gd3", "event_id": event_id, "event_type": event_type,
                 "previous_state": events[-1]["new_state"], "new_state": state_projection(state),
                 "actor": actor, "owner_gate": gate, "evidence": evidence or [],
                 "decision": "Synthetic test fixture transition only."}
        if fmt is not None:
            event["format"] = fmt
        append_event(self.project, event)

    def checks(self, stage="all"):
        return {c["check_id"]: c for c in evaluate(self.project, stage)["checks"]}

    def test_every_stage_route_runs_and_is_read_only(self):
        before = {p.name: sha(p) for p in self.project.glob('*.json*')}
        for stage in ("all", "canon", "text", "illustrations", "kindle", "print", "metadata", "retailer"):
            with self.subTest(stage=stage):
                self.assertNotEqual(evaluate(self.project, stage)["overall"], "FAIL")
        self.assertEqual(before, {p.name: sha(p) for p in self.project.glob('*.json*')})

    def test_full_state_digest_detects_nonstage_mutation(self):
        state = self.load_state()
        state["metadata"]["isbn"]["value"] = "invented"
        self.save_state(state)
        self.assertEqual(self.checks("canon")["event-state-consistency"]["state"], "FAIL")

    def test_schema_missing_workflow_and_malformed_hash_fail(self):
        state = self.load_state()
        del state["workflow"]
        self.save_state(state)
        self.assertEqual(self.checks("canon")["state-schema"]["state"], "FAIL")
        state = initial_state(self.project)
        state["series_publication_source"]["sha256"] = "z" * 64
        self.save_state(state)
        self.assertEqual(self.checks("canon")["state-schema"]["state"], "FAIL")

    def test_invalid_event_timestamp_fails_closed(self):
        path = self.project / "GOOD_DOG_BOOK_THREE_EVENT_LEDGER_V1.jsonl"
        event = json.loads(path.read_text())
        event["timestamp"] = "not-a-date"
        path.write_text(json.dumps(event) + "\n")
        self.assertEqual(self.checks("canon")["event-state-consistency"]["state"], "FAIL")

    def test_corrupt_ledger_and_changed_evidence_fail_closed(self):
        path = self.project / "GOOD_DOG_BOOK_THREE_EVENT_LEDGER_V1.jsonl"
        original = path.read_bytes()
        path.write_bytes(original + b'{bad json}\n')
        self.assertEqual(self.checks("canon")["event-state-consistency"]["state"], "FAIL")
        path.write_bytes(original)
        (self.project / CANON_NAME).write_text("changed")
        self.assertEqual(self.checks("canon")["event-state-consistency"]["state"], "FAIL")

    def test_approved_gate_requires_owner_evidence(self):
        state = self.load_state()
        state["gates"]["A"] = "APPROVED"
        self.record(state)
        self.assertEqual(self.checks("canon")["owner-gates-and-editorial-order"]["state"], "FAIL")

    def test_gate_a_authorization_does_not_require_title_or_art_count(self):
        state = self.load_state()
        state["gates"]["A"] = "APPROVED"
        proof = self.evidence("owner-a.json", {"owner": "owner", "gate": "A", "decision": "APPROVED"})
        self.record(state, event_type="OWNER_GATE_APPROVED", evidence=[proof], gate="A", actor="owner")
        self.assertEqual(self.checks("canon")["owner-gates-and-editorial-order"]["state"], "PASS")
        self.assertEqual(state["metadata"]["title"]["value"], "UNKNOWN")
        self.assertNotIn("count", state["illustrations"])

    def test_editorial_stages_cannot_be_combined_or_skipped(self):
        state = self.load_state()
        state["workflow"]["line_edit"] = "IN_PROGRESS"
        self.record(state)
        result = self.checks("text")["owner-gates-and-editorial-order"]
        self.assertEqual(result["state"], "FAIL")
        self.assertIn("line_edit requires", " ".join(result["observed"]))

    def test_retailer_invalid_jump_and_owner_gate_f_are_enforced(self):
        for old, new in (("NOT_STARTED", "LIVE"), ("LOCAL_QA_PASS", "IN_REVIEW"), ("IN_REVIEW", "LOCAL_QA_PASS")):
            with self.subTest(old=old, new=new), self.assertRaises(ValueError):
                validate_retailer_transition(old, new, evidence_available=True)
        with self.assertRaises(ValueError):
            validate_retailer_transition("KDP_PREVIEW_PASS", "SUBMISSION_AUTHORIZED", evidence_available=True)
        validate_retailer_transition("KDP_PREVIEW_PASS", "SUBMISSION_AUTHORIZED", evidence_available=True, owner_authorized=True)

    def test_retailer_live_requires_evidence_even_when_unchanged(self):
        for old in ("SUBMITTED", "IN_REVIEW", "PUBLISHING", "LIVE"):
            with self.subTest(old=old), self.assertRaises(ValueError):
                validate_retailer_transition(old, "LIVE", evidence_available=False)
        validate_retailer_transition("IN_REVIEW", "LIVE", evidence_available=True)
        validate_retailer_transition("PUBLISHING", "LIVE", evidence_available=True)

    def test_live_proof_does_not_invent_uploaded_binary_hash(self):
        state = self.load_state()
        proof = self.evidence("retailer-observation.json", {"status": "LIVE", "observed_at": "2026-09-30T00:00:00Z"})
        for phase in ("LOCAL_QA_PASS", "KDP_PREVIEW_PENDING", "KDP_PREVIEW_PASS", "SUBMISSION_AUTHORIZED", "SUBMITTED", "IN_REVIEW", "PUBLISHING", "LIVE"):
            record = state["formats"]["kindle"]
            record["retailer_state"] = phase
            if phase == "LOCAL_QA_PASS":
                record["local_qa"].update(state=phase, evidence_path=proof["path"], output_sha256="a" * 64)
            elif phase.startswith("KDP_PREVIEW"):
                record["kdp_preview"].update(state=phase, evidence_path=proof["path"], upload_sha256="a" * 64)
            elif phase in {"SUBMISSION_AUTHORIZED", "SUBMITTED"}:
                record["submission"].update(state=phase, evidence_path=proof["path"], upload_sha256="a" * 64)
            else:
                record["publication"].update(state=phase, evidence_path=proof["path"], observed_at="2026-09-30T00:00:00Z")
            if phase == "SUBMISSION_AUTHORIZED":
                state["gates"]["F"] = "APPROVED"
            self.record(state, evidence=[proof], event_type="OWNER_GATE_APPROVED" if phase == "SUBMISSION_AUTHORIZED" else "RETAILER_OBSERVED",
                        gate="F" if phase == "SUBMISSION_AUTHORIZED" else "NONE", actor="owner" if phase == "SUBMISSION_AUTHORIZED" else "system", fmt="kindle")
            if phase in {"IN_REVIEW", "PUBLISHING", "LIVE"}:
                self.assertEqual(self.checks("retailer")["kindle-publication"]["state"], "PASS")
        checks = self.checks("retailer")
        self.assertEqual(checks["kindle-upload-binary-provenance"]["state"], "UNKNOWN")
        self.assertEqual(checks["event-state-consistency"]["state"], "PASS")

    def test_title_limit_is_external_and_cannot_erase_local_status(self):
        state = self.load_state()
        proof = self.evidence("title-limit.json", {"message": "Title creation is temporarily limited."})
        state["retailer_constraints"] = [{"type": "KDP_TITLE_CREATION_LIMIT", "classification": "EXTERNAL_RETAILER_BLOCK", "format": "kindle",
                                           "observed_at": "2026-09-30T00:00:00Z", "reset_at": None, "evidence": proof, "status": "ACTIVE"}]
        self.record(state, evidence=[proof])
        self.assertFalse(external_action_allowed(state, "kindle"))
        self.assertTrue(external_action_allowed(state, "paperback"))
        self.assertEqual(state["formats"]["kindle"]["local_qa"]["state"], "NOT_STARTED")
        self.assertEqual(self.checks("retailer")["kindle-KDP_TITLE_CREATION_LIMIT"]["state"], "PASS")
        state["retailer_constraints"][0]["reset_at"] = "2020-01-01T00:00:00Z"
        self.assertFalse(external_action_allowed(state, "kindle"))

    def test_fixed_layout_route_fails_without_explicit_owner_exception(self):
        state = self.load_state()
        state["production_config"]["kindle_route"] = "PRINT_REPLICA"
        state["production_config"]["kindle_primary_source"] = "PDF"
        self.record(state)
        self.assertEqual(self.checks("kindle")["GOOD_DOGS_KINDLE_ROUTE"]["state"], "FAIL")
        proof = self.evidence("owner-route.json", {"owner": "owner", "exception": "fixture only"})
        state["production_config"]["kindle_route_exception"] = {"owner": "owner", "reason": "Explicit synthetic exception", "evidence": proof}
        self.record(state, evidence=[proof])
        self.assertEqual(self.checks("kindle")["GOOD_DOGS_KINDLE_ROUTE"]["state"], "OWNER_ACCEPTED_EXCEPTION")

    def test_visible_contents_parity_and_navigation_are_independent(self):
        state = self.load_state()
        self.assertIsNone(state["contents_navigation"]["paperback"]["visible_contents"]["enabled"])
        checks = self.checks("all")
        self.assertEqual(checks["VISIBLE_CONTENTS"]["state"], "UNKNOWN")
        self.assertEqual(checks["DIGITAL_NAVIGATION_REQUIRED"]["state"], "PASS")
        self.assertEqual(checks["DIGITAL_NAVIGATION"]["state"], "NOT_APPLICABLE")
        state["formats"]["paperback"]["local_qa"]["state"] = "LOCAL_QA_PASS"
        state["contents_navigation"]["paperback"]["visible_contents"] = {"enabled": True, "state": "PASS"}
        state["contents_navigation"]["paperback"]["contents_parity"] = {"enabled": True, "state": "PASS"}
        self.record(state)
        checks = self.checks("print")
        self.assertEqual(checks["VISIBLE_CONTENTS"]["state"], "FAIL")
        self.assertEqual(checks["paperback-CONTENTS_PARITY"]["state"], "FAIL")

    def test_print_pass_requires_geometry_evidence(self):
        state = self.load_state()
        state["formats"]["paperback"]["local_qa"]["state"] = "LOCAL_QA_PASS"
        self.record(state)
        self.assertEqual(self.checks("print")["KDP_NON_BLEED_IMAGE_SAFE_AREA_CHECK"]["state"], "FAIL")

    def test_book_two_six_margin_escapes_fail_and_repairs_pass(self):
        fixture = json.loads((ROOT / "tests/fixtures/book_three/book_two_margin_escape.json").read_text())
        for bbox, expected in ((fixture["escaped_bbox_pt"], "FAIL"), (fixture["repaired_bbox_pt"], "PASS")):
            results = image_safe_area([{"page": page, "bbox_pt": bbox} for page in fixture["pages"]], fixture["safe_box_pt"], fixture["clearance_pt"])
            self.assertEqual([r["page"] for r in results], [4, 91, 97, 160, 213, 251])
            self.assertEqual([r["state"] for r in results], [expected] * 6)

    def test_touching_safe_boundary_and_nonfinite_geometry_fail(self):
        self.assertEqual(image_safe_area([{"page": 1, "bbox_pt": [36, 18, 324, 576]}], [36, 18, 324, 576], 0)[0]["state"], "FAIL")
        with self.assertRaises(ValueError):
            image_safe_area([], [0, 0, float("nan"), 100], 0)

    def dog_line(self):
        text = "Where do I listen?"
        return text, {"asset_id": "fixture-comic", "panel": 1, "speaker": "Pixel", "species": "DOG", "channel": "PICTIQ",
                      "source_span": {"start": 0, "end": len(text), "text": text, "sha256": hashlib.sha256(text.encode()).hexdigest()}}

    def test_pictiq_missing_composer_is_hold(self):
        text, line = self.dog_line()
        self.assertIn("PICTIQ_HOLD", dialogue_findings(self.project, text, [line])[0])

    def test_pictiq_exact_owner_mapping_passes_then_mismatch_fails(self):
        text, line = self.dog_line()
        output = self.evidence("composer.json", {"owner_supplied": True})
        approval_data = {"approved": True, "owner": "owner", "asset_id": line["asset_id"], "panel": line["panel"], "speaker": line["speaker"],
                         "source_span_sha256": line["source_span"]["sha256"], "composer_sha256": output["sha256"]}
        approval = self.evidence("composer-approved.json", approval_data)
        line["composer"] = {"output_ref": output, "approval_ref": approval}
        self.assertEqual(dialogue_findings(self.project, text, [line]), [])
        line["panel"] = 2
        self.assertIn("mapping mismatch", dialogue_findings(self.project, text, [line])[0])

    def test_dialogue_wrong_source_and_species_channel_fail(self):
        text, line = self.dog_line()
        line["source_span"]["text"] = "Different"
        self.assertIn("source span mismatch", dialogue_findings(self.project, text, [line])[0])
        for species, channel in (("DOG", "ENGLISH"), ("HUMAN", "PICTIQ"), ("SYSTEM", "PICTIQ")):
            text, line = self.dog_line()
            line.update(species=species, channel=channel)
            self.assertTrue(dialogue_findings(self.project, text, [line]))

    def test_wrong_output_author_surface_fails(self):
        state = self.load_state()
        state["production_config"]["author_surfaces"]["amazon"] = "Sminx Jonahtan J."
        self.record(state)
        self.assertEqual(self.checks("metadata")["author-surface-mapping"]["state"], "FAIL")

    def test_text_lock_hash_drift_fails(self):
        state = self.load_state()
        ref = self.evidence("lock.md", {"synthetic": "not a novel"})
        state["text_lock"] = {"status": "LOCKED", **ref}
        state["text_lock"]["sha256"] = "f" * 64
        self.record(state)
        self.assertEqual(self.checks("text")["text-lock"]["state"], "FAIL")

    def test_instrumentation_is_unknown_until_measured_and_negative_fails(self):
        state = self.load_state()
        self.assertTrue(all(v is None for v in state["instrumentation"].values()))
        state["instrumentation"]["api_cost_usd"] = -1
        self.save_state(state)
        self.assertEqual(self.checks("canon")["state-schema"]["state"], "FAIL")

    def test_current_v6_v4_publication_regression_and_hash_drift(self):
        check = self.checks("canon")["current-series-publication-baseline"]
        self.assertEqual(check["state"], "PASS")
        self.assertEqual(check["observed"]["kindle_asin"], "B0HLJ9VMWB")
        self.assertEqual(check["observed"]["paperback_asin"], "B0HLLKRHRW")
        self.assertEqual(check["observed"]["series"], "LIVE")
        (self.project / "GOOD_DOGS_CANONICAL_MANIFEST_V6.json").write_text('{}')
        self.assertEqual(self.checks("canon")["current-series-publication-baseline"]["state"], "FAIL")

    def test_build_fingerprint_changes_with_each_canonical_input(self):
        args = {"text_lock_sha256": "a" * 64, "asset_manifest_sha256": "b" * 64, "production_config": {"route": "DOCX"}, "tool_version": "v1"}
        original = build_id("gd3", **args)
        for field, value in (("text_lock_sha256", "c" * 64), ("asset_manifest_sha256", "d" * 64), ("production_config", {"route": "PDF"}), ("tool_version", "v2")):
            self.assertNotEqual(original, build_id("gd3", **{**args, field: value}))

    def test_build_record_carries_hashes_outputs_and_validator_records(self):
        lock = self.evidence("fixture-lock.json", {})
        assets = self.evidence("fixture-assets.json", {})
        output = self.evidence("fixture-output.json", {"output": True})
        result = make_validator_result("fixture", "PASS", evidence_path=output["path"], input_sha256=[lock["sha256"]],
                                       output_sha256=[output["sha256"]], evidence_available=True)
        record = make_build_record(self.project, text_lock_ref=lock, asset_manifest_ref=assets, production_config={"route": "DOCX"},
                                   tool_version="fixture-v1", output_refs=[output], validator_records=[result])
        self.assertEqual(record["outputs"], [output])
        self.assertEqual(record["validators"], [result])
        self.assertEqual(len(record["production_config_sha256"]), 64)
        (self.project / output["path"]).write_text('changed')
        with self.assertRaises(ValueError):
            make_build_record(self.project, text_lock_ref=lock, asset_manifest_ref=assets, production_config={}, tool_version="v1", output_refs=[output], validator_records=[result])

    def locked_fixture(self):
        state = self.load_state()
        for gate in "ABC":
            proof = self.evidence(f"owner-{gate}.json", {"owner": "owner", "gate": gate, "approved": True})
            state["gates"][gate] = "APPROVED"
            self.record(state, event_type="OWNER_GATE_APPROVED", evidence=[proof], gate=gate, actor="owner")
        state["workflow_evidence"] = {}
        for stage in ("developmental", "compression_integrity", "line_edit"):
            proof = self.evidence(f"{stage}-qa.json", {"function": stage, "state": "PASS"})
            state["workflow"][stage] = "PASS"
            state["workflow_evidence"][stage] = proof
            self.record(state, evidence=[proof])
        ref = self.evidence("synthetic-text-lock.json", {"synthetic_fixture": True})
        state["text_lock"] = {"status": "LOCKED", **ref}
        self.record(state, event_type="TEXT_LOCKED", evidence=[ref])
        return state

    def test_title_limit_preserves_valid_local_qa_pass(self):
        state = self.locked_fixture()
        output = self.evidence("synthetic-output.docx", {"synthetic_fixture": True})
        qa = self.evidence("kindle-qa.json", {"output_ref": output})
        nav = self.evidence("kindle-navigation.json", {"digital_navigation": "PASS"})
        state["contents_navigation"]["kindle"]["digital_navigation"] = {"state": "PASS", "evidence_path": nav["path"]}
        state["formats"]["kindle"]["local_qa"] = {"state": "LOCAL_QA_PASS", "evidence_path": qa["path"], "output_sha256": output["sha256"]}
        state["formats"]["kindle"]["retailer_state"] = "LOCAL_QA_PASS"
        self.record(state, evidence=[qa, nav])
        self.assertEqual(self.checks("kindle")["kindle-local-qa"]["state"], "PASS")
        limit = self.evidence("limit.json", {"observed": "KDP_TITLE_CREATION_LIMIT"})
        state["retailer_constraints"] = [{"type": "KDP_TITLE_CREATION_LIMIT", "classification": "EXTERNAL_RETAILER_BLOCK", "format": "kindle",
                                           "observed_at": "2026-09-30T00:00:00Z", "reset_at": None, "evidence": limit, "status": "ACTIVE"}]
        self.record(state, evidence=[limit])
        self.assertFalse(external_action_allowed(state, "kindle"))
        self.assertEqual(self.checks("kindle")["kindle-local-qa"]["state"], "PASS")

    def test_status_blocks_future_technical_failure_without_repairing_state(self):
        state = self.load_state()
        state["production_config"]["kindle_primary_source"] = "PDF"
        self.record(state)
        before = sha(self.project / "GOOD_DOG_BOOK_THREE_STATE_V1.json")
        self.assertIn("GOOD_DOGS_KINDLE_ROUTE", render_status(self.project))
        self.assertEqual(before, sha(self.project / "GOOD_DOG_BOOK_THREE_STATE_V1.json"))

    def test_safe_area_geometry_is_bound_to_exact_binary(self):
        state = self.locked_fixture()
        output = self.evidence("synthetic-print.pdf", {"synthetic_fixture": True})
        qa = self.evidence("print-qa.json", {"output_ref": output})
        state["formats"]["paperback"]["local_qa"] = {"state": "LOCAL_QA_PASS", "evidence_path": qa["path"], "output_sha256": output["sha256"]}
        state["formats"]["paperback"]["retailer_state"] = "LOCAL_QA_PASS"
        state["contents_navigation"]["paperback"]["visible_contents"]["enabled"] = False
        spec = {"state": "APPROVED", "safe_box_pt": [36, 18, 324, 576], "clearance_pt": 0, "authority": "synthetic approved fixture"}
        state["production_config"]["print_safe_area"] = spec
        geometry = {"output_ref": output, "trim_pt": [396, 612], "image_inventory_complete": True,
                    "placements": [{"page": 4, "bbox_pt": [43.2, 73.8, 309.6, 464.4]}]}
        proof = self.evidence("print-geometry.json", geometry)
        state["production_config"]["print_geometry_evidence"] = proof
        self.record(state, evidence=[qa, proof])
        self.assertEqual(self.checks("print")["KDP_NON_BLEED_IMAGE_SAFE_AREA_CHECK"]["state"], "PASS")
        geometry["output_ref"] = self.evidence("wrong-output.pdf", {"wrong": True})
        state["production_config"]["print_geometry_evidence"] = self.evidence("wrong-geometry.json", geometry)
        self.record(state, evidence=[state["production_config"]["print_geometry_evidence"]])
        self.assertEqual(self.checks("print")["KDP_NON_BLEED_IMAGE_SAFE_AREA_CHECK"]["state"], "FAIL")

    def test_valid_initial_state_loads(self):
        report = evaluate(self.project, "all")
        self.assertFalse([c for c in report["checks"] if c["state"] == "FAIL"])

    def test_not_started_content_remains_unknown(self):
        report = evaluate(self.project, "text")
        self.assertEqual(next(c["state"] for c in report["checks"] if c["check_id"] == "text-lock"), "NOT_APPLICABLE")

    def test_initial_state_carries_every_requested_stage_without_invention(self):
        state = self.load_state()
        self.assertEqual(state["current_gate"], "A_PENDING")
        self.assertTrue(all(value == "NOT_STARTED" for value in state["workflow"].values()))
        self.assertTrue(all(value is None for value in state["instrumentation"].values()))
        self.assertEqual(state["metadata"]["title"]["value"], "UNKNOWN")
        self.assertEqual(state["continuity_packet"]["path"], None)
        self.assertEqual(state["drafting_model"]["causal_checkpoints"], 3)

    def test_canon_conflict_blocks(self):
        state = self.load_state()
        state["series"]["name"]["value"] = "Conflicting Series"
        self.save_state(state)
        self.assertIn("FAIL", [c["state"] for c in evaluate(self.project, "canon")["checks"]])

    def test_invalid_series_position_blocks(self):
        state = self.load_state()
        state["series"]["position"]["value"] = 2
        self.save_state(state)
        self.assertIn("FAIL", [c["state"] for c in evaluate(self.project, "canon")["checks"]])

    def test_wrong_author_surface_mapping_blocks(self):
        state = self.load_state()
        state["metadata"]["author_display"]["value"] = "Sminx Jonahtan"
        self.save_state(state)
        self.assertIn("FAIL", [c["state"] for c in evaluate(self.project, "metadata")["checks"]])

    def test_missing_evidence_cannot_be_pass(self):
        result = make_validator_result("fixture", "PASS", evidence_path=None, input_sha256=[])
        self.assertEqual(result["state"], "UNKNOWN")

    def test_event_state_disagreement_blocks(self):
        path = self.project / "GOOD_DOG_BOOK_THREE_EVENT_LEDGER_V1.jsonl"
        event = json.loads(path.read_text().strip())
        event["new_state"]["current_stage"] = "DRAFTING"
        path.write_text(json.dumps(event) + "\n", encoding="utf-8")
        self.assertIn("FAIL", [c["state"] for c in evaluate(self.project, "all")["checks"]])

    def test_local_qa_cannot_be_kdp_pass_without_evidence(self):
        state = self.load_state()
        state["formats"]["kindle"]["local_qa"] = {"state": "LOCAL_QA_PASS", "evidence_path": None, "output_sha256": None}
        state["formats"]["kindle"]["kdp_preview"] = {"state": "KDP_PREVIEW_PASS", "evidence_path": None, "upload_sha256": None}
        self.save_state(state)
        self.assertIn("FAIL", [c["state"] for c in evaluate(self.project, "kindle")["checks"]])

    def test_in_review_cannot_be_live_without_retailer_evidence(self):
        state = self.load_state()
        state["formats"]["paperback"]["submission"] = {"state": "IN_REVIEW", "evidence_path": None, "upload_sha256": None}
        state["formats"]["paperback"]["publication"] = {"state": "LIVE", "evidence_path": None, "observed_at": None, "upload_sha256": None}
        self.save_state(state)
        self.assertIn("FAIL", [c["state"] for c in evaluate(self.project, "print")["checks"]])

    def test_status_identifies_gate_a_next_action(self):
        status = render_status(self.project)
        self.assertIn("OWNER ACTION REQUIRED: AUTHORIZE GATE A — CONCEPT + ARCHITECTURE DEVELOPMENT", status)
        self.assertIn("NEXT ALLOWED ACTION: BUILD CANONICAL BOOK THREE CONTEXT PACKET AND DEVELOP CONCEPT OPTIONS", status)

    def test_status_cli_does_not_change_book_one_or_two(self):
        protected = [self.project / CANON_NAME,
                     self.project / "GOOD_DOGS_CANONICAL_MANIFEST_V6.json",
                     self.project / "GOOD_DOG_SERIES_PUBLICATION_CANON_V4.json"]
        for name in ("book-one-sentinel.txt", "book-two-sentinel.txt"):
            path = self.project / name
            path.write_text("Synthetic earlier-book artifact; must remain unchanged.")
            protected.append(path)
        before = {str(path): sha(path) for path in protected}
        with contextlib.redirect_stdout(io.StringIO()):
            result = cli_main(["book", "status", "gd3"], root=Path(self.temp.name))
        self.assertEqual(result, 0)
        self.assertEqual(before, {str(path): sha(path) for path in protected})

    def test_validate_cli_stage_is_read_only_and_runnable(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = cli_main(["book", "validate", "gd3", "--stage", "canon"], root=Path(self.temp.name))
        self.assertEqual(result, 0)
        self.assertIn("series-canon: PASS", output.getvalue())

    def test_build_id_is_stable_and_directory_is_never_overwritten(self):
        args = {"text_lock_sha256": "a" * 64, "asset_manifest_sha256": "b" * 64,
                "production_config": {"trim": "5.5x8.5"}, "tool_version": "foundation-v1"}
        self.assertEqual(build_id("gd3", **args), build_id("gd3", **args))
        first = create_build_directory(self.project, "gd3", **args)
        self.assertTrue(first.is_dir())
        with self.assertRaises(FileExistsError):
            create_build_directory(self.project, "gd3", **args)

    def test_append_event_preserves_previous_bytes_and_rejects_duplicate_id(self):
        path = self.project / "GOOD_DOG_BOOK_THREE_EVENT_LEDGER_V1.jsonl"
        original = path.read_bytes()
        state = self.load_state()
        state["event_cursor"] = "gd3-0002"
        self.save_state(state)
        event = json.loads(original)
        event.update({"event_id":"gd3-0002", "event_type":"CHECK_RECORDED", "decision":"Record unchanged initial snapshot.",
                      "previous_state":state_projection(state), "new_state":state_projection(state)})
        append_event(self.project, event)
        updated = path.read_bytes()
        self.assertTrue(updated.startswith(original))
        with self.assertRaises(ValueError):
            append_event(self.project, event)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    unittest.main()
