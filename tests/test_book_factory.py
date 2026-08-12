import unittest
from pathlib import Path

from abvx_harness.harness import validate_repository


ROOT = Path(__file__).resolve().parents[1]


class BookFactoryTests(unittest.TestCase):
    def test_repository_validation_covers_book_contracts(self):
        checked = validate_repository(ROOT)
        self.assertIn("books/projects/fragments-therapists-notebook.json", checked)
        self.assertIn("books/projects/unusual-indices-book.json", checked)
        self.assertIn("books/source-packs/unusual-indices-book-source-pack.json", checked)
        self.assertIn("books/specs/unusual-indices-book-spec.seed.json", checked)


if __name__ == "__main__":
    unittest.main()
