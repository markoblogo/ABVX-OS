#!/usr/bin/env python3
"""Build the owner-authorized Phase 1 import from retained Oct2 evidence only."""
from __future__ import annotations
import json
from datetime import date
from pathlib import Path
from abvx_harness.book_radar import load_state
from abvx_harness.book_radar_outcomes import UNKNOWN as U, evidence, funnel, classify, calibrate

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'book-radar/audits/outcome-foundation-v1'
LEDGER='book-radar/audits/decision-system-v1/BOOK_RADAR_HISTORICAL_DECISION_LEDGER_V1.json'
SNAP='book-radar/runs/kdp-decision-audit/2026-10-02/snapshot.json'
PRIMARY={'pmp-2026':'product:PMP-2026-ORIENTATION','rn2-037':'product:RN2-037','rn3-091':'product:RN3-091','rn5-001':'product:RN5-001','odyssey-tp':'product:ODYSSEY-TOKI-PONA'}
DISC={'pmp-2026':'pmp','rn2-037':'ham','rn3-091':'french-road-rules','rn5-001':'solar','odyssey-tp':'odyssey'}
TP={'meditations-tp','christmas-carol-tp','seneca-tp','dao-tp','machine-mind','epictetus-tp','cicero-tp','sunzi-art-of-war-tp','tiny-language-protocol','odyssey-tp'}
FR={'jeanne-la-bataillonneuse-miss-adrienne','la-ville-modernisme','le-maitre-navire','la-zone-sanatorium','le-voyage-leonardo'}
def read(p):return json.loads((ROOT/p).read_text())
def refs(*ps):return [evidence(ROOT,p) for p in dict.fromkeys(ps)]
def quantity_window(allrow,paidrow,freevals,period):
 return {'start':period['start'],'end':period['end'],'processed_units':allrow['values'][2], 'paid_units':paidrow['values'][2],'free_units':freevals[2],'ebook_paid':paidrow['values'][0],'print_paid':paidrow['values'][1],'evidence':refs(allrow['raw_ref'],paidrow['raw_ref'])}
def money_window(row,period):
 v=row['values'];return {'start':period['start'],'end':period['end'],'estimated_royalties':v[3],'ebook':v[0],'print':v[1],'kenp':v[2],'currency':'EUR','status':'ESTIMATE','evidence':refs(row['raw_ref'])}
def build():
 s=read(SNAP); ledger={b['book_id']:b for b in read(LEDGER)['records']}; state=load_state(ROOT)
 bundle={'schema_version':'book-radar-outcome-import/v1',**{k:[] for k in ['observed_books','actuals','portfolio_baselines','commercial_hypotheses','calibrations','products','launches']}}
 bundle['products'].append({'id':PRIMARY['odyssey-tp'],'title':ledger['odyssey-tp']['title'],'opportunity_id':None,'status':'OBSERVED_COMPARISON','source_ref':LEDGER,'radar_selection':'NOT_ASSERTED'})
 observed='2026-10-02'
 for row in s['titles']:
  k=row['book_id']; old=ledger[k]; bid='book:'+k; pid=PRIMARY.get(k,U); initial=k in PRIMARY
  oid={'pmp-2026':'PMP-2026-ORIENTATION','rn2-037':'RN2-037','rn3-091':'RN3-091','rn5-001':'RN5-001'}.get(k)
  op=next((o for o in state['opportunities'] if o['id']==oid),None)
  ds=[d['id'] for d in state['decisions'] if d['opportunity_id']==oid] if oid else []
  cohorts=[];mechanisms=[]; limitations=['Overlapping tags; unverified original-work/genre status is left unclassified.']
  if k in PRIMARY and k!='odyssey-tp':cohorts.append('RADAR_PRIMARY');mechanisms.append('REFERENCE')
  if k in TP:cohorts.append('TOKI_PONA');mechanisms.append('TOKI_PONA_NICHE')
  if k in FR:cohorts.append('OTHER_TRANSLATION');mechanisms.append('TRANSLATION');limitations.append('French translation classification retained from portfolio audit; not a rights clearance.')
  if old['public_domain_source']=='YES':mechanisms+=['PUBLIC_DOMAIN_TRANSFORMATION','TRANSLATION']
  if old['original_translation_adaptation']=='ORIGINAL':
   if 'FICTION' in old['book_type'] and 'NONFICTION' not in old['book_type']:cohorts.append('ORIGINAL_FICTION');mechanisms.append('ORIGINAL_FICTION')
   elif 'NONFICTION' in old['book_type']:cohorts.append('ORIGINAL_NONFICTION');mechanisms.append('ORIGINAL_NONFICTION')
  if old['series_or_standalone'].startswith('Good Dogs'):cohorts.append('SERIES_FICTION');mechanisms.append('SERIES_FICTION')
  dpath='book-radar/runs/discovery-audit-v1/2026-09-21/'+DISC[k]+'.json' if initial else None
  d=read(dpath) if dpath else None; date_refs=refs(dpath) if dpath else []
  asins=(d['listing'].get('asins') or {'paperback':d['listing'].get('asin',U)}) if d else old['asins'] if isinstance(old['asins'],dict) else {}
  formats=[{'id':bid+':'+fmt,'format':fmt,'asin':asin,'evidence':date_refs if d else refs(LEDGER)} for fmt,asin in asins.items() if asin and asin!=U]
  book={'schema_version':'book-radar-observed-book/v1','id':bid,'title':row['title'],'audit_book_id':k,'product_id':pid,'initial_experiment':initial,'cohorts':cohorts,'mechanisms':sorted(set(mechanisms)) or ['OTHER'],'classification_limitations':limitations,'radar_run_id':op['radar_run_id'] if op else U,'decision_ids':ds,'publication_date':d['listing']['publication_date'] if d else U,'publication_timestamp':U,'first_verified_live_date':d['observed_at'] if d else U,'date_evidence':date_refs,'formats':formats,'evidence':refs(LEDGER,SNAP)}
  bundle['observed_books'].append(book)
  unknownstage={'state':U,'evidence':[],'window':U}
  events={stage:dict(unknownstage) for stage in ['PUBLISHED','INDEXED','DISCOVERABLE']};discovery=[];categories=[]
  if d:
   for st in ('PUBLISHED','INDEXED'):events[st]={'state':'OBSERVED_POSITIVE','evidence':date_refs,'window':d['observed_at']}
   for q in d['queries']:
    raw_result=q['result'];depth=U;position=U;placement=U;result=U
    if raw_result=='NOT_FOUND':
     if 'first 16' in q.get('depth',''):depth=16
     elif k=='rn5-001':depth=2
     result='NOT_FOUND_WITHIN_DEPTH' if depth!=U else U
    if raw_result=='OBSERVED':
     result='FOUND';placement='ORGANIC';position=1
     if k=='rn3-091':depth=1
     # Odyssey source explicitly identifies first non-sponsored result;
     # its '2 of 3 overall' is not an organic depth or organic rank 2.
     events['DISCOVERABLE']={'state':'OBSERVED_POSITIVE','evidence':date_refs,'window':d['observed_at']}
    discovery.append({'observed_date':d['observed_at'],'observed_at':U,'marketplace':d['marketplace'],'query':q['query'],'surface':U,'signed_in_context':'SIGNED_OUT_COOKIE_BANNER' if k=='rn3-091' else 'SIGNED_IN_PERSONALIZED','depth_inspected':depth,'position':position,'placement':placement,'result':result,'asin':next(iter(asins.values()),U),'title_id':bid,'evidence':date_refs,'limitations':d['limitations']+['Source retained at date precision; device/time UNKNOWN; absent bounded query does not prove global undiscoverability.']})
   categories=[{'observed_date':d['observed_at'],'marketplace':d['marketplace'],'category':d['indexing']['category'],'position':U,'evidence':date_refs}]
   bundle['launches'].append({'id':'launch:observed:'+k+':2026-09-21','product_id':pid,'publication_date':book['publication_date'],'publication_timestamp':U,'first_verified_live_date':'2026-09-21','evidence':date_refs,'status_note':'Retained direct listing observation; date is not a publication timestamp; shopper availability differs by context.'})
  actual={'schema_version':'book-radar-observed-actual/v1','id':'actual:observed:'+k+':2026-10-02','book_id':bid,'product_id':pid,'observed_date':observed,'book_age_days':(date.fromisoformat(observed)-date.fromisoformat(book['publication_date'])).days if book['publication_date']!=U else U,'age_basis':'PUBLICATION_DATE' if book['publication_date']!=U else U,'checkpoint':'AD_HOC','marketplace_scope':'KDP_ACCOUNT_ALL_MARKETPLACES','windows':{'lifetime':quantity_window(row['orders_lifetime'],row['paid_lifetime'],row['free_lifetime']['values'],s['periods']['lifetime']), 'recent':quantity_window(row['orders_recent_90d'],row['paid_recent_90d'],row['free_recent_90d_derived'],s['periods']['recent_90d']), 'kenp':{'start':'2026-09-01','end':'2026-09-30','kenp_pages':row['kenp_september']['values'][0],'status':'PROVISIONAL','evidence':refs(row['kenp_september']['raw_ref'])}, 'money':money_window(row['royalties_lifetime_eur'],s['periods']['lifetime']),'recent_money':money_window(row['royalties_recent_90d_eur'],s['periods']['recent_90d'])},'instrumentation':{f:U for f in ['impressions','clicks','detail_page_visits','sample_opens','ku_starts','ad_impressions','ad_clicks','ctr','conversion']},'instrumentation_window':U,'instrumentation_evidence':[],'economics':{f:U for f in ['api_cost','other_machine_cost','owner_attention_minutes','production_elapsed_minutes','rework_minutes','paid_promotion_cost','acquisition_cost','currency']},'retailer_events':events,'discovery':discovery,'category_observations':categories,'other_discovery_evidence':date_refs,'identity_evidence':refs(LEDGER,SNAP)}
  # Include direct Free filter evidence in the lifetime units window.
  actual['windows']['lifetime']['evidence']+=refs(row['free_lifetime']['raw_ref'])
  actual['stage_applicability']={st:{'state':U,'evidence':[]} for st in ['PUBLISHED','INDEXED','DISCOVERABLE','EXPOSED','CLICKED','PURCHASED','READ']};actual['funnel']=funnel(actual);actual['classification']=classify(actual);bundle['actuals'].append(actual)
  if initial:
   keys=['audience','job_intent','discovery_surface','query_category','competitive_set','differentiation','click_reason','purchase_read_proposition','production_cost_budget','owner_attention_budget','observation_window','success_signal','failure_signal','learning_goal']
   fields={f:{'value':U,'evidence':[]} for f in keys};pre=old['prepublication_decision'];pref=refs(*pre['refs'])
   if op:
    for field,source in [('job_intent','buyer_job'),('query_category','query_cluster'),('differentiation','concept')]:
     if op.get(source):fields[field]={'value':op[source] if isinstance(op[source],(str,list)) else json.dumps(op[source],ensure_ascii=False),'evidence':pref}
    fields['competitive_set']={'value':pre['known_before'],'evidence':pref}
   prediction=pre['prediction']
   if isinstance(prediction,dict):
    fields['observation_window']={'value':'90 calendar days; retained scenario, not a calibrated probability','evidence':pref}
    if 'owner_hours_estimate' in prediction:fields['owner_attention_budget']={'value':str(prediction['owner_hours_estimate'])+' estimated owner-hours; not measured actual cost','evidence':pref}
   bundle['commercial_hypotheses'].append({'schema_version':'book-radar-commercial-hypothesis/v1','id':'hypothesis:historical:'+k,'book_id':bid,'status':'HISTORICAL_PARTIAL','decision_date':old['selection_date'] if k!='odyssey-tp' else U,'fields':fields,'hindsight_policy':'RETAINED_PREPUBLICATION_ONLY'})
   ranges=[('UNKNOWN',U)]
   if k=='rn2-037':ranges=[('initial',[20,50]),('investment',[25,60]),('production-contract',[25,60])]
   elif k=='rn3-091':ranges=[('top-five',[35,35])]
   elif k=='rn5-001':ranges=[('top-seven',[30,30])]
   for label,ran in ranges:
    claim={'id':k+':'+label,'metric':'paid_units' if ran!=U else U,'basis':'UNSPECIFIED_SALES_UNITS' if ran!=U else U,'horizon_days':90 if ran!=U else U,'range':ran,'evidence':pref,'source_kind':'RETAINED_SCENARIO_UNCALIBRATED' if ran!=U else 'NO_RETAINED_FORECAST'}
    bundle['calibrations'].append(calibrate(claim,actual,book))
 life=s['periods']['lifetime'];recent=s['periods']['recent_90d'];total=sum(a['windows']['money']['estimated_royalties'] for a in bundle['actuals']);rtotal=sum(a['windows']['recent_money']['estimated_royalties'] for a in bundle['actuals'])
 bundle['portfolio_baselines'].append({'schema_version':'book-radar-portfolio-baseline/v1','id':'baseline:kdp:2026-10-02','observed_date':observed,'title_count':34,'actual_ids':[a['id'] for a in bundle['actuals']],'currency':'EUR','totals':{'processed_units':life['orders_processed'],'paid_units':life['paid_processed'],'free_units':life['free_processed'],'ebook_paid':life['ebook_paid'],'print_paid':life['print_paid']},'royalty_reconciliation':{'headline':903.46,'aggregate_row':903.47,'sum_title_rows':round(total,2),'aggregate_minus_title_rows':round(903.47-total,2),'recent_aggregate':223.42,'recent_sum_title_rows':round(rtotal,2),'recent_difference':round(223.42-rtotal,2)},'evidence':refs(SNAP)})
 return bundle
if __name__=='__main__':
 target=OUT/'outcome-import-v1.json';bundle=build();payload=json.dumps(bundle,ensure_ascii=False,indent=2)+'\n'
 if target.exists():
  if json.loads(target.read_text())!=bundle:raise SystemExit('Refusing to rewrite existing foundation import')
 else:target.write_text(payload)
 print(json.dumps({'path':str(target),'counts':{k:len(v) for k,v in bundle.items() if isinstance(v,list)}}))
