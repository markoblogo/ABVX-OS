import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from abvx_harness import book_radar_wide as wide

REAL = Path(__file__).resolve().parents[1]

class WideTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        (self.base/'raw.txt').write_text('SYNTHETIC retained observations, not market evidence.\n')
        sha=hashlib.sha256((self.base/'raw.txt').read_bytes()).hexdigest()
        self.packet={'schema_version':'book-radar-wide-input/v1','run_id':'synthetic-test','origin':'SYNTHETIC','as_of':'2026-10-03T12:00:00Z','evidence':[{'id':'e1','path':'raw.txt','sha256':sha,'kind':'EXTERNAL','source_uri':'https://publisher.example/catalog','market':'Amazon.com','language':'EN'}],'signals':[{'schema_version':'book-radar-wide-signal/v1','signal_id':'s1','observed_at':'2026-10-03T10:00:00Z','source_family':'BOOK_MARKET','source':'https://publisher.example/catalog','market':'Amazon.com','language':'EN','raw_phrase':'huge general topic','evidence_ids':['e1'],'freshness':{'source_date':'2026-10-02','date_basis':'PUBLICATION'},'initial_intent':'GENERAL_INFORMATION_INTENT','provenance':{'kind':'EXTERNAL','recorded_by':'offline-fixture'},'buyer_job':{'audience':'curious readers','job':'find a quick fact','intent':'GENERAL_INFORMATION_INTENT','query':'huge general topic','subject':'general','category':'general','bucket':'OTHER','mechanism':'OTHER'}}]}
    def path(self):
        p=self.base/'input.json';p.write_text(json.dumps(self.packet));return p
    def test_weak_reading_intent_killed_before_deep_shelf(self):
        result=wide.screen(self.path())
        self.assertEqual(result['clusters'][0]['decision'],'KILL')
        self.assertEqual(result['clusters'][0]['decision_reason'],'GENERAL_INFORMATION_ONLY')
        self.assertEqual(result['counts']['quick_screen'],0)
        self.assertFalse(result['canonical_state_written'])
        self.assertFalse((self.base/'book-radar').exists())

    def readable(self):
        s=self.packet['signals'][0];s['job_support']='SUPPORTS';s['initial_intent']=s['buyer_job']['intent']='BOOK_SERVED_LEARNING_INTENT'
        e=copy.deepcopy(self.packet['evidence'][0]);e.update(id='e2',source_uri='https://community.example/discussion');self.packet['evidence'].append(e)
        t=copy.deepcopy(s);t.update(signal_id='s2',source_family='COMMUNITY',source=e['source_uri'],evidence_ids=['e2']);self.packet['signals'].append(t)
        return wide.cluster_id(s['buyer_job'],s['market'],s['language'])

    def quick(self,**changes):
        cid=self.readable();features={k:{'value':v,'evidence_ids':['e1'],'observation_ids':['o1']} for k,v in {'book_serving':'PRESENT','activity':'PRESENT','entrants':'PRESENT','incumbent':'ABSENT','sponsored':'ABSENT','query_relevance':'PRESENT'}.items()}
        for k,v in changes.items():features[k]={'value':v,'evidence_ids':[] if v=='UNKNOWN' else ['e1'],'observation_ids':[] if v=='UNKNOWN' else ['o1']}
        self.packet['quick_screens']=[{'cluster_id':cid,'market':'Amazon.com','language':'EN','query':'home guide','observed_at':'2026-10-03T10:00:00Z','organic_depth_reached':5,'sponsored_depth_reached':1,'sample_complete':True,'context':{'delivery':'synthetic US','locale':'EN','signed_in':'NO','sort':'Featured'},'observations':[{'id':'o1','text':'SYNTHETIC five relevant books, activity context, recent organic-listed formats. No paid-demand or cold-start proof.','evidence_ids':['e1']}],'features':features,'rights':'NO_OBVIOUS_BLOCK','value_of_information':'HIGH'}]
        return self.packet['quick_screens'][0]

    def test_dead_shelf_killed_with_retained_reason_and_cost(self):
        self.quick(activity='ABSENT');c=wide.screen(self.path())['clusters'][0]
        self.assertEqual(c['decision_reason'],'VISIBLE_ACTIVITY_ABSENT');self.assertEqual(c['decision'],'KILL')
        self.assertTrue(c['decision_evidence']);self.assertIn('cost_to_kill',c['kill_record'])

    def test_unknown_high_value_parks_not_demands(self):
        self.quick(activity='UNKNOWN');c=wide.screen(self.path())['clusters'][0]
        self.assertEqual(c['decision'],'PARK');self.assertEqual(c['park']['value_of_information'],'HIGH')
        self.assertTrue(c['park']['next_required_evidence'])

    def test_survivor_handoff_is_exact_shelf_cluster_shape(self):
        self.quick();result=wide.screen(self.path());self.assertEqual(result['counts']['investigate'],1)
        h=wide.handoff(result,result['clusters'][0]['cluster_id'])
        from abvx_harness.schema_validation import draft_2020_12_validator
        schema=json.loads((REAL/'schemas/EXTERNAL_SHELF_SNAPSHOT_SCHEMA_V1.json').read_text())['properties']['cluster']
        draft_2020_12_validator(schema).validate(h['cluster'])
        self.assertFalse(h['canonical_state_written']);self.assertTrue(h['requires_owner_authorized_collection'])

    def test_required_offline_cases_A_to_M(self):
        cases=json.loads((REAL/'tests/fixtures/wide-screener-v1/cases.json').read_text())
        for key,c in cases.items():
            with self.subTest(case=key):
                r=wide.screen(REAL/'tests/fixtures/wide-screener-v1'/c['file'])
                if key=='I':
                    self.assertEqual(next(x['decision'] for x in r['clusters'] if x['language']=='FR'),'PARK')
                    self.assertEqual(next(x['decision'] for x in r['clusters'] if x['language']=='EN'),'INVESTIGATE')
                else:self.assertEqual(r['clusters'][0]['decision'],c['expected'])
                if key in ('F','H'):self.assertEqual(r['counts']['normalized'],1)
                if key=='G':self.assertEqual(len(r['clusters'][0]['corroboration']['current_independent_origins']),2)
                if key=='M':self.assertEqual(r['clusters'][0]['late_factory_cost_class'],'HIGH')
                if key=='L':self.assertEqual(r['clusters'][0]['late_factory_cost_class'],'UNKNOWN')
                self.assertEqual(r['deep_shelf_calls'],0)

    def test_scale_without_deep_objects_or_owner_flood(self):
        r=wide.screen(REAL/'tests/fixtures/wide-screener-v1/scale-1000.json')
        self.assertEqual([r['counts'][k] for k in ('raw','normalized','corroborated','quick_screen','kill','park','investigate')],[1000,200,40,40,180,10,10])
        self.assertEqual(len(r['owner_items']),5);self.assertEqual(r['deep_shelf_calls'],0)

    def test_llm_ideas_cannot_corroborate(self):
        self.readable()
        for s in self.packet['signals']:s['provenance']['kind']='LLM_QUERY_EXPANSION';s['source_family']='LLM_EXPANSION';s['job_support']='UNKNOWN'
        c=wide.screen(self.path())['clusters'][0];self.assertEqual(c['decision'],'PARK');self.assertEqual(c['corroboration']['status'],'UNKNOWN')

    def test_same_ecosystem_pages_are_one_origin(self):
        self.readable();self.packet['evidence'][1]['source_uri']='https://publisher.example/another'
        self.packet['signals'][1]['source']=self.packet['evidence'][1]['source_uri']
        c=wide.screen(self.path())['clusters'][0];self.assertEqual(c['corroboration']['status'],'WEAK');self.assertEqual(c['decision'],'PARK')

    def test_freshness_is_source_specific(self):
        self.readable()
        for s in self.packet['signals']:s['freshness']['source_date']='2026-05-01'
        c=wide.screen(self.path())['clusters'][0];self.assertEqual(c['corroboration']['status'],'WEAK')

    def test_future_date_and_hash_drift_fail_closed(self):
        self.packet['signals'][0]['freshness']['source_date']='2027-01-01'
        with self.assertRaises(Exception):wide.check(self.path())
        self.packet['signals'][0]['freshness']['source_date']='2026-10-02';(self.base/'raw.txt').write_text('changed')
        with self.assertRaises(Exception):wide.screen(self.path())

    def test_feature_without_observation_rejected(self):
        self.quick()['features']['activity']['observation_ids']=['invented']
        with self.assertRaises(Exception):wide.check(self.path())

    def test_cross_language_feature_rejected(self):
        self.quick()['language']='FR'
        with self.assertRaises(Exception):wide.screen(self.path())

    def test_unknown_cost_and_zero_denominator_not_zero_filled(self):
        r=wide.screen(self.path());self.assertIsNone(r['costs']['cost_per_kill_usd']);self.assertIsNone(r['costs']['cost_per_investigate_usd'])
        self.assertIsNone(r['clusters'][0]['kill_record']['owner_attention_to_kill_minutes'])

    def test_breadth_cap_parks_synonym_disguised_subjects(self):
        p=json.loads((REAL/'tests/fixtures/wide-screener-v1/scale-1000.json').read_text())
        for s in p['signals']:s['buyer_job']['subject']='one fashionable domain'
        target=self.base/'raw.txt';target.write_bytes((REAL/'tests/fixtures/wide-screener-v1/raw.txt').read_bytes())
        self.packet=p;r=wide.screen(self.path());self.assertEqual(r['counts']['investigate'],2)

    def test_stable_identity_previous_run_no_history_rewrite(self):
        self.quick();path=self.path();r=wide.screen(path);previous=self.base/'run.json';previous.write_text(json.dumps(r));before=previous.read_bytes()
        r2=wide.screen(path,previous);self.assertEqual(r2['counts']['new_jobs'],0);self.assertEqual(r2['counts']['updated_jobs'],1);self.assertEqual(previous.read_bytes(),before)

    def test_park_or_kill_cannot_handoff(self):
        r=wide.screen(self.path())
        with self.assertRaises(Exception):wide.handoff(r,r['clusters'][0]['cluster_id'])

    def test_no_implicit_language_mirroring(self):
        self.quick();r=wide.screen(self.path());self.assertEqual(len(r['clusters']),1);self.assertEqual(r['clusters'][0]['language'],'EN')

    def test_optional_deep_fields_not_required(self):
        self.quick();r=wide.screen(self.path());self.assertEqual(r['clusters'][0]['decision'],'INVESTIGATE')

    def test_rights_and_fast_window_gate_before_queue(self):
        q=self.quick();q['rights']='BLOCK';self.assertEqual(wide.screen(self.path())['clusters'][0]['decision_reason'],'RIGHTS_PLATFORM_OBVIOUS_BLOCK')

    def test_sponsored_without_organic_killed(self):
        q=self.quick(sponsored='PRESENT');q['organic_depth_reached']=0;self.assertEqual(wide.screen(self.path())['clusters'][0]['decision_reason'],'SPONSORED_DOMINATED_WITHOUT_ORGANIC_EVIDENCE')

    def test_invalid_evidence_paths_and_duplicate_ids_fail(self):
        self.packet['evidence'][0]['path']='../raw.txt'
        with self.assertRaises(Exception):wide.check(self.path())
        self.packet['evidence'][0]['path']='raw.txt';self.packet['signals'].append(copy.deepcopy(self.packet['signals'][0]))
        with self.assertRaises(Exception):wide.check(self.path())

    def test_cli_actions_and_live_option_rejected(self):
        import io
        from contextlib import redirect_stdout,redirect_stderr
        from abvx_harness.__main__ import main
        with redirect_stdout(io.StringIO()) as output:self.assertEqual(main(['book-radar','wide','screen',str(self.path()),'--json']),0)
        self.assertFalse(json.loads(output.getvalue())['live_collection'])
        with redirect_stderr(io.StringIO()):self.assertEqual(main(['book-radar','wide','screen',str(self.path()),'--live','true']),1)

    def test_no_support_annotation_cannot_corroborate(self):
        self.readable()
        for s in self.packet['signals']:s.pop('job_support',None)
        self.assertEqual(wide.screen(self.path())['clusters'][0]['corroboration']['status'],'UNKNOWN')

    def test_contradictory_current_job_evidence_parks(self):
        self.readable();self.packet['signals'][1]['job_support']='CONTRADICTS'
        c=wide.screen(self.path())['clusters'][0];self.assertEqual(c['corroboration']['status'],'CONTRADICTED');self.assertEqual(c['decision'],'PARK')

    def test_partial_negative_sample_parks(self):
        self.quick(activity='ABSENT')['sample_complete']=False
        self.assertEqual(wide.screen(self.path())['clusters'][0]['decision_reason'],'PARK_NEEDS_WIDER_SAMPLE')

    def test_fake_report_promotion_cannot_handoff(self):
        r=wide.screen(self.path());r['clusters'][0]['decision']='INVESTIGATE';p=self.base/'run.json';p.write_text(json.dumps(r))
        with self.assertRaises(Exception):wide.handoff(p,r['clusters'][0]['cluster_id'])

    def test_budget_overflow_fails_without_mutation(self):
        self.packet['policy']={'limits':{'max_raw':1}};self.readable()
        with self.assertRaises(Exception):wide.screen(self.path())

    def test_amazon_pages_are_one_marketplace_origin(self):
        self.readable()
        for i,s in enumerate(self.packet['signals']):
            uri='https://www.amazon.com/'+('search' if i==0 else 'category');self.packet['evidence'][i]['source_uri']=uri;s['source']=uri
        c=wide.screen(self.path())['clusters'][0];self.assertEqual(c['evidence_origins'],['amazon']);self.assertEqual(c['decision'],'PARK')

    def test_synthetic_result_cannot_relabel_as_retained(self):
        self.quick();r=wide.screen(self.path());r['origin']='RETAINED';p=self.base/'run.json';p.write_text(json.dumps(r))
        with self.assertRaises(Exception):wide.read_run(p)

    def test_changed_input_fails_report(self):
        self.quick();r=wide.screen(self.path());p=self.base/'run.json';p.write_text(json.dumps(r));self.packet['run_id']='changed';self.path()
        with self.assertRaises(Exception):wide.read_run(p)

    def test_mutated_saved_audience_cannot_forge_handoff(self):
        self.quick();r=wide.screen(self.path());r['clusters'][0]['audience']='invented buyer';p=self.base/'run.json';p.write_text(json.dumps(r))
        with self.assertRaises(Exception):wide.handoff(p,r['clusters'][0]['cluster_id'])
