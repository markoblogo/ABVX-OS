from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import patch

from abvx_harness.local_model import answer_local_model


class LocalModelTests(unittest.TestCase):
    def test_preserves_explicit_only_read_only_receipt(self):
        class Response:
            def read(self):
                return json.dumps({"ok": True, "evidence": {"context_mode": "explicit_only", "live_proof": False}, "status": "ABSTAINED"}).encode()

            def __enter__(self): return self
            def __exit__(self, *_): return False

        with patch("abvx_harness.local_model.urlopen", return_value=Response()):
            result = answer_local_model(Path("."), Path("docs/examples/local-model-request.json"), url="http://127.0.0.1:8766/v1/answer")
        self.assertEqual(result["status"], "ABSTAINED")


if __name__ == "__main__":
    unittest.main()
