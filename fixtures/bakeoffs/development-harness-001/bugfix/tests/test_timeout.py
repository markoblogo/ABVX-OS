import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from timeout import parse_timeout
from timeout_before import parse_timeout as parse_timeout_before


class TimeoutTests(unittest.TestCase):
    def test_fixture_reproduces_the_historical_regression(self):
        self.assertEqual(parse_timeout_before(0), 30)

    def test_zero_is_explicit(self):
        self.assertEqual(parse_timeout(0), 0)

    def test_missing_uses_default(self):
        self.assertEqual(parse_timeout(None, 12), 12)

    def test_negative_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_timeout(-1)
