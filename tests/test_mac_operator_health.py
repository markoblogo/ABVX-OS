import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from abvx_harness import mac_operator as m


class HealthTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.patcher = patch.object(m, 'STATE', Path(self.temp.name))
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def test_missing_stale_and_future_never_claim_health(self):
        for stamp, expected in ((None, 'UNKNOWN'), (1, 'STALE'), (2000, 'UNKNOWN')):
            m.save(m.STATE / 'latest-scheduled.json', {'time': stamp})
            self.assertEqual(m.health(1000)['sample_freshness'], expected)
            self.assertEqual(m.health(1000)['status'], 'ATTENTION')

    def test_health_is_read_only_and_does_not_probe(self):
        m.save(m.STATE / 'latest-scheduled.json', {'time': 900, 'status': 'ATTENTION'})
        before = (m.STATE / 'latest-scheduled.json').read_bytes()
        with patch.object(m, 'command') as probe:
            result = m.health(1000)
            probe.assert_not_called()
        self.assertEqual(result['status'], 'OK')
        self.assertEqual(result['host_status'], 'ATTENTION')
        self.assertEqual((m.STATE / 'latest-scheduled.json').read_bytes(), before)

    def test_failure_phase_is_redacted_and_propagates(self):
        with patch.object(m, 'diagnose', side_effect=ValueError('secret-token')):
            with self.assertRaises(ValueError):
                m.tick('scheduled')
        receipt = m.load(m.STATE / 'tick-scheduled.json')
        self.assertEqual(receipt['status'], 'FAILED')
        self.assertEqual(receipt['phase'], 'diagnose')
        self.assertNotIn('secret-token', str(receipt))

    def test_manual_tick_never_replaces_scheduled_receipt(self):
        m.save(m.STATE / 'tick-scheduled.json', {'status': 'FAILED'})
        with patch.object(m, 'diagnose', return_value={}), patch.object(m, 'poll_telegram', return_value={'status': 'NOT_CONNECTED'}):
            self.assertEqual(m.tick('manual')['status'], 'COMPLETE')
        self.assertEqual(m.load(m.STATE / 'tick-scheduled.json')['status'], 'FAILED')

    def test_running_tick_gets_grace_but_unfinished_tick_is_visible(self):
        m.save(m.STATE / 'latest-scheduled.json', {'time': 950})
        m.save(m.STATE / 'tick-scheduled.json', {'status': 'RUNNING', 'started_at': 900})
        self.assertEqual(m.health(1000)['status'], 'OK')
        self.assertEqual(m.health(1250)['status'], 'ATTENTION')
