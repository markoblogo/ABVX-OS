import unittest
import json
from pathlib import Path

from abvx_harness.harness import validate_repository


ROOT = Path(__file__).resolve().parents[1]


class BookFactoryTests(unittest.TestCase):
    def test_repository_validation_covers_book_contracts(self):
        checked = validate_repository(ROOT)
        self.assertIn("books/projects/fragments-therapists-notebook.json", checked)
        self.assertIn("books/projects/unusual-indices-book.json", checked)
        self.assertIn("books/projects/your-saas-bill-is-ridiculous.json", checked)
        self.assertIn("books/source-packs/unusual-indices-book-source-pack.json", checked)
        self.assertIn("books/source-packs/your-saas-bill-is-ridiculous-source-pack.json", checked)
        self.assertIn("books/specs/unusual-indices-book-spec.seed.json", checked)
        self.assertIn("books/specs/unusual-indices-book-spec.proposed.json", checked)
        self.assertIn("books/specs/your-saas-bill-is-ridiculous-spec.json", checked)
        self.assertIn("books/artifacts/unusual-indices-book/final-008/amazon/amazon-publication-package.json", checked)

    def test_commercial_nonfiction_profile_encodes_final_acceptance_rules(self):
        profile = json.loads((ROOT / "books/design/profiles/commercial-nonfiction-5x8-bw.json").read_text())
        self.assertEqual(profile["status"], "ADMITTED")
        self.assertEqual(profile["admission"]["acceptance_project"], "unusual-indices-book")
        self.assertTrue(profile["admission"]["human_gate_required"])
        self.assertIn("PRINT_TOC_REQUIRES_PAGE_NUMBERS", profile["production_rules"])
        self.assertIn("KINDLE_TOC_HAS_NO_PRINT_PAGINATION", profile["production_rules"])
        self.assertIn("PRE_CHAPTER_PAGE_BALANCE_REQUIRED", profile["production_rules"])
        self.assertIn("FULL_BOOK_CONTACT_SHEET_REQUIRED_BEFORE_PROFILE_ADMISSION", profile["production_rules"])
        self.assertIn("TECHNICAL_QA_DOES_NOT_EQUAL_VISUAL_QA", profile["production_rules"])
        self.assertIn("KNOWN_PROFILE_FAST_PATH", profile["production_rules"])

    def test_acceptance_case_closes_production_not_publication(self):
        evidence = json.loads((ROOT / "evidence/book-factory/commercial-nonfiction-5x8-bw-acceptance-001.evidence.json").read_text())
        project = json.loads((ROOT / "books/projects/unusual-indices-book.json").read_text())
        self.assertEqual(evidence["result"], "PASS")
        self.assertFalse(evidence["environment"]["external_publication_performed"])
        self.assertEqual(evidence["metrics"]["paperback_page_count"], 80)
        self.assertEqual(project["status"], "WAITING_FOR_HUMAN")
        self.assertIn("BOOK_FACTORY_ACCEPTANCE_CASE_COMPLETE", json.loads((ROOT / "books/specs/unusual-indices-book-spec.proposed.json").read_text())["current_state"])

    def test_final_unusual_indices_qa_is_release_candidate_ready(self):
        qa = json.loads((ROOT / "books/research/unusual-indices/final-production-008-qa.json").read_text())
        self.assertEqual(qa["state"], "PAPERBACK_INTERIOR_RC_READY")
        self.assertEqual(qa["interior_visual_count"], 0)
        self.assertFalse(qa["page_balance"]["blank_pages"])
        self.assertFalse(qa["page_balance"]["suspicious_pre_chapter_pages"])
        self.assertTrue(all(result == "PASS" for result in qa["qa_matrix"].values()))


if __name__ == "__main__":
    unittest.main()
