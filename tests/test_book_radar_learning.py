"""Synthetic learning fixtures; never new market observations or real outcomes."""
import copy
import hashlib
import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from abvx_harness import book_radar_markets as markets
from abvx_harness import book_radar_learning as learning


class LearningTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.history = self.root / 'learning'

    def test_method_protocol_is_frozen_and_does_not_validate_t7(self):
        protocol = {'action': 'REGISTER_PROTOCOL', 'id': 'synthetic-block',
            'cohort': {'market': 'amazon', 'geography': 'US', 'language': 'en', 'format': 'paperback'},
            'profiles': [{'id': 'DEFECT/v1', 'birth': 'Repeated buyer defect', 'stop': 'Adequate alternatives'},
                         {'id': 'MOTIVE/v1', 'birth': 'Reading pleasure', 'stop': 'No reader route'}],
            'qualifier': 'Same evidence gate; do not require a utilitarian job',
            'budget': {'arm_seconds': 1200, 'review_seconds': 600, 'cards_per_arm': 2},
            'context': {'blinding': 'NON_BLIND_PROSPECTIVE_PILOT', 'portfolio_seeds': False},
            'method_forecast': {mid: {'hypothesis': 'Synthetic question', 'commercial_effect': 'UNKNOWN',
                'range': 'UNKNOWN', 'confidence': 'NOT_CALIBRATED'} for mid in ('DEFECT/v1', 'MOTIVE/v1')},
            'evidence': []}
        first = learning.method_event(self.history, protocol, self.root)
        self.assertEqual(first, learning.method_event(self.history, protocol, self.root))
        protocol['qualifier'] = 'Changed after the fact'
        with self.assertRaises(ValueError):
            learning.method_event(self.history, protocol, self.root)
        report = learning.retrospective(self.history)
        self.assertEqual(report['validation']['status'], 'INSUFFICIENT_DATA')
        self.assertEqual(report['method_comparison']['winner'], 'NOT_ADJUDICATED')
        self.assertFalse(report['production_authorized'])

    def run_fixture(self, name, day='2026-10-11', price=15, students=100, currency='EUR', **changes):
        run = self.root / 'runs' / name
        run.mkdir(parents=True)
        packet = markets.template('udemy')
        candidate = packet['opportunities'][0]
        candidate.update(id='U04', topic='SYNTHETIC workflow', audience='Synthetic buyer', motivation='Synthetic job')
        candidate['geography'] = 'US'
        candidate['proposals']['udemy']['format'] = 'course'
        proof = {'facts': {'students_cumulative': students}, 'synthetic': True}
        (run / 'proof.json').write_text(json.dumps(proof))
        row = markets.observation_template('udemy', candidate, day)
        row.update(id='obs:' + name, availability='AVAILABLE', source_url='https://www.udemy.com/course/synthetic/',
                   upstream_url='https://www.udemy.com/course/synthetic/', storage_permission='RETAINED_AUTHORIZED',
                   evidence_path='proof.json', evidence_sha256=hashlib.sha256((run / 'proof.json').read_bytes()).hexdigest())
        row['metrics']['price'] = {'status': 'VERIFIED', 'value': price, 'unit': currency, 'note': 'SYNTHETIC'}
        row.update(changes)
        if row['availability'] != 'AVAILABLE':
            for signal in row['metrics'].values():
                signal.update(status='MISSING', value=None, unit=None)
        packet['observations'] = [row]
        (run / 'input.json').write_text(json.dumps(packet))
        (run / 'execution.json').write_text(json.dumps({'execution': 'COMPLETE'}))
        (run / 'ranking.json').write_text(json.dumps({'opportunities': [{'id': 'U04', 'commercial_potential_judgment': 'HIGH_CONDITIONAL'}]}))
        return run

    def test_history_is_immutable_and_replays_do_not_multiply_evidence(self):
        first = self.run_fixture('first')
        learning.learn_run(first, self.history)
        learning.learn_run(self.run_fixture('replay'), self.history)
        before = {str(p): p.read_bytes() for p in self.history.rglob('*') if p.is_file()}
        report = learning.learn_run(first, self.history)['report']
        self.assertEqual(report['research_progress']['unique_observations'], 1)
        self.assertEqual(report['research_progress']['duplicate_observations_excluded'], 1)
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.history.rglob('*') if p.is_file()})
        packet = json.loads((first / 'input.json').read_text())
        packet['opportunities'][0]['topic'] = 'Changed original prediction'
        (first / 'input.json').write_text(json.dumps(packet))
        with self.assertRaises(ValueError):
            learning.learn_run(first, self.history)

    def test_final_review_is_a_separate_stage_and_cannot_rewrite_acquisition(self):
        run = self.run_fixture('stages')
        ranking = (run / 'ranking.json').read_bytes()
        (run / 'ranking.json').unlink()
        learning.learn_run(run, self.history)
        (run / 'ranking.json').write_bytes(ranking)
        report = learning.learn_run(run, self.history)['report']
        self.assertEqual(len(list((self.history / 'snapshots').glob('*.json'))), 2)
        self.assertEqual(report['research_progress']['unique_observations'], 1)
        self.assertEqual(report['research_progress']['retained_runs'], 1)
        self.assertEqual(report['candidates'][0]['original_assessment']['commercial_potential_judgment'], 'HIGH_CONDITIONAL')

    def test_only_matching_direct_product_currency_and_windows_compare(self):
        learning.learn_run(self.run_fixture('one'), self.history)
        second = self.run_fixture('two', day='2026-10-12', price=12, students=110)
        report = learning.learn_run(second, self.history)['report']
        changes = report['research_progress']['typed_source_changes']
        self.assertEqual(next(x for x in changes if x['metric'] == 'price')['after'], 12)
        self.assertEqual(next(x for x in changes if x['metric'] == 'source:students_cumulative')['after'], 110)
        self.assertTrue(all('UNKNOWN' in x['interpretation'] for x in changes))
        for name, updates, currency in [('currency', {}, 'USD'), ('period', {'period_start': '2026-10-01', 'period_end': '2026-10-12'}, 'EUR'), ('shelf', {'source_url': 'https://www.udemy.com/courses/search/?q=synthetic'}, 'EUR')]:
            with self.subTest(name=name):
                other = self.root / name
                learning.learn_run(self.root / 'runs/one', other)
                result = learning.learn_run(self.run_fixture(name, day='2026-10-12', currency=currency, **updates), other)['report']
                self.assertFalse([x for x in result['research_progress']['typed_source_changes'] if x['metric'] == 'price'])

    def test_missing_paid_orders_never_become_success_from_students_or_price(self):
        report = learning.learn_run(self.run_fixture('proxies', students=100000), self.history)['report']
        self.assertEqual(report['candidates'][0]['status'], 'VALIDATE')
        self.assertFalse(report['production_authorized'])
        self.assertEqual(report['research_progress']['commercial_predictions_confirmed'], 'UNPROVEN')
        self.assertEqual(report['research_progress']['return_per_production_hour'], 'UNKNOWN')
        self.assertEqual(report['delayed_outcomes'], [])

    def test_changed_context_is_flagged_without_rewriting_forecast(self):
        learning.learn_run(self.run_fixture('old'), self.history)
        run = self.run_fixture('new', day='2026-10-12')
        data = json.loads((run / 'input.json').read_text())
        data['opportunities'][0]['audience'] = 'Another buyer'
        (run / 'input.json').write_text(json.dumps(data))
        report = learning.learn_run(run, self.history)['report']
        self.assertEqual(report['research_progress']['hypothesis_continuity'][0]['context'], 'CHANGED_REVIEW_REQUIRED')
        old = next(s for s in learning.records(self.history, 'snapshots') if s['run_id'] == 'old')
        self.assertEqual(old['opportunities'][0]['audience'], 'Synthetic buyer')

    def test_preserves_candidate_specific_validation_question(self):
        run = self.run_fixture('specific')
        question = 'Compare three direct workflow curricula for human-review failure recovery.'
        (run / 'ranking.json').write_text(json.dumps({'opportunities': [{'id': 'U04', 'next_commercial_validation': question}]}))
        report = learning.learn_run(run, self.history)['report']
        self.assertEqual(report['candidates'][0]['next_validation'], question)

    def test_corrupt_original_source_is_rejected(self):
        run = self.run_fixture('corrupt')
        (run / 'proof.json').write_text('Changed source')
        with self.assertRaises(ValueError):
            learning.learn_run(run, self.history)
        self.assertFalse((self.history / 'snapshots').exists())

    def test_unavailable_source_and_unknown_buyer_stay_on_hold(self):
        run = self.run_fixture('unavailable', availability='ACCESS_FAILED')
        report = learning.learn_run(run, self.history)['report']
        self.assertEqual(report['candidates'][0]['status'], 'HOLD')
        unknown = self.run_fixture('unknown-buyer')
        packet = json.loads((unknown / 'input.json').read_text())
        packet['opportunities'][0]['audience'] = 'UNKNOWN'
        (unknown / 'input.json').write_text(json.dumps(packet))
        result = learning.learn_run(unknown, self.root / 'unknown')['report']
        self.assertEqual(result['candidates'][0]['status'], 'HOLD')

    def test_unknown_geography_cannot_establish_price_movement(self):
        history = self.root / 'unknown-geo'
        for name, day, price in [('geo1', '2026-10-11', 15), ('geo2', '2026-10-12', 12)]:
            run = self.run_fixture(name, day=day, price=price, geography='UNKNOWN')
            report = learning.learn_run(run, history)['report']
        self.assertFalse([c for c in report['research_progress']['typed_source_changes'] if c['metric'] == 'price'])

    def test_validated_improvement_is_measured_and_never_executes_adoption(self):
        learning.learn_run(self.run_fixture('validation'), self.history)
        registered = {'proposal_id': learning.PROPOSAL, 'experiment_id': 't7',
                      'status': 'VALIDATION_REGISTERED', 'plan': {'target': 'T7 six products; four followups'}}
        learning.add_event(self.history, registered, self.root)
        source = self.root / 'synthetic-measurements.json'
        source.write_text('{"fixture": "SYNTHETIC, tests only"}')
        ref = {'path': source.name, 'sha256': hashlib.sha256(source.read_bytes()).hexdigest()}
        m = {'panel_size': 6, 'matched_followups': 4, 'questions_resolved': 1,
             'research_minutes': 20, 'proxy_to_paid_substitutions': 0, 'minimum_followup_days': 7}
        event = {'proposal_id': learning.PROPOSAL, 'experiment_id': 't7', 'status': 'VALIDATED',
                 'dataset_kind': 'REAL_HISTORY', 'measurements': m, 'evidence': [ref]}
        # This exercises guards with synthetic fixtures; no operational event is written.
        m['minimum_followup_days'] = 1
        with self.assertRaises(ValueError):
            learning.add_event(self.history, event, self.root)
        m['minimum_followup_days'] = 7
        learning.add_event(self.history, event, self.root)
        event['status'] = 'ADOPTED'
        with self.assertRaises(ValueError):
            learning.add_event(self.history, event, self.root)
        approval = self.root / 'synthetic-owner-review.txt'
        approval.write_text('SYNTHETIC approval fixture; no operational authority')
        event['owner_approval'] = {'path': approval.name, 'sha256': hashlib.sha256(approval.read_bytes()).hexdigest()}
        saved = learning.add_event(self.history, event, self.root)
        self.assertFalse(saved['automatic_action'])
        report = learning.retrospective(self.history)
        self.assertEqual(report['validation']['status'], 'ADOPTED')
        self.assertEqual(report['production_policy'], 'HOLD')

    def test_improvement_needs_preregistration_real_evidence_and_owner_review(self):
        learning.learn_run(self.run_fixture('events'), self.history)
        source = self.root / 'experiment.json'
        source.write_text('{"synthetic": true}')
        ref = {'path': source.name, 'sha256': hashlib.sha256(source.read_bytes()).hexdigest()}
        event = {'proposal_id': learning.PROPOSAL, 'experiment_id': 'coverage-test',
                 'status': 'VALIDATED', 'dataset_kind': 'REAL_HISTORY',
                 'measurements': {'matched_followups': 4}, 'evidence': [ref]}
        with self.assertRaises(ValueError):
            learning.add_event(self.history, event, self.root)
        registered = {'proposal_id': learning.PROPOSAL, 'experiment_id': 'coverage-test',
                      'status': 'VALIDATION_REGISTERED', 'plan': {'target': '4/6 comparable followups'}}
        learning.add_event(self.history, registered, self.root)
        event['dataset_kind'] = 'SYNTHETIC'
        with self.assertRaises(ValueError):
            learning.add_event(self.history, event, self.root)
        event['status'] = 'INSUFFICIENT_DATA'
        learning.add_event(self.history, event, self.root)
        learning.add_event(self.history, event, self.root)
        self.assertEqual(len(learning.records(self.history, 'events')), 2)
        event.update(status='ADOPTED', dataset_kind='REAL_HISTORY')
        with self.assertRaises(ValueError):
            learning.add_event(self.history, event, self.root)

    def test_delayed_actuals_require_explicit_identity_and_zero_is_not_failure(self):
        from test_book_radar_outcomes import fixture, refresh
        report = learning.learn_run(self.run_fixture('outcome'), self.history)['report']
        _, actual, _ = fixture(self.root)
        links = {'links': [{'hypothesis_key': report['candidates'][0]['hypothesis_key'],
                            'actual_id': actual['id'], 'book_id': actual['book_id']}]}
        link_path, actual_path = self.root / 'links.json', self.root / 'actuals.json'
        link_path.write_text(json.dumps(links))
        actual_path.write_text(json.dumps({'actuals': [actual]}))
        learning.bind_outcomes(self.history, link_path, actual_path, self.root)
        learning.bind_outcomes(self.history, link_path, actual_path, self.root)
        report = learning.retrospective(self.history)
        self.assertEqual(len(report['delayed_outcomes']), 1)
        own = report['delayed_outcomes'][0]
        self.assertEqual(own['funnel']['PURCHASED']['state'], 'OBSERVED_ZERO')
        self.assertEqual(own['funnel']['EXPOSED']['state'], 'UNKNOWN')
        self.assertEqual(own['commercial_success'], 'UNPROVEN')
        links['links'][0]['book_id'] = 'book:wrong'
        link_path.write_text(json.dumps(links))
        with self.assertRaises(ValueError):
            learning.bind_outcomes(self.history, link_path, actual_path, self.root)
        links['links'][0]['book_id'] = actual['book_id']
        link_path.write_text(json.dumps(links))
        actual['id'] = 'actual:delayed'
        actual['observed_date'] = '2026-12-06'
        actual['book_age_days'] = 90
        for key in ('lifetime', 'recent'):
            actual['windows'][key].update(end='2026-12-06', processed_units=1, paid_units=1, ebook_paid=1)
        refresh(actual)
        links['links'][0]['actual_id'] = actual['id']
        link_path.write_text(json.dumps(links))
        actual_path.write_text(json.dumps({'actuals': [actual]}))
        learning.bind_outcomes(self.history, link_path, actual_path, self.root)
        self.assertEqual(len(learning.retrospective(self.history)['delayed_outcomes']), 2)
        actual['id'] = 'actual:unknown'
        for key in ('lifetime', 'recent'):
            for metric in ('processed_units', 'paid_units', 'free_units', 'ebook_paid', 'print_paid'):
                actual['windows'][key][metric] = 'UNKNOWN'
        refresh(actual)
        links['links'][0]['actual_id'] = actual['id']
        link_path.write_text(json.dumps(links))
        actual_path.write_text(json.dumps({'actuals': [actual]}))
        learning.bind_outcomes(self.history, link_path, actual_path, self.root)
        own = next(o for o in learning.retrospective(self.history)['delayed_outcomes'] if o['binding']['actual_id'] == actual['id'])
        self.assertEqual(own['funnel']['PURCHASED']['state'], 'UNKNOWN')
        self.assertEqual(own['commercial_success'], 'UNPROVEN')

    def test_go_is_bound_to_paid_source_existing_gate_and_complete_review(self):
        run = self.run_fixture('go')
        packet = json.loads((run / 'input.json').read_text())
        row = packet['observations'][0]
        row.update(period_start='2026-10-01', period_end='2026-10-11')
        row['metrics']['paid_enrollments'] = {'status': 'VERIFIED', 'value': 3, 'unit': 'orders', 'note': 'Synthetic only'}
        (run / 'input.json').write_text(json.dumps(packet))
        review = {'research_digest': learning.digest(packet), 'candidates': {'U04': {'facets': {
            key: {'conclusion': 'SUPPORTED', 'proof_sha256': row['evidence_sha256'], 'reason': 'Synthetic reviewed assertion'} for key in learning.FACETS}}}}
        (run / 'commercial-review.json').write_text(json.dumps(review))
        with patch.object(markets, 'assess_market', return_value={'eligible': False}):
            result = learning.learn_run(run, self.history)
            self.assertEqual(result['report']['candidates'][0]['status'], 'VALIDATE')
        with patch.object(markets, 'assess_market', return_value={'eligible': True}):
            report = learning.learn_run(run, self.root / 'approved-review')['report']
            self.assertEqual(report['candidates'][0]['status'], 'GO')
            self.assertFalse(report['candidates'][0]['production_authorized'])

    def test_tampered_learning_snapshot_is_detected(self):
        learning.learn_run(self.run_fixture('tamper'), self.history)
        path = next((self.history / 'snapshots').glob('*.json'))
        value = json.loads(path.read_text())
        value['opportunities'][0]['audience'] = 'Silently rewritten'
        path.write_text(json.dumps(value))
        with self.assertRaises(ValueError):
            learning.retrospective(self.history)

    def test_existing_acquisition_entrypoint_runs_learning_and_keeps_four_market_receipt_gate(self):
        import argparse
        import importlib.util
        spec = importlib.util.spec_from_file_location('radar_entry', learning.REPO / 'scripts/run_multi_market_radar.py')
        entry = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(entry)
        source = self.run_fixture('acquisition')
        row = json.loads((source / 'input.json').read_text())['observations'][0]
        receipt = {'attempts': [{'marketplace': m, 'source_url': row['source_url'],
            'evidence_ref': 'proof.json', 'evidence_sha256': row['evidence_sha256'],
            'captured_at_utc': '2026-10-11T09:00:00Z', 'method': 'LIVE_BROWSER',
            'status': 'AVAILABLE' if m == 'udemy' else 'ACCESS_FAILED',
            'blocker': 'SYNTHETIC integration test, no network'} for m in markets.MARKETS]}
        receipt_path = source / 'acquisition.json'
        receipt_path.write_text(json.dumps(receipt))
        args = argparse.Namespace(input=source / 'input.json', acquisition=receipt_path,
            run_id='synthetic-execution', as_of='2026-10-11', hours=4, history=self.history, ranking=None)
        with patch.object(entry, 'REPO', self.root):
            result = entry.run(args)
            self.assertEqual(result['learning']['status'], 'COMPLETE')
            self.assertEqual(result['source_coverage'], 'PARTIAL')
            cached = copy.deepcopy(receipt)
            next(a for a in cached['attempts'] if a['marketplace'] == 'udemy')['method'] = 'CACHED'
            receipt_path.write_text(json.dumps(cached))
            args.run_id = 'cached-must-fail'
            with self.assertRaises(ValueError):
                entry.run(args)
            receipt['attempts'].pop()
            receipt_path.write_text(json.dumps(receipt))
            args.run_id = 'must-fail'
            with self.assertRaises(ValueError):
                entry.run(args)
