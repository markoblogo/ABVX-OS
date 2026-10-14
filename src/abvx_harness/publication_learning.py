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
 non_rendered=frozenset(('head','script','style','template','noscript','textarea','title'))
 def __init__(self):
  super().__init__();self.canonical=[];self.parts=[];self.stack=[];self.players=[]
 def handle_starttag(self,tag,attrs):
  # A browser keeps the first duplicate attribute, whereas dict keeps the
  # last. Ambiguous evidence or visibility attributes cannot prove release.
  seen=set()
  for key,_ in attrs:
   if key in seen and key in ('src','title','href','rel','hidden','inert','aria-hidden','style','open'):
    raise ValueError('Duplicate structural HTML attribute')
   seen.add(key)
  if self.stack and self.stack[-1]['tag']=='head' and tag not in ('html','head','base','basefont','bgsound','link','meta','noframes','script','style','template','title','noscript'):
   self.handle_endtag('head')
  attr=dict(attrs);parent=self.stack[-1] if self.stack else None
  namespace=parent['namespace'] if parent else 'html'
  if parent and ((namespace=='svg' and parent['tag'] in ('foreignobject','desc','title'))
      or (namespace=='math' and parent['tag'] in ('mi','mo','mn','ms','mtext') and tag not in ('mglyph','malignmark'))
      or (namespace=='math' and parent['tag']=='annotation-xml' and parent['html_integration'])):
   namespace='html'
  if namespace=='html' and tag in ('svg','math'):namespace=tag
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
  self.handle_starttag(tag,attrs)
  if tag=='iframe' and self.stack and self.stack[-1]['namespace']=='html' and self.stack[-1]['player'] is not None:self.stack[-1]['player']['valid']=False
  # Only foreign SVG/MathML elements honor the slash; HTML templates and
  # hidden ancestors stay open. Integration points switch children to HTML.
  if self.stack and self.stack[-1]['tag']==tag and self.stack[-1]['namespace']!='html':self.handle_endtag(tag)
 def handle_endtag(self,tag):
  for index in range(len(self.stack)-1,-1,-1):
   if self.stack[index]['tag']==tag:
    del self.stack[index:];break
 def handle_data(self,value):
  if value.strip() and self.stack and self.stack[-1]['tag']=='head':self.handle_endtag('head')
  if self.stack and self.stack[-1]['hidden']:return
  self.parts.append(value)
  if self.stack and self.stack[-1]['anchor'] is not None:self.stack[-1]['anchor']['parts'].append(value)
def plain(value):
 value=re.sub(r'^\s*(?:`{3,}|~{3,})[^\n]*$', '', value, flags=re.M)
 value=re.sub(r'!\[[^\]]*\]\([^)]*\)','',value);value=re.sub(r'\[([^\]]+)\]\([^)]*\)',r'\1',value)
 return ' '.join(re.findall(r'[^\W_]+',html.unescape(value).casefold()))
def authored_plain(value):
 # Preserve literal HTML in Markdown code spans before extracting rendered
 # inline text. Do not unescape entities before parsing: escaped tags are text.
 runs=list(re.finditer(r'`+',value));pieces=[];cursor=0;index=0
 while index<len(runs):
  opening=runs[index];closing=next((j for j in range(index+1,len(runs)) if len(runs[j][0])==len(opening[0])),None)
  if closing is None:index+=1;continue
  end=runs[closing];pieces.extend((value[cursor:opening.start()],'<code>'+html.escape(value[opening.end():end.start()])+'</code>'))
  cursor=end.end();index=closing+1
 pieces.append(value[cursor:])
 parser=Visible();parser.feed(''.join(pieces));parser.close()
 return plain(' '.join(parser.parts))

def inline_video_source(line):
 match=re.fullmatch(r'\[([^\]\n]+)\]\((https://[^\s)]+)\)',line.strip())
 if not match:return None
 label,href=match.groups()
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

def publication_markdown_blocks(body_lines):
 # Keep fence identity/length and indentation until block classification. Fences
 # interrupt prose; indented code starts only outside an existing paragraph.
 paragraph=[];paragraph_kind='paragraph';code=None;fence=None;fence_indent=0;list_indent=None;list_marker=None;comment=False
 for raw in '\n\n'.join(body_lines).replace('\r\n','\n').split('\n'):
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
   if raw[end+3:].strip():yield 'text',raw[end+3:]
   continue
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
  if re.match(r' {0,3}<!--',raw):
   if paragraph:yield paragraph_kind,' '.join(paragraph);paragraph=[]
   paragraph_kind='paragraph'
   end=raw.find('-->')
   comment=end<0
   if not comment and raw[end+3:].strip():yield 'text',raw[end+3:]
   continue
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
  line=raw.strip()
  heading=re.fullmatch(r'#{1,6}\s+(.+)',line)
  item=re.fullmatch(r'(?:[-*+]|[0-9]{1,9}[.)])\s+(.+)',line)
  marker=re.match(r'([-*+]|([0-9]{1,9})([.)]))\s+',expanded.lstrip()) if item else None
  marker_key=(len(expanded)-len(expanded.lstrip()),marker[3]) if marker and marker[2] else None
  # Only a start number of 1 can interrupt prose. Matching sibling markers
  # continue an existing ordered list without stripping numbers from prose.
  if marker and marker[2] and int(marker[2])!=1 and paragraph and marker_key!=list_marker:item=None
  if heading or item:
   if paragraph:yield paragraph_kind,' '.join(paragraph);paragraph=[]
   paragraph_kind='text' if item else 'paragraph'
   if item:
    list_indent=len(expanded)-len(expanded.lstrip())+marker.end();list_marker=marker_key
    paragraph=[item[1]]
   else:
    if list_indent is not None and not expanded.startswith(' '*list_indent):list_indent=None;list_marker=None
    yield 'text',heading[1]
  else:paragraph.append(line)
 if paragraph:yield paragraph_kind,' '.join(paragraph)
 if code is not None:yield 'code','\n'.join(code)

def validate_live_html(item,data):
 parser=Visible();parser.feed(data.decode('utf-8'));url='https://abvx.xyz'+item['enrichment']['canonical_path']
 text=plain(' '.join(parser.parts))
 if parser.canonical!=[url] or plain(item['title']) not in text:raise ValueError('Production canonical/title not verified')
 required=0;used=set()
 for kind,block in publication_markdown_blocks(item['payload']['body_lines']):
  if kind=='paragraph' and inline_video_source(block) is not None:
   required+=1
   if not inline_video_verified(block,parser,used):raise ValueError('Authored inline video not verified')
  else:
   expected=plain(block) if kind=='code' else authored_plain(block)
   if (kind=='text' and expected) or len(expected)>12:
    required+=1
    if ' '+expected+' ' not in ' '+text+' ':raise ValueError('Authored production text not verified')
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
