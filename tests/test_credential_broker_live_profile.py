import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "credential-broker"))
import abvx_credential_broker as cb
from tests.fixtures.fake_credential_keychain import FakeKeychain


class SmokeProfileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.keychain = FakeKeychain()
        self.keychain.put("openai.primary", "synthetic-only-smoke-fixture")
        self.calls = []
        def provider(payload, secret):
            self.calls.append((payload["model"], secret))
            return {"output_text": "OK", "usage": {"input_tokens": 2, "input_tokens_details": {"cached_tokens": 0}, "output_tokens": 1}}
        self.broker = cb.Broker(Path(self.temp.name), self.keychain, provider)

    def tearDown(self): self.temp.cleanup()

    def _request(self, **changes):
        value = {"project": cb.SMOKE_PROJECT, "purpose": cb.SMOKE_PURPOSE, "model": cb.MODEL,
                 "input": "Return exactly OK.", "max_output_tokens": 64, "budget_usd": 0.01}
        value.update(changes)
        return self.broker.request(value, {"os_uid": os.getuid()})

    def test_smoke_capability_one_call_zero_retries_and_fifteen_minutes(self):
        request = self._request()
        cid = self.broker.approve(request["request_id"], True)["capability_id"]
        cap = cb.read_json(Path(self.temp.name) / "capabilities" / f"{cid}.json")
        self.assertEqual((cap["max_calls"], cap["max_retries"], cap["budget_usd"]), (1, 0, 0.01))
        lifetime = datetime.fromisoformat(cap["expires_at"]) - datetime.fromisoformat(cb.read_json(Path(self.temp.name) / "requests" / f"{request['request_id']}.json")["created_at"])
        self.assertGreaterEqual(lifetime, timedelta(minutes=15))
        self.assertLess(lifetime, timedelta(minutes=15, seconds=1))
        result = self.broker.execute(cid, {"purpose": cb.SMOKE_PURPOSE, "input": "Return exactly OK.", "max_output_tokens": 64}, {"os_uid": os.getuid()})
        self.assertEqual(result["output_text"], "OK")
        with self.assertRaises(PermissionError):
            self.broker.execute(cid, {"purpose": cb.SMOKE_PURPOSE, "input": "again", "max_output_tokens": 64}, {"os_uid": os.getuid()})
        self.assertEqual(len(self.calls), 1)

    def test_smoke_scope_and_budget_cannot_widen(self):
        for changes in ({"budget_usd": 0.02}, {"max_output_tokens": 65}, {"purpose": "translation-qa"}, {"project": cb.PROJECT}):
            with self.assertRaises(ValueError): self._request(**changes)
        request = self._request()
        cid = self.broker.approve(request["request_id"], True)["capability_id"]
        path = Path(self.temp.name) / "capabilities" / f"{cid}.json"
        cap = cb.read_json(path)
        cap["max_retries"] = 1
        cb.write_json(path, cap)
        with self.assertRaises(PermissionError):
            self.broker.execute(cid, {"purpose": cb.SMOKE_PURPOSE, "input": "x", "max_output_tokens": 64}, {"os_uid": os.getuid()})
        self.assertFalse(self.calls)
