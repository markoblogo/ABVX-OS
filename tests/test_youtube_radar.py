import copy
import csv
from datetime import date, timedelta
import tempfile
from pathlib import Path
import unittest
from abvx_harness import youtube as y
from abvx_harness.youtube_radar import studio_csv, financial_context, menu, research_request
from test_youtube_intelligence import API, CLOCK, VIDEO, experiment, packet

class RadarTests(unittest.TestCase):
    def test_csv_unknown_and_official_rpm_separate(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'a.csv'
            p.write_text('Контент,Название видео,Просмотры,Расчетный доход (EUR),Доход на тысячу просмотров (EUR)\n AAAAAAAAAAA,test,100,1,20\nBBBBBBBBBBB,test,,,\n')
            a,b=studio_csv(p,{'start':'2026-10-05','end':'2026-11-01'})
            self.assertEqual(a['official_rpm_eur'],20)
            self.assertEqual(a['derived_revenue_per_1000_views_eur'],10)
            self.assertEqual(a['format'],'UNKNOWN')
            self.assertIsNone(b['estimated_revenue_eur'])
            self.assertEqual(a['video_id'],VIDEO)
    def test_menu_no_filler_and_cap(self):
        p=packet(); self.assertEqual(menu(p)['shortfall'],10)
        p['opportunities']=[dict(title='topic '+str(i),priority=i) for i in range(25)]
        self.assertEqual(len(menu(p)['cards']),20)
        self.assertEqual(len(menu(p,False)['cards']),3)
        p['opportunities'] += [dict(title='TOPIC 0',priority=30)]
        self.assertEqual(len(menu(p)['cards']),20)
    def test_paris_week_request_no_scheduler(self):
        r=research_request(date(2026,11,2),{})
        self.assertEqual((r['week_start'],r['week_end']),('2026-11-02','2026-11-08'))
    def test_financial_join_preserves_period_and_unknowns(self):
        acq={'reports':[dict(label='video_revenue_28d',requested_period={'start':'2026-10-01','end':'2026-10-28'},rows=[dict(video=VIDEO,estimatedRevenue=1)])]}
        rows=[dict(video_id=v,format_group='UNKNOWN',hypothesis_status='OBSERVATIONAL_ONLY') for v in [VIDEO,'BBBBBBBBBBB']]
        a,b=financial_context(acq,rows)
        self.assertEqual(a['revenue_28d']['period']['start'],'2026-10-01')
        self.assertIsNone(a['official_rpm']);self.assertIsNone(b['revenue_28d'])
    def test_revenue_acquisition_optional_failures_do_not_erase_base(self):
        api=API(); api.credentials=type('Money',(),{'has_scopes':lambda *_:True})()
        original=api.call
        def call(resource,**params):
            if resource=='analytics' and params.get('dimensions')=='video' and 'estimatedRevenue' in params['metrics']:
                raise ValueError('GOOGLE_READ_FAILED: redacted')
            return original(resource,**params)
        api.call=call
        a=y.acquire(api,y.config(),CLOCK.date()-timedelta(days=3),CLOCK)
        self.assertTrue(a['revenue']['supplement_failures'])
        self.assertTrue(any(r['label']=='channel_28d' for r in a['reports']))
    def test_money_hypothesis_requires_full_age_days(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); ex=experiment();ex['primary_metric']='estimatedRevenue';ex['minimum_result']=1
            y.register(root,ex,CLOCK)
            y.event(root,dict(type='PUBLISHED',experiment_id=ex['id'],video_id=VIDEO))
            report=dict(label='revenue_age_7d:'+VIDEO,requested_period={'start':'2026-10-01','end':'2026-10-07'},rows=[dict(day=str(date(2026,10,1)+timedelta(days=i)),estimatedRevenue=.2) for i in range(7)])
            self.assertEqual(y.evaluate({'reports':[report]},root,'test')[0]['status'],'SUPPORTED')
            report['rows'].pop()
            self.assertEqual(y.evaluate({'reports':[report]},root,'test2')[0]['status'],'IMMATURE_OR_UNAVAILABLE')
    def test_studio_rpm_keeps_source_and_window(self):
        uploads=[dict(video_id=VIDEO,format_group='SHORT',hypothesis_status='OBSERVATIONAL_ONLY')]
        e={'evidence_sha256':'proof','packet':{'metrics':[dict(metric='rpm',video_id=VIDEO,value=2,period={'start':'2026-10-05','end':'2026-11-01'})]}}
        r=financial_context({'reports':[]},uploads,[e])[0]
        self.assertEqual(r['studio_rpm_observations'][0]['evidence_sha256'],'proof')
        self.assertIsNone(r['revenue_28d'])

    def test_unplanned_recent_upload_gets_age_revenue_without_winning_rank(self):
        api=API();api.credentials=type('Money',(),{'has_scopes':lambda *_:True})()
        a=y.acquire(api,y.config(),CLOCK.date()-timedelta(days=3),CLOCK)
        self.assertIn(VIDEO,a['revenue']['supplement_scope']['focus_ids'])
        self.assertTrue(any(r['label']=='revenue_age_7d:'+VIDEO for r in a['reports']))

    def test_channel_filter_and_semantic_key_reject_repeats(self):
        p={'opportunities':[
            dict(title='new phrasing',priority=1,selection=dict(niche_fit='PASS',novelty_status='REPEAT',novelty_key='same')),
            dict(title='new demand',priority=2,selection=dict(niche_fit='PASS',novelty_status='NEW_QUESTION',novelty_key='new')),
            dict(title='duplicate phrasing',priority=3,selection=dict(niche_fit='PASS',novelty_status='NEW_QUESTION',novelty_key='new')),
            dict(title='outside niche',priority=4,selection=dict(niche_fit='REJECT',novelty_status='NEW_QUESTION',novelty_key='other'))]}
        self.assertEqual([c['title'] for c in menu(p)['cards']],['new demand'])
    def test_developer_growth_is_not_acceleration_or_youtube_demand(self):
        from abvx_harness.youtube_radar import momentum
        points=[dict(entity='repo',metric='stars',observed_at=f'2026-11-02T{h}:00:00Z',value=v) for h,v in [('00',100),('12',120)]]
        r=momentum(points);self.assertEqual(r['per_day'],40)
        self.assertEqual(r['youtube_demand'],'UNPROVEN');self.assertEqual(r['acceleration'],'UNKNOWN')
        points[-1]['entity']='another'
        with self.assertRaises(ValueError):momentum(points)
    def test_secondary_views_pass_cannot_make_revenue_pass(self):
        from abvx_harness.youtube_radar import prediction_result,learning_review
        report=dict(label='age_7d:'+VIDEO,requested_period={'start':'2026-10-01','end':'2026-10-07'},rows=[dict(day=str(date(2026,10,1)+timedelta(days=i)),views=100) for i in range(7)])
        a={'reports':[report]}
        self.assertEqual(prediction_result(a,VIDEO,7,'views',500)['status'],'SUPPORTED')
        self.assertEqual(prediction_result(a,VIDEO,7,'estimatedRevenue',1)['status'],'IMMATURE_OR_UNAVAILABLE')
        review=learning_review([dict(experiment_id='one',video_id=VIDEO,status='SUPPORTED'),dict(experiment_id='two',video_id=VIDEO,status='NOT_SUPPORTED')])
        self.assertEqual(review['independent_uploads'],1)
        self.assertTrue(all(x['causal_status']=='UNPROVEN' for x in review['findings']))

    def test_radar_cannot_claim_complete_with_missing_monetary_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            p=packet();p['method_version']='youtube-radar/test'
            result=y.run(Path(td),'missing-money',p,api=API(),as_of=CLOCK)
            self.assertEqual(result['status'],'PARTIAL_DATA')
            self.assertTrue((Path(td)/'runs/missing-money/learning-review.json').exists())

    def test_nantes_handoff_hash_and_age_fencing(self):
        from abvx_harness.youtube_radar import nantes_packet
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);result=y.run(root,'handoff',packet(),api=API(),as_of=CLOCK)
            run=root/'runs/handoff'
            import json
            record=json.loads((run/'execution.json').read_text())
            clock=__import__('datetime').datetime.fromisoformat(record['captured_at'])
            p=nantes_packet(run,'weekly','real-lease',clock)
            self.assertEqual(p['token'],'real-lease');self.assertEqual(p['status'],'PARTIAL')
            self.assertEqual(p['failure_reason'],'MONETARY_DATA_UNAVAILABLE')
            self.assertEqual(nantes_packet(run,'daily','x',clock+timedelta(days=2))['status'],'PARTIAL')
            (run/'research.json').write_text('{}')
            with self.assertRaises(Exception):nantes_packet(run,'weekly','x',clock)
    def test_acquisition_checkpoint_keeps_real_responses(self):
        progress=[];api=API()
        y.acquire(api,y.config(),CLOCK.date()-timedelta(days=3),CLOCK,checkpoint=lambda p:progress.append(copy.deepcopy(p)))
        self.assertTrue(progress);self.assertEqual(progress[0]['status'],'IN_PROGRESS')
        self.assertEqual(progress[0]['catalog'][0]['video_id'],VIDEO)


class PartialResearchHandoffTest(unittest.TestCase):
    def test_partial_independent_research_cannot_inherit_complete_run(self):
        import json
        from datetime import datetime
        from abvx_harness.youtube_radar import nantes_packet
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);y.run(root,'override',packet(),api=API(),as_of=CLOCK);run=root/'runs/override'
            acquisition=json.loads((run/'acquisition.json').read_text());acquisition['revenue']['availability']='REPORTED';(run/'acquisition.json').write_text(json.dumps(acquisition))
            record=json.loads((run/'execution.json').read_text());record.update(status='COMPLETE',acquisition_digest=y.digest(acquisition));(run/'execution.json').write_text(json.dumps(record));clock=datetime.fromisoformat(record['captured_at'])
            revised=packet();revised.update(as_of=clock.date().isoformat(),status='PARTIAL');src=root/'partial.json';src.write_text(json.dumps(revised))
            self.assertEqual(nantes_packet(run,'weekly','fixture',clock)['status'],'COMPLETE')
            result=nantes_packet(run,'weekly','fixture',clock,src);self.assertEqual(result['status'],'PARTIAL');self.assertEqual(result['failure_reason'],'PARTIAL_RESEARCH')
