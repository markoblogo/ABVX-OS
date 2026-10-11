import json,shutil,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from abvx_harness.content_ops import prepare_content_item,approve_content_item,publish_content_item
from abvx_harness.harness import ValidationError
ROOT=Path(__file__).resolve().parents[1]
class PublicationLearningTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
  for rel in ('schemas','registries','content/fixtures'):shutil.copytree(ROOT/rel,self.root/rel)
 def prepared(self):return prepare_content_item(self.root,'content/fixtures/abvx-working-story-dry-run.json')
 def test_preparation_starts_private_session_but_handoff_is_not_success(self):
  item=self.prepared();p=self.root/'.tmp/publication-learning'/item['id']/'session.json'
  self.assertTrue(p.is_file());self.assertEqual(json.loads(p.read_text())['origin'],'SYNTHETIC')
  approve_content_item(self.root,item['id']);publish_content_item(self.root,item['id'])
  self.assertFalse((p.parent/'outcome.json').exists())
 def test_no_approval_or_preview_can_close_a_publication(self):
  from abvx_harness.publication_learning import complete_publication
  item=self.prepared()
  with self.assertRaises((ValueError,ValidationError)):
   complete_publication(self.root,item['id'],self.root/'site',owner_minutes='UNKNOWN',rework_count=0)
 def test_checks_are_bound_to_exact_site_tree(self):
  from abvx_harness.publication_learning import tree_digest
  site=self.root/'site';site.mkdir();(site/'content').mkdir();(site/'content/post.md').write_text('first')
  with patch('abvx_harness.publication_learning.tracked_files',return_value=['content/post.md']):
   before=tree_digest(site);(site/'content/post.md').write_text('changed');self.assertNotEqual(before,tree_digest(site))
 def test_live_probe_rejects_preview_redirect_wrong_body_and_missing_canonical(self):
  from abvx_harness.publication_learning import validate_live_html
  item={'title':'Synthetic title','enrichment':{'canonical_path':'/writing/synthetic'},'payload':{'body_lines':['A distinctive synthetic paragraph for a local test only.']}}
  valid=b'<link rel="canonical" href="https://abvx.xyz/writing/synthetic"><h1>Synthetic title</h1><p>A distinctive synthetic paragraph for a local test only.</p>'
  validate_live_html(item,valid)
  for html in (valid.replace(b'https://abvx.xyz',b'https://preview.vercel.app'),valid.replace(b'distinctive',b'wrong'),valid.replace(b'rel="canonical"',b'rel="other"')):
   with self.assertRaises(ValueError):validate_live_html(item,html)
 def test_scoped_qa_covers_member_and_keeps_full_and_publication_workloads_distinct(self):
  from abvx_harness.publication_learning import validate_qa_scope,qa_profile
  item={'enrichment':{'canonical_path':'/writing/post'}}
  scope={'profile':'publication-v1','base':'a'*40,'routes':['/writing/post']}
  validate_qa_scope(scope,item)
  validate_qa_scope(None,item)
  validate_qa_scope({'profile':'full'},item)
  for invalid in ({**scope,'routes':['/writing/other']},{**scope,'base':'bad'},{'profile':'unknown'}):
   with self.assertRaises(ValueError):validate_qa_scope(invalid,item)
  self.assertEqual(qa_profile({}),{})
  self.assertNotEqual(qa_profile({'qaScope':scope}),qa_profile({'qaScope':{'profile':'full'}}))
 def test_closeout_records_metrics_and_export_but_never_preview(self):
  from abvx_harness.publication_learning import check_publication,complete_publication
  from types import SimpleNamespace
  item=self.prepared();approve_content_item(self.root,item['id']);publish_content_item(self.root,item['id'])
  site=self.root/'site';site.mkdir();(site/'source.md').write_text('synthetic')
  directory=self.root/'.tmp/publication-learning'/item['id'];session=json.loads((directory/'session.json').read_text())
  live=('<link rel="canonical" href="https://abvx.xyz'+item['enrichment']['canonical_path']+'"><h1>'+item['title']+'</h1>'+''.join('<p>'+line+'</p>' for block in item['payload']['body_lines'] for line in block.split('\n\n'))).encode()
  from abvx_harness.publication_learning import CHECKS,tree_digest
  import hashlib
  logs=site/'exports/editorial-checks';logs.mkdir(parents=True)
  def fake_release(*args,**kwargs):
   for name in CHECKS:(logs/f"{name.replace(':','-')}.log").write_bytes(b'SYNTHETIC CHECK PASS')
   receipt={'result':'PASS','treeDigest':tree_digest(site),'buildMode':'default','checks':[{'name':n,'status':'PASS','sha256':hashlib.sha256(b'SYNTHETIC CHECK PASS').hexdigest()} for n in CHECKS]}
   (logs/'receipt.json').write_text(json.dumps(receipt));return SimpleNamespace(stdout=b'',stderr=b'',returncode=0)
  with patch('abvx_harness.publication_learning.verified_site',return_value=site),patch('abvx_harness.publication_learning.tracked_files',return_value=['source.md']),patch('abvx_harness.publication_learning.subprocess.run',side_effect=fake_release) as runner:
   self.assertEqual(check_publication(self.root,item['id'],site)['status'],'PASS')
   self.assertEqual(runner.call_count,1)
   check_publication(self.root,item['id'],site,reuse_checks=True);self.assertEqual(runner.call_count,1)
   with patch('abvx_harness.publication_learning.fetch_production',return_value=b'<h1>preview</h1>'):
    with self.assertRaises(ValueError):complete_publication(self.root,item['id'],site,owner_minutes=2,rework_count=1)
   self.assertFalse((directory/'outcome.json').exists())
   with patch('abvx_harness.publication_learning.fetch_production',return_value=live):
    result=complete_publication(self.root,item['id'],site,owner_minutes=2,rework_count=1)
    self.assertEqual(result['status'],'RECORDED');self.assertEqual(result['origin'],'SYNTHETIC')
    row=json.loads((directory/'outcome.json').read_text());self.assertEqual(row['ownerMinutes'],2);self.assertEqual(row['reworkCount'],1)
    before=(directory/'outcome.json').read_bytes();complete_publication(self.root,item['id'],site,owner_minutes=2,rework_count=1)
    self.assertEqual(before,(directory/'outcome.json').read_bytes())
    for key,value in (('origin','OBSERVED'),('workflowVersion','wrong-version')):
     changed=json.loads(before);changed[key]=value;(directory/'outcome.json').write_text(json.dumps(changed))
     with self.assertRaises(ValueError):complete_publication(self.root,item['id'],site,owner_minutes=2,rework_count=1)
     (directory/'outcome.json').write_bytes(before)
   (site/'source.md').write_text('changed')
   with self.assertRaises(ValueError):complete_publication(self.root,item['id'],site,owner_minutes=2,rework_count=1)
 def test_cross_runtime_closeout_keeps_test_history_out_of_canonical_cortex(self):
  # Observed-shaped contract fixtures live only in a fresh temporary runtime.
  import subprocess,sys
  cortex_source=Path('/tmp/cortex-abv-os-learning-20261010')
  if not cortex_source.is_dir():self.skipTest('Optional local cross-runtime source unavailable')
  cortex=(self.root/'cortex').resolve();cortex.mkdir()
  for rel in ('src','config'):shutil.copytree(cortex_source/rel,cortex/rel)
  shutil.copy2(cortex_source/'package.json',cortex/'package.json')
  from abvx_harness.process_learning import build_packet,digest,inspect_candidate
  from datetime import datetime,timezone,timedelta
  now=datetime.now(timezone.utc).replace(microsecond=0);start=now-timedelta(seconds=2)
  row={'schemaVersion':1,'kind':'AbvxOsProcessOutcome','tenant':'abvx-os','runId':'synthetic-cross-runtime','workflowId':'site.content.publish','workflowVersion':'publication-v1','origin':'OBSERVED','startedAt':start.isoformat().replace('+00:00','Z'),'completedAt':now.isoformat().replace('+00:00','Z'),'status':'PASS','elapsedSeconds':2,'ownerMinutes':3,'reworkCount':0,'qualityGate':'PASS','safetyGate':'PASS','evidence':[{'ref':'workload:synthetic-profile','sha256':'a'*64}]}
  packet=build_packet([row],'synthetic-cross-batch',row['completedAt']);file=self.root/'batch.json';file.write_text(json.dumps(packet));out=cortex/'data/abvx-os/synthetic-cross-runtime'
  args=['node','src/abvx-os-receive.mjs','--packet',str(file),'--context-out',str(out/'context.json'),'--candidate-out',str(out/'candidate.json')]
  for _ in range(2):
   run=subprocess.run(args,cwd=cortex,capture_output=True,text=True);self.assertEqual(run.returncode,0,run.stderr)
  context=json.loads((out/'context.json').read_text());candidate=json.loads((out/'candidate.json').read_text())
  self.assertEqual(inspect_candidate(context,candidate,'publication-v1',[packet])['status'],'RECORDED_READY_FOR_ANALYSIS')
  self.assertEqual(len((cortex/'data/abvx-os/ledger.jsonl').read_text().splitlines()),1)

 def test_native_story_filename_and_all_approved_frontmatter(self):
  from abvx_harness.publication_learning import verified_site
  from types import SimpleNamespace
  item=self.prepared();site=self.root/'site';directory=site/'content/working-stories';directory.mkdir(parents=True)
  file=directory/f"ws-999-{item['slug']}.md";source=item['payload']['source_markdown'];file.write_text(source)
  with patch('abvx_harness.publication_learning.subprocess.run',return_value=SimpleNamespace(stdout=b'https://github.com/markoblogo/ABVXsite.git')):
   self.assertEqual(verified_site(self.root,item,site),site.resolve())
   file.write_text(source.replace('"visibility": "public"','"visibility": "private"'))
   with self.assertRaises(ValueError):verified_site(self.root,item,site)
 def test_rejected_completed_id_preserves_approved_item(self):
  item=self.prepared();approve_content_item(self.root,item['id']);publish_content_item(self.root,item['id'])
  from abvx_harness.content_ops import inspect_content_item
  before=inspect_content_item(self.root,item['id']);(self.root/'.tmp/publication-learning'/item['id']/'outcome.json').write_text('{}')
  with self.assertRaises(ValueError):self.prepared()
  self.assertEqual(before,inspect_content_item(self.root,item['id']))
 def test_video_profile_uses_frontmatter_not_prose_or_null_field(self):
  from abvx_harness.publication_learning import start_publication
  item=self.prepared();item['id']='no-video-profile';source=item['payload']['source_markdown'];item['payload']['source_markdown']=source.replace('"language": "en"','"language": "en", "videoUrl": null')+'\nThe literal key "videoUrl" is not a video.\n'
  start_publication(self.root,item,'SYNTHETIC');session=json.loads((self.root/'.tmp/publication-learning'/item['id']/'session.json').read_text());self.assertFalse(session['workload']['video'])
 def test_fenced_code_does_not_require_rendered_language_marker(self):
  from abvx_harness.publication_learning import validate_live_html
  item={'title':'Code test','enrichment':{'canonical_path':'/writing/code-test'},'payload':{'body_lines':['```python\nprint("distinctive test phrase")\n```']}}
  validate_live_html(item,b'<link rel="canonical" href="https://abvx.xyz/writing/code-test"><h1>Code test</h1><pre>print("distinctive test phrase")</pre>')
 def test_invalid_batch_is_rejected_before_cortex_call(self):
  from abvx_harness.publication_learning import transfer_publication
  item=self.prepared();directory=self.root/'.tmp/publication-learning'/item['id'];(directory/'batch.json').write_text('{"payload":{"outcomes":[]}}')
  with patch('abvx_harness.publication_learning.subprocess.run') as receiver:
   with self.assertRaises(ValueError):transfer_publication(self.root,item['id'],self.root/'cortex')
   receiver.assert_not_called()
 def test_cited_batch_resolution_ignores_unrelated_history(self):
  from abvx_harness.publication_learning import cited_batches
  directory=self.root/'.tmp/publication-learning/current';directory.mkdir(parents=True);packet={'packetId':'publication:current'};(directory/'batch.json').write_text(json.dumps(packet))
  for i in range(101):
   unrelated=directory.parent/f'unrelated-{i}';unrelated.mkdir();(unrelated/'batch.json').write_text('corrupt unrelated history')
  with patch('abvx_harness.publication_learning.validate_packet',side_effect=lambda x:x):
   self.assertEqual(cited_batches(self.root,{'results':[{'sourcePacketId':'publication:current'}]}),[packet])
 def test_immutable_write_does_not_leave_partial_destination(self):
  from abvx_harness.process_learning import _write_once
  target=self.root/'evidence.json'
  with patch('abvx_harness.process_learning.os.fsync',side_effect=OSError('synthetic interrupted flush')):
   with self.assertRaises(OSError):_write_once(target,{'status':'PASS'})
  self.assertFalse(target.exists());self.assertFalse(list(self.root.glob('.evidence.json-*')))
  _write_once(target,{'status':'PASS'});_write_once(target,{'status':'PASS'})
  self.assertEqual(json.loads(target.read_text()),{'status':'PASS'})
 def test_tree_digest_includes_deleted_paths_and_executable_mode(self):
  from abvx_harness.publication_learning import tree_digest
  site=self.root/'site';site.mkdir();file=site/'source.md';file.write_text('same');file.chmod(0o644)
  with patch('abvx_harness.publication_learning.tracked_files',return_value=['source.md']):
   before=tree_digest(site);file.chmod(0o755);self.assertNotEqual(before,tree_digest(site));file.chmod(0o644);self.assertEqual(before,tree_digest(site));file.unlink();self.assertNotEqual(before,tree_digest(site))
