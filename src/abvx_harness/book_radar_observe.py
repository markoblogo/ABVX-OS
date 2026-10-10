"""Manual checkpoint operations over existing Radar state. No collectors or schedules."""
from __future__ import annotations
import json
from copy import deepcopy
from datetime import date, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from .harness import ValidationError, load_json
from .book_radar_outcomes import UNKNOWN as U, CHECKPOINTS, evidence, _evidence_refs

PACKET='book-radar-checkpoint-evidence-packet/v1'
RECEIPT='book-radar-checkpoint-receipt/v1'
COLLECTION='checkpoint_packets'
UNOBSERVABLE=('organic_impressions','detail_page_visits','sample_opens','matched_ku_starts','reader_identity','matched_series_continuation')
COSTS=('owner_minutes','ai_api','other_machine','production_minutes','rework_minutes','rework_cost','artwork','advertising_acquisition','other_acquisition','external_services','elapsed_calendar_days')
STATES=('UPCOMING','DUE_TODAY','OVERDUE','COLLECTED_EXACT','COLLECTED_LATE','COLLECTED_APPROXIMATE','MISSING','NOT_APPLICABLE')

def protocol(root):
    return load_json(root/'BOOK_RADAR_CONTROLLED_CALIBRATION_V1.json')

def today(root):
    return datetime.now(ZoneInfo(protocol(root)['schedule']['timezone'])).date().isoformat()

@lru_cache(maxsize=1)
def packet_validator():
    from .schema_validation import load_draft_2020_12_validator
    return load_draft_2020_12_validator(Path(__file__).resolve().parents[2]/'schemas/book_radar_checkpoint_packet.schema.json')

def _error(message):
    raise ValidationError(message)

def experiments(state,root):
    result=[]
    for b in state['observed_books']:
        if b['initial_experiment']:
            result.append({'id':b['audit_book_id'],'title':b['title'],'book':b,'contract':None,'kind':'BOOK'})
    for c in state['experiment_contracts']:
        b=next((b for b in state['observed_books'] if b['product_id']==c['product_id']),None)
        p=next(p for p in state['products'] if p['id']==c['product_id'])
        result.append({'id':c['id'],'title':p.get('title',p['id']),'book':b,'contract':c,'kind':'BOOK'})
    p=protocol(root)
    result.append({'id':p['experiment_id'],'title':'Controlled T7/T14 protocol','book':None,'contract':None,'kind':'CONTROLLED_PROTOCOL','protocol':p})
    return result

def _format_launch_states(state,book_id):
    """Latest owner-observed state per format, preserving the submission event."""
    events=[]
    for event in state.get('launches',[]):
        if event.get('book_id')!=book_id:continue
        if event.get('event_type') not in ('KDP_SUBMISSION','KDP_FORMAT_STATUS_OBSERVATION'):continue
        events.append(event)
    events.sort(key=lambda x:(x.get('observed_date',x.get('submission_date','')),x.get('id','')))
    latest={}
    for event in events:
        for fmt in event.get('format_states',[]):
            fid=fmt.get('format_id')
            if not fid:continue
            previous=latest.get(fid,{})
            merged={**previous,**fmt,'book_id':book_id,'submission_event_id':event.get('submission_event_id',event.get('id'))}
            # A later non-LIVE status cannot erase a previously confirmed live date.
            if previous.get('first_confirmed_live_date','UNKNOWN')!='UNKNOWN':
                merged['first_confirmed_live_date']=previous['first_confirmed_live_date']
            latest[fid]=merged
    return list(latest.values())

def _confirmed_live_anchor(state,book_id):
    dates=[r['first_confirmed_live_date'] for r in _format_launch_states(state,book_id)
           if r.get('first_confirmed_live_date','UNKNOWN')!='UNKNOWN']
    return min(dates) if dates else U

def _checkpoint_anchor(experiment,state):
    b=experiment.get('book') or {}
    if not b:return U
    submissions=any(x.get('book_id')==b.get('id') and x.get('event_type')=='KDP_SUBMISSION'
                    for x in state.get('launches',[]))
    return _confirmed_live_anchor(state,b.get('id',U)) if submissions else b.get('publication_date',U)

def _live_confirmation(state,experiment,as_of):
    b=experiment.get('book') or {}
    if not b:return []
    pending=[]
    for fmt in _format_launch_states(state,b.get('id',U)):
        live_date=fmt.get('first_confirmed_live_date',U)
        if live_date!=U:continue
        pending.append({'experiment_id':experiment['id'],'title':experiment['title'],
            'action':'CONFIRM_LIVE_STATUS','format_id':fmt['format_id'],'format':fmt.get('format',U),
            'status':fmt.get('status',U),'submission_date':fmt.get('submission_date',U),
            'effective_date':fmt.get('submission_date',U),'asin':fmt.get('asin',U),
            'marketplace':fmt.get('marketplace',U),'reason':'Commercial checkpoints wait for first confirmed LIVE date'})
    return pending

def resolve(state,root,identifier):
    choices=[e for e in experiments(state,root) if identifier in (e['id'],(e['book'] or {}).get('id'))]
    if len(choices)!=1:_error('Unknown or ambiguous experiment ID; use IDs shown by --status')
    return choices[0]

def _target(experiment,cp):
    if experiment['kind']=='CONTROLLED_PROTOCOL':
        if cp not in ('T7','T14'):_error('Controlled protocol requires T7 or T14')
        return experiment['protocol']['schedule'][cp.lower()],U
    if cp not in tuple('D'+str(d) for d in CHECKPOINTS):_error('Book checkpoints require D0/D7/D14/D30/D60/D90')
    pub=_checkpoint_anchor(experiment,experiment.get('state',{}))
    return ((date.fromisoformat(pub)+timedelta(days=int(cp[1:]))).isoformat() if pub!=U else U),pub

def _timing(p):
    if p['applicability']['state']=='NOT_APPLICABLE':return 'NOT_APPLICABLE'
    if p['target_date']==U:return U
    delta=(date.fromisoformat(p['actual_date'])-date.fromisoformat(p['target_date'])).days
    if delta==0:return 'EXACT'
    if p['approximate_tolerance_days'] and abs(delta)<=p['approximate_tolerance_days']:return 'APPROXIMATE'
    if delta>0:return 'LATE'
    _error('Early collection requires an explicitly declared approximation tolerance')

def validate_packet(p):
    errors=list(packet_validator().iter_errors(p))
    if errors:_error('Invalid checkpoint packet: '+errors[0].message)
    try:zone=ZoneInfo(p['timezone'])
    except (ZoneInfoNotFoundError,ValueError) as error:raise ValidationError('Unknown packet timezone') from error
    def timestamp(value):
        if value!=U and datetime.fromisoformat(value).astimezone(zone).date().isoformat()!=p['actual_date']:_error('Observation timestamp/date mismatch')
    timestamp(p['observed_at'])
    if len({(r['subject_id'],r['marketplace'],tuple(r['formats']) if isinstance(r['formats'],list) else r['formats'],r['scope']) for r in p['accounts']})!=len(p['accounts']):_error('Duplicate account scope/format observations')
    for row in p['accounts']:
        for key in ('orders','kenp','royalties'):
            w=row[key]
            if w==U:continue
            if w['start']>w['end'] or w['end']>p['actual_date']:_error('Reporting window includes future data or reversed dates')
            if any(isinstance(v,(int,float)) for v in w.values()) and not w['evidence']:_error('Observed account values require evidence')
        w=row['orders']
        if w!=U:
            for total,parts in [('processed_units',('paid_units','free_units')),('paid_units',('ebook_paid','print_paid'))]:
                if all(w[k]!=U for k in (total,*parts)) and w[total]!=sum(w[k] for k in parts):_error('Paid/free/format totals do not reconcile')
    for row in p['retailers']:
        timestamp(row['observed_at'])
        if (row['availability']!=U or row['price']!=U or row['first_verified_live_date']!=U) and not row['evidence']:_error('Retailer observation requires evidence')
        if row['first_verified_live_date']!=U and row['first_verified_live_date']>p['actual_date']:_error('First verified live cannot be in the future')
    from .book_radar_attribution import validate_record as validate_phase2
    for q in p['search_snapshots']:
        validate_phase2(q,'search_snapshots')
        if q['observed_date']!=p['actual_date']:_error('Search snapshot must preserve this actual collection date')
        timestamp(q['observed_at'])
    for row in p['categories']:
        timestamp(row['observed_at'])
        if row['presence']=='NOT_FOUND_WITHIN_DEPTH' and (row['position']!=U or row['depth']==U):_error('Absent category cannot establish a rank')
        if (row['position']!=U or row['presence']!=U) and not row['evidence']:_error('Category observation requires evidence')
    for row in p['costs']:
        if any(v!=U for k,v in row['actual'].items() if k!='currency') and not row['evidence']:_error('Known cost requires evidence')
        monetary=('ai_api','other_machine','rework_cost','artwork','advertising_acquisition','other_acquisition','external_services')
        if any(row['actual'][k]!=U for k in monetary) and row['actual']['currency']==U:_error('Known monetary costs require currency')
    app=p['applicability']
    if app['state']=='NOT_APPLICABLE' and (app['recorded_by']!='OWNER' or app['reason']==U or not app['evidence']):_error('N/A requires an explicit OWNER reason and evidence')
    if p['collection_state']=='COMPLETE' and app['state']!='NOT_APPLICABLE' and not (p['accounts'] or p['retailers'] or p['search_snapshots'] or p['categories']):_error('Costs or notes alone do not complete a commercial checkpoint')
    if not list(_evidence_refs(p)):_error('Packet requires retained evidence, including access-failure evidence when applicable')
    _timing(p)

def obligations(state,e):
    if e['kind']=='CONTROLLED_PROTOCOL':
        p=e['protocol'];queries=[]
        for f in p['query_families']:
            c=next(c for c in p['controls'] if c['id']==f['control'])
            for q in [f['primary'],*f['secondary'],*f['long_tail']]:queries.append({'subject_id':c['id'],'query':q,'marketplace':c['marketplace'],'depth':16,'rank_basis':'ORGANIC','device_surface':U,'signed_in_context':'SIGNED_OUT','delivery_context':'France' if c['marketplace']=='amazon.com' else '75001 Paris','lock':f['status']})
        return {'queries':queries,'categories':[],'retailers':p['controls'],'subjects':[c['id'] for c in p['controls']]}
    b=e['book'];bid=b['id'] if b else U
    queries=[]
    for q in state['search_snapshots']:
        if (q['experiment_id']==e['id'] or bid!=U and q['book_id']==bid) and (q['marketplace'],q['query']) not in [(x['marketplace'],x['query']) for x in queries]:
            queries.append({k:q[k] for k in ('query','marketplace','depth','rank_basis','device_surface','signed_in_context','delivery_context')}|{'subject_id':bid,'lock':'RETAINED_HISTORICAL_NOT_PROSPECTIVE_LOCK' if e['contract'] is None else 'FROZEN_ROUTE_REFERENCE'})
    rows=[a for a in state['actuals'] if a.get('book_id')==bid and a.get('schema_version')=='book-radar-observed-actual/v1']
    latest=max(rows,key=lambda a:a['observed_date']) if rows else None
    return {'queries':queries,'categories':latest['category_observations'] if latest else [],'retailers':b['formats'] if b else [],'subjects':[bid]}

def validate_links(p,state,root):
    e={**resolve(state,root,p['experiment_id']),'state':state};target,pub=_target(e,p['checkpoint'])
    age=(date.fromisoformat(p['actual_date'])-date.fromisoformat(pub)).days if pub!=U else U
    if p['target_date']!=target or p['book_age_days']!=age:_error('Target date/commercial age must derive from the canonical checkpoint anchor')
    if age!=U and age<0:_error('Observation precedes publication')
    o=obligations(state,e);subjects=set(o['subjects'])
    for key in ('accounts','retailers','categories','costs'):
        if any(row['subject_id'] not in subjects for row in p[key]):_error('Packet subject does not belong to experiment')
    bid=(e['book'] or {}).get('id',U)
    for q in p['search_snapshots']:
        if q['book_id'] not in ({bid} if e['kind']=='BOOK' else {b['id'] for b in state['observed_books']}|{U}):_error('Search snapshot book mismatch')
        if q['experiment_id'] not in (U,e['id']):_error('Search snapshot experiment mismatch')
    if p['collection_state']=='COMPLETE' and p['applicability']['state']!='NOT_APPLICABLE':
        if not subjects<={r['subject_id'] for r in p['accounts']}:_error('Completed collection requires account outcomes or explicit UNKNOWN attempts for each subject')
        expected={(q['marketplace'],q['query']) for q in o['queries']};present={(q['marketplace'],q['query']) for q in p['search_snapshots']}
        if not expected<=present:_error('Completed collection is missing retained/locked queries')
        expected={(c['marketplace'],c['category']) for c in o['categories']};present={(c['marketplace'],c['target_category']) for c in p['categories']}
        if not expected<=present:_error('Completed collection is missing category attempts')
        if e['kind']=='CONTROLLED_PROTOCOL' and not subjects<={r['subject_id'] for r in p['retailers']}:_error('Completed controlled collection requires retained retailer identity attempts for each control')
        if e['kind']=='BOOK' and o['retailers']:
            if not {f['asin'] for f in o['retailers']}<={f['asin'] for f in p['retailers']}:_error('Completed collection is missing retained format identities')
    records=p.get('records',{})
    if e['kind']=='CONTROLLED_PROTOCOL' and any(records.values()):_error('Controlled packets cannot generate actuals/attribution/calibration; protocol remains separate')
    from .book_radar_outcomes import validate_record as validate_phase1
    from .book_radar_attribution import validate_record as validate_phase2
    for col,rows in records.items():
        for row in rows:
            validate_phase1(row,col);validate_phase2(row,col)
            if row.get('book_id')!=bid or row.get('observed_date')!=p['actual_date']:_error('Native record book/date mismatch')
            if col=='actuals':
                if row.get('schema_version')!='book-radar-observed-actual/v1':_error('Collected native actuals require the accepted Foundation contract')
                a=next((r for r in p['accounts'] if r['subject_id']==bid),None)
                if not a:_error('Native actual requires collected account observations')
                for key,window in [('orders','lifetime'),('kenp','kenp'),('royalties','money')]:
                    if a[key]==U:_error('Incomplete account windows cannot be manufactured into a native actual')
                    captured={k:v for k,v in a[key].items() if k!='window_kind'}
                    if row['windows'][window]!=captured:_error('Native actual differs from collected account evidence')
                if a['orders']['window_kind']!='LIFETIME':_error('Fixed-period orders cannot be called Lifetime')
                unavailable=('impressions','clicks','detail_page_visits','sample_opens','ku_starts','ctr','conversion')
                if any(row['instrumentation'][k]!=U for k in unavailable):_error('Current standard source cannot supply organic traffic; ad-specific fields stay separate')
            if col=='attribution_observations':
                a=next((r for r in p['accounts'] if r['subject_id']==bid),None)
                if not a:_error('Native attribution requires matching account data')
                for metric,component,field in [('paid_units','orders','paid_units'),('free_units','orders','free_units'),('ebook_paid','orders','ebook_paid'),('print_paid','orders','print_paid'),('kenp','kenp','kenp_pages'),('estimated_royalties','royalties','estimated_royalties')]:
                    expected=a[component][field] if a[component]!=U else U
                    if row['actual_outcomes'][metric]!=expected:_error('Native attribution outcome differs from packet account data')
    return e

def validate_record(record,collection):
    if collection!=COLLECTION:return
    if set(record)!={'schema_version','id','source','packet','assessment'} or record['schema_version']!=RECEIPT:_error('Invalid checkpoint receipt')
    validate_packet(record['packet'])
    if record['id']!=record['packet']['id'] or record['assessment']['timing']!=_timing(record['packet']):_error('Checkpoint receipt identity/timing mismatch')
    if set(record['source'])!={'path','sha256'} or len(record['source']['sha256'])!=64:_error('Invalid packet source reference')
    a=record['assessment']
    if set(a)!={'timing','comparability','interpretation'} or set(a['comparability'])!={'status','compared_to','reasons'}:_error('Invalid receipt assessment')
    if a['comparability']['status'] not in ('COMPARABLE','PARTIALLY_COMPARABLE','NOT_COMPARABLE',U):_error('Invalid comparability state')
    if a['interpretation'] not in ('NOT_APPLICABLE','PROHIBITED_UNTIL_T14','OWNER_REVIEW_REQUIRED_NO_AUTOMATIC_INTERPRETATION'):_error('No automatic protocol interpretation is allowed')

def validate_state(state,root=None):
    if root is None:root=Path(__file__).resolve().parents[2]
    for r in state.get(COLLECTION,[]):
        e=validate_links(r['packet'],state,root)
        if e['kind']=='CONTROLLED_PROTOCOL':
            expected='PROHIBITED_UNTIL_T14' if r['packet']['actual_date']<e['protocol']['schedule']['t14'] else 'OWNER_REVIEW_REQUIRED_NO_AUTOMATIC_INTERPRETATION'
            if r['assessment']['interpretation']!=expected:_error('Controlled interpretation restriction changed')

def verify_evidence(root,state):
    previous=load_json(root/'book-radar/state.json').get(COLLECTION,[]) if (root/'book-radar/state.json').exists() else []
    previous_ids={old['id'] for old in previous}
    current={r['id']:r for r in state.get(COLLECTION,[])}
    if any(current.get(r['id'])!=r for r in previous):_error('Checkpoint receipts are immutable and append-only')
    for r in state.get(COLLECTION,[]):
        refs=[r['source'],*list(_evidence_refs(r['packet']))]
        for ref in refs:
            if evidence(root,ref['path'])!=ref:_error('Checkpoint evidence bytes changed')
        if load_json(root/r['source']['path'])!=r['packet']:_error('Source packet bytes/content mismatch')
        if r['id'] not in previous_ids and r['assessment']!=assess(root,state,r['packet'],today(root)):_error('New checkpoint receipt assessment differs from validated evidence')

def _baseline(state,p,e):
    previous=[r for r in state.get(COLLECTION,[]) if r['packet']['experiment_id']==e['id'] and r['id']!=p['id'] and (r['packet']['actual_date']<p['actual_date'] or r['packet']['actual_date']==p['actual_date'] and r['packet']['observed_at']!=U and p['observed_at']!=U and datetime.fromisoformat(r['packet']['observed_at'])<datetime.fromisoformat(p['observed_at']))]
    if previous:
        r=max(previous,key=lambda r:(r['packet']['actual_date'],datetime.fromisoformat(r['packet']['observed_at']).timestamp() if r['packet']['observed_at']!=U else float('-inf')));return r['id'],r['packet']
    bid=(e['book'] or {}).get('id',U)
    actuals=[a for a in state['actuals'] if a.get('book_id')==bid and a.get('schema_version')=='book-radar-observed-actual/v1' and a['observed_date']<p['actual_date']]
    if not actuals:return U,{'accounts':[],'search_snapshots':[],'categories':[]}
    a=max(actuals,key=lambda a:a['observed_date']);scope=a['marketplace_scope']
    row={'subject_id':bid,'scope':scope,'marketplace':U,'formats':U,'orders':a['windows']['lifetime'],'kenp':a['windows']['kenp'],'royalties':a['windows']['money']}
    return a['id'],{'accounts':[row],'search_snapshots':[q for q in state['search_snapshots'] if q['book_id']==bid and q['observed_date']<p['actual_date']],'categories':a['category_observations']}

def comparability(state,p,e):
    previous,old=_baseline(state,p,e);good=[];bad=[];unknown=[]
    def compare(label,a,b):
        if a==U or b==U:unknown.append(label+': unknown historical/current context')
        elif a!=b:bad.append(label+': different values')
        else:good.append(label)
    for a in p['accounts']:
        b=next((b for b in old['accounts'] if b['subject_id']==a['subject_id']),None)
        if not b:unknown.append('account: no previous subject');continue
        for k in ('scope','marketplace','formats'):
            av,bv=a[k],b[k]
            if k=='formats' and isinstance(av,list) and isinstance(bv,list):av,bv=sorted(av),sorted(bv)
            compare('account.'+k,av,bv)
        for k in ('orders','kenp','royalties'):
            if a[k]==U or b[k]==U:unknown.append(k+': reporting window unknown');continue
            for field in ('start','end'):compare(k+'.window.'+field,a[k][field],b[k][field])
            if k=='royalties':compare('royalties.currency',a[k]['currency'],b[k]['currency'])
    for a in p['search_snapshots']:
        matches=[b for b in old['search_snapshots'] if b['query']==a['query'] and b['marketplace']==a['marketplace']]
        b=max(matches,key=lambda b:b['observed_date']) if matches else None
        if not b:
            if old['search_snapshots']:bad.append('search: no matching marketplace/query among retained previous routes')
            else:unknown.append('search: historical query/marketplace not retained')
            continue
        for k in ('depth','rank_basis','signed_in_context','device_surface','delivery_context'):compare('search '+a['query']+'.'+k,a[k],b[k])
    for a in p['categories']:
        b=next((b for b in old.get('categories',[]) if b.get('category')==a['target_category'] and b['marketplace']==a['marketplace']),None)
        if not b:unknown.append('category: previous route unknown');continue
        for k in ('depth','context'):compare('category.'+k,a[k],b.get(k,U))
    status='UNKNOWN' if previous==U or not good and not bad else 'PARTIALLY_COMPARABLE' if good and (bad or unknown) else 'NOT_COMPARABLE' if bad else 'COMPARABLE'
    reasons=list(dict.fromkeys(bad+unknown)) or ([] if good else ['No comparable prior observation'])
    return {'status':status,'compared_to':previous,'reasons':reasons}

def assess(root,state,p,as_of):
    validate_packet(p);e=validate_links(p,state,root)
    if p['actual_date']>as_of:_error('Actual observation cannot be in the future')
    comp=comparability(state,p,e);declared=p['comparability']
    if declared['status']!=U and declared['status']!=comp['status']:_error('Declared comparability hides known limitations')
    if declared['compared_to']!=U and declared['compared_to']!=comp['compared_to']:_error('Comparability baseline identity mismatch')
    comp['reasons']=list(dict.fromkeys(comp['reasons']+declared['reasons']))
    interpretation='NOT_APPLICABLE'
    if e['kind']=='CONTROLLED_PROTOCOL':interpretation='PROHIBITED_UNTIL_T14' if p['actual_date']<e['protocol']['schedule']['t14'] else 'OWNER_REVIEW_REQUIRED_NO_AUTOMATIC_INTERPRETATION'
    return {'timing':_timing(p),'comparability':comp,'interpretation':interpretation}

def record_packet(root,source,as_of=None):
    from .book_radar import load_state,save_state,_append_unique
    state=load_state(root);p=load_json(source);as_of=as_of or today(root)
    validate_packet(p)
    try:ref=evidence(root,source.resolve().relative_to(root.resolve()).as_posix())
    except ValueError as error:raise ValidationError('Retain the evidence packet inside the repository before import') from error
    for source_ref in _evidence_refs(p):
        if evidence(root,source_ref['path'])!=source_ref:_error('Evidence hash mismatch/changed bytes')
    prior=next((r for r in state.get(COLLECTION,[]) if r['id']==p['id']),None)
    if prior:
        if prior['source']['sha256']!=ref['sha256'] or prior['packet']!=p:_error('Same checkpoint identity with changed bytes rejected')
        verify_evidence(root,state);return {'status':'ALREADY_RECORDED','added':0,'external_writes':0}
    assessment=assess(root,state,p,as_of)
    r={'schema_version':RECEIPT,'id':p['id'],'source':ref,'packet':p,'assessment':assessment}
    added={COLLECTION:_append_unique(state,COLLECTION,[r])}
    for col,rows in p.get('records',{}).items():added[col]=_append_unique(state,col,rows)
    if resolve(state,root,p['experiment_id'])['kind']=='BOOK':added['search_snapshots']=_append_unique(state,'search_snapshots',p['search_snapshots'])
    save_state(root,state)
    return {'status':'RECORDED','added':added,'assessment':assessment,'external_writes':0}

def check_packet(root,source,as_of=None):
    from .book_radar import load_state
    p=load_json(source)
    assessment=assess(root,load_state(root),p,as_of or today(root))
    for ref in _evidence_refs(p):
        if evidence(root,ref['path'])!=ref:_error('Evidence hash mismatch/changed bytes')
    return {'status':'VALID','assessment':assessment}

def _rows(state,e,as_of):
    labels=('T7','T14') if e['kind']=='CONTROLLED_PROTOCOL' else tuple('D'+str(d) for d in CHECKPOINTS)
    bid=(e['book'] or {}).get('id',U)
    historical=[a for a in state['actuals'] if a.get('book_id')==bid and a.get('schema_version')=='book-radar-observed-actual/v1' and a['observed_date']<=as_of]
    first=min((a['observed_date'] for a in historical),default=U)
    rows=[]
    for cp in labels:
        target,pub=_target(e,cp);captures=[r for r in state.get(COLLECTION,[]) if r['packet']['experiment_id']==e['id'] and r['packet']['checkpoint']==cp and r['packet']['actual_date']<=as_of and r['packet']['collection_state']=='COMPLETE']
        exact=[a for a in historical if a['checkpoint']==cp and a['observed_date']==target]
        status='MISSING';reason='Publication anchor UNKNOWN';ids=[]
        if captures:
            r=max(captures,key=lambda r:(r['assessment']['timing']=='EXACT',r['packet']['actual_date']))
            status='NOT_APPLICABLE' if r['assessment']['timing']=='NOT_APPLICABLE' else 'COLLECTED_'+r['assessment']['timing'] if r['assessment']['timing']!=U else 'MISSING'
            reason='Explicit checkpoint packet; capture timing is not metric completeness';ids=[r['id']]
        elif exact:status='COLLECTED_EXACT';reason='Explicit canonical checkpoint actual';ids=[a['id'] for a in exact]
        elif target!=U:
            status='UPCOMING' if target>as_of else 'DUE_TODAY' if target==as_of else 'OVERDUE'
            reason='No explicit complete checkpoint capture'
            if target<as_of and first!=U and target<first:status='MISSING';reason='Historical checkpoint before earliest retained actual; no backfill'
        rows.append({'experiment_id':e['id'],'title':e['title'],'checkpoint':cp,'target_date':target,'status':status,'reason':reason,'observation_ids':ids})
    return rows

def due(root,as_of=None):
    from .book_radar import load_state
    state=load_state(root);as_of=as_of or today(root);date.fromisoformat(as_of)
    all_experiments=experiments(state,root)
    rows=[r for e in all_experiments for r in _rows(state,{**e,'state':state},as_of)]
    live_due=[r for e in all_experiments for r in _live_confirmation(state,e,as_of)]
    waiting={r['experiment_id'] for r in live_due}
    active=[r for r in rows if r['experiment_id'] not in waiting and (r['status'] in ('DUE_TODAY','OVERDUE') or r['status']=='MISSING' and r['target_date']==U)]
    upcoming=[]
    for e in experiments(state,root):
        if e['id'] in waiting:continue
        candidates=[r for r in rows if r['experiment_id']==e['id'] and r['status']=='UPCOMING']
        if candidates:upcoming.append(min(candidates,key=lambda r:r['target_date']))
    p=protocol(root)
    return {'as_of':as_of,'due':active,'live_confirmation_due':live_due,'upcoming':sorted(upcoming,key=lambda r:(r['target_date'],r['experiment_id'])),'checkpoints':rows,'historical_missing':sum(r['status']=='MISSING' and r['target_date']!=U for r in rows),'controlled_interpretation':'PROHIBITED UNTIL T14' if as_of<p['schedule']['t14'] else 'OWNER REVIEW REQUIRED; NO AUTOMATIC INTERPRETATION','t14_date':p['schedule']['t14'],'external_writes':0}

def checklist(root,identifier,as_of=None):
    from .book_radar import load_state
    state=load_state(root);e=resolve(state,root,identifier);as_of=as_of or today(root);rows=_rows(state,{**e,'state':state},as_of)
    pending=[r for r in rows if r['status'] in ('UPCOMING','DUE_TODAY','OVERDUE') or r['target_date']==U]
    live_due=_live_confirmation(state,e,as_of)
    next_row=live_due[0] if live_due else min(pending,key=lambda r:r['target_date']) if pending and all(r['target_date']!=U for r in pending) else pending[0] if pending else U
    b=e['book'] or {};o=obligations(state,e)
    t0_path=root/'book-radar/calibration/controlled-persistence-v1/t0/t0-observations.json'
    cohorts=load_json(t0_path).get('queries',[]) if e['kind']=='CONTROLLED_PROTOCOL' and t0_path.is_file() else []
    previous=[a for a in state['actuals'] if a.get('book_id')==b.get('id',U) and a.get('observed_date','9999')<=as_of]
    latest=max(previous,key=lambda a:a.get('observed_date','')) if previous else None
    packets=[r for r in state.get(COLLECTION,[]) if r['packet']['experiment_id']==e['id'] and r['packet']['accounts'] and r['packet']['actual_date']<=as_of]
    latest_packet=max(packets,key=lambda r:r['packet']['actual_date']) if packets else None
    prior_account={'id':latest['id'],'date':latest['observed_date']} if latest else U
    prior_comparability=U
    if latest_packet and (latest is None or latest_packet['packet']['actual_date']>=latest['observed_date']):
        prior_account={'id':latest_packet['id'],'date':latest_packet['packet']['actual_date']};prior_comparability=latest_packet['assessment']['comparability']['status']
    return {'experiment_id':e['id'],'title':e['title'],'kind':e['kind'],'next':next_row,'live_confirmation_due':live_due,'publication_date':b.get('publication_date',U),'first_verified_live_date':b.get('first_verified_live_date',U),'formats':o['retailers'],'collect':['Paid / Free and paid format split, exact report windows/scope','KENP and estimated royalties in their own windows','Availability / identity / current displayed price for retained formats','Repeat listed queries and category routes; preserve depth and context','Retain hashes and capture timestamp; costs optional; explicit comparability'],'queries':o['queries'],'categories':o['categories'],'previous_account':prior_account,'previous_search_dates':sorted({q['observed_date'] for q in state['search_snapshots'] if q['book_id']==b.get('id',U)}),'previous_comparability':prior_comparability,'not_observable':{k:'NOT_OBSERVABLE_FROM_CURRENT_STANDARD_SOURCE' for k in UNOBSERVABLE},'frozen_expected_path':e['contract']['plan']['expected_path'] if e['contract'] else U,'interpretation':('PROHIBITED UNTIL T14' if as_of<e['protocol']['schedule']['t14'] else 'OWNER REVIEW REQUIRED; NO AUTOMATIC INTERPRETATION') if e['kind']=='CONTROLLED_PROTOCOL' else 'Use accepted attribution rules only; no new adjudication here','fixed_cohorts':cohorts,'controlled_context':'All departments; default Featured; signed out; first 16 organic positions; fixed cohorts/ASINs from retained T0' if e['kind']=='CONTROLLED_PROTOCOL' else U}

def status(root,as_of=None):
    from .book_radar import load_state
    from .book_radar_attribution import report as accepted_report
    state=load_state(root);as_of=as_of or today(root);rows=[]
    accepted=accepted_report(root,'cards',as_of)['experiments']
    for e in experiments(state,root):
        b=e['book'] or {};cp=_rows(state,{**e,'state':state},as_of);pending=[r for r in cp if r['status'] in ('DUE_TODAY','OVERDUE','UPCOMING') or r['target_date']==U]
        live_due=_live_confirmation(state,e,as_of)
        next_row=live_due[0] if live_due else min(pending,key=lambda r:r['target_date']) if pending and all(r['target_date']!=U for r in pending) else pending[0] if pending else U
        packets=[r for r in state.get(COLLECTION,[]) if r['packet']['experiment_id']==e['id'] and r['packet']['actual_date']<=as_of]
        latest=max(packets,key=lambda r:(r['packet']['actual_date'],r['packet']['observed_at'])) if packets else None
        actuals=[a for a in state['actuals'] if a.get('book_id')==b.get('id',U) and a.get('observed_date','9999')<=as_of]
        last=max(actuals,key=lambda a:a['observed_date']) if actuals else None
        attr=next((a for a in accepted if a['id'] in (e['id'],'historical:'+e['id'])),None)
        missing=[]
        for name in ('accounts','retailers','search_snapshots','categories'):
            if latest is None or not latest['packet'][name]:missing.append('checkpoint.'+name)
        if latest:
            for a in latest['packet']['accounts']:
                for key in ('orders','kenp','royalties'):
                    if a[key]==U:missing.append(key)
                    else:missing.extend(key+'.'+k for k,v in a[key].items() if v==U)
            if not latest['packet']['costs']:missing.append('costs UNKNOWN (optional)')
        calibration=[c for c in state['calibrations'] if c.get('book_id')==b.get('id') and c.get('observed_date','9999')<=as_of]
        pub=_checkpoint_anchor(e,state)
        native_checkpoints=[a for a in actuals if a.get('checkpoint') in tuple('D'+str(d) for d in CHECKPOINTS)]
        native_last=max(native_checkpoints,key=lambda a:a['observed_date']) if native_checkpoints else None
        checkpoint_experiment={**e,'state':state}
        rows.append({'experiment_id':e['id'],'title':e['title'],'current_age_days':(date.fromisoformat(as_of)-date.fromisoformat(pub)).days if pub!=U else U,'latest_checkpoint':{'id':latest['id'],'checkpoint':latest['packet']['checkpoint'],'actual_date':latest['packet']['actual_date'],'timing':latest['assessment']['timing'],'collection_state':latest['packet']['collection_state']} if latest else {'id':native_last['id'],'checkpoint':native_last['checkpoint'],'actual_date':native_last['observed_date'],'timing':('EXACT' if native_last['observed_date']==_target(checkpoint_experiment,native_last['checkpoint'])[0] else 'LATE' if _target(checkpoint_experiment,native_last['checkpoint'])[0]!=U and native_last['observed_date']>_target(checkpoint_experiment,native_last['checkpoint'])[0] else U),'collection_state':'CANONICAL_ACCOUNT_CHECKPOINT'} if native_last else U,'latest_actual':({'id':latest['id'],'date':latest['packet']['actual_date'],'source':'CHECKPOINT_PACKET'} if latest and latest['packet']['accounts'] and (not last or latest['packet']['actual_date']>=last['observed_date']) else {'id':last['id'],'date':last['observed_date'],'source':'FOUNDATION_ACTUAL'} if last else U),'next':next_row,'missing_evidence':missing,'not_observable':list(UNOBSERVABLE),'comparability':latest['assessment']['comparability'] if latest else {'status':U,'reasons':['Historical context not fully retained']},'attribution_state':attr['attribution'] if attr else U,'attribution_source_date':attr['observation'].get('observed_date',U) if attr and isinstance(attr['observation'],dict) else U,'calibration_state':[{'id':c['id'],'status':c['status'],'observed_date':c['observed_date']} for c in calibration] or U,'protocol_interpretation':due(root,as_of)['controlled_interpretation'] if e['kind']=='CONTROLLED_PROTOCOL' else 'NOT_APPLICABLE'})
    return {'as_of':as_of,'experiments':rows,'read_only':True,'new_attribution_records':0,'new_calibration_records':0,'external_writes':0}

def template(root,identifier,cp,as_of=None):
    from .book_radar import load_state
    state=load_state(root);e=resolve(state,root,identifier);target,pub=_target({**e,'state':state},cp)
    return {'schema_version':PACKET,'id':'packet:REPLACE_WITH_UNIQUE_CAPTURE_ID','experiment_id':e['id'],'checkpoint':cp,'target_date':target,'actual_date':'REPLACE_WITH_ACTUAL_CAPTURE_DATE','observed_at':U,'timezone':protocol(root)['schedule']['timezone'],'book_age_days':U,'collection_state':'PARTIAL','approximate_tolerance_days':0,'applicability':{'state':'APPLICABLE','recorded_by':'OPERATOR','reason':'Manual collection','evidence':[]},'accounts':[],'retailers':[],'search_snapshots':[],'categories':[],'costs':[],'not_observable':{k:'NOT_OBSERVABLE_FROM_CURRENT_STANDARD_SOURCE' for k in UNOBSERVABLE},'comparability':{'status':U,'compared_to':U,'reasons':[]},'evidence':[],'notes':['Complete actual date and commercial age from the checkpoint anchor; for submission-tracked books this is the earliest supported format LIVE date. Preserve each format LIVE date separately. Template is not yet a valid observation.']}

def render(value,mode):
    if mode=='due':
        lines=['RADAR OBSERVATIONS DUE — '+value['as_of']]
        for label,key in [('DUE NOW','due'),('NEXT UPCOMING','upcoming')]:
            lines+=['',label]
            lines += [f"{r['experiment_id']} | {r['checkpoint']} | {r['target_date']} | {r['status']}" for r in value[key]] or ['None']
            if key=='due':
                lines+=['','CONFIRM LIVE STATUS']
                lines += [f"{r['experiment_id']} | {r['format']} | {r['status']} | ASIN {r['asin']} | submitted {r['submission_date']}" for r in value['live_confirmation_due']] or ['None']
        lines+=['',f"Historical missing checkpoints: {value['historical_missing']} — no backfill",'INTERPRETATION: '+value['controlled_interpretation'],'Checklist: ./bin/abvx radar observe <experiment-id>']
        return '\n'.join(lines)
    if mode=='checklist':
        lines=[value['title'],value['experiment_id'],'NEXT: '+json.dumps(value['next'],ensure_ascii=False),'']
        if value['live_confirmation_due']:
            lines+=['CONFIRM LIVE STATUS BY FORMAT:']+[json.dumps(r,ensure_ascii=False) for r in value['live_confirmation_due']]
        lines+=['[ ] '+item for item in value['collect']]
        lines+=['','RETAILER IDENTITIES:']+[json.dumps(f,ensure_ascii=False) for f in value['formats']]
        lines+=['','SEARCH ROUTES (repeat verbatim):']+[json.dumps(q,ensure_ascii=False) for q in value['queries']]
        lines+=['','CATEGORY ROUTES:']+[json.dumps(c,ensure_ascii=False) for c in value['categories']]
        lines+=['Repeat direct ASIN page breadcrumb/rank context; missing position stays UNKNOWN.','', 'PREVIOUS ACCOUNT: '+json.dumps(value['previous_account']), 'PREVIOUS SEARCH DATES: '+json.dumps(value['previous_search_dates']),'PREVIOUS COMPARABILITY: '+value['previous_comparability'],'','NOT OBSERVABLE: '+', '.join(value['not_observable']),'INTERPRETATION: '+value['interpretation']]
        if value['controlled_context']!=U:lines+=['CONTEXT: '+value['controlled_context'],'FIXED T0 COHORTS (retain missing identities as NOT_CAPTURED):',json.dumps(value['fixed_cohorts'],ensure_ascii=False)]
        return '\n'.join(lines)
    if mode=='status':
        lines=['RADAR OBSERVATION STATUS — '+value['as_of']]
        for r in value['experiments']:
            lines+=['',r['experiment_id']+' | age '+str(r['current_age_days']),'LATEST CHECKPOINT: '+json.dumps(r['latest_checkpoint']),'LATEST ACTUAL: '+json.dumps(r['latest_actual']),'NEXT: '+json.dumps(r['next']),'MISSING: '+', '.join(r['missing_evidence']),'COMPARABILITY: '+r['comparability']['status'],'ATTRIBUTION (existing rules; source '+r['attribution_source_date']+'): '+json.dumps(r['attribution_state']),'CALIBRATION (retained): '+json.dumps(r['calibration_state'])]
            if r['protocol_interpretation']!='NOT_APPLICABLE':lines+=['INTERPRETATION: '+r['protocol_interpretation']]
        return '\n'.join(lines)
    return json.dumps(value,ensure_ascii=False,indent=2)
