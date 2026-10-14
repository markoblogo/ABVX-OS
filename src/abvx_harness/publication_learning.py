"""Publication closeout using existing project checks and private OS/Cortex contracts."""
from __future__ import annotations
import argparse,fcntl,hashlib,html,json,re,subprocess
from datetime import datetime,timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request,build_opener,HTTPRedirectHandler
from urllib.parse import urlsplit,parse_qs
from .process_learning import _id,_integer,_time,_write_once,build_packet,digest,validate_outcome,validate_packet,inspect_candidate,ELAPSED_POLICY,PUBLICATION_VERSIONS,PUBLICATION_CHANGES,validate_series
from .content_ops import _load_item,_approval_fingerprint

VERSION='publication-v1'
CHECKS=('content:validate','ecosystem:check','lint','test:sync','cortex-abv:vector-export:check','build','qa:seo','dependency-audit')
PUBLICATION_CHECKS=('content:validate','ecosystem:check','test:publication','build','qa:seo','dependency-audit')
CYCLE_VERSIONS={'baseline':'publication-v2-baseline','early-input':'publication-v2-early-input','batch-validation':'publication-v2-batch-validation','reuse-context':'publication-v2-reuse-context'}
def utc():return datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z')
def folder(root,item_id):
 _id(item_id);base=root.resolve()/'.tmp/publication-learning';target=base/item_id
 if target.resolve()!=target:raise ValueError('Symlink publication state forbidden')
 return target

def begin_cycle(root,run_id,item_ids,*,trial='baseline',series_id=None):
 # Serialize membership reservations; concurrent commands cannot claim the same material.
 lock=folder(root,'cycle-lock')/'begin.lock';lock.parent.mkdir(parents=True,exist_ok=True)
 if lock.is_symlink():raise ValueError('Symlink cycle lock forbidden')
 with lock.open('a') as handle:
  fcntl.flock(handle,fcntl.LOCK_EX)
  _recover_reservation(root)
  return _begin_cycle(root,run_id,item_ids,trial=trial,series_id=series_id)

def _begin_cycle(root,run_id,item_ids,*,trial='baseline',series_id=None):
 """First work after publication authorization, before preparation; never backdate."""
 if len(run_id)>108 or 'cycle-lock' in [run_id,*item_ids]:raise ValueError('Reserve namespace and packet-prefix capacity')
 if trial=='batch-validation' and len(item_ids)<2:raise ValueError('Batch-validation requires a pool')
 if trial not in CYCLE_VERSIONS:raise ValueError('One controlled trial or baseline required')
 if not isinstance(item_ids,list) or not 1<=len(item_ids)<=20 or len(set(item_ids))!=len(item_ids) or run_id in item_ids:
  raise ValueError('Select 1–20 unique items and a distinct cycle ID')
 if any(not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',i) for i in [run_id,*item_ids]):raise ValueError('Publication slugs required')
 target=folder(root,run_id)/'cycle.json'
 if target.is_symlink() or (target.parent/'outcome.json').exists() or (target.parent/'session.json').exists() or (target.parent/'cycle-claim.json').exists():raise ValueError('Use a fresh cycle ID')
 value={'schemaVersion':2,'kind':'AbvxPublicationCycle','runId':run_id,'itemIds':sorted(item_ids),
        'mode':'single' if len(item_ids)==1 else 'batch','workflowVersion':CYCLE_VERSIONS[trial],'startedAt':utc()}
 claims=[folder(root,i)/'cycle-claim.json' for i in item_ids]
 claim={'runId':run_id}
 for i,path in zip(item_ids,claims):
  if (path.parent/'cycle.json').exists():raise ValueError('Cycle IDs cannot be intake members')
  if path.is_symlink():raise ValueError('Symlink membership claim forbidden')
  if path.exists() and json.loads(path.read_text())!=claim:raise ValueError('Item already belongs to another independent cycle')
  if not target.exists() and (folder(root,i)/'session.json').exists():raise ValueError('Begin before intake; historical timing cannot be reconstructed')
 if target.exists():
  previous=json.loads(target.read_text());_time(previous.get('startedAt'));value['startedAt']=previous['startedAt']
 if series_id:
  series=validate_series(json.loads(series_path(root,series_id).read_text()))
  key='baselineRunIds' if trial=='baseline' else 'heldOutRunIds'
  if run_id not in series[key] or value['workflowVersion']!=series['baselineVersion' if key=='baselineRunIds' else 'candidateVersion']:raise ValueError('Cycle outside declared trial/version')
  if _time(series['createdAt'])>=_time(value['startedAt']):raise ValueError('Series must strictly precede work')
  if key=='heldOutRunIds':
   for previous in series['baselineRunIds']:
    previous_file=folder(root,previous)/'outcome.json'
    if not previous_file.exists():raise ValueError('Finish every declared baseline cycle before held-out work')
    row=validate_outcome(json.loads(previous_file.read_text()))
    if _time(row['completedAt'])>=_time(value['startedAt']):raise ValueError('Finish baseline before held-out work')
  value['trialSeries']={'id':series_id,'sha256':digest(series)}
 _write_once(folder(root,'cycle-lock')/'pending.json',value)
 _recover_reservation(root)
 return value

def _recover_reservation(root):
 pending=folder(root,'cycle-lock')/'pending.json'
 if not pending.exists():return
 if pending.is_symlink():raise ValueError('Symlink reservation journal forbidden')
 value=json.loads(pending.read_text());run=value['runId'];items=value['itemIds']
 if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',run) or len(run)>108 or not isinstance(items,list) or not 1<=len(items)<=20 or len(set(items))!=len(items) or run in items or 'cycle-lock' in [run,*items]:raise ValueError('Invalid pending reservation')
 _time(value['startedAt'])
 if value['workflowVersion'] not in PUBLICATION_VERSIONS or value['mode']!=('single' if len(items)==1 else 'batch'):raise ValueError('Invalid pending cycle')
 for item in items:
  if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',item):raise ValueError('Invalid pending member')
  target=folder(root,item)/'cycle-claim.json'
  if target.is_symlink() or (target.parent/'cycle.json').exists():raise ValueError('Conflicting pending namespace')
  _write_once(target,{'runId':run})
 target=folder(root,run)/'cycle.json'
 if target.is_symlink() or (target.parent/'cycle-claim.json').exists():raise ValueError('Conflicting pending namespace')
 _write_once(target,value);pending.unlink()

def series_path(root,series_id):
 if not isinstance(series_id,str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',series_id) or len(series_id)>108:raise ValueError('Safe series ID required')
 target=root.resolve()/'.tmp/publication-trials'/f'{series_id}.json'
 if target.resolve()!=target:raise ValueError('Symlink trial state forbidden')
 return target

def begin_series(root,series_id,change,baseline_runs,held_out_runs):
 lock=folder(root,'cycle-lock')/'begin.lock';lock.parent.mkdir(parents=True,exist_ok=True)
 if lock.is_symlink():raise ValueError('Symlink cycle lock forbidden')
 with lock.open('a') as handle:
  fcntl.flock(handle,fcntl.LOCK_EX);_recover_reservation(root)
  return _begin_series(root,series_id,change,baseline_runs,held_out_runs)

def _begin_series(root,series_id,change,baseline_runs,held_out_runs):
 candidates=[v for v,c in PUBLICATION_CHANGES.items() if c==change]
 if len(candidates)!=1:raise ValueError('One supported intervention required')
 target=series_path(root,series_id)
 series={'schemaVersion':1,'kind':'AbvxPublicationTrialSeries','seriesId':series_id,'createdAt':utc(),
         'change':change,'baselineVersion':'publication-v2-baseline','candidateVersion':candidates[0],
         'baselineRunIds':baseline_runs,'heldOutRunIds':held_out_runs}
 validate_series(series)
 if any(not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',i) or len(i)>108 for i in baseline_runs+held_out_runs):raise ValueError('Safe producer cycle IDs required')
 if target.exists():series['createdAt']=json.loads(target.read_text())['createdAt']
 elif any((folder(root,i)/'cycle.json').exists() for i in baseline_runs+held_out_runs):raise ValueError('Declare complete series before first work')
 _write_once(target,series);return series

def trial_evidence(root,cycle):
 binding=cycle.get('trialSeries')
 if not binding:return []
 if not isinstance(binding,dict) or set(binding)!={'id','sha256'}:raise ValueError('Invalid series binding')
 series=validate_series(json.loads(series_path(root,binding['id']).read_text()))
 if digest(series)!=binding['sha256']:raise ValueError('Trial series changed')
 expected=series['baselineRunIds'] if cycle['workflowVersion']==series['baselineVersion'] else series['heldOutRunIds']
 if cycle['runId'] not in expected or _time(series['createdAt'])>=_time(cycle['startedAt']):raise ValueError('Cycle outside preregistered series')
 return [{'ref':'trial:publication-series','sha256':digest(series)}]

def abort_cycle(root,run_id,*,status,rework_count,cortex_root=None,origin=None):
 if status not in ('FAIL','CANCELLED'):raise ValueError('Explicit terminal failure/cancellation required')
 _integer(rework_count);directory=folder(root,run_id);cycle=json.loads((directory/'cycle.json').read_text())
 if cycle.get('runId')!=run_id or cycle.get('workflowVersion') not in PUBLICATION_VERSIONS:raise ValueError('Started cycle required')
 profile=[];origins=set()
 for item_id in cycle['itemIds']:
  path=folder(root,item_id)/'session.json'
  if path.exists():
   session=json.loads(path.read_text());profile.append(session['workload']);origins.add(session['origin'])
 if len(origins)>1:raise ValueError('Cannot mix synthetic and observed failures')
 if origin is not None and origin not in ('OBSERVED','SYNTHETIC'):raise ValueError('Explicit valid origin required')
 if not origins and origin is None:raise ValueError('Explicit origin required before intake')
 if origins and origin is not None and origin not in origins:raise ValueError('Explicit origin differs from intake evidence')
 actual_origin=next(iter(origins)) if origins else origin
 target=directory/'outcome.json';end=utc()
 if target.exists():end=json.loads(target.read_text())['completedAt']
 row={'schemaVersion':1,'kind':'AbvxOsProcessOutcome','tenant':'abvx-os','runId':run_id,
      'workflowId':'site.content.publish','workflowVersion':cycle['workflowVersion'],'origin':actual_origin,
      'startedAt':cycle['startedAt'],'completedAt':end,'status':status,
      'elapsedSeconds':round((_time(end)-_time(cycle['startedAt'])).total_seconds(),6),
      'ownerMinutes':'UNKNOWN','reworkCount':rework_count,'qualityGate':'UNKNOWN','safetyGate':'UNKNOWN',
      'evidence':[ELAPSED_POLICY,{'ref':'cycle:'+run_id,'sha256':digest(cycle)},
                  {'ref':'workload:publication-profile','sha256':digest({'mode':cycle['mode'],'items':sorted(profile,key=digest),'incomplete':True})},*trial_evidence(root,cycle)]}
 validate_outcome(row);_write_once(target,row);_write_once(directory/'batch.json',build_packet([row],'publication:'+run_id,end))
 if cortex_root:transfer_publication(root,run_id,cortex_root)
 return row


def start_publication(root,item,origin):
 if item['project']!='abvxsite' or item['adapter']['id'] not in ('abvx.writing','abvx.working-story'):return
 target=folder(root,item['id'])/'session.json'
 workload={'surface':item['surface'],'tier':item['validation']['tier'],'assets':len(item['payload'].get('media_assets',[])),'video':bool(markdown_parts(item['payload']['source_markdown'])[0].get('videoUrl')) if item['payload'].get('source_markdown') else False}
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
  if file.is_symlink():raise ValueError('Site tree contains symlink source')
  if not file.exists():refs.append({'mode':'deleted','path':name,'sha256':None});continue
  if file.resolve()!=file or not file.is_file():raise ValueError('Site tree contains symlink or missing source')
  refs.append({'mode':'100755' if file.stat().st_mode&0o111 else '100644','path':name,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
 return digest(refs)
def markdown_parts(value):
 match=re.match(r'\A---\s*\n(.*?)\n---(?:\n|$)(.*)\Z',value,re.S)
 if not match:raise ValueError('Native Markdown required')
 return json.loads(match[1]),match[2].strip()
def verified_site(root,item,site):
 site=Path(site).resolve()
 remote=subprocess.run(['git','remote','get-url','origin'],cwd=site,capture_output=True,check=True).stdout.decode().strip()
 if not re.fullmatch(r'(?:https://github.com/|git@github.com:)markoblogo/ABVXsite(?:\.git)?',remote):raise ValueError('ABVXsite project checkout required')
 expected='working-stories' if item['adapter']['id']=='abvx.working-story' else 'writing'
 source=item['payload'].get('source_markdown')
 if not source:raise ValueError('Native approved Markdown is required for verified closeout')
 proposed,expected_body=markdown_parts(source)
 name=f"{proposed['story_id']}-{item['slug']}.md" if expected=='working-stories' else f"{item['slug']}.md"
 file=site/'content'/expected/name
 if file.resolve()!=file or not file.is_file():raise ValueError('Approved public source missing')
 actual,actual_body=markdown_parts(file.read_text())
 if actual!=proposed or actual_body!=expected_body or actual.get('slug')!=item['slug'] or actual.get('title')!=item['title']:raise ValueError('Site source differs from approved content')
 for asset in item['payload'].get('media_assets',[]):
  media=site/'public'/asset['target'].lstrip('/')
  if not asset['target'].startswith('/media/') or media.resolve()!=media or not media.is_file() or hashlib.sha256(media.read_bytes()).hexdigest()!=asset['sha256']:raise ValueError('Site media differs from approved asset')
 return site

def qa_profile(checks):
 # Legacy receipts remain comparable to their original full-check workload.
 scope=checks.get('qaScope')
 value={} if scope is None else {'qaProfile':scope['profile']}
 if 'checkProfile' in checks:value['checkProfile']=checks['checkProfile']
 return value

def check_names(receipt):
 profile=receipt.get('checkProfile','full')
 if profile=='full':return CHECKS
 if profile=='publication-v1' and isinstance(receipt.get('qaScope'),dict) and receipt['qaScope'].get('profile')=='publication-v1':return PUBLICATION_CHECKS
 raise ValueError('Known check profile with matching QA scope required')

def validate_qa_scope(scope,item):
 if scope is None:return
 if not isinstance(scope,dict) or scope.get('profile') not in ('full','publication-v1'):raise ValueError('Known QA scope required')
 if scope['profile']=='publication-v1':
  routes=scope.get('routes')
  if not isinstance(routes,list) or not routes or item['enrichment']['canonical_path'] not in routes or any(not isinstance(r,str) or not re.fullmatch(r'/writing/(?:working-stories/)?[a-z0-9]+(?:-[a-z0-9]+)*',r) for r in routes) or not re.fullmatch(r'[a-f0-9]{40}',scope.get('base','')):raise ValueError('Publication QA must cover this approved material')

def check_publication(root,item_id,site,*,reuse_checks=False):
 item=_load_item(root,item_id)
 if item['status']!='PUBLISH_PACKET_EMITTED' or item['human_gate'].get('approved_content_sha256')!=_approval_fingerprint(item):raise ValueError('Approved current handoff required')
 site=verified_site(root,item,site);directory=folder(root,item_id);source=site/'exports/editorial-checks'
 if not reuse_checks:
  result=subprocess.run(['npm','run','content:release-check'],cwd=site,capture_output=True)
  if result.returncode:raise ValueError('Site release check failed; retained site logs explain the failed check')
 receipt=json.loads((source/'receipt.json').read_text())
 if receipt.get('result')!='PASS' or receipt.get('treeDigest')!=tree_digest(site) or [c.get('name') for c in receipt.get('checks',[])]!=list(check_names(receipt)) or any(c.get('status')!='PASS' for c in receipt['checks']):raise ValueError('Fresh complete site release receipt required')
 validate_qa_scope(receipt.get('qaScope'),item)
 verified_site(root,item,site);checks=[]
 for entry in receipt['checks']:
  name=entry['name'];data=(source/f"{name.replace(':','-')}.log").read_bytes();sha=hashlib.sha256(data).hexdigest()
  if sha!=entry.get('sha256'):raise ValueError('Site check log changed')
  target=directory/f"{name.replace(':','-')}-{sha[:12]}.log"
  if not target.exists():target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
  checks.append({'ref':'check:'+name,'sha256':sha,'status':'PASS'})
 value={'kind':'AbvxPublicationChecks','itemId':item_id,'approvalDigest':_approval_fingerprint(item),'treeDigest':receipt['treeDigest'],'checks':checks,'checkedAt':utc(),'buildMode':receipt.get('buildMode'),'status':'PASS'}
 if 'qaScope' in receipt:value['qaScope']=receipt['qaScope']
 if 'checkProfile' in receipt:value['checkProfile']=receipt['checkProfile']
 (directory/'checks.json').write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
 return value

class Visible(HTMLParser):
 # Track only the ancestors and semantic player projections needed by this
 # probe. This is static HTML evidence, not a computed-layout browser audit.
 void_tags=frozenset(('area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'))
 non_rendered=frozenset(('head','script','style','template','noscript','textarea','title','select'))
 def __init__(self):
  super().__init__();self.canonical=[];self.parts=[];self.stack=[];self.players=[]
 def child_namespace(self,tag):
  if not self.stack:return 'html'
  parent=self.stack[-1];namespace=parent['namespace']
  if ((namespace=='svg' and parent['tag'] in ('foreignobject','desc','title'))
      or (namespace=='math' and parent['tag'] in ('mi','mo','mn','ms','mtext') and tag not in ('mglyph','malignmark'))
      or (namespace=='math' and parent['tag']=='annotation-xml' and parent['html_integration'])):return 'html'
  return namespace
 def in_select(self):
  for node in reversed(self.stack):
   if node['namespace']=='html' and node['tag']=='template':return False
   if node['namespace']=='html' and node['tag']=='select':return True
  return False
 def handle_starttag(self,tag,attrs):
  # A browser keeps the first duplicate attribute, whereas dict keeps the
  # last. Ambiguous evidence or visibility attributes cannot prove release.
  seen=set()
  for key,_ in attrs:
   if key in seen and key in ('src','title','href','rel','hidden','inert','aria-hidden','style','open','encoding'):
    raise ValueError('Duplicate structural HTML attribute')
   seen.add(key)
  attr=dict(attrs)
  if self.in_select():
   if tag in ('input','keygen','textarea','select'):
    self.handle_endtag('select')
    if tag=='select':return
   elif tag not in ('option','optgroup','hr','script','template'):return
  namespace=self.child_namespace(tag)
  breakout=tag in ('b','big','blockquote','body','br','center','code','dd','div','dl','dt','em','embed','h1','h2','h3','h4','h5','h6','head','hr','i','img','li','listing','menu','meta','nobr','ol','p','pre','ruby','s','small','span','strong','strike','sub','sup','table','tt','u','ul','var') or (tag=='font' and any(k in attr for k in ('color','face','size')))
  if namespace!='html' and breakout:
   while self.stack and self.child_namespace(tag)!='html':self.stack.pop()
  if self.stack and self.stack[-1]['tag']=='head' and tag not in ('html','head','base','basefont','bgsound','link','meta','noframes','script','style','template','title','noscript'):
   self.handle_endtag('head')
  parent=self.stack[-1] if self.stack else None;namespace=self.child_namespace(tag)
  if namespace=='html' and tag in ('svg','math'):namespace=tag
  # Legacy raw-text elements are outside the site's publication renderer.
  # Python versions disagree about their tokenizer state, especially '/>'.
  # Reject them rather than let apparent child markup prove a real player.
  if namespace=='html' and tag in ('plaintext','xmp','noembed','noframes'):raise ValueError('Unsupported raw-text HTML evidence')
  if namespace=='html' and tag in ('address','article','aside','blockquote','dd','details','div','dl','dt','li','fieldset','figcaption','figure','footer','form','h1','h2','h3','h4','h5','h6','header','hgroup','hr','main','menu','nav','ol','p','pre','section','table','ul'):
   # Block starts close a paragraph in button scope, even if its optional
   # end tag was omitted. Do not cross a template or foreign boundary.
   for node in reversed(self.stack):
    if node['namespace']!='html' or node['tag'] in ('template','html','table','td','th','button','applet','marquee','object'):break
    if node['tag']=='p':self.handle_endtag('p');break
   parent=self.stack[-1] if self.stack else None
  if namespace=='html' and tag in ('li','dt','dd'):
   for node in reversed(self.stack):
    if node['namespace']!='html' or node['tag'] in ('template','html','table','ul','ol','dl'):break
    if node['tag'] in (('li',) if tag=='li' else ('dt','dd')):self.handle_endtag(node['tag']);break
   parent=self.stack[-1] if self.stack else None
  if namespace=='html' and tag in ('h1','h2','h3','h4','h5','h6') and self.stack and self.stack[-1]['namespace']=='html' and self.stack[-1]['tag'] in ('h1','h2','h3','h4','h5','h6'):
   self.stack.pop();parent=self.stack[-1] if self.stack else None
  style=attr.get('style') or ''
  hidden=bool((parent and parent['hidden']) or tag in self.non_rendered
      or (tag in ('details','dialog') and 'open' not in attr)
      or 'hidden' in attr or 'inert' in attr or (attr.get('aria-hidden') or '').casefold()=='true'
      or re.search(r'(?:^|;)\s*(?:display\s*:\s*none|visibility\s*:\s*(?:hidden|collapse)|content-visibility\s*:\s*hidden)\s*(?:!\s*important\s*)?(?:;|$)',style,re.I))
  player=parent['player'] if parent else None
  caption=parent['caption'] if parent else None
  anchor=parent['anchor'] if parent else None
  if namespace=='html' and tag=='figure':
   player={'frames':[],'links':[],'valid':True};caption=None;anchor=None
   if not hidden:self.players.append(player)
  if tag=='figcaption':caption=player if namespace=='html' and parent and parent['namespace']=='html' and parent['tag']=='figure' else None
  if not hidden and namespace=='html' and tag=='iframe' and parent and parent['namespace']=='html' and parent['tag']=='figure' and player is not None:
   player['frames'].append((attr.get('src') or '',attr.get('title') or ''))
  if tag=='a':
   anchor=None
   if not hidden and namespace=='html' and player is not None and caption is player:
    anchor={'href':attr.get('href') or '', 'parts':[]};player['links'].append(anchor)
  if namespace=='html' and tag=='link' and 'canonical' in (attr.get('rel') or '').split():self.canonical.append(attr.get('href'))
  if namespace!='html' or tag not in self.void_tags:self.stack.append({'tag':tag,'namespace':namespace,'html_integration':(attr.get('encoding') or '').casefold() in ('text/html','application/xhtml+xml'),'hidden':hidden or tag=='iframe','player':player,'caption':caption,'anchor':anchor})
 def handle_startendtag(self,tag,attrs):
  previous=self.stack[-1] if self.stack else None
  self.handle_starttag(tag,attrs)
  node=self.stack[-1] if self.stack and self.stack[-1] is not previous and self.stack[-1]['tag']==tag else None
  if node and tag=='iframe' and node['namespace']=='html' and node['player'] is not None:node['player']['valid']=False
  # Ignored select tokens create no node. Only foreign SVG/MathML elements
  # honor the slash; HTML templates and hidden ancestors stay open.
  if node and node['namespace']!='html':self.handle_endtag(tag)
 def handle_endtag(self,tag):
  if self.in_select() and tag not in ('select','option','optgroup','template','script'):return
  for index in range(len(self.stack)-1,-1,-1):
   if self.stack[index]['tag']==tag:
    del self.stack[index:];break
 def handle_data(self,value):
  if value.strip() and self.stack and self.stack[-1]['tag']=='head':self.handle_endtag('head')
  if self.stack and self.stack[-1]['hidden']:return
  self.parts.append(value)
  if self.stack and self.stack[-1]['anchor'] is not None:self.stack[-1]['anchor']['parts'].append(value)
def bracket_end(value,start):
 depth=1;cursor=start+1
 while cursor<len(value):
  if value[cursor]=='\\' and cursor+1<len(value):cursor+=2;continue
  if value[cursor]=='[':depth+=1
  if value[cursor]==']':
   depth-=1
   if not depth:return cursor
  cursor+=1
 return None

def inline_target_end(value,start):
 cursor=start+1
 while cursor<len(value) and value[cursor].isspace():cursor+=1
 if cursor>=len(value):return None
 if value[cursor]=='<':
  cursor+=1
  while cursor<len(value):
   if value[cursor]=='\\' and cursor+1<len(value):cursor+=2;continue
   if value[cursor]=='>':cursor+=1;break
   if value[cursor] in '<\r\n':return None
   cursor+=1
  else:return None
 else:
  depth=0
  while cursor<len(value) and not value[cursor].isspace():
   ch=value[cursor]
   if ch=='\\' and cursor+1<len(value):cursor+=2;continue
   if ch==')' and not depth:return cursor+1
   if ch=='(':depth+=1
   elif ch==')':depth-=1
   cursor+=1
  if depth:return None
 before_space=cursor
 while cursor<len(value) and value[cursor].isspace():cursor+=1
 if cursor<len(value) and value[cursor]==')':return cursor+1
 if cursor==before_space or cursor>=len(value) or value[cursor] not in ('"',"'",'('):return None
 close=')' if value[cursor]=='(' else value[cursor];cursor+=1
 while cursor<len(value):
  if value[cursor]=='\\' and cursor+1<len(value):cursor+=2;continue
  if value[cursor]==close:cursor+=1;break
  cursor+=1
 else:return None
 while cursor<len(value) and value[cursor].isspace():cursor+=1
 return cursor+1 if cursor<len(value) and value[cursor]==')' else None

def inline_link_text(value):
 pieces=[];cursor=0
 while cursor<len(value):
  if value[cursor]=='\\' and cursor+1<len(value):pieces.append(value[cursor:cursor+2]);cursor+=2;continue
  image=value[cursor:cursor+2]=='![';start=cursor+1 if image else cursor
  if value[start:start+1]=='[':
   end=bracket_end(value,start)
   if end is not None and value[end+1:end+2]=='(':
    target=inline_target_end(value,end+1)
    if target is not None:
     pieces.append('' if image else inline_link_text(value[start+1:end]));cursor=target;continue
  pieces.append(value[cursor]);cursor+=1
 return ''.join(pieces)

def rendered_plain(value):return ' '.join(re.findall(r'[^\W_]+',value.casefold()))
def plain(value,decode_entities=True):
 value=re.sub(r'^\s*(?:`{3,}|~{3,})[^\n]*$', '', value, flags=re.M)
 value=inline_link_text(value)
 return rendered_plain(html.unescape(value) if decode_entities else value)
def reference_label(value):return ' '.join(value.split()).casefold()
def resolve_reference_links(value,references):
 pieces=[];cursor=0
 while cursor<len(value):
  if value[cursor]=='\\' and cursor+1<len(value):pieces.append(value[cursor:cursor+2]);cursor+=2;continue
  image=value[cursor:cursor+2]=='![';start=cursor+1 if image else cursor
  if value[start:start+1]=='[':
   end=bracket_end(value,start)
   if end is not None:
    label=value[start+1:end];target=end+1;key=label
    inline=inline_target_end(value,target) if value[target:target+1]=='(' else None
    if inline is not None:
     pieces.append(value[cursor:inline]);cursor=inline;continue
    if value[target:target+1]=='[':
     ref_end=bracket_end(value,target)
     if ref_end is not None:key=value[target+1:ref_end] or label;target=ref_end+1
     else:key=None
    elif not image:key=None
    if key is not None and len(key)<=999 and reference_label(key) in references:
     pieces.append('' if image else label);cursor=target;continue
  pieces.append(value[cursor]);cursor+=1
 return ''.join(pieces)

# CommonMark raw HTML is stricter than HTMLParser's error recovery. Preserve
# HTML-looking ordinary text when it cannot be a valid inline HTML construct.
MD_ATTRIBUTE=r"""[A-Za-z_:][A-Za-z0-9_.:-]*(?:\s*=\s*(?:[^\s\"'=<>`]+|'[^']*'|"[^"]*"))?"""
MD_HTML=re.compile(r"""(?:<[A-Za-z][A-Za-z0-9-]*(?:\s+"""+MD_ATTRIBUTE+r""")*\s*/?>|</[A-Za-z][A-Za-z0-9-]*\s*>|<!--(?!(?:>|->))(?:(?!-->).)*-->|<\?.*?\?>|<![A-Z]+\s+[^>]*>|<!\[CDATA\[.*?\]\]>)""",re.S)
def markdown_inline_html(value):
 pieces=[];cursor=0
 while cursor<len(value):
  if value[cursor]=='<':
   match=MD_HTML.match(value,cursor)
   if match:pieces.append(match[0]);cursor=match.end();continue
   pieces.append('&lt;')
  else:pieces.append(value[cursor])
  cursor+=1
 return ''.join(pieces)

HTML_BLOCK_NAMES=frozenset('address article aside base basefont blockquote body caption center col colgroup dd details dialog dir div dl dt fieldset figcaption figure footer form frame frameset h1 h2 h3 h4 h5 h6 head header hr html iframe legend li link main menu menuitem nav noframes ol optgroup option p param search section summary table tbody td tfoot th thead title tr track ul'.split())
def raw_html_block_end(line,paragraph):
 tag=re.match(r' {0,3}<(/?)([A-Za-z][A-Za-z0-9-]*)(?=\s|/?>|$)',line)
 if tag:
  name=tag[2].casefold()
  if not tag[1] and name in ('script','pre','style','textarea'):return '</'+name+'>'
  if name in HTML_BLOCK_NAMES:return 'blank'
 stripped=line.lstrip()
 if stripped.startswith('<?'):return '?>'
 if stripped.startswith('<![CDATA['):return ']]>'
 if re.match(r'<![A-Z]',stripped):return '>'
 if not paragraph and MD_HTML.fullmatch(stripped.rstrip()):return 'blank'
 return None
def escaped_html_delimiters(value):
 # Backslash escapes are Markdown text before raw-HTML recognition. Even
 # runs leave a real delimiter; odd runs protect it from HTMLParser.
 return re.sub(r'(\\+)([<>])',lambda m:m[1][:-1]+html.escape(m[2]) if len(m[1])%2 else m[0],value)
def authored_plain(value,references=frozenset(),raw_html=False):
 if raw_html:
  parser=Visible();parser.feed(value);parser.close();return rendered_plain(' '.join(parser.parts))
 # Preserve literal HTML in Markdown code spans before extracting rendered
 # inline text. Do not unescape entities before parsing: escaped tags are text.
 runs=list(re.finditer(r'`+',value));pieces=[];cursor=0;index=0
 while index<len(runs):
  opening=runs[index];prefix=value[:opening.start()]
  if (len(prefix)-len(prefix.rstrip('\\')))%2:index+=1;continue
  closing=next((j for j in range(index+1,len(runs)) if len(runs[j][0])==len(opening[0])),None)
  if closing is None:index+=1;continue
  end=runs[closing];pieces.extend((escaped_html_delimiters(inline_link_text(resolve_reference_links(value[cursor:opening.start()],references))),'<code>'+html.escape(value[opening.end():end.start()])+'</code>'))
  cursor=end.end();index=closing+1
 pieces.append(escaped_html_delimiters(inline_link_text(resolve_reference_links(value[cursor:],references))))
 source=''.join(pieces)
 # CommonMark URI/email autolinks are visible text, not HTML start tags.
 source=re.sub(r'<([A-Za-z][A-Za-z0-9+.-]{1,31}:[^<>\x00-\x20]*|[A-Za-z0-9.!#$%&\'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?)>',lambda m:'<a>'+html.escape(m[1])+'</a>',source)
 parser=Visible();parser.feed(markdown_inline_html(source));parser.close()
 return rendered_plain(' '.join(parser.parts))

def inline_video_source(line):
 # A non-rendered trailing comment does not turn a video paragraph into text.
 line=re.sub(r'(?:\s*<!--(?:(?!-->).)*-->)+\s*$', '', line, flags=re.S)
 line=line.strip();end=bracket_end(line,0) if line.startswith('[') else None
 match=re.fullmatch(r'\((https://[^\s)]+)\)',line[end+1:]) if end is not None else None
 if not match:return None
 label,href=line[1:end],match[1]
 try:
  url=urlsplit(href)
  if url.hostname=='youtu.be':video_path=bool(url.path.strip('/'))
  elif url.hostname in ('youtube.com','www.youtube.com','www.youtube-nocookie.com'):
   video_path=url.path=='/watch' or url.path.startswith(('/embed/','/shorts/'))
  else:return None
  if not video_path:return None
  # A malformed ID on a video URL must fail, even if its label is visible.
  result=(label,href,None)
  if url.scheme!='https' or url.username or url.password or url.port not in (None,443):return result
  if url.hostname=='youtu.be':video_id=url.path[1:] if re.fullmatch(r'/[A-Za-z0-9_-]{11}',url.path) else None
  elif url.path=='/watch' and url.hostname!='www.youtube-nocookie.com':video_id=parse_qs(url.query,keep_blank_values=True).get('v',[''])[0]
  else:
   path=re.fullmatch(r'/(?:embed|shorts)/([A-Za-z0-9_-]{11})',url.path);video_id=path[1] if path else None
  return (label,href,video_id) if video_id and re.fullmatch(r'[A-Za-z0-9_-]{11}',video_id) else result
 except ValueError:return (label,href,None)

def reference_video_paragraph(block,references):
 # A whole rendered reference link is still a standalone video paragraph.
 # Keep the first definition's destination for exact iframe/fallback proof;
 # ordinary prose and literal code remain on the text-verification path.
 line=re.sub(r'(?:\s*<!--(?:(?!-->).)*-->)+\s*$','',block,flags=re.S).strip()
 if not line.startswith('['):return block
 end=bracket_end(line,0)
 if end is None:return block
 label=line[1:end];key=label;tail=line[end+1:]
 if tail:
  if not tail.startswith('[') or bracket_end(tail,0)!=len(tail)-1:return block
  key=tail[1:-1] or label
 href=references.get(reference_label(key))
 return '['+label+']('+href+')' if href else block

def inline_video_verified(line,parser,used=None):
 source=inline_video_source(line)
 if not source:return False
 label,href,video_id=source
 if not video_id or not plain(label):return False
 for index,player in enumerate(parser.players):
  # Each component owns one direct player and its caption. Page-wide links
  # and anchors in other figures cannot serve as this player's fallback.
  if not player['valid'] or len(player['frames'])!=1 or (used is not None and index in used):continue
  src,title=player['frames'][0]
  try:frame=urlsplit(src)
  except ValueError:continue
  if (frame.scheme=='https' and frame.netloc=='www.youtube-nocookie.com'
      and frame.path=='/embed/'+video_id and plain(title)==plain(label)
      and any(link['href']==href and plain(' '.join(link['parts'])) for link in player['links'])):
   if used is not None:used.add(index)
   return True
 return False

def reference_title_end(lines,index,container,initial=''):
 # A complete title may begin with the destination or on the following line.
 title=initial.strip()
 for cursor in range(index,len(lines)):
  if cursor>index:
   raw=lines[cursor].expandtabs(4)
   if not raw.strip() or (container and not raw.startswith(' '*container)):break
   title+=('\n' if title else '')+raw[container:].strip()
  if not title:continue
  if title[0] not in ('"',"'",'('):break
  if re.fullmatch(r"""(?:"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|\((?:[^()\\]|\\.)*\))""",title,re.S):return cursor
 return None

def reference_definition(lines,index,container,relative):
 opening=re.match(r' {0,3}\[',relative)
 if not opening:return None
 label=[];position=opening.end();destination_line=index;source=relative
 while True:
  if position>=len(source):
   destination_line+=1
   if destination_line>=len(lines):return None
   raw=lines[destination_line].expandtabs(4)
   if not raw.strip() or (container and not raw.startswith(' '*container)):return None
   label.append('\n');source=raw[container:];position=0
  ch=source[position]
  if ch=='\\' and position+1<len(source):label.extend(source[position:position+2]);position+=2
  elif ch==']':
   if source[position+1:position+2]!=':':return None
   source=source[position+2:].lstrip(' \t');break
  elif ch=='[':return None
  else:label.append(ch);position+=1
  if len(label)>999:return None
 label=''.join(label)
 if not label.strip() or len(label)>999:return None
 if not source:
  destination_line+=1
  if destination_line>=len(lines):return None
  raw=lines[destination_line].expandtabs(4)
  if not raw.strip() or (container and not raw.startswith(' '*container)):return None
  source=raw[container:].lstrip()
 # Angle destinations allow spaces but no raw angle brackets or line breaks.
 # Bare destinations require balanced, escape-aware parentheses and no controls.
 pos=0;depth=0
 if source.startswith('<'):
  pos=1
  while pos<len(source):
   ch=source[pos]
   if ch=='\\' and pos+1<len(source) and source[pos+1] in '<>\\':pos+=2;continue
   if ch=='>':pos+=1;break
   if ch=='<' or ch in '\r\n':return None
   pos+=1
  else:return None
 else:
  while pos<len(source) and source[pos] not in ' \t':
   ch=source[pos]
   if ord(ch)<32 or ord(ch)==127:return None
   if ch=='\\' and pos+1<len(source) and source[pos+1] in '()\\':pos+=2;continue
   if ch=='(':depth+=1
   if ch==')':
    depth-=1
    if depth<0:return None
   pos+=1
  if not pos or depth:return None
 remainder=source[pos:]
 if remainder and remainder[0] not in ' \t':return None
 if remainder.strip():
  end=reference_title_end(lines,destination_line,container,remainder)
  if end is None:return None
 else:
  end=reference_title_end(lines,destination_line,container)
 destination=source[:pos]
 if destination.startswith('<'):destination=destination[1:-1]
 destination=html.unescape(re.sub(r'\\([!"#$%&\'()*+,\-./:;<=>?@\[\]\\^_`{|}~])',r'\1',destination))
 return label,destination_line if end is None else end,destination

def quoted_block(lines,index,container=0):
 # Remove one explicit quote container; recursive classification preserves
 # nested quotes and literal '>' inside fenced/indented code. Lazy prose
 # continues the same paragraph, but blank/block boundaries end it.
 quoted=[];cursor=index;lazy=False;fence=None
 while cursor<len(lines):
  raw=lines[cursor].expandtabs(4)
  if container and raw.startswith(' '*container):raw=raw[container:]
  prefix=re.match(r' {0,3}>[ \t]?',raw)
  if prefix:
   relative=raw[prefix.end():];quoted.append(relative)
   marker=re.fullmatch(r' {0,3}(`{3,}|~{3,})(.*)',relative)
   if marker:
    if fence is None:fence=marker[1]
    elif marker[1][0]==fence[0] and len(marker[1])>=len(fence) and not marker[2].strip():fence=None
   lazy=bool(relative.strip()) and fence is None and not re.match(r' {0,3}(?:#{1,6}(?:\s|$)|<|>|[-*+]\s*$)',relative) and not relative.startswith('    ')
  elif lazy and raw.strip() and not re.match(r' {0,3}(?:>|#{1,6}(?:\s|$)|`{3,}|~{3,}|[-*+](?:\s|$)|[0-9]{1,9}[.)](?:\s|$)|<)',raw):quoted.append(raw)
  else:break
  cursor+=1
 return quoted,cursor-1

def publication_markdown_blocks(body_lines):
 # Keep fence identity/length and indentation until block classification. Fences
 # interrupt prose; indented code starts only outside an existing paragraph.
 paragraph=[];paragraph_kind='paragraph';code=None;fence=None;fence_indent=0;list_indent=None;list_marker=None;comment=False;raw_html=[];html_end=None
 lines='\n\n'.join(body_lines).replace('\r\n','\n').split('\n');skip_through=-1
 for source_index,raw in enumerate(lines):
  if source_index<=skip_through:continue
  if html_end is not None:
   if html_end=='blank' and not raw.strip():
    yield 'html','\n'.join(raw_html);raw_html=[];html_end=None;continue
   raw_html.append(raw)
   if html_end!='blank' and html_end in raw.casefold():
    yield 'html','\n'.join(raw_html);raw_html=[];html_end=None
   continue
  if fence is not None:
   expanded=raw.expandtabs(4)
   if fence_indent and raw.strip() and not expanded.startswith(' '*fence_indent):
    # A dedent ends the list container even without a closing fence.
    yield 'code','\n'.join(code);code=None;fence=None;fence_indent=0;list_indent=None;list_marker=None
   else:
    relative=expanded[fence_indent:] if fence_indent else raw
    if re.fullmatch(r' {0,3}'+re.escape(fence[0])+r'{'+str(len(fence))+r',}[ \t]*',relative):
     yield 'code','\n'.join(code);code=None;fence=None;fence_indent=0
    else:code.append(relative)
    continue
  if comment:
   end=raw.find('-->')
   if end<0:continue
   comment=False
   raw=raw[end+3:].lstrip()
  if not raw.strip():
   if code is not None:code.append('')
   else:
    if paragraph:yield paragraph_kind,' '.join(paragraph);paragraph=[]
    paragraph_kind='paragraph'
   continue
  expanded=raw.expandtabs(4)
  if list_indent is not None and not paragraph and not expanded.startswith(' '*list_indent):list_indent=None;list_marker=None
  container=list_indent if list_indent is not None and expanded.startswith(' '*list_indent) else 0
  relative=expanded[container:];indented=relative.startswith('    ')
  if code is not None:
   if indented:
    code.append(relative[4:]);continue
   yield 'code','\n'.join(code).rstrip('\n');code=None
  if re.match(r' {0,3}>',relative):
   if paragraph:yield paragraph_kind,' '.join(paragraph);paragraph=[]
   paragraph_kind='paragraph'
   # Quote prefixes are measured after the enclosing list indentation.
   quoted,skip_through=quoted_block(lines,source_index,container)
   yield from publication_markdown_blocks(['\n'.join(quoted)])
   continue
  while re.match(r' {0,3}<!--',raw):
   if paragraph:yield paragraph_kind,' '.join(paragraph);paragraph=[]
   paragraph_kind='paragraph';end=raw.find('-->');comment=end<0
   raw='' if comment else raw[end+3:].lstrip()
  if not raw.strip():continue
  expanded=raw.expandtabs(4);relative=expanded[container:] if expanded.startswith(' '*container) else expanded
  indented=relative.startswith('    ')
  definition=reference_definition(lines,source_index,container,relative) if not paragraph and not indented else None
  if definition:
   label,skip_through,destination=definition
   yield 'reference','['+label+']: '+destination;continue
  opening=re.fullmatch(r' {0,3}(`{3,}|~{3,})(.*)',relative)
  if opening and not (opening[1][0]=='`' and '`' in opening[2]):
   if paragraph:yield paragraph_kind,' '.join(paragraph);paragraph=[]
   paragraph_kind='paragraph';fence=opening[1];fence_indent=container;code=[]
   if not container:list_indent=None;list_marker=None
   continue
  if indented:
   if paragraph:paragraph.append(raw.strip())
   else:code=[relative[4:]]
   continue
  html_end=raw_html_block_end(relative,paragraph)
  if html_end is not None:
   if paragraph:yield paragraph_kind,' '.join(paragraph);paragraph=[]
   paragraph_kind='paragraph';raw_html=[relative]
   if html_end!='blank' and html_end in relative.casefold():
    yield 'html','\n'.join(raw_html);raw_html=[];html_end=None
   continue
  line=raw.strip()
  heading=re.fullmatch(r'#{1,6}\s+(.+)',line)
  item=re.fullmatch(r'(?:[-*+]|[0-9]{1,9}[.)])(?:\s+(.+))?',line)
  marker=re.match(r'([-*+]|([0-9]{1,9})([.)]))(?:[ \t]+|$)',expanded.lstrip()) if item else None
  marker_key=(len(expanded)-len(expanded.lstrip()),marker[3]) if marker and marker[2] else None
  # Only a start number of 1 can interrupt prose. Matching sibling markers
  # continue an existing ordered list without stripping numbers from prose.
  if marker and marker[2] and int(marker[2])!=1 and paragraph and marker_key!=list_marker:item=None
  if item and not item[1] and paragraph:item=None
  if heading or item:
   if paragraph:yield paragraph_kind,' '.join(paragraph);paragraph=[]
   paragraph_kind='text' if item and item[1] else 'paragraph'
   if item:
    list_indent=len(expanded)-len(expanded.lstrip())+(marker.end() if item[1] else len(marker[1])+1);list_marker=marker_key
    padding=marker.end()-len(marker[1])
    if padding>4:
     list_indent-=padding-1;code=[expanded[list_indent+4:]];paragraph_kind='paragraph'
    elif item[1]:paragraph=[item[1]]
   else:
    if list_indent is not None and not expanded.startswith(' '*list_indent):list_indent=None;list_marker=None
    yield 'text',heading[1]
  else:paragraph.append(line)
 if paragraph:yield paragraph_kind,' '.join(paragraph)
 if code is not None:yield 'code','\n'.join(code)
 if raw_html:yield 'html','\n'.join(raw_html)

def validate_live_html(item,data):
 parser=Visible();parser.feed(data.decode('utf-8'));url='https://abvx.xyz'+item['enrichment']['canonical_path']
 text=rendered_plain(' '.join(parser.parts))
 if parser.canonical!=[url] or plain(item['title']) not in text:raise ValueError('Production canonical/title not verified')
 required=0;used=set();cursor=0;visible=' '+text+' '
 blocks=list(publication_markdown_blocks(item['payload']['body_lines']))
 references={}
 for kind,block in blocks:
  if kind=='reference':
   end=bracket_end(block,0);references.setdefault(reference_label(block[1:end]),block[end+2:].strip())
 for kind,block in blocks:
  if kind=='reference':continue
  video=reference_video_paragraph(block,references) if kind=='paragraph' else block
  if kind=='paragraph' and inline_video_source(video) is not None:
   required+=1
   if not inline_video_verified(video,parser,used):raise ValueError('Authored inline video not verified')
  else:
   expected=rendered_plain(block) if kind=='code' else authored_plain(block,references,raw_html=kind=='html')
   if (kind in ('text','paragraph','html') and expected) or len(expected)>12:
    required+=1;needle=' '+expected+' ';position=visible.find(needle,cursor)
    if position<0:raise ValueError('Authored production text not verified')
    cursor=position+len(needle)-1
 if not required:raise ValueError('Authored production text not verified')
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

def verify_publication_inputs(root,item_id,site,*,checked_tree=None):
 item=_load_item(root,item_id);directory=folder(root,item_id)
 if item['status']!='PUBLISH_PACKET_EMITTED' or item['human_gate'].get('approved_content_sha256')!=_approval_fingerprint(item):raise ValueError('Approved current handoff required')
 session=json.loads((directory/'session.json').read_text());checks=json.loads((directory/'checks.json').read_text())
 if session.get('itemId')!=item_id or session.get('origin') not in ('OBSERVED','SYNTHETIC') or session.get('workflowVersion')!=VERSION:raise ValueError('Valid publication session required')
 site=verified_site(root,item,site)
 if checks.get('kind')!='AbvxPublicationChecks' or checks.get('itemId')!=item_id or checks.get('approvalDigest')!=_approval_fingerprint(item) or checks.get('status')!='PASS' or checks.get('treeDigest')!=(checked_tree if checked_tree is not None else tree_digest(site)) or [c.get('ref') for c in checks['checks']]!=['check:'+n for n in check_names(checks)] or any(c.get('status')!='PASS' for c in checks['checks']):raise ValueError('Fresh passing checks for exact site tree required')
 validate_qa_scope(checks.get('qaScope'),item)
 # Verify logs still exist with their recorded digest; do not export their contents.
 for c in checks['checks']:
  name=c['ref'][6:].replace(':','-');log=directory/f"{name}-{c['sha256'][:12]}.log"
  if hashlib.sha256(log.read_bytes()).hexdigest()!=c['sha256']:raise ValueError('Check evidence changed')
 packet=json.loads((root/item['publication']['packet_ref']).read_text())
 if packet['payload']!=item['payload'] or packet['slug']!=item['slug']:raise ValueError('Publish packet changed')
 return item,session,checks,site

def complete_publication(root,item_id,site,*,owner_minutes='UNKNOWN',rework_count,cortex_root=None):
 directory=folder(root,item_id)
 if (directory/'cycle-claim.json').exists():raise ValueError('Complete the independent cycle; member outcomes would duplicate one batch')
 if owner_minutes!='UNKNOWN':_integer(owner_minutes)
 _integer(rework_count)
 item,session,checks,site=verify_publication_inputs(root,item_id,site)
 url='https://abvx.xyz'+item['enrichment']['canonical_path']
 if not (directory/'outcome.json').exists():
  live_digest=validate_live_html(item,fetch_production(url));end=utc()
  row={'schemaVersion':1,'kind':'AbvxOsProcessOutcome','tenant':'abvx-os','runId':item_id,'workflowId':'site.content.publish','workflowVersion':VERSION,'origin':session['origin'],'startedAt':session['startedAt'],'completedAt':end,'status':'PASS','elapsedSeconds':round((_time(end)-_time(session['startedAt'])).total_seconds(),6),'ownerMinutes':owner_minutes,'reworkCount':rework_count,'qualityGate':'PASS','safetyGate':'PASS','evidence':[{'ref':'workload:publication-profile','sha256':digest({**session['workload'],'buildMode':checks.get('buildMode'),**qa_profile(checks)})},{'ref':'production:authored-text','sha256':live_digest},{'ref':'approval:content','sha256':_approval_fingerprint(item)},*[{'ref':c['ref'],'sha256':c['sha256']} for c in checks['checks']]]}
  validate_outcome(row);_write_once(directory/'outcome.json',row)
 else:
  row=validate_outcome(json.loads((directory/'outcome.json').read_text()))
  expected={'runId':item_id,'workflowId':'site.content.publish','workflowVersion':VERSION,'origin':session['origin'],'startedAt':session['startedAt'],'ownerMinutes':owner_minutes,'reworkCount':rework_count,'status':'PASS','qualityGate':'PASS','safetyGate':'PASS'}
  evidence=[{'ref':'workload:publication-profile','sha256':digest({**session['workload'],'buildMode':checks.get('buildMode'),**qa_profile(checks)})},{'ref':'approval:content','sha256':_approval_fingerprint(item)},*[{'ref':c['ref'],'sha256':c['sha256']} for c in checks['checks']]]
  retained=[entry for entry in row['evidence'] if entry['ref']!='production:authored-text']
  if any(row[key]!=value for key,value in expected.items()) or retained!=evidence or sum(entry['ref']=='production:authored-text' for entry in row['evidence'])!=1:raise ValueError('Immutable publication measurement differs')
  # Re-verify retained production evidence before completing an interrupted export.
  if not (directory/'batch.json').exists() and row['evidence'][1]!={'ref':'production:authored-text','sha256':validate_live_html(item,fetch_production(url))}:raise ValueError('Retained production evidence differs')
 batch=build_packet([row],'publication:'+item_id,row['completedAt']);_write_once(directory/'batch.json',batch)
 result={'status':'RECORDED','origin':row['origin'],'cortexStatus':'PENDING_TRANSFER','executionAuthorized':False}
 if cortex_root:
  if row['origin']!='OBSERVED':raise ValueError('Synthetic publication cannot enter operational Cortex history')
  receipt=transfer_publication(root,item_id,cortex_root);result.update(cortexStatus=receipt['status'])
 return result

def complete_cycle(root,run_id,site,*,rework_count,cortex_root=None):
 """One observation per release, including shared preparation, checks and deployment wait."""
 _integer(rework_count)
 directory=folder(root,run_id);cycle=json.loads((directory/'cycle.json').read_text())
 target=directory/'outcome.json'
 if target.exists() and validate_outcome(json.loads(target.read_text()))['status']!='PASS':raise ValueError('Cycle already has a terminal failure/cancellation')
 if cycle.get('schemaVersion')!=2 or cycle.get('kind')!='AbvxPublicationCycle' or cycle.get('runId')!=run_id or cycle.get('workflowVersion') not in PUBLICATION_VERSIONS:
  raise ValueError('Started publication cycle required')
 items=cycle.get('itemIds')
 if not isinstance(items,list) or not 1<=len(items)<=20 or len(set(items))!=len(items) or run_id in items or cycle.get('mode')!=('single' if len(items)==1 else 'batch'):
  raise ValueError('Bound cycle members required')
 site=Path(site).resolve();sha=clean_site_sha(site);deployment=deployment_snapshot(sha);tree=tree_digest(site)
 if _time(deployment.get('deploymentCreatedAt'))<_time(cycle['startedAt']):raise ValueError('Production release predates this publication cycle')
 if _time(deployment.get('mergedAt'))<_time(cycle['startedAt']):raise ValueError('Merged source predates this publication cycle')
 proofs=[];profiles=[];origins=set();shared_checks=None
 for item_id in items:
  if json.loads((folder(root,item_id)/'cycle-claim.json').read_text())!={'runId':run_id} or (folder(root,item_id)/'outcome.json').exists():
   raise ValueError('Member already counted or belongs to another cycle')
  item,session,checks,_=verify_publication_inputs(root,item_id,site,checked_tree=tree)
  if _time(session['startedAt'])<_time(cycle['startedAt']):raise ValueError('Cycle began after intake')
  common={'treeDigest':checks['treeDigest'],'buildMode':checks.get('buildMode'),'checks':checks['checks']}
  if 'qaScope' in checks:common['qaScope']=checks['qaScope']
  if 'checkProfile' in checks:common['checkProfile']=checks['checkProfile']
  if cycle['workflowVersion']=='publication-v2-batch-validation' and shared_checks is not None and common!=shared_checks:raise ValueError('Batch-validation requires one shared passing release receipt')
  shared_checks=common
  origins.add(session['origin']);profiles.append({**session['workload'],'buildMode':checks.get('buildMode'),**qa_profile(checks)})
  live=validate_live_html(item,fetch_production('https://abvx.xyz'+item['enrichment']['canonical_path']))
  proofs.append({'itemId':item_id,'approvalDigest':_approval_fingerprint(item),'checksDigest':digest(checks),'productionHtmlDigest':live})
 if len(origins)!=1:raise ValueError('Cannot mix synthetic and observed cycle members')
 stable=lambda value:{k:v for k,v in value.items() if not k.endswith('ResponseDigest')}
 if stable(deployment_snapshot(sha))!=stable(deployment) or clean_site_sha(site)!=sha or tree_digest(site)!=tree:
  raise ValueError('Source or deployment changed during cycle closeout')
 profile={'mode':cycle['mode'],'items':sorted(profiles,key=digest)}
 evidence=[ELAPSED_POLICY,{'ref':'cycle:'+run_id,'sha256':digest(cycle)},
           {'ref':'workload:publication-profile','sha256':digest(profile)},
           {'ref':'production:cycle-members','sha256':digest(proofs)},
           {'ref':'production:deployed-sha','sha256':digest(sha)},
           {'ref':'production:deployment','sha256':digest(stable(deployment))},*trial_evidence(root,cycle)]
 target=directory/'outcome.json'
 end=utc()
 if target.exists():end=json.loads(target.read_text())['completedAt']
 row={'schemaVersion':1,'kind':'AbvxOsProcessOutcome','tenant':'abvx-os','runId':run_id,
      'workflowId':'site.content.publish','workflowVersion':cycle['workflowVersion'],'origin':origins.pop(),
      'startedAt':cycle['startedAt'],'completedAt':end,'status':'PASS',
      'elapsedSeconds':round((_time(end)-_time(cycle['startedAt'])).total_seconds(),6),
      'ownerMinutes':'UNKNOWN','reworkCount':rework_count,'qualityGate':'PASS','safetyGate':'PASS','evidence':evidence}
 validate_outcome(row)
 if target.exists() and json.loads(target.read_text())!=row:raise ValueError('Immutable terminal publication evidence differs')
 release=folder(root,'cycle-lock')/'releases'/f'{sha}.json'
 if release.resolve()!=release:raise ValueError('Symlink release reservation forbidden')
 _write_once(release,{'runId':run_id})
 _write_once(directory/'cycle-proof.json',{'cycle':cycle,'profile':profile,'members':proofs,'deployedSha':sha,'deployment':stable(deployment)})
 _write_once(target,row)
 _write_once(directory/'batch.json',build_packet([row],'publication:'+run_id,end))
 result={'status':'RECORDED','origin':row['origin'],'elapsedSeconds':row['elapsedSeconds'],
         'items':len(items),'mode':cycle['mode'],'cortexStatus':'PENDING_TRANSFER','executionAuthorized':False}
 if cortex_root:result['cortexStatus']=transfer_publication(root,run_id,cortex_root)['status']
 return result


def cited_batches(root,context):
 results=context.get('results')
 if not isinstance(results,list) or not 1<=len(results)<=20:raise ValueError('Bounded Cortex context required')
 packets=[]
 for packet_id in dict.fromkeys(result['sourcePacketId'] for result in results):
  if not isinstance(packet_id,str) or not re.fullmatch(r'publication:[a-z0-9]+(?:-[a-z0-9]+)*',packet_id):raise ValueError('Publication source batch required')
  packet=validate_packet(json.loads((folder(root,packet_id.removeprefix('publication:'))/'batch.json').read_text()))
  if packet['packetId']!=packet_id:raise ValueError('Cited batch identity mismatch')
  packets.append(packet)
 return packets

def transfer_publication(root,item_id,cortex_root):
 directory=folder(root,item_id);batch=validate_packet(json.loads((directory/'batch.json').read_text()))
 if batch['packetId']!='publication:'+item_id or len(batch['payload']['outcomes'])!=1:raise ValueError('Selected publication batch required')
 row=batch['payload']['outcomes'][0]
 if row['runId']!=item_id or row['workflowId']!='site.content.publish' or row['workflowVersion'] not in ({VERSION}|PUBLICATION_VERSIONS) or row!=validate_outcome(json.loads((directory/'outcome.json').read_text())):raise ValueError('Publication outcome binding mismatch')
 if row['origin']!='OBSERVED':raise ValueError('Synthetic publication cannot enter operational Cortex history')
 cortex=Path(cortex_root).resolve();target=cortex/'data/abvx-os/publications'/item_id
 result=subprocess.run(['node','src/abvx-os-receive.mjs','--packet',str((directory/'batch.json').resolve()),'--context-out',str(target/'context.json'),'--candidate-out',str(target/'candidate.json')],cwd=cortex,capture_output=True,timeout=30)
 if result.returncode:raise ValueError('Cortex transfer failed; retained local outcome can be retried')
 context=json.loads((target/'context.json').read_text());candidate=json.loads((target/'candidate.json').read_text())
 # Original batches for previous publications are explicitly enumerated here, not manuscripts.
 packets=cited_batches(root,context)
 receipt=inspect_candidate(context,candidate,row['workflowVersion'],packets);_write_once(directory/'cortex-review.json',receipt)
 return receipt


def github_json(endpoint):
 # The host, repository and GET endpoint are fixed by the caller; never print auth/error output.
 try:
  result=subprocess.run(['gh','api','--hostname','github.com','--method','GET',endpoint],capture_output=True,check=True,timeout=30)
 except (OSError,subprocess.SubprocessError) as error:
  raise ValueError('GitHub deployment evidence unavailable') from error
 if len(result.stdout)>2*1024*1024:raise ValueError('GitHub deployment response exceeds bound')
 return json.loads(result.stdout)

def deployment_snapshot(sha):
 endpoint='repos/markoblogo/ABVXsite/deployments?environment=Production&per_page=1'
 deployments=github_json(endpoint)
 if not isinstance(deployments,list) or len(deployments)!=1:raise ValueError('Latest production deployment required')
 deployment=deployments[0]
 if not isinstance(deployment,dict) or type(deployment.get('id')) is not int or deployment['id']<=0 or deployment.get('environment')!='Production' or deployment.get('sha')!=sha:
  raise ValueError('Production deployment SHA differs from checked checkout')
 statuses=github_json(f"repos/markoblogo/ABVXsite/deployments/{deployment['id']}/statuses?per_page=1")
 if not isinstance(statuses,list) or len(statuses)!=1:raise ValueError('Latest deployment status required')
 status=statuses[0]
 if not isinstance(status,dict) or type(status.get('id')) is not int or status['id']<=0 or status.get('state')!='success' or status.get('environment')!='Production':
  raise ValueError('Successful production deployment required')
 now=_time(utc())
 for value in (deployment,status):
  if _time(value.get('created_at'))>now:raise ValueError('Future deployment evidence rejected')
 if _time(status['created_at'])<_time(deployment['created_at']):raise ValueError('Deployment status predates deployment')
 pulls=github_json(f'repos/markoblogo/ABVXsite/commits/{sha}/pulls?per_page=100')
 if not isinstance(pulls,list):raise ValueError('Merged site PR evidence required')
 matches=[p for p in pulls if isinstance(p,dict) and p.get('merge_commit_sha')==sha and p.get('merged_at') and
          p.get('base',{}).get('ref')=='main' and p.get('base',{}).get('repo',{}).get('full_name')=='markoblogo/ABVXsite']
 if len(matches)!=1 or type(matches[0].get('number')) is not int or matches[0]['number']<=0:
  raise ValueError('Deployment SHA must be the exact merge commit of one site PR')
 merged=matches[0]
 if _time(merged['merged_at'])>_time(deployment['created_at']):raise ValueError('Production deployment predates merge')
 return {'provider':'github-deployments','repository':'markoblogo/ABVXsite','deploymentId':deployment['id'],
         'statusId':status['id'],'environment':'Production','state':'success','sha':sha,
         'deploymentCreatedAt':deployment['created_at'],'statusCreatedAt':status['created_at'],
         'deploymentResponseDigest':digest({key:deployment[key] for key in ('id','sha','environment','created_at')}),
         'statusResponseDigest':digest({key:status[key] for key in ('id','state','environment','created_at')}),
         'mergedPrNumber':merged['number'],'mergedAt':merged['merged_at'],
         'mergeResponseDigest':digest({'number':merged['number'],'merge_commit_sha':sha,'merged_at':merged['merged_at'],
                                     'base':'main','repository':'markoblogo/ABVXsite'})}

def clean_site_sha(site):
 status=subprocess.run(['git','status','--porcelain','--untracked-files=all'],cwd=site,capture_output=True,check=True).stdout
 if status.strip():raise ValueError('Committed clean checked site checkout required')
 sha=subprocess.run(['git','rev-parse','HEAD'],cwd=site,capture_output=True,check=True).stdout.decode().strip()
 if not re.fullmatch('[a-f0-9]{40}',sha):raise ValueError('Full Git commit SHA required')
 return sha

def verify_first_cycle(root,item_id,site,cortex_root):
 """Explicit read-only source/deployment probes; retain local acceptance proof, enable nothing."""
 directory=folder(root,item_id)
 row=validate_outcome(json.loads((directory/'outcome.json').read_text()))
 if row['runId']!=item_id or row['origin']!='OBSERVED' or row['workflowId']!='site.content.publish' or row['workflowVersion']!=VERSION or row['status']!='PASS' or row['qualityGate']!='PASS' or row['safetyGate']!='PASS':
  raise ValueError('Verified observed native-publication outcome required')
 if not (directory/'cortex-review.json').is_file():raise ValueError('Complete scoped Cortex return before first-cycle acceptance')
 # Reuse exact source, approval, check-log and tree verification. This preserves the immutable measurement.
 complete_publication(root,item_id,site,owner_minutes=row['ownerMinutes'],rework_count=row['reworkCount'])
 sha=clean_site_sha(site)
 deployment=deployment_snapshot(sha)
 item=_load_item(root,item_id)
 live_digest=validate_live_html(item,fetch_production('https://abvx.xyz'+item['enrichment']['canonical_path']))
 review=transfer_publication(root,item_id,cortex_root)
 if review.get('executionAuthorized') is not False or review.get('status') not in ('RECORDED_READY_FOR_ANALYSIS','NEEDS_MEASUREMENT'):
  raise ValueError('Independently validated model-free OS return required')
 # A new rollout while probing cannot be silently accepted against the previous source.
 stable=lambda value:{key:item for key,item in value.items() if not key.endswith('ResponseDigest')}
 if stable(deployment_snapshot(sha))!=stable(deployment):raise ValueError('Deployment changed during first-cycle verification')
 complete_publication(root,item_id,site,owner_minutes=row['ownerMinutes'],rework_count=row['reworkCount'])
 if clean_site_sha(site)!=sha:raise ValueError('Checked source changed during first-cycle verification')
 context_file=Path(cortex_root).resolve()/'data/abvx-os/publications'/item_id/'context.json'
 if context_file.resolve()!=context_file:raise ValueError('Symlink Cortex context forbidden')
 context=json.loads(context_file.read_text())
 candidate_file=context_file.with_name('candidate.json')
 if candidate_file.resolve()!=candidate_file:raise ValueError('Symlink Cortex candidate forbidden')
 candidate=json.loads(candidate_file.read_text())
 if inspect_candidate(context,candidate,VERSION,cited_batches(root,context))!=review:raise ValueError('Cortex return changed during first-cycle verification')
 batch=validate_packet(json.loads((directory/'batch.json').read_text()))
 receipt={'schemaVersion':1,'kind':'AbvxPublicationFirstCycleVerification','status':'VERIFIED','itemId':item_id,
          'origin':'OBSERVED','verifiedAt':utc(),'deployedSha':sha,'deployment':deployment,
          'outcomeDigest':digest(row),'sourcePacketDigest':digest(batch),
          'contextDigest':digest(context),'osReviewDigest':digest(review),
          'productionHtmlDigest':live_digest,'executionAuthorized':False}
 target=directory/'first-cycle.json'
 if target.exists():
  previous=json.loads(target.read_text())
  _time(previous.get('verifiedAt'))
  receipt['verifiedAt']=previous['verifiedAt']
 _write_once(target,receipt)
 return receipt

def main(argv,root):
 parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='action',required=True)
 begin=sub.add_parser('begin');begin.add_argument('--run',required=True);begin.add_argument('--item',action='append',required=True);begin.add_argument('--trial',choices=CYCLE_VERSIONS,default='baseline');begin.add_argument('--series')
 series=sub.add_parser('series-begin');series.add_argument('--series',required=True);series.add_argument('--change',required=True,choices=sorted(set(PUBLICATION_CHANGES.values())));series.add_argument('--baseline-run',action='append',required=True);series.add_argument('--held-out-run',action='append',required=True)
 abort=sub.add_parser('abort-cycle');abort.add_argument('--run',required=True);abort.add_argument('--status',required=True,choices=['FAIL','CANCELLED']);abort.add_argument('--rework-count',required=True,type=int);abort.add_argument('--cortex-root',type=Path);abort.add_argument('--origin',choices=['OBSERVED','SYNTHETIC'])
 close=sub.add_parser('complete-cycle');close.add_argument('--run',required=True);close.add_argument('--site-root',required=True,type=Path);close.add_argument('--rework-count',required=True,type=int);close.add_argument('--cortex-root',type=Path)
 for name in ('check','complete','transfer','verify-first-cycle'):
  command=sub.add_parser(name);command.add_argument('--item',required=True)
  if name!='transfer':command.add_argument('--site-root',required=True,type=Path)
  if name=='check':command.add_argument('--reuse-checks',action='store_true')
  if name!='check':command.add_argument('--cortex-root',type=Path,required=name in ('transfer','verify-first-cycle'))
  if name=='complete':command.add_argument('--owner-minutes',default='UNKNOWN');command.add_argument('--rework-count',required=True,type=int)
 args=parser.parse_args(argv)
 if args.action=='begin':value=begin_cycle(root,args.run,args.item,trial=args.trial,series_id=args.series)
 elif args.action=='series-begin':value=begin_series(root,args.series,args.change,args.baseline_run,args.held_out_run)
 elif args.action=='abort-cycle':
  row=abort_cycle(root,args.run,status=args.status,rework_count=args.rework_count,cortex_root=args.cortex_root,origin=args.origin);value={'status':row['status'],'elapsedSeconds':row['elapsedSeconds'],'executionAuthorized':False}
 elif args.action=='complete-cycle':value=complete_cycle(root,args.run,args.site_root,rework_count=args.rework_count,cortex_root=args.cortex_root)
 elif args.action=='check':value=check_publication(root,args.item,args.site_root,reuse_checks=args.reuse_checks)
 elif args.action=='transfer':value=transfer_publication(root,args.item,args.cortex_root)
 elif args.action=='verify-first-cycle':
  receipt=verify_first_cycle(root,args.item,args.site_root,args.cortex_root)
  value={'status':receipt['status'],'deployedSha':receipt['deployedSha'],'executionAuthorized':False}
 else:value=complete_publication(root,args.item,args.site_root,owner_minutes='UNKNOWN' if args.owner_minutes=='UNKNOWN' else int(args.owner_minutes),rework_count=args.rework_count,cortex_root=args.cortex_root)
 print(json.dumps(value if args.action!='check' else {'status':value['status'],'checks':len(value['checks'])},sort_keys=True))
 return 1 if value.get('status')=='FAIL' else 0
