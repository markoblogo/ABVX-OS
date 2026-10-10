"""Synthetic regression fixtures; no real experiments or retailer writes."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timezone
from abvx_harness.book_radar import empty_state, save_state, load_state, import_bundle, add_records
from abvx_harness.book_radar_attribution import (U, STAGES, COSTS, measure, attribute, validate_record,
    enable, report, render_cards, historical_view, series_summary)
from abvx_harness.book_radar_outcomes import checkpoint, evidence
from abvx_harness.harness import ValidationError
from test_book_radar_outcomes import fixture, refresh

class AttributionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.book,self.actual,self.claim=fixture(self.root);self.refs=self.book['evidence']
        self.owner=self.root/'owner.txt';self.owner.write_text('OWNER authorizes prospective Phase 2')
        out=self.root/'book-radar/audits/observation-attribution-v1';out.mkdir(parents=True)
        (out/'DATA_OBSERVABILITY_V1.md').write_text('Standard KDP surfaces do not expose matched readers.')
        s=empty_state();s['products']=[{'id':'product:old','prediction':{'range':[20,50]}}]
        s['opportunities']=[{'id':'opportunity:old'}]
        s['decisions']=[{'id':'decision:old','opportunity_id':'opportunity:old','decision':'winner'}]
        save_state(self.root,s);self.before=copy.deepcopy(s);enable(self.root,self.owner)
    def contract(self,waived=False):
        plan={k:'Synthetic fixture '+k for k in ['buyer','job','hypothesis','discovery_route','expected_path','alternatives','selection_reason','observation_window','success_condition','failure_condition','learning_goal']}
        plan.update(package_price={'format':'ebook','promise':'Synthetic test only','price':2.99,'currency':'EUR'},checkpoints=[0,7,14,30,60,90],evaluation_day=7,checkpoint_measures={f'D{d}':{'metric':'PAID_UNITS','target':1,'rule':'at least target, no causal implication'} for d in [0,7,14,30,60,90]})
        return {'schema_version':'book-radar-experiment-contract/v1','id':'experiment:test','product_id':'product:new','selection_decision_id':'decision:old','status':'WAIVED' if waived else 'FROZEN','frozen_at':datetime.now(timezone.utc).isoformat(),'plan':plan,'cost_budget':{**{c:0 for c in COSTS},'currency':'EUR'},'waiver':{'recorded_by':'OWNER','recorded_at':load_state(self.root)['experiment_policies'][0]['effective_at'],'reason':'Explicit synthetic test waiver','evidence':self.refs} if waived else None,'evidence':self.refs}
    def admit(self,waived=False):
        c=self.contract(waived);bundle={'schema_version':'book-radar-import/v1','products':[{'id':'product:new','title':'SYNTHETIC ONLY','opportunity_id':'opportunity:old','experiment_contract_id':c['id']}],'experiment_contracts':[c]}
        p=self.root/'bundle.json';p.write_text(json.dumps(bundle));import_bundle(self.root,p);return c
    def observation(self):
        o=historical_view(self.book,self.actual,[{'claim':self.claim}],'2026-10-02',self.refs[0])
        o.update(required_checkpoint_day=7,observed_date='2026-09-14',checkpoint=checkpoint(self.book['publication_date'],'2026-09-14',7))
        o['stages']={s:measure('POSITIVE','DIRECT_EVIDENCE',1,'D0-D7','TEST_COHORT',self.refs,'COMPLETE') for s in STAGES}
        o['reading']=measure()
        for key in ('paid_window','kenp_window','royalty_window'):o['actual_outcomes'][key]='2026-09-07/2026-09-14'
        return o
    def test_unknown_is_not_zero(self):
        o=self.observation();o['stages']['MARKET_OPPORTUNITY']=measure()
        self.assertNotEqual(o['stages']['MARKET_OPPORTUNITY'],measure('ZERO','DIRECT_DEMAND_TEST',0))
        self.assertEqual(attribute(o)['classification'],U)
    def test_absence_cannot_be_a_rank(self):
        snap={'schema_version':'book-radar-search-snapshot/v1','id':'search:test','book_id':U,'experiment_id':U,'observed_date':'2026-10-03','observed_at':U,'marketplace':'amazon.com','query':'synthetic query','device_surface':U,'signed_in_context':U,'delivery_context':U,'depth':16,'presence':'NOT_FOUND_WITHIN_DEPTH','rank':U,'rank_basis':'ORGANIC','target_asin':U,'competing_results':[],'competitor_capture_status':U,'category_context':U,'method':'READ_ONLY_RETAILER_SNAPSHOT','repeat_protocol_id':'protocol:test','evidence':self.refs,'limitations':['Synthetic bounded test']}
        validate_record(snap,'search_snapshots');snap['rank']=17
        with self.assertRaises(ValidationError):validate_record(snap,'search_snapshots')
    def test_no_sales_do_not_establish_market_failure(self):
        o=self.observation();o['stages']['MARKET_OPPORTUNITY']=measure()
        o['stages']['PURCHASE_READ']=measure('ZERO','PAID_UNITS',0,'D0-D7','TEST_COHORT',self.refs,'COMPLETE')
        self.assertEqual(attribute(o)['classification'],U)
    def test_direct_market_test_is_required(self):
        o=self.observation();o['stages']['MARKET_OPPORTUNITY']=measure('ZERO','PAID_UNITS',0,'D0-D7','TEST_COHORT',self.refs,'COMPLETE')
        self.assertEqual(attribute(o)['classification'],U)
        o['stages']['MARKET_OPPORTUNITY']['metric']='DIRECT_DEMAND_TEST'
        self.assertEqual(attribute(o)['classification'],'MARKET_HYPOTHESIS_UNSUPPORTED')
    def test_discovery_is_not_conversion(self):
        o=self.observation();o['stages']['DISCOVERY']=measure('ZERO','QUERY_PRESENCE',0,'D0-D7','TEST_COHORT',self.refs,'COMPLETE')
        self.assertEqual(attribute(o)['classification'],U)
        o['stages']['DISCOVERY']['metric']='FROZEN_ROUTE_TEST'
        self.assertEqual(attribute(o)['classification'],'NOT_DISCOVERED')
    def test_customer_impressions_required_for_click_failure(self):
        o=self.observation();o['stages']['VISIBILITY']['metric']='QUERY_PRESENCE'
        o['stages']['DETAIL_PAGE_VISIT']=measure('ZERO','DETAIL_PAGE_VISITS',0,'D0-D7','TEST_COHORT',self.refs,'COMPLETE')
        self.assertEqual(attribute(o)['classification'],U)
        o['stages']['VISIBILITY']['metric']='CUSTOMER_IMPRESSIONS'
        self.assertEqual(attribute(o)['classification'],'DISCOVERED_NOT_CLICKED')
    def test_conversion_requires_known_upstream_and_comparable_window(self):
        o=self.observation();o['stages']['DETAIL_PAGE_VISIT']['metric']='DETAIL_PAGE_VISITS'
        o['stages']['PURCHASE_READ']=measure('ZERO','PAID_UNITS',0,'D0-D7','TEST_COHORT',self.refs,'COMPLETE')
        self.assertEqual(attribute(o)['classification'],'VISITED_NOT_CONVERTED')
        for block in [U,'NOT_OBSERVABLE']:
            o['stages']['DISCOVERY']=measure(block,refs=self.refs)
            self.assertEqual(attribute(o)['classification'],U)
        o=self.observation();o['stages']['DETAIL_PAGE_VISIT']['metric']='DETAIL_PAGE_VISITS'
        o['stages']['PURCHASE_READ']=measure('ZERO','PAID_UNITS',0,'lifetime','TEST_COHORT',self.refs,'COMPLETE')
        self.assertEqual(attribute(o)['classification'],U)
    def test_zero_kenp_is_not_matched_purchaser_nonreading(self):
        o=self.observation();o['stages']['PURCHASE_READ']['metric']='PAID_UNITS'
        o['reading']=measure('ZERO','KENP_PAGES',0,'D0-D7','TEST_COHORT',self.refs,'COMPLETE')
        self.assertEqual(attribute(o)['classification'],U)
        o['reading']['metric']='MATCHED_PURCHASER_READS'
        self.assertEqual(attribute(o)['classification'],'PURCHASED_NOT_READ')
    def test_free_kenp_royalty_are_not_orders(self):
        self.actual['windows']['lifetime'].update(free_units=26,processed_units=26)
        refresh(self.actual);o=historical_view(self.book,self.actual,[],'2026-10-02',self.refs[0])
        self.assertEqual(o['actual_outcomes']['paid_units'],0)
        self.assertEqual(o['actual_outcomes']['free_units'],26)
        self.assertEqual(o['actual_outcomes']['kenp'],10)
        self.assertEqual(o['actual_outcomes']['estimated_royalties'],0.04)
        self.assertEqual(attribute(o)['classification'],'INSUFFICIENT_OBSERVATION')
    def test_historical_unknown_numeric_does_not_become_zero(self):
        self.actual['windows']['lifetime']['paid_units']=U;self.actual['windows']['kenp']['kenp_pages']=U
        o=historical_view(self.book,self.actual,[],'2026-10-02',self.refs[0])
        self.assertEqual(o['stages']['PURCHASE_READ']['state'],U)
    def test_pending_checkpoint_is_insufficient_not_adjudicated(self):
        o=self.observation();o.update(required_checkpoint_day=90,observed_date='2026-10-02',checkpoint=checkpoint(self.book['publication_date'],'2026-10-02',90))
        self.assertEqual(attribute(o)['classification'],'INSUFFICIENT_OBSERVATION')
        validate_record(o,'attribution_observations')
        o['checkpoint']['status']='EXACT'
        with self.assertRaises(ValidationError):validate_record(o,'attribution_observations')
    def test_prospective_only_and_historical_unchanged(self):
        c=self.admit();s=load_state(self.root)
        for col in self.before:self.assertEqual(s[col][:len(self.before[col])],self.before[col]) if isinstance(self.before[col],list) else None
        self.assertEqual(s['products'][0],self.before['products'][0]);self.assertEqual(len(s['experiment_contracts']),1)
        self.assertEqual(c['product_id'],'product:new')
    def test_historical_record_rewrite_rejected_after_cutover(self):
        s=load_state(self.root);s['products'][0]['prediction']['range']=[99,100]
        with self.assertRaises(ValidationError):save_state(self.root,s)
    def test_new_product_even_old_candidate_needs_contract(self):
        s=load_state(self.root);s['products'].append({'id':'product:new','opportunity_id':'opportunity:old'})
        with self.assertRaises(ValidationError):save_state(self.root,s)
    def test_product_cannot_bypass_gate_by_omitting_opportunity(self):
        p=self.root/'product.json';p.write_text(json.dumps({'id':'product:new'}))
        with self.assertRaises(ValidationError):add_records(self.root,'products',p)
    def test_freeze_must_precede_production_without_backdating(self):
        c=self.contract();p=self.root/'bundle.json';before=(self.root/'book-radar/state.json').read_bytes()
        bundle={'schema_version':'book-radar-import/v1','products':[{'id':'product:new','opportunity_id':'opportunity:old','experiment_contract_id':c['id'],'production_started_at':'2000-01-01T00:00:00+00:00'}],'experiment_contracts':[c]}
        p.write_text(json.dumps(bundle))
        with self.assertRaises(ValidationError):import_bundle(self.root,p)
        self.assertEqual(before,(self.root/'book-radar/state.json').read_bytes())
        bundle['products'][0].pop('production_started_at');c['frozen_at']='2000-01-01T00:00:00+00:00';p.write_text(json.dumps(bundle))
        with self.assertRaises(ValidationError):import_bundle(self.root,p)
    def test_frozen_contract_fields_and_measures_mandatory(self):
        c=self.contract();validate_record(c,'experiment_contracts')
        for key in ['buyer','hypothesis','discovery_route','learning_goal']:
            bad=copy.deepcopy(c);bad['plan'][key]=U
            with self.assertRaises(ValidationError):validate_record(bad,'experiment_contracts')
        bad=copy.deepcopy(c);bad['plan']['checkpoints']=[7]
        with self.assertRaises(ValidationError):validate_record(bad,'experiment_contracts')
        bad=copy.deepcopy(c);bad['plan']['package_price']['price']=U
        with self.assertRaises(ValidationError):validate_record(bad,'experiment_contracts')
    def test_waiver_remains_explicit_in_cards(self):
        self.admit(True);r=report(self.root,'cards','2099-01-01')
        self.assertEqual(r['experiments'][0]['status'],'WAIVED')
        self.assertIn('OWNER waiver',render_cards(r));self.assertIn('Explicit synthetic test waiver',render_cards(r))
    def test_waiver_does_not_manufacture_a_testable_hypothesis(self):
        o=self.observation();o['stages']['MARKET_OPPORTUNITY']=measure('ZERO','DIRECT_DEMAND_TEST',0,'D0-D7','TEST_COHORT',self.refs,'COMPLETE')
        c=self.contract(True);c['plan']['hypothesis']=U
        self.assertEqual(attribute(o,c)['classification'],U)
        self.assertEqual(c['status'],'WAIVED')
    def test_contract_and_policy_immutable(self):
        self.admit();s=load_state(self.root);s['experiment_contracts'][0]['plan']['hypothesis']='Hindsight rewrite'
        with self.assertRaises(ValidationError):save_state(self.root,s)
        s=load_state(self.root);s['experiment_policies']=[]
        with self.assertRaises(ValidationError):save_state(self.root,s)
    def test_new_product_cannot_be_grandfathered_in_atomic_enable(self):
        s=load_state(self.root);s['experiment_policies'][0]['historical_product_ids'].append('product:new');s['products'].append({'id':'product:new'})
        with self.assertRaises(ValidationError):save_state(self.root,s)
    def test_missing_cost_stays_unknown(self):
        self.admit();r=report(self.root,'cards','2099-01-01')
        self.assertTrue(all(v==U for v in r['experiments'][0]['actual_cost'].values()))
        self.assertTrue(all(v==U for v in r['experiments'][0]['checkpoint_observations'].values()))
    def test_import_hash_provenance_checked(self):
        c=self.contract();c['evidence'][0]['sha256']='0'*64
        p=self.root/'bundle.json';p.write_text(json.dumps({'schema_version':'book-radar-import/v1','products':[{'id':'product:new','opportunity_id':'opportunity:old','experiment_contract_id':c['id']}],'experiment_contracts':[c]}))
        with self.assertRaises(ValidationError):import_bundle(self.root,p)
    def test_production_authorization_without_contract_rejected(self):
        s=load_state(self.root);s['decisions'].append({'id':'decision:new','opportunity_id':'opportunity:old','production_authorized':True})
        with self.assertRaises(ValidationError):save_state(self.root,s)
    def test_catalog_sales_ratios_are_not_readthrough(self):
        o={'method':'AGGREGATE_CATALOG_ONLY','entrants':U,'continuers':U}
        self.assertEqual(series_summary(o)['read_through'],U)
        o.update(method='DIRECT_MATCHED_COHORT',entrants=10,continuers=4)
        self.assertEqual(series_summary(o)['read_through'],0.4)
    def test_readthrough_requires_matching_and_book_pair(self):
        o={'schema_version':'book-radar-series-observation/v1','id':'series:test','observed_date':'2026-10-03','series_id':'series:example','book_ids':['book:A','book:B'],'membership_basis':'OFFICIAL_SERIES','membership_evidence':self.refs,'window':'D0-D90','scope':'TEST_COHORT','method':'AGGREGATE_CATALOG_ONLY','entry_book_id':U,'continuation_book_id':U,'cohort_basis':U,'entrants':U,'continuers':U,'identity_evidence':[],'paid_units':U,'free_units':U,'kenp':U,'estimated_royalties':U,'currency':U,'evidence':[]}
        validate_record(o,'series_observations');o.update(entrants=10,continuers=4)
        with self.assertRaises(ValidationError):validate_record(o,'series_observations')
        o.update(method='DIRECT_MATCHED_COHORT',entry_book_id='book:A',continuation_book_id='book:B',cohort_basis='READERS',identity_evidence=self.refs)
        validate_record(o,'series_observations')
        o['continuers']=11
        with self.assertRaises(ValidationError):validate_record(o,'series_observations')
    def test_evidence_cannot_relabel_free_as_paid(self):
        o=self.observation();o['stages']['PURCHASE_READ']=measure('POSITIVE','PAID_UNITS',26,'D0-D7','TEST_COHORT',self.refs,'COMPLETE')
        with self.assertRaises(ValidationError):validate_record(o,'attribution_observations')
    def test_import_idempotent(self):
        self.admit();source=self.root/'bundle.json';before=(self.root/'book-radar/state.json').read_bytes()
        receipt=import_bundle(self.root,source)
        self.assertTrue(all(n==0 for n in receipt['added'].values()))
        self.assertEqual(before,(self.root/'book-radar/state.json').read_bytes())
    def test_reports_are_read_only_and_complete_stage_vector(self):
        self.admit();before=(self.root/'book-radar/state.json').read_bytes()
        r=report(self.root,'funnel','2099-01-01');self.assertEqual(r['first_unknown_or_unobservable'],{'MARKET_OPPORTUNITY':1})
        self.assertEqual(before,(self.root/'book-radar/state.json').read_bytes())
    def test_late_observation_cannot_adjudicate_exact_checkpoint(self):
        o=self.observation();o.update(required_checkpoint_day=7,observed_date='2026-09-15',checkpoint=checkpoint(self.book['publication_date'],'2026-09-15',7))
        self.assertEqual(attribute(o)['classification'],U)
        validate_record(o,'attribution_observations')

if __name__=='__main__':unittest.main()
