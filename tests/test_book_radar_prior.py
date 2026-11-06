import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from abvx_harness.book_radar_prior import (AXES, assess_pair, decision_context,
    internal_projection, paid_state, reference, review, verify_reference, validate)
from abvx_harness.harness import ValidationError
from abvx_harness.book_radar import empty_state, save_state
from abvx_harness.book_radar_outcomes import calibrate
from test_book_radar_outcomes import fixture as outcome_fixture, refresh


def axes(status='SAME'):
    ref={'path':'fixture.json','sha256':'a'*64,'selector':'fixture'}
    return {a:dict(status=status,reason='Explicit semantic regression fixture',
        internal_evidence=[] if status=='UNKNOWN' else [ref],
        external_evidence=[] if status=='UNKNOWN' else [ref]) for a in AXES}


def prior(comp, paid):
    return {'assessment':assess_pair(comp,{'paid_units':paid})}


class PriorSemanticsTests(unittest.TestCase):
    def test_zero_is_not_no_demand(self):
        p=assess_pair(axes(),{'paid_units':0})
        self.assertEqual(p['paid_state'],'ZERO_PAID')
        self.assertEqual(p['market_demand_verdict'],'UNKNOWN')
        self.assertFalse(p['automatic_kill'])

    def test_free_and_kenp_are_not_paid(self):
        self.assertEqual(paid_state({'paid_units':0,'free_units':100,'kenp':500,'royalties':25}),'ZERO_PAID')

    def test_unknown_is_not_zero(self):
        self.assertEqual(paid_state({'paid_units':'UNKNOWN','kenp':0}),'UNKNOWN_PAID')
        self.assertEqual(paid_state({}),'UNKNOWN_PAID')

    def test_topic_similarity_is_not_match(self):
        a=axes('UNKNOWN');a['topic_domain']=axes()['topic_domain']
        self.assertFalse(assess_pair(a,{'paid_units':0})['eligible_match'])

    def test_same_job_route_event_strong_match(self):
        p=assess_pair(axes(),{'paid_units':0})
        self.assertEqual(p['match_confidence'],'HIGH')
        self.assertEqual(p['relationship'],'REPEAT_OF_EXISTING_EXPERIMENT')

    def test_different_market_or_language_blocks_repeat(self):
        for key in ('marketplace','language'):
            a=axes();a[key]['status']='DIFFERENT'
            self.assertFalse(assess_pair(a,{'paid_units':0})['eligible_match'])

    def test_positive_prior_is_not_automatic_go_or_known_mechanism(self):
        a=axes();a['job']['status']='PARTIAL';a['freshness_event']['status']='UNKNOWN'
        p=assess_pair(a,{'paid_units':171})
        self.assertEqual(p['relationship'],'ADJACENT_TO_PRIOR_SUCCESS')
        self.assertFalse(p['automatic_go']);self.assertEqual(p['causal_mechanism'],'UNKNOWN')

    def test_negative_prior_parks_context_not_wide(self):
        c=decision_context([prior(axes(),0)],'PARTIAL',{'state':'NONE','statement':'same event','evidence':[]},'INVESTIGATE')
        self.assertEqual(c['implication'],'PARK_CONTEXT_PENDING_MATERIAL_DIFFERENCE')
        self.assertEqual(c['external_status_preserved'],'INVESTIGATE')
        self.assertFalse(c['automatic_kill'])

    def test_verified_new_event_can_leave_investigation_rational(self):
        c=decision_context([prior(axes(),0)],'PARTIAL',{'state':'VERIFIED','statement':'New event with evidence','evidence':[axes()['job']['external_evidence'][0]]},'INVESTIGATE')
        self.assertEqual(c['implication'],'OWNER_REVIEW_CONDITIONAL_INVESTIGATION')
        self.assertEqual(c['market_demand_verdict'],'UNKNOWN')

    def test_verified_difference_without_evidence_rejects(self):
        with self.assertRaises(ValidationError):
            decision_context([prior(axes(),0)],'PARTIAL',{'state':'VERIFIED','evidence':[]},'INVESTIGATE')

    def test_unrelated_guide_is_not_match(self):
        a=axes();a['job']['status']='DIFFERENT';a['audience']['status']='DIFFERENT'
        self.assertFalse(assess_pair(a,{'paid_units':0})['eligible_match'])

    def test_no_match_does_not_prove_novelty_with_partial_catalog(self):
        c=decision_context([],'PARTIAL',{'state':'UNKNOWN'},'INVESTIGATE')
        self.assertEqual(c['relationship'],'UNKNOWN');self.assertEqual(c['implication'],'NORMAL_EXTERNAL_PIPELINE')

    def test_sufficient_coverage_can_record_novel(self):
        self.assertEqual(decision_context([],'SUFFICIENT',{'state':'UNKNOWN'},'INVESTIGATE')['relationship'],'NOVEL_MARKET')

    def test_evidence_required_on_both_sides(self):
        a=axes();a['job']['internal_evidence']=[]
        with self.assertRaises(ValidationError):assess_pair(a,{'paid_units':0})

    def test_all_axes_explicit(self):
        a=axes();del a['job']
        with self.assertRaises(ValidationError):assess_pair(a,{'paid_units':0})

    def test_reference_change_and_escape_reject(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'fixture.json').write_text('{}')
            ref=reference(root,'fixture.json','id=1');verify_reference(root,ref)
            (root/'fixture.json').write_text('{"changed":true}')
            with self.assertRaises(ValidationError):verify_reference(root,ref)
            with self.assertRaises(ValidationError):reference(root,'../outside','id=1')

    def test_missing_canonical_state_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValidationError):internal_projection(Path(d),'2026-10-04')


class SyntheticPriorIntegrationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.path = self.root / 'book-radar/audits/synthetic-prior'
        self.path.mkdir(parents=True)
        note = self.root / 'book-radar/audits/observation-attribution-v1/DATA_OBSERVABILITY_V1.md'
        note.parent.mkdir(parents=True)
        note.write_text('Synthetic observability limitations; no real account data.')
        state = empty_state()
        for name, units in [('pmp-2026', 0), ('odyssey-tp', 73)]:
            book, actual, claim = outcome_fixture(self.root)
            book.update(id='book:' + name, product_id='product:' + name, audit_book_id=name,
                        title='Synthetic ' + name, publication_date='2026-09-01')
            actual.update(id='actual:' + name, book_id=book['id'], product_id=book['product_id'], book_age_days=31)
            actual['windows']['lifetime'].update(processed_units=units, paid_units=units, ebook_paid=units)
            refresh(actual)
            claim.update(id='forecast:' + name, metric='UNKNOWN', range='UNKNOWN')
            state['products'].append({'id':book['product_id']})
            state['observed_books'].append(book)
            state['actuals'].append(actual)
            state['calibrations'].append(calibrate(claim, actual, book))
        save_state(self.root, state)
        wide = self.root / 'book-radar/audits/live-wide-market-scan-v2/engine-run.json'
        wide.parent.mkdir(parents=True)
        wide.write_text('{"synthetic":true,"opportunities":["pmp","unrelated"]}')
        external = reference(self.root, str(wide.relative_to(self.root)), 'synthetic opportunity')
        internal = reference(self.root, 'book-radar/state.json', 'synthetic prior')
        comparisons = axes()
        for axis in comparisons.values():
            axis['internal_evidence'] = [internal]
            axis['external_evidence'] = [external]
        request = {'opportunity_id':'synthetic:pmp', 'kind':'LIVE_SURVIVOR', 'external_status':'INVESTIGATE',
                   'external_ref':external, 'comparisons':[{'book_id':'book:pmp-2026', 'axes':comparisons}],
                   'coverage':'PARTIAL', 'coverage_note':'Synthetic catalog only',
                   'material_difference':{'state':'NONE', 'statement':'Same synthetic experiment', 'evidence':[external]},
                   'value_of_information':'MEDIUM', 'next_research':{'action':'Inspect synthetic gap',
                   'max_minutes':20, 'owner_authorization_required':True}}
        other = {**request, 'opportunity_id':'synthetic:unrelated', 'comparisons':[]}
        (self.path / 'review-inputs.json').write_text(json.dumps([request, other]))

    def test_pmp_actuals_and_read_only_projection(self):
        state=self.root/'book-radar/state.json';before=state.read_bytes()
        with patch('abvx_harness.book_radar.save_state',side_effect=AssertionError('read-only violation')):
            catalog=internal_projection(self.root,'2026-10-04')
        p=catalog['book:pmp-2026']
        self.assertEqual((p['paid_units'],p['free_units'],p['kenp'],p['royalties']),(0,0,10,0.04))
        self.assertEqual(p['observed_date'],'2026-10-02')
        self.assertEqual(p['attribution_state']['classification'],'INSUFFICIENT_OBSERVATION')
        self.assertEqual(p['calibration_state'][0]['status'],'UNKNOWN')
        self.assertIn('D30',p['current_checkpoint']['due_unrecorded'])
        self.assertEqual(before,state.read_bytes())

    def test_toki_pona_paid_positive_but_mechanism_uncertain(self):
        p=internal_projection(self.root,'2026-10-04')['book:odyssey-tp']
        self.assertEqual(p['paid_state'],'POSITIVE_PAID')
        self.assertEqual(p['attribution_state']['classification'],'INSUFFICIENT_OBSERVATION')
        a=axes();a['job']['status']='PARTIAL';a['freshness_event']['status']='UNKNOWN'
        self.assertEqual(assess_pair(a,p)['causal_mechanism'],'UNKNOWN')

    def test_concurrent_canonical_change_rejects(self):
        calls=0
        def changed(root,path,selector):
            nonlocal calls
            ref=reference(root,path,selector)
            if selector=='Radar canonical state':
                calls+=1
                if calls==2:ref['sha256']='0'*64
            return ref
        with patch('abvx_harness.book_radar_prior.reference',side_effect=changed):
            with self.assertRaisesRegex(ValidationError,'changed during'):
                internal_projection(self.root,'2026-10-04')

    def test_material_difference_stale_reference_rejects(self):
        requests=json.loads((self.path/'review-inputs.json').read_text())[:1]
        requests[0]['material_difference']['state']='VERIFIED'
        requests[0]['material_difference']['evidence'][0]['sha256']='0'*64
        with self.assertRaisesRegex(ValidationError,'evidence changed'):
            review(self.root,requests,'2026-10-04')

    def test_synthetic_overlay_pmp_surface_and_unchanged_wide(self):
        requests=json.loads((self.path/'review-inputs.json').read_text())
        wide=self.root/'book-radar/audits/live-wide-market-scan-v2/engine-run.json';before=wide.read_bytes()
        state=self.root/'book-radar/state.json';state_before=state.read_bytes()
        value=review(self.root,requests,'2026-10-04');validate(value)
        p=next(r for r in value['reviews'] if r['opportunity_id']=='synthetic:pmp')
        self.assertEqual(p['internal_matches'][0]['book_id'],'book:pmp-2026')
        self.assertEqual(p['context']['deep_research_priority'],'LOW')
        self.assertEqual(p['external_status'],'INVESTIGATE')
        self.assertEqual(before,wide.read_bytes());self.assertEqual(state_before,state.read_bytes())
        for r in value['reviews']:
            if r['kind']=='LIVE_SURVIVOR' and r is not p:self.assertEqual(r['internal_matches'],[])
        self.assertFalse(value['scoring_changes']);self.assertEqual(value['shelf_calls'],0)


if __name__=='__main__':unittest.main()
