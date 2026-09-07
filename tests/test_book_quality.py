import unittest

from abvx_harness.book_quality import assess_visual_reference_quality


class BookQualityGateTests(unittest.TestCase):
    def test_technical_pass_does_not_override_product_failure(self):
        result = assess_visual_reference_quality({
            "scores": {"information_density": 1, "perceived_value": 2,
                       "editorial_enrichment": 1, "target_reader_advantage": 2,
                       "page_purpose": 1, "learning_value": 2},
            "pages": [{"page": 8, "usable_area_fill": .18, "isolated_groupable_entry": True}],
        })
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["density_signal"]["flagged_pages"], [8])

    def test_intentional_sparse_page_is_excluded(self):
        result = assess_visual_reference_quality({
            "scores": {key: 4 for key in ("information_density", "perceived_value",
                       "editorial_enrichment", "target_reader_advantage", "page_purpose", "learning_value")},
            "pages": [{"page": 1, "usable_area_fill": .12, "intentional_sparse": True}],
        })
        self.assertEqual(result["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
