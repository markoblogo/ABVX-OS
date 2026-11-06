import json
import os
import socket
import subprocess
import time
import sys
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "credential-broker"))
import abvx_credential_broker as cb
from tests.fixtures.fake_credential_keychain import FakeKeychain

FAKE = "sk-test-never-a-real-secret-0123456789"


class MutableClock:
    def __init__(self): self.now = datetime(2026, 9, 29, tzinfo=timezone.utc)
    def __call__(self): return self.now


class BrokerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / "broker"
        self.keychain = FakeKeychain()
        self.keychain.put("openai.primary", FAKE)
        self.calls = []
        self.clock = MutableClock()
        self.provider = self.success
        self.broker = cb.Broker(self.home, self.keychain, self.invoke, self.clock)
        self.cap = self.new_cap()

    def tearDown(self): self.tmp.cleanup()

    def invoke(self, payload, secret): return self.provider(payload, secret)

    def success(self, payload, secret):
        self.calls.append((payload, secret))
        return {"output_text": "safe result", "usage": {"input_tokens": 10, "input_tokens_details": {"cached_tokens": 2}, "output_tokens": 20}}

    def new_cap(self, budget=1.0, purpose="translation-qa", max_tokens=1024):
        r = self.broker.request({"project": cb.PROJECT, "purpose": purpose, "input": "do not persist this private prompt", "max_output_tokens": max_tokens, "budget_usd": budget}, {"os_uid": os.getuid(), "executable": "test"})
        return self.broker.approve(r["request_id"], True)["capability_id"]

    def run_call(self, cap=None, input_text="hello", max_tokens=10, purpose="translation-qa"):
        return self.broker.execute(cap or self.cap, {"purpose": purpose, "input": input_text, "max_output_tokens": max_tokens})

    def test_01_allowed_request_returns_sanitized_result_and_usage(self):
        result = self.run_call()
        self.assertEqual(result["output_text"], "safe result")
        self.assertEqual(result["usage"]["input_tokens"], 10)
        self.assertEqual(self.calls[0][1], FAKE)
        self.assertNotIn(FAKE, json.dumps(result))

    def test_02_unapproved_model_denied(self):
        with self.assertRaises(ValueError): self.broker.request({"project": cb.PROJECT, "purpose": "translation-qa", "input": "x", "model": "not-allowed"}, {})

    def test_03_expired_capability_denied(self):
        self.clock.now += timedelta(hours=5)
        with self.assertRaises(PermissionError): self.run_call()

    def test_04_revoked_capability_denied(self):
        self.broker.revoke(self.cap)
        with self.assertRaises(PermissionError): self.run_call()

    def test_05_budget_warning_is_audited(self):
        small = self.new_cap(budget=0.00006)
        self.provider = lambda p, k: {"output_text": "safe", "usage": {"input_tokens": 100, "input_tokens_details": {"cached_tokens": 0}, "output_tokens": 70}}
        self.run_call(small, max_tokens=1)
        events = (self.home / "audit.jsonl").read_text()
        self.assertIn('"event":"budget_warning"', events)

    def test_06_budget_exhaustion_stops_next_call(self):
        small = self.new_cap(budget=0.000001)
        with self.assertRaises(PermissionError): self.run_call(small)
        self.assertFalse(self.calls)

    def test_07_retry_attempts_count_and_charge(self):
        n = {"count": 0}
        def flaky(payload, secret):
            n["count"] += 1
            if n["count"] == 1: raise TimeoutError("temporary")
            return self.success(payload, secret)
        self.provider = flaky
        result = self.run_call()
        cap = cb.read_json(self.home / "capabilities" / f"{self.cap}.json")
        self.assertEqual(cap["calls"], 2)
        self.assertGreaterEqual(cap["spent_usd"], result["estimated_cost_usd"])

    def test_08_malformed_request_denied(self):
        with self.assertRaises(ValueError): self.broker.request({"project": cb.PROJECT, "purpose": "translation-qa"}, {})

    def test_09_arbitrary_url_denied(self):
        with self.assertRaises(ValueError): self.broker.execute(self.cap, {"purpose": "translation-qa", "input": "x", "url": "https://example.invalid"})

    def test_10_arbitrary_authorization_header_denied(self):
        with self.assertRaises(ValueError): self.broker.execute(self.cap, {"purpose": "translation-qa", "input": "x", "headers": {"Authorization": "Bearer x"}})

    def test_11_raw_secret_retrieval_has_no_cli_command(self):
        p = subprocess.run([sys.executable, str(ROOT / "scripts/credential-broker/abvx_credential_broker.py"), "--home", str(self.home), "secrets", "get", "openai.primary"], capture_output=True, text=True)
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn(FAKE, p.stdout + p.stderr)

    def test_12_provider_error_exact_secret_is_redacted(self):
        self.provider = lambda p, k: (_ for _ in ()).throw(RuntimeError("bad response " + k))
        with self.assertRaises(RuntimeError) as err: self.run_call()
        self.assertNotIn(FAKE, str(err.exception))

    def test_13_audit_redaction_and_no_prompt_persistence(self):
        self.provider = lambda p, k: {"output_text": "Bearer " + k, "usage": {}}
        result = self.run_call()
        audit = (self.home / "audit.jsonl").read_text()
        persisted = "".join(p.read_text() for p in self.home.rglob("*.json")) + audit + json.dumps(result)
        self.assertNotIn(FAKE, persisted)
        self.assertNotIn("do not persist this private prompt", persisted)
        self.assertIn("[REDACTED]", result["output_text"])

    def test_14_broker_restart_preserves_capability_state(self):
        restarted = cb.Broker(self.home, self.keychain, self.invoke, self.clock)
        result = restarted.execute(self.cap, {"purpose": "translation-qa", "input": "hello", "max_output_tokens": 10})
        self.assertEqual(result["output_text"], "safe result")

    def test_15_concurrent_calls_cannot_overreserve_run_budget(self):
        small = self.new_cap(budget=0.00006)
        barrier = threading.Barrier(8)
        outcomes = []
        def worker():
            barrier.wait()
            try: self.run_call(small, max_tokens=1); outcomes.append("ok")
            except PermissionError: outcomes.append("denied")
        ts = [threading.Thread(target=worker) for _ in range(8)]
        for t in ts: t.start()
        for t in ts: t.join()
        self.assertEqual(outcomes.count("ok"), 1)
        self.assertEqual(outcomes.count("denied"), 7)

    def test_19_path_shaped_identifiers_denied_before_file_access(self):
        for bad in ("../requests/anything", "/tmp/anything", "a" * 32 + "/../x", ""):
            with self.assertRaises(ValueError): self.broker.approve(bad, True)
            with self.assertRaises(ValueError): self.broker.revoke(bad)
            with self.assertRaises(ValueError): self.broker.execute(bad, {"purpose": "translation-qa", "input": "x"})

    def test_20_capability_scope_tampering_denied(self):
        path = self.home / "capabilities" / f"{self.cap}.json"
        for change in ({"project": "other"}, {"operation": "secrets.get"}, {"model": "not-allowed"}, {"budget_usd": 100}, {"max_calls": 100000}):
            cap = cb.read_json(path)
            original = cap.copy()
            cap.update(change)
            cb.write_json(path, cap)
            with self.assertRaises(PermissionError): self.run_call()
            cb.write_json(path, original)
        self.assertFalse(self.calls)

    def test_21_uid_binding_and_replay_expiry(self):
        with self.assertRaises(PermissionError):
            self.broker.execute(self.cap, {"purpose": "translation-qa", "input": "x"}, {"os_uid": os.getuid() + 1})
        self.clock.now += timedelta(hours=5)
        with self.assertRaises(PermissionError): self.run_call()
        self.assertFalse(self.calls)


@unittest.skipUnless(sys.platform == "darwin", "macOS Keychain integration test")
class KeychainTests(unittest.TestCase):
    def test_16_fake_keychain_crud_and_restart(self):
        keychain = FakeKeychain()
        keychain.put("openai.primary", FAKE)
        self.assertTrue(keychain.exists("openai.primary"))
        restarted = FakeKeychain()
        restarted.items = keychain.items
        self.assertEqual(restarted.get("openai.primary"), FAKE)
        keychain.update("openai.primary", "synthetic-updated-value")
        self.assertEqual(keychain.get("openai.primary"), "synthetic-updated-value")
        keychain.delete("openai.primary")
        self.assertFalse(keychain.exists("openai.primary"))

    def test_17_local_unix_socket_permissions_identity_and_daemon_restart(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td) / "broker-home"
            command = [sys.executable, str(ROOT / "scripts/credential-broker/abvx_credential_broker.py"), "--home", str(home), "serve"]
            clean_env = {"PATH": os.environ.get("PATH", ""), "HOME": td}
            def stop(proc):
                proc.terminate()
                proc.communicate(timeout=3)
            def start():
                proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=clean_env)
                for _ in range(100):
                    if (home / "broker.sock").exists():
                        try:
                            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as probe:
                                probe.settimeout(0.1)
                                probe.connect(str(home / "broker.sock"))
                            return proc
                        except (ConnectionRefusedError, FileNotFoundError, TimeoutError):
                            pass
                    if proc.poll() is not None: self.fail("broker daemon exited before socket appeared")
                    time.sleep(0.03)
                stop(proc); self.fail("broker socket did not start")
            proc = start()
            try:
                self.assertEqual((home / "broker.sock").stat().st_mode & 0o777, 0o600)
                first = cb.client(home, {"action": "request", "project": cb.PROJECT, "purpose": "translation-qa", "input": "synthetic socket payload"})
                self.assertTrue(first["ok"])
                saved = cb.read_json(next((home / "requests").glob("*.json")))
                self.assertEqual(saved["identity"]["os_uid"], os.getuid())
                spoof = cb.client(home, {"action": "request", "project": cb.PROJECT, "purpose": "translation-qa", "input": "x", "agent": "trusted-owner"})
                self.assertFalse(spoof["ok"])
                direct_secret = cb.client(home, {"action": "get", "credential_id": "openai.primary"})
                self.assertFalse(direct_secret["ok"])
            finally:
                stop(proc)
            proc = start()
            try:
                second = cb.client(home, {"action": "request", "project": cb.PROJECT, "purpose": "translation-qa", "input": "second synthetic payload"})
                self.assertTrue(second["ok"])
            finally:
                stop(proc)

    @unittest.skipUnless(sys.platform == "darwin" and os.environ.get("ABVX_RUN_KEYCHAIN_TESTS") == "1", "explicit macOS Keychain test opt-in required")
    def test_18_isolated_macos_keychain_crud_permissions_and_restart(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td) / "broker-home"
            path = str(Path(td) / "fake-only.keychain-db")
            password = "fake-keychain-password-only"
            account = "openai.synthetic"
            fake = "synthetic-only-canary-6f8a9c"
            made = subprocess.run(["/usr/bin/security", "create-keychain", "-p", password, path], capture_output=True)
            if made.returncode: self.skipTest("OS refused isolated synthetic Keychain creation")
            os.chmod(path, 0o600)
            try:
                unlocked = subprocess.run(["/usr/bin/security", "unlock-keychain", "-p", password, path], capture_output=True)
                self.assertEqual(unlocked.returncode, 0)
                kc = cb.Keychain(home=home, test_keychain=path)
                kc.store.add_synthetic(account, fake)
                self.assertTrue(kc.exists(account))
                self.assertEqual(kc._read_for_provider(account), fake)
                self.assertEqual(Path(path).stat().st_mode & 0o777, 0o600)
                restarted = cb.Keychain(home=home, test_keychain=path)
                self.assertEqual(restarted._read_for_provider(account), fake)
                kc.store.update_synthetic(account, "synthetic-updated-value")
                self.assertEqual(kc._read_for_provider(account), "synthetic-updated-value")
                kc.store.delete_synthetic(account)
                self.assertFalse(kc.exists(account))
            finally:
                subprocess.run(["/usr/bin/security", "delete-keychain", path], capture_output=True)


if __name__ == "__main__": unittest.main()
