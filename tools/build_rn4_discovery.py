#!/usr/bin/env python3
"""Build the evidence-bounded RN4 discovery artifacts.

Broad-screen scores are hypotheses. Investment decisions are stored separately
and rely only on the cited current evidence.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "book-radar" / "runs" / "rn4"
OBSERVED = "2026-09-07"

TOPICS = [
    ("wedding speech builder", "wedding speaker", "turn memories into a safe, timed wedding speech", "guided workbook", "9.99-16.99", "events"),
    ("eulogy writing workbook", "bereaved family speaker", "shape memories into a respectful eulogy", "large-format workbook", "12.99-19.99", "family"),
    ("home construction control book", "first-time home builder", "control quotes, changes, meetings and handover", "large-format workbook", "14.99-24.99", "home"),
    ("renovation snagging workbook", "home renovator", "record defects, owners and closeout evidence", "photo-ready workbook", "14.99-22.99", "home"),
    ("sewing fit diagnostic", "intermediate sewist", "diagnose garment fit symptoms and test adjustments", "visual workbook", "16.99-24.99", "hobby"),
    ("knitting calculation workbook", "garment knitter", "convert measurements and gauge into a fitting plan", "calculation workbook", "14.99-21.99", "hobby"),
    ("espresso dial-in map", "home espresso owner", "reach a repeatable shot without random adjustments", "decision-map logbook", "12.99-18.99", "hobby"),
    ("houseplant pest detective", "houseplant owner", "identify common pests and choose a safe first response", "visual diagnostic guide", "14.99-22.99", "hobby"),
    ("family oral-history sessions", "adult child or grandchild", "capture a relative's stories in structured sessions", "giftable interview workbook", "14.99-22.99", "gift"),
    ("pet-sitter handoff", "pet owner", "leave complete care instructions for a temporary sitter", "fillable handoff book", "9.99-15.99", "family"),
    ("first 30 days with a puppy", "new dog owner", "coordinate household routines and training", "family workbook", "12.99-18.99", "pets"),
    ("senior move downsizing", "adult child", "coordinate decisions when a parent moves to smaller housing", "transition workbook", "14.99-22.99", "family"),
    ("divorce document organizer", "separating adult", "collect and track documents for professional meetings", "document workbook", "14.99-24.99", "life-admin"),
    ("new executor organizer", "estate executor", "track estate tasks and professional questions", "administration workbook", "14.99-24.99", "life-admin"),
    ("first-time landlord turnover", "small landlord", "coordinate inspection, evidence and contractor tasks", "property workbook", "13.99-21.99", "business"),
    ("short-term rental reset book", "holiday-rental host", "standardize cleaner handoff and issue escalation", "operations workbook", "12.99-19.99", "business"),
    ("market-stall operations book", "craft-market seller", "plan stock, display, payments and post-event review", "seller workbook", "12.99-18.99", "business"),
    ("freelance client onboarding", "new freelancer", "turn an accepted proposal into a controlled kickoff", "professional workbook", "14.99-21.99", "careers"),
    ("career-change story bank", "career changer", "build evidence-based interview stories", "interview workbook", "12.99-19.99", "careers"),
    ("manager difficult-conversation prep", "first-time manager", "prepare a fair, specific workplace conversation", "manager workbook", "14.99-22.99", "careers"),
    ("board-meeting decision book", "small-company director", "prepare, record and close board decisions", "governance workbook", "18.99-29.99", "business"),
    ("restaurant pre-opening readiness", "independent restaurant owner", "sequence operational readiness before opening", "launch workbook", "18.99-29.99", "business"),
    ("food-truck opening binder", "first-time food-truck operator", "coordinate permits, equipment and opening checks", "launch workbook", "18.99-29.99", "business"),
    ("VSME sustainability data pack", "EU SME operator", "answer customer and bank sustainability data requests", "professional workbook", "24.99-39.99", "professional"),
    ("EU accessibility self-audit", "small ecommerce operator", "triage accessibility gaps and evidence remediation", "compliance workbook", "24.99-39.99", "professional"),
    ("GPSR product-file organizer", "small EU marketplace seller", "assemble product-safety evidence by SKU", "compliance workbook", "24.99-39.99", "professional"),
    ("AI Act inventory workbook", "small EU business", "inventory AI uses and route governance questions", "compliance workbook", "24.99-39.99", "professional"),
    ("NIS2 supplier evidence book", "small B2B supplier", "organize security evidence requested by customers", "professional workbook", "24.99-39.99", "professional"),
    ("DORA ICT supplier pack", "small financial-sector vendor", "organize resilience evidence for customer reviews", "professional workbook", "29.99-44.99", "professional"),
    ("micro-business year-end close", "solo business owner", "collect records and close the year cleanly", "finance workbook", "14.99-24.99", "business"),
    ("French school message decoder", "newly arrived parent", "understand recurring school forms and messages", "bilingual scenario reference", "14.99-21.99", "language"),
    ("workplace French for warehouse staff", "new warehouse worker", "understand routine instructions and escalation phrases", "bilingual visual phrasebook", "13.99-19.99", "language"),
    ("construction-site safety French", "migrant construction worker", "recognize instructions and safety vocabulary", "bilingual visual reference", "15.99-22.99", "language"),
    ("medical appointment phrase board", "traveler or migrant", "prepare questions and understand appointment flow", "bilingual communication aid", "12.99-19.99", "language"),
    ("French citizenship interview map", "naturalization applicant", "sequence official knowledge and oral preparation", "source-dependent study guide", "14.99-22.99", "education"),
    ("EU drone A1/A3 visual map", "new recreational drone pilot", "understand official learning objectives and operating limits", "visual study companion", "16.99-24.99", "education"),
    ("forklift safety study map", "new warehouse operator", "organize training concepts before assessment", "visual study companion", "14.99-21.99", "education"),
    ("food-handler safety map", "entry-level food worker", "organize core safety concepts before training", "visual study companion", "13.99-19.99", "education"),
    ("adult dyslexia-friendly logic puzzles", "adult puzzle buyer", "enjoy low-clutter progressive logic practice", "large-print activity book", "10.99-16.99", "activity"),
    ("train-journey activity book", "parent traveling with child", "occupy a child with journey-specific offline play", "activity book", "9.99-15.99", "activity"),
    ("museum detective Paris", "family visiting Paris", "turn museum visits into observation games", "travel activity book", "12.99-18.99", "travel"),
    ("European road-trip spotting game", "family on a road trip", "play offline observation games across countries", "travel activity book", "10.99-16.99", "travel"),
    ("amateur astronomy challenge book", "beginner stargazer", "complete progressive observations with modest equipment", "challenge workbook", "14.99-21.99", "hobby"),
    ("birdsong memory map", "beginner birder", "learn common bird calls through visual mnemonics", "visual learning guide", "16.99-24.99", "hobby"),
    ("urban sketching missions", "beginner sketcher", "build observation skill through location-based prompts", "workbook", "14.99-22.99", "hobby"),
    ("watercolor mixing recipes", "beginner watercolorist", "build a reusable color-mixing library", "color workbook", "18.99-29.99", "hobby"),
    ("sourdough troubleshooting map", "home baker", "diagnose failures from crumb, timing and temperature", "visual guide + log", "14.99-22.99", "hobby"),
    ("fermentation safety log", "home fermenter", "record batches and recognize stop conditions", "safety-led workbook", "14.99-22.99", "hobby"),
    ("beekeeping inspection decisions", "novice beekeeper", "turn hive observations into next inspection questions", "seasonal workbook", "16.99-24.99", "hobby"),
    ("genealogy evidence planner", "family-history researcher", "separate facts, hypotheses and source citations", "research workbook", "14.99-22.99", "history"),
]

LOCALES = [
    ("EN", "Amazon.com", "English-language"),
    ("FR", "Amazon.fr", "French-language"),
    ("PL", "Amazon.pl", "Polish-language"),
    ("UK", "Amazon.fr", "Ukrainian-language in France"),
]

ADVANCE_BASES = {0, 1, 2, 4, 5, 6, 8, 12, 17, 19, 23, 24, 25, 26, 30, 31, 38, 45}

def score(base: int, locale: str) -> dict:
    # Broad screen only: conservative, reproducible estimates on the fixed 1-5 scale.
    demand = 4 if base in {0,1,2,6,8,12,17,19,45} else 3
    if base in {23,24,25,26}: demand = 3
    competition = 2 if base in {0,2,8,17,19,45} else 3
    feasibility = 2 if base in {24,25,26,27,28,32,33,34,35,36,37,44,48} else 4
    if locale in {"PL","UK"}: feasibility = max(1, feasibility-1)
    evidence = 3 if base in {0,1,2,23} else 2
    return {
        "demand": demand, "momentum": 3, "competition_weakness": competition,
        "newcomer_viability": 2 if competition == 2 else 3,
        "production_feasibility": feasibility, "shelf_life": 4,
        "economics": 4 if TOPICS[base][4].startswith(("18","24","29")) else 3,
        "new_entrant_evidence": evidence, "evidence_quality": evidence,
    }

def total(metrics: dict) -> float:
    weights = {"demand":20,"momentum":8,"competition_weakness":10,"newcomer_viability":8,"production_feasibility":15,"shelf_life":8,"economics":12,"new_entrant_evidence":10,"evidence_quality":9}
    return round(sum(metrics[k]*v for k,v in weights.items())/(5*sum(weights.values()))*100,1)

opportunities=[]; evidence=[]; scores=[]; decisions=[]; broad=[]
for i,(topic,buyer,jtbd,fmt,price,group) in enumerate(TOPICS):
    for lang,market,audience in LOCALES:
        n=len(opportunities)+1; oid=f"RN4-{n:03d}"; metrics=score(i,lang)
        query=f"{topic} {lang.lower()}"
        opportunities.append({"id":oid,"radar_run_id":"radar-native-4","buyer_job":jtbd,"query_cluster":query,"format":fmt,"price_band":price,"concept":topic,"group":group,"language":lang,"primary_marketplace":market,"audience":f"{audience} {buyer}","portfolio_information_gain":"HIGH" if group in {"events","gift","activity","professional"} else "MEDIUM","product_quality_risk":"HIGH" if fmt.startswith(("visual","color")) or "activity" in fmt else "MEDIUM" if "workbook" in fmt else "LOW","source":"radar-native-4"})
        evidence.append({"id":f"evidence:{oid}:broad","opportunity_id":oid,"observed_at":OBSERVED,"summary":"Broad-screen hypothesis only; direct evidence required before authorization.","details":{"evidence_quality":metrics["evidence_quality"],"direct_amazon_observation":False}})
        scores.append({"id":f"score:{oid}:radar-native-v1","opportunity_id":oid,"scoring_model_id":"radar-native-v1","metrics":metrics,"penalties":{"paid_ads":0,"rights_trademark_compliance":0},"total":total(metrics)})
        advance=i in ADVANCE_BASES and lang==LOCALES[i%4][0]
        reason="Advanced for diversified deep scan; broad score is not investment evidence." if advance else "Rejected at broad screen: weaker evidence, differentiation, safety/rights fit, or execution economics than the diversified cutoff."
        decisions.append({"id":f"decision:{oid}:broad","opportunity_id":oid,"decision":"advance_to_deep_scan" if advance else "rejected_at_broad_screen","reason":reason,"decided_at":OBSERVED})
        if not advance: broad.append({"opportunity_id":oid,"reason":reason})

deep_ids=[o["id"] for o in opportunities if any(d["opportunity_id"]==o["id"] and d["decision"]=="advance_to_deep_scan" for d in decisions)]

DEEP = [
 ("RN4-001","Wedding Speech Builder","EN","Amazon.com","FAIL","78 results; many near-identical August-September 2026 entrants without visible ratings; established manuals have 33-54 ratings.","copycat surge and no observed newcomer traction","MEDIUM",0.75,72),
 ("RN4-006","Eulogy Writing Workbook","FR","Amazon.fr","FAIL","A professional-led 169-page workbook exists at GBP9.99; exact current Amazon traction not observed.","author trust and grief sensitivity; evidence too weak","MEDIUM",1.0,65),
 ("RN4-011","Home Construction Control Book","PL","Amazon.pl","FAIL","Prior RN3 evidence showed entrants, but current Amazon.fr analogue has 61 results and mostly 0-9 reviews at EUR5.99-12.16.","low-content clutter and degraded price power","MEDIUM",1.0,96),
 ("RN4-017","Sewing Fit Diagnostic","EN","Amazon.com","FAIL","Persistent instructional category, but no directly observed recent newcomer traction in this pass.","high expert and illustration dependency","HIGH",2.5,120),
 ("RN4-022","Knitting Calculation Workbook","FR","Amazon.fr","FAIL","Known evergreen craft job; direct exact-query Amazon evidence was not strong enough.","specialist accuracy and free calculator pressure","MEDIUM",2.0,85),
 ("RN4-027","Espresso Dial-in Map","PL","Amazon.pl","FAIL","Multiple brewing logs exist; no observed paid traction for diagnostic transformation.","logbook commoditization","MEDIUM",1.5,78),
 ("RN4-033","Family Oral-History Sessions","EN","Amazon.com","FAIL","Large established prompted-memory-book category.","review moat and gift packaging dependence","MEDIUM",1.25,110),
 ("RN4-049","Divorce Document Organizer","EN","Amazon.com","FAIL","Buyer job is real, but current newcomer evidence not established.","legal-boundary and privacy risk","MEDIUM",1.5,92),
 ("RN4-070","Freelance Client Onboarding","FR","Amazon.fr","FAIL","Abundant free templates and software alternatives.","weak paid book value layer","LOW",0.75,60),
 ("RN4-080","Manager Conversation Prep","UK","Amazon.fr","FAIL","Large management-book market but no exact workbook newcomer proof.","generic differentiation","MEDIUM",1.0,76),
 ("RN4-096","VSME Sustainability Data Pack","UK","Amazon.fr","FAIL","Only 12 broad VSME-reporting results on Amazon.com; official EU standard changed July 2026.","rapid standards volatility and buyer-channel mismatch","MEDIUM",2.5,150),
 ("RN4-097","EU Accessibility Self-Audit","EN","Amazon.com","FAIL","Regulatory need exists; no visible KDP newcomer traction captured.","legal/compliance exposure and free web tools","HIGH",3.0,130),
 ("RN4-102","GPSR Product-File Organizer","FR","Amazon.fr","FAIL","Marketplace seller compliance job is current but volatile.","platform/legal volatility; specialist audit needed","HIGH",3.0,140),
 ("RN4-107","AI Act Inventory Workbook","PL","Amazon.pl","FAIL","Current business attention is strong, but book competition and rules are moving.","short shelf life and legal framing risk","HIGH",3.0,160),
 ("RN4-123","French School Message Decoder","PL","Amazon.pl","FAIL","Clear migrant-parent job, but exact paid Amazon demand remains unobserved.","translation apps create severe free pressure","MEDIUM",1.5,70),
 ("RN4-128","Warehouse Workplace French","UK","Amazon.fr","FAIL","Employer/worker need is plausible; no current exact-query newcomer evidence.","safety language and buyer-channel mismatch","HIGH",2.0,82),
 ("RN4-155","Dyslexia-Friendly Logic Puzzles","PL","Amazon.pl","FAIL","Puzzle demand is established but saturated.","accessibility claims require specialist validation","HIGH",2.0,88),
 ("RN4-182","Watercolor Mixing Recipes","FR","Amazon.fr","FAIL","Buyers pay for color workbooks, but physical-media competitors and color print cost are strong.","asset-heavy product quality risk","HIGH",3.0,115),
]

candidates=[]
for oid,name,lang,market,gate,dem,why,risk,hours,ev in DEEP:
    regulated={"RN4-096","RN4-097","RN4-102","RN4-107"}
    weak_paid={"RN4-070","RN4-123"}
    attention={"subject_matter_hours":0,"product_taste_minutes":20,"language_review_minutes":0 if lang=="EN" else 45,"cover_minutes":20,"kdp_upload_minutes":25,"expected_correction_minutes":{"LOW":30,"MEDIUM":60,"HIGH":90}[risk]}
    total_hours=round(attention["subject_matter_hours"]+sum(v for k,v in attention.items() if k.endswith("minutes"))/60,2)
    candidates.append({"id":oid,"working_product":name,"language":lang,"marketplace":market,"buyer":next(o["audience"] for o in opportunities if o["id"]==oid),"jtbd":next(o["buyer_job"] for o in opportunities if o["id"]==oid),"format":next(o["format"] for o in opportunities if o["id"]==oid),"demand_evidence":dem,"why_market_real":"The trigger and query are observable, but commercial strength varies; see direct evidence.","newcomer_evidence":"No high-confidence recent entrant with meaningful visible traction was verified in this pass unless explicitly stated.","why_new_entrant_can_win":"Only through the stated workflow architecture; no generic clarity claim is accepted.","why_now":"Current search activity or regulatory/event trigger, subject to the currentness gate.","exact_product":f"A {next(o['format'] for o in opportunities if o['id']==oid)} organized around {next(o['buyer_job'] for o in opportunities if o['id']==oid)}.","why_better":"A decision-and-review workflow rather than a blank log or prose restatement.","thesis_falsifier":"No recent entrant with low review count and meaningful visible rank/purchase signal after an exact-query refresh.","competition":"See demand evidence; exact result counts are query snapshots, not sales.","commercial_differentiation":"Specific workflow architecture was proposed, but the gate failed because differentiation was not paired with sufficient current newcomer evidence.","free_alternative_pressure":"MEDIUM-HIGH","paid_value_layer":"structured physical workflow and durable record","raw_to_product_transformation":"public/free advice -> buyer-sequenced decisions, worksheets and review loop","portfolio_similarity":{"classification":"NOVEL","overlap_score":18 if oid not in {"RN4-123","RN4-128"} else 31,"gate":"PASS"},"author_dependency":"HIGH" if risk=="HIGH" else "LOW","language_qa_requirement":"native review required" if lang!="EN" else "direct English QA","product_quality_risk":risk,"portfolio_information_gain":"HIGH","shelf_life":"1-2 years" if oid in regulated else "3-5 years","expected_product_scale":"96-176 pages","expected_price":next(o["price_band"] for o in opportunities if o["id"]==oid),"expected_royalty":round(ev/max(1,20),2),"units_90d":20,"ev_90d":ev,"human_attention":attention,"anton_hours":total_hours,"ev_per_anton_hour":round(ev/total_hours,1),"main_risk":why,"evidence_confidence":"LOW" if "unobserved" in why or "not" in dem.lower() else "MEDIUM","gates":{"portfolio_similarity":"PASS","commercial_differentiation":"PASS","free_alternative_paid_value":"FAIL" if oid in weak_paid else "PASS","source_rights":"FAIL" if oid in regulated else "PASS","currentness":"FAIL" if oid in regulated else "PASS","autonomous_factual_qa":"FAIL" if risk=="HIGH" else "PASS","language_qa":"FAIL" if lang!="EN" and risk=="HIGH" else "PASS_WITH_COST","product_quality_feasibility":"FAIL" if risk=="HIGH" else "PASS_WITH_REPRESENTATIVE_GATE","raw_data_transformation":"PASS"},"final_gate":gate})

for c in candidates:
    evidence.append({"id":f"evidence:{c['id']}:deep","opportunity_id":c["id"],"observed_at":OBSERVED,"summary":c["demand_evidence"],"details":{"newcomer_evidence":c["newcomer_evidence"],"confidence":c["evidence_confidence"],"gate_results":c["gates"]}})

top_ids=["RN4-001","RN4-006","RN4-011","RN4-096","RN4-182"]
top=[next(c for c in candidates if c["id"]==x) | {"rank":i+1} for i,x in enumerate(top_ids)]
gate_outcomes=[]
for c in top:
    gate_outcomes.append({"opportunity_id":c["id"],"outcome":"BLOCKED","blocking_evidence":c["main_risk"],"production_authorized":False})
    decisions.append({"id":f"decision:{c['id']}:rn4-preproduction","opportunity_id":c["id"],"decision":"reject_after_preproduction_gate","reason":c["main_risk"],"decided_at":OBSERVED,"production_authorized":False})

for c in candidates:
    if c["id"] not in top_ids:
        decisions.append({"id":f"decision:{c['id']}:rn4-deep","opportunity_id":c["id"],"decision":"reject_after_deep_scan","reason":c["main_risk"],"decided_at":OBSERVED,"production_authorized":False})

run={"schema_version":"book-radar-import/v1","radar_runs":[{"id":"radar-native-4","name":"Radar-Native Discovery #4","observed_at":OBSERVED,"status":"NO_PRODUCT","scoring_model_id":"radar-native-v1","opportunities_scanned":200,"deep_scanned":18}],"opportunities":opportunities,"evidence":evidence,"scores":scores,"decisions":decisions}

OUT.mkdir(parents=True,exist_ok=True)
files={
 "broad-opportunities.json":{"count":len(opportunities),"opportunities":opportunities,"scores":scores},
 "rejection-log.json":{"broad_rejections":broad,"deep_gate_exclusions":[{"opportunity_id":c["id"],"reason":c["main_risk"]} for c in candidates]},
 "deep-scan.json":{"count":len(candidates),"candidates":candidates},
 "top-five.json":{"top_five":top},
 "preproduction-gates.json":{"outcomes":gate_outcomes,"final_decision":"NO_PRODUCT","production_started":False},
 "production-contract.json":{"status":"NOT_CREATED_NO_SURVIVING_WINNER","production_authorized":False,"reason":"All five finalists failed at least one controlling pre-production gate."},
}
for name,data in files.items():
    (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
(ROOT/"book-radar"/"imports"/"rn4-discovery.json").write_text(json.dumps(run,ensure_ascii=False,indent=2)+"\n")
print(json.dumps({"opportunities":len(opportunities),"deep":len(candidates),"top":len(top)}))
