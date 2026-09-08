#!/usr/bin/env python3
"""Reconcile RN4-RN6 funnel history and emit candidate-generation-v2."""
from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'book-radar/audits'; OUT.mkdir(parents=True,exist_ok=True)
STRATEGIES=ROOT/'book-radar/strategies'; STRATEGIES.mkdir(parents=True,exist_ok=True)

RUNS={
 'RN4':{'broad':200,'deep':18,'finalists':5,'gates_tested':5,'gate_pass':0,'authorized':0,'human_required':0,'human_pass':0},
 'RN5':{'broad':280,'deep':24,'finalists':7,'gates_tested':1,'gate_pass':1,'authorized':1,'human_required':1,'human_pass':1},
 'RN6':{'broad':330,'deep':27,'finalists':10,'gates_tested':10,'gate_pass':0,'authorized':0,'human_required':0,'human_pass':0},
}
PRIMARY_LATE_REJECTIONS={
 'DEMAND_TOO_WEAK':1,
 'NEWCOMER_EVIDENCE_TOO_WEAK':1,
 'SATURATION':2,
 'FREE_ALTERNATIVE_TOO_STRONG':0,
 'DIFFERENTIATION_TOO_WEAK':2,
 'BOOK_FORMAT_FIT_WEAK':0,
 'PAID_VALUE_TOO_WEAK':1,
 'AUTHOR_DEPENDENCY_TOO_HIGH':3,
 'RIGHTS/SOURCE_RISK':0,
 'VOLATILITY':2,
 'PORTFOLIO_OVERLAP':0,
 'PRODUCT_QUALITY_RISK':3,
 'FORMAT_ELIGIBILITY':0,
 'OTHER':0,
}

def rate(n,d): return round(100*n/d+1e-9,1) if d else None

def main():
 totals={k:sum(v[k] for v in RUNS.values()) for k in next(iter(RUNS.values()))}
 per_run={}
 for run,v in RUNS.items():
  per_run[run]={**v,'broad_to_deep_pct':rate(v['deep'],v['broad']),'deep_to_finalist_pct':rate(v['finalists'],v['deep']),'finalist_to_gate_pass_pct':rate(v['gate_pass'],v['finalists']),'tested_gate_pass_pct':rate(v['gate_pass'],v['gates_tested']),'gate_pass_to_authorization_pct':rate(v['authorized'],v['gate_pass']),'authorization_to_human_pass_pct':rate(v['human_pass'],v['human_required'])}
 rejected=sum(PRIMARY_LATE_REJECTIONS.values())
 reasons={k:{'count':v,'proportion_pct':rate(v,rejected)} for k,v in PRIMARY_LATE_REJECTIONS.items()}
 audit={
  'schema_version':'discovery-effectiveness-audit/v1','scope':['RN4','RN5','RN6'],
  'source_of_truth':['book-radar/runs/rn4','book-radar/runs/rn5','book-radar/runs/rn6','RN5 human gate and production records'],
  'data_quality':{
   'status':'PASS_WITH_LIMITATIONS',
   'limitations':['RN5 stopped investment testing after the rank-1 survivor, so six finalists are neither passes nor rejections.','RN4 broad rejection reasons are aggregated rather than candidate-specific.','Discovery source was not persisted per candidate; source-type conversion cannot be measured reliably.','Positive cases are calibration examples, not a statistically representative sample.'],
  },
  'per_run':per_run,'totals':{**totals,'broad_to_deep_pct':rate(totals['deep'],totals['broad']),'deep_to_finalist_pct':rate(totals['finalists'],totals['deep']),'finalist_to_authorization_pct':rate(totals['authorized'],totals['finalists']),'tested_gate_pass_pct':rate(totals['gate_pass'],totals['gates_tested'])},
  'late_rejections':{'denominator':rejected,'method':'one primary reason per blocked finalist; RN5 untested finalists excluded','categories':reasons},
  'weakness_location':{'classification':'MIXED','primary':'DEEP_PROMOTION_AND_FINAL_RANKING','evidence':'RN6 promoted ten candidates despite weak direct purchase-intent/newcomer evidence already visible for several; final gates nevertheless correctly caught author, quality and volatility risks that were not cheap-screenable.'},
  'experimental_signal_findings':{
   'purchase_trigger_strength':'USEFUL','value_of_solving':'USEFUL','time_to_need':'USEFUL','book_purchase_naturalness':'USEFUL','wtp_proxy_strength':'USEFUL','commercial_intent_confidence':'USEFUL',
   'basis':'RN1/RN2 have explicit exam triggers; RN3 has immediate cross-system navigation; RN5 has a high-value contract decision. RN6 curiosity/ongoing-interest candidates lacked equivalent purchase evidence despite plausible JTBDs.'
  },
  'positive_case_archetypes':['credential/exam decision','credential/exam performance','cross-system practical transition','high-value purchase decision'],
  'architecture_finding':'No evidence of RN5 decoder overfit in RN6 Top 10; none used DATA_TO_DECISION. Architecture frequency alone did not predict authorization.',
  'language_finding':'Multilingual search adds real cross-system asymmetry (RN3), but also volume and format/language QA friction. Preserve coverage and gate eligibility early.',
  'source_effectiveness':'INCONCLUSIVE quantitatively because item-level origin was not stored. Qualitatively, external/community discovery found problems while Amazon evidence killed weak paid-book theses; persist source_origin in future runs.',
  'conclusion':'MINOR_GENERATION_CALIBRATION_JUSTIFIED',
  'recommended_change':'Record and use six experimental commercial-intent signals plus source_origin for generation and promotion; preserve 25% exploratory candidates; do not alter permanent scoring weights or historical records.'
 }
 (OUT/'discovery-effectiveness-rn4-rn6-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
 md=f'''# Discovery Effectiveness Audit: RN4–RN6\n\n## Decision\n\n**MINOR GENERATION CALIBRATION JUSTIFIED.** The rejection gates are doing useful work, but RN6 promoted several interesting, architecturally attractive ideas after weak purchase-intent and newcomer evidence was already visible. The correction belongs in generation and early promotion—not in additional hard gates.\n\n## Reconciled funnel\n\n- Broad → deep: **69 / 810 (8.5%)**\n- Deep → finalist: **22 / 69 (31.9%)**\n- Finalist → authorization: **1 / 22 (4.5%)**\n- Actually tested final gates → pass: **1 / 16 (6.3%)**\n- Gate pass → production authorization: **1 / 1**\n- Required human product gate → pass: **1 / 1**\n\nRN5's six lower-ranked finalists were not tested after RN5-001 survived. They are excluded from late-rejection counts rather than silently treated as failures.\n\n## Primary late rejection reasons\n\nAcross 15 blocked finalists: author dependency 3 (20.0%); product-quality risk 3 (20.0%); saturation 2 (13.3%); differentiation 2 (13.3%); volatility 2 (13.3%); demand, newcomer evidence and paid value 1 each (6.7% each). Zero as a *primary* reason does not mean a factor was absent; only one principal cause was assigned per finalist.\n\n## Where weakness enters\n\nThe answer is **mixed, concentrated at deep promotion and final ranking**. RN6's First Swim Meet, Pétanque and Quilting concepts reached Top 10 despite weak direct purchase-intent/newcomer proof. Conversely, author dependency, image-production burden and standards volatility often needed final investigation. The investment gates should remain intact.\n\n## Positive-case comparison\n\nThe four calibration successes do not share one architecture. They do share an identifiable purchase occasion and a natural book-shaped job: PMP and Ham have exam triggers; RN3 serves an immediate cross-system transition; RN5 supports a consequential contract decision. Their value mechanism was visible before production. Several RN6 finalists had a plausible recurring problem but only curiosity/community evidence, with no observed willingness to buy the proposed product.\n\n## Signals\n\nPurchase trigger, value of solving, time-to-need, book-purchase naturalness and willingness-to-pay proxies are all useful **experimental** signals. They should improve promotion precision, but must not become hard gates or silently change the permanent score.\n\nDiscovery-source effectiveness is quantitatively **inconclusive** because RN4–RN6 did not persist item-level source origin. Qualitatively, community/external discovery found real problems while Amazon frequently disproved the paid-book thesis. RN7 should persist origin.\n\n## Calibration\n\nUse `candidate-generation-v2`: 75% commercial-intent generation, 25% exploratory weak-prior generation; persist six experimental signals and evidence labels; use them for early ranking and tie-breaking only. Preserve all languages, all existing gates, the scoring model, and historical records.\n'''
 (OUT/'discovery-effectiveness-rn4-rn6-audit.md').write_text(md)
 strategy={
  'schema_version':'candidate-generation-strategy/v2','id':'candidate-generation-v2','status':'ACTIVE_EXPERIMENT','effective_from_run':'RN7',
  'previous_behavior':'Generated primarily from plausible underserved buyer jobs and architecture diversity; commercial intent was assessed inconsistently and source origin was not persisted.',
  'audit_evidence_ref':'book-radar/audits/discovery-effectiveness-rn4-rn6-audit.json',
  'mix':{'commercial_intent_oriented_target_pct':75,'exploratory_weak_prior_target_pct':25,'hard_quota':False},
  'required_generation_questions':['who needs this','what happened that creates need now','current workaround','why workaround is unsatisfactory','why a book is natural','what evidence suggests paid behavior','what is the raw-to-product transformation'],
  'experimental_fields':{
   'purchase_trigger_strength':{'scale':[0,5],'use':['generation','promotion','tie_breaking']},
   'value_of_solving':{'scale':[0,5],'use':['generation','promotion','tie_breaking']},
   'time_to_need':{'values':['NOW_DAYS','WEEKS','ONGOING','SOMEDAY_CURIOSITY','UNKNOWN'],'use':['promotion','analysis']},
   'book_purchase_naturalness':{'scale':[0,5],'use':['generation','promotion','tie_breaking']},
   'wtp_proxy_strength':{'scale':[0,5],'use':['generation','promotion','tie_breaking']},
   'commercial_intent_confidence':{'scale':[0,5],'use':['promotion','analysis']},
   'source_origin':{'values':['AMAZON_FIRST','COMMUNITY_REDDIT','OFFICIAL_COMPLEXITY','SEARCH_QUERY','COMPETITOR_ADJACENCY','REGULATORY_CHANGE','MARKETPLACE_GAP','LANGUAGE_ARBITRAGE','PORTFOLIO_ASSET_DERIVATION','OTHER'],'use':['analysis']},
  },
  'explicit_non_changes':['permanent scoring weights unchanged','existing hard gates unchanged','historical RN4-RN6 records unchanged','language coverage unchanged','NO_PRODUCT remains valid','low-trigger evergreen hobby/reference candidates remain eligible through exploratory path'],
 }
 (STRATEGIES/'candidate-generation-v2.json').write_text(json.dumps(strategy,indent=2)+'\n')
 print(json.dumps({'status':'COMPLETE','conclusion':audit['conclusion'],'totals':audit['totals']},indent=2))

if __name__=='__main__': main()
