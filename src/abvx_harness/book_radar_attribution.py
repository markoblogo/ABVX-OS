"""Phase 2: prospective experiment admission and conservative attribution only."""
from __future__ import annotations
import json
from collections import Counter
from copy import deepcopy
from datetime import date, datetime, timezone
from functools import lru_cache
from pathlib import Path
from .harness import ValidationError, load_json
from .book_radar_outcomes import UNKNOWN as U, checkpoint, evidence, _evidence_refs

STAGES=('MARKET_OPPORTUNITY','AMAZON_AVAILABILITY','DISCOVERY','VISIBILITY','DETAIL_PAGE_VISIT','SAMPLE_KU_START','PURCHASE_READ','ROYALTY','SERIES_READ_THROUGH')
STATES=('POSITIVE','ZERO','UNKNOWN','NOT_APPLICABLE','NOT_OBSERVABLE')
COLLECTIONS=('experiment_policies','experiment_contracts','attribution_observations','search_snapshots','experiment_costs','series_observations')
COSTS=('owner_minutes','ai_api','production_minutes','rework_minutes','artwork','advertising_acquisition','external_services','elapsed_calendar_days')

@lru_cache(maxsize=6)
def validator(collection):
    from .schema_validation import draft_2020_12_validator
    schema=load_json(Path(__file__).resolve().parents[2]/'schemas/book_radar_attribution.schema.json')
    schema['$ref']='#/$defs/'+collection
    return draft_2020_12_validator(schema)

def validate_record(record,collection):
    if collection not in COLLECTIONS:return
    errors=list(validator(collection).iter_errors(record))
    if errors:raise ValidationError(f"{record.get('id')}: {errors[0].message}")
    if collection=='experiment_contracts':
        if record['status']=='FROZEN':
            for key,value in record['plan'].items():
                if value==U or value==[] or isinstance(value,str) and not value.strip():raise ValidationError(f'Frozen plan missing {key}')
            if any(value==U for value in record['cost_budget'].values()):raise ValidationError('Frozen budget requires explicit values, not UNKNOWN')
            if not record['evidence']:raise ValidationError('Frozen hypothesis requires provenance')
            if record['waiver'] is not None:raise ValidationError('Frozen experiment cannot silently carry a waiver')
            if set(record['plan']['checkpoints'])!={0,7,14,30,60,90}:raise ValidationError('All six checkpoint plans are required')
            if any(v==U for v in record['plan']['package_price'].values()):raise ValidationError('Frozen package/price cannot be UNKNOWN')
            if any(m['metric']==U or m['rule']==U or m['target']==U for m in record['plan']['checkpoint_measures'].values()):raise ValidationError('Checkpoints require measurable definitions')
        elif record['waiver'] is None or record['waiver']['recorded_by']!='OWNER' or not record['waiver']['evidence']:
            raise ValidationError('Waiver requires an explicit OWNER record')
        if record['waiver'] and (record['waiver']['reason']==U or datetime.fromisoformat(record['waiver']['recorded_at'])>datetime.fromisoformat(record['frozen_at'])):
            raise ValidationError('OWNER waiver reason/date must precede admission')
    if collection=='search_snapshots':
        if record['presence']!=U and not record['evidence']:raise ValidationError('Search observation requires provenance')
        if record['presence'] in ('NOT_FOUND_WITHIN_DEPTH',U) and record['rank']!=U:raise ValidationError('Absence cannot establish a rank')
        if record['presence']=='NOT_FOUND_WITHIN_DEPTH' and record['depth']==U:raise ValidationError('Absence requires inspected depth')
        if record['presence']=='FOUND' and record['rank']==U:raise ValidationError('Found presence requires observed rank')
        if record['rank']!=U and record['depth']!=U and record['rank']>record['depth']:raise ValidationError('Observed rank exceeds inspected depth')
        if record['observed_at']!=U and record['observed_at'][:10]!=record['observed_date']:raise ValidationError('Snapshot time/date mismatch')
    if collection=='attribution_observations':
        if record['publication_date']!=U and not record['publication_evidence']:raise ValidationError('Publication anchor requires evidence')
        if record['required_checkpoint_day']!=U:
            expected=checkpoint(record['publication_date'],record['observed_date'],record['required_checkpoint_day'])
            if record['checkpoint']!=expected:raise ValidationError('Checkpoint must derive from the actual date and publication anchor')
        elif record['checkpoint']['status']!=U:raise ValidationError('Unknown evaluation contract cannot assert an exact checkpoint')
        for stage in list(record['stages'].values())+[record['reading']]:
            if stage['state'] in ('POSITIVE','ZERO'):
                if stage['value']==U or not stage['evidence']:raise ValidationError('Observed stage requires value and evidence')
                if (stage['value']>0)!=(stage['state']=='POSITIVE'):raise ValidationError('Positive/zero value mismatch')
            elif stage['value']!=U:raise ValidationError('Unobserved stage cannot carry a numeric value')
            if stage['state'] in ('NOT_APPLICABLE','NOT_OBSERVABLE') and not stage['evidence']:raise ValidationError('Non-observability/applicability requires evidence')
        if record['reading']['state'] in ('POSITIVE','ZERO') and not record['reading']['evidence']:raise ValidationError('Reading requires direct evidence')
        metrics={'PAID_UNITS':'paid_units','KENP_PAGES':'kenp','ESTIMATED_ROYALTIES':'estimated_royalties'}
        for stage in record['stages'].values():
            if stage['state'] in ('POSITIVE','ZERO') and stage['metric'] in metrics:
                if stage['value']!=record['actual_outcomes'][metrics[stage['metric']]]:raise ValidationError('Observed metric must match its explicit outcome, never a proxy')
        if any(not learning['evidence'] for learning in record['learning']):raise ValidationError('Learning requires evidence and an explicit scope')
        for key in ('paid_window','kenp_window','royalty_window'):
            window=record['actual_outcomes'][key]
            if window!=U:
                try:start,end=map(date.fromisoformat,window.split('/'))
                except ValueError as error:raise ValidationError('Outcome windows require ISO start/end or UNKNOWN') from error
                if start>end or end>date.fromisoformat(record['observed_date']):raise ValidationError('Outcome window cannot include future data')
    if collection=='series_observations':
        if not record['membership_evidence']:raise ValidationError('Series/catalog membership requires provenance')
        if any(record[k]!=U for k in ('paid_units','free_units','kenp','estimated_royalties')) and not record['evidence']:raise ValidationError('Catalog aggregates require evidence')
        if record['method']=='DIRECT_MATCHED_COHORT':
            if record['entrants']==U or record['continuers']==U or record['continuers']>record['entrants'] or not record['identity_evidence']:raise ValidationError('Read-through requires matched cohort evidence')
            if record['entry_book_id']==record['continuation_book_id'] or not {record['entry_book_id'],record['continuation_book_id']}<=set(record['book_ids']) or record['cohort_basis']==U:raise ValidationError('Read-through requires an identified book pair and cohort basis')
        elif record['entrants']!=U or record['continuers']!=U:raise ValidationError('Aggregate title sales are not matched readers')
    if collection=='experiment_costs' and any(v!=U for v in record['actual'].values()) and not record['evidence']:
        raise ValidationError('Measured cost requires evidence')

def validate_state(state):
    policies=state.get('experiment_policies',[])
    if len(policies)>1:raise ValidationError('One immutable prospective admission policy is supported')
    products={p['id']:p for p in state['products']};books={b['id'] for b in state['observed_books']}
    contracts={c['id']:c for c in state.get('experiment_contracts',[])}
    decisions={d['id']:d for d in state['decisions']}
    for c in contracts.values():
        if c['product_id'] not in products:raise ValidationError('Experiment product missing')
        decision=decisions.get(c['selection_decision_id'])
        if c['status']=='FROZEN' and (decision is None or decision.get('opportunity_id')!=products[c['product_id']].get('opportunity_id')):raise ValidationError('Frozen contract requires linked selection evidence')
    if policies:
        policy=policies[0]
        if not set(policy['historical_product_ids'])<=set(products):raise ValidationError('Protected historical products missing')
        for p in products.values():
            if p['id'] in policy['historical_product_ids']:continue
            c=contracts.get(p.get('experiment_contract_id'))
            if c is None or c['product_id']!=p['id']:raise ValidationError(f"{p['id']}: frozen experiment or OWNER waiver required")
            if datetime.fromisoformat(c['frozen_at'])<datetime.fromisoformat(policy['effective_at']):raise ValidationError('New contract cannot be backdated before policy')
            started=p.get('production_started_at')
            if started:
                try:stamp=datetime.fromisoformat(started)
                except (ValueError,TypeError) as error:raise ValidationError('Production start requires an actual timestamp') from error
                if stamp.tzinfo is None:raise ValidationError('Production start requires timezone context')
                if datetime.fromisoformat(c['frozen_at'])>stamp:raise ValidationError('Contract/waiver must precede production')
        for d in decisions.values():
            if d['id'] not in policy['historical_decision_ids'] and d.get('production_authorized'):
                if not any(p.get('opportunity_id')==d.get('opportunity_id') and p.get('experiment_contract_id') in contracts for p in products.values()):raise ValidationError('Production authorization requires an admitted product/contract')
    for name in ('attribution_observations','search_snapshots','experiment_costs'):
        for o in state.get(name,[]):
            if o['experiment_id']!=U and o['experiment_id'] not in contracts:raise ValidationError('Observation experiment missing')
            if o.get('book_id',U)!=U and o['book_id'] not in books:raise ValidationError('Observation book missing')
            if name=='attribution_observations' and o['experiment_id']!=U:
                c=contracts[o['experiment_id']]
                if c['status']=='FROZEN' and o['required_checkpoint_day']!=c['plan']['evaluation_day']:raise ValidationError('Required checkpoint must match frozen evaluation day')
            if name=='attribution_observations' and o['book_id']!=U:
                book=next(b for b in state['observed_books'] if b['id']==o['book_id'])
                if book['publication_date']!=U and o['publication_date']!=book['publication_date']:raise ValidationError('Cannot replace a known publication anchor')
                if o['experiment_id']!=U and book['product_id']!=contracts[o['experiment_id']]['product_id']:raise ValidationError('Observation book/experiment product mismatch')
            if name=='attribution_observations' and o['actual_id']!=U:
                actual=next((a for a in state['actuals'] if a['id']==o['actual_id']),None)
                if actual is None or actual.get('book_id')!=o['book_id'] or actual.get('observed_date')!=o['observed_date']:raise ValidationError('Observation actual identity/date mismatch')
    for o in state.get('series_observations',[]):
        if not set(o['book_ids'])<=books:raise ValidationError('Series member identity missing')

def preserve_contracts(root,state):
    path=root/'book-radar/state.json'
    if not path.is_file():return
    before=load_json(path)
    immutable=COLLECTIONS
    if before.get('experiment_policies') or state.get('experiment_policies'):
        from .book_radar import COLLECTIONS as all_collections
        immutable=all_collections
    for col in immutable:
        previous=before.get(col,[]);current={r['id']:r for r in state.get(col,[])}
        if any(current.get(r['id'])!=r for r in previous):raise ValidationError(f'Immutable {col} changed or removed')
    if not before.get('experiment_policies') and state.get('experiment_policies'):
        if set(state['experiment_policies'][0]['historical_product_ids'])!={p['id'] for p in before['products']}:
            raise ValidationError('Policy cutover must freeze exactly the pre-existing products')
        if set(state['experiment_policies'][0]['historical_decision_ids'])!={d['id'] for d in before['decisions']}:raise ValidationError('Policy cutover must freeze pre-existing decisions')
    for col in COLLECTIONS:
        for record in state.get(col,[]):
            for ref in _evidence_refs(record):
                if evidence(root,ref['path'])!=ref:raise ValidationError('Attribution evidence hash mismatch')

def enable(root,owner_record):
    from .book_radar import load_state,save_state
    state=load_state(root)
    if state['experiment_policies']:return {'status':'ALREADY_ENABLED','policy':state['experiment_policies'][0]['id']}
    ref=evidence(root,str(owner_record.relative_to(root)))
    now=datetime.now(timezone.utc).isoformat()
    policy={'schema_version':'book-radar-experiment-policy/v1','id':'policy:prospective-experiments:v1','effective_at':now,'historical_product_ids':[p['id'] for p in state['products']],'historical_decision_ids':[d['id'] for d in state['decisions']],'recorded_by':'OWNER','evidence':[ref]}
    state['experiment_policies'].append(policy);save_state(root,state)
    return {'status':'ENABLED','policy':policy,'external_writes':0}

def import_records(root,source):
    from .book_radar import load_state,save_state,_append_unique
    bundle=load_json(source);allowed=set(COLLECTIONS)-{'experiment_policies'}
    if bundle.get('schema_version')!='book-radar-attribution-import/v1' or set(bundle)-allowed-{'schema_version'}:raise ValidationError('Unsupported attribution import')
    refs={(r['path'],r['sha256']):r for r in _evidence_refs(bundle)}
    for ref in refs.values():
        if evidence(root,ref['path'])!=ref:raise ValidationError('Evidence hash mismatch')
    state=load_state(root)
    added={col:_append_unique(state,col,bundle.get(col,[])) for col in allowed}
    save_state(root,state)
    return {'status':'ATTRIBUTION_RECORDED','added':added,'external_writes':0}

def measure(state=U,metric=U,value=U,window=U,scope=U,refs=None,coverage='PARTIAL'):
    return {'state':state,'metric':metric,'value':value,'window':window,'scope':scope,'evidence':refs or [],'coverage':coverage}

def attribute(observation,contract=None):
    """Failure attribution cannot bypass unknown/not-observable upstream stages."""
    stages=observation['stages'];cp=observation['checkpoint']
    if cp['status']!='EXACT':return {'classification':'INSUFFICIENT_OBSERVATION' if cp['status'] in ('PENDING','UNKNOWN') else U,'evidence':[],'reason':'Required checkpoint not observed exactly'}
    def partial(value):
        if isinstance(value,dict):return any(partial(v) for v in value.values())
        if isinstance(value,list):return not value or any(partial(v) for v in value)
        return value==U
    if contract and contract['status']=='WAIVED' and partial(contract['plan']):
        return {'classification':U,'evidence':[],'reason':'Explicitly waived partial hypothesis cannot support failure attribution'}
    def prefix(target):
        return all(stages[k]['state'] in ('POSITIVE','NOT_APPLICABLE') for k in STAGES[:STAGES.index(target)])
    def comparable(*keys):
        rows=[stages[k] for k in keys]
        return len({(x['window'],x['scope']) for x in rows})==1 and rows[0]['window']!=U and rows[0]['scope']!=U and all(x['coverage']=='COMPLETE' and x['evidence'] for x in rows)
    market=stages['MARKET_OPPORTUNITY']
    if market['state']=='ZERO' and market['metric']=='DIRECT_DEMAND_TEST' and market['coverage']=='COMPLETE' and market['evidence'] and market['window']!=U and market['scope']!=U:
        return {'classification':'MARKET_HYPOTHESIS_UNSUPPORTED','evidence':market['evidence'],'reason':'Direct prespecified demand test, not no sales'}
    discovery=stages['DISCOVERY'];vis=stages['VISIBILITY'];visit=stages['DETAIL_PAGE_VISIT'];purchase=stages['PURCHASE_READ']
    label=U;keys=[]
    if prefix('DISCOVERY') and discovery['state']=='ZERO' and discovery['metric']=='FROZEN_ROUTE_TEST' and comparable('DISCOVERY'):label='NOT_DISCOVERED';keys=['DISCOVERY']
    elif prefix('DETAIL_PAGE_VISIT') and vis['metric']=='CUSTOMER_IMPRESSIONS' and visit['state']=='ZERO' and visit['metric']=='DETAIL_PAGE_VISITS' and comparable('VISIBILITY','DETAIL_PAGE_VISIT'):
        label='DISCOVERED_NOT_CLICKED';keys=['VISIBILITY','DETAIL_PAGE_VISIT']
    elif prefix('PURCHASE_READ') and visit['metric']=='DETAIL_PAGE_VISITS' and purchase['state']=='ZERO' and purchase['metric']=='PAID_UNITS' and comparable('DETAIL_PAGE_VISIT','PURCHASE_READ'):
        label='VISITED_NOT_CONVERTED';keys=['DETAIL_PAGE_VISIT','PURCHASE_READ']
    reading=observation['reading']
    if prefix('PURCHASE_READ') and purchase['state']=='POSITIVE' and purchase['metric']=='PAID_UNITS' and purchase['coverage']=='COMPLETE' and purchase['evidence'] and purchase['window']!=U and purchase['scope']!=U and reading['state']=='ZERO' and reading['metric']=='MATCHED_PURCHASER_READS' and reading['coverage']=='COMPLETE' and reading['evidence'] and reading['window']==purchase['window'] and reading['scope']==purchase['scope']:
        label='PURCHASED_NOT_READ';keys=['PURCHASE_READ']
    return {'classification':label,'evidence':[r for k in keys for r in stages[k]['evidence']]+(reading['evidence'] if label=='PURCHASED_NOT_READ' else []),'reason':'Evidence-bound route/window finding' if label!=U else 'Unknown upstream stage, mismatched scope/window, or incomplete evidence'}

def historical_view(book,actual,claims,as_of,capability_ref):
    """Projection, not a rewrite or new retrospective experiment contract."""
    stages={s:measure() for s in STAGES}
    for new,old in [('AMAZON_AVAILABILITY','PUBLISHED'),('DISCOVERY','DISCOVERABLE')]:
        oldstage=actual['funnel'][old]
        if oldstage['state']=='OBSERVED_POSITIVE':stages[new]=measure('POSITIVE','LISTING_PRESENT' if new=='AMAZON_AVAILABILITY' else 'QUERY_PRESENCE',1,oldstage['window'],'BOUNDED_RETAILER_CONTEXT',oldstage['evidence'])
    # Search visibility is not the number of customer impressions.
    if stages['DISCOVERY']['state']=='POSITIVE':stages['VISIBILITY']=deepcopy(stages['DISCOVERY'])
    for s,metric in [('DETAIL_PAGE_VISIT','DETAIL_PAGE_VISITS'),('SAMPLE_KU_START','KU_STARTS'),('SERIES_READ_THROUGH','MATCHED_READER_CONTINUATION')]:
        stages[s]=measure('NOT_OBSERVABLE',metric,refs=[capability_ref])
    lifetime=actual['windows']['lifetime'];kenp=actual['windows']['kenp'];money=actual['windows']['money']
    paid=lifetime['paid_units'];pages=kenp['kenp_pages'];royalty=money['estimated_royalties']
    positive=any(v!=U and v>0 for v in (paid,pages))
    known=positive or all(v!=U for v in (paid,pages))
    stages['PURCHASE_READ']=measure('POSITIVE' if positive else 'ZERO' if known else U,'PAID_UNITS_OR_KENP',1 if positive else 0 if known else U,'MULTIPLE_EXPLICIT_WINDOWS','KDP_ACCOUNT',lifetime['evidence']+kenp['evidence'])
    stages['ROYALTY']=measure('POSITIVE' if royalty!=U and royalty>0 else 'ZERO' if royalty!=U else U,'ESTIMATED_ROYALTIES',royalty,money['start']+'/'+money['end'],'KDP_ACCOUNT_'+money['currency'],money['evidence'])
    days=[c['claim']['horizon_days'] for c in claims if c['claim']['horizon_days']!=U]
    cp=checkpoint(book['publication_date'],actual['observed_date'],max(days)) if days else {'checkpoint':U,'status':U,'actual_observation_date':actual['observed_date'],'actual_book_age_days':actual['book_age_days'],'due_date':U,'age_basis':'PUBLICATION_DATE_ONLY_NOT_FIRST_LIVE'}
    reading=measure('NOT_OBSERVABLE','MATCHED_PURCHASER_READS',refs=[capability_ref])
    return {'schema_version':'book-radar-attribution-observation/v1','id':'projection:'+actual['id'],'book_id':book['id'],'experiment_id':U,'observed_date':actual['observed_date'],'publication_date':book['publication_date'],'publication_evidence':book['date_evidence'],'required_checkpoint_day':max(days) if days else U,'stages':stages,'reading':reading,'checkpoint':cp,'actual_id':actual['id'],'actual_outcomes':{'paid_units':lifetime['paid_units'],'free_units':lifetime['free_units'],'ebook_paid':lifetime['ebook_paid'],'print_paid':lifetime['print_paid'],'kenp':kenp['kenp_pages'],'kenp_window':kenp['start']+'/'+kenp['end'],'estimated_royalties':money['estimated_royalties'],'currency':money['currency'],'paid_window':lifetime['start']+'/'+lifetime['end'],'royalty_window':money['start']+'/'+money['end'],'royalty_status':money['status'],'kenp_status':kenp['status'],'marketplace_scope':actual['marketplace_scope']},'learning':[]}

def series_summary(observation):
    direct=observation['method']=='DIRECT_MATCHED_COHORT'
    return {**observation,'read_through':observation['continuers']/observation['entrants'] if direct and observation['entrants']>0 else U,'causality':'NOT_ESTABLISHED','sales_ratio_is_read_through':False}

def report(root,kind,as_of):
    from .book_radar import load_state
    from .book_radar_outcomes import outcome_report
    date.fromisoformat(as_of)
    state=load_state(root);out=root/'book-radar/audits/observation-attribution-v1'
    ref=evidence(root,str((out/'DATA_OBSERVABILITY_V1.md').relative_to(root)))
    experiments=[]
    for book in state['observed_books']:
        if not book['initial_experiment']:continue
        rows=[a for a in state['actuals'] if a.get('schema_version')=='book-radar-observed-actual/v1' and a['book_id']==book['id'] and a['observed_date']<=as_of]
        if not rows:continue
        actual=max(rows,key=lambda a:a['observed_date']);claims=[c for c in state['calibrations'] if c.get('book_id')==book['id'] and c['observed_date']<=as_of]
        obs=historical_view(book,actual,claims,as_of,ref)
        partial=next((h for h in state['commercial_hypotheses'] if h['book_id']==book['id']),None)
        decisions=[d for d in state['decisions'] if d['id'] in book['decision_ids']]
        experiments.append({'id':'historical:'+book['audit_book_id'],'title':book['title'],'status':'HISTORICAL_PARTIAL','contract':partial or U,'selection':decisions,'observation':obs,'attribution':attribute(obs),'cost_budget':U,'actual_cost':{**{c:U for c in COSTS},'currency':U},'checkpoints':[checkpoint(book['publication_date'],actual['observed_date'],d) for d in (0,7,14,30,60,90)],'learned':'No causal learning; incomplete observation. T7/T14 protocol not interpreted.'})
        experiments[-1]['checkpoint_observations']={f'D{d}':[a['id'] for a in rows if a['book_age_days']==d] or U for d in (0,7,14,30,60,90)}
    for contract in state['experiment_contracts']:
        if contract['frozen_at'][:10]>as_of:continue
        obs=[o for o in state['attribution_observations'] if o['experiment_id']==contract['id'] and o['observed_date']<=as_of]
        latest=max(obs,key=lambda o:o['observed_date']) if obs else None
        costs=[c for c in state['experiment_costs'] if c['experiment_id']==contract['id'] and c['observed_date']<=as_of]
        experiments.append({'id':contract['id'],'title':products_title(state,contract['product_id']),'status':contract['status'],'contract':contract,'selection':contract['plan']['selection_reason'],'observation':latest or U,'attribution':attribute(latest,contract) if latest else {'classification':U,'reason':'No observations','evidence':[]},'cost_budget':contract['cost_budget'],'actual_cost':max(costs,key=lambda c:c['observed_date'])['actual'] if costs else {**{c:U for c in COSTS},'currency':U},'checkpoints':contract['plan']['checkpoint_measures'],'learned':latest['learning'] if latest else U})
        experiments[-1]['checkpoint_observations']={f'D{d}':[o['id'] for o in obs if o['checkpoint']['actual_book_age_days']==d] or U for d in (0,7,14,30,60,90)}
    if kind=='series':return {'report':kind,'as_of':as_of,'series':[series_summary(o) for o in state['series_observations'] if o['observed_date']<=as_of],'toki_comparison':outcome_report(root,'cohorts',as_of)}
    if kind=='funnel':
        counts={s:{v:0 for v in STATES} for s in STAGES};unknown_frontier=Counter()
        metric_counts={s:Counter() for s in STAGES}
        for e in experiments:
            stages=e['observation']['stages'] if isinstance(e['observation'],dict) else {s:measure() for s in STAGES}
            for s in STAGES:
                counts[s][stages[s]['state']]+=1
                metric_counts[s][stages[s]['metric']]+=1
            first=next((s for s in STAGES if stages[s]['state'] in (U,'NOT_OBSERVABLE')),None)
            if first:unknown_frontier[first]+=1
        return {'report':kind,'as_of':as_of,'experiment_count':len(experiments),'stage_counts':counts,'stage_metric_counts':{s:dict(c) for s,c in metric_counts.items()},'first_unknown_or_unobservable':dict(unknown_frontier),'attribution_counts':dict(Counter(e['attribution']['classification'] for e in experiments)),'definition':'Independent observed stage counts; NOT a claim every upstream stage was traversed. PURCHASE_READ includes separate paid and KENP observations; QUERY_PRESENCE is not customer impressions.'}
    return {'report':kind,'as_of':as_of,'experiments':experiments}

def products_title(state,product_id):
    return next(p for p in state['products'] if p['id']==product_id).get('title',product_id)

def render_cards(value):
    def brief(v):
        text=json.dumps(v,ensure_ascii=False) if not isinstance(v,str) else v
        return text.replace('|','/').replace('\n',' ')[:350]
    cards=[]
    for e in value['experiments']:
        contract=e['contract'];obs=e['observation'];plan=contract.get('plan',contract.get('fields',{})) if isinstance(contract,dict) else {}
        stage_line='; '.join(s+': '+(obs['stages'][s]['state'] if isinstance(obs,dict) else U) for s in STAGES)
        checkpoints=e['checkpoints']
        if isinstance(checkpoints,list):
            checkpoints='; '.join(c['checkpoint']+': '+c['status']+' (observation '+c['actual_observation_date']+')' for c in checkpoints)
        elif isinstance(checkpoints,dict):
            checkpoints='Plan '+('; '.join(k+': '+v['metric']+' target '+str(v['target']) for k,v in checkpoints.items()))
        if e['status']=='HISTORICAL_PARTIAL':
            plan={k:v['value'] for k,v in plan.items()}
            plan.update(buyer=plan.get('audience',U),job=plan.get('job_intent',U),hypothesis=plan.get('purchase_read_proposition',U),discovery_route=plan.get('discovery_surface',U))
        rows=[('Status',e['status']),('Hypothesis',plan.get('hypothesis',plan.get('job_intent',U))),('Buyer / job',str(plan.get('buyer',U))+' / '+str(plan.get('job',U))),('Why selected',e['selection']),('Discovery route / expected path',str(plan.get('discovery_route',plan.get('query_category',U)))+' / '+str(plan.get('expected_path',U))),('Competing alternatives',plan.get('alternatives',plan.get('competitive_set',U))),('Package / proposed price',plan.get('package_price',U)),('Cost budget',e['cost_budget']),('Checkpoints',checkpoints),('Current observed stages',stage_line),('Actuals / date',obs['observed_date']+' / '+str({k:obs['actual_outcomes'][k] for k in ('paid_units','free_units','ebook_paid','print_paid','kenp','estimated_royalties','currency')}) if isinstance(obs,dict) else U),('Attribution',e['attribution']),('Actual cost',e['actual_cost']),('Learned',e['learned'])]
        if isinstance(obs,dict):
            outcomes=obs['actual_outcomes']
            rows.insert(11,('Outcome windows',{k:outcomes[k] for k in ('paid_window','kenp_window','royalty_window','royalty_status','kenp_status')}))
        rows.insert(9,('Recorded checkpoints',e.get('checkpoint_observations',U)))
        if isinstance(contract,dict) and contract.get('waiver'):rows.insert(1,('OWNER waiver',contract['waiver']))
        cards.append('# Radar Experiment Card — '+e['id']+'\n\n'+e['title']+'\n\n| Field | Observation |\n|---|---|\n'+'\n'.join('| '+k+' | '+(v if k=='Current observed stages' else brief(v))+' |' for k,v in rows)+'\n\nSummary card; full JSON retains unabridged fields. Historical blanks are not reconstructed.\n')
    return '\n---\n\n'.join(cards)
