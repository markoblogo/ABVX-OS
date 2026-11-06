from datetime import datetime
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from abvx_harness import mac_operator as m, mac_workflows as w, mac_alerts as a, mac_storage as storage


class OperationsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.state = self.root / 'state'
        self.state.mkdir()
        self.patch = patch.object(m, 'STATE', self.state)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.temp.cleanup()

    def snapshot(self, issues=None, unknown=None):
        return {'time': 1000, 'issues': issues or [], 'unavailable_probes': unknown or [], 'workflow_health': {}}

    def notifications(self):
        return list((self.state / 'notifications').glob('*.json'))

    def test_outage_and_stale_service_alert_once_until_fresh_online(self):
        sample = self.snapshot()
        rec = {'status': 'WAITING', 'current_internet': 'UNAVAILABLE', 'offline_seconds': 200}
        sample['services'] = {'network_recovery': {'service_status': 'RUNNING', 'bounded_recovery': rec}}
        for _ in range(3):
            a.reconcile(self.state, sample, m.load, m.save)
        self.assertEqual(len(self.notifications()), 1)
        rec.update(status='STALE', current_internet='UNKNOWN')
        a.reconcile(self.state, sample, m.load, m.save)
        self.assertEqual(len(self.notifications()), 2)
        rec.update(status='ONLINE', current_internet='ONLINE', offline_seconds=0)
        a.reconcile(self.state, sample, m.load, m.save)
        self.assertEqual(len(self.notifications()), 4)

    def test_network_pause_alert_deduplicates_and_needs_online_to_close(self):
        sample = self.snapshot()
        sample['services'] = {'network_recovery': {'bounded_recovery': {'status': 'PAUSED'}}}
        for _ in range(3):
            a.reconcile(self.state, sample, m.load, m.save)
        self.assertEqual(len(self.notifications()), 1)
        sample['services']['network_recovery']['bounded_recovery']['status'] = 'UNKNOWN'
        a.reconcile(self.state, sample, m.load, m.save)
        self.assertEqual(len(self.notifications()), 1)
        sample['services']['network_recovery']['bounded_recovery']['status'] = 'ONLINE'
        a.reconcile(self.state, sample, m.load, m.save)
        self.assertEqual(len(self.notifications()), 2)

    def test_manual_cannot_overwrite_scheduled(self):
        with patch.object(m, 'command', return_value={'code': 0, 'output': ''}), patch.object(m, 'services', return_value={}), patch.object(w, 'project', return_value={}):
            m.diagnose('scheduled')
            before = (self.state / 'latest.json').read_bytes()
            summary = (self.state / 'summary.txt').read_bytes()
            with patch.object(m, 'command', return_value={'code': 1, 'output': 'denied'}):
                result = m.diagnose()
            self.assertEqual((self.state / 'latest.json').read_bytes(), before)
            self.assertEqual((self.state / 'summary.txt').read_bytes(), summary)
            self.assertIsNotNone(result['last_complete_scheduled'])
            self.assertTrue((self.state / 'latest-manual.json').exists())

    def test_open_unchanged_recovery_and_reopen(self):
        for _ in range(4):
            a.reconcile(self.state, self.snapshot(['disk']), m.load, m.save)
        self.assertEqual(len(self.notifications()), 1)
        a.reconcile(self.state, self.snapshot(), m.load, m.save)
        self.assertEqual(len(self.notifications()), 2)
        a.reconcile(self.state, self.snapshot(['disk']), m.load, m.save)
        self.assertEqual(len(self.notifications()), 3)

    def test_probe_denial_cannot_claim_memory_recovery(self):
        a.reconcile(self.state, self.snapshot(['memory']), m.load, m.save)
        a.reconcile(self.state, self.snapshot(unknown=['pressure']), m.load, m.save)
        self.assertEqual(len(self.notifications()), 1)

    def test_repeated_failure_alert_once_at_threshold(self):
        for _ in range(6):
            a.reconcile(self.state, self.snapshot(unknown=['pressure']), m.load, m.save)
        self.assertEqual(len(self.notifications()), 1)

    def test_retry_cap_and_cooldown(self):
        a.reconcile(self.state, self.snapshot(['disk']), m.load, m.save)
        sent, local = [], []
        def remote(msg):
            if msg: sent.append(msg)
            return {'status': 'UNAVAILABLE'}
        for now in (1000, 1100, 4601, 8202, 12000):
            a.deliver(self.state, m.load, m.save, lambda msg: local.append(msg), remote, now)
        self.assertEqual(len(sent), 3)
        self.assertEqual(len(local), 1)
        self.assertEqual(m.load(self.notifications()[0])['status'], 'DELIVERY_FAILED')

    def test_symlink_cleanup_excluded(self):
        home = self.root / 'home'
        (home / 'Library').mkdir(parents=True)
        target = self.root / 'protected'
        target.mkdir()
        (home / 'Library/Caches').symlink_to(target, target_is_directory=True)
        result = storage.preview(home)
        self.assertTrue(all(c['status'] == 'EXCLUDED_SYMLINK' for c in result['candidates']))
        self.assertFalse(result['deletion_authorized'])

    def test_scan_budget_and_no_symlink_following(self):
        folder = self.root / 'cache'
        folder.mkdir()
        secret = self.root / 'secret'
        secret.write_bytes(b'x' * 100000)
        (folder / 'link').symlink_to(secret)
        self.assertLess(storage.measure(folder)['allocated_bytes'], 100000)
        self.assertFalse(storage.measure(folder, max_entries=1)['complete'])
        self.assertEqual(secret.stat().st_size, 100000)

    def test_active_without_new_evidence_is_overdue(self):
        now = datetime.fromisoformat('2026-10-20T12:00:00+02:00').timestamp()
        schedule = {'status': 'ACTIVE', 'rrule': 'FREQ=WEEKLY;BYDAY=MO;BYHOUR=8;BYMINUTE=0', 'last_run_at': (now - 3600) * 1000}
        with patch.object(w, 'scheduler', return_value=schedule):
            result = w.project(self.root, self.root, now)['radar']
        self.assertEqual(result['status'], 'OVERDUE_EVIDENCE')
        self.assertTrue(result['attempt_without_accepted_completion'])

    def test_custom_schedule_is_unknown(self):
        with patch.object(w, 'scheduler', return_value={'status': 'ACTIVE', 'rrule': 'FREQ=DAILY'}):
            self.assertEqual(w.project(self.root, self.root)['radar']['status'], 'UNKNOWN_OR_INACTIVE_SCHEDULE')

    def test_future_receipt_rejected(self):
        run = self.root / 'run'
        run.mkdir()
        m.save(run / 'execution.json', {'status': 'COMPLETE', 'captured_at': '2099-01-01T00:00:00Z'})
        self.assertIsNone(w.run_receipt(self.root, 'youtube', run, 1000)['completed_at'])

    def test_handoff_claim_once_no_historical_completion(self):
        result = w.enqueue(self.root, self.state, 'radar', 'r1', m.save)
        key = Path(result['handoff']).stem
        self.assertEqual(w.transition(self.root, self.state, key, 'claim', m.save)['status'], 'CLAIMED')
        self.assertEqual(w.transition(self.root, self.state, key, 'claim', m.save)['status'], 'ALREADY_CLAIMED_OR_TERMINAL')
        self.assertEqual(w.transition(self.root, self.state, key, 'complete', m.save, 'absent')['status'], 'BLOCKED_RESULT_EVIDENCE')
        with self.assertRaises(ValueError):
            w.transition(self.root, self.state, '../bad', 'claim', m.save)

    def test_bad_sender_stale_and_duplicate_updates(self):
        config = {'token': 'test:synthetic', 'user_id': 1, 'chat_id': 1}
        def msg(uid, date):
            return {'from': {'id': uid}, 'chat': {'id': 1, 'type': 'private'}, 'date': date, 'text': 'Как там Mac?'}
        updates = [{'update_id': 1, 'message': msg(2, 1000)}, {'update_id': 2, 'message': msg(1, 1)}, {'update_id': 3, 'message': msg(1, 1000)}]
        def api(d, method, payload):
            return updates if method == 'getUpdates' else True
        with patch.object(m, 'telegram_config', return_value=config), patch.object(m, 'telegram_api', side_effect=api), patch.object(m.time, 'time', return_value=1000), patch.object(m, 'execute', return_value={'status': 'DUPLICATE'}) as effect:
            m.poll_telegram()
            m.poll_telegram()
            effect.assert_called_once_with('status', 'telegram-3')

    def test_transport_error_does_not_expose_token(self):
        config = {'token': 'synthetic-secret', 'user_id': 1, 'chat_id': 1}
        with patch.object(m, 'telegram_config', return_value=config), patch.object(m, 'telegram_api', side_effect=OSError('synthetic-secret')):
            result = m.notify_remote('test')
        self.assertNotIn('synthetic-secret', json.dumps(result))


class EvidenceBindingTests(unittest.TestCase):
    setUp = OperationsTests.setUp
    tearDown = OperationsTests.tearDown

    def test_hash_bound_youtube_receipt_accepts_then_rejects_change(self):
        run = self.root / 'run'
        run.mkdir()
        acquisition, research = {'raw': 'synthetic'}, {'research': 'synthetic'}
        m.save(run / 'acquisition.json', acquisition)
        m.save(run / 'research.json', research)
        m.save(run / 'analysis.json', {'synthetic': True})
        (run / 'REPORT.md').write_text('synthetic report')
        m.save(run / 'execution.json', {'status': 'COMPLETE', 'captured_at': '2026-10-19T12:00:00Z',
               'acquisition_digest': w.digest(acquisition), 'research_digest': w.digest(research)})
        self.assertEqual(w.run_receipt(self.root, 'youtube', run, 2000000000)['status'], 'EVIDENCE_PRESENT')
        m.save(run / 'research.json', {'changed': True})
        self.assertEqual(w.run_receipt(self.root, 'youtube', run, 2000000000)['status'], 'INCOMPLETE_OR_BLOCKED')

    def test_cancel_allows_fresh_handoff_without_replay(self):
        result = w.enqueue(self.root, self.state, 'radar', 'r1', m.save)
        w.transition(self.root, self.state, Path(result['handoff']).stem, 'cancel', m.save)
        fresh = w.enqueue(self.root, self.state, 'radar', 'r2', m.save)
        self.assertEqual(fresh['status'], 'WAITING_FOR_CODEX')
        self.assertNotEqual(fresh['handoff'], result['handoff'])

if __name__ == '__main__':
    unittest.main()
