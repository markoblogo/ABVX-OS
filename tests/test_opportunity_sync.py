import json
from pathlib import Path
import tempfile
import unittest
from abvx_harness import opportunity_sync as sync
from abvx_harness import nantes_radar as radar

class SyncTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        radar._write_json(self.root/radar.STATE,{'schema_version':'v1','profiles':{},'jobs':{},'packets':{},'events':[],'collections':[],'history':[],'opportunities':[{'id':'epic-gift','name':'Epic Gift','kind':'vacancy','status':'UNKNOWN','application_status':'UNKNOWN','owner_decision':'UNKNOWN','source_refs':['fixture:original'],'notes':''}]})

    def test_sync_read_returns_fresh_catalog_without_candidate_details(self):
        result=sync.read(self.root)
        self.assertEqual(len(result['opportunities']),1)
        self.assertEqual(result['catalog_digest'],radar.digest(radar.load_json(self.root/radar.STATE)['opportunities']))
        self.assertEqual(result['sync']['allowed_fields'],['status','application_status','owner_decision'])

    def packet(self, kind='chat_user', changes=None):
        message='12345678-1234-4234-8234-123456789abc'
        return {'schema_version':'v1','run_id':'11111111-1111-4111-8111-111111111111','expected_digest':radar.digest(radar.load_json(self.root/radar.STATE)['opportunities']),'updates':[{'opportunity_id':'epic-gift','changes':changes or {'owner_decision':'DEFERRED'},'source':{'kind':kind,'message_id':message,'ref':f'https://chatgpt.com/c/{sync.PRIMARY_CHAT}?messageId={message}' if kind!='gmail_message' else 'https://mail.google.com/mail/u/0/#inbox/message123','text':'Синтетический пример: отложить Epic Gift.','quote':'отложить Epic Gift'}}]}

    def test_user_decision_updates_catalog_and_retains_source(self):
        before=radar.load_json(self.root/radar.STATE)
        receipt=sync.apply(self.root,self.packet())
        state=radar.load_json(self.root/radar.STATE)
        self.assertEqual(state['opportunities'][0]['owner_decision'],'DEFERRED')
        self.assertEqual(receipt['applied'],1)
        self.assertEqual(state['history'][-1]['origin'],'connected-review-sync')
        for k in ['profiles','jobs','packets','events','collections']:self.assertEqual(before[k],state[k])

    def test_replay_does_not_duplicate_and_run_id_reuse_cannot_change_payload(self):
        p=self.packet();sync.apply(self.root,p)
        length=len(radar.load_json(self.root/radar.STATE)['history'])
        self.assertTrue(sync.apply(self.root,p)['replayed'])
        self.assertEqual(len(radar.load_json(self.root/radar.STATE)['history']),length)
        p['updates'][0]['changes']['owner_decision']='DECLINED'
        with self.assertRaises(radar.ValidationError):sync.apply(self.root,p)

    def test_assistant_suggestion_is_queued_not_owner_decision(self):
        receipt=sync.apply(self.root,self.packet('assistant_proposal'))
        state=radar.load_json(self.root/radar.STATE)
        self.assertEqual(receipt['queued'],1)
        self.assertEqual(state['opportunities'][0]['owner_decision'],'UNKNOWN')

    def test_mail_cannot_set_owner_decision(self):
        with self.assertRaises(radar.ValidationError):sync.apply(self.root,self.packet('gmail_message'))

    def test_stale_digest_missing_quote_and_wrong_chat_fail_closed(self):
        for mode in ['stale','quote','chat']:
            p=self.packet()
            if mode=='stale':p['expected_digest']='0'*64
            if mode=='quote':p['updates'][0]['source']['quote']='not present'
            if mode=='chat':p['updates'][0]['source']['ref']=p['updates'][0]['source']['ref'].replace(sync.PRIMARY_CHAT,'other')
            with self.assertRaises(radar.ValidationError):sync.apply(self.root,p)
        self.assertEqual(radar.load_json(self.root/radar.STATE)['history'],[])

    def test_atomic_batch_rejects_unknown_id_and_unsafe_fields(self):
        for bad in [{'opportunity_id':'missing'}, {'changes':{'send_email':'yes'}}]:
            p=self.packet();p['updates'].append({**p['updates'][0],**bad})
            with self.assertRaises(radar.ValidationError):sync.apply(self.root,p)
            self.assertEqual(radar.load_json(self.root/radar.STATE)['opportunities'][0]['owner_decision'],'UNKNOWN')

    def test_mail_status_is_reported_evidence_without_sending(self):
        p=self.packet('gmail_message',{'application_status':'INTERVIEW_INVITED'})
        receipt=sync.apply(self.root,p)
        self.assertEqual(receipt['external_actions'],'NONE')
        self.assertEqual(radar.load_json(self.root/radar.STATE)['events'],[])

    def test_independent_runs_have_distinct_inbox_files(self):
        a=sync.read(self.root);b=sync.read(self.root)
        self.assertNotEqual(a['sync']['file'],b['sync']['file'])
        self.assertIn(a['sync']['run_id'],a['sync']['file'])
