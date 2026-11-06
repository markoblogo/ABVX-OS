"""Thin content-revision receipt bridge. No Git/deploy/public-page checks or Cortex PASS claims."""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path
from .content_ops import _load_item,_approval_fingerprint
from .publication_learning import folder,utc,markdown_parts
from .process_learning import _write_once,_time,_integer

PROFILE='runtime-writing-v1'
def sha(value):return hashlib.sha256(value.encode()).hexdigest()
def validate_commit(item,command,receipt,export,engine):
    if item.get('status')!='PUBLISH_PACKET_EMITTED' or item.get('human_gate',{}).get('approved_content_sha256')!=_approval_fingerprint(item):
        raise ValueError('Current source-specific approval and handoff required')
    source=item.get('payload',{}).get('source_markdown')
    if not isinstance(source,str) or command.get('source')!=source or sha(source)!=item['payload'].get('source_sha256'):
        raise ValueError('Exact accepted source required')
    if command.get('action') not in ('publish','update') or receipt.get('action')!=command['action'] or command.get('requestId')!=receipt.get('requestId'):
        raise ValueError('Matching content request required')
    if receipt.get('profile')!=PROFILE or receipt.get('status')!='STORED' or receipt.get('originalSourceSha256')!=sha(source):
        raise ValueError('Runtime storage receipt required; not a legacy QA receipt')
    if receipt.get('approval')!={'intakeId':item['id'],'sourceSha256':sha(source)} or command.get('approval')!=receipt['approval']:
        raise ValueError('Receipt approval binding differs')
    if engine.get('status')!='PRODUCTION_ENGINE_VERIFIED' or not re.fullmatch('[a-f0-9]{64}',engine.get('engineVersion','')) or engine['engineVersion']!=receipt.get('engineVersion') or not re.fullmatch('[a-f0-9]{64}',engine.get('evidence_sha256','')) or not re.fullmatch('[a-f0-9]{40}',engine.get('validatedDeploymentSha','')):
        raise ValueError('Separately verified production engine required')
    if receipt.get('deploymentEnvironment')!='production' or not re.fullmatch('[a-f0-9]{40}',receipt.get('deploymentSha') or '') or export.get('deploymentEnvironment')!='production':
        raise ValueError('Local/Preview receipts cannot confirm a Production content write')
    if export.get('engineVersion')!=receipt['engineVersion']:
        raise ValueError('Engine changed during confirmation')
    original,body=markdown_parts(source)
    if receipt.get('id')!=item['slug'] or receipt.get('canonicalUrl')!='https://abvx.xyz/writing/'+('working-stories/' if original.get('type')=='working-story' else '')+item['slug'] or receipt.get('bodySha256')!=sha(body):
        raise ValueError('Canonical/source binding differs')
    record=export['snapshot']['records'][item['slug']]
    if record['currentRevision']!=receipt.get('revision'):raise ValueError('Stored revision is no longer current')
    version=record['versions'][record['currentRevision']]
    if version.get('withdrawn') or sha(version['source'])!=receipt.get('sourceSha256') or version.get('sourceSha256')!=receipt['sourceSha256']:
        raise ValueError('Stored source integrity differs')
    stored,stored_body=markdown_parts(version['source'])
    for image in [original.get('media'),original.get('heroImage'),original.get('coverImage'),*original.get('illustrations',[])]:
        if not image:continue
        mapping=next((m for m in receipt.get('mediaMapping',[]) if m['from']==image['src']),None)
        if mapping:image['src']=mapping['to']
    if original!=stored or body!=stored_body or record['firstPublishedAt']!=receipt.get('firstPublishedAt') or stored.get('date',stored.get('publishedAt'))!=receipt.get('firstPublishedAt'):
        raise ValueError('Stored metadata/prose changed beyond approved media mapping')
    return {'canonicalUrl':receipt['canonicalUrl'],'revision':receipt['revision'],'sourceSha256':receipt['sourceSha256'],'engineVersion':receipt['engineVersion']}

def complete_runtime(root,run_id,item_id,command,receipt,export,engine,*,rework_count):
    """Close one runtime single; preserve old outcome formats and original timer."""
    _integer(rework_count)
    directory=folder(root,run_id);cycle=json.loads((directory/'cycle.json').read_text())
    if cycle.get('itemIds')!=[item_id] or json.loads((folder(root,item_id)/'cycle-claim.json').read_text())!={'runId':run_id}:
        raise ValueError('Bound single runtime cycle required')
    if (directory/'outcome.json').exists() or (folder(root,item_id)/'outcome.json').exists():raise ValueError('Legacy outcome already exists')
    proof=validate_commit(_load_item(root,item_id),command,receipt,export,engine)
    if _time(receipt['storedAt'])<_time(cycle['startedAt']):raise ValueError('Content write predates the cycle')
    target=directory/'runtime-outcome.json'
    row={'schemaVersion':1,'profile':PROFILE,'status':'CONTENT_COMMITTED_UNVERIFIED','runId':run_id,'itemId':item_id,
         'startedAt':cycle['startedAt'],'storedAt':receipt['storedAt'],'recordedAt':utc(),'ownerMinutes':'UNKNOWN',
         'reworkCount':rework_count,'publicVerification':'OWNER_OPTIONAL','legacyQualityGate':'NOT_RUN',
         'cortexStatus':'NOT_QUALIFIED_RUNTIME_PROFILE','content':proof,
         'receiptSha256':sha(json.dumps(receipt,sort_keys=True))}
    row['elapsedToCommitSeconds']=round((_time(receipt['storedAt'])-_time(cycle['startedAt'])).total_seconds(),6)
    if target.exists():
        previous=json.loads(target.read_text());row['recordedAt']=previous['recordedAt']
        if row!=previous:raise ValueError('Immutable runtime closeout differs')
    _write_once(directory/'runtime-command.json',command);_write_once(directory/'runtime-receipt.json',receipt)
    _write_once(target,row)
    # These are projections only. Failure cannot trigger another publication.
    return row

def main(argv,root):
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('run','item','command','receipt','export','engine'):p.add_argument('--'+name,required=True)
    p.add_argument('--rework-count',type=int,required=True);p.add_argument('--site-root',type=Path);a=p.parse_args(argv)
    load=lambda path:json.loads(Path(path).read_text())
    result=complete_runtime(Path(root),a.run,a.item,load(a.command),load(a.receipt),load(a.export),load(a.engine),rework_count=a.rework_count)
    if a.site_root:
        from .book_readiness import atomic,after_publication
        target=a.site_root/'exports/runtime-writing/live-export.json'
        value=load(a.export)
        runtime_inventory(a.site_root,value)
        atomic(target,value)
        atomic(target.parent/'authority.json',{'profile':PROFILE,'engineVersion':value['engineVersion']})
        result['bookReadiness']=after_publication(Path(root),a.site_root)
    print(json.dumps(result,indent=2))

def runtime_inventory(site,value=None):
    """Regenerable private projection of the authenticated source; no alternate editable store."""
    path=Path(site)/'exports/runtime-writing/live-export.json'
    if value is None:
        if not path.exists():
            if (path.parent/'authority.json').exists():raise ValueError('Runtime inventory unavailable; bundled archive is stale')
            return None
        value=json.loads(path.read_text())
    if value.get('deploymentEnvironment')!='production' or value.get('authority')!='RUNTIME_WRITING_ENABLED' or not re.fullmatch('[a-f0-9]{64}',value.get('engineVersion','')) or not isinstance(value.get('publicIndex',{}).get('items'),list):
        raise ValueError('Authenticated production runtime export required')
    records=value['snapshot']['records'];docs={};withdrawn=set()
    for slug,record in records.items():
        version=record['versions'][record['currentRevision']]
        if sha(version['source'])!=version['sourceSha256']:raise ValueError('Runtime source integrity differs')
        data,body=markdown_parts(version['source'])
        if data.get('slug')!=slug or not isinstance(data.get('title'),str) or not data['title'].strip():raise ValueError('Runtime canonical source differs')
        url='https://abvx.xyz/writing/'+('working-stories/' if data.get('type')=='working-story' else '')+slug
        if version.get('withdrawn'):withdrawn.add(url)
        else:docs[url]=(data,body,str(path)+'#'+slug,True)
    for source in value.get('legacySources',[]):
        data,body=markdown_parts(source)
        if not re.fullmatch('[a-z0-9]+(?:-[a-z0-9]+)*',data.get('slug','')) or data.get('visibility') in ('private','draft'):raise ValueError('Invalid legacy source export')
        url='https://abvx.xyz/writing/'+('working-stories/' if data.get('type')=='working-story' else '')+data['slug']
        if url in docs or url in withdrawn:raise ValueError('Legacy source cannot override a managed record')
        docs[url]=(data,body,str(path)+'#legacy/'+data['slug'],True)
    return docs,withdrawn,value['publicIndex'],value['snapshot'].get('assets',{}),{'https://abvx.xyz/writing/'+('working-stories/' if markdown_parts(record['versions'][record['currentRevision']]['source'])[0].get('type')=='working-story' else '')+slug for slug,record in records.items()}
