import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from abvx_harness.harness import ValidationError
from abvx_harness.psychology_warehouse import _classify, _match_usage, _norm, _read_blocks, ingest, query


BOOK = {"id": "fragments-therapists-notebook", "title": "Fragments from a Therapist's Notebook", "canonical_manuscript": {"locator": None}}


def source_text(*notes):
    return "\n***\n".join(notes) + "\n***\n"


class PsychologyWarehouseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source = self.root / "Phy-notes.txt"
        book = self.root / "books/projects/fragments-therapists-notebook.json"
        book.parent.mkdir(parents=True)
        book.write_text(json.dumps(BOOK), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def ingest(self, text, full=False):
        self.source.write_text(text, encoding="utf-8")
        return ingest(self.root, self.source, full=full)

    def note_ids(self):
        data = json.loads((self.root / "psychology-warehouse/state/warehouse.json").read_text())
        return [n["note_id"] for n in data["notes"] if n["current"]]

    def test_unchanged_rerun_is_idempotent_and_preserves_taxonomy(self):
        text = source_text("Травма и отношения. Человек учится устанавливать границы.")
        self.ingest(text)
        note_id = self.note_ids()[0]
        taxonomy = (self.root / "psychology-warehouse/taxonomy/taxonomy-v1.json").read_bytes()
        report = self.ingest(text)
        self.assertEqual(report["delta"]["new"], 0)
        self.assertEqual(report["delta"]["unchanged"], 1)
        self.assertEqual(self.note_ids(), [note_id])
        self.assertEqual((self.root / "psychology-warehouse/taxonomy/taxonomy-v1.json").read_bytes(), taxonomy)

    def test_append_and_exact_duplicate_keep_prior_id_and_duplicate_relationship(self):
        text = "Первое наблюдение про травму, отношения и границы"
        self.ingest(source_text(text))
        first = self.note_ids()[0]
        report = self.ingest(source_text(text, "Новое наблюдение о страхе и терапии", text))
        self.assertEqual(report["delta"]["new"], 2)
        self.assertEqual(self.note_ids()[0], first)
        data = json.loads((self.root / "psychology-warehouse/state/warehouse.json").read_text())
        self.assertTrue(any(n["duplicate_of"] == first for n in data["notes"] if n["current"]))

    def test_edit_preserves_id_and_archives_verbatim_prior_version(self):
        self.ingest(source_text("Наблюдение о травме и способах адаптации в отношениях"))
        old_id = self.note_ids()[0]
        report = self.ingest(source_text("Наблюдение о травме и способах адаптации в новых отношениях"))
        self.assertEqual(report["delta"]["changed"], 1)
        self.assertEqual(self.note_ids(), [old_id])
        data = json.loads((self.root / "psychology-warehouse/state/warehouse.json").read_text())
        note = next(n for n in data["notes"] if n["current"])
        self.assertEqual(note["versions"][0]["original_text"], "Наблюдение о травме и способах адаптации в отношениях\n")

    def test_reordering_does_not_renumber_records(self):
        self.ingest(source_text("Травма и адаптация как отдельное наблюдение", "Терапия и отношения как отдельное наблюдение"))
        ids_before = set(self.note_ids())
        self.ingest(source_text("Терапия и отношения как отдельное наблюдение", "Травма и адаптация как отдельное наблюдение"))
        self.assertEqual(set(self.note_ids()), ids_before)

    def test_classification_is_multilabel_and_provenance_is_conservative(self):
        value = _classify("Травма в отношениях может влиять на адаптацию. Я думаю об этом после практики с клиентом.")
        labels = {x["label"] for x in value["topics"]}
        self.assertTrue({"TRAUMA", "RELATIONSHIPS", "ADAPTATION_AND_COPING"} <= labels)
        self.assertEqual(value["provenance"]["status"], "PERSONAL_OR_PRACTICE_NOTE")
        self.assertIn("CASE_LIKE_MATERIAL", value["privacy_flags"])

    def test_ambiguous_unknown_and_attributed_quote(self):
        self.assertEqual(_classify("Небольшая заметка.")["classification_review"], "UNCLASSIFIED")
        self.assertEqual(_classify("Страх")["classification_review"], "AMBIGUOUS")
        attributed = _classify("По словам Иванова, это наблюдение помогает понять травму.")
        self.assertEqual(attributed["provenance"]["status"], "ATTRIBUTED_SOURCE")
        quote = _classify("По словам Иванова, это наблюдение помогает понять травму. «Важно беречь границы человека».")
        self.assertEqual(quote["provenance"]["status"], "LIKELY_QUOTE_OR_EXCERPT")
        self.assertTrue(quote["provenance"]["attribution_if_explicit"])

    def test_near_duplicate_detection_keeps_both_assets_and_marks_review(self):
        a = "Травма может влиять на близкие отношения и способность человека доверять другим людям в жизни"
        b = "Травма может влиять на близкие отношения и способность человека доверять другим людям в жизни сегодня"
        report = self.ingest(source_text(a, b))
        self.assertEqual(report["delta"]["new"], 2)
        state = json.loads((self.root / "psychology-warehouse/state/warehouse.json").read_text())
        self.assertTrue(any(r["type"] == "NEAR_DUPLICATE" for n in state["notes"] for r in n["relationships"]))

    def test_exact_usage_match_and_review_matcher(self):
        notes = [{"note_id": "PHY-test", "normalized_text_for_matching": _norm("A note about trauma and healing.")}]
        exact = _match_usage(notes, ["A note about trauma and healing."], "book")
        self.assertEqual(exact[0]["relation"], "EXACT_MATCH")
        review = _match_usage(notes, ["A note about trauma, healing and a few added words."], "book")
        self.assertTrue(review and review[0]["relation"] in {"REVIEW", "POSSIBLE_RELATION"})

    def test_usage_is_many_to_many_and_unused_is_qualified(self):
        self.ingest(source_text("Травма и отношения. Человек может адаптироваться."))
        usage_path = self.root / "psychology-warehouse/usage/ledger.json"
        ledger = json.loads(usage_path.read_text())
        note_id = self.note_ids()[0]
        ledger["usages"].extend([
            {"note_id": note_id, "project_id": "example-book", "relation": "TRANSFORMATIVE_SEED"},
            {"note_id": note_id, "project_id": "second-book", "relation": "EXPANDED_FROM"},
        ])
        usage_path.write_text(json.dumps(ledger), encoding="utf-8")
        self.ingest(source_text("Травма и отношения. Человек может адаптироваться."))
        self.assertEqual(query(self.root, "used", "example-book")["count"], 1)
        self.assertIn("not never-published", query(self.root, "unused")["usage_semantics"])
        self.assertEqual(len(json.loads(usage_path.read_text())["usages"]), 2)
        self.assertEqual(query(self.root, "used", "second-book")["count"], 1)

    def test_missing_fragments_source_blocks_usage_claim(self):
        self.ingest(source_text("Травма и отношения. Человек может адаптироваться."))
        result = query(self.root, "used", "fragments")
        self.assertEqual(result["result"], "BLOCKED")
        self.assertIsNone(result["count"])

    def test_source_change_during_ingest_fails_without_writing_state(self):
        self.source.write_text(source_text("Травма и отношения"), encoding="utf-8")
        original_reader = _read_blocks

        def mutate_after_read(data):
            parsed = original_reader(data)
            self.source.write_text(source_text("Изменённый источник"), encoding="utf-8")
            return parsed

        with patch("abvx_harness.psychology_warehouse._read_blocks", side_effect=mutate_after_read):
            with self.assertRaisesRegex(ValidationError, "SOURCE_CHANGED_DURING_INGEST"):
                ingest(self.root, self.source)
        self.assertFalse((self.root / "psychology-warehouse/state/warehouse.json").exists())


if __name__ == "__main__":
    unittest.main()
