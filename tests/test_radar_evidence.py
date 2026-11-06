import json
import unittest
from pathlib import Path

from abvx_harness.harness import ValidationError, validate
from abvx_harness.radar_evidence import (
    bibliographic_translation_outcome,
    is_organic_discovery,
    resolve_local_raw_pointer,
    validate_evidence_record,
)

ROOT = Path(__file__).resolve().parents[1]


class RadarEvidenceTests(unittest.TestCase):
    def test_collection_failure_is_not_no_result(self):
        searches = [
            {"status": "NO_RESULT", "complete_work_found": False},
            {"status": "COLLECTION_FAILED", "complete_work_found": False},
        ]
        self.assertEqual(bibliographic_translation_outcome(searches), "UNCERTAIN")

    def test_successful_catalogue_searches_can_record_none_found_without_claiming_never_translated(self):
        searches = [
            {"status": "NO_RESULT", "complete_work_found": False, "exhaustive": True},
            {"status": "SUCCESS", "complete_work_found": False, "exhaustive": True},
        ]
        self.assertEqual(bibliographic_translation_outcome(searches), "NO_COMPLETE_TRANSLATION_FOUND")

    def test_positive_complete_translation_record_wins(self):
        self.assertEqual(
            bibliographic_translation_outcome([{"status": "SUCCESS", "complete_work_found": True}]),
            "COMPLETE_TRANSLATION_EXISTS",
        )

    def test_only_unpersonalized_organic_observations_count_as_discovery(self):
        base = {"status": "SUCCESS", "placement_type": "ORGANIC", "organic_position": 1, "personalized_state": "FALSE"}
        self.assertTrue(is_organic_discovery(base))
        self.assertFalse(is_organic_discovery({**base, "personalized_state": "UNKNOWN"}))
        self.assertFalse(is_organic_discovery({**base, "personalized_state": "TRUE"}))
        self.assertFalse(is_organic_discovery({**base, "placement_type": "SPONSORED"}))
        self.assertFalse(is_organic_discovery({**base, "status": "BLOCKED"}))
        self.assertFalse(is_organic_discovery({**base, "personalized_modules": ["PREVIOUSLY_VIEWED_MODULE"]}))
        self.assertFalse(is_organic_discovery({**base, "organic_position": None}))

    def test_amazon_contract_captures_context_and_separates_sponsored_modules(self):
        schema = json.loads((ROOT / "schemas/amazon_observation.schema.json").read_text())
        observation = {
            "schema_version": "amazon-observation/v1", "evidence_id": "AMZ-1",
            "observed_at": "2026-09-26T00:00:00Z", "marketplace": "Amazon.fr", "query": "roman ukrainien",
            "asin": "B000000001", "placement_type": "ORGANIC", "organic_position": 2,
            "organic_depth": 20, "sponsored_position": None, "personalized_modules": [],
            "personalized_state": "FALSE", "signed_in_state": "FALSE", "delivery_location_context": "France",
            "price": {"amount": 6.8, "currency": "EUR"}, "bsr": {"rank": 1234, "category": "Kindle"},
            "rating": 4.5, "review_count": 3, "availability": "Available", "format_linkage": [],
            "collection_method": "MANUAL_WEB", "status": "SUCCESS", "error_class": None,
            "raw_evidence_pointer": "raw.json#/records/AMZ-1", "tool_version": None,
            "collector_version": "manual-v1", "notes": [],
        }
        validate(observation, schema, schema_path=ROOT / "schemas/amazon_observation.schema.json", root=ROOT)
        self.assertTrue(is_organic_discovery(observation))
        observation["placement_type"] = "SPONSORED"
        observation["sponsored_position"] = 1
        self.assertFalse(is_organic_discovery(observation))

    def test_failure_status_cannot_carry_a_successful_normalized_value(self):
        schema = json.loads((ROOT / "schemas/radar_evidence.schema.json").read_text())
        record = {
            "schema_version": "radar-evidence/v1", "evidence_id": "E-FAIL",
            "observed_at": "2026-09-26T00:00:00Z", "source_type": "CATALOG",
            "source_name": "test", "collection_method": "MANUAL_WEB",
            "marketplace_or_catalog": "test", "query": "q",
            "entity": {"entity_type": "WORK", "label": "w", "identifiers": []},
            "raw_evidence_pointer": "raw.json#/records/E-FAIL",
            "normalized_value": {"collection_result": "NO_RESULT"},
            "evidence_class": "BIBLIOGRAPHIC_RECORD", "confidence": "LOW",
            "personalized_state": "UNKNOWN", "location_context": None,
            "tool_version": None, "collector_version": "radar-evidence/v1",
            "status": "COLLECTION_FAILED", "error_class": "NETWORK",
            "notes": [],
        }
        with self.assertRaises(ValidationError):
            validate_evidence_record(record, schema)

    @unittest.skipUnless(__import__("os").environ.get("ABVX_RUN_PRIVATE_SOURCE_TESTS") == "1", "private retained-history acceptance; explicit opt-in required")
    def test_five_seed_acceptance_fixture_validates_and_retains_raw_pointers(self):
        path = ROOT / "book-radar/acceptance/ukrainian-modernism-infra-v1/acceptance-v1.json"
        payload = json.loads(path.read_text())
        schema = json.loads((ROOT / "schemas/ukrainian_modernism_radar_acceptance.schema.json").read_text())
        validate(payload, schema, schema_path=ROOT / "schemas/ukrainian_modernism_radar_acceptance.schema.json", root=ROOT)
        self.assertEqual(len(payload["seeds"]), 5)
        for filename, schema_name in (("rights-evidence-v1.json", "rights_evidence.schema.json"), ("translation-existence-v1.json", "translation_existence.schema.json")):
            batch = json.loads((path.parent / filename).read_text())
            contract_schema = json.loads((ROOT / "schemas" / schema_name).read_text())
            self.assertEqual(len(batch["records"]), 5)
            for record in batch["records"]:
                validate(record, contract_schema, schema_path=ROOT / "schemas" / schema_name, root=ROOT)
        evidence_by_id = {item["evidence_id"]: item for item in payload["evidence"]}
        for seed in payload["seeds"]:
            with self.subTest(seed=seed["seed_id"]):
                self.assertTrue(seed["evidence_ids"])
            for evidence_id in seed["evidence_ids"]:
                evidence = evidence_by_id[evidence_id]
                self.assertTrue(evidence["raw_evidence_pointer"])
                raw = resolve_local_raw_pointer(ROOT, evidence["raw_evidence_pointer"])
                self.assertTrue(raw["uri"].startswith("https://"))
                self.assertTrue(raw["observation"])
                self.assertIn(evidence["status"], {"SUCCESS", "NO_RESULT", "COLLECTION_FAILED", "BLOCKED", "CAPTCHA", "UNSUPPORTED_MARKETPLACE", "AUTH_REQUIRED", "RATE_LIMITED", "UNKNOWN_FAILURE"})
                self.assertIn(evidence_id, {item["evidence_id"] for item in payload["evidence"]})
            self.assertEqual(seed["rights_evidence"]["decision"], "REVIEW")
            self.assertEqual(seed["translation_evidence"]["outcome"], "UNCERTAIN")
            self.assertEqual(seed["status"], "UNRESOLVED")


if __name__ == "__main__":
    unittest.main()
