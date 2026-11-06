"""Synthetic prospective-method contracts; no operational sales or authority."""
import copy
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from abvx_harness import book_radar_learning as learning


class MethodTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.history = self.root / 'learning'
        self.clock = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.mock = patch.object(learning, 'now', side_effect=lambda: self.clock.isoformat())
        self.mock.start()
        self.addCleanup(self.mock.stop)
        self.protocol = {'action': 'REGISTER_PROTOCOL', 'id': 'test',
            'cohort': {'market': 'amazon', 'geography': 'US', 'language': 'en', 'format': 'paperback'},
            'profiles': [{'id': 'DEFECT/v1', 'birth': 'Buyer defect', 'stop': 'Substitutes'},
                         {'id': 'MOTIVE/v1', 'birth': 'Reading pleasure', 'stop': 'No reader'}],
            'qualifier': 'Same external commercial gate',
            'budget': {'arm_seconds': 1200, 'review_seconds': 600, 'cards_per_arm': 2},
            'context': {'blinding': 'NON_BLIND_PROSPECTIVE_PILOT', 'portfolio_seeds': False},
            'method_forecast': {mid: {'hypothesis': 'Synthetic question', 'commercial_effect': 'UNKNOWN',
                'range': 'UNKNOWN', 'confidence': 'NOT_CALIBRATED'} for mid in ('DEFECT/v1', 'MOTIVE/v1')}, 'evidence': []}
        self.send(self.protocol)

    def send(self, data):
        return learning.method_event(self.history, data, self.root)

    def tick(self, seconds=1):
        self.clock += timedelta(seconds=seconds)

    def start(self, method='DEFECT/v1'):
        self.tick()
        return self.send({'action': 'START_ARM', 'id': 'test', 'method_id': method})

    def hypothesis(self, identity='h1', method='DEFECT/v1', niche='n1'):
        self.tick()
        return {'action': 'FREEZE_HYPOTHESIS', 'id': 'test', 'hypothesis_id': identity,
            'niche_id': niche, 'method_id': method, 'buyer': 'Synthetic reader',
            'unmet_need_or_motive': 'Enjoy a particular story form', 'alternatives': ['Existing books'],
            'supply_gap_cause': 'UNKNOWN', 'encounter_route': 'Amazon query',
            'product': 'Paperback story collection', 'birth_assessment': 'INSUFFICIENT_EVIDENCE',
            'preliminary_demand': 'INSUFFICIENT_EVIDENCE',
            'forecast': {'metric': 'paid_units', 'basis': 'PAID_PROCESSED', 'horizon_days': 30,
                         'range': 'UNKNOWN', 'anchor': 'PUBLICATION_DATE', 'rationale': 'No calibrated basis'},
            'confidence': 'LOW', 'evidence': [], 'negative_evidence': [],
            'next_falsification': 'Test actual buyer choice', 'cost_estimate': 'UNKNOWN'}

    def test_hypotheses_freeze_before_review_and_keep_unknown_forecasts(self):
        self.start()
        h = self.hypothesis()
        record = self.send(h)
        self.assertEqual(record, self.send(h))
        changed = copy.deepcopy(h); changed['forecast']['range'] = [10, 20]
        with self.assertRaises(ValueError): self.send(changed)
        self.tick(1190)
        self.send({'action': 'CLOSE_ARM', 'id': 'test', 'method_id': 'DEFECT/v1',
                   'trace': ['Synthetic unsuccessful search'], 'limitations': ['Synthetic'], 'evidence': []})
        with self.assertRaises(ValueError): self.send(self.hypothesis('late'))
        report = learning.method_comparison(self.history)
        self.assertEqual(report['winner'], 'NOT_ADJUDICATED')
        row = report['methods'][0]
        self.assertEqual(row['hypotheses'], 1)
        self.assertEqual(row['forecast_results']['NOT_FORECASTABLE'], 1)
        self.assertEqual(row['commercial_result'], 'UNPROVEN')
        self.assertEqual(row['return_per_hour'], 'UNKNOWN')

    def close(self, method='DEFECT/v1'):
        self.tick()
        return self.send({'action': 'CLOSE_ARM', 'id': 'test', 'method_id': method,
                          'trace': ['SYNTHETIC search'], 'limitations': [], 'evidence': []})

    def proof_ref(self, name='proof.txt'):
        p = self.root / name
        p.write_text('SYNTHETIC test proof, not operational authority or market evidence')
        import hashlib
        return {'path': name, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}

    def review(self):
        self.send({'action': 'START_REVIEW', 'id': 'test'})
        self.tick()
        self.send({'action': 'CLOSE_REVIEW', 'id': 'test', 'findings': 'SYNTHETIC no winner',
                   'evidence': [self.proof_ref()]})

    def prepared(self):
        self.start()
        h = self.hypothesis(); h['forecast']['range'] = [2, 4]
        self.send(h); self.close(); self.start('MOTIVE/v1')
        self.send({'action': 'LINK_DISCOVERY', 'id': 'test', 'hypothesis_id': 'h1',
                   'method_id': 'MOTIVE/v1', 'role': 'INDEPENDENT_REDISCOVERY', 'evidence': [self.proof_ref()]})
        self.close('MOTIVE/v1'); self.review()

    def trial(self, num=1):
        return {'action': 'REGISTER_TRIAL', 'id': 'test', 'trial_id': 't' + str(num),
            'hypothesis_id': 'h1', 'niche_id': 'n1', 'book_id': 'book:' + str(num),
            'product_family_id': 'product:' + str(num), 'planned_publication_at': '2026-01-02T00:00:00Z',
            'owner_approval': self.proof_ref('approval.txt'), 'identity_evidence': [self.proof_ref()],
            'trial_plan': {'total_loss_cap': 'SYNTHETIC', 'rights_quality': 'SYNTHETIC',
                           'route': 'SYNTHETIC', 'checkpoints': [0, 7, 14, 30, 60, 90]},
            'costs': dict.fromkeys(['production_minutes', 'maintenance_minutes', 'owner_minutes', 'rework_minutes', 'cash_cost'], 'UNKNOWN')}

    def test_shared_discovery_is_one_trial_and_fourth_product_rejected(self):
        self.prepared()
        t = self.trial()
        t.pop('owner_approval')
        with self.assertRaises(ValueError): self.send(t)
        for n in range(1, 4): self.send(self.trial(n))
        with self.assertRaises(ValueError): self.send(self.trial(4))
        t = self.trial(4); t['niche_id'] = 'alias-niche'
        with self.assertRaises(ValueError): self.send(t)
        report = learning.method_comparison(self.history)
        self.assertEqual(report['unique_trial_count'], 3)
        self.assertEqual(len(report['trials'][0]['joint_methods']), 2)
        self.assertEqual(report['winner'], 'NOT_ADJUDICATED')

    def test_versions_budget_order_and_corrupt_proof_fail_closed(self):
        protocol = copy.deepcopy(self.protocol); protocol['id'] = 'next'
        protocol['profiles'][0]['birth'] = 'Changed method'
        with self.assertRaises(ValueError): self.send(protocol)
        self.start()
        with self.assertRaises(ValueError): self.start('MOTIVE/v1')
        with self.assertRaises(ValueError): self.send({'action': 'START_REVIEW', 'id': 'test'})
        self.tick(1201)
        with self.assertRaises(ValueError): self.send(self.hypothesis())
        closed = self.close()
        self.assertEqual(closed['measurements']['budget_status'], 'OVERRUN')
        self.start('MOTIVE/v1')
        h = self.hypothesis(method='MOTIVE/v1'); h['evidence'] = [self.proof_ref()]
        self.send(h)
        sha = h['evidence'][0]['sha256']
        (self.history / 'proofs' / (sha + '.json')).write_text('{}')
        with self.assertRaises((ValueError, KeyError)): learning.method_comparison(self.history)

    def test_each_method_needs_its_own_preregistered_question_and_forecast(self):
        protocol = copy.deepcopy(self.protocol)
        protocol['id'] = 'missing-method-forecast'
        protocol['method_forecast'] = {'DEFECT/v1': {
            'hypothesis': 'Synthetic question', 'commercial_effect': 'UNKNOWN',
            'range': 'UNKNOWN', 'confidence': 'NOT_CALIBRATED'}}
        with self.assertRaises(ValueError):
            self.send(protocol)

    def test_method_registration_cannot_satisfy_t7_preregistration(self):
        with self.assertRaises(ValueError):
            learning.add_event(self.history, {'proposal_id': learning.PROPOSAL,
                'experiment_id': 'test', 'status': 'INSUFFICIENT_DATA',
                'measurements': {'synthetic': True}, 'evidence': [self.proof_ref()]}, self.root)

    def test_schema_rejects_malformed_method_event_and_trial_format_reset(self):
        self.prepared(); self.send(self.trial())
        t = self.trial(2); t['product_family_id'] = 'product:1'
        with self.assertRaises(ValueError): self.send(t)
        h = next(e for e in learning.records(self.history, 'events') if e['data']['action'] == 'FREEZE_HYPOTHESIS')
        h.pop('recorded_at'); h.pop('record_digest'); h.pop('schema_version')
        del h['data']['forecast']
        with self.assertRaises(Exception): learning.write(self.history, 'events', 'malformed', h)

    def test_real_outcome_contract_deduplicates_and_matches_exact_forecast(self):
        from test_book_radar_outcomes import fixture, refresh
        self.prepared(); self.send(self.trial())
        book, actual, _ = fixture(self.root)
        ref = self.proof_ref()
        book.update(id='book:1', product_id='product:1', publication_date='2026-01-02',
                    formats=[{'id': 'print:1', 'format': 'paperback', 'asin': 'SYNTHETIC1', 'evidence': [ref]}])
        book['date_evidence'] = [ref]
        actual.update(id='actual:1', book_id='book:1', product_id='product:1', observed_date='2026-02-01',
                      book_age_days=30, marketplace_scope='AMAZON_COM')
        for window in actual['windows'].values():
            window.update(start='2026-01-02', end='2026-02-01')
        for key in ('lifetime', 'recent'):
            actual['windows'][key].update(start='2026-01-02', end='2026-02-01', paid_units=3,
                processed_units=3, print_paid=3, ebook_paid=0, free_units=0)
        refresh(actual)
        binding = {'action': 'BIND_OUTCOME', 'id': 'test', 'trial_id': 't1', 'actual_id': 'actual:1',
                   'actual': actual, 'book': book, 'organic_attribution': 'UNKNOWN'}
        self.clock = datetime(2026, 2, 2, tzinfo=timezone.utc)
        mismatched = copy.deepcopy(binding)
        mismatched['book']['product_id'] = 'another-product'
        with self.assertRaises(ValueError):
            self.send(mismatched)
        self.send(binding); self.send(binding)
        report = learning.method_comparison(self.history)
        self.assertEqual(report['unique_trial_count'], 1)
        self.assertEqual(len(report['trials'][0]['results']), 1)
        result = report['trials'][0]['results'][0]
        self.assertEqual(result['forecast_status'], 'SUPPORTED')
        self.assertEqual(result['organic_attribution'], 'UNKNOWN')
        self.assertEqual(result['funnel_diagnosis']['classification'], 'UNKNOWN')
        self.assertEqual(report['winner'], 'NOT_ADJUDICATED')
        # Another account-wide cumulative snapshot is retained but never comparable.
        binding['actual_id'] = actual['id'] = 'actual:2'
        actual['marketplace_scope'] = 'KDP_ACCOUNT_ALL_MARKETPLACES'
        self.send(binding)
        results = learning.method_comparison(self.history)['trials'][0]['results']
        self.assertIn('INCOMPARABLE', [r['forecast_status'] for r in results])
