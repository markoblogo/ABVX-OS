"""Offline, evidence-bound cheap screening; no collectors or commercial state writes."""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
import time
import math
from collections import Counter
from datetime import datetime, date, timedelta
from functools import lru_cache
from urllib.parse import urlsplit, parse_qsl, urlencode
from pathlib import Path

from .harness import ValidationError
from .schema_validation import load_draft_2020_12_validator, draft_2020_12_validator

SCHEMAS=Path(__file__).resolve().parents[2]/'schemas'
STAGES=('RAW','NORMALIZE','CORROBORATE','QUICK_SCREEN','QUEUE')
READING={'BOOK_BUYING_INTENT','BOOK_SERVED_LEARNING_INTENT','REFERENCE_INTENT','ENTERTAINMENT_READING_INTENT'}
WINDOWS={'BOOK_MARKET':(30,365),'SEARCH_INTENT':(7,30),'COMMUNITY':(30,90),'CHANGE_EVENT':(14,60),'CROSS_MARKET':(30,180),'PORTFOLIO_ADJACENCY':(30,90),'LLM_EXPANSION':(0,0)}
LIMITS={'max_raw':1000,'max_clusters':200,'max_quick_screens':40,'max_investigate':10,'max_per_subject':2,'max_owner_items':5}

def fail(message):
    raise ValidationError('Wide screener: '+message)

@lru_cache(maxsize=4)
def validator(name):
    return load_draft_2020_12_validator(SCHEMAS/name)

def shape(value,name):
    errors=list(validator(name).iter_errors(value))
    if errors:
        e=errors[0];fail('/'+'/'.join(map(str,e.absolute_path))+': '+e.message)

def stamp(value):
    t=datetime.fromisoformat(value.replace('Z','+00:00'))
    if t.tzinfo is None:fail('timestamps require timezone')
    return t

def load(path):
    try:
        if Path(path).stat().st_size>16*1024*1024:fail('input/run exceeds 16 MiB pilot limit')
        return json.loads(Path(path).read_text(),parse_constant=lambda s:fail('non-finite JSON number'))
    except (OSError,ValueError) as e:
        fail('cannot read JSON: '+str(e))

def policy(packet):
    supplied=packet.get('policy',{})
    return {**supplied,'limits':{**LIMITS,**supplied.get('limits',{})},'max_quick_age_days':supplied.get('max_quick_age_days',30),'max_next_research_minutes':supplied.get('max_next_research_minutes',20)}

def origin(uri,groups):
    host=(urlsplit(uri).hostname or '').casefold().removeprefix('www.')
    if urlsplit(uri).scheme!='https' or not host:fail('external source requires HTTPS origin')
    if re.fullmatch(r'(?:[^.]+\.)?amazon\.(?:com|fr)',host):return 'amazon'
    for ecosystem in ('reddit.com','youtube.com','google.com'):
        if host==ecosystem or host.endswith('.'+ecosystem):return ecosystem
    if host in groups:return groups[host]  # explicit corporate-origin merging only
    return host

def freshness(signal,packet):
    f=signal['freshness'];d=f['source_date']
    if not d or f['date_basis']=='UNKNOWN' or signal['provenance']['kind']!='EXTERNAL':return 'UNKNOWN'
    age=(stamp(packet['as_of']).date()-date.fromisoformat(d)).days
    if age<0:fail('future source date cannot corroborate current job')
    defaults=WINDOWS[signal['source_family']]
    limits=packet.get('policy',{}).get('freshness_windows_days',{}).get(signal['source_family'],{'fresh':defaults[0],'recent':defaults[1]})
    if limits['fresh']>limits['recent']:fail('freshness window order')
    return 'FRESH' if age<=limits['fresh'] else 'RECENT' if age<=limits['recent'] else 'STALE'

def checked(path):
    path=Path(path);packet=load(path);shape(packet,'BOOK_RADAR_WIDE_INPUT_SCHEMA_V1.json')
    def finite(node):
        if isinstance(node,float) and not math.isfinite(node):fail('non-finite numeric value')
        if isinstance(node,dict):
            for v in node.values():finite(v)
        elif isinstance(node,list):
            for v in node:finite(v)
    finite(packet)
    p=policy(packet);asof=stamp(packet['as_of']);evidence={};hashes={};size=0
    if len(packet['signals'])>p['limits']['max_raw']:fail('raw run budget exceeded')
    for e in packet['evidence']:
        if e['id'] in evidence:fail('duplicate evidence id')
        rel=Path(e['path']);resolved=(path.parent/rel).resolve()
        if rel.is_absolute() or '..' in rel.parts or not resolved.is_relative_to(path.parent.resolve()):fail('evidence path escapes input directory')
        if not resolved.is_file():fail('missing retained evidence')
        if resolved not in hashes:
            size+=resolved.stat().st_size
            if size>64*1024*1024:fail('retained evidence exceeds 64 MiB pilot limit')
            hashes[resolved]=hashlib.sha256(resolved.read_bytes()).hexdigest()
        if hashes[resolved]!=e['sha256']:fail('evidence hash mismatch')
        origin(e['source_uri'],p.get('origin_groups',{}));evidence[e['id']]=e
    seen=set()
    def refs(ids,market,language,external=False):
        for eid in ids:
            e=evidence.get(eid)
            if not e or e['market']!=market or e['language']!=language:fail('evidence reference / market-language mismatch')
            if external and e['kind']!='EXTERNAL':fail('LLM material cannot support observed market feature')
    for s in packet['signals']:
        if s['signal_id'] in seen:fail('duplicate signal id')
        seen.add(s['signal_id']);refs(s['evidence_ids'],s['market'],s['language'])
        if stamp(s['observed_at'])>asof:fail('future signal observation')
        if s['provenance']['kind']=='EXTERNAL':
            if not s['evidence_ids']:fail('external signal requires evidence')
            if s['source_family']=='LLM_EXPANSION':fail('LLM source family cannot be external corroboration')
            if any(evidence[i]['kind']!='EXTERNAL' or evidence[i]['source_uri']!=s['source'] for i in s['evidence_ids']):fail('external signal source provenance mismatch')
        if s.get('job_support','UNKNOWN')!='UNKNOWN' and s['provenance']['kind']!='EXTERNAL':fail('LLM cannot corroborate or contradict job')
        freshness(s,packet)
    screen_ids=set()
    for q in packet.get('quick_screens',[]):
        if q['cluster_id'] in screen_ids:fail('duplicate quick screen')
        screen_ids.add(q['cluster_id'])
        if stamp(q['observed_at'])>asof:fail('future quick screen')
        obs={}
        for o in q['observations']:
            if o['id'] in obs or not o['evidence_ids']:fail('observation identity/evidence missing')
            refs(o['evidence_ids'],q['market'],q['language'],True);obs[o['id']]=o
        for feature in q['features'].values():
            refs(feature['evidence_ids'],q['market'],q['language'],True)
            if feature['value']=='UNKNOWN':continue
            if not feature['observation_ids'] or not feature['evidence_ids']:fail('derived feature requires observation and evidence')
            supporting=set()
            for oid in feature['observation_ids']:
                if oid not in obs:fail('unknown feature observation')
                supporting.update(obs[oid]['evidence_ids'])
            if not set(feature['evidence_ids'])<=supporting:fail('feature evidence must derive from cited observations')
        if q['rights'] in ('BLOCK','POSSIBLE_BLOCK') and not obs:fail('rights block needs retained observation')
        ev=q.get('event')
        if ev:
            refs(ev['evidence_ids'],q['market'],q['language'],True)
            if any(ev[k] is not None for k in ('event_date','information_half_life_days','book_time_to_market_days')) and not ev['evidence_ids']:fail('event timing requires evidence')
    return packet

def canonical(text):
    return ' '.join(re.sub(r'[^\w]+', ' ', unicodedata.normalize('NFKC', text).casefold()).split())

def cluster_id(buyer_job, market, language):
    key=[canonical(buyer_job[k]) for k in ('audience','job','intent')]+[market,language]
    return 'wide:'+hashlib.sha256(json.dumps(key).encode()).hexdigest()[:24]

def _normalize(packet):
    groups={};aliases={canonical(k):canonical(v) for k,v in packet.get('aliases',{}).items()}
    for k,v in aliases.items():
        if not k or not v or (v in aliases and aliases[v]!=v):fail('aliases must map directly to final canonical text')
    for signal in packet['signals']:
        job=signal['buyer_job'].copy()
        for k in ('audience','job'):job[k]=aliases.get(canonical(job[k]),canonical(job[k]))
        if not job['audience'] or not job['job'] or not canonical(job['query']):fail('coherent buyer/job/query required')
        cid=cluster_id(job,signal['market'],signal['language'])
        if cid not in groups:
            groups[cid]={'cluster_id':cid,**job,'market':signal['market'],'language':signal['language'],'raw_signals':[],'query_family':[],'source_families':[]}
        c=groups[cid];c['raw_signals'].append(signal['signal_id']);c['query_family'].append(job['query']);c['source_families'].append(signal['source_family'])
        if any(c[k]!=job[k] for k in ('subject','category','bucket','mechanism')):fail('same buyer/job has conflicting breadth labels; normalize before screening')
    if len(groups)>policy(packet)['limits']['max_clusters']:fail('normalized job budget exceeded')
    for c in groups.values():
        c['raw_signals'].sort();c['raw_signal_count']=len(c['raw_signals']);c['query_family']=sorted(set(c['query_family']));c['source_families']=sorted(set(c['source_families']))
    return sorted(groups.values(),key=lambda c:c['cluster_id'])

def normalize(path):
    packet=checked(path)
    return {'schema_version':'book-radar-wide-normalization/v1','run_id':packet['run_id'],'origin':packet['origin'],'clusters':_normalize(packet),'canonical_state_written':False,'live_collection':False}

def check(path):
    p=checked(path);clusters=_normalize(p)
    known={c['cluster_id']:c for c in clusters}
    for q in p.get('quick_screens',[]):
        c=known.get(q['cluster_id'])
        if not c or (q['market'],q['language'])!=(c['market'],c['language']):fail('quick screen not bound to normalized market/language cluster')
    return {'status':'PASS','signals':len(p['signals']),'clusters':len(clusters),'origin':p['origin'],'live_collection':False,'canonical_state_written':False}

def feature(q,name):
    return q['features'][name]['value'] if q else 'UNKNOWN'

def cost_summary(packet,timings,counts):
    acq=packet.get('acquisition_costs',{});stages={}
    for stage in STAGES:
        supplied=acq.get(stage,{})
        stages[stage]={'machine_seconds':timings[stage],**{k:supplied.get(k) for k in ('external_api_usd','machine_usd','manual_minutes','owner_minutes')}}
    def total(k):
        vals=[v[k] for v in stages.values()]
        return None if any(v is None for v in vals) else sum(vals)
    money=None if total('external_api_usd') is None or total('machine_usd') is None else total('external_api_usd')+total('machine_usd')
    ratios={name:None if not counts[denom] or money is None else money/counts[denom] for name,denom in [('cost_per_raw_signal_usd','raw'),('cost_per_normalized_job_usd','normalized'),('cost_per_kill_usd','kill'),('cost_per_investigate_usd','investigate')]}
    return {'stages':stages,'total_usd':money,'manual_minutes':total('manual_minutes'),'owner_minutes':total('owner_minutes'),**ratios,'machine_seconds_per_raw':timings['RAW']/counts['raw'],'machine_seconds_per_screen':timings['QUICK_SCREEN']/counts['quick_screen'] if counts['quick_screen'] else None,'machine_seconds_per_kill':sum(timings.values())/counts['kill'] if counts['kill'] else None,'machine_seconds_per_investigate':sum(timings.values())/counts['investigate'] if counts['investigate'] else None,'owner_minutes_per_survivor':total('owner_minutes')/counts['investigate'] if total('owner_minutes') is not None and counts['investigate'] else None,'measurement_scope':'Machine processing measured; acquisition labor/cost supplied separately. Unknown remains null; zero-denominator ratios unavailable.','synthetic_costs_only':packet['origin']=='SYNTHETIC'}

def screen(path,previous=None):
    started=time.perf_counter();packet=checked(path);timings={s:0.0 for s in STAGES};timings['RAW']=time.perf_counter()-started
    t=time.perf_counter();clusters=_normalize(packet);timings['NORMALIZE']=time.perf_counter()-t
    p=policy(packet);evidence={e['id']:e for e in packet['evidence']};signals={s['signal_id']:s for s in packet['signals']};quick={q['cluster_id']:q for q in packet.get('quick_screens',[])}
    known={c['cluster_id']:c for c in clusters}
    if any(cid not in known or (q['market'],q['language'])!=(known[cid]['market'],known[cid]['language']) for cid,q in quick.items()):fail('quick screen cluster / market-language mismatch')
    candidates=[];screen_count=0;stage_entries=Counter(RAW=len(packet['signals']),NORMALIZE=len(clusters));corroborated=0
    def decide(c,decision,reason,stage):
        c.update(decision=decision,decision_reason=reason,stage=stage)
        c['interpretation']='Bounded evidence justifies deeper collection, not verified demand/cold start.' if decision=='INVESTIGATE' else 'Current assumptions reject further spend.' if decision=='KILL' else 'Missing evidence may change the decision; no automatic recheck.'
        c['next_required_evidence']=[] if decision=='KILL' else ['Retain current relevant organic sample and verify activity / edition / author context']
    for c in clusters:
        c.update(schema_version='book-radar-wide-cluster/v1',origin=packet['origin'],evidence_origins=[],corroboration={'status':'UNKNOWN','current_independent_origins':[],'evidence_ids':[]},quick_screen=None,activity_evidence={},entrant_signal={},incumbent_signal={},sponsored_signal={},query_relevance={},freshness='UNKNOWN',time_to_market={'status':'UNKNOWN'},unknowns=[],contradictions=[],research_cost={},kill_record=None,park=None,late_factory_cost_class='UNKNOWN',decision_evidence=[])
        ss=[signals[s] for s in c['raw_signals']];external=[s for s in ss if s['provenance']['kind']=='EXTERNAL'];ids=sorted({i for s in external for i in s['evidence_ids']});c['decision_evidence']=ids
        if not external:
            c['unknowns']=['EXTERNAL_JOB_EVIDENCE'];decide(c,'PARK','PARK_NO_EXTERNAL_EVIDENCE','NORMALIZE');continue
        if c['intent'] not in READING:
            decide(c,'KILL','GENERAL_INFORMATION_ONLY' if c['intent'] in ('GENERAL_INFORMATION_INTENT','NEWS_INTENT') else 'NO_BOOK_RELEVANCE','NORMALIZE');continue
        t=time.perf_counter();stage_entries['CORROBORATE']+=1
        origins=sorted({origin(s['source'],p.get('origin_groups',{})) for s in external});current=[s for s in external if freshness(s,packet) in ('FRESH','RECENT') and s.get('job_support')=='SUPPORTS'];freshorigins=sorted({origin(s['source'],p.get('origin_groups',{})) for s in current});c['evidence_origins']=origins
        contradictory=[s for s in external if s.get('job_support')=='CONTRADICTS' and freshness(s,packet) in ('FRESH','RECENT')]
        statuses=[freshness(s,packet) for s in external];c['freshness']=next((s for s in ('FRESH','RECENT','UNKNOWN','STALE') if s in statuses),'UNKNOWN')
        c['corroboration']={'status':'CORROBORATED' if len(freshorigins)>=2 else 'WEAK' if freshorigins else 'UNKNOWN','current_independent_origins':freshorigins,'evidence_ids':sorted({i for s in current for i in s['evidence_ids']})};timings['CORROBORATE']+=time.perf_counter()-t
        if contradictory:
            c['corroboration']['status']='CONTRADICTED';c['contradictions']=[s['signal_id'] for s in contradictory];decide(c,'PARK','PARK_CONTRADICTORY_JOB_EVIDENCE','CORROBORATE');continue
        if len(freshorigins)<2:
            c['unknowns']=['INDEPENDENT_CURRENT_CORROBORATION'];decide(c,'PARK','PARK_UNTIL_MORE_MARKET_HISTORY','CORROBORATE');continue
        corroborated+=1
        q=quick.get(c['cluster_id'])
        if not q or screen_count>=p['limits']['max_quick_screens']:
            c['unknowns']=['QUICK_SCREEN'];decide(c,'PARK','PARK_SCREEN_BUDGET' if q else 'PARK_NEEDS_MARKET_SAMPLE','QUICK_SCREEN');continue
        screen_count+=1;stage_entries['QUICK_SCREEN']+=1;t=time.perf_counter();c['quick_screen']=q
        for name,output in [('activity','activity_evidence'),('entrants','entrant_signal'),('incumbent','incumbent_signal'),('sponsored','sponsored_signal'),('query_relevance','query_relevance')]:c[output]=q['features'][name]
        c['unknowns']=[k for k in q['features'] if feature(q,k)=='UNKNOWN'];c['decision_evidence']=sorted(set(ids)|{e for o in q['observations'] for e in o['evidence_ids']})
        reason=None;decision='KILL';stage='QUICK_SCREEN'
        age=(stamp(packet['as_of'])-stamp(q['observed_at'])).total_seconds()/86400
        if age>p['max_quick_age_days']:decision,reason='PARK','PARK_STALE_SCREEN'
        elif q['rights']=='BLOCK':reason='RIGHTS_PLATFORM_OBVIOUS_BLOCK'
        elif q['rights']=='POSSIBLE_BLOCK':decision,reason='PARK','PARK_RIGHTS_AMBIGUITY'
        ev=q.get('event')
        if not reason and ev and ev['event_date'] is not None and ev['information_half_life_days'] is not None and ev['book_time_to_market_days'] is not None:
            elapsed=(stamp(packet['as_of']).date()-date.fromisoformat(ev['event_date'])).days;remaining=ev['information_half_life_days']-elapsed;c['time_to_market']={'status':'FAIL' if ev['book_time_to_market_days']>remaining else 'REVIEW','remaining_days':remaining,'evidence_ids':ev['evidence_ids']}
            if ev['book_time_to_market_days']>remaining:reason='TIME_TO_MARKET_MISMATCH'
        if not reason:
            kills=[('query_relevance','ABSENT','QUERY_MISMATCH'),('book_serving','ABSENT','NO_BOOK_RELEVANCE'),('activity','ABSENT','VISIBLE_ACTIVITY_ABSENT'),('incumbent','PRESENT','INCUMBENT_DOMINATED')]
            reason=next((r for name,v,r in kills if feature(q,name)==v),None)
            if feature(q,'sponsored')=='PRESENT' and q['organic_depth_reached']==0:reason='SPONSORED_DOMINATED_WITHOUT_ORGANIC_EVIDENCE'
            if reason in ('VISIBLE_ACTIVITY_ABSENT','INCUMBENT_DOMINATED','SPONSORED_DOMINATED_WITHOUT_ORGANIC_EVIDENCE') and not q['sample_complete']:decision,reason='PARK','PARK_NEEDS_WIDER_SAMPLE'
        if reason and decision=='KILL' and not q['observations']:fail('kill requires retained observations')
        if not reason:
            core=all(feature(q,k)=='PRESENT' for k in ('book_serving','activity','query_relevance'))
            if core and q['organic_depth_reached']>0 and feature(q,'incumbent')=='ABSENT' and feature(q,'entrants')=='PRESENT' and q['rights']=='NO_OBVIOUS_BLOCK' and q['value_of_information'] in ('MEDIUM','HIGH'):
                decide(c,'INVESTIGATE','EVIDENCE_JUSTIFIES_DEEP_COLLECTION',stage);candidates.append(c)
            else:
                decide(c,'PARK','PARK_LOW_VALUE_UNKNOWN' if q['value_of_information']=='LOW' else 'PARK_NEEDS_IDENTITY_EVIDENCE' if feature(q,'entrants')!='PRESENT' else 'PARK_NEEDS_BETTER_QUERY',stage)
        else:decide(c,decision,reason,stage)
        timings['QUICK_SCREEN']+=time.perf_counter()-t
    t=time.perf_counter();subject=Counter();audience=Counter();mechanisms=Counter();accepted=[]
    # Evidence gate first; transparent lexicographic queue order, never a scalar score.
    candidates.sort(key=lambda c:({'HIGH':0,'MEDIUM':1,'LOW':2}[c['quick_screen']['value_of_information']],{'FRESH':0,'RECENT':1,'UNKNOWN':2,'STALE':3}[c['freshness']],c['cluster_id']))
    for c in candidates:
        sk=canonical(c['subject']);ak=canonical(c['audience']);mk=c['mechanism'];stage_entries['QUEUE']+=1
        portfolio_only=set(c['source_families'])<={'PORTFOLIO_ADJACENCY','LLM_EXPANSION'}
        if len(accepted)>=p['limits']['max_investigate'] or subject[sk]>=p['limits']['max_per_subject'] or audience[ak]>=p['limits']['max_per_subject'] or (portfolio_only and any(set(x['source_families'])<={'PORTFOLIO_ADJACENCY','LLM_EXPANSION'} for x in accepted)):
            decide(c,'PARK','PARK_BREADTH_OR_QUEUE_CAPACITY','QUEUE')
        else:
            accepted.append(c);subject[sk]+=1;audience[ak]+=1;mechanisms[mk]+=1;c['stage']='QUEUE';c['late_factory_cost_class']=c['quick_screen'].get('factory_cost_class','UNKNOWN')
    timings['QUEUE']=time.perf_counter()-t
    counts={'raw':len(packet['signals']),'normalized':len(clusters),'corroborated':corroborated,'quick_screen':screen_count,**{k:sum(c['decision']==k.upper() for c in clusters) for k in ('kill','park','investigate')}}
    costs=cost_summary(packet,timings,counts)
    for c in clusters:
        reached=STAGES[:STAGES.index(c['stage'])+1];acq=packet.get('acquisition_costs',{})
        allocations={s:timings[s]/max(stage_entries[s],1) for s in reached};c['research_cost']={'machine_seconds_allocated':sum(allocations.values()),'allocation_basis':'Equal measured stage-time share; not exact per-cluster CPU/acquisition cost','external_usd':None,'manual_minutes':None,'owner_minutes':None}
        for name,key in [('external_usd','external_api_usd'),('manual_minutes','manual_minutes'),('owner_minutes','owner_minutes')]:
            vals=[acq.get(s,{}).get(key) for s in reached];c['research_cost'][name]=None if any(v is None for v in vals) else sum(v/max(stage_entries[s],1) for s,v in zip(reached,vals))
        if c['decision']=='PARK':
            voi=c['quick_screen']['value_of_information'] if c['quick_screen'] else 'MEDIUM'
            c['park']={'why':c['decision_reason'],'next_required_evidence':c['next_required_evidence'],'value_of_information':voi,'recheck_condition':'New relevant current evidence or changed query/market context; no automatic recheck','expiry':None,'max_next_research_minutes':5 if voi=='LOW' else p['max_next_research_minutes'],'max_next_research_usd':None}
        elif c['decision']=='KILL':
            if not c['decision_evidence']:fail('kill without evidence')
            c['kill_record']={'stage_killed':c['stage'],'reason':c['decision_reason'],'evidence':c['decision_evidence'],'cost_to_kill':c['research_cost'],'time_to_kill_seconds_allocated':c['research_cost']['machine_seconds_allocated'],'owner_attention_to_kill_minutes':c['research_cost']['owner_minutes']}
        shape(c,'BOOK_RADAR_WIDE_CLUSTER_SCHEMA_V1.json')
    prior=set()
    if previous:
        previous=read_run(previous)
        if previous['origin']!=packet['origin']:fail('previous run origin mismatch')
        prior={c['cluster_id'] for c in previous['clusters']}
    ids={c['cluster_id'] for c in clusters};counts.update(new_jobs=len(ids-prior),updated_jobs=len(ids&prior))
    source_stats={}
    for family in sorted({s['source_family'] for s in packet['signals']}):
        rows=[c for c in clusters if family in c['source_families']]
        source_stats[family]={'raw_signals':sum(s['source_family']==family for s in packet['signals']),'normalized_jobs':len(rows),'corroborated':sum(c['corroboration']['status']=='CORROBORATED' for c in rows),'quick_screened':sum(c['quick_screen'] is not None for c in rows),**{k:sum(c['decision']==k.upper() for c in rows) for k in ('kill','park','investigate')},'cost_usd':None,'cost_basis':'Source-family costs unmetered; mixed-origin clusters are multi-attributed, never additive distinct totals'}
    owner=[c['cluster_id'] for c in accepted]+[c['cluster_id'] for c in clusters if c['decision']=='PARK' and c['park']['value_of_information']=='HIGH']
    total_machine=time.perf_counter()-started
    costs['unattributed_machine_seconds']=max(0.0,total_machine-sum(timings.values()))
    costs['total_machine_seconds']=total_machine
    costs['machine_seconds_per_kill']=total_machine/counts['kill'] if counts['kill'] else None
    costs['machine_seconds_per_investigate']=total_machine/counts['investigate'] if counts['investigate'] else None
    breadth={'subjects':dict(subject),'audiences':dict(audience),'mechanisms':dict(mechanisms),**{name:dict(Counter(c[key] for c in accepted)) for name,key in [('jobs','job'),('languages','language'),('categories','category'),('buckets','bucket'),('freshness','freshness')]}}
    return {'schema_version':'book-radar-wide-run/v1','run_id':packet['run_id'],'origin':packet['origin'],'as_of':packet['as_of'],'input_ref':{'path':str(Path(path).resolve()),'sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest()},'clusters':clusters,'counts':counts,'costs':costs,'source_family_performance':source_stats,'breadth':breadth,'owner_items':owner[:p['limits']['max_owner_items']],'owner_items_deferred':max(len(owner)-p['limits']['max_owner_items'],0),'false_survivor_rate':None,'evidence':packet['evidence'],'canonical_state_written':False,'live_collection':False,'deep_shelf_calls':0,'production_candidates':0}

def read_run(path):
    r=load(path)
    if r.get('schema_version')!='book-radar-wide-run/v1' or r.get('origin') not in ('SYNTHETIC','RETAINED') or not isinstance(r.get('clusters'),list):fail('invalid run envelope')
    for c in r['clusters']:
        shape(c,'BOOK_RADAR_WIDE_CLUSTER_SCHEMA_V1.json')
        if c['origin']!=r['origin']:fail('run/cluster evidence domain mismatch')
    ref=r.get('input_ref',{})
    source=Path(ref.get('path',''))
    if not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest()!=ref.get('sha256'):fail('run input missing or changed')
    recomputed=screen(source)
    fields=tuple(k for k in recomputed['clusters'][0] if k not in ('research_cost','kill_record'))
    if [[c[k] for k in fields] for c in r['clusters']]!=[[c[k] for k in fields] for c in recomputed['clusters']] or r['evidence']!=recomputed['evidence'] or r['origin']!=recomputed['origin'] or r['as_of']!=recomputed['as_of']:
        fail('run decision/provenance differs from validated retained input')
    return r

def handoff(run,cid):
    if not isinstance(run,dict):run=read_run(run)
    c=next((c for c in run['clusters'] if c['cluster_id']==cid),None)
    if not c or c['decision']!='INVESTIGATE':fail('handoff requires INVESTIGATE')
    q=c['quick_screen'];cluster={'schema_version':'external-shelf-cluster/v1','id':cid,'label':c['audience']+' — '+c['job'],'frozen_at':run['as_of'],'routes':[{'id':'wide-query-v1','kind':'QUERY','definition':q['query'],'marketplace':c['market']}],'limitations':['Wide screening is not demand/reachability qualification','Freeze at handoff; collection must occur on or after frozen_at','Language '+c['language']+'; preserve explicit capture context','Synthetic source never becomes retained live evidence']}
    parent=json.loads((SCHEMAS/'EXTERNAL_SHELF_SNAPSHOT_SCHEMA_V1.json').read_text())
    draft_2020_12_validator(parent['properties']['cluster']).validate(cluster)
    return {'schema_version':'book-radar-wide-shelf-handoff/v1','origin':run['origin'],'cluster':cluster,'capture_request':{'marketplace':c['market'],'language':c['language'],'route_id':'wide-query-v1','route_definition':q['query'],'context':q['context'],'requested_organic_depth':20,'maximum_organic_depth':30,'missingness':'Keep UNKNOWN / NOT_VISIBLE / ACCESS_FAILED distinct','repeat_plan':'T0, useful T7, required T14 for finalists'},'evidence_base_directory':str(Path(run['input_ref']['path']).parent),'evidence_refs':[e for e in run['evidence'] if e['id'] in c['decision_evidence']],'main_uncertainty':c['unknowns'] or ['Real paid demand, genuine cold start, edition identity and repeat activity unqualified'],'next_required_evidence':c['next_required_evidence'],'estimated_deep_research_cost':{'minutes_ceiling':20,'usd':None},'source_diversity':c['evidence_origins'],'requires_owner_authorized_collection':True,'canonical_state_written':False,'production_authorized':False}

def render(run):
    summary=f"Wide screener {run['run_id']} [{run['origin']}]\n"+' → '.join(f'{k.upper()} {run["counts"][k]}' for k in ('raw','normalized','corroborated','quick_screen','kill','park','investigate'))+'\nLive collection: NO; deep shelf calls: 0; production: NO\n'
    rows={c['cluster_id']:c for c in run['clusters']}
    for cid in run['owner_items']:
        c=rows[cid];summary+=f"{c['decision']} {cid}: {c['audience']} / {c['job']} [{c['market']} {c['language']}]\nReason: {c['decision_reason']}; origins: {', '.join(c['evidence_origins'])}\nNext evidence: {'; '.join(c['next_required_evidence'])}\n"
    return summary+'Deferred owner items: '+str(run['owner_items_deferred'])+'\n'

# Read-only research projection. Historical screen decisions remain immutable.
FOLLOW_UP = {
    'PARK_NO_EXTERNAL_EVIDENCE': ('External reader evidence', 'Find one independent dated reader or book source for this query.'),
    'PARK_UNTIL_MORE_MARKET_HISTORY': ('Independent current corroboration', 'Check a second independent current source for the same reader/format; retain an access failure explicitly.'),
    'PARK_CONTRADICTORY_JOB_EVIDENCE': ('Resolution of conflicting reader evidence', 'Compare the conflicting observations in matched market/format context.'),
    'PARK_NEEDS_MARKET_SAMPLE': ('Relevant organic book sample', 'Capture the first relevant organic books, their ASINs, formats and delivery context for the frozen query.'),
    'PARK_STALE_SCREEN': ('Current listing facts', 'Revisit the same query and identities; keep historical dates and missing fields.'),
    'PARK_RIGHTS_AMBIGUITY': ('Work-specific rights clearance', 'Check original, translation and image rights separately for the target territory.'),
    'PARK_NEEDS_IDENTITY_EVIDENCE': ('Recent listing identity/history', 'Check publication, edition and creator history of one relevant activity witness.'),
    'PARK_NEEDS_BETTER_QUERY': ('A relevant book encounter route', 'Test the reader wording against an organic book shelf; do not substitute ads or template sales.'),
    'PARK_NEEDS_WIDER_SAMPLE': ('Adequate relevant sample', 'Expand the same bounded organic sample before inferring absence or incumbent lock.'),
}


def book_shortlist(run_path, history=(), *, as_of=None, minutes=100, exploration_share=0.6, baseline_date=None, canonical_root=None, hypothesis_links=None, reviews=()):
    """Route externally observed book leads, never promote them to TEST.

    Existing Wide files are the history. Explicit input aliases provide reviewed
    semantic normalization; this is not unrestricted paraphrase detection.
    """
    if isinstance(minutes, bool) or not isinstance(minutes, (int, float)) or not math.isfinite(minutes) or not 0 < minutes <= 240:
        fail('discovery minutes must be in (0,240]')
    if isinstance(exploration_share, bool) or not isinstance(exploration_share, (int, float)) or not math.isfinite(exploration_share) or not 0 <= exploration_share <= 1:
        fail('exploration share must be in [0,1]')
    if len(history) > 52: fail('discovery history exceeds 52 retained runs')
    current = read_run(run_path)
    day = date.fromisoformat(as_of) if as_of else stamp(current['as_of']).date()
    runs = {}
    for path in [*history, run_path]:
        run = read_run(path)
        if run['origin'] != current['origin']: fail('discovery history origin mismatch')
        if stamp(run['as_of']).date() > day: fail('future discovery run')
        if run['run_id'] in runs and runs[run['run_id']]['input_ref']['sha256'] != run['input_ref']['sha256']:
            fail('conflicting discovery run identity')
        runs[run['run_id']] = run
    ordered = sorted(runs.values(), key=lambda r: (r['as_of'], r['run_id']))
    if any(r['as_of'] > current['as_of'] for r in ordered): fail('history newer than selected discovery run')
    packets = {r['run_id']: checked(r['input_ref']['path']) for r in ordered}
    def source_identity(url):
        parts=urlsplit(url)
        tracking={'qid','ref','ref_','tag','dib','dib_tag','crid','sprefix','linkCode','linkId','camp','creative'}
        query=urlencode(sorted((k,v) for k,v in parse_qsl(parts.query) if k not in tracking and not k.startswith('utm_')))
        path=parts.path.split('/ref=')[0].rstrip('/')
        return parts.hostname.casefold()+path+('?' + query if query else '')
    def source_facts(c, packet):
        return {json.dumps([source_identity(s['source']), canonical(s['raw_phrase']),
                            s['freshness']['source_date'] if s['freshness']['date_basis'] in ('PUBLICATION', 'ACTIVITY') else None], ensure_ascii=False)
                for s in packet['signals'] if s['signal_id'] in c['raw_signals'] and s['provenance']['kind'] == 'EXTERNAL'}
    prior, seen, repeats, progressed = {}, set(), 0, set()
    fresh_book_jobs, failed_sources = set(), set()
    for run in ordered:
        packet = packets[run['run_id']]
        for c in run['clusters']:
            cid = c['cluster_id']
            repeats += cid in seen
            seen.add(cid)
            if c['decision'] == 'INVESTIGATE': progressed.add(cid)
            signals = [s for s in packet['signals'] if s['signal_id'] in c['raw_signals'] and s['provenance']['kind'] == 'EXTERNAL']
            if any(s['source_family'] == 'BOOK_MARKET' and freshness(s, packet) in ('FRESH','RECENT') for s in signals): fresh_book_jobs.add(cid)
            failed_sources.update(s['source'] for s in signals if freshness(s, packet) in ('UNKNOWN','STALE'))
            if run['run_id'] != current['run_id']:
                entry = prior.setdefault(cid, {'facts': set(), 'killed': False})
                entry['facts'].update(source_facts(c, packet)); entry['killed'] |= c['decision'] == 'KILL'
    links = {}
    if hypothesis_links:
        if canonical_root is None or not isinstance(hypothesis_links,dict): fail('canonical links require an explicit repository')
        from .book_radar import load_state
        canonical_state = load_state(Path(canonical_root))
        known = {o['id'] for o in canonical_state['opportunities']}
        retained_ids = {c['cluster_id'] for run in ordered for c in run['clusters']}
        for cid, ids in hypothesis_links.items():
            if cid not in retained_ids or not isinstance(ids,list) or not ids or any(not isinstance(i,str) or i not in known for i in ids):
                fail('canonical hypothesis link must resolve existing opportunity IDs')
            links[cid] = {'opportunity_ids':sorted(set(ids)), 'decisions':[d for d in canonical_state['decisions'] if d.get('opportunity_id') in ids]}
    packet = packets[current['run_id']]
    supplied_quick = {q['cluster_id']:q for q in packet.get('quick_screens',[])}
    if not isinstance(reviews,(list,tuple)) or len(reviews)>200: fail('research reviews require a bounded list')
    review_map = {}
    for review in reviews:
        if not isinstance(review,dict) or set(review)-{'cluster_id','status','reason','main_missing_fact','next_action','evidence_ids'} or not isinstance(review.get('cluster_id'),str) or review.get('cluster_id') not in {c['cluster_id'] for c in current['clusters']} or review.get('status') not in ('HOLD','REJECTED'):
            fail('research review can only hold or reject a known cluster')
        cid = review['cluster_id']
        cluster = next(c for c in current['clusters'] if c['cluster_id']==cid)
        if cid in review_map or not isinstance(review.get('evidence_ids'),list) or not review['evidence_ids'] or any(not isinstance(i,str) for i in review['evidence_ids']) or not set(review['evidence_ids']) <= set(cluster['decision_evidence']) or not all(isinstance(review.get(k),str) and review[k].strip() for k in ('reason','main_missing_fact','next_action')):
            fail('research review requires unique identity, resolved evidence and one question/action')
        review_map[cid] = review
    projected = {**packet, 'as_of': day.isoformat()+'T23:59:59+00:00'}
    queue, deferred, seeds, decisions = [], [], [], []
    for c in current['clusters']:
        cid = c['cluster_id']
        signals = [s for s in packet['signals'] if s['signal_id'] in c['raw_signals'] and s['provenance']['kind'] == 'EXTERNAL']
        current_signals = [s for s in signals if freshness(s, projected) in ('FRESH','RECENT')]
        current_origins = {origin(s['source'], policy(packet).get('origin_groups',{})) for s in current_signals if s.get('job_support')=='SUPPORTS'}
        old = prior.get(cid)
        changed = bool(source_facts(c, packet) - (old['facts'] if old else set()))
        lane = 'EXPLOITATION' if 'PORTFOLIO_ADJACENCY' in c['source_families'] else 'EXPLORATION'
        missing, action = FOLLOW_UP.get(c['decision_reason'], ('Matched reader choice and economics', 'Validate one decisive reader-choice fact before assessing a commercial experiment.'))
        row = {'cluster_id': cid, 'audience': c['audience'], 'job': c['job'], 'market': c['market'],
               'language': c['language'], 'lane': lane, 'historical_decision': c['decision'], 'evidence_ids':c['decision_evidence'],
               'status': 'RESEARCH', 'canonical_history':links.get(cid),
               'novelty': 'RETAINED_THESIS_NEW_CONTEXT' if cid in links else 'NEW_TO_RETAINED_HISTORY' if old is None else 'NEW_SOURCE_FACT' if changed else 'REPEAT_NO_NEW_SIGNAL',
               'main_missing_fact': missing, 'next_action': action, 'query': c['query_family'][0],
               'research_cap_minutes': min(20, policy(packet)['max_next_research_minutes']),
               'evidence_confidence': 'RESEARCH_CORROBORATION_ONLY' if len(current_origins)>=2 else 'LOW',
               'source_freshness': {s['signal_id']:freshness(s, projected) for s in signals},
               'current_book_signal': any(s['source_family']=='BOOK_MARKET' for s in current_signals),
               'value_of_information': supplied_quick.get(cid,{}).get('value_of_information','MEDIUM'),
               'attractiveness': 'UNASSESSED', 'production_authorized': False}
        decisions.append(row)
        if cid in review_map:
            review = review_map[cid]
            deferred.append({**row, **review, 'review_scope':'Evidence-bound research disposition; historical screen remains unchanged.'})
            continue
        if signals and all(s['source_family'] in ('CROSS_MARKET','LLM_EXPANSION') for s in signals):
            seeds.append({**row, 'status': 'SEED_ONLY', 'main_missing_fact': 'Book-format evidence'}); continue
        reason = 'CANONICAL_DECISION_REVIEW' if cid in links and any(d.get('decision') in ('REJECT','HOLD') for d in links[cid]['decisions']) else 'HISTORICAL_KILL_REVIEW' if old and old['killed'] else c['decision_reason'] if c['decision']=='KILL' else 'NO_EXTERNAL_SOURCE' if not signals else 'NO_CURRENT_SOURCE' if not any(freshness(s, projected) in ('FRESH','RECENT') for s in signals) else 'ACQUISITION_REQUIRED_FOR_THIS_RUN' if stamp(current['as_of']).date()!=day else 'REPEAT_NO_NEW_SIGNAL' if old and not changed else None
        if reason:
            if reason=='CANONICAL_DECISION_REVIEW':
                row.update(main_missing_fact='Source-bound rationale for revisiting a retained thesis',
                           next_action='Compare the new observations with the retained rejection, record a material-difference/reopen rationale, and preserve the original decision.')
            deferred.append({**row, 'status': 'REJECTED' if c['decision']=='KILL' else 'HOLD', 'reason': reason}); continue
        queue.append(row)
    queue.sort(key=lambda r: (r['historical_decision']!='INVESTIGATE', not r['current_book_signal'],
        {'HIGH':0,'MEDIUM':1,'LOW':2}[r['value_of_information']],
        r['novelty']!='NEW_TO_RETAINED_HISTORY', r['cluster_id']))
    budgets = {'EXPLORATION': minutes*exploration_share, 'EXPLOITATION': minutes*(1-exploration_share)}
    used = dict.fromkeys(budgets, 0)
    selected = []
    for row in queue:
        lane = row['lane']; cap = row['research_cap_minutes']
        if used[lane]+cap <= budgets[lane]+1e-9:
            selected.append(row); used[lane] += cap
        else: deferred.append({**row, 'status':'HOLD', 'reason':'LANE_RESEARCH_BUDGET'})
    baseline = date.fromisoformat(baseline_date) if baseline_date else stamp(ordered[0]['as_of']).date()
    if baseline > day: fail('future method baseline')
    if baseline_date and stamp(current['as_of']).date()>baseline and not any(stamp(r['as_of']).date()<=baseline for r in ordered):
        fail('retain baseline discovery run in history before advancing the weekly pointer')
    historical_ids = {c['cluster_id'] for r in ordered if stamp(r['as_of']).date() < baseline for c in r['clusters']}
    method_runs = [r for r in ordered if stamp(r['as_of']).date() >= baseline]
    method_ids = {c['cluster_id'] for r in method_runs for c in r['clusters']}
    book_ids = {c['cluster_id'] for r in method_runs for c in r['clusters'] if not set(c['source_families']) <= {'CROSS_MARKET','LLM_EXPANSION'}}
    age = (day-baseline).days
    stage = 'D21' if age>=21 else 'D14' if age>=14 else 'NOT_DUE'
    missing_cost = any(r['costs']['stages'][s].get('manual_minutes') is None for r in ordered for s in STAGES)
    # Keep discovery breadth visible before the bounded deep-research queue.
    # This is a presentation projection, never a weaker production/validation gate.
    selected_ids = {r['cluster_id'] for r in selected}
    discovery_pool = [{**r, 'status':'HOLD' if r['cluster_id'] in review_map else 'DISCOVERY',
                       'validation_status':'SELECTED_FOR_RESEARCH' if r['cluster_id'] in selected_ids else 'DEFERRED'}
                      for r in decisions if r['historical_decision'] != 'KILL'
                      and r['novelty'] != 'REPEAT_NO_NEW_SIGNAL'
                      and review_map.get(r['cluster_id'],{}).get('status') != 'REJECTED']
    return {'schema_version':'book-radar-book-shortlist/v1', 'as_of':day.isoformat(), 'origin':current['origin'],
        'run_id':current['run_id'], 'current_acquisition':stamp(current['as_of']).date()==day, 'book_research_shortlist':selected, 'owner_research_recommendations':selected[:2], 'deferred':deferred, 'cross_market_seeds':seeds,
        'discovery_pool':discovery_pool,
        'discovery_pool_scope':'Early reader jobs for comparison; not production recommendations. Repeats and rejected rows excluded.',
        'decision_history':[{'run_id':r['run_id'], 'as_of':r['as_of'], 'decisions':[{'cluster_id':c['cluster_id'], 'decision':c['decision'], 'reason':c['decision_reason']} for c in r['clusters']]} for r in ordered],
        'budget':{'minutes':minutes,'exploration_share':exploration_share,'allocated':budgets,'selected_minutes':used,'actual_minutes':'UNKNOWN'},
        'method_review':{'baseline':baseline.isoformat(),'day14':(baseline+timedelta(days=14)).isoformat(),
            'day21':(baseline+timedelta(days=21)).isoformat(),'stage':stage,'retained_runs':len(ordered),
            'distinct_hypotheses':len(seen),'new_hypotheses_since_baseline':len(method_ids-historical_ids-set(links)),
            'explicitly_linked_canonical_theses':len(links),
            'new_book_hypotheses_since_baseline':len((method_ids-historical_ids-set(links)) & book_ids),
            'runs_since_baseline':len(method_runs),'repeat_occurrences':repeats,'jobs_with_current_book_signals_at_capture':len(fresh_book_jobs),
            'progressed_to_investigate':len(progressed),'test_candidates':'UNKNOWN_NOT_ASSESSED_BY_WIDE',
            'sources_without_current_dated_evidence':sorted(failed_sources),
            'acquisition_cost_usd':None if any(r['costs']['total_usd'] is None for r in ordered) else sum(r['costs']['total_usd'] for r in ordered),
            'processor_seconds':sum(r['costs']['total_machine_seconds'] for r in ordered), 'actual_research_minutes':'UNKNOWN' if missing_cost else sum(r['costs']['stages'][s]['manual_minutes'] for r in ordered for s in STAGES),
            'next_action':'NOT_DUE' if stage=='NOT_DUE' else 'REVIEW_SOURCE_AND_QUERY_BOTTLENECKS' if stage=='D14' else 'COMPARE_FREE_TOOLS_AND_PREPARE_OWNER_REVIEWED_PAID_OPTION_IF_JUSTIFIED',
            'scope':'Research method quality only; no assumed book sales deadline.'},
        'novelty_scope':'Compared retained runs and explicitly reviewed canonical links; not exhaustive semantic novelty.',
        'semantic_deduplication':'Reviewed input aliases plus market/language/reader-job identity; unreviewed paraphrases may need human linking.',
        'canonical_state_written':False,'network_requests':0,'production_authorized':False,'automatic_test_promotion':False}


COMMERCIAL_STAGES = ('demand', 'competition', 'differentiation', 'feasibility', 'compare')


def commercial_review_pipeline(menu):
    """Route sourced research; never infer market facts or authorize production.

    Acquisition is performed by the existing weekly agent, not this local loader.
    Legacy cards remain readable but cannot bypass content comparison.
    """
    reviews = menu.get('commercial_reviews', {})
    queue = menu.get('research_queue', [])
    if not isinstance(reviews, dict) or not isinstance(queue, list) or len(queue) > 24:
        fail('invalid bounded commercial research queue')
    rows = menu['cards'] + queue
    if len(rows) > 24: fail('commercial research is capped at 24 candidates')
    budget = menu.get('research_budget', {'max_checks':24, 'used_checks':0})
    if not isinstance(budget, dict) or set(budget) != {'max_checks','used_checks'} or any(type(budget[k]) is not int for k in budget) or not 1 <= budget['max_checks'] <= 100 or not 0 <= budget['used_checks'] <= budget['max_checks']:
        fail('invalid commercial research budget')
    if any(not isinstance(row, dict) or row.get('production_authorized') is not False for row in rows):
        fail('commercial queue never grants production authority')
    ids = [row.get('id') for row in rows if isinstance(row, dict)]
    if len(ids) != len(rows) or any(not isinstance(i, str) or not i for i in ids) or len(ids) != len(set(ids)):
        fail('commercial queue requires unique candidate ids')
    if set(reviews) - set(ids): fail('commercial review has an unknown candidate')
    outcomes = []
    for row in rows:
        review = reviews.get(row['id'], {})
        if not isinstance(review, dict): fail('commercial review must be an object')
        next_stage, disposition = None, 'READY_FOR_OWNER_DECISION'
        for stage in COMMERCIAL_STAGES:
            check = review.get(stage)
            if check is None:
                if next_stage is None: next_stage, disposition = stage, 'RESEARCH_REQUIRED'
                continue
            if not isinstance(check, dict) or check.get('status') not in {'PASS', 'REVIEW', 'FAIL'}:
                fail('invalid commercial stage')
            sources = check.get('sources', [])
            if not isinstance(check.get('reason'), str) or not check['reason'].strip() or not isinstance(sources, list):
                fail('commercial stage needs a reason and sources')
            for source in sources:
                if not isinstance(source, dict) or not isinstance(source.get('url'), str) or not source['url'].startswith('https://'):
                    fail('commercial evidence needs a public source URL')
                try: day = date.fromisoformat(source['observed_date'])
                except (KeyError, TypeError, ValueError): fail('commercial evidence needs an observation date')
                if day > date.fromisoformat(menu['as_of']): fail('future commercial evidence')
            if stage == 'feasibility' and check.get('hard_blockers'):
                if not isinstance(check['hard_blockers'], list) or any(not isinstance(b, str) or not b.strip() for b in check['hard_blockers']):
                    fail('hard blockers must be explained')
                next_stage, disposition = stage, 'REJECTED_ADVANCE_QUEUE'
                break
            if check['status'] == 'FAIL':
                next_stage, disposition = stage, 'REJECTED_ADVANCE_QUEUE'
                break
            if check['status'] == 'REVIEW':
                if next_stage is None: next_stage, disposition = stage, 'RESEARCH_REQUIRED'
                continue
            if not sources: fail('a passing commercial stage needs evidence')
            if stage == 'competition':
                books = check.get('books', [])
                if not isinstance(books, list) or len(books) < 2:
                    fail('competition PASS needs at least two content-checked books')
                identities = []
                for book in books:
                    if not isinstance(book, dict) or not isinstance(book.get('identity'), str) or not book['identity'].strip() or book.get('basis') not in {'SAMPLE', 'TOC', 'PUBLISHER_DESCRIPTION'} or book.get('source_url') not in [s['url'] for s in sources]:
                        fail('competition books need identity, content basis and bound source')
                    identities.append(book['identity'])
                if len(set(identities)) != len(identities): fail('competition books must be distinct')
            if stage == 'differentiation':
                if not isinstance(check.get('competitor_already_offers_claim'), bool):
                    fail('differentiation needs an explicit overlap check')
                basis = check.get('purchase_basis')
                if basis is not None:
                    fields = {
                        'REPEAT_ENTERTAINMENT': ('reader', 'reason_to_buy', 'original_content_plan', 'genre_fit', 'repeat_purchase_evidence', 'discovery_route', 'quality_plan', 'rights_plan'),
                        'PRACTICAL_FIT': ('reader', 'reason_to_buy', 'reader_outcome', 'audience_fit', 'delivery_plan', 'discovery_route', 'quality_plan', 'rights_plan'),
                        'SPECIAL_EDITION': ('reader', 'reason_to_buy', 'work_selection', 'language_audience', 'rights_basis', 'alternatives', 'discovery_route', 'quality_plan'),
                    }
                    if not isinstance(basis, dict) or basis.get('kind') not in fields:
                        fail('purchase basis needs a supported product type')
                    if any(not isinstance(basis.get(k), str) or not basis[k].strip() for k in fields[basis['kind']]):
                        fail('purchase basis needs an explained reader, offer, route and quality/rights plan')
                    evidence_urls = basis.get('evidence_urls')
                    if not isinstance(evidence_urls, list) or not evidence_urls or any(u not in [s['url'] for s in sources] for u in evidence_urls):
                        fail('purchase basis needs bound supporting sources')
                    if check['competitor_already_offers_claim'] and basis.get('uniqueness_claim_removed') is not True:
                        fail('overlap cancels the uniqueness claim, not the product')
                if menu.get('selection_method') == 'purchase-reason-by-product-type/v2' and basis is None:
                    fail('v2 recommendation needs an explained product-specific purchase basis')
                if check['competitor_already_offers_claim'] and basis is None and check.get('revised_advantage_validated') is not True:
                    if next_stage is None: next_stage, disposition = stage, 'RESEARCH_REQUIRED'
                    continue
                if not isinstance(check.get('advantage'), str) or not check['advantage'].strip():
                    fail('differentiation needs a specific compared advantage')
            if stage == 'compare' and menu.get('selection_method') == 'purchase-reason-by-product-type/v2':
                factors = check.get('factors')
                required = {'buyer_signal', 'market_access', 'purchase_reason', 'buyer_route', 'capability_fit'}
                if not isinstance(factors, dict) or set(factors) != required:
                    fail('v2 comparison needs the five explained commercial factors')
                for factor in factors.values():
                    if not isinstance(factor, dict) or not isinstance(factor.get('argument'), str) or not factor['argument'].strip() or not isinstance(factor.get('evidence_urls'), list) or not factor['evidence_urls'] or any(u not in [s['url'] for s in sources] for u in factor['evidence_urls']):
                        fail('comparison factor needs an argument and bound evidence')
        outcomes.append({'id':row['id'], 'disposition':disposition, 'next_stage':next_stage,
                         'production_authorized':False})
    pending = [r for r in outcomes if r['disposition'] == 'RESEARCH_REQUIRED']
    selected = {r['id'] for r in outcomes if r['disposition'] == 'READY_FOR_OWNER_DECISION'} & set(menu.get('top_owner_review', []))
    return {'policy':menu.get('selection_method', 'PASS9_CONTENT_BEFORE_RECOMMENDATION'), 'outcomes':outcomes,
            'next_checks':pending, 'research_budget':budget,
            'action':'PRESENT_OWNER_DECISIONS' if selected else (('RESEARCH_BUDGET_EXHAUSTED' if budget['used_checks'] == budget['max_checks'] else 'CONTINUE_RESEARCH_WITHIN_BUDGET') if pending else 'QUEUE_EXHAUSTED'),
            'acquisition_executor':'EXISTING_WEEKLY_AGENT', 'automatic_source_acquisition':False,
            'production_authorized':False}


def merge_readiness_menu(menu, handoff):
    """Derived routing only. The frozen source menu and reviews are never rewritten."""
    import copy
    merged = copy.deepcopy(menu)
    queue = merged.setdefault('research_queue', [])
    reviews = merged.setdefault('commercial_reviews', {})
    notes = []
    available = {x['id']: x for x in handoff['candidates']} if handoff['status'] == 'CURRENT' else {}
    existing = merged['cards'] + queue
    for row in existing:
        if not row['id'].startswith('readiness:'):
            continue
        live = available.get(row['id'])
        bound = row.get('readiness_ref', {})
        if live is None or bound.get('material_review_digest') != live['material_review_digest']:
            reviews[row['id']] = {}  # In-memory invalidation, never edit historical evidence.
            notes.append({'id': row['id'], 'reason': 'MATERIAL_MISSING_STALE_OR_CHANGED_RECHECK'})
    known = {x['id'] for x in existing}
    for item in handoff['candidates']:
        if item['id'] in known:
            continue
        if handoff['status'] != 'CURRENT':
            notes.append({'id': item['id'], 'reason': 'REFRESH_MATERIAL_BEFORE_CURRENT_RESEARCH'})
            continue
        if len(merged['cards']) + len(queue) >= 24:
            notes.append({'id': item['id'], 'reason': 'EXISTING_QUEUE_CAP_REVIEW_NEXT_BATCH'})
            continue
        queue.append({'id': item['id'], 'title': item['title'], 'status': 'RESEARCH',
                      'source_kind': 'OWN_ARCHIVE', 'production_authorized': False,
                      'readiness_ref': {'candidate_id': item['candidate_id'],
                                        'material_review_digest': item['material_review_digest'],
                                        'member_digest': item['member_digest'],
                                        'source_report': item['source_report']}})
    return merged, notes


def weekly_book_review(root, as_of, *, readiness_snapshot=None):
    """Optional pointer manifest consumed by the existing weekly runner, no scheduler."""
    from .book_readiness import research_handoff
    readiness = readiness_snapshot if readiness_snapshot is not None else research_handoff(root, as_of)
    path = Path(root)/'book-radar/discovery-review.json'
    if not path.exists():
        if readiness['status'] == 'UNAVAILABLE': return None
        seed = {'as_of': as_of, 'cards': [], 'top_owner_review': [], 'production_authorized': False}
        merged, notes = merge_readiness_menu(seed, readiness)
        return {'current_acquisition': False, 'owner_research_recommendations': [],
                'owner_production_review_candidates': [], 'production_authorized': False,
                'method_review': {'status': 'NO_EXTERNAL_DISCOVERY_MANIFEST'},
                'book_readiness': readiness, 'book_readiness_research_queue': readiness['candidates'],
                'commercial_intake': merged['research_queue'], 'readiness_routing_notes': notes,
                'commercial_pipeline': commercial_review_pipeline(merged)}
    config = load(path)
    if set(config)-{'run','history','minutes','exploration_share','baseline_date','hypothesis_links','reviews','editorial_menu'} or not isinstance(config.get('run'),str) or not isinstance(config.get('history',[]),list):
        fail('invalid discovery review manifest')
    def local(ref):
        if not isinstance(ref,str): fail('discovery run reference must be a path')
        target=(Path(root)/ref).resolve()
        if not target.is_relative_to(Path(root).resolve()): fail('discovery review reference escapes repository')
        return target
    result = book_shortlist(local(config['run']), [local(p) for p in config.get('history',[])], as_of=as_of,
                          minutes=config.get('minutes',100), exploration_share=config.get('exploration_share',0.6),
                          baseline_date=config.get('baseline_date'), canonical_root=root,
                          hypothesis_links=config.get('hypothesis_links'), reviews=config.get('reviews',[]))
    result['book_readiness'] = readiness
    result['book_readiness_research_queue'] = readiness['candidates']
    if 'editorial_menu' in config:
        ref = config['editorial_menu']
        if not isinstance(ref, dict) or set(ref) != {'path', 'sha256'}:
            fail('editorial menu needs an immutable local reference')
        menu_path = local(ref['path'])
        if hashlib.sha256(menu_path.read_bytes()).hexdigest() != ref['sha256']:
            fail('editorial menu proof changed')
        menu = load(menu_path)
        cards, top = menu.get('cards'), menu.get('top_owner_review')
        if menu.get('production_authorized') is not False or not isinstance(cards, list) or not 1 <= len(cards) <= 5 or not isinstance(top, list) or len(top) > 2:
            fail('editorial menu is a bounded research-only projection')
        if any(not isinstance(c, dict) or c.get('production_authorized') is not False or not isinstance(c.get('id'), str) or not c['id'] or c.get('status') not in {'DISCOVERY','RESEARCH','READY FOR OWNER REVIEW','HOLD'} for c in cards):
            fail('invalid editorial card or production approval')
        ids = [c['id'] for c in cards]
        if len(set(ids)) != len(ids) or len(set(top)) != len(top) or not set(top) <= set(ids):
            fail('editorial owner candidates must resolve unique cards')
        menu_day = date.fromisoformat(menu['as_of'])
        if menu_day > date.fromisoformat(as_of): fail('future editorial evidence')
        current = menu['as_of'] == as_of and result['current_acquisition']
        result['book_opportunity_menu'] = {**menu, 'freshness':'CURRENT_RESEARCH_ONLY' if current else 'REFRESH_REQUIRED'}
        routed, notes = merge_readiness_menu(menu, readiness)
        result['commercial_intake'] = routed.get('research_queue', [])
        result['readiness_routing_notes'] = notes
        pipeline = commercial_review_pipeline(routed)
        ready = {r['id'] for r in pipeline['outcomes'] if r['disposition'] == 'READY_FOR_OWNER_DECISION'}
        result['commercial_pipeline'] = {**pipeline, 'action':pipeline['action'] if current else 'REFRESH_ACQUISITION_FIRST'}
        result['owner_production_review_candidates'] = [c for c in cards if c['id'] in top and c['id'] in ready] if current else []
    else:
        seed = {'as_of': as_of, 'cards': [], 'top_owner_review': [], 'production_authorized': False}
        routed, notes = merge_readiness_menu(seed, readiness)
        result['commercial_intake'] = routed['research_queue']
        result['readiness_routing_notes'] = notes
        result['commercial_pipeline'] = commercial_review_pipeline(routed)
    return result
