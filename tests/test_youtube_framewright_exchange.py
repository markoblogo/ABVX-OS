"""Framewright receiver tests use only synthetic local data."""
from pathlib import Path
import tempfile
import unittest
from abvx_harness import youtube_framewright_exchange as radar
from abvx_harness import framewright_wire as wire

class RadarReceiverTest(unittest.TestCase):
    def test_unknown_idea_waits_without_partial_link(self):
        with tempfile.TemporaryDirectory() as t:
            payload={'project_id':'framewright:fixture','radar_idea_id':'idea-1','research_revision':'a'*64,'idea_sha256':'b'*64,'selected_at':'2026-11-05T12:00:00+00:00','link_mode':'retrospective_observation','owner_approval':True,'timing_basis':'owner confirmed retrospective association'}
            msg=wire.message('association','framewright','framewright:fixture','a'*64,0,payload['selected_at'],payload)
            result=wire.receive(Path(t),'radar',msg,radar.apply_message)
            self.assertEqual(result['result'],'pending')
            self.assertNotIn('links',wire.state(Path(t),'radar')['data'])


class RadarFlowTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.idea={'id':'idea-1','title':'Question','question':'Why?','hypothesis':'A hypothesis','format':'horizontal','sources':[],'constraints':[]}
        s=wire.state(self.root,'radar');s['data']['menus']={'a'*64:{'packet_sha256':'a'*64,'as_of':'2026-11-05','ideas':[self.idea]}};wire.atomic(wire.directory(self.root,'radar')/'state.json',s)
    def link(self,project='framewright:fixture'):
        p={'project_id':project,'radar_idea_id':'idea-1','research_revision':'a'*64,'idea_sha256':wire.digest(self.idea),'selected_at':'2026-11-05T12:00:00+00:00','link_mode':'retrospective_observation','owner_approval':True,'timing_basis':'owner confirmed retrospective association'}
        row=wire.message('association','framewright',project,'a'*64,0,p['selected_at'],p)
        self.assertEqual(wire.receive(self.root,'radar',row,radar.apply_message)['result'],'applied');return row
    def status(self,project='framewright:fixture',seq=1,status='published',vid='abcdefghijk'):
        pubs=[dict(platform='youtube',video_id=vid,url='https://youtu.be/'+vid,output_id='final',receipt_id='e000001',provenance='owner_report',recorded_at='2026-11-05T12:00:00+00:00',master_sha256='b'*64)] if status=='published' else []
        p=dict(project_id=project,radar_idea_id='idea-1',research_revision='a'*64,source_journal_sha256='c'*64,status=status,outputs=[dict(id='final',sha256='b'*64,bytes=100,accepted=True)],publications=pubs)
        return wire.message('production_status','framewright',project,wire.digest(p),seq,'2026-11-05T12:00:00+00:00',p)
    def test_repeated_links_are_not_experiments(self):
        row=self.link();self.assertEqual(wire.receive(self.root,'radar',row,radar.apply_message)['result'],'duplicate')
        s=wire.state(self.root,'radar')['data'];self.assertEqual(len(s['links']),1);self.assertNotIn('experiments',s);self.assertNotIn('events',s)
    def test_video_cannot_be_bound_to_two_projects(self):
        self.link();self.link('framewright:other')
        self.assertEqual(wire.receive(self.root,'radar',self.status(),radar.apply_message)['result'],'applied')
        bad=wire.receive(self.root,'radar',self.status('framewright:other'),radar.apply_message)
        self.assertEqual(bad['result'],'rejected');self.assertNotIn('framewright:other',wire.state(self.root,'radar')['data']['production'])
    def test_old_status_cannot_rollback_current(self):
        self.link();wire.receive(self.root,'radar',self.status(seq=2),radar.apply_message)
        wire.receive(self.root,'radar',self.status(seq=1,status='ready_for_review'),radar.apply_message)
        self.assertEqual(wire.state(self.root,'radar')['data']['production']['framewright:fixture']['payload']['status'],'published')
    def test_same_revision_with_different_content_is_rejected(self):
        self.link();wire.receive(self.root,'radar',self.status(),radar.apply_message)
        self.assertEqual(wire.receive(self.root,'radar',self.status(status='accepted'),radar.apply_message)['result'],'rejected')
    def test_future_selected_mode_does_not_bypass_experiment_registration(self):
        row=self.link();self.assertEqual(row['payload']['link_mode'],'retrospective_observation')
        self.assertFalse((self.root/'experiments').exists());self.assertFalse((self.root/'events').exists())
    def test_existing_intake_is_referenced_unchanged(self):
        import json
        self.link();wire.receive(self.root,'radar',self.status(),radar.apply_message)
        src=self.root/'intake';src.mkdir();p=src/'prior.json';p.write_text(json.dumps({'id':'prior','status':'RECEIVED','summary':json.dumps({'candidate_id':'idea-1','video_id':'abcdefghijk'})}));before=p.read_bytes()
        radar.attach_intake(self.root,'framewright:fixture','prior',src)
        self.assertEqual(p.read_bytes(),before);self.assertEqual(len(list(src.glob('*.json'))),1)
    def test_publication_requires_matching_output_pin(self):
        self.link();row=self.status();row['payload']['publications'][0]['master_sha256']='f'*64
        row=wire.message('production_status','framewright',row['entity_key'],'f'*64,3,row['occurred_at'],row['payload'])
        self.assertEqual(wire.receive(self.root,'radar',row,radar.apply_message)['result'],'rejected')

class AnalyticsReportTest(unittest.TestCase):
    setUp=RadarFlowTest.setUp
    link=RadarFlowTest.link
    status=RadarFlowTest.status
    def make_report(self):
        import json
        from abvx_harness.process_learning import digest
        self.link();wire.receive(self.root,'radar',self.status(),radar.apply_message);radar.configure(self.root,'UC'+'a'*22)
        reports=[]
        for vid,views in [('zzzzzzzzzzz',7),('abcdefghijk',23)]:
            reports.append({'label':'videos_7d','parameters':{'dimensions':'video,creatorContentType','metrics':'views,averageViewDuration','filters':'video=='+vid},'requested_period':{'start':'2026-11-06','end':'2026-11-12'},'availability':'REPORTED','rows':[{'video':vid,'creatorContentType':'VIDEO_ON_DEMAND','views':views,'averageViewDuration':12.5}]})
        acquisition={'catalog':[{'video_id':'abcdefghijk','published_at':'2026-11-05T12:00:00+00:00'}],'reports':reports}
        run=self.root/'run';run.mkdir();(run/'acquisition.json').write_text(json.dumps(acquisition));(run/'execution.json').write_text(json.dumps({'acquisition_digest':digest(acquisition),'channel_id':'UC'+'a'*22,'captured_at':'2026-11-14T12:00:00+00:00'}));return run
    def test_existing_sharded_video_content_type_report_is_minimised(self):
        run=self.make_report();result=radar.export_analytics(run,self.root,'framewright:fixture','abcdefghijk')
        self.assertEqual(result['kind'],'analytics_snapshot');self.assertEqual(result['payload']['metrics']['views'],23);self.assertIsNone(result['payload']['metrics']['estimated_revenue']);self.assertEqual(result['payload']['window'],'calendar_report')
    def test_changed_acquisition_cannot_be_exported_as_retained_evidence(self):
        run=self.make_report();p=run/'acquisition.json';p.write_text('{}')
        with self.assertRaises(ValueError):radar.export_analytics(run,self.root,'framewright:fixture','abcdefghijk')

class OptionalSelectionTest(unittest.TestCase):
    def test_valid_legacy_research_without_selection_exports(self):
        import json
        from test_youtube_intelligence import packet,CLOCK
        p=packet();card={k:'fixture' for k in ['id','title','concept','rationale','duration','hook','visual','production','hypothesis','primary_metric']};card.update(priority=1,lane='PROVEN',format='HORIZONTAL_SHORT',complexity='LOW',sources=[dict(url='https://example.com',checked_at=CLOCK.isoformat(),supports='fixture')]);p['opportunities']=[card]
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);src=root/'research.json';src.write_text(json.dumps(p));row=radar.export_menu(src,root)
            self.assertEqual(row['kind'],'idea_menu');self.assertEqual(row['payload']['ideas'][0]['constraints'],['fixture'])

if __name__=='__main__':unittest.main()
