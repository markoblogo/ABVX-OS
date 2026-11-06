import importlib.util
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location('journal', Path(__file__).parents[1] / 'scripts/nantes_radar_journal.py')
j = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(j)


class JournalTests(unittest.TestCase):
    def setup_run(self, root):
        j.init(root, '2026-10-27-weekly', 'weekly')

    def test_completed_stage_survives_other_stage_failure_and_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            j.init(root, '2026-10-27-weekly', 'weekly')
            token = j.begin(root, '2026-10-27-weekly', 'youtube')['token']
            j.finish(root, '2026-10-27-weekly', 'youtube', {
                'token': token, 'status': 'COMPLETE', 'summary': 'Verified channel: 4080 subscribers.',
                'sources': [{'ref': 'https://youtube.com/@abv_creative', 'checked_at': '2026-10-27T17:00:00+01:00'}]})
            token = j.begin(root, '2026-10-27-weekly', 'gmail')['token']
            j.finish(root, '2026-10-27-weekly', 'gmail', {
                'token': token, 'status': 'FAILED', 'summary': 'Mailbox not read.', 'sources': [],
                'failure_reason': 'Provider timeout', 'retryable': True})
            state = j.init(root, '2026-10-27-weekly', 'weekly')
            self.assertEqual(state['stages']['youtube']['status'], 'COMPLETE')
            report = j.assemble(root, '2026-10-27-weekly')
            self.assertIn('4080', report['text'])
            self.assertIn('Provider timeout', report['text'])
            self.assertEqual(report['status'], 'PARTIAL')
            self.assertEqual(len(state['stages']), 6)

    def test_retry_limit_and_stale_worker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.setup_run(root)
            first = j.begin(root, '2026-10-27-weekly', 'gmail')['token']
            with self.assertRaisesRegex(ValueError, 'already running'):
                j.begin(root, '2026-10-27-weekly', 'gmail')
            packet = {'token': first, 'status': 'FAILED', 'summary': 'Timeout', 'sources': [],
                      'failure_reason': 'Timeout', 'retryable': True}
            j.finish(root, '2026-10-27-weekly', 'gmail', packet)
            second = j.begin(root, '2026-10-27-weekly', 'gmail')['token']
            with self.assertRaisesRegex(ValueError, 'Stale'):
                j.finish(root, '2026-10-27-weekly', 'gmail', packet)
            packet['token'] = second
            j.finish(root, '2026-10-27-weekly', 'gmail', packet)
            with self.assertRaisesRegex(ValueError, 'exhausted'):
                j.begin(root, '2026-10-27-weekly', 'gmail')

    def test_delivery_requires_frozen_hash_and_exact_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.setup_run(root)
            receipt = j.prepare(root, '2026-10-27-weekly')
            self.assertEqual(receipt['status'], 'PREPARED')
            ref = 'https://chatgpt.com/c/6addc92d-6e14-83eb-bec4-2e1c7c428fbb?messageId=12345678-abcd-1234-abcd-123456789abc'
            with self.assertRaisesRegex(ValueError, 'mismatched'):
                j.ack(root, '2026-10-27-weekly', 'wrong', ref)
            j.ack(root, '2026-10-27-weekly', receipt['sha256'], ref)
            self.assertEqual(j.ack(root, '2026-10-27-weekly', receipt['sha256'], ref)['status'], 'PUBLISHED')
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                j.ack(root, '2026-10-27-weekly', receipt['sha256'], ref.replace('12345678', '22345678'))

    def test_corruption_never_reinitializes_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.setup_run(root)
            path = root / '2026-10-27-weekly/state.json'
            path.write_text('broken')
            with self.assertRaises(ValueError):
                self.setup_run(root)
            self.assertEqual(path.read_text(), 'broken')

    def test_empty_requires_evidence_and_failure_requires_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.setup_run(root)
            token = j.begin(root, '2026-10-27-weekly', 'jobs')['token']
            with self.assertRaisesRegex(ValueError, 'Evidence required'):
                j.finish(root, '2026-10-27-weekly', 'jobs', {'token': token, 'status': 'EMPTY', 'summary': 'Nothing'})
            with self.assertRaisesRegex(ValueError, 'failure_reason'):
                j.finish(root, '2026-10-27-weekly', 'jobs', {'token': token, 'status': 'BLOCKED', 'summary': 'No access'})

    def test_expired_stage_resumes_without_touching_other_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.setup_run(root)
            first = j.begin(root, '2026-10-27-weekly', 'udemy')['token']
            state = j.load(root, '2026-10-27-weekly')
            state['stages']['udemy']['attempts'][-1]['started_at'] = '2020-01-01T00:00:00Z'
            j.save(root, state)
            resumed = j.begin(root, '2026-10-27-weekly', 'udemy')
            self.assertNotEqual(first, resumed['token'])
            self.assertEqual(resumed['attempt'], 2)
            self.assertEqual(j.load(root, '2026-10-27-weekly')['stages']['udemy']['attempts'][0]['status'], 'INTERRUPTED')

    def test_published_partial_can_resume_only_missing_stage_without_losing_first_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            self.setup_run(root)
            token=j.begin(root,'2026-10-27-weekly','gmail')['token']
            j.finish(root,'2026-10-27-weekly','gmail',{'token':token,'status':'BLOCKED','summary':'Mailbox unavailable',
                'sources':[],'failure_reason':'Provider offline','retryable':True})
            first=j.prepare(root,'2026-10-27-weekly')
            ref='https://chatgpt.com/c/6addc92d-6e14-83eb-bec4-2e1c7c428fbb?messageId=12345678-abcd-1234-abcd-123456789abc'
            j.ack(root,'2026-10-27-weekly',first['sha256'],ref)
            original=Path(first['report_file']).read_bytes()
            j.resume(root,'2026-10-27-weekly','Provider recovered')
            token=j.begin(root,'2026-10-27-weekly','gmail')['token']
            j.finish(root,'2026-10-27-weekly','gmail',{'token':token,'status':'EMPTY','summary':'No new messages in checked scope',
                'sources':[{'ref':'https://mail.google.com/','checked_at':'2026-10-27T17:00:00Z'}]})
            second=j.prepare(root,'2026-10-27-weekly')
            self.assertNotEqual(first['report_file'],second['report_file'])
            self.assertEqual(original,Path(first['report_file']).read_bytes())
            self.assertEqual(j.load(root,'2026-10-27-weekly')['publication_history'][0]['chat_ref'],ref)

    def test_crashed_last_attempt_becomes_failed_and_can_still_publish_partial(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            self.setup_run(root)
            for _ in range(2):
                j.begin(root,'2026-10-27-weekly','gmail')
                state=j.load(root,'2026-10-27-weekly')
                state['stages']['gmail']['attempts'][-1]['started_at']='2020-01-01T00:00:00Z'
                j.save(root,state)
            with self.assertRaisesRegex(ValueError,'exhausted'):
                j.begin(root,'2026-10-27-weekly','gmail')
            self.assertEqual(j.load(root,'2026-10-27-weekly')['stages']['gmail']['status'],'FAILED')
            self.assertEqual(j.prepare(root,'2026-10-27-weekly')['status'],'PREPARED')

    def test_recovery_without_changed_result_cannot_republish(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            self.setup_run(root)
            first=j.prepare(root,'2026-10-27-weekly')
            ref='https://chatgpt.com/c/6addc92d-6e14-83eb-bec4-2e1c7c428fbb?messageId=12345678-abcd-1234-abcd-123456789abc'
            j.ack(root,'2026-10-27-weekly',first['sha256'],ref)
            j.resume(root,'2026-10-27-weekly','Provider recovered')
            with self.assertRaisesRegex(ValueError,'No changed stage result'):
                j.prepare(root,'2026-10-27-weekly')


if __name__ == '__main__':
    unittest.main()


import json
import hashlib

class BookAttachmentTests(unittest.TestCase):
 def packet(self,root):
  p=root/'review.json';p.write_text(json.dumps({'schema_version':'book-radar-owner-review/v1','run_id':'2026-11-02-weekly','as_of':'2026-11-02','production_authorized':False,'summary':'SYNTHETIC research recommendation, not a book','recommendations':[{'id':'x','title':'SYNTHETIC title','production_authorized':False}],'sources':[{'ref':'https://publisher.example','checked_at':'2026-11-02T12:00:00+01:00'}]}));return p
 def test_attach_to_prepared_run_preserves_stages_and_delivery(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);before=j.init(root,'2026-11-02-weekly','weekly');receipt=j.prepare(root,'2026-11-02-weekly');before=j.load(root,'2026-11-02-weekly');final=Path(receipt['report_file']).read_bytes()
   p=self.packet(root);r=j.attach_book_review(root,'2026-11-02-weekly',p);after=j.load(root,'2026-11-02-weekly')
   self.assertEqual(before['stages'],after['stages']);self.assertEqual(before['publication'],after['publication']);self.assertEqual(final,Path(receipt['report_file']).read_bytes());self.assertEqual(after['book_reviews'][0]['candidate_ids'],['x'])
   self.assertEqual(j.attach_book_review(root,'2026-11-02-weekly',p)['status'],'ALREADY_ATTACHED');self.assertEqual(len(j.load(root,'2026-11-02-weekly')['book_reviews']),1)
   self.assertIn('SYNTHETIC',j.assemble(root,'2026-11-02-weekly')['text']);self.assertEqual(hashlib.sha256(Path(r['path']).read_bytes()).hexdigest(),r['sha256'])
 def test_rejects_wrong_run_future_sources_authority_and_duplicate_ids(self):
  for field,value in [('run_id','2026-11-09-weekly'),('production_authorized',True),('sources',[{'ref':'https://publisher.example','checked_at':'2026-11-09T12:00:00Z'}]),('recommendations',[{'id':'x','title':'a','production_authorized':False}]*2)]:
   with tempfile.TemporaryDirectory() as t:
    root=Path(t);j.init(root,'2026-11-02-weekly','weekly');p=self.packet(root);d=json.loads(p.read_text());d[field]=value;p.write_text(json.dumps(d))
    with self.assertRaises(ValueError):j.attach_book_review(root,'2026-11-02-weekly',p)
    self.assertNotIn('book_reviews',j.load(root,'2026-11-02-weekly'))
