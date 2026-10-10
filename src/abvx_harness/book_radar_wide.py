"""Offline, evidence-bound cheap screening; no collectors or commercial state writes."""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
import time
import math
from collections import Counter
from datetime import datetime, date
from functools import lru_cache
from urllib.parse import urlsplit
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
