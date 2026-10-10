"""Operational regression fixtures remain in temporary roots, never canonical state."""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from abvx_harness.book_radar import empty_state,save_state,load_state,import_bundle
from abvx_harness.book_radar_outcomes import evidence
from abvx_harness.book_radar_observe import (U,UNOBSERVABLE,record_packet,check_packet,due,status,checklist,validate_packet,comparability,resolve,render,template)
from abvx_harness.harness import ValidationError
from test_book_radar_outcomes import fixture,refresh

class ObservationOperationsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        real=Path(__file__).resolve().parents[1]
        (self.root/'BOOK_RADAR_CONTROLLED_CALIBRATION_V1.json').write_bytes((real/'BOOK_RADAR_CONTROLLED_CALIBRATION_V1.json').read_bytes())
        self.book,self.actual,self.claim=fixture(self.root);self.book['publication_date']='2026-09-03';self.actual['book_age_days']=29;refresh(self.actual)
        s=empty_state();s['products']=[{'id':self.book['product_id']}];s['observed_books']=[self.book];s['actuals']=[self.actual];save_state(self.root,s)
        p=self.root/'book-radar/audits/observation-attribution-v1';p.mkdir(parents=True);(p/'DATA_OBSERVABILITY_V1.md').write_text('Standard-source capability fixture')
        clock=patch('abvx_harness.book_radar_observe.today',return_value='2026-10-10');clock.start();self.addCleanup(clock.stop)
    def packet(self,day='2026-10-03',checkpoint='D30'):
        w=copy.deepcopy(self.actual['windows']['lifetime']);w['end']=day;w['window_kind']='LIFETIME'
        k=copy.deepcopy(self.actual['windows']['kenp']);m=copy.deepcopy(self.actual['windows']['money']);m['end']=day
        return {'schema_version':'book-radar-checkpoint-evidence-packet/v1','id':'packet:test:'+day,'experiment_id':self.book['audit_book_id'],'checkpoint':checkpoint,'target_date':'2026-10-03','actual_date':day,'observed_at':day+'T12:00:00+02:00','timezone':'Europe/Paris','book_age_days':( __import__('datetime').date.fromisoformat(day)-__import__('datetime').date.fromisoformat(self.book['publication_date'])).days,'collection_state':'COMPLETE','approximate_tolerance_days':0,'applicability':{'state':'APPLICABLE','recorded_by':'OPERATOR','reason':'Manual synthetic collection','evidence':[]},'accounts':[{'subject_id':self.book['id'],'scope':self.actual['marketplace_scope'],'marketplace':U,'formats':['ebook','print'],'orders':w,'kenp':k,'royalties':m}],'retailers':[],'search_snapshots':[],'categories':[],'costs':[],'not_observable':{k:'NOT_OBSERVABLE_FROM_CURRENT_STANDARD_SOURCE' for k in UNOBSERVABLE},'comparability':{'status':U,'compared_to':U,'reasons':[]},'evidence':self.book['evidence'],'notes':['SYNTHETIC TEMPORARY FIXTURE ONLY']}
    def source(self,p):
        path=self.root/'packet.json';path.write_text(json.dumps(p,indent=2)+'\n');return path
    def test_due_today_is_not_overdue(self):
        def d(at):return next(r for r in due(self.root,at)['checkpoints'] if r['experiment_id']=='test' and r['checkpoint']=='D30')['status']
        self.assertEqual(d('2026-10-02'),'UPCOMING');self.assertEqual(d('2026-10-03'),'DUE_TODAY');self.assertEqual(d('2026-10-04'),'OVERDUE')
    def test_nearby_actual_is_not_checkpoint_complete(self):
        r=next(r for r in due(self.root,'2026-10-03')['checkpoints'] if r['experiment_id']=='test' and r['checkpoint']=='D30')
        self.assertEqual(r['status'],'DUE_TODAY');self.assertEqual(r['observation_ids'],[])
    def test_historical_missing_not_backfilled(self):
        r=next(r for r in due(self.root,'2026-10-03')['checkpoints'] if r['experiment_id']=='test' and r['checkpoint']=='D7')
        self.assertEqual(r['status'],'MISSING')
    def test_late_is_not_exact_and_actual_date_preserved(self):
        p=self.packet('2026-10-04');receipt=record_packet(self.root,self.source(p));self.assertEqual(receipt['assessment']['timing'],'LATE')
        stored=load_state(self.root)['checkpoint_packets'][0];self.assertEqual(stored['packet']['actual_date'],'2026-10-04');self.assertEqual(stored['packet']['target_date'],'2026-10-03')
        r=next(r for r in due(self.root,'2026-10-05')['checkpoints'] if r['experiment_id']=='test' and r['checkpoint']=='D30');self.assertEqual(r['status'],'COLLECTED_LATE')
    def test_exact_packet_explicitly_completes_checkpoint(self):
        record_packet(self.root,self.source(self.packet()))
        r=next(r for r in due(self.root,'2026-10-03')['checkpoints'] if r['experiment_id']=='test' and r['checkpoint']=='D30');self.assertEqual(r['status'],'COLLECTED_EXACT')
    def test_approximation_requires_explicit_tolerance(self):
        p=self.packet('2026-10-02')
        with self.assertRaises(ValidationError):record_packet(self.root,self.source(p))
        p['approximate_tolerance_days']=1;receipt=record_packet(self.root,self.source(p));self.assertEqual(receipt['assessment']['timing'],'APPROXIMATE')
        r=next(r for r in due(self.root,'2026-10-03')['checkpoints'] if r['experiment_id']=='test' and r['checkpoint']=='D30');self.assertEqual(r['status'],'COLLECTED_APPROXIMATE')
    def test_partial_packet_does_not_complete_checkpoint(self):
        p=self.packet();p['collection_state']='PARTIAL';record_packet(self.root,self.source(p))
        r=next(r for r in due(self.root,'2026-10-03')['checkpoints'] if r['experiment_id']=='test' and r['checkpoint']=='D30');self.assertEqual(r['status'],'DUE_TODAY')
    def test_unknown_and_not_observable_are_not_zero(self):
        p=self.packet();p['accounts'][0]['orders']['paid_units']=U;validate_packet(p)
        self.assertEqual(p['accounts'][0]['orders']['paid_units'],U)
        self.assertEqual(p['not_observable']['organic_impressions'],'NOT_OBSERVABLE_FROM_CURRENT_STANDARD_SOURCE')
        p['not_observable']['organic_impressions']=0
        with self.assertRaises(ValidationError):validate_packet(p)
    def test_free_kenp_and_royalties_not_orders(self):
        p=self.packet();w=p['accounts'][0]['orders'];w.update(processed_units=26,free_units=26)
        validate_packet(p);record_packet(self.root,self.source(p));a=load_state(self.root)['checkpoint_packets'][0]['packet']['accounts'][0]
        self.assertEqual(a['orders']['paid_units'],0);self.assertEqual(a['orders']['free_units'],26);self.assertEqual(a['kenp']['kenp_pages'],10);self.assertEqual(a['royalties']['estimated_royalties'],0.04)
    def test_bounded_absence_is_not_rank(self):
        p=self.packet();q={'schema_version':'book-radar-search-snapshot/v1','id':'search:test','book_id':self.book['id'],'experiment_id':U,'observed_date':p['actual_date'],'observed_at':p['observed_at'],'marketplace':'amazon.com','query':'test retained query','device_surface':U,'signed_in_context':U,'delivery_context':U,'depth':16,'presence':'NOT_FOUND_WITHIN_DEPTH','rank':U,'rank_basis':'ORGANIC','target_asin':U,'competing_results':[],'competitor_capture_status':U,'category_context':U,'method':'READ_ONLY_RETAILER_SNAPSHOT','repeat_protocol_id':U,'evidence':self.book['evidence'],'limitations':['Synthetic bounded capture']}
        p['search_snapshots']=[q];validate_packet(p);q['rank']=17
        with self.assertRaises(ValidationError):validate_packet(p)
    def test_first_live_does_not_replace_publication(self):
        p=self.packet();p['target_date']='2026-10-21';p['book_age_days']=12
        before=(self.root/'book-radar/state.json').read_bytes()
        with self.assertRaises(ValidationError):record_packet(self.root,self.source(p))
        self.assertEqual(before,(self.root/'book-radar/state.json').read_bytes());self.assertEqual(load_state(self.root)['observed_books'][0]['publication_timestamp'],U)
    def test_same_evidence_import_idempotent(self):
        path=self.source(self.packet());record_packet(self.root,path);before=(self.root/'book-radar/state.json').read_bytes()
        self.assertEqual(record_packet(self.root,path)['added'],0);self.assertEqual(before,(self.root/'book-radar/state.json').read_bytes())
    def test_changed_evidence_bytes_reject(self):
        path=self.source(self.packet());record_packet(self.root,path);before=(self.root/'book-radar/state.json').read_bytes();(self.root/'raw.txt').write_text('changed retained evidence')
        with self.assertRaises(ValidationError):record_packet(self.root,path)
        self.assertEqual(before,(self.root/'book-radar/state.json').read_bytes())
    def test_same_identity_changed_packet_bytes_reject(self):
        path=self.source(self.packet());record_packet(self.root,path);before=(self.root/'book-radar/state.json').read_bytes();path.write_text(path.read_text()+' ')
        with self.assertRaises(ValidationError):record_packet(self.root,path)
        self.assertEqual(before,(self.root/'book-radar/state.json').read_bytes())
    def test_invalid_packet_no_mutation(self):
        p=self.packet();p.pop('accounts');before=(self.root/'book-radar/state.json').read_bytes()
        with self.assertRaises(ValidationError):record_packet(self.root,self.source(p))
        self.assertEqual(before,(self.root/'book-radar/state.json').read_bytes())
    def test_cost_absence_does_not_block(self):
        p=self.packet();record_packet(self.root,self.source(p));self.assertEqual(load_state(self.root)['checkpoint_packets'][0]['packet']['costs'],[])
    def controlled(self):
        p=self.packet();p.update(experiment_id='book-radar-controlled-persistence-v1',checkpoint='T7',book_age_days=U,collection_state='PARTIAL');p['accounts'][0]['subject_id']='pmp-2026';return p
    def test_t7_collection_does_not_interpret(self):
        p=self.controlled();r=record_packet(self.root,self.source(p));self.assertEqual(r['assessment']['interpretation'],'PROHIBITED_UNTIL_T14')
        self.assertIn('PROHIBITED UNTIL T14',render(due(self.root,'2026-10-03'),'due'))
        self.assertEqual(load_state(self.root)['calibrations'],[])
    def test_t7_interpretation_payload_rejected(self):
        p=self.controlled();p['attribution']='MARKET_HYPOTHESIS_UNSUPPORTED'
        with self.assertRaises(ValidationError):record_packet(self.root,self.source(p))
        p=self.controlled();p['records']={'actuals':[self.actual],'attribution_observations':[],'experiment_costs':[]}
        with self.assertRaises(ValidationError):record_packet(self.root,self.source(p))
    def test_status_due_checklist_are_read_only(self):
        before=(self.root/'book-radar/state.json').read_bytes();d=due(self.root,'2026-10-03');s=status(self.root,'2026-10-03');checklist(self.root,'test','2026-10-03')
        self.assertEqual(before,(self.root/'book-radar/state.json').read_bytes());self.assertEqual(s['new_attribution_records'],0);self.assertEqual(s['new_calibration_records'],0)
    def test_comparability_cannot_hide_unknown_context_or_changed_window(self):
        p=self.packet();a=check_packet(self.root,self.source(p))['assessment']['comparability']
        self.assertEqual(a['status'],'PARTIALLY_COMPARABLE');self.assertTrue(any('unknown' in r for r in a['reasons']));self.assertTrue(any('window' in r for r in a['reasons']))
        p['comparability']['status']='COMPARABLE'
        with self.assertRaises(ValidationError):record_packet(self.root,self.source(p))
    def test_native_actuals_must_match_packet_and_are_appended(self):
        p=self.packet();a=copy.deepcopy(self.actual);a.update(id='actual:D30:test',observed_date=p['actual_date'],book_age_days=30,checkpoint='D30')
        for key,window in [('orders','lifetime'),('kenp','kenp'),('royalties','money')]:a['windows'][window]={k:v for k,v in p['accounts'][0][key].items() if k!='window_kind'}
        refresh(a);p['records']={'actuals':[a],'attribution_observations':[],'experiment_costs':[]};record_packet(self.root,self.source(p));s=load_state(self.root)
        self.assertEqual(len(s['actuals']),2);self.assertEqual(s['actuals'][0],self.actual)
    def test_not_applicable_requires_owner_evidence(self):
        p=self.packet();p['applicability']['state']='NOT_APPLICABLE'
        with self.assertRaises(ValidationError):validate_packet(p)
        p['applicability'].update(recorded_by='OWNER',reason='Synthetic explicit waiver',evidence=self.book['evidence']);record_packet(self.root,self.source(p))
        r=next(r for r in due(self.root,'2026-10-03')['checkpoints'] if r['experiment_id']=='test' and r['checkpoint']=='D30');self.assertEqual(r['status'],'NOT_APPLICABLE')
    def test_upcoming_schedule_uses_fixture_publication_date(self):
        result=due(self.root,'2026-10-02')
        actual={x['experiment_id']:x['target_date'] for x in result['upcoming'] if x['checkpoint']=='D30'}
        self.assertEqual(actual,{'test':'2026-10-03'})
        self.assertTrue(any(x['experiment_id']=='test' for x in due(self.root,'2026-10-03')['due']))
    def test_no_future_observations(self):
        p=self.packet('2026-10-11')
        with self.assertRaises(ValidationError):record_packet(self.root,self.source(p))
    def test_unknown_publication_stays_missing(self):
        s=load_state(self.root);s['observed_books'][0]['publication_date']=U;s['actuals'][0]['book_age_days']=U;s['actuals'][0]['age_basis']=U;save_state(self.root,s)
        r=next(r for r in due(self.root,'2026-10-03')['checkpoints'] if r['experiment_id']=='test' and r['checkpoint']=='D30');self.assertEqual(r['status'],'MISSING');self.assertEqual(r['target_date'],U)
    def test_submission_waits_for_format_live_confirmation_before_checkpoints(self):
        s=load_state(self.root);s['observed_books'][0]['publication_date']=U;s['actuals'][0]['book_age_days']=U;s['actuals'][0]['age_basis']=U
        s['launches']=[{'id':'launch:test:submission','event_type':'KDP_SUBMISSION','book_id':self.book['id'],'submission_date':'2026-10-05','format_states':[{'format_id':'test:kindle','format':'Kindle','asin':'B0TEST','status':'PUBLISHING','submission_date':'2026-10-05','first_confirmed_live_date':U}]}]
        save_state(self.root,s);r=due(self.root,'2026-10-05')
        self.assertEqual([x['action'] for x in r['live_confirmation_due']],['CONFIRM_LIVE_STATUS'])
        self.assertFalse(any(x['experiment_id']=='test' for x in r['due']+r['upcoming']))
        self.assertEqual(checklist(self.root,'test','2026-10-05')['next']['action'],'CONFIRM_LIVE_STATUS')
    def test_confirmed_format_live_date_anchors_existing_checkpoints(self):
        s=load_state(self.root);s['observed_books'][0]['publication_date']=U;s['actuals'][0]['book_age_days']=U;s['actuals'][0]['age_basis']=U
        s['launches']=[{'id':'launch:test:submission','event_type':'KDP_SUBMISSION','book_id':self.book['id'],'submission_date':'2026-10-05','format_states':[{'format_id':'test:kindle','format':'Kindle','asin':'B0TEST','status':'PUBLISHING','submission_date':'2026-10-05','first_confirmed_live_date':U},{'format_id':'test:paperback','format':'Paperback','asin':'B0TESTP','status':'PUBLISHING','submission_date':'2026-10-05','first_confirmed_live_date':U}]},{'id':'launch:test:kindle-live','event_type':'KDP_FORMAT_STATUS_OBSERVATION','submission_event_id':'launch:test:submission','book_id':self.book['id'],'observed_date':'2026-10-08','format_states':[{'format_id':'test:kindle','format':'Kindle','status':'LIVE','first_confirmed_live_date':'2026-10-08'}]},{'id':'launch:test:paperback-live','event_type':'KDP_FORMAT_STATUS_OBSERVATION','submission_event_id':'launch:test:submission','book_id':self.book['id'],'observed_date':'2026-10-10','format_states':[{'format_id':'test:paperback','format':'Paperback','status':'LIVE','first_confirmed_live_date':'2026-10-10'}]}]
        save_state(self.root,s);r=due(self.root,'2026-10-10')
        d0=next(x for x in r['checkpoints'] if x['experiment_id']=='test' and x['checkpoint']=='D0')
        d7=next(x for x in r['checkpoints'] if x['experiment_id']=='test' and x['checkpoint']=='D7')
        self.assertEqual(d0['target_date'],'2026-10-08');self.assertEqual(d0['status'],'OVERDUE')
        self.assertEqual(d7['target_date'],'2026-10-15');self.assertEqual(r['live_confirmation_due'],[])
        self.assertEqual(template(self.root,'test','D7','2026-10-10')['target_date'],'2026-10-15')
        from abvx_harness.book_radar_observe import _format_launch_states
        dates={x['format']:x['first_confirmed_live_date'] for x in _format_launch_states(s,self.book['id'])}
        self.assertEqual(dates,{'Kindle':'2026-10-08','Paperback':'2026-10-10'})
    def test_complete_collection_requires_all_retained_queries(self):
        s=load_state(self.root);p=self.packet();p['search_snapshots']=[]
        q={'schema_version':'book-radar-search-snapshot/v1','id':'search:old','book_id':self.book['id'],'experiment_id':U,'observed_date':'2026-10-02','observed_at':U,'marketplace':'amazon.com','query':'retained route','device_surface':U,'signed_in_context':U,'delivery_context':U,'depth':16,'presence':U,'rank':U,'rank_basis':'ORGANIC','target_asin':U,'competing_results':[],'competitor_capture_status':U,'category_context':U,'method':'READ_ONLY_RETAILER_SNAPSHOT','repeat_protocol_id':U,'evidence':self.book['evidence'],'limitations':[]};s['search_snapshots'].append(q);save_state(self.root,s)
        with self.assertRaises(ValidationError):record_packet(self.root,self.source(p))
    def test_category_absence_never_creates_rank(self):
        p=self.packet();p['categories']=[{'subject_id':self.book['id'],'target_category':'retained category','category':U,'marketplace':'amazon.com','observed_at':p['observed_at'],'presence':'NOT_FOUND_WITHIN_DEPTH','position':17,'depth':16,'context':U,'evidence':self.book['evidence']}]
        with self.assertRaises(ValidationError):validate_packet(p)

    def test_explicit_ad_hoc_actual_on_target_still_not_checkpoint(self):
        s=load_state(self.root);s['actuals'][0]['observed_date']='2026-10-03';s['actuals'][0]['book_age_days']=30;refresh(s['actuals'][0]);save_state(self.root,s)
        row=next(r for r in due(self.root,'2026-10-03')['checkpoints'] if r['experiment_id']=='test' and r['checkpoint']=='D30')
        self.assertEqual(row['status'],'DUE_TODAY')
    def test_receipt_removal_or_modification_rejected(self):
        record_packet(self.root,self.source(self.packet()));before=(self.root/'book-radar/state.json').read_bytes()
        s=load_state(self.root);s['checkpoint_packets']=[]
        with self.assertRaises(ValidationError):save_state(self.root,s)
        self.assertEqual(before,(self.root/'book-radar/state.json').read_bytes())
        s=load_state(self.root);s['checkpoint_packets'][0]['assessment']['comparability']['reasons'].append('Changed immutable receipt')
        with self.assertRaises(ValidationError):save_state(self.root,s)
    def test_native_actual_traffic_cannot_be_manufactured(self):
        p=self.packet();a=copy.deepcopy(self.actual);a.update(id='actual:bad',observed_date=p['actual_date'],book_age_days=30,checkpoint='D30')
        for key,window in [('orders','lifetime'),('kenp','kenp'),('royalties','money')]:a['windows'][window]={k:v for k,v in p['accounts'][0][key].items() if k!='window_kind'}
        a['instrumentation']['impressions']=100;a['instrumentation_evidence']=self.book['evidence'];a['instrumentation_window']='Synthetic window';refresh(a);p['records']={'actuals':[a],'attribution_observations':[],'experiment_costs':[]}
        with self.assertRaises(ValidationError):record_packet(self.root,self.source(p))
    def test_cli_read_commands_do_not_write(self):
        from abvx_harness.__main__ import main
        from contextlib import redirect_stdout
        from io import StringIO
        before=(self.root/'book-radar/state.json').read_bytes()
        with redirect_stdout(StringIO()):
            for args in (['radar','observe','--due'],['radar','observe','test'],['radar','observe','--status'],['radar','observe','test','--template','D30']):
                self.assertEqual(main(args,root=self.root),0)
        self.assertEqual(before,(self.root/'book-radar/state.json').read_bytes())

    def test_unknown_format_coverage_is_explicit_and_checklist_uses_latest_packet(self):
        p=self.packet();p['accounts'][0]['formats']=U;validate_packet(p);record_packet(self.root,self.source(p))
        c=checklist(self.root,'test','2026-10-04');self.assertEqual(c['previous_account']['id'],p['id']);self.assertEqual(c['previous_account']['date'],'2026-10-03');self.assertEqual(c['previous_comparability'],'PARTIALLY_COMPARABLE')

    def test_cli_record_check_and_repeat_are_append_only(self):
        from abvx_harness.__main__ import main
        from contextlib import redirect_stdout
        from io import StringIO
        path=self.source(self.packet());out=StringIO()
        with redirect_stdout(out):
            self.assertEqual(main(['radar','observe','--check',str(path)],root=self.root),0)
            self.assertEqual(main(['radar','observe','--record',str(path)],root=self.root),0)
            before=(self.root/'book-radar/state.json').read_bytes()
            self.assertEqual(main(['radar','observe','--record',str(path)],root=self.root),0)
        self.assertIn('ALREADY_RECORDED',out.getvalue());self.assertEqual(before,(self.root/'book-radar/state.json').read_bytes())
    def test_cli_record_cannot_override_collection_clock(self):
        from abvx_harness.__main__ import main
        from contextlib import redirect_stderr
        from io import StringIO
        before=(self.root/'book-radar/state.json').read_bytes()
        with redirect_stderr(StringIO()):
            self.assertEqual(main(['radar','observe','--record',str(self.source(self.packet())),'--as-of','2026-10-20'],root=self.root),1)
        self.assertEqual(before,(self.root/'book-radar/state.json').read_bytes())

    def test_unretained_search_baseline_is_unknown_not_incomparable(self):
        p=self.packet();p['accounts']=[];p['collection_state']='PARTIAL'
        p['search_snapshots']=[{'schema_version':'book-radar-search-snapshot/v1','id':'search:new-only','book_id':self.book['id'],'experiment_id':U,'observed_date':p['actual_date'],'observed_at':p['observed_at'],'marketplace':'amazon.com','query':'retained query with missing historical capture','device_surface':U,'signed_in_context':U,'delivery_context':U,'depth':16,'presence':U,'rank':U,'rank_basis':'ORGANIC','target_asin':U,'competing_results':[],'competitor_capture_status':U,'category_context':U,'method':'READ_ONLY_RETAILER_SNAPSHOT','repeat_protocol_id':U,'evidence':self.book['evidence'],'limitations':[]}]
        result=check_packet(self.root,self.source(p))['assessment']['comparability']
        self.assertEqual(result['status'],U);self.assertTrue(any('not retained' in r for r in result['reasons']))

if __name__=='__main__':unittest.main()
