import unittest

from abvx_harness.book_quality import assess_visual_reference_quality
from abvx_harness.book_quality import DIMENSIONS


class BookQualityGateTests(unittest.TestCase):
    def test_technical_pass_does_not_override_product_failure(self):
        result = assess_visual_reference_quality({
            "scores": {key: 2 for key in DIMENSIONS},
            "pages": [{"page": 8, "usable_area_fill": .18, "text_amount":.1,"visual_amount":.2,"meaningful_information_units":1,"isolated_groupable_entry": True}],
        })
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["density_signal"]["flagged_pages"], [8])

    def test_intentional_sparse_page_is_excluded(self):
        result = assess_visual_reference_quality({
            "scores": {key: 4 for key in DIMENSIONS},
            "pages": [{"page": 1, "usable_area_fill": .12, "intentional_sparse": True}],
        })
        self.assertEqual(result["status"], "PASS")

    def test_density_warning_needs_justification_or_redesign(self):
        scores = {key: 4 for key in DIMENSIONS}
        sparse = {"page": 12, "usable_area_fill": .2, "text_amount": .1, "visual_amount": .2, "meaningful_information_units": 1}
        self.assertEqual(assess_visual_reference_quality({"scores": scores, "pages": [sparse]})["status"], "FAIL")
        sparse["density_exception_justification"] = "deliberate full-page recognition pause"
        self.assertEqual(assess_visual_reference_quality({"scores": scores, "pages": [sparse]})["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
