"""Publication closeout using existing project checks and private OS/Cortex contracts."""
from __future__ import annotations
import argparse,hashlib,html,json,re,subprocess
from datetime import datetime,timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request,build_opener,HTTPRedirectHandler
from .process_learning import _id,_integer,_time,_write_once,build_packet,digest,validate_outcome,inspect_candidate
from .content_ops import _load_item,_approval_fingerprint

VERSION='publication-v1'
CHECKS=('content:validate','ecosystem:check','lint','test:sync','cortex-abv:vector-export:check','build','qa:seo','dependency-audit')
def utc():return datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z')
def folder(root,item_id):
 _id(item_id);base=root.resolve()/'.tmp/publication-learning';target=base/item_id
 if target.resolve()!=target:raise ValueError('Symlink publication state forbidden')
 return target

def start_publication(root,item,origin):
 if item['project']!='abvxsite' or item['adapter']['id'] not in ('abvx.writing','abvx.working-story'):return
 target=folder(root,item['id'])/'session.json'
 workload={'surface':item['surface'],'tier':item['validation']['tier'],'assets':len(item['payload'].get('media_assets',[])),'video':bool(item['payload'].get('source_markdown') and '"videoUrl"' in item['payload']['source_markdown'])}
 if target.exists():
  saved=json.loads(target.read_text())
  if saved.get('itemId')!=item['id'] or saved.get('origin')!=origin or saved.get('workload')!=workload or (target.parent/'outcome.json').exists():raise ValueError('Use a new intake ID for changed or completed publication')
  return
 _write_once(target,{'schemaVersion':1,'kind':'AbvxPublicationSession','itemId':item['id'],'origin':origin,'workflowVersion':VERSION,'startedAt':utc(),'workload':workload})

def tracked_files(site):
 result=subprocess.run(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=site,capture_output=True,check=True)
 return sorted(set(result.stdout.decode().split('\0'))-{''})
def tree_digest(site):
 site=site.resolve();refs=[]
 for name in tracked_files(site):
  file=site/name
  if file.resolve()!=file or not file.is_file():raise ValueError('Site tree contains symlink or missing source')
  refs.append({'path':name,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
 return digest(refs)
def verified_site(root,item,site):
 site=Path(site).resolve()
 remote=subprocess.run(['git','remote','get-url','origin'],cwd=site,capture_output=True,check=True).stdout.decode().strip()
 if not re.fullmatch(r'(?:https://github.com/|git@github.com:)markoblogo/ABVXsite(?:\.git)?',remote):raise ValueError('ABVXsite project checkout required')
 expected='working-stories' if item['adapter']['id']=='abvx.working-story' else 'writing'
 file=site/'content'/expected/f"{item['slug']}.md"
 if file.resolve()!=file or not file.is_file():raise ValueError('Approved public source missing')
 source=item['payload'].get('source_markdown')
 if not source:raise ValueError('Native approved Markdown is required for verified closeout')
 def body(value):
  match=re.match(r'\A---\s*\n(.*?)\n---(?:\n|$)(.*)\Z',value,re.S)
  if not match:raise ValueError('Native Markdown required')
  return json.loads(match[1]),match[2].strip()
 proposed,expected_body=body(source);actual,actual_body=body(file.read_text())
 if actual_body!=expected_body or actual.get('slug')!=item['slug'] or actual.get('title')!=item['title']:raise ValueError('Site source differs from approved content')
 for asset in item['payload'].get('media_assets',[]):
  media=site/'public'/asset['target'].lstrip('/')
  if not asset['target'].startswith('/media/') or media.resolve()!=media or not media.is_file() or hashlib.sha256(media.read_bytes()).hexdigest()!=asset['sha256']:raise ValueError('Site media differs from approved asset')
 return site

def check_publication(root,item_id,site,*,reuse_checks=False):
 item=_load_item(root,item_id)
 if item['status']!='PUBLISH_PACKET_EMITTED' or item['human_gate'].get('approved_content_sha256')!=_approval_fingerprint(item):raise ValueError('Approved current handoff required')
 site=verified_site(root,item,site);directory=folder(root,item_id);source=site/'exports/editorial-checks'
 if not reuse_checks:
  result=subprocess.run(['npm','run','content:release-check'],cwd=site,capture_output=True)
  if result.returncode:raise ValueError('Site release check failed; retained site logs explain the failed check')
 receipt=json.loads((source/'receipt.json').read_text())
 if receipt.get('result')!='PASS' or receipt.get('treeDigest')!=tree_digest(site) or [c.get('name') for c in receipt.get('checks',[])]!=list(CHECKS) or any(c.get('status')!='PASS' for c in receipt['checks']):raise ValueError('Fresh complete site release receipt required')
 verified_site(root,item,site);checks=[]
 for entry in receipt['checks']:
  name=entry['name'];data=(source/f"{name.replace(':','-')}.log").read_bytes();sha=hashlib.sha256(data).hexdigest()
  if sha!=entry.get('sha256'):raise ValueError('Site check log changed')
  target=directory/f"{name.replace(':','-')}-{sha[:12]}.log"
  if not target.exists():target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
  checks.append({'ref':'check:'+name,'sha256':sha,'status':'PASS'})
 value={'kind':'AbvxPublicationChecks','itemId':item_id,'approvalDigest':_approval_fingerprint(item),'treeDigest':receipt['treeDigest'],'checks':checks,'checkedAt':utc(),'buildMode':receipt.get('buildMode'),'status':'PASS'}
 (directory/'checks.json').write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
 return value

class Visible(HTMLParser):
 def __init__(self):super().__init__();self.canonical=[];self.parts=[];self.hidden=0
 def handle_starttag(self,tag,attrs):
  attr=dict(attrs)
  if tag in ('script','style'):self.hidden+=1
  if tag=='link' and 'canonical' in attr.get('rel','').split():self.canonical.append(attr.get('href'))
 def handle_endtag(self,tag):
  if tag in ('script','style'):self.hidden=max(0,self.hidden-1)
 def handle_data(self,value):
  if not self.hidden:self.parts.append(value)
def plain(value):
 value=re.sub(r'!\[[^\]]*\]\([^)]*\)','',value);value=re.sub(r'\[([^\]]+)\]\([^)]*\)',r'\1',value)
 return ' '.join(re.findall(r'[^\W_]+',html.unescape(value).casefold()))
def validate_live_html(item,data):
 parser=Visible();parser.feed(data.decode('utf-8'));url='https://abvx.xyz'+item['enrichment']['canonical_path']
 text=plain(' '.join(parser.parts))
 if parser.canonical!=[url] or plain(item['title']) not in text:raise ValueError('Production canonical/title not verified')
 paragraphs=[plain(line) for block in item['payload']['body_lines'] for line in block.split('\n\n')]
 paragraphs=[p for p in paragraphs if len(p)>12]
 if not paragraphs or any(p not in text for p in paragraphs):raise ValueError('Authored production text not verified')
 return hashlib.sha256(data).hexdigest()
class NoRedirect(HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):raise ValueError('Production redirect rejected')
def fetch_production(url):
 if not re.fullmatch(r'https://abvx\.xyz/writing/(?:working-stories/)?[a-z0-9]+(?:-[a-z0-9]+)*',url):raise ValueError('ABVX production writing URL required')
 with build_opener(NoRedirect()).open(Request(url,headers={'User-Agent':'ABVX-Publication-Verification/1'}),timeout=30) as response:
  if response.status!=200 or 'text/html' not in response.headers.get('Content-Type',''):raise ValueError('Production HTML unavailable')
  value=response.read(6*1024*1024+1)
  if len(value)>6*1024*1024:raise ValueError('Production response exceeds bound')
  return value

def complete_publication(root,item_id,site,*,owner_minutes='UNKNOWN',rework_count,cortex_root=None):
 item=_load_item(root,item_id);directory=folder(root,item_id)
 if item['status']!='PUBLISH_PACKET_EMITTED' or item['human_gate'].get('approved_content_sha256')!=_approval_fingerprint(item):raise ValueError('Approved current handoff required')
 if owner_minutes!='UNKNOWN':_integer(owner_minutes)
 _integer(rework_count)
 session=json.loads((directory/'session.json').read_text());checks=json.loads((directory/'checks.json').read_text())
 if session.get('itemId')!=item_id or session.get('origin') not in ('OBSERVED','SYNTHETIC') or session.get('workflowVersion')!=VERSION:raise ValueError('Valid publication session required')
 site=verified_site(root,item,site)
 if checks.get('kind')!='AbvxPublicationChecks' or checks.get('itemId')!=item_id or checks.get('approvalDigest')!=_approval_fingerprint(item) or checks.get('status')!='PASS' or checks.get('treeDigest')!=tree_digest(site) or [c.get('ref') for c in checks['checks']]!=['check:'+n for n in CHECKS] or any(c.get('status')!='PASS' for c in checks['checks']):raise ValueError('Fresh passing checks for exact site tree required')
 # Verify logs still exist with their recorded digest; do not export their contents.
 for c in checks['checks']:
  name=c['ref'][6:].replace(':','-');log=directory/f"{name}-{c['sha256'][:12]}.log"
  if hashlib.sha256(log.read_bytes()).hexdigest()!=c['sha256']:raise ValueError('Check evidence changed')
 packet=json.loads((root/item['publication']['packet_ref']).read_text())
 if packet['payload']!=item['payload'] or packet['slug']!=item['slug']:raise ValueError('Publish packet changed')
 url='https://abvx.xyz'+item['enrichment']['canonical_path']
 if not (directory/'outcome.json').exists():
  live_digest=validate_live_html(item,fetch_production(url));end=utc()
  row={'schemaVersion':1,'kind':'AbvxOsProcessOutcome','tenant':'abvx-os','runId':item_id,'workflowId':'site.content.publish','workflowVersion':VERSION,'origin':session['origin'],'startedAt':session['startedAt'],'completedAt':end,'status':'PASS','elapsedSeconds':round((_time(end)-_time(session['startedAt'])).total_seconds(),6),'ownerMinutes':owner_minutes,'reworkCount':rework_count,'qualityGate':'PASS','safetyGate':'PASS','evidence':[{'ref':'workload:publication-profile','sha256':digest({**session['workload'],'buildMode':checks.get('buildMode')})},{'ref':'production:authored-text','sha256':live_digest},{'ref':'approval:content','sha256':_approval_fingerprint(item)},*[{'ref':c['ref'],'sha256':c['sha256']} for c in checks['checks']]]}
  validate_outcome(row);_write_once(directory/'outcome.json',row)
 else:
  row=validate_outcome(json.loads((directory/'outcome.json').read_text()))
  if row['runId']!=item_id or row['ownerMinutes']!=owner_minutes or row['reworkCount']!=rework_count:raise ValueError('Immutable publication measurement differs')
 batch=build_packet([row],'publication:'+item_id,row['completedAt']);_write_once(directory/'batch.json',batch)
 result={'status':'RECORDED','origin':row['origin'],'cortexStatus':'PENDING_TRANSFER','executionAuthorized':False}
 if cortex_root:
  if row['origin']!='OBSERVED':raise ValueError('Synthetic publication cannot enter operational Cortex history')
  receipt=transfer_publication(root,item_id,cortex_root);result.update(cortexStatus=receipt['status'])
 return result

def transfer_publication(root,item_id,cortex_root):
 directory=folder(root,item_id);batch=json.loads((directory/'batch.json').read_text());row=validate_outcome(batch['payload']['outcomes'][0])
 if row['origin']!='OBSERVED':raise ValueError('Synthetic publication cannot enter operational Cortex history')
 cortex=Path(cortex_root).resolve();target=cortex/'data/abvx-os/publications'/item_id
 result=subprocess.run(['node','src/abvx-os-receive.mjs','--packet',str((directory/'batch.json').resolve()),'--context-out',str(target/'context.json'),'--candidate-out',str(target/'candidate.json')],cwd=cortex,capture_output=True,timeout=30)
 if result.returncode:raise ValueError('Cortex transfer failed; retained local outcome can be retried')
 context=json.loads((target/'context.json').read_text());candidate=json.loads((target/'candidate.json').read_text())
 # Original batches for previous publications are explicitly enumerated here, not manuscripts.
 packets=[json.loads(p.read_text()) for p in (root/'.tmp/publication-learning').glob('*/batch.json')]
 receipt=inspect_candidate(context,candidate,VERSION,packets);_write_once(directory/'cortex-review.json',receipt)
 return receipt

def main(argv,root):
 parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='action',required=True)
 for name in ('check','complete','transfer'):
  command=sub.add_parser(name);command.add_argument('--item',required=True)
  if name!='transfer':command.add_argument('--site-root',required=True,type=Path)
  if name=='check':command.add_argument('--reuse-checks',action='store_true')
  if name!='check':command.add_argument('--cortex-root',type=Path,required=name=='transfer')
  if name=='complete':command.add_argument('--owner-minutes',default='UNKNOWN');command.add_argument('--rework-count',required=True,type=int)
 args=parser.parse_args(argv)
 if args.action=='check':value=check_publication(root,args.item,args.site_root,reuse_checks=args.reuse_checks)
 elif args.action=='transfer':value=transfer_publication(root,args.item,args.cortex_root)
 else:value=complete_publication(root,args.item,args.site_root,owner_minutes='UNKNOWN' if args.owner_minutes=='UNKNOWN' else int(args.owner_minutes),rework_count=args.rework_count,cortex_root=args.cortex_root)
 print(json.dumps(value if args.action!='check' else {'status':value['status'],'checks':len(value['checks'])},sort_keys=True))
 return 1 if value.get('status')=='FAIL' else 0
