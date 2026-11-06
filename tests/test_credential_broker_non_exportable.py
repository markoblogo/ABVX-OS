import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "credential-broker"))
import abvx_credential_broker as cb
from macos_secitem import SecItemStore
from tests.fixtures.fake_credential_keychain import FakeKeychain


@unittest.skipUnless(sys.platform == "darwin", "macOS Security.framework proof")
class NonExportableTests(unittest.TestCase):
    @unittest.skipUnless(os.environ.get("ABVX_RUN_KEYCHAIN_TESTS") == "1", "explicit native Keychain test opt-in required")
    def test_03_default_keychain_synthetic_secitem_lifecycle(self):
        store = SecItemStore("ABVX Credential Broker Synthetic Login Probe " + uuid.uuid4().hex)
        account = "openai.synthetic"
        canary = "synthetic-default-" + uuid.uuid4().hex
        try:
            store.add_synthetic(account, canary)
            self.assertTrue(store.exists(account))
            store.update_synthetic(account, canary + "-updated")
            restarted = SecItemStore(store.service)
            self.assertEqual(restarted._read_for_provider(account), canary + "-updated")
        finally:
            store.delete_synthetic(account)
        self.assertFalse(store.exists(account))

    @unittest.skipUnless(os.environ.get("ABVX_RUN_KEYCHAIN_TESTS") == "1", "explicit native Keychain test opt-in required")
    def test_01_synthetic_secitem_provider_restart_redaction_and_canary(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "synthetic.keychain-db"
            password = "synthetic-only-password"
            made = subprocess.run(["/usr/bin/security", "create-keychain", "-p", password, str(path)], capture_output=True)
            if made.returncode: self.skipTest("isolated synthetic Keychain unavailable")
            os.chmod(path, 0o600)
            canary = "synthetic-canary-" + uuid.uuid4().hex
            output = io.StringIO()
            errors = io.StringIO()
            try:
                unlocked = subprocess.run(["/usr/bin/security", "unlock-keychain", "-p", password, str(path)], capture_output=True)
                self.assertEqual(unlocked.returncode, 0)
                store = cb.Keychain(test_keychain=str(path)).store
                store.add_synthetic("openai.synthetic", canary)
                store.update_synthetic("openai.synthetic", canary + "-updated")
                canary += "-updated"

                class SyntheticAdapter:
                    def __init__(self, item): self.item = item
                    def _read_for_provider(self, account):
                        if account != "openai.primary": raise RuntimeError("wrong operation scope")
                        return self.item._read_for_provider("openai.synthetic")

                seen = []
                def mock_provider(payload, secret):
                    seen.append(secret == canary and payload["model"] == cb.MODEL)
                    return {"output_text": "synthetic operation succeeded", "usage": {"input_tokens": 2, "input_tokens_details": {"cached_tokens": 0}, "output_tokens": 3}}

                home = root / "broker"
                broker = cb.Broker(home, SyntheticAdapter(store), mock_provider)
                request = broker.request({"project": cb.PROJECT, "purpose": "translation-qa", "input": "synthetic", "budget_usd": 1}, {"os_uid": os.getuid()})
                cap = broker.approve(request["request_id"], True)["capability_id"]
                with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                    result = broker.execute(cap, {"purpose": "translation-qa", "input": "synthetic"})
                    self.assertEqual(result["output_text"], "synthetic operation succeeded")
                    restarted = cb.Broker(home, SyntheticAdapter(cb.Keychain(test_keychain=str(path)).store), mock_provider)
                    restarted.execute(cap, {"purpose": "translation-qa", "input": "synthetic after restart"})
                    restarted.provider = lambda payload, secret: (_ for _ in ()).throw(RuntimeError("provider error " + secret))
                    with self.assertRaises(RuntimeError) as err:
                        restarted.execute(cap, {"purpose": "translation-qa", "input": "synthetic error"})
                    self.assertNotIn(canary, str(err.exception))
                self.assertEqual(seen, [True, True])
                files = [p for p in home.rglob("*") if p.is_file()]
                reports = list((ROOT / "docs/audits/abvx-credential-broker-non-exportable-v1").glob("*.md"))
                exposed = output.getvalue().encode() + errors.getvalue().encode()
                for file in files + reports:
                    exposed += file.read_bytes()
                self.assertEqual(exposed.count(canary.encode()), 0)
                store.delete_synthetic("openai.synthetic")
                self.assertFalse(store.exists("openai.synthetic"))
            finally:
                subprocess.run(["/usr/bin/security", "delete-keychain", str(path)], capture_output=True)

    def test_02_separate_same_uid_attacker_has_no_raw_interface(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td) / "broker"
            fake = FakeKeychain()
            pending = cb.Broker(home, fake, lambda payload, secret: (_ for _ in ()).throw(AssertionError("provider must not be reached")))
            req = pending.request({"project": cb.PROJECT, "purpose": "translation-qa", "input": "synthetic", "budget_usd": 1}, {"os_uid": os.getuid()})
            cap = pending.approve(req["request_id"], True)["capability_id"]
            command = [sys.executable, str(ROOT / "scripts/credential-broker/abvx_credential_broker.py"), "--home", str(home), "serve"]
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env={"PATH": os.environ.get("PATH", ""), "HOME": td})
            try:
                for _ in range(100):
                    if (home / "broker.sock").exists():
                        try:
                            cb.client(home, {"action": "unsupported"})
                            break
                        except (ConnectionRefusedError, FileNotFoundError): pass
                    if process.poll() is not None: self.fail("synthetic daemon exited")
                    time.sleep(0.03)
                attacker = subprocess.run([sys.executable, str(ROOT / "tests/fixtures/credential_broker_attacker.py"), str(home), cap], capture_output=True, text=True, timeout=15)
                self.assertEqual(attacker.returncode, 0, attacker.stderr[:200])
                outcome = json.loads(attacker.stdout)
                self.assertEqual(outcome["same_uid"], os.getuid())
                self.assertTrue(outcome["direct_socket_pending"])
                self.assertTrue(outcome["state_readable"])
                self.assertTrue(outcome["state_mutable"])
                for key in ("raw_get", "unsupported", "context_reuse", "path_traversal", "arbitrary_url", "arbitrary_header", "environment_dump", "shell_command", "tampered_capability_execute"):
                    self.assertFalse(outcome[key], key)
                bridge = subprocess.run([sys.executable, str(ROOT / "scripts/credential-broker/macos_secitem.py"), "get", "openai.synthetic"], capture_output=True, text=True)
                self.assertEqual(bridge.stdout + bridge.stderr, "")
                self.assertFalse((ROOT / "scripts/credential-broker/keychain_helper.swift").exists())
            finally:
                process.terminate()
                process.communicate(timeout=5)
