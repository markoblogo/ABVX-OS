import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from labels import display_labels


class LabelTests(unittest.TestCase):
    def test_display_labels_reuses_normalization_contract(self):
        self.assertEqual(display_labels(["  Release Candidate ", "Needs Review"]), "release-candidate, needs-review")

    def test_empty_list_is_stable(self):
        self.assertEqual(display_labels([]), "")
