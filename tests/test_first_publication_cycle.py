"""Deployment/source binding tests use only temporary, observed-shaped fixtures."""
import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from abvx_harness.process_learning import build_packet, digest, inspect_candidate

ROOT = Path(__file__).resolve().parents[1]


class FirstPublicationCycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.site = self.root / 'site'
        self.site.mkdir()
        for args in (['init', '-q'], ['config', 'user.name', 'Synthetic'],
                     ['config', 'user.email', 'synthetic@example.invalid']):
            subprocess.run(['git', *args], cwd=self.site, check=True, capture_output=True)
        (self.site / 'post.md').write_text('Synthetic source')
        subprocess.run(['git', 'add', 'post.md'], cwd=self.site, check=True)
        subprocess.run(['git', 'commit', '-qm', 'Synthetic source'], cwd=self.site, check=True)
        self.sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=self.site).decode().strip()
        self.directory = self.root / '.tmp/publication-learning/synthetic-cycle'
        self.directory.mkdir(parents=True)
        self.row = json.loads((ROOT / 'tests/fixtures/process-learning/synthetic-packet.json').read_text())['payload']['outcomes'][0]
        self.row.update(runId='synthetic-cycle', workflowId='site.content.publish',
                        workflowVersion='publication-v1', origin='OBSERVED', status='PASS',
                        qualityGate='PASS', safetyGate='PASS', ownerMinutes='UNKNOWN')
        self.batch = build_packet([self.row], 'publication:synthetic-cycle', self.row['completedAt'])
        result = {'outcome': self.row, 'sourcePacketId': self.batch['packetId'], 'sourcePayloadDigest': digest(self.batch['payload'])}
        self.context = {'schemaVersion': 1, 'kind': 'AbvxOsExperienceContext', 'tenant': 'abvx-os',
                        'workflowId': 'site.content.publish', 'query': 'site.content.publish',
                        'asOf': '2026-10-10T02:00:00Z', 'retrievalMode': 'tfidf-lite',
                        'eligibleRuns': 1, 'results': [result], 'authority': 'none', 'executionAuthorized': False}
        sources = [{'runId': self.row['runId'], 'sourcePacketId': result['sourcePacketId'], 'sourcePayloadDigest': result['sourcePayloadDigest']}]
        candidate = {'schemaVersion': 1, 'kind': 'AbvxOsLearningCandidate', 'tenant': 'abvx-os',
                     'status': 'INSUFFICIENT_METRICS', 'workflowId': 'site.content.publish',
                     'contextDigest': digest(self.context), 'findings': [{'code': 'OWNER_EFFORT_UNKNOWN', 'runIds': [self.row['runId']]}],
                     'sources': sources, 'authority': 'none', 'executionAuthorized': False}
        candidate['candidateDigest'] = digest(candidate)
        self.review = inspect_candidate(self.context, candidate, 'publication-v1', [self.batch])
        for name, value in [('outcome', self.row), ('batch', self.batch), ('cortex-review', self.review)]:
            (self.directory / (name + '.json')).write_text(json.dumps(value))
        self.cortex = self.root / 'cortex'
        context = self.cortex / 'data/abvx-os/publications/synthetic-cycle/context.json'
        context.parent.mkdir(parents=True)
        context.write_text(json.dumps(self.context))
        context.with_name('candidate.json').write_text(json.dumps(candidate))
        self.item = {'enrichment': {'canonical_path': '/writing/synthetic-cycle'}}
        self.deployment = {'id': 123, 'sha': self.sha, 'environment': 'Production',
                           'created_at': '2026-10-10T00:00:00Z'}
        self.status = {'id': 456, 'state': 'success', 'environment': 'Production',
                       'created_at': '2026-10-10T00:00:01Z'}
        self.merge = {'number': 54, 'merged_at': '2026-10-10T00:00:00Z', 'merge_commit_sha': self.sha, 'base': {'ref': 'main', 'repo': {'full_name': 'markoblogo/ABVXsite'}}}
        self.git_run = subprocess.run

    def run_gate(self, deployment=None, status=None, second_deployment=None, change_source=False):
        from abvx_harness.publication_learning import verify_first_cycle
        selected = copy.deepcopy(deployment or self.deployment)
        state = copy.deepcopy(status or self.status)
        calls = 0
        def run(args, **kwargs):
            nonlocal calls
            if args[0] != 'gh':
                return self.git_run(args, **kwargs)
            endpoint = args[-1]
            if '/pulls?' in endpoint:
                payload = [self.merge]
            elif '/statuses?' in endpoint:
                payload = [state]
            else:
                calls += 1
                if calls > 1 and change_source: (self.site / 'post.md').write_text('Changed while probing')
                payload = [second_deployment if calls > 1 and second_deployment else selected]
            return SimpleNamespace(stdout=json.dumps(payload).encode(), returncode=0)
        with patch('abvx_harness.publication_learning.subprocess.run', side_effect=run), \
             patch('abvx_harness.publication_learning.complete_publication', return_value={'status': 'RECORDED'}), \
             patch('abvx_harness.publication_learning.transfer_publication', return_value=self.review), \
             patch('abvx_harness.publication_learning._load_item', return_value=self.item), \
             patch('abvx_harness.publication_learning.fetch_production', return_value=b'synthetic-live-html'), \
             patch('abvx_harness.publication_learning.validate_live_html', return_value='a' * 64):
            return verify_first_cycle(self.root, 'synthetic-cycle', self.site, self.cortex)

    def test_first_cycle_retains_source_deployment_and_return_bindings(self):
        receipt = self.run_gate()
        self.assertEqual(receipt['status'], 'VERIFIED')
        self.assertEqual(receipt['deployedSha'], self.sha)
        self.assertEqual(receipt['sourcePacketDigest'], digest(self.batch))
        self.assertEqual(receipt['osReviewDigest'], digest(self.review))
        self.assertEqual(receipt['productionHtmlDigest'], 'a' * 64)
        self.assertFalse(receipt['executionAuthorized'])
        self.assertEqual(receipt, json.loads((self.directory / 'first-cycle.json').read_text()))
        self.assertEqual(receipt, self.run_gate())

    def test_unknown_owner_effort_allows_transport_but_never_claims_savings(self):
        self.review.update(status='NEEDS_MEASUREMENT')
        receipt = self.run_gate()
        self.assertEqual(receipt['status'], 'VERIFIED')
        self.assertFalse(receipt['executionAuthorized'])

    def test_wrong_sha_preview_failed_or_changed_deployments_cannot_pass(self):
        for deployment, status, second in [
            ({**self.deployment, 'sha': 'b' * 40}, self.status, None),
            ({**self.deployment, 'environment': 'Preview'}, self.status, None),
            (self.deployment, {**self.status, 'state': 'in_progress'}, None),
            (self.deployment, {**self.status, 'environment': 'Preview'}, None),
            (self.deployment, self.status, {**self.deployment, 'id': 789}),
        ]:
            with self.subTest(deployment=deployment, status=status), self.assertRaises(ValueError):
                self.run_gate(deployment, status, second)
            self.assertFalse((self.directory / 'first-cycle.json').exists())

    def test_synthetic_missing_return_or_uncommitted_source_cannot_pass(self):
        outcome_file = self.directory / 'outcome.json'
        outcome_file.write_text(json.dumps({**self.row, 'origin': 'SYNTHETIC'}))
        with self.assertRaises(ValueError): self.run_gate()
        outcome_file.write_text(json.dumps(self.row))
        review_file = self.directory / 'cortex-review.json'
        review_file.unlink()
        with self.assertRaises(ValueError): self.run_gate()
        review_file.write_text(json.dumps(self.review))
        (self.site / 'post.md').write_text('Changed after checks')
        with self.assertRaises(ValueError): self.run_gate()
        self.assertFalse((self.directory / 'first-cycle.json').exists())

    def test_unmerged_or_foreign_commit_cannot_satisfy_merge_sha_gate(self):
        for edit in ({'merged_at': None}, {'merge_commit_sha': 'b' * 40},
                     {'base': {'ref': 'other', 'repo': {'full_name': 'markoblogo/ABVXsite'}}}):
            saved = copy.deepcopy(self.merge)
            self.merge.update(edit)
            with self.assertRaises(ValueError): self.run_gate()
            self.merge = saved
            self.assertFalse((self.directory / 'first-cycle.json').exists())

    def test_unrelated_provider_description_change_is_not_a_new_rollout(self):
        receipt = self.run_gate(second_deployment={**self.deployment, 'description': 'Updated by provider'})
        self.assertEqual(receipt['status'], 'VERIFIED')

    def test_source_change_during_provider_probe_cannot_be_accepted(self):
        with self.assertRaises(ValueError): self.run_gate(change_source=True)
        self.assertFalse((self.directory / 'first-cycle.json').exists())

    def test_changed_return_context_cannot_be_bound_to_old_review(self):
        context = self.cortex / 'data/abvx-os/publications/synthetic-cycle/context.json'
        context.write_text(json.dumps({**self.context, 'query': 'Changed after return'}))
        with self.assertRaises(ValueError): self.run_gate()
        self.assertFalse((self.directory / 'first-cycle.json').exists())

    def test_retry_preserves_original_receipt_after_unrelated_provider_metadata_changes(self):
        original = self.run_gate()
        retried = self.run_gate(deployment={**self.deployment, 'description': 'Updated by provider'})
        self.assertEqual(retried, original)
