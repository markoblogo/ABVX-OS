"""Research routing tests; synthetic data never establishes market success."""
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stdout
import test_book_radar_wide as wide_fixtures
from abvx_harness import book_radar_wide as wide
from abvx_harness.harness import ValidationError
from abvx_harness.__main__ import main

class BookShortlistTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)

    def run_file(self,name,day='2026-11-02',*,lane='EXPLORATION',cross=False,phrase='SYNTHETIC fact',language='FR',kill=False):
        fixture=wide_fixtures.WideTests();fixture.setUp();self.addCleanup(fixture.tmp.cleanup)
        fixture.quick(activity='ABSENT' if kill else 'PRESENT')
        packet=copy.deepcopy(fixture.packet);packet.update(run_id=name,as_of=day+'T12:00:00Z')
        for e in packet['evidence']:e['language']=language
        for signal in packet['signals']:
            signal.update(observed_at=day+'T10:00:00Z',language=language,raw_phrase=phrase)
            signal['freshness']={'source_date':day,'date_basis':'CAPTURE'}
            if cross:signal['source_family']='CROSS_MARKET'
            elif lane=='EXPLOITATION' and signal['signal_id']=='s2':signal['source_family']='PORTFOLIO_ADJACENCY'
        cid=wide.cluster_id(packet['signals'][0]['buyer_job'],'Amazon.com',language)
        for q in packet['quick_screens']:q.update(cluster_id=cid,language=language,observed_at=day+'T10:00:00Z')
        base=self.root/name;base.mkdir();(base/'raw.txt').write_bytes((fixture.base/'raw.txt').read_bytes())
        source=base/'input.json';source.write_text(json.dumps(packet));run=base/'run.json';run.write_text(json.dumps(wide.screen(source)))
        return run

    def test_early_discovery_survives_validation_deferral_without_promotion(self):
        run=self.run_file('one-origin')
        source=run.parent/'input.json';packet=json.loads(source.read_text())
        packet['signals']=packet['signals'][:1];packet['quick_screens']=[]
        source.write_text(json.dumps(packet));run.write_text(json.dumps(wide.screen(source)))
        result=wide.book_shortlist(run,minutes=1)
        self.assertEqual(result['book_research_shortlist'],[])
        self.assertEqual(len(result['discovery_pool']),1)
        row=result['discovery_pool'][0]
        self.assertEqual(row['status'],'DISCOVERY')
        self.assertEqual(row['historical_decision'],'PARK')
        self.assertEqual(row['validation_status'],'DEFERRED')
        self.assertFalse(row['production_authorized'])
        self.assertFalse(result['production_authorized'])

    def test_editorial_menu_is_hashed_research_only_and_expires(self):
        import hashlib
        run=self.run_file('editorial')
        folder=self.root/'book-radar';folder.mkdir()
        menu={'as_of':'2026-11-02','production_authorized':False,'top_owner_review':['p1'],
              'cards':[{'id':'p1','status':'READY FOR OWNER REVIEW','production_authorized':False}]}
        source=folder/'menu.json'
        manifest={'run':str(run.relative_to(self.root)),
                  'editorial_menu':{'path':'book-radar/menu.json','sha256':''}}
        def save_menu():
            source.write_text(json.dumps(menu));manifest['editorial_menu']['sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
            (folder/'discovery-review.json').write_text(json.dumps(manifest))
        save_menu()
        current=wide.weekly_book_review(self.root,'2026-11-02')
        self.assertEqual(current['owner_production_review_candidates'],[])  # Legacy menu lacks content checks.
        self.assertEqual(current['book_opportunity_menu']['freshness'],'CURRENT_RESEARCH_ONLY')
        stale=wide.weekly_book_review(self.root,'2026-11-09')
        self.assertEqual(stale['owner_production_review_candidates'],[])
        self.assertEqual(stale['book_opportunity_menu']['freshness'],'REFRESH_REQUIRED')
        source.write_text('changed')
        with self.assertRaises(ValidationError):wide.weekly_book_review(self.root,'2026-11-02')
        menu['production_authorized']=True;save_menu()
        with self.assertRaises(ValidationError):wide.weekly_book_review(self.root,'2026-11-02')

    def test_non_english_language_can_be_researched_without_test_promotion(self):
        run=self.run_file('minority',language='BR-FR')
        result=wide.book_shortlist(run)
        self.assertEqual(result['book_research_shortlist'][0]['language'],'BR-FR')
        self.assertTrue(all(r['status']=='RESEARCH' for r in result['book_research_shortlist']))
        self.assertFalse(result['automatic_test_promotion'])

    def test_capture_date_and_replayed_run_do_not_create_new_signal(self):
        first=self.run_file('first');next_run=self.run_file('next','2026-11-09')
        result=wide.book_shortlist(next_run,[first,first])
        self.assertEqual(result['book_research_shortlist'],[])
        self.assertEqual(result['deferred'][0]['reason'],'REPEAT_NO_NEW_SIGNAL')
        self.assertEqual(result['method_review']['retained_runs'],2)

    def test_changed_fact_can_reopen_research_without_erasing_history(self):
        old=self.run_file('old');new=self.run_file('new','2026-11-09',phrase='SYNTHETIC changed price 12')
        before=old.read_bytes();result=wide.book_shortlist(new,[old])
        self.assertEqual(result['book_research_shortlist'][0]['novelty'],'NEW_SOURCE_FACT')
        self.assertEqual(old.read_bytes(),before)
        self.assertEqual(len(result['decision_history']),2)

    def test_historical_kill_requires_explicit_review(self):
        old=self.run_file('killed',kill=True);new=self.run_file('changed','2026-11-09',phrase='new fact')
        result=wide.book_shortlist(new,[old])
        self.assertEqual(result['book_research_shortlist'],[])
        self.assertEqual(result['deferred'][0]['reason'],'HISTORICAL_KILL_REVIEW')

    def test_cross_market_signal_is_a_seed_not_book_shortlist(self):
        result=wide.book_shortlist(self.run_file('etsy',cross=True))
        self.assertEqual(result['book_research_shortlist'],[])
        self.assertEqual(result['cross_market_seeds'][0]['status'],'SEED_ONLY')

    def test_lane_budget_is_research_attention_not_book_quota(self):
        run=self.run_file('adjacent',lane='EXPLOITATION')
        result=wide.book_shortlist(run,minutes=40,exploration_share=.6)
        self.assertEqual(result['book_research_shortlist'],[])
        self.assertEqual(result['deferred'][0]['reason'],'LANE_RESEARCH_BUDGET')
        result=wide.book_shortlist(run,minutes=50,exploration_share=.6)
        self.assertEqual(result['budget']['selected_minutes']['EXPLOITATION'],20)
        self.assertFalse(result['production_authorized'])

    def test_14_and_21_day_review_does_not_claim_sales_or_costs(self):
        run=self.run_file('baseline')
        for day,stage in [('2026-11-15','NOT_DUE'),('2026-11-16','D14'),('2026-11-23','D21')]:
            result=wide.book_shortlist(run,as_of=day)
            self.assertEqual(result['method_review']['stage'],stage)
            self.assertEqual(result['method_review']['actual_research_minutes'],'UNKNOWN')
            self.assertEqual(result['method_review']['test_candidates'],'UNKNOWN_NOT_ASSESSED_BY_WIDE')
        expired=wide.book_shortlist(run,as_of='2028-01-02')
        self.assertEqual(expired['book_research_shortlist'],[])
        self.assertEqual(expired['deferred'][0]['reason'],'NO_CURRENT_SOURCE')

    def test_manifest_and_cli_reuse_retained_runs_without_writing_state(self):
        run=self.run_file('manifest')
        folder=self.root/'book-radar';folder.mkdir()
        (folder/'discovery-review.json').write_text(json.dumps({'run':str(run.relative_to(self.root)),'baseline_date':'2026-11-02'}))
        result=wide.weekly_book_review(self.root,'2026-11-16')
        self.assertEqual(result['method_review']['stage'],'D14')
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(['book-radar','wide','shortlist',str(run),'--json']),0)
        self.assertFalse(json.loads(output.getvalue())['canonical_state_written'])
        self.assertFalse((folder/'state.json').exists())

    def test_future_history_and_escaping_manifest_are_rejected(self):
        early=self.run_file('early');later=self.run_file('future','2026-11-09')
        with self.assertRaises(ValidationError):wide.book_shortlist(early,[later],as_of='2026-11-02')
        folder=self.root/'book-radar';folder.mkdir()
        (folder/'discovery-review.json').write_text(json.dumps({'run':'../outside.json'}))
        with self.assertRaises(ValidationError):wide.weekly_book_review(self.root,'2026-11-02')

    def test_human_aliases_merge_semantic_jobs_before_shortlisting(self):
        run=self.run_file('aliases');source=run.parent/'input.json';packet=json.loads(source.read_text())
        job=packet['signals'][0]['buyer_job']['job'];packet['signals'][1]['buyer_job']['job']='a reviewed equivalent paraphrase'
        packet['aliases']={'a reviewed equivalent paraphrase':job}
        source.write_text(json.dumps(packet));run.write_text(json.dumps(wide.screen(source)))
        self.assertEqual(len(wide.book_shortlist(run)['book_research_shortlist']),1)

    def test_existing_weekly_entrypoint_attaches_method_review(self):
        import argparse
        import importlib.util
        import hashlib
        from unittest.mock import patch
        import test_book_radar_learning as learning_fixtures
        from abvx_harness import book_radar_markets as markets
        fixture=learning_fixtures.LearningTests();fixture.setUp();self.addCleanup(fixture.tmp.cleanup)
        source=fixture.run_fixture('weekly-source',day='2026-11-02')
        proof=source/'proof.json';sha=hashlib.sha256(proof.read_bytes()).hexdigest()
        receipt={'attempts':[dict(marketplace=m,status='AVAILABLE' if m=='udemy' else 'ACCESS_FAILED',
             source_url='https://www.udemy.com/course/synthetic/' if m=='udemy' else 'https://example.org/'+m,
             evidence_ref=proof.name,evidence_sha256=sha,captured_at_utc='2026-11-02T12:00:00Z',
             method='LIVE_BROWSER',blocker='SYNTHETIC no live source') for m in markets.MARKETS]}
        acquisition=source/'acquisition.json';acquisition.write_text(json.dumps(receipt))
        run=self.run_file('weekly-book');folder=self.root/'book-radar';folder.mkdir()
        (folder/'discovery-review.json').write_text(json.dumps({'run':str(run.relative_to(self.root)),'baseline_date':'2026-11-02'}))
        spec=importlib.util.spec_from_file_location('weekly_books_entry',Path(__file__).parents[1]/'scripts/run_multi_market_radar.py')
        entry=importlib.util.module_from_spec(spec);spec.loader.exec_module(entry)
        args=argparse.Namespace(input=source/'input.json',acquisition=acquisition,ranking=None,
                               run_id='synthetic-book-review',as_of='2026-11-02',hours=4,history=self.root/'learning')
        with patch.object(entry,'REPO',self.root):result=entry.run(args)
        menu=json.loads((Path(result['output'])/'weekly.json').read_text())
        self.assertEqual(menu['book_discovery']['method_review']['day14'],'2026-11-16')
        self.assertFalse(menu['book_discovery']['production_authorized'])
        self.assertTrue((Path(result['output'])/'book-discovery.json').is_file())
        self.assertFalse((folder/'state.json').exists())

    def test_reviewed_canonical_repeat_is_not_counted_as_new(self):
        from unittest.mock import patch
        run=self.run_file('canonical')
        cid=json.loads(run.read_text())['clusters'][0]['cluster_id']
        state={'opportunities':[{'id':'OLD-1'}], 'decisions':[{'id':'decision-old','opportunity_id':'OLD-1','decision':'REJECT'}]}
        with patch('abvx_harness.book_radar.load_state',return_value=state):
            result=wide.book_shortlist(run,canonical_root=self.root,hypothesis_links={cid:['OLD-1']})
        self.assertEqual(result['book_research_shortlist'],[])
        self.assertEqual(result['deferred'][0]['novelty'],'RETAINED_THESIS_NEW_CONTEXT')
        self.assertEqual(result['method_review']['new_hypotheses_since_baseline'],0)
        self.assertEqual(state['decisions'][0]['decision'],'REJECT')

    def test_evidence_bound_hold_is_retained_but_cannot_promote_test(self):
        run=self.run_file('review')
        cluster=json.loads(run.read_text())['clusters'][0]
        review={'cluster_id':cluster['cluster_id'],'status':'HOLD','reason':'SYNTHETIC served already',
                'main_missing_fact':'Distinct reader need','next_action':'Check one independent reader request',
                'evidence_ids':cluster['decision_evidence']}
        result=wide.book_shortlist(run,reviews=[review])
        self.assertEqual(result['book_research_shortlist'],[])
        self.assertEqual(result['deferred'][0]['main_missing_fact'],'Distinct reader need')
        review['status']='TEST'
        with self.assertRaises(ValidationError):wide.book_shortlist(run,reviews=[review])
        review['status']='HOLD';review['evidence_ids']=['unresolved']
        with self.assertRaises(ValidationError):wide.book_shortlist(run,reviews=[review])

    def test_weekly_replay_requests_acquisition_instead_of_calling_old_leads_new(self):
        run=self.run_file('yesterday')
        result=wide.book_shortlist(run,as_of='2026-11-09')
        self.assertFalse(result['current_acquisition'])
        self.assertEqual(result['owner_research_recommendations'],[])
        self.assertEqual(result['deferred'][0]['reason'],'ACQUISITION_REQUIRED_FOR_THIS_RUN')

    def test_advancing_weekly_pointer_cannot_reset_baseline_history(self):
        first=self.run_file('baseline-history');new=self.run_file('week-two','2026-11-09')
        with self.assertRaises(ValidationError):
            wide.book_shortlist(new,baseline_date='2026-11-02')
        result=wide.book_shortlist(new,[first],baseline_date='2026-11-02')
        self.assertEqual(result['method_review']['repeat_occurrences'],1)
        self.assertEqual(result['owner_research_recommendations'],[])

    def test_tracking_links_do_not_create_new_evidence(self):
        first=self.run_file('tracked-first');new=self.run_file('tracked-new','2026-11-09')
        source=new.parent/'input.json';packet=json.loads(source.read_text())
        for e in packet['evidence']:e['source_uri']+='?utm_source=changed&qid=123'
        for s in packet['signals']:s['source']+='?utm_source=changed&qid=123'
        source.write_text(json.dumps(packet));new.write_text(json.dumps(wide.screen(source)))
        result=wide.book_shortlist(new,[first])
        self.assertEqual(result['book_research_shortlist'],[])
        self.assertEqual(result['deferred'][0]['reason'],'REPEAT_NO_NEW_SIGNAL')

    def test_review_cannot_inject_production_authority(self):
        run=self.run_file('authority');cluster=json.loads(run.read_text())['clusters'][0]
        review={'cluster_id':cluster['cluster_id'],'status':'HOLD','reason':'SYNTHETIC',
                'main_missing_fact':'Distinct need','next_action':'Check request',
                'evidence_ids':cluster['decision_evidence'],'production_authorized':True}
        with self.assertRaises(ValidationError):wide.book_shortlist(run,reviews=[review])

    def test_canonical_links_survive_when_thesis_is_only_in_history(self):
        from unittest.mock import patch
        first=self.run_file('linked-baseline')
        new=self.run_file('different-current','2026-11-09',language='BR-FR')
        old_cid=json.loads(first.read_text())['clusters'][0]['cluster_id']
        state={'opportunities':[{'id':'OLD-1'}], 'decisions':[{'opportunity_id':'OLD-1','decision':'REJECT'}]}
        with patch('abvx_harness.book_radar.load_state',return_value=state):
            result=wide.book_shortlist(new,[first],baseline_date='2026-11-02',canonical_root=self.root,hypothesis_links={old_cid:['OLD-1']})
            self.assertEqual(result['method_review']['explicitly_linked_canonical_theses'],1)
            self.assertEqual(result['method_review']['new_hypotheses_since_baseline'],1)
            self.assertEqual(result['method_review']['distinct_hypotheses'],2)
            with self.assertRaises(ValidationError):
                wide.book_shortlist(new,[first],canonical_root=self.root,hypothesis_links={'unretained-thesis':['OLD-1']})
        self.assertEqual(state['decisions'][0]['decision'],'REJECT')
