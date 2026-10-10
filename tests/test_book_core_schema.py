from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from abvx_harness.book_core import validate_state
from abvx_harness.harness import ValidationError
from abvx_harness.schema_validation import (
    draft_2020_12_validator,
    load_draft_2020_12_validator,
    validate_draft_2020_12,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "ABVX_BOOK_CORE_STATE_SCHEMA_V1.json"
FIXTURES = ROOT / "tests" / "fixtures" / "book_core" / "schema_validation"


def valid_state():
    return json.loads((FIXTURES / "valid_state.json").read_text(encoding="utf-8"))


class BookCoreSchemaTests(unittest.TestCase):
    def test_state_schema_is_checked_and_valid_fixture_passes_draft_2020_12(self):
        validator = load_draft_2020_12_validator(SCHEMA)
        self.assertEqual(validator.META_SCHEMA["$id"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(validate_draft_2020_12(valid_state(), SCHEMA), [])

    def test_invalid_enum_is_rejected(self):
        value = valid_state()
        value["identity"]["rights_status"] = "MAYBE"
        self.assertTrue(validate_draft_2020_12(value, SCHEMA))

    def test_missing_required_field_is_rejected(self):
        value = valid_state()
        del value["identity"]
        self.assertTrue(validate_draft_2020_12(value, SCHEMA))

    def test_invalid_conditional_is_rejected(self):
        value = valid_state()
        value["cover"] = {"state": "ACCEPTED"}
        self.assertTrue(validate_draft_2020_12(value, SCHEMA))

    def test_bad_local_ref_fails_closed_at_resolution(self):
        schema = {"$schema": "https://json-schema.org/draft/2020-12/schema",
                  "$defs": {}, "type": "object", "properties": {"payload": {"$ref": "#/$defs/missing"}}}
        validator = draft_2020_12_validator(schema)
        with self.assertRaises(Exception):
            list(validator.iter_errors({"payload": {}}))

    def test_external_ref_cannot_fetch_at_runtime(self):
        schema = {"$schema": "https://json-schema.org/draft/2020-12/schema",
                  "$ref": "https://abvx.invalid/not-local.json"}
        with self.assertRaises(Exception):
            list(draft_2020_12_validator(schema).iter_errors({}))

    def test_schema_valid_semantic_invalid_state_still_fails_abvx(self):
        value = copy.deepcopy(valid_state())
        value["extensions"] = {"unknown.module": {"state": "PASS"}}
        self.assertEqual(validate_draft_2020_12(value, SCHEMA), [])
        with self.assertRaisesRegex(ValidationError, "unknown registered extension"):
            validate_state(value)


if __name__ == "__main__":
    unittest.main()
