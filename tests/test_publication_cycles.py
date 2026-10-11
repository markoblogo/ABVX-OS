"""Cycle measurement uses temporary state, never real publications or Cortex history."""
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


class PublicationCycles(unittest.TestCase):
    def test_batch_closeout_records_total_command_to_production_once(self):
        from abvx_harness.publication_learning import begin_cycle, complete_cycle, CHECKS
        from abvx_harness.process_learning import validate_packet, elapsed_only
        with TemporaryDirectory() as temp:
            root = Path(temp)
            with patch('abvx_harness.publication_learning.utc', return_value='2026-10-11T10:00:00.000Z'):
                begin_cycle(root, 'cycle-test', ['post-one', 'post-two'])
            def verified(root, item_id, site, **kwargs):
                item = {'enrichment':{'canonical_path':'/writing/'+item_id}, 'id':item_id}
                session = {'origin':'OBSERVED','startedAt':'2026-10-11T10:00:10.000Z',
                           'workload':{'surface':'writing','tier':'standard','assets':1,'video':False}}
                checks = {'treeDigest':'a'*64,'buildMode':'default','checks':[{'ref':'check:'+n,'sha256':'a'*64} for n in CHECKS]}
                return item,session,checks,site
            with patch('abvx_harness.publication_learning.verify_publication_inputs',side_effect=verified), \
                 patch('abvx_harness.publication_learning.tree_digest',return_value='a'*64), \
                 patch('abvx_harness.publication_learning.clean_site_sha',return_value='b'*40), \
                 patch('abvx_harness.publication_learning.deployment_snapshot',return_value={'sha':'b'*40,'state':'success'}), \
                 patch('abvx_harness.publication_learning.fetch_production',return_value=b'public HTML'), \
                 patch('abvx_harness.publication_learning.validate_live_html',return_value='c'*64), \
                 patch('abvx_harness.publication_learning._approval_fingerprint',return_value='d'*64), \
                 patch('abvx_harness.publication_learning.utc',return_value='2026-10-11T10:01:40.000Z'):
                first=complete_cycle(root,'cycle-test',root,rework_count=1)
                self.assertEqual(complete_cycle(root,'cycle-test',root,rework_count=1),first)
                with self.assertRaises(ValueError):complete_cycle(root,'cycle-test',root,rework_count=2)
                with patch('abvx_harness.publication_learning.verify_publication_inputs',side_effect=ValueError('stale member')):
                    with self.assertRaises(ValueError):complete_cycle(root,'cycle-test',root,rework_count=1)
            row=json.loads((root/'.tmp/publication-learning/cycle-test/outcome.json').read_text())
            self.assertEqual(row['elapsedSeconds'],100)
            self.assertEqual(row['ownerMinutes'],'UNKNOWN')
            self.assertTrue(elapsed_only(row))
            packet=validate_packet(json.loads((root/'.tmp/publication-learning/cycle-test/batch.json').read_text()))
            self.assertEqual(len(packet['payload']['outcomes']),1)
            for item in ('post-one','post-two'):
                self.assertFalse((root/'.tmp/publication-learning'/item/'outcome.json').exists())

    def test_begin_precedes_intake_and_reserves_a_single_independent_batch(self):
        from abvx_harness.publication_learning import begin_cycle
        with TemporaryDirectory() as temp:
            root = Path(temp)
            args = (root, 'cycle-test', ['post-one', 'post-two'])
            with patch('abvx_harness.publication_learning.utc', return_value='2026-10-11T10:00:00.000Z'):
                first = begin_cycle(*args)
            self.assertEqual(first['mode'], 'batch')
            self.assertEqual(first['startedAt'], '2026-10-11T10:00:00.000Z')
            self.assertEqual(begin_cycle(*args), first)
            with self.assertRaises(ValueError):
                begin_cycle(root, 'other-cycle', ['post-two'])
            with self.assertRaises(ValueError):
                begin_cycle(root, 'cycle-test', ['post-one'])
            self.assertFalse((root / '.tmp/publication-learning/cycle-test/outcome.json').exists())

    def test_begin_rejects_retroactive_measurement(self):
        from abvx_harness.publication_learning import begin_cycle
        with TemporaryDirectory() as temp:
            root = Path(temp)
            item = root / '.tmp/publication-learning/post-one'
            item.mkdir(parents=True)
            (item / 'session.json').write_text('{}')
            with self.assertRaises(ValueError):
                begin_cycle(root, 'cycle-test', ['post-one'])

    def test_concurrent_cycles_cannot_claim_the_same_material(self):
        from abvx_harness.publication_learning import begin_cycle
        from concurrent.futures import ThreadPoolExecutor
        with TemporaryDirectory() as temp:
            root=Path(temp)
            def attempt(run):
                try:begin_cycle(root,run,['post-one']);return True
                except ValueError:return False
            with ThreadPoolExecutor(max_workers=2) as pool:
                self.assertEqual(sum(pool.map(attempt,['cycle-one','cycle-two'])),1)

    def test_legacy_member_closeout_cannot_double_count_a_cycle(self):
        from abvx_harness.publication_learning import begin_cycle, complete_publication
        with TemporaryDirectory() as temp:
            root=Path(temp);begin_cycle(root,'cycle-one',['post-one'])
            with self.assertRaisesRegex(ValueError,'independent cycle'):
                complete_publication(root,'post-one',root,rework_count=0)

    def test_new_cycle_returns_from_an_isolated_cortex_with_unknown_owner_effort(self):
        import shutil, subprocess
        from datetime import datetime, timezone, timedelta
        from abvx_harness.process_learning import ELAPSED_POLICY, build_packet, digest, inspect_candidate
        source=Path('/tmp/cortex-publication-elapsed')
        if not source.is_dir():self.skipTest('Optional isolated Cortex source unavailable')
        with TemporaryDirectory() as temp:
            root=Path(temp).resolve();cortex=root/'cortex';cortex.mkdir()
            for part in ('src','config'):shutil.copytree(source/part,cortex/part)
            shutil.copy2(source/'package.json',cortex/'package.json')
            end=datetime.now(timezone.utc).replace(microsecond=0)
            row={'schemaVersion':1,'kind':'AbvxOsProcessOutcome','tenant':'abvx-os','runId':'synthetic-cycle',
                 'workflowId':'site.content.publish','workflowVersion':'publication-v2-baseline','origin':'OBSERVED',
                 'startedAt':(end-timedelta(seconds=3)).isoformat().replace('+00:00','Z'),
                 'completedAt':end.isoformat().replace('+00:00','Z'),'status':'PASS','elapsedSeconds':3,
                 'ownerMinutes':'UNKNOWN','reworkCount':0,'qualityGate':'PASS','safetyGate':'PASS',
                 'evidence':[ELAPSED_POLICY,{'ref':'cycle:synthetic-cycle','sha256':'b'*64},
                             {'ref':'workload:publication-profile','sha256':'c'*64}]}
            packet=build_packet([row],'publication:synthetic-cycle',row['completedAt'])
            file=root/'packet.json';file.write_text(json.dumps(packet))
            target=cortex/'data/abvx-os/publications/synthetic-cycle'
            args=['node','src/abvx-os-receive.mjs','--packet',str(file),'--context-out',str(target/'context.json'),'--candidate-out',str(target/'candidate.json')]
            for _ in range(2):
                process=subprocess.run(args,cwd=cortex,capture_output=True,text=True)
                self.assertEqual(process.returncode,0,process.stderr)
            context=json.loads((target/'context.json').read_text());candidate=json.loads((target/'candidate.json').read_text())
            self.assertEqual(inspect_candidate(context,candidate,row['workflowVersion'],[packet])['status'],'RECORDED_READY_FOR_ANALYSIS')
            self.assertEqual(len((cortex/'data/abvx-os/ledger.jsonl').read_text().splitlines()),1)
