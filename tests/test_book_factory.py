import unittest
import json
import zipfile
import tempfile
from pathlib import Path

from abvx_harness.harness import validate_repository
from abvx_harness.book_preflight import audit_epub_toc, audit_page_geometry, audit_print_toc, audit_svg, find_collisions, high_risk_pages
from abvx_harness.publishing_gates import release_authorization


ROOT = Path(__file__).resolve().parents[1]


class BookFactoryTests(unittest.TestCase):
    def test_kdp_safe_area_rejects_text_and_objects_inside_mediabox_but_outside_live_area(self):
        for name in ("text-outside-safe-area.json", "object-outside-safe-area.json"):
            fixture = json.loads((ROOT / "books/factory/fixtures/preflight" / name).read_text())
            result = audit_page_geometry(fixture["pages"], fixture["page_count"], fixture["bleed"])
            self.assertEqual(result["status"], fixture["expected"])

    def test_visual_collision_and_duplicate_svg_label_fail(self):
        fixture = json.loads((ROOT / "books/factory/fixtures/preflight/overlapping-text.json").read_text())
        self.assertTrue(find_collisions(fixture["boxes"]))
        result = audit_svg(ROOT / "books/factory/fixtures/preflight/corrupt-label.svg", ["MAP"])
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["duplicated"], ["MAP"])

    def test_missing_print_and_kindle_contents_fail_closed(self):
        self.assertEqual(audit_print_toc("Title\nChapter 1\n")["status"], "FAIL")
        with tempfile.TemporaryDirectory() as directory:
            epub = Path(directory) / "missing-toc.epub"
            with zipfile.ZipFile(epub, "w") as archive:
                archive.writestr("OEBPS/content.opf", "<package/>")
            self.assertEqual(audit_epub_toc(epub)["status"], "FAIL")

    def test_kindle_navigation_and_reader_contents_pass_together(self):
        with tempfile.TemporaryDirectory() as directory:
            epub = Path(directory) / "book.epub"
            opf = '<package><manifest><item id="nav" href="nav.xhtml"/></manifest><spine><itemref idref="nav"/></spine></package>'
            nav = '<html><body><nav><a href="chapter.xhtml">Chapter</a></nav></body></html>'
            with zipfile.ZipFile(epub, "w") as archive:
                archive.writestr("OEBPS/content.opf", opf)
                archive.writestr("OEBPS/nav.xhtml", nav)
                archive.writestr("OEBPS/chapter.xhtml", "<html/>")
            self.assertEqual(audit_epub_toc(epub)["status"], "PASS")

    def test_high_risk_selection_includes_dense_and_structural_pages(self):
        records = [{"page": 1, "kind": "front_matter"}, {"page": 4, "kind": "toc"},
                   {"page": 9, "kind": "first_chapter"}, {"page": 50, "text_density": 99},
                   {"page": 70, "visual_density": 99}, {"page": 181, "kind": "crosswalk"},
                   {"page": 208, "kind": "last_page", "near_boundary": True}]
        self.assertEqual(high_risk_pages(records), [1, 4, 9, 50, 70, 181, 208])

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

    def test_all_book_production_requires_format_specific_contents(self):
        policy = (ROOT / "docs/book-production-policy.md").read_text()
        playbook = json.loads((ROOT / "playbooks/book-factory.known-profile-commercial-nonfiction.json").read_text())
        standard = playbook["validation"]["checks"]["STANDARD"]
        self.assertIn("Every reader-facing book", policy)
        self.assertIn("visible print TOC", " ".join(standard))
        self.assertIn("interactive EPUB TOC", " ".join(standard))
        self.assertIn("reading order", policy)

    def test_technical_validity_alone_never_means_kdp_ready(self):
        result = release_authorization({"technical": "PASS", "toc_navigation": "PASS"})
        self.assertEqual(result["status"], "PRODUCTION_BLOCKED")
        self.assertIn("product_quality", {item["gate"] for item in result["failures"]})

    def test_final_unusual_indices_qa_is_release_candidate_ready(self):
        qa = json.loads((ROOT / "books/research/unusual-indices/final-production-008-qa.json").read_text())
        self.assertEqual(qa["state"], "PAPERBACK_INTERIOR_RC_READY")
        self.assertEqual(qa["interior_visual_count"], 0)
        self.assertFalse(qa["page_balance"]["blank_pages"])
        self.assertFalse(qa["page_balance"]["suspicious_pre_chapter_pages"])
        self.assertTrue(all(result == "PASS" for result in qa["qa_matrix"].values()))


if __name__ == "__main__":
    unittest.main()
