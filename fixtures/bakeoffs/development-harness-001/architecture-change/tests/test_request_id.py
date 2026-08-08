import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from service import get_status
from transport import build_headers


class RequestIdTests(unittest.TestCase):
    def test_legacy_call_remains_compatible(self):
        self.assertEqual(get_status(), {"path": "/status", "headers": {"accept": "application/json"}})

    def test_identifier_crosses_both_components(self):
        self.assertEqual(get_status("req-7")["headers"]["x-request-id"], "req-7")
        self.assertEqual(build_headers("req-7")["x-request-id"], "req-7")
