import copy,hashlib,json,unittest
from unittest.mock import patch
from abvx_harness.runtime_publication import validate_commit
class RuntimeReceiptTests(unittest.TestCase):
 def test_commit_is_bound_to_approved_source_and_never_claims_public_qa(self):
  source='---\n'+json.dumps({'id':'one','slug':'one','title':'One','publishedAt':'2026-10-26'})+'\n---\n\nAuthor text.'
  sha=lambda s:hashlib.sha256(s.encode()).hexdigest()
  item={'id':'intake-one','slug':'one','status':'PUBLISH_PACKET_EMITTED','human_gate':{'approved_content_sha256':'approved'},'payload':{'source_markdown':source,'source_sha256':sha(source)}}
  approval={'intakeId':'intake-one','sourceSha256':sha(source)}
  command={'action':'publish','requestId':'request-one','source':source,'approval':approval}
  receipt={'profile':'runtime-writing-v1','status':'STORED','id':'one','action':'publish','requestId':'request-one','revision':'rev-one','originalSourceSha256':sha(source),'sourceSha256':sha(source),'bodySha256':sha('Author text.'),'canonicalUrl':'https://abvx.xyz/writing/one','approval':approval,'engineVersion':'a'*64,'deploymentEnvironment':'production','deploymentSha':'e'*40,'firstPublishedAt':'2026-10-26'}
  export={'deploymentEnvironment':'production','engineVersion':'a'*64,'snapshot':{'records':{'one':{'currentRevision':'rev-one','firstPublishedAt':'2026-10-26','versions':{'rev-one':{'source':source,'sourceSha256':sha(source),'withdrawn':False}}}}}}
  engine={'engineVersion':'a'*64,'status':'PRODUCTION_ENGINE_VERIFIED','evidence_sha256':'b'*64,'validatedDeploymentSha':'d'*40}
  with patch('abvx_harness.runtime_publication._approval_fingerprint',return_value='approved'):
   self.assertEqual(validate_commit(item,command,receipt,export,engine)['revision'],'rev-one')
   for field,value in [('profile','publication-v1'),('deploymentEnvironment','local'),('originalSourceSha256','0'*64),('engineVersion','c'*64),('canonicalUrl','https://preview.example/one')]:
    changed={**receipt,field:value}
    with self.assertRaises(ValueError):validate_commit(item,command,changed,export,engine)
   changed=copy.deepcopy(export);changed['snapshot']['records']['one']['currentRevision']='different'
   with self.assertRaises(ValueError):validate_commit(item,command,receipt,changed,engine)

 def test_runtime_inventory_preserves_authority_and_withdrawals(self):
  from pathlib import Path
  from tempfile import TemporaryDirectory
  from abvx_harness.runtime_publication import runtime_inventory
  from abvx_harness.book_readiness import source_documents
  with TemporaryDirectory() as temp:
   root=Path(temp);site=root/'site';directory=site/'exports/runtime-writing';directory.mkdir(parents=True)
   source='---\n'+json.dumps({'id':'one','slug':'one','title':'One','publishedAt':'2026-10-26','visibility':'public'})+'\n---\n\nCurrent author text.'
   value={'deploymentEnvironment':'production','authority':'RUNTIME_WRITING_ENABLED','engineVersion':'a'*64,'publicIndex':{'items':[{'canonicalUrl':'https://abvx.xyz/writing/one'}]},'snapshot':{'records':{'one':{'currentRevision':'r','versions':{'r':{'source':source,'sourceSha256':hashlib.sha256(source.encode()).hexdigest(),'withdrawn':False}}}},'assets':{}}}
   (directory/'live-export.json').write_text(json.dumps(value))
   (site/'content/writing').mkdir(parents=True);(site/'content/writing/old.md').write_text(source.replace('Current author text.','Stale archive text.'))
   (site/'content/writing/two.md').write_text(source.replace('one','two').replace('Current author text.','Later legacy post.'))
   (site/'public').mkdir();(site/'public/content-index.json').write_text(json.dumps({'items':[{'canonicalUrl':'https://abvx.xyz/writing/two'}]}))
   docs,_,indexed,_=source_documents(root,site)
   self.assertIn('https://abvx.xyz/writing/two',docs);self.assertIn('https://abvx.xyz/writing/two',indexed)
   self.assertEqual(docs['https://abvx.xyz/writing/one'][1],'Current author text.')
   value['snapshot']['records']['one']['versions']['r']['withdrawn']=True
   (directory/'live-export.json').write_text(json.dumps(value))
   self.assertNotIn('https://abvx.xyz/writing/one',source_documents(root,site)[0])
   (directory/'authority.json').write_text('{}');(directory/'live-export.json').unlink()
   with self.assertRaises(ValueError):runtime_inventory(site)

 def test_runtime_terminal_cannot_be_aborted_through_legacy_path(self):
  from pathlib import Path
  from tempfile import TemporaryDirectory
  from abvx_harness.publication_learning import folder,abort_cycle
  with TemporaryDirectory() as temp:
   root=Path(temp);directory=folder(root,'runtime-one');directory.mkdir(parents=True)
   (directory/'runtime-outcome.json').write_text('{}')
   with self.assertRaisesRegex(ValueError,'already closed'):abort_cycle(root,'runtime-one',status='CANCELLED',rework_count=0)

 def test_runtime_story_inventory_uses_nested_canonical_and_withdrawal(self):
  from pathlib import Path
  from tempfile import TemporaryDirectory
  from abvx_harness.runtime_publication import runtime_inventory
  from abvx_harness.book_readiness import source_documents
  with TemporaryDirectory() as temp:
   site=Path(temp)/'site';directory=site/'exports/runtime-writing';directory.mkdir(parents=True)
   data={'type':'working-story','slug':'case-one','title':'Case One','date':'2026-10-28','visibility':'public','story_id':'ws-001','book':{'include':True,'status':'draft'}}
   source='---\n'+json.dumps(data)+'\n---\n\nCurrent case.'
   url='https://abvx.xyz/writing/working-stories/case-one'
   version={'source':source,'sourceSha256':hashlib.sha256(source.encode()).hexdigest(),'withdrawn':False}
   value={'deploymentEnvironment':'production','authority':'RUNTIME_WRITING_ENABLED','engineVersion':'a'*64,'publicIndex':{'items':[{'canonicalUrl':url}]},'snapshot':{'records':{'case-one':{'currentRevision':'r','versions':{'r':version}}},'assets':{}}}
   (directory/'live-export.json').write_text(json.dumps(value))
   legacy=site/'content/working-stories';legacy.mkdir(parents=True);(legacy/'case.md').write_text(source.replace('Current case.','Stale case.'))
   docs=source_documents(Path(temp),site)[0];self.assertEqual(docs[url][1],'Current case.')
   version['withdrawn']=True;(directory/'live-export.json').write_text(json.dumps(value))
   self.assertIn(url,runtime_inventory(site)[1]);self.assertNotIn(url,source_documents(Path(temp),site)[0])
