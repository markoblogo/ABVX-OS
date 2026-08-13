import unittest
from pathlib import Path

from abvx_harness.harness import validate_repository


ROOT = Path(__file__).resolve().parents[1]


class UnusualIndicesResearchTests(unittest.TestCase):
    def test_repository_validation_covers_unusual_indices_research_artifacts(self):
        checked = validate_repository(ROOT)
        self.assertIn("books/research/unusual-indices/source-document.json", checked)
        self.assertIn("books/research/unusual-indices/normalized-corpus.json", checked)
        self.assertIn("books/research/unusual-indices/commercial-opportunity-report.json", checked)


if __name__ == "__main__":
    unittest.main()
