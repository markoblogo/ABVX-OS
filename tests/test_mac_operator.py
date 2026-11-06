import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from abvx_harness import mac_operator as m


class MacOperatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.state = patch.object(m, 'STATE', Path(self.temp.name))
        self.state.start()

    def tearDown(self):
        self.state.stop()
        self.temp.cleanup()

    def test_duplicate_effect_is_not_repeated(self):
        with patch.object(m, 'diagnose', return_value={'status': 'OK'}) as effect:
            m.execute('status', 'same')
            self.assertEqual(m.execute('status', 'same')['status'], 'DUPLICATE')
            effect.assert_called_once()

    def test_unknown_cannot_spawn(self):
        with patch.object(m, 'command') as cmd:
            self.assertEqual(m.execute('rm -rf /', 'bad')['status'], 'CLARIFY')
            cmd.assert_not_called()

    def test_weekly_cannot_fake_execution(self):
        self.assertEqual(m.execute('weekly', 'w')['status'], 'WAITING_FOR_CODEX')
        self.assertFalse(m.execute('weekly', 'w2')['research_started'])
        self.assertEqual(m.execute('weekly', 'w3')['status'], 'ALREADY_PENDING')

    def test_cleanup_never_deletes(self):
        self.assertFalse(m.cleanup()['deletion_authorized'])

    def test_plist_bounds(self):
        self.assertEqual(m.plist()['ThrottleInterval'], 60)
        self.assertEqual(m.plist()['StartInterval'], 300)
        self.assertNotIn('UserName', m.plist())

    def test_unconnected_transport(self):
        self.assertEqual(m.poll_telegram()['status'], 'NOT_CONNECTED')

    def test_insecure_secret_file_rejected(self):
        p = m.STATE / 'telegram.json'
        p.write_text('{}')
        p.chmod(0o644)
        self.assertEqual(m.poll_telegram()['status'], 'BLOCKED_CONFIG_PERMISSIONS_OR_SCHEMA')

    def test_disk_history_does_not_mix_external_and_internal(self):
        m.save(m.STATE / 'sample-000.json', {'load': [0, 0, 0], 'disk_free': 123})
        with patch.object(m, 'command', return_value={'code': 0, 'output': ''}), patch.object(m, 'services', return_value={}):
            result = m.diagnose()
        self.assertIsNone(result['disk_delta'])
        self.assertIn(result['disk_path'], ('/', '/System/Volumes/Data'))
        self.assertIn('repository_disk', result)

    def test_unavailable_evidence_is_partial(self):
        with patch.object(m, 'command', return_value={'code': 1, 'output': 'denied'}), patch.object(m, 'services', return_value={}):
            result = m.diagnose()
            self.assertIn(result['status'], ('PARTIAL', 'ATTENTION'))
            self.assertIn('pressure', result['unavailable_probes'])

if __name__ == '__main__':
    unittest.main()
