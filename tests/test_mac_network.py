import tempfile
import json
import unittest
from pathlib import Path
from abvx_harness import mac_network as n


class NetworkBridgeTests(unittest.TestCase):
    def test_fresh_receipt_requires_activated_adapter_and_expires(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            receipt = folder / 'state.json'
            receipt.write_text(json.dumps({'schema_version': 'v1', 'time': 1000,
                'status': 'PAUSED', 'internet': 'UNAVAILABLE', 'attempts': 3}))
            job = {'label': n.LABEL, 'evidence': {'code': 0, 'output': 'state = running\nabvx_harness.hotel_recovery'}}
            self.assertEqual(n.inspect([job], folder, receipt, 1100)['bounded_recovery']['status'], 'PAUSED')
            self.assertEqual(n.inspect([job], folder, receipt, 1300)['bounded_recovery']['status'], 'STALE')
            job['evidence']['output'] = 'state = running'
            self.assertEqual(n.inspect([job], folder, receipt, 1100)['bounded_recovery']['status'], 'NOT_ACTIVATED')

    def test_only_fixed_events_are_exported_and_old_online_is_not_current(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / 'hotspot.log').write_text('2026-10-21 17:00:00,123 internet_online\n2026-10-21 17:01:00,123 secret_token\n2026-10-21 17:02:00,123 reconnect_failed_ValueError\n')
            result = n.inspect([{'label': n.LABEL, 'evidence': {'code': 0, 'output': ' state = running\n'}}], folder)
            self.assertEqual(result['service_status'], 'RUNNING')
            self.assertEqual(result['current_internet'], 'UNKNOWN')
            self.assertEqual(len(result['recent_events']), 2)
            self.assertNotIn('secret_token', str(result))

    def test_missing_or_symlinked_log_is_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            self.assertEqual(n.inspect([], folder)['log_status'], 'UNAVAILABLE')
            (folder / 'target').write_text('private')
            (folder / 'hotspot.log').symlink_to(folder / 'target')
            self.assertEqual(n.inspect([], folder)['log_status'], 'UNAVAILABLE')
