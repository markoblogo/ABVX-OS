"""Synthetic isolated tests. No browser, credential, network or production state."""
import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest

from abvx_harness import youtube as y

VIDEO = 'AAAAAAAAAAA'
CLOCK = datetime(2026, 10, 19, 19, 0, tzinfo=timezone.utc)


def packet():
    return {'schema_version': 'youtube-research/v1', 'as_of': '2026-10-19',
            'status': 'COMPLETE', 'research_seconds': 20, 'method_version': 'synthetic/v1',
            'limitations': ['Synthetic fixture, not real research'], 'opportunities': []}


def experiment():
    return {'schema_version': 'youtube-experiment/v1', 'id': 'test-experiment',
            'created_at': CLOCK.isoformat(), 'topic': 'synthetic topic', 'format': 'HORIZONTAL_SHORT',
            'hypothesis': 'A result-first clip obtains the registered number of views.',
            'expected_response': 'Views at or above a prespecified threshold',
            'sources': [{'url': 'https://example.org/source', 'checked_at': CLOCK.isoformat(), 'supports': 'Synthetic fixture'}],
            'primary_metric': 'views', 'window_days': 7, 'minimum_result': 5,
            'threshold_basis': 'Synthetic test threshold, not a calibrated recommendation'}


def video(vid=VIDEO, published='2026-10-10T12:00:00Z', privacy='public'):
    return {'id': vid, 'snippet': {'title': 'Synthetic upload', 'publishedAt': published,
                                 'liveBroadcastContent': 'none'},
            'status': {'privacyStatus': privacy}, 'contentDetails': {'duration': 'PT35S'},
            'statistics': {'viewCount': '100'}}


class Credentials:
    def has_scopes(self, scopes):
        return False


class API:
    credentials = Credentials()
    def __init__(self, videos=None, pages=None):
        self.calls = 0
        self.invocations = []
        self.videos = videos or [video()]
        self.pages = pages
    def call(self, resource, **params):
        self.calls += 1
        self.invocations.append((resource, params))
        if resource == 'channels':
            return {'items': [{'id': y.config()['channel_id'], 'contentDetails': {'relatedPlaylists': {'uploads': 'UU_test'}}}]}
        if resource == 'playlistItems':
            if self.pages:
                return self.pages[1 if params.get('pageToken') else 0]
            return {'items': [{'contentDetails': {'videoId': v['id']}} for v in self.videos]}
        if resource == 'videos':
            return {'items': [v for v in self.videos if v['id'] in params['id'].split(',')]}
        if resource == 'analytics':
            if params['dimensions'] == 'day' and 'filters' not in params:
                names = ['day'] + params['metrics'].split(',')
                row = [params['startDate']] + [1 for _ in names[1:]]
                return {'columnHeaders': [{'name': n} for n in names], 'rows': [row]}
            return {'columnHeaders': [{'name': n} for n in params['dimensions'].split(',') + params['metrics'].split(',')], 'rows': []}
        raise AssertionError('Unexpected or mutating API operation')


class YouTubeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
    def tearDown(self):
        self.temp.cleanup()
    def acquire(self, api):
        return y.acquire(api, y.config(), CLOCK.date() - timedelta(days=3), CLOCK)
    def test_config_and_schema(self):
        self.assertEqual(y.config()['editorial_guideline'], {'PROVEN': .4, 'EMERGING': .4, 'CREATIVE': .2})
    def test_all_upload_pages_and_spontaneous_analysis(self):
        pages = [{'items': [{'contentDetails': {'videoId': VIDEO}}], 'nextPageToken': 'two'},
                 {'items': [{'contentDetails': {'videoId': 'BBBBBBBBBBB'}}]}]
        api = API([video(), video('BBBBBBBBBBB')], pages)
        acquired = self.acquire(api)
        rows = y.analyze(acquired, self.root)
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(r['hypothesis_status'] == 'OBSERVATIONAL_ONLY' for r in rows))
        self.assertTrue(all(r['availability'] == 'NO_REPORTED_ROWS' for r in rows))
        self.assertEqual(len([p for r, p in api.invocations if r == 'playlistItems']), 2)
    def test_identity_mismatch_fails_before_other_reads(self):
        api = API()
        original = api.call
        def call(resource, **params):
            if resource == 'channels': return {'items': [{'id': 'wrong'}]}
            return original(resource, **params)
        api.call = call
        with self.assertRaisesRegex(ValueError, 'CHANNEL_ID_MISMATCH'): self.acquire(api)
    def test_new_upload_discovery_does_not_make_hypotheses(self):
        acquired=self.acquire(API())
        first=self.root/'runs'/'first';first.mkdir(parents=True)
        y._write_once(first/'acquisition.json',acquired)
        current=self.acquire(API([video(),video('BBBBBBBBBBB')]))
        rows=y.analyze(current,self.root,'second')
        self.assertEqual(rows[0]['discovery_status'],'PREVIOUSLY_SEEN')
        self.assertEqual(rows[1]['discovery_status'],'NEWLY_DISCOVERED')
        self.assertIsNone(rows[1]['experiment_id'])
    def test_actual_api_content_type_aliases(self):
        acquired=self.acquire(API([video(),video('BBBBBBBBBBB')]))
        acquired['reports'].append({'label':'videos_28d','rows':[
            {'video':VIDEO,'creatorContentType':'shorts','views':1},
            {'video':'BBBBBBBBBBB','creatorContentType':'videoOnDemand','views':1}]})
        rows=y.analyze(acquired,self.root)
        self.assertEqual(rows[0]['format_group'],'SHORT')
        self.assertEqual(rows[1]['format_group'],'REGULAR_UNDER_3_MIN')
    def test_empty_channel_data_not_accepted_for_scheduling(self):
        api=API(); original=api.call
        def call(resource,**params):
            result=original(resource,**params)
            if resource=='analytics':result['rows']=[]
            return result
        api.call=call
        self.assertEqual(y.run(self.root,'empty',packet(),api,CLOCK)['status'],'PARTIAL_DATA')
    def test_private_and_future_excluded(self):
        api = API([video(privacy='private'), video('BBBBBBBBBBB', published='2027-01-01T00:00:00Z')])
        self.assertEqual(y.analyze(self.acquire(api), self.root), [])
    def test_repeated_page_token_rejected(self):
        api = API(pages=[{'nextPageToken': 'same'}, {'nextPageToken': 'same'}])
        with self.assertRaisesRegex(ValueError, 'Repeated'): self.acquire(api)
    def test_reports_keep_sources_and_requested_periods(self):
        acquired = self.acquire(API())
        self.assertEqual(acquired['discovery'], 'COMPLETE')
        self.assertEqual(acquired['revenue']['availability'], 'SCOPE_NOT_GRANTED')
        self.assertTrue(all('response' in r and 'requested_period' in r for r in acquired['reports']))
        self.assertTrue(any(r['label'] == 'age_7d:' + VIDEO for r in acquired['reports']))
    def test_malformed_table_rejected(self):
        with self.assertRaises(ValueError): y.table({'columnHeaders': [{'name': 'views'}], 'rows': [[1,2]]})
    def test_research_cost_and_no_opportunity_count_cap(self):
        p = packet(); p['research_seconds'] = 2701
        with self.assertRaises(ValueError): y.research(p, y.config())
        card = {k: 'Synthetic' for k in ['id','title','concept','rationale','duration','hook','visual','production','hypothesis','primary_metric']}
        card.update(priority=1,lane='CREATIVE',format='SHORT',complexity='LOW',sources=experiment()['sources'])
        p = packet(); p['opportunities'] = [dict(card, id=f'c{i}') for i in range(101)]
        self.assertEqual(len(y.research(p,y.config())['opportunities']),101)
    def test_editorial_mix_does_not_require_quota(self):
        self.assertEqual(y.editorial_mix([])['actual_counts']['PROVEN'],0)
    def test_duplicate_opportunity_rejected(self):
        card = {k: 'Synthetic' for k in ['id','title','concept','rationale','duration','hook','visual','production','hypothesis','primary_metric']}
        card.update(priority=1,lane='PROVEN',format='SHORT',complexity='LOW',sources=experiment()['sources'])
        p=packet();p['opportunities']=[card,card]
        with self.assertRaises(ValueError):y.research(p,y.config())
    def test_prospective_freeze_and_late_binding_rejected(self):
        y.register(self.root,experiment(),CLOCK)
        y.change(self.root,{'type':'APPROVED','experiment_id':'test-experiment'})
        p=self.root/'runs'/'source';p.mkdir(parents=True)
        y._write_once(p/'acquisition.json',{'catalog':[{'video_id':VIDEO,'published_at':'2026-10-10T12:00:00Z'}]})
        with self.assertRaisesRegex(ValueError,'RETROSPECTIVE'):
            y.change(self.root,{'type':'PUBLISHED','experiment_id':'test-experiment','video_id':VIDEO})
    def test_no_manual_evaluated_claim(self):
        y.register(self.root,experiment(),CLOCK)
        with self.assertRaisesRegex(ValueError,'generated'):
            y.change(self.root,{'type':'EVALUATED','experiment_id':'test-experiment','video_id':VIDEO,'evidence_run':'x','assessment':{}})
    def test_approval_required(self):
        y.register(self.root,experiment(),CLOCK)
        with self.assertRaisesRegex(ValueError,'prior approval'):
            y.change(self.root,{'type':'PUBLISHED','experiment_id':'test-experiment','video_id':VIDEO})
    def test_lock_excludes_concurrent_writer(self):
        with y.lock(self.root):
            with self.assertRaisesRegex(ValueError,'writer.lock'):
                with y.lock(self.root): pass
    def test_complete_synthetic_run_and_no_overwrite(self):
        result=y.run(self.root,'synthetic',packet(),API(),CLOCK)
        self.assertEqual(result['status'],'COMPLETE')
        self.assertTrue(Path(result['report']).is_file())
        with self.assertRaisesRegex(ValueError,'already exists'):
            y.run(self.root,'synthetic',packet(),API(),CLOCK)
    def test_failure_has_receipt_and_no_sensitive_body(self):
        api=API();api.call=lambda *a,**kw: (_ for _ in ()).throw(RuntimeError('private-access-token'))
        with self.assertRaises(RuntimeError):y.run(self.root,'failed',packet(),api,CLOCK)
        text=(self.root/'runs/failed/execution.json').read_text()
        self.assertNotIn('private-access-token',text)
        self.assertEqual(json.loads(text)['status'],'BLOCKED')
    def test_freshness_no_history_as_live(self):
        p=packet();p['as_of']='2026-10-18'
        with self.assertRaisesRegex(ValueError,'Fresh research'):y.run(self.root,'old',p,API(),CLOCK)
    def test_incomplete_window_is_unknown_then_evaluates(self):
        y.register(self.root,experiment(),CLOCK)
        y.event(self.root,{'type':'PUBLISHED','experiment_id':'test-experiment','video_id':VIDEO})
        r={'label':'age_7d:'+VIDEO,'requested_period':{'start':'2026-10-01','end':'2026-10-07'},
           'rows':[{'day':'2026-10-01','views':20}]}
        self.assertEqual(y.evaluate({'reports':[r]},self.root,'one')[0]['status'],'IMMATURE_OR_UNAVAILABLE')
        r['rows']=[{'day':f'2026-10-0{i}','views':1} for i in range(1,8)]
        self.assertEqual(y.evaluate({'reports':[r]},self.root,'two')[0]['status'],'SUPPORTED')
        count=len(y.events(self.root)); y.evaluate({'reports':[r]},self.root,'two')
        self.assertEqual(len(y.events(self.root)),count)
    def test_import_supplementary_not_api(self):
        proof=self.root/'export.csv';proof.write_text('impressions_ctr,7.6\n')
        p={'schema_version':'youtube-studio-import/v1','channel_id':y.config()['channel_id'],
           'captured_at':CLOCK.isoformat(),'source_kind':'STUDIO_EXPORT',
           'metrics':[{'metric':'impressions_ctr','value':7.6,'unit':'PERCENT','video_id':None,
                      'definition':'Studio thumbnail CTR','period':{'start':'2026-09-21','end':'2026-10-18'}}]}
        self.assertEqual(y.import_studio(self.root,p,proof)['status'],'IMPORTED_SUPPLEMENTARY')
        self.assertEqual(list((self.root/'runs').glob('*')),[])


if __name__ == '__main__':
    unittest.main()
