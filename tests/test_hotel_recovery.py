import unittest
from unittest.mock import Mock
from abvx_harness import hotel_recovery as h


class RecoveryTests(unittest.TestCase):
    def test_new_outage_does_not_inherit_success_cooldown(self):
        adapter = Mock()
        adapter.online.return_value = True
        state = h.step(adapter, {'attempts': 1, 'failed_probes': 2, 'last_attempt': 990}, lambda s: None, 1000)
        adapter.online.return_value = False
        adapter.reconnect.return_value = 'form_unavailable'
        state = h.step(adapter, state, lambda s: None, 1015)
        adapter.reconnect.assert_not_called()
        state = h.step(adapter, state, lambda s: None, 1030)
        adapter.reconnect.assert_called_once()

    def test_retry_backoff_and_history_survive_recovery(self):
        adapter = Mock()
        adapter.online.return_value = False
        adapter.reconnect.side_effect = ValueError('unapproved_redirect')
        state = {'attempts': 0, 'failed_probes': 1}
        for now in (1000, 1015, 1060, 1075, 1180):
            state = h.step(adapter, state, lambda s: None, now)
        self.assertEqual(adapter.reconnect.call_count, 3)
        self.assertEqual(state['status'], 'PAUSED')
        adapter.online.return_value = True
        state = h.step(adapter, state, lambda s: None, 1200)
        self.assertEqual(state['status'], 'ONLINE')
        self.assertIsNone(state['offline_since'])
        self.assertTrue(any(e.get('reason') == 'unapproved_redirect' for e in state['events']))

    def test_probe_exception_never_triggers_login_or_kills_supervisor(self):
        adapter = Mock()
        adapter.online.side_effect = RuntimeError('private-url')
        state = h.step(adapter, {'attempts': 0}, lambda s: None, 1000)
        self.assertEqual(state['status'], 'PROBE_ERROR')
        self.assertEqual(state['internet'], 'UNKNOWN')
        self.assertNotIn('private-url', str(state))
        adapter.reconnect.assert_not_called()

    def test_three_failures_pause_persist_and_restart_does_not_reset(self):
        adapter = Mock()
        adapter.online.return_value = False
        adapter.reconnect.side_effect = ValueError('unapproved_redirect')
        saved = []
        state = {'attempts': 0, 'failed_probes': 1}
        for now in (1000, 1100, 1300, 1600, 1900, 2200):
            state = h.step(adapter, state, lambda s: saved.append(dict(s)), now)
        self.assertEqual(adapter.reconnect.call_count, 3)
        self.assertEqual(state['status'], 'PAUSED')
        self.assertEqual(state['last_reason'], 'unapproved_redirect')
        self.assertEqual(saved[0]['status'], 'ATTEMPTING')
        h.step(adapter, dict(state), lambda s: None, 10000)
        self.assertEqual(adapter.reconnect.call_count, 3)

    def test_online_rearms_but_unverified_success_does_not(self):
        adapter = Mock()
        adapter.online.return_value = False
        adapter.reconnect.return_value = 'internet_restored'
        state = h.step(adapter, {'attempts': 2, 'failed_probes': 2}, lambda s: None, 1000)
        self.assertEqual(state['status'], 'PAUSED')
        adapter.online.return_value = True
        state = h.step(adapter, state, lambda s: None, 1100)
        self.assertEqual(state['status'], 'ONLINE')
        self.assertEqual(state['attempts'], 0)

    def test_other_network_does_not_spend_budget_or_retry_too_fast(self):
        adapter = Mock()
        adapter.online.return_value = False
        adapter.reconnect.return_value = 'outside_configured_hotel_network'
        state = h.step(adapter, {'attempts': 0, 'failed_probes': 2}, lambda s: None, 1000)
        self.assertEqual(state['attempts'], 0)
        h.step(adapter, state, lambda s: None, 1100)
        self.assertEqual(adapter.reconnect.call_count, 1)

    def test_raw_errors_are_not_retained(self):
        self.assertEqual(h.reason(ValueError('https://token:secret@example.test')), 'unexpected_error')
        self.assertEqual(h.reason(ValueError('additional_required_field')), 'additional_required_field')

    def test_interrupted_attempt_slot_stays_spent(self):
        adapter = Mock()
        adapter.online.return_value = False
        state = h.step(adapter, {'attempts': 3, 'failed_probes': 2, 'status': 'ATTEMPTING'}, lambda s: None, 1000)
        adapter.reconnect.assert_not_called()
        self.assertEqual(state['status'], 'PAUSED')
