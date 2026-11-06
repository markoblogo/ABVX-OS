import copy
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch
from abvx_harness import nantes_radar as radar
from abvx_harness.harness import ValidationError, load_json
from abvx_harness.__main__ import main

ROOT = Path(radar.__file__).resolve().parents[2]


class NantesRadarTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'schemas').mkdir()
        shutil.copy2(ROOT / 'schemas/nantes_radar.schema.json', self.root / 'schemas/nantes_radar.schema.json')
        self.profile = {'id':'synthetic', 'name':'Synthetic Person', 'location':'Nantes', 'roles':['Marketing'], 'skills':['marketing','product strategy'], 'languages':{'fr':'A2','en':'B2'}, 'source_refs':['fixture:cv'], 'facts':[{'id':'f1','text':'Synthetic marketing experience.', 'tags':['marketing'], 'confirmed':True,'language':'en','source_ref':'fixture:cv#f1'}, {'id':'f2','text':'Unconfirmed claim must never appear.', 'tags':['marketing'], 'confirmed':False,'language':'en','source_ref':'fixture:cv#f2'}]}
        self.job = {'title':'Marketing lead', 'company':'Synthetic Ltd', 'url':'https://example.org/jobs/123?utm_source=mail', 'location':'France', 'work_mode':'remote', 'remote_scope':'France', 'description':'Marketing and product strategy.', 'tags':['marketing'], 'required_languages':{'fr':'C1'}, 'eligibility':'UNKNOWN'}
        self.bundle = {'schema_version':'v1','source':'fixture:board','captured_at':'2026-10-23T08:00:00Z','jobs':[self.job]}
        radar.put_profile(self.root, self.profile)

    def imported(self):
        radar.import_jobs(self.root, self.bundle)
        return next(iter(load_json(self.root / radar.STATE)['jobs']))

    def packet(self):
        return radar.make_draft(self.root, self.imported(), 'synthetic')

    def test_tracking_parameters_do_not_duplicate_a_vacancy(self):
        self.assertEqual(radar.canonical_url('https://example.org/job/123?utm_source=mail&jobId=123#apply'), 'https://example.org/job/123?jobId=123')

    def test_import_and_reimport_preserve_identity_and_sources(self):
        first = self.imported()
        self.bundle['source'] = 'fixture:second-board'
        self.job['url'] = 'https://example.org/jobs/123?utm_source=other'
        radar.import_jobs(self.root, self.bundle)
        state = load_json(self.root / radar.STATE)
        self.assertEqual(list(state['jobs']), [first])
        self.assertEqual(len(state['jobs'][first]['provenance']), 2)

    def test_requisition_merges_cross_board_but_title_only_does_not(self):
        self.job['requisition_id'] = 'abc'
        first = self.imported()
        other = copy.deepcopy(self.job); other['url'] = 'https://other.example/abc'
        radar.import_jobs(self.root, {**self.bundle, 'jobs':[other]})
        self.assertEqual(len(load_json(self.root/radar.STATE)['jobs']), 1)
        other.pop('requisition_id'); other['url'] = 'https://third.example/abc'
        radar.import_jobs(self.root, {**self.bundle,'jobs':[other]})
        rows = radar.ranking(self.root, 'synthetic')
        self.assertEqual(len(rows), 2)
        self.assertTrue(rows[0]['possible_duplicates'])

    def test_different_requisitions_do_not_collapse(self):
        self.job['requisition_id'] = 'a'; self.imported()
        self.job['url'] = 'https://other.example/def'; self.job['requisition_id'] = 'b'
        radar.import_jobs(self.root, self.bundle)
        self.assertEqual(len(load_json(self.root/radar.STATE)['jobs']), 2)

    def test_bad_batch_does_not_partially_import(self):
        self.bundle['jobs'].append({**self.job,'url':'javascript:alert(1)'})
        with self.assertRaises(ValidationError): radar.import_jobs(self.root, self.bundle)
        self.assertEqual(load_json(self.root/radar.STATE)['jobs'], {})

    def test_invalid_mode_and_naive_capture_are_rejected(self):
        self.job['work_mode'] = 'any'
        with self.assertRaises(ValidationError): radar.import_jobs(self.root,self.bundle)
        self.job['work_mode'] = 'remote'; self.bundle['captured_at']='2026-10-23T08:00:00'
        with self.assertRaises(ValidationError): radar.import_jobs(self.root,self.bundle)

    def test_older_observation_cannot_reopen_closed_job(self):
        self.job['status']='closed'; self.imported()
        self.bundle['captured_at']='2026-10-22T08:00:00Z'; self.job['status']='open'
        radar.import_jobs(self.root,self.bundle)
        self.assertEqual(radar.ranking(self.root,'synthetic')[0]['status'],'closed')

    def test_france_remote_is_not_the_same_as_us_remote(self):
        self.assertEqual(radar.location_gate(self.job),'PASS')
        self.job['remote_scope']='United States'; self.assertEqual(radar.location_gate(self.job),'FAIL')
        self.job['remote_scope']='UNKNOWN'; self.assertEqual(radar.location_gate(self.job),'REVIEW')
        self.job['remote_scope']='Europe excluding France'; self.assertEqual(radar.location_gate(self.job),'REVIEW')
        self.job['eligible_countries']=['DE']; self.assertEqual(radar.location_gate(self.job),'FAIL')

    def test_language_and_work_rights_uncertainty_is_visible(self):
        self.imported(); row=radar.ranking(self.root,'synthetic')[0]
        self.assertEqual(row['language_gate'],'REVIEW'); self.assertEqual(row['eligibility_gate'],'UNKNOWN')
        self.assertTrue(any('A2' in f and 'C1' in f for f in row['flags']))
        self.assertEqual(row['score_kind'],'keyword-triage-v1')

    def test_expired_or_missing_body_blocks_draft(self):
        self.job['deadline']='2020-01-01'; job_id=self.imported()
        with self.assertRaises(ValidationError): radar.make_draft(self.root,job_id,'synthetic')
        self.job.pop('deadline'); self.job['description']=''; radar.import_jobs(self.root,self.bundle)
        with self.assertRaises(ValidationError): radar.make_draft(self.root,job_id,'synthetic')
        self.assertIsNone(radar.ranking(self.root,'synthetic')[0]['score'])

    def test_draft_uses_confirmed_facts_and_keeps_provenance(self):
        packet=self.packet()
        self.assertIn('Synthetic marketing experience.',packet['cv'])
        self.assertNotIn('Unconfirmed claim',packet['letter'])
        self.assertEqual(packet['decision'],'PENDING')
        self.assertEqual(packet['source_refs'],['fixture:cv#f1'])
        self.assertIn('DRAFT',packet['letter'])

    def test_candidate_eligibility_failure_blocks_draft(self):
        self.profile['work_eligibility']='FAIL';radar.put_profile(self.root,self.profile)
        jid=self.imported()
        with self.assertRaises(ValidationError):radar.make_draft(self.root,jid,'synthetic')

    def test_french_draft_needs_confirmed_french_facts(self):
        job_id=self.imported()
        with self.assertRaises(ValidationError):radar.make_draft(self.root,job_id,'synthetic','fr')

    def test_manual_approval_is_bound_to_displayed_digest(self):
        packet=self.packet()
        with self.assertRaises(ValidationError):radar.review(self.root,packet['id'],'APPROVED','human','wrong')
        result=radar.review(self.root,packet['id'],'APPROVED','human',packet['digest'])
        self.assertEqual(result['external_action'],'NONE')
        self.assertEqual(load_json(self.root/radar.STATE)['events'],[])

    def test_profile_change_invalidates_review(self):
        packet=self.packet(); self.profile['location']='Paris'; radar.put_profile(self.root,self.profile)
        with self.assertRaises(ValidationError):radar.review(self.root,packet['id'],'APPROVED','human',packet['digest'])

    def test_tampered_letter_cannot_use_previous_approval(self):
        packet=self.packet(); state=load_json(self.root/radar.STATE)
        state['packets'][packet['id']]['letter']='Changed!'; radar._write_json(self.root/radar.STATE,state)
        with self.assertRaises(ValidationError):radar.review(self.root,packet['id'],'APPROVED','human',packet['digest'])

    def test_outcomes_need_actual_submission_evidence_and_are_idempotent(self):
        packet=self.packet(); jid=packet['job_id']; today=radar.date.today().isoformat()
        with self.assertRaises(ValidationError):radar.record_event(self.root,jid,'synthetic','submitted','fixture',today,packet['id'])
        with self.assertRaises(ValidationError):radar.record_event(self.root,jid,'synthetic','offer','fixture',today)
        radar.review(self.root,packet['id'],'APPROVED','human',packet['digest'])
        for _ in range(2):radar.record_event(self.root,jid,'synthetic','submitted','fixture:external-manual-action',today,packet['id'])
        radar.record_event(self.root,jid,'synthetic','interview','fixture:owner-report',today)
        self.assertEqual(len(load_json(self.root/radar.STATE)['events']),2)
        self.assertFalse(radar.ranking(self.root,'synthetic')[0]['shortlist'])

    def test_historical_kinds_unknowns_and_dates_are_not_invented(self):
        doc={'schema_version':'v1','opportunities':[{'id':'legacy-one','name':'Legacy name','kind':'UNKNOWN','status':'NEEDS_IMPORT','source_refs':['chatgpt-conversation://fixture'],'notes':'Mention only; no application proof.'}], 'events':[{'opportunity_id':'legacy-one','status':'UNKNOWN','occurred_at':None,'source_refs':['chatgpt-conversation://fixture'],'notes':'Date unknown.'}]}
        for _ in range(2):radar.import_history(self.root,doc)
        state=load_json(self.root/radar.STATE)
        self.assertEqual(len(state['opportunities']),1);self.assertEqual(len(state['history']),1)
        self.assertIsNone(state['history'][0]['occurred_at']);self.assertEqual(state['events'],[])

    def test_historical_conflict_does_not_overwrite_prior_evidence(self):
        doc={'schema_version':'v1','opportunities':[{'id':'x','name':'X','kind':'platform','status':'UNKNOWN','source_refs':['fixture:history'],'notes':''}],'events':[]}
        radar.import_history(self.root,doc);doc['opportunities'][0]['kind']='vacancy'
        with self.assertRaises(ValidationError):radar.import_history(self.root,doc)
        self.assertEqual(load_json(self.root/radar.STATE)['opportunities'][0]['kind'],'platform')

    def test_cli_uses_existing_abvx_entrypoint(self):
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(['opportunities','catalog'],root=self.root),0)
        self.assertEqual(json.loads(output.getvalue())['profiles'],['synthetic'])

    def test_feed_failure_is_not_no_result(self):
        with patch.object(radar,'build_opener') as opener:
            opener.return_value.open.side_effect=OSError('fixture offline')
            with self.assertRaises(ValidationError):radar.search(self.root,'marketing')
        self.assertEqual(load_json(self.root/radar.STATE)['collections'][-1]['status'],'COLLECTION_FAILED')

    def test_cached_feed_search_does_not_call_network(self):
        path=self.root/'.tmp/opportunities/remotive-cache.json'
        radar._write_json(path,{'fetched_at':radar.now_iso(),'jobs':[{'title':'Marketing lead','company_name':'Synthetic Ltd','url':'https://remotive.com/remote-jobs/marketing/synthetic-123','description':'Marketing work','candidate_required_location':'Worldwide'}]})
        with patch.object(radar,'build_opener') as opener:
            result=radar.search(self.root,'marketing');opener.assert_not_called()
        self.assertEqual(result['added'],1)
        self.assertEqual(radar.ranking(self.root,'synthetic')[0]['source'],'Remotive')

    def test_historical_entry_can_link_to_vacancy_without_losing_history(self):
        jid=self.imported()
        radar.import_history(self.root,{'schema_version':'v1','opportunities':[{'id':'legacy','name':'Old lead','kind':'UNKNOWN','status':'UNKNOWN','source_refs':['fixture:chat'],'notes':''}],'events':[]})
        radar.link(self.root,'legacy',jid,'fixture:owner-reconciliation')
        state=load_json(self.root/radar.STATE)
        self.assertEqual(state['opportunities'][0]['linked_job_id'],jid)
        self.assertEqual(len(state['jobs']),1)
        self.assertEqual(state['history'][-1]['origin'],'human-link')

    def test_missing_working_language_is_review_not_pass(self):
        self.job.pop('required_languages');self.imported()
        self.assertEqual(radar.ranking(self.root,'synthetic')[0]['language_gate'],'REVIEW')

    def test_decisions_append_history_without_external_actions(self):
        doc={'schema_version':'v1','opportunities':[{'id':'x','name':'X','kind':'platform','status':'UNKNOWN','source_refs':['fixture:history'],'notes':''}],'events':[]}
        radar.import_history(self.root,doc)
        radar.decide(self.root,'x','deferred','owner choice','fixture:human')
        state=load_json(self.root/radar.STATE)
        self.assertEqual(state['opportunities'][0]['status'],'deferred')
        self.assertEqual(state['history'][-1]['previous_status'],'UNKNOWN')
        self.assertEqual(state['events'],[])

class HistoryReconciliationTests(unittest.TestCase):
    setUp = NantesRadarTests.setUp
    imported = NantesRadarTests.imported
    def test_reconciliation_preserves_prior_record_and_rejects_stale_writer(self):
        original={'id':'x','name':'X','kind':'UNKNOWN','status':'NEEDS_IMPORT','source_refs':['fixture:old'],'notes':''}
        radar.import_history(self.root,{'schema_version':'v1','opportunities':[original],'events':[]})
        before=load_json(self.root/radar.STATE)
        updated={**original,'kind':'vacancy','status':'HISTORICAL_LEAD','source_refs':['fixture:old','fixture:new'],'notes':'No sending inferred.'}
        bundle={'schema_version':'v1','opportunities':[updated],'events':[]}
        radar.reconcile_history(self.root,bundle,radar.digest(before['opportunities']))
        state=load_json(self.root/radar.STATE)
        self.assertEqual(state['history'][-1]['previous_record'],original)
        self.assertEqual(state['events'],[])
        with self.assertRaises(ValidationError):radar.reconcile_history(self.root,bundle,'stale')
        count=len(state['history'])
        radar.reconcile_history(self.root,bundle,radar.digest(state['opportunities']))
        self.assertEqual(len(load_json(self.root/radar.STATE)['history']),count)

    def test_assistant_suggestion_cannot_become_owner_decision_or_sent_application(self):
        original={'id':'x','name':'X','kind':'UNKNOWN','status':'UNKNOWN','source_refs':['fixture:assistant'],'notes':''}
        radar.import_history(self.root,{'schema_version':'v1','opportunities':[original],'events':[]})
        before=load_json(self.root/radar.STATE)
        for field in ['application_status','owner_decision']:
            changed={**original,field:'submitted'}
            with self.assertRaises(ValidationError):radar.reconcile_history(self.root,{'schema_version':'v1','opportunities':[changed],'events':[]},radar.digest(before['opportunities']))

    def test_context_pack_excludes_private_candidate_facts_and_packet_bodies(self):
        jid=self.imported();radar.make_draft(self.root,jid,'synthetic')
        packet=radar.context_pack(self.root)
        text=json.dumps(packet)
        self.assertNotIn('Synthetic marketing experience',text)
        self.assertNotIn('Unconfirmed claim',text)
        self.assertEqual(packet['local_sync'],'MANUAL_EXPORT_ONLY')
        self.assertEqual(packet['primary_chat'],'https://chatgpt.com/c/6ac8a06b-fae0-83ed-b55e-fd23524d85f9')

    def test_employment_prospect_is_not_fabricated_vacancy(self):
        original={'id':'x','name':'X','kind':'employment_prospect','status':'UNSOLICITED_PROPOSED','source_refs':['fixture:assistant'],'notes':'No vacancy confirmed.'}
        radar.import_history(self.root,{'schema_version':'v1','opportunities':[original],'events':[]})
        self.assertEqual(load_json(self.root/radar.STATE)['jobs'],{})

if __name__=='__main__':unittest.main()
