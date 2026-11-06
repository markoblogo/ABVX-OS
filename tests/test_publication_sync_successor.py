"""Synthetic provider responses; no GitHub mutations or real journal writes."""
import copy
import unittest
from unittest.mock import patch
from abvx_harness.publication_learning import deployment_snapshot

A='a'*40
B='b'*40
PREFIX='repos/markoblogo/ABVXsite/'

class PublicationSyncSuccessor(unittest.TestCase):
    def setUp(self):
        release={'id':100,'sha':A,'environment':'Production','created_at':'2026-10-25T14:16:00Z'}
        latest={'id':101,'sha':B,'environment':'Production','created_at':'2026-10-25T14:18:00Z'}
        files=[{'filename':'content/writing-discovery.json','status':'modified'},{'filename':'public/content-index.json','status':'modified'},{'filename':'public/llms.txt','status':'modified'}]
        self.data={
            'deployments?environment=Production&per_page=1':[latest],
            'deployments?environment=Production&per_page=20':[latest,release],
            'deployments/100/statuses?per_page=1':[{'id':200,'state':'success','environment':'Production','created_at':'2026-10-25T14:16:01Z'}],
            'deployments/101/statuses?per_page=1':[{'id':201,'state':'success','environment':'Production','created_at':'2026-10-25T14:18:01Z'}],
            f'compare/{A}...{B}?per_page=100':{'status':'ahead','behind_by':0,'base_commit':{'sha':A},'merge_base_commit':{'sha':A},'total_commits':1,'commits':[{'sha':B}],'files':copy.deepcopy(files)},
            f'commits/{B}':{'sha':B,'parents':[{'sha':A}],'commit':{'message':'writing-sync: refresh discoveries'},'files':copy.deepcopy(files)},
            f'commits/{A}/pulls?per_page=100':[{'number':150,'merge_commit_sha':A,'merged_at':'2026-10-25T14:15:00Z','base':{'ref':'main','repo':{'full_name':'markoblogo/ABVXsite'}}}],
        }

    def snapshot(self,allow=True):
        def api(endpoint):
            self.assertTrue(endpoint.startswith(PREFIX))
            return copy.deepcopy(self.data[endpoint[len(PREFIX):]])
        with patch('abvx_harness.publication_learning.github_json',side_effect=api),patch('abvx_harness.publication_learning.utc',return_value='2026-10-25T14:30:00Z'):
            return deployment_snapshot(A,allow_metadata_sync=allow)

    def test_successful_release_followed_by_metadata_sync_retains_both_identities(self):
        value=self.snapshot()
        self.assertEqual(value['sha'],A)
        self.assertEqual(value['deploymentId'],100)
        self.assertEqual(value['currentProductionSha'],B)
        self.assertEqual(value['metadataOnlySuccessor']['deploymentId'],101)
        self.assertEqual(value['verificationMode'],'SUCCESSFUL_RELEASE_WITH_METADATA_ONLY_SUCCESSOR')
        self.assertEqual(value,self.snapshot())

    def test_default_verification_remains_strict(self):
        with self.assertRaises(ValueError):self.snapshot(allow=False)

    def test_latest_exact_release_keeps_original_strict_path(self):
        self.data['deployments?environment=Production&per_page=1']=[self.data['deployments?environment=Production&per_page=20'][1]]
        value=self.snapshot();self.assertEqual(value['sha'],A)
        self.assertNotIn('metadataOnlySuccessor',value)

    def test_code_or_content_change_is_rejected_even_if_aggregate_diff_hides_it(self):
        for filename in ['src/app/writing/page.tsx','content/writing/post.md','public/media/cover.webp']:
            with self.subTest(filename=filename):
                old=copy.deepcopy(self.data[f'commits/{B}']['files'])
                self.data[f'commits/{B}']['files']=[{'filename':filename,'status':'modified'}]
                with self.assertRaises(ValueError):self.snapshot()
                self.data[f'commits/{B}']['files']=old

    def test_deleted_renamed_missing_and_unknown_files_fail_closed(self):
        for files in [[],[{'filename':'public/llms.txt','status':'removed'}],[{'filename':'public/llms.txt','status':'renamed','previous_filename':'content/writing/post.md'}],[{'filename':'other.json','status':'modified'}]]:
            with self.subTest(files=files):
                self.data[f'commits/{B}']['files']=files
                with self.assertRaises(ValueError):self.snapshot()

    def test_pending_or_failed_original_and_successor_are_rejected(self):
        for endpoint in ['deployments/100/statuses?per_page=1','deployments/101/statuses?per_page=1']:
            for state in ['pending','failure']:
                self.data[endpoint][0]['state']=state
                with self.assertRaises(ValueError):self.snapshot()
            self.data[endpoint][0]['state']='success'

    def test_diverged_history_or_merge_commit_cannot_qualify(self):
        self.data[f'compare/{A}...{B}?per_page=100']['status']='diverged'
        with self.assertRaises(ValueError):self.snapshot()
        self.data[f'compare/{A}...{B}?per_page=100']['status']='ahead'
        self.data[f'commits/{B}']['parents']=[{'sha':A},{'sha':'c'*40}]
        with self.assertRaises(ValueError):self.snapshot()

    def test_incomplete_or_oversized_commit_comparison_is_rejected(self):
        for count in [2,11]:
            self.data[f'compare/{A}...{B}?per_page=100']['total_commits']=count
            with self.assertRaises(ValueError):self.snapshot()

    def test_missing_original_or_changed_latest_inventory_is_rejected(self):
        self.data['deployments?environment=Production&per_page=20']=[]
        with self.assertRaises(ValueError):self.snapshot()

    def test_future_successor_and_non_sync_commit_are_rejected(self):
        self.data[f'commits/{B}']['commit']['message']='change authored content'
        with self.assertRaises(ValueError):self.snapshot()
        self.data[f'commits/{B}']['commit']['message']='writing-sync: refresh'
        self.data['deployments/101/statuses?per_page=1'][0]['created_at']='2026-10-26T14:18:01Z'
        with self.assertRaises(ValueError):self.snapshot()

if __name__=='__main__':unittest.main()
