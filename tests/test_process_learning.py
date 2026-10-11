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

class ElapsedPolicyTests(unittest.TestCase):
    def test_publication_elapsed_policy_keeps_unknown_effort_and_checks_independence(self):
        from abvx_harness.process_learning import ELAPSED_POLICY, elapsed_only
        row = {**outcome(), 'workflowId':'site.content.publish', 'workflowVersion':'publication-v2-baseline',
               'evidence':[ELAPSED_POLICY, {'ref':'cycle:synthetic-run','sha256':'b'*64},
                           {'ref':'workload:publication-profile','sha256':'c'*64},{'ref':'production:deployed-sha','sha256':'d'*64}]}
        self.assertTrue(elapsed_only(validate_outcome(row)))
        for change in ({'workflowId':'book.production'}, {'workflowVersion':'publication-v1'},
                       {'evidence':[{'ref':ELAPSED_POLICY['ref'],'sha256':'0'*64}]}):
            with self.assertRaises(ValueError): validate_outcome({**row, **change})
        ctx,_,_ = ProcessLearningTests().candidate_fixture()
        packet = build_packet([row], 'synthetic-batch', '2026-10-10T01:00:00Z')
        ctx.update(workflowId='site.content.publish',results=[{'outcome':row,'sourcePacketId':packet['packetId'],'sourcePayloadDigest':digest(packet['payload'])}])
        material={'schemaVersion':1,'kind':'AbvxOsLearningCandidate','tenant':'abvx-os','status':'READY_FOR_ANALYSIS','workflowId':ctx['workflowId'],'contextDigest':digest(ctx),'sources':[{'runId':row['runId'],'sourcePacketId':packet['packetId'],'sourcePayloadDigest':digest(packet['payload'])}],'authority':'none','executionAuthorized':False}
        result=inspect_candidate(ctx,{**material,'candidateDigest':digest(material)},row['workflowVersion'],[packet])
        self.assertEqual(result['status'],'RECORDED_READY_FOR_ANALYSIS')
        self.assertEqual(row['ownerMinutes'],'UNKNOWN')

    def test_cross_runtime_proposal_recomputes_latency_and_rejects_correlated_cycles(self):
        import subprocess
        from abvx_harness.process_learning import ELAPSED_POLICY
        cortex=Path('/tmp/cortex-publication-elapsed')
        if not cortex.is_dir():self.skipTest('Optional isolated Cortex source unavailable')
        rows=[]
        for i in range(10):
            r={**outcome(),'runId':f'synthetic-{i}','workflowId':'site.content.publish',
               'workflowVersion':'publication-v2-baseline' if i<5 else 'publication-v2-early-input',
               'origin':'OBSERVED','elapsedSeconds':10 if i<5 else 5,
               'completedAt':'2026-10-10T00:00:10Z' if i<5 else '2026-10-10T00:00:05Z',
               'evidence':[ELAPSED_POLICY,{'ref':f'cycle:synthetic-{i}','sha256':digest({'cycle':i})},
                           {'ref':'workload:publication-profile','sha256':'c'*64},{'ref':'production:deployed-sha','sha256':'d'*64}]}
            from datetime import datetime,timezone,timedelta
            start=datetime(2026,10,10,tzinfo=timezone.utc)+timedelta(seconds=i*20)
            r.update(startedAt=start.isoformat(timespec='milliseconds').replace('+00:00','Z'),completedAt=(start+timedelta(seconds=r['elapsedSeconds'])).isoformat(timespec='milliseconds').replace('+00:00','Z'))
            r['evidence'][-1]['sha256']=digest({'release':i})
            rows.append(r)
        candidate={'proposalId':'synthetic-latency','workflowId':'site.content.publish','baselineVersion':'publication-v2-baseline','candidateVersion':'publication-v2-early-input','change':'EARLY_INPUT_VALIDATION','baselineRunIds':[r['runId'] for r in rows[:5]],'heldOutRunIds':[r['runId'] for r in rows[5:]]}
        series={'schemaVersion':1,'kind':'AbvxPublicationTrialSeries','seriesId':'synthetic-series','createdAt':'2026-10-09T00:00:00Z',**{k:candidate[k] for k in ('baselineVersion','candidateVersion','change','baselineRunIds','heldOutRunIds')}}
        for r in rows:r['evidence'].append({'ref':'trial:publication-series','sha256':digest(series)})
        # Observed-shaped test evidence never touches a ledger or canonical runtime.
        cases=[(None,'PENDING_OWNER_REVIEW'),
               (lambda r:r.append({**r[0],'runId':'synthetic-extra','status':'FAIL','evidence':[ELAPSED_POLICY,{'ref':'cycle:synthetic-extra','sha256':digest({'cycle':'extra'})},*r[0]['evidence'][2:]]}),'BLOCKED_INSUFFICIENT_EVIDENCE'),
               (lambda r:r[5].update(startedAt='2026-10-10T00:00:00.000Z',completedAt='2026-10-10T00:00:05.000Z'),'BLOCKED_INSUFFICIENT_EVIDENCE'),
               (lambda r:r[5]['evidence'][3].update(sha256=r[0]['evidence'][3]['sha256']),'BLOCKED_INSUFFICIENT_EVIDENCE'),
               (lambda r:r[5]['evidence'][1].update(sha256=r[0]['evidence'][1]['sha256']),'BLOCKED_INSUFFICIENT_EVIDENCE'),
               (lambda r:r[5].update(safetyGate='FAIL'),'BLOCKED_INSUFFICIENT_EVIDENCE'),
               (lambda r:[row.update(reworkCount=1) for row in r[5:]],'BLOCKED_INSUFFICIENT_EVIDENCE'),
               (lambda r:r[5]['evidence'][2].update(sha256='d'*64),'BLOCKED_INSUFFICIENT_EVIDENCE')]
        script="import {readFileSync} from 'node:fs'; import {evaluateOptimization} from './src/abvx-os-learning.mjs'; console.log(JSON.stringify(evaluateOptimization(JSON.parse(readFileSync(0,'utf8')))));"
        for edit,status in cases:
            altered=copy.deepcopy(rows)
            if edit:edit(altered)
            packet=build_packet(altered,'synthetic-latency','2026-10-10T01:00:00Z')
            process=subprocess.run(['node','--input-type=module','-e',script],cwd=cortex,input=json.dumps({'packet':packet,'candidate':candidate,'series':series}),text=True,capture_output=True,check=True)
            proposal=json.loads(process.stdout)
            self.assertEqual(inspect_proposal(packet,proposal,'publication-v2-baseline',series)['status'],status)
        equal_series={**series,'createdAt':rows[0]['startedAt']}
        altered=copy.deepcopy(rows)
        for row in altered:row['evidence'][-1]['sha256']=digest(equal_series)
        packet=build_packet(altered,'synthetic-latency','2026-10-10T01:00:00Z')
        process=subprocess.run(['node','--input-type=module','-e',script],cwd=cortex,input=json.dumps({'packet':packet,'candidate':candidate,'series':equal_series}),text=True,capture_output=True,check=True)
        self.assertEqual(inspect_proposal(packet,json.loads(process.stdout),'publication-v2-baseline',equal_series)['status'],'BLOCKED_INSUFFICIENT_EVIDENCE')

    def test_full_cycle_run_identifier_fits_evidence_refs(self):
        from abvx_harness.process_learning import ELAPSED_POLICY
        for length in (114,115,120):
            run='r'*length
            row={**outcome(),'runId':run,'workflowId':'site.content.publish','workflowVersion':'publication-v2-baseline','evidence':[ELAPSED_POLICY,{'ref':'cycle:'+run,'sha256':'b'*64},{'ref':'workload:publication-profile','sha256':'c'*64},{'ref':'production:deployed-sha','sha256':'d'*64}]}
            self.assertEqual(validate_outcome(row),row)

    def test_os_rejects_a_digest_valid_proposal_for_the_wrong_intervention(self):
        root=Path(__file__).parent/'fixtures/process-learning'
        packet=json.loads((root/'synthetic-packet.json').read_text())
        proposal=json.loads((root/'synthetic-proposal.json').read_text())
        proposal.update(workflowId='site.content.publish',baselineVersion='publication-v2-baseline',candidateVersion='publication-v2-reuse-context',change='EARLY_INPUT_VALIDATION')
        proposal['proposalDigest']=digest({k:v for k,v in proposal.items() if k!='proposalDigest'})
        with self.assertRaisesRegex(ValueError,'intervention'):inspect_proposal(packet,proposal,'publication-v2-baseline')
