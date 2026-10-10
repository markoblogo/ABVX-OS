import copy
import json
import tempfile
import unittest
from pathlib import Path
from abvx_harness.book_radar import DEFAULT_MODEL, empty_state, load_state, save_state, score_values
from abvx_harness.book_radar_outcomes import (UNKNOWN as U, calibrate, checkpoint, classify, cohort_summary,
    evidence, funnel, import_foundation, outcome_report, validate_record)
from abvx_harness.harness import ValidationError


def fixture(root):
    (root/'raw.txt').write_text('observed report')
    ref=[evidence(root,'raw.txt')]
    book={'schema_version':'book-radar-observed-book/v1','id':'book:test','title':'Test','audit_book_id':'test','product_id':'product:test','initial_experiment':True,'cohorts':['TOKI_PONA'],'mechanisms':['TOKI_PONA_NICHE'],'classification_limitations':['Descriptive only'],'radar_run_id':U,'decision_ids':[],'publication_date':'2026-09-07','publication_timestamp':U,'first_verified_live_date':'2026-09-21','date_evidence':ref,'formats':[],'evidence':ref}
    units={'start':'2026-09-01','end':'2026-10-02','processed_units':0,'paid_units':0,'free_units':0,'ebook_paid':0,'print_paid':0,'evidence':ref}
    money={'start':'2026-09-01','end':'2026-10-02','estimated_royalties':0.04,'ebook':0,'print':0,'kenp':0.04,'currency':'EUR','status':'ESTIMATE','evidence':ref}
    actual={'schema_version':'book-radar-observed-actual/v1','id':'actual:test','book_id':book['id'],'product_id':book['product_id'],'observed_date':'2026-10-02','book_age_days':25,'age_basis':'PUBLICATION_DATE','checkpoint':'AD_HOC','marketplace_scope':'KDP_ACCOUNT','windows':{'lifetime':copy.deepcopy(units),'recent':copy.deepcopy(units),'money':copy.deepcopy(money),'recent_money':copy.deepcopy(money),'kenp':{'start':'2026-09-01','end':'2026-09-30','kenp_pages':10,'status':'PROVISIONAL','evidence':ref}},'instrumentation':{k:U for k in ['impressions','clicks','detail_page_visits','sample_opens','ku_starts','ad_impressions','ad_clicks','ctr','conversion']},'instrumentation_window':U,'instrumentation_evidence':[],'economics':{k:U for k in ['api_cost','other_machine_cost','owner_attention_minutes','production_elapsed_minutes','rework_minutes','paid_promotion_cost','acquisition_cost','currency']},'retailer_events':{k:{'state':U,'evidence':[],'window':U} for k in ['PUBLISHED','INDEXED','DISCOVERABLE']},'discovery':[],'category_observations':[],'other_discovery_evidence':[],'identity_evidence':ref}
    actual['stage_applicability']={st:{'state':U,'evidence':[]} for st in ['PUBLISHED','INDEXED','DISCOVERABLE','EXPOSED','CLICKED','PURCHASED','READ']}
    refresh(actual)
    claim={'id':'forecast:test','metric':'paid_units','basis':'PAID_PROCESSED','horizon_days':90,'range':[20,50],'evidence':ref,'source_kind':'PREPUBLICATION'}
    return book,actual,claim

def refresh(actual):
    actual['funnel']=funnel(actual);actual['classification']=classify(actual)

class OutcomeFoundationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.book,self.actual,self.claim=fixture(self.root)
    def test_free_is_not_paid(self):
        self.actual['windows']['lifetime'].update(processed_units=26,free_units=26)
        refresh(self.actual);validate_record(self.actual,'actuals')
        self.assertEqual(self.actual['funnel']['PURCHASED']['state'],'OBSERVED_ZERO')
    def test_unknown_is_not_zero(self):
        self.actual['windows']['lifetime'].update(processed_units=U,paid_units=U,free_units=U,ebook_paid=U,print_paid=U)
        refresh(self.actual);validate_record(self.actual,'actuals')
        self.assertEqual(self.actual['funnel']['PURCHASED']['state'],U)
        self.assertEqual(self.actual['funnel']['EXPOSED']['state'],U)
    def test_kenp_is_not_order(self):
        self.assertEqual(self.actual['funnel']['READ']['state'],'OBSERVED_POSITIVE')
        self.assertEqual(self.actual['funnel']['PURCHASED']['state'],'OBSERVED_ZERO')
    def test_royalty_change_is_not_sale(self):
        before=copy.deepcopy(self.actual['funnel']);self.actual['windows']['money']['estimated_royalties']=40
        refresh(self.actual);self.assertEqual(before,self.actual['funnel'])
    def test_first_live_is_not_publication_date_or_timestamp(self):
        self.book['publication_date']=U;self.actual['book_age_days']=U;self.actual['age_basis']=U
        state=self.state();save_state(self.root,state)
        r=outcome_report(self.root,'checkpoints','2026-10-02')['experiments'][0]
        self.assertEqual(r['next_due'],U);self.assertEqual(self.book['publication_timestamp'],U)
    def test_not_found_within_depth_is_not_deeper_rank(self):
        self.actual['discovery']=[{'observed_date':'2026-09-21','observed_at':U,'marketplace':'amazon.com','query':'bounded query','surface':U,'signed_in_context':U,'depth_inspected':16,'position':U,'placement':U,'result':'NOT_FOUND_WITHIN_DEPTH','asin':U,'title_id':self.book['id'],'evidence':self.book['evidence'],'limitations':['Only one query']}]
        refresh(self.actual);validate_record(self.actual,'actuals')
        self.assertEqual(self.actual['classification']['classification'],U)
        self.assertEqual(self.actual['classification']['findings'][0]['classification'],'NOT_FOUND_IN_OBSERVED_DEPTH')
        self.actual['discovery'][0]['position']=17
        with self.assertRaises(ValidationError):validate_record(self.actual,'actuals')
    def test_d25_zero_does_not_fail_d90(self):
        c=calibrate(self.claim,self.actual,self.book)
        self.assertEqual(c['status'],'NOT_YET_ADJUDICABLE');self.assertEqual(c['early_signal'],'NEGATIVE_EARLY_SIGNAL')
    def test_money_claim_cannot_be_compared_to_paid_units(self):
        self.claim['metric']='estimated_royalties'
        self.assertEqual(calibrate(self.claim,self.actual,self.book)['status'],'INCOMPARABLE')
    def test_exact_horizon_and_paid_definition_required(self):
        self.actual['book_age_days']=90;self.actual['observed_date']='2026-12-06'
        for key in ['lifetime','recent']:self.actual['windows'][key]['end']='2026-12-06'
        c=calibrate(self.claim,self.actual,self.book);self.assertEqual(c['status'],'NOT_SUPPORTED')
        self.claim['basis']='UNSPECIFIED_SALES_UNITS';self.assertEqual(calibrate(self.claim,self.actual,self.book)['status'],'INCOMPARABLE')
        self.claim['basis']='PAID_PROCESSED';self.actual['book_age_days']=91
        self.assertEqual(calibrate(self.claim,self.actual,self.book)['status'],'INCOMPARABLE')
    def test_checkpoints_do_not_manufacture_dates(self):
        for day in [0,7,14,30,60,90]:
            from datetime import date,timedelta
            observed=(date(2026,9,7)+timedelta(days=day)).isoformat()
            self.assertEqual(checkpoint('2026-09-07',observed,day)['status'],'EXACT')
        cp=checkpoint('2026-09-07','2026-10-02',30);self.assertEqual(cp['status'],'PENDING');self.assertEqual(cp['actual_book_age_days'],25)
        self.assertEqual(checkpoint('2026-09-07','2026-10-08',30)['status'],'LATE')
        self.assertEqual(checkpoint('2026-09-07','2026-10-06',30,approximate_tolerance=1)['status'],'APPROXIMATE')
    def test_impressions_without_click_denominator_is_unknown(self):
        self.actual['instrumentation']['impressions']=100;self.actual['instrumentation_evidence']=self.book['evidence'];self.actual['instrumentation_window']='lifetime'
        refresh(self.actual);self.assertEqual(self.actual['classification']['classification'],U)
        self.actual['instrumentation']['clicks']=0;refresh(self.actual)
        self.assertEqual(self.actual['classification']['classification'],'EXPOSURE_WITHOUT_CLICK')
        self.actual['instrumentation']['clicks']=5;refresh(self.actual)
        self.assertEqual(self.actual['classification']['classification'],'CLICK_WITHOUT_PURCHASE')
        self.actual['instrumentation_window']='recent';refresh(self.actual)
        self.assertEqual(self.actual['classification']['classification'],U)
    def test_not_applicable_requires_explicit_evidence(self):
        self.actual['stage_applicability']['CLICKED']={'state':'NOT_APPLICABLE','evidence':self.book['evidence']}
        refresh(self.actual);validate_record(self.actual,'actuals')
        self.assertEqual(self.actual['funnel']['CLICKED']['state'],'NOT_APPLICABLE')
        self.actual['stage_applicability']['READ']={'state':'NOT_APPLICABLE','evidence':self.book['evidence']}
        with self.assertRaises(ValidationError):refresh(self.actual)
    def test_unknown_cohort_metrics_remain_unknown(self):
        self.actual['windows']['lifetime']['free_units']=U
        summary=cohort_summary(self.state(),{'actual_ids':['actual:test'],'currency':'EUR','totals':{'paid_units':0}})
        self.assertEqual(summary['cohorts']['TOKI_PONA']['free_units'],U)
    def test_schema_rejects_bool_negative_missing_evidence(self):
        for bad in [-1,False]:
            self.actual['windows']['lifetime']['paid_units']=bad
            with self.assertRaises(ValidationError):validate_record(self.actual,'actuals')
        self.actual['windows']['lifetime']['paid_units']=0;self.actual['windows']['lifetime']['evidence']=[]
        with self.assertRaises(ValidationError):validate_record(self.actual,'actuals')
    def state(self):
        s=empty_state();s['products']=[{'id':self.book['product_id'],'prediction':{'range':[20,50],'horizon_days':90}}]
        s['observed_books']=[self.book];s['actuals']=[self.actual];return s
    def test_actuals_and_calibration_do_not_mutate_prediction_or_model(self):
        s=self.state();prediction=copy.deepcopy(s['products']);claim=copy.deepcopy(self.claim);model=copy.deepcopy(DEFAULT_MODEL)
        s['calibrations']=[calibrate(self.claim,self.actual,self.book)];save_state(self.root,s)
        self.assertEqual(load_state(self.root)['products'],prediction);self.assertEqual(self.claim,claim);self.assertEqual(DEFAULT_MODEL,model)
    def test_toki_cohort_is_descriptive_without_score_bonus(self):
        s=self.state();baseline={'actual_ids':['actual:test'],'currency':'EUR','totals':{'paid_units':0}}
        score=score_values({k:3 for k in DEFAULT_MODEL['weights']},{},DEFAULT_MODEL)
        c=cohort_summary(s,baseline);self.assertEqual(c['cohorts']['TOKI_PONA']['title_count'],1)
        self.assertEqual(c['causality'],'NOT_ESTABLISHED');self.assertEqual(c['scoring_effect'],'NONE')
        self.assertEqual(score_values({k:3 for k in DEFAULT_MODEL['weights']},{},DEFAULT_MODEL),score)
    def test_import_idempotent_and_collision_atomic(self):
        s=empty_state();s['products']=[{'id':self.book['product_id'],'prediction':{'range':[20,50]}}];save_state(self.root,s)
        source=self.root/'import.json';bundle={'schema_version':'book-radar-outcome-import/v1','observed_books':[self.book],'actuals':[self.actual],'calibrations':[calibrate(self.claim,self.actual,self.book)]}
        source.write_text(json.dumps(bundle));first=import_foundation(self.root,source);before=(self.root/'book-radar/state.json').read_bytes()
        self.assertEqual(first['added']['actuals'],1);self.assertEqual(import_foundation(self.root,source)['added']['actuals'],0)
        self.assertEqual(before,(self.root/'book-radar/state.json').read_bytes())
        bundle['actuals'][0]['windows']['money']['estimated_royalties']=9;source.write_text(json.dumps(bundle))
        with self.assertRaises(ValidationError):import_foundation(self.root,source)
        self.assertEqual(before,(self.root/'book-radar/state.json').read_bytes())
    def test_import_verifies_evidence_hash_before_write(self):
        s=empty_state();s['products']=[{'id':self.book['product_id']}];save_state(self.root,s)
        source=self.root/'import.json';source.write_text(json.dumps({'schema_version':'book-radar-outcome-import/v1','observed_books':[self.book],'actuals':[self.actual]}))
        before=(self.root/'book-radar/state.json').read_bytes();(self.root/'raw.txt').write_text('tampered')
        with self.assertRaises(ValidationError):import_foundation(self.root,source)
        self.assertEqual(before,(self.root/'book-radar/state.json').read_bytes())
    def test_read_only_reports_do_not_modify_state(self):
        save_state(self.root,self.state());before=(self.root/'book-radar/state.json').read_bytes()
        for kind in ['outcomes','cohorts','calibration','checkpoints']:outcome_report(self.root,kind,'2026-10-02')
        self.assertEqual(before,(self.root/'book-radar/state.json').read_bytes())

if __name__=='__main__':unittest.main()
