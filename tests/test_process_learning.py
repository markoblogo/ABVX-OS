"""Synthetic public-interface coverage for explicit private process learning."""
import copy, json, unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from abvx_harness.process_learning import build_packet, validate_packet, validate_outcome, digest, inspect_candidate, inspect_proposal


def outcome():
    return {'schemaVersion':1,'kind':'AbvxOsProcessOutcome','tenant':'abvx-os','runId':'synthetic-run','workflowId':'os.maintenance','workflowVersion':'v1','origin':'SYNTHETIC','startedAt':'2026-10-10T00:00:00Z','completedAt':'2026-10-10T00:00:10Z','status':'PASS','elapsedSeconds':10,'ownerMinutes':'UNKNOWN','reworkCount':0,'qualityGate':'PASS','safetyGate':'PASS','evidence':[{'ref':'synthetic-check','sha256':'a'*64}]}

class ProcessLearningTests(unittest.TestCase):
    def test_outcome_excludes_text_paths_and_false_metrics(self):
        for edit in ({'extra':'private manuscript'},{'elapsedSeconds':True},{'schemaVersion':True},{'startedAt':'2026-02-30T00:00:00Z'},{'elapsedSeconds':11},{'ownerMinutes':-1}):
            with self.subTest(edit=edit),self.assertRaises(ValueError):validate_outcome({**outcome(),**edit})
    def test_packet_is_exact_private_and_hash_bound(self):
        p=build_packet([outcome()],'synthetic-batch','2026-10-10T01:00:00Z');self.assertEqual(validate_packet(p),p)
        for edit in (lambda p:p.update(classification='public'),lambda p:p['payload'].update(schemaVersion=True),lambda p:p['payload']['outcomes'][0].update(ownerMinutes=0)):
            other=copy.deepcopy(p);edit(other)
            with self.assertRaises(ValueError):validate_packet(other)
    def test_duplicate_mixed_and_future_runs_rejected(self):
        a=outcome();b={**a,'runId':'synthetic-second','origin':'OBSERVED'}
        for rows,at in (([a,a],'2026-10-10T01:00:00Z'),([a,b],'2026-10-10T01:00:00Z'),([a],'2026-10-09T01:00:00Z')):
            with self.assertRaises(ValueError):build_packet(rows,'synthetic-batch',at)
    def candidate_fixture(self):
        p=build_packet([outcome()],'synthetic-batch','2026-10-10T01:00:00Z')
        context={'schemaVersion':1,'kind':'AbvxOsExperienceContext','tenant':'abvx-os','workflowId':'os.maintenance','query':'synthetic check','asOf':'2026-10-10T02:00:00Z','retrievalMode':'tfidf-lite','eligibleRuns':1,'results':[{'outcome':outcome(),'sourcePacketId':p['packetId'],'sourcePayloadDigest':digest(p['payload'])}],'authority':'none','executionAuthorized':False}
        candidate={'schemaVersion':1,'kind':'AbvxOsLearningCandidate','tenant':'abvx-os','status':'PENDING_TRIAL','workflowId':'os.maintenance','contextDigest':digest(context),'modelProvider':'local-ollama','model':'synthetic-model','change':'EARLY_INPUT_VALIDATION','rationale':'Validate inputs before a long run.','runIds':['synthetic-run'],'sources':[{'runId':'synthetic-run','sourcePacketId':p['packetId'],'sourcePayloadDigest':digest(p['payload'])}],'limitations':['MODEL_SUGGESTION_NOT_MEASURED_GAIN','INDEPENDENT_BASELINE_AND_HELD_OUT_TRIAL_REQUIRED'],'authority':'none','executionAuthorized':False,'ownerReviewRequired':True}
        candidate['candidateDigest']=digest(candidate);return context,candidate,[p]
    def test_candidate_acceptance_is_review_only_and_bound_to_current_evidence(self):
        ctx,c,packets=self.candidate_fixture();receipt=inspect_candidate(ctx,c,'v1',packets)
        self.assertEqual(receipt['status'],'PENDING_OWNER_TRIAL_REVIEW');self.assertFalse(receipt['executionAuthorized'])
        for edit in (lambda c:c.update(executionAuthorized=True),lambda c:c.update(runIds=['unseen']),lambda c:c.update(change='DELETE_FILES')):
            other=copy.deepcopy(c);edit(other);other['candidateDigest']=digest({k:v for k,v in other.items() if k!='candidateDigest'})
            with self.assertRaises(ValueError):inspect_candidate(ctx,other,'v1',packets)
        with self.assertRaises(ValueError):inspect_candidate(ctx,c,'v2',packets)

    def test_cortex_proposal_fixture_is_verified_without_promoting_synthetic_gain(self):
        root=Path(__file__).parent/'fixtures/process-learning'
        p=json.loads((root/'synthetic-packet.json').read_text());proposal=json.loads((root/'synthetic-proposal.json').read_text())
        result=inspect_proposal(p,proposal,'v1');self.assertEqual(result['status'],'BLOCKED_INSUFFICIENT_EVIDENCE')
        self.assertIn('SYNTHETIC_EVIDENCE_ONLY',result['reasons'])
        proposal['baseline']['elapsedSeconds']=99
        with self.assertRaises(ValueError):inspect_proposal(p,proposal,'v1')

    def test_record_hook_runs_read_only_check_once_and_retains_unknown_effort(self):
        from abvx_harness.process_learning import record_check
        from unittest.mock import patch
        from types import SimpleNamespace
        with TemporaryDirectory() as directory:
            root=Path(directory);target=root/'.tmp/learning/synthetic-record.json'
            with patch('abvx_harness.process_learning.subprocess.run',return_value=SimpleNamespace(stdout=b'SYNTHETIC PASS',stderr=b'',returncode=0)) as run:
                row=record_check(root,'contract-checks',target);self.assertEqual(run.call_count,1)
            self.assertEqual(row['ownerMinutes'],'UNKNOWN');self.assertEqual(row['safetyGate'],'UNKNOWN')
            self.assertTrue(target.is_file());self.assertTrue(target.with_suffix('.log').is_file())
            with self.assertRaises(ValueError):record_check(root,'contract-checks',target)

    def test_metric_diagnosis_is_recomputed_from_original_os_evidence(self):
        ctx,_,packets=self.candidate_fixture()
        material={'schemaVersion':1,'kind':'AbvxOsLearningCandidate','tenant':'abvx-os','status':'INSUFFICIENT_METRICS','workflowId':'os.maintenance','contextDigest':digest(ctx),'findings':[{'code':'OWNER_EFFORT_UNKNOWN','runIds':['synthetic-run']}],'sources':[{'runId':'synthetic-run','sourcePacketId':packets[0]['packetId'],'sourcePayloadDigest':digest(packets[0]['payload'])}],'authority':'none','executionAuthorized':False}
        candidate={**material,'candidateDigest':digest(material)}
        self.assertEqual(inspect_candidate(ctx,candidate,'v1',packets)['status'],'NEEDS_MEASUREMENT')
        for edit in (lambda m:m.update(findings=[]),lambda m:m['findings'][0].update(runIds=['unseen']),lambda m:m.update(executionAuthorized=True)):
            other=copy.deepcopy(material);edit(other)
            with self.assertRaises(ValueError):inspect_candidate(ctx,{**other,'candidateDigest':digest(other)},'v1',packets)
        with self.assertRaises(ValueError):inspect_candidate(ctx,candidate,'v2',packets)

class DurationRegressionTests(unittest.TestCase):
    def test_short_check_retains_measured_fractional_duration(self):
        from abvx_harness.process_learning import record_check
        from unittest.mock import patch
        from types import SimpleNamespace
        with TemporaryDirectory() as directory:
            root=Path(directory)
            with patch('abvx_harness.process_learning.subprocess.run',return_value=SimpleNamespace(stdout=b'PASS',stderr=b'',returncode=0)):
                row=record_check(root,'maintenance-tests',root/'.tmp/short-check.json')
            self.assertGreater(row['elapsedSeconds'],0)
            validate_outcome(row)
