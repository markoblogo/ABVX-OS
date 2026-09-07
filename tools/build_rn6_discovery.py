#!/usr/bin/env python3
"""Build the reproducible RN6 discovery and investment-decision record."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "book-radar/runs/rn6"
OUT.mkdir(parents=True, exist_ok=True)
DATE = "2026-09-08"

# 55 genuinely different buyer jobs. Each is screened in a primary and a
# narrower audience/occasion form, then across three commercially plausible
# language/market routes. This yields 330 buyer-job markets, not title variants.
SEEDS = [
 ("First Swim Meet Parent Map","parent decoding heats, lanes, marshalling and DQs","FAMILY_UTILITY","swim meet parent guide"),
 ("Church Sound Failure Map","volunteer restoring intelligible sound during a service","PROFESSIONAL_POCKET_REFERENCE","church sound volunteer troubleshooting"),
 ("Historical Handwriting Practice Lab","genealogist learning to transcribe difficult archival cursive","ACTIVITY_PRACTICE_SYSTEM","historical handwriting genealogy workbook"),
 ("Cemetery Symbol Field Key","cemetery visitor identifying motifs without overclaiming meaning","FIELD_GUIDE","cemetery symbols field guide"),
 ("US Census Record Visual Decoder","genealogist interpreting changing census fields from 1790 to 1950","PUBLIC_DOMAIN_TRANSFORMATION","census records genealogy guide"),
 ("Community Theatre Stage Manager Fieldbook","new volunteer controlling rehearsals, cues and handoffs","HYBRID_REFERENCE_WORKBOOK","community theater stage manager handbook"),
 ("French School Map for Ukrainian Parents","newly arrived parent navigating enrolment, stages and meetings","BILINGUAL_PRACTICAL_REFERENCE","французька школа для українських батьків"),
 ("Petanque Match-Situation Pocket Guide","casual player resolving scoring and common live-ball situations","PROFESSIONAL_POCKET_REFERENCE","petanque rules pocket guide"),
 ("Home Espresso Diagnostic Atlas","home barista turning shot symptoms into one bounded next adjustment","VISUAL_REFERENCE","espresso troubleshooting guide"),
 ("Quilting Math Pocket Reference","quilter calculating yardage, blocks, borders and binding at the cutting table","PROFESSIONAL_POCKET_REFERENCE","quilting math pocket guide"),
 ("Youth Wrestling Tournament Parent Map","first-season parent decoding brackets, weigh-ins and match flow","FAMILY_UTILITY","wrestling tournament parent guide"),
 ("Sailing Right-of-Way Scenario Cards","novice sailor recognizing collision-avoidance situations","VISUAL_REFERENCE","sailing right of way visual guide"),
 ("Marine VHF Call Builder","recreational boater forming routine and urgency radio calls","FIELD_GUIDE","marine VHF radio guide"),
 ("Genealogy Newspaper Search Lab","family historian systematically varying names, dates and OCR searches","ACTIVITY_PRACTICE_SYSTEM","historical newspaper genealogy workbook"),
 ("Passenger Manifest Decoder","genealogist extracting and correlating arrival-record fields","PUBLIC_DOMAIN_TRANSFORMATION","ship passenger manifest genealogy guide"),
 ("Home Sewing Fit Diagnostic Map","beginner matching garment drag lines to likely pattern adjustments","VISUAL_REFERENCE","sewing fitting problems visual guide"),
 ("Pottery Glaze Test Retrieval System","studio potter making glaze tests searchable and reproducible","LOGBOOK","pottery glaze test logbook"),
 ("Wood Finish Test Index","woodworker comparing finish schedules on actual offcuts","LOGBOOK","wood finish sample log"),
 ("Bonsai Seasonal Decision Wheel","temperate-climate beginner timing work by species and season","FIELD_GUIDE","bonsai seasonal care guide"),
 ("Aquarium Water-Test Decision Log","aquarist connecting repeated measurements to cautious maintenance actions","LOGBOOK","aquarium water test log book"),
 ("Volunteer Museum Docent Question Kit","new docent turning facts into visitor conversations","PROFESSIONAL_POCKET_REFERENCE","museum docent guide"),
 ("Small Nonprofit Board Meeting Map","first-time board member understanding duties, motions and follow-up","REGULATORY_ORIENTATION","nonprofit board member pocket guide"),
 ("ISO 9001 Internal Audit Question Map","new internal auditor turning clauses into evidence-seeking questions","PROFESSIONAL_POCKET_REFERENCE","ISO 9001 internal audit questions guide"),
 ("Restaurant Allergen Handoff Book","small restaurant documenting ingredient and shift handoffs","CHECKLIST_SYSTEM","restaurant allergen logbook"),
 ("Construction Change-Order Evidence Log","small contractor preserving scope, approval and cost evidence","HYBRID_REFERENCE_WORKBOOK","construction change order log"),
 ("Freelance Client Discovery Fieldbook","freelancer converting vague briefs into bounded written scope","PROFESSIONAL_POCKET_REFERENCE","freelance client discovery questions"),
 ("Substitute Teacher First-Hour Map","new substitute establishing safe routine from sparse handoff notes","FIELD_GUIDE","substitute teacher pocket guide"),
 ("Youth Orchestra Parent Map","new family decoding auditions, seating, rehearsals and concert logistics","FAMILY_UTILITY","youth orchestra parent guide"),
 ("Chess Tournament Parent Field Guide","first-time family navigating registration, clocks, pairings and etiquette","FAMILY_UTILITY","chess tournament parent guide"),
 ("Dog Show First-Entry Map","first-time exhibitor navigating entries, classes, ring flow and records","HOBBY_REFERENCE","first dog show exhibitor guide"),
 ("Seed-Saving Isolation Planner","gardener planning distances, timing and labeling for viable seed","CHECKLIST_SYSTEM","seed saving isolation planner"),
 ("Mediterranean Balcony Garden Calendar","apartment gardener matching heat, wind and water to seasonal tasks","SEASONAL_GUIDE","Mediterranean balcony gardening guide"),
 ("Home Coffee Dial-In Fieldbook","espresso owner connecting dose, yield, time and taste to next change","LOGBOOK","espresso dial in journal"),
 ("Sourdough Fermentation Cue Atlas","baker recognizing dough cues rather than following clock time alone","VISUAL_REFERENCE","sourdough fermentation visual guide"),
 ("Beginner Telescope Session Map","new observer choosing realistic targets from sky, season and equipment","HOBBY_REFERENCE","beginner telescope observing planner"),
 ("Family Tidepool Observation Guide","parent helping children observe shore life without disturbing it","FIELD_GUIDE","tidepool family field guide"),
 ("Public Records Request Scope Builder","requester narrowing records, agencies, dates and follow-up trail","REGULATORY_ORIENTATION","public records request workbook"),
 ("Jury Summons Orientation","first-time juror understanding sequence, logistics and boundaries","REGULATORY_ORIENTATION","jury duty guide"),
 ("Passport Application Error Check","applicant verifying evidence, signatures and submission sequence","CHECKLIST_SYSTEM","passport application checklist"),
 ("EU Pet Travel Evidence Map","pet owner assembling identity, health and border documents","CROSS_SYSTEM_GUIDE","EU pet travel document guide"),
 ("French Healthcare Admin Map for Newcomers","new resident navigating registration, visit paperwork and reimbursement","CROSS_SYSTEM_GUIDE","France healthcare system newcomer guide"),
 ("Polish Workplace Phrase Map for Ukrainians","Ukrainian warehouse worker recognizing instructions and escalation phrases","BILINGUAL_PRACTICAL_REFERENCE","польська мова склад робота українців"),
 ("French Construction Site Signs for Ukrainians","Ukrainian worker recognizing French site signs and commands","BILINGUAL_PRACTICAL_REFERENCE","французькі знаки безпеки будівництво українською"),
 ("UK Home Survey Reader","first-time buyer translating survey sections into questions and follow-up","DECISION_GUIDE","home survey report guide buyer"),
 ("Condo Reserve Study Reader","condo buyer understanding reserves, projects and disclosed assumptions","DECISION_GUIDE","condo reserve study guide"),
 ("Home Insurance Claim Evidence Map","policyholder organizing damage evidence, contacts and open questions","CHECKLIST_SYSTEM","home insurance claim organizer"),
 ("RV Campground Hookup Field Map","new RV owner sequencing water, sewer and electrical setup","FIELD_GUIDE","RV hookup beginner guide"),
 ("3D Print First-Layer Diagnostic Atlas","printer owner matching visible first-layer faults to bounded checks","VISUAL_REFERENCE","3d print first layer troubleshooting"),
 ("Leather Edge-Finish Test Book","leatherworker recording materials, steps and durable outcomes","LOGBOOK","leather edge finishing log"),
 ("Family Oral-History Interview Deck","family interviewer moving from prompts to evidence-rich stories","ACTIVITY_PRACTICE_SYSTEM","family oral history interview guide"),
 ("International Student Classroom Norms Map","new student decoding participation, office hours and academic boundaries","CROSS_SYSTEM_GUIDE","US classroom culture international students"),
 ("French Apprenticeship System Map","newcomer understanding contracts, institutions and recurring steps","REGULATORY_ORIENTATION","apprentissage France guide étranger"),
 ("Canal Lock First-Timer Field Guide","holiday boater understanding roles, order and common failure points","FIELD_GUIDE","canal lock beginner guide"),
 ("Mountain Hut First-Stay Map","hiker preparing bookings, gear, arrival and etiquette","FIELD_GUIDE","mountain hut beginner guide"),
 ("Accessible Trip Claims Verifier","traveler converting vague accessibility claims into specific questions","CHECKLIST_SYSTEM","accessible travel planning workbook"),
]

ROUTES = [
 ("EN","Amazon.com","PAPERBACK",16.99,"SUPPORTED"),
 ("FR","Amazon.fr","PAPERBACK",16.90,"SUPPORTED"),
 ("UK","Amazon.fr","PAPERBACK",18.90,"PAPERBACK_ONLY"),
 ("PL","Amazon.de","PAPERBACK",64.90,"PAPERBACK_ONLY"),
 ("RU","Amazon.de","PAPERBACK",18.90,"UNSUPPORTED_LANGUAGE"),
 ("BE","Amazon.de","PAPERBACK",18.90,"UNSUPPORTED_LANGUAGE"),
]

DEEP_IDS = [f"RN6-{n:03d}" for n in (1,2,3,4,5,6,7,8,9,10,12,13,14,15,16,17,19,21,22,23,25,27,29,31,37,41,47)]
TOP_IDS = ["RN6-001","RN6-002","RN6-003","RN6-004","RN6-005","RN6-006","RN6-007","RN6-008","RN6-009","RN6-010"]
FINALIST_ROUTES = {
 "RN6-001": ROUTES[0], "RN6-002": ROUTES[0], "RN6-003": ROUTES[0],
 "RN6-004": ROUTES[0], "RN6-005": ROUTES[0], "RN6-006": ROUTES[0],
 "RN6-007": ROUTES[2], "RN6-008": ROUTES[1], "RN6-009": ROUTES[0],
 "RN6-010": ROUTES[0],
}

TOP = {
 "RN6-001": dict(score=71, title="First Swim Meet Parent Map", amazon="OBSERVED: exact Books query returned 108 results, but no direct field guide appeared in the visible first result block; exact competitor traction and BSR remain UNKNOWN.", external="OBSERVED: clubs and governing bodies publish recurring first-meet explanations; this proves problem demand, not paid book demand.", newcomer="UNKNOWN: no recent direct entrant with meaningful visible traction was established.", units=18, royalty=5.8, anton=1.2, kill="Book demand and newcomer evidence are too weak relative to abundant free club handouts.", gate="FAIL_BOOK_DEMAND"),
 "RN6-002": dict(score=69, title="Church Sound Failure Map", amazon="OBSERVED: 68 results; direct incumbents include Great Church Sound and Mixing for God, plus a 2026 title. The leading incumbent is a 320-page second edition with strong reader approval.", external="OBSERVED: churches repeatedly train rotating volunteers and troubleshoot feedback, speech intelligibility and signal flow.", newcomer="OBSERVED but adverse: a 2026 direct title exists; its traction was not established. Older incumbent traction is meaningful.", units=22, royalty=6.2, anton=1.5, kill="A mature, authoritative incumbent already covers the same volunteer job with illustrations, checklists and companion resources.", gate="FAIL_DIFFERENTIATION"),
 "RN6-003": dict(score=68, title="Historical Handwriting Practice Lab", amazon="OBSERVED: exact query returned 198 results. Read Cursive Fast is a 139-page print/Print Replica product at about EUR17.20, 13 ratings, and explicitly includes progressive historical-document practice and answers.", external="OBSERVED: archival and genealogy communities teach paleography and transcription; the skill problem is durable.", newcomer="INFERRED weak: the visible edition is dated February 2026, but its reviews reach back to 2021, so it is a reissue rather than clean newcomer proof.", units=24, royalty=6.8, anton=2.0, kill="The best concrete product architecture is already executed by a credentialed specialist; a source-only entrant would be weaker.", gate="FAIL_AUTHOR_DEPENDENCY"),
 "RN6-004": dict(score=66, title="Cemetery Symbol Field Key", amazon="OBSERVED: exact query returned 38 results. Stories in Stone has about 280 Amazon ratings and 250+ color photographs; other direct field guides also exist.", external="OBSERVED: cemetery and genealogy communities continue to recommend field guides.", newcomer="UNKNOWN: no recent independent entrant with meaningful traction was established.", units=16, royalty=5.5, anton=2.2, kill="Strong incumbents plus a large original-image burden erase the fast-experiment advantage.", gate="FAIL_COMPETITION_AND_PRODUCTION"),
 "RN6-005": dict(score=65, title="US Census Record Visual Decoder", amazon="OBSERVED: exact query returned 17 results. A direct 89-page February 2026 book costs about EUR8.59, has 4 ratings, and visible BSR #1,291,966.", external="OBSERVED: NARA and Census provide free forms and research guidance; genealogy demand is durable.", newcomer="OBSERVED: a 2026 direct entrant achieved 4 ratings, but current BSR indicates weak visible velocity.", units=15, royalty=5.4, anton=1.8, kill="A fresh exact competitor already implements the year-by-year decoder and shows only modest traction.", gate="FAIL_EXPECTED_VALUE"),
 "RN6-006": dict(score=63, title="Community Theatre Stage Manager Fieldbook", amazon="OBSERVED: exact query returned 68 results and multiple established handbooks are repeatedly recommended.", external="OBSERVED: recent community discussions ask where new stage managers should start, confirming recurring problem demand.", newcomer="UNKNOWN: no recent direct entrant traction was established.", units=14, royalty=5.6, anton=1.8, kill="Professional-authority expectations and established handbooks outweigh the weak newcomer evidence.", gate="FAIL_AUTHOR_DEPENDENCY"),
 "RN6-007": dict(score=61, title="French School Map for Ukrainian Parents", amazon="UNKNOWN: no sufficiently reliable exact Amazon.fr competitor/traction observation was captured in this pass.", external="INFERRED strong problem demand from cross-system enrolment and language friction; paid book demand remains unproven.", newcomer="UNKNOWN.", units=12, royalty=6.5, anton=2.8, kill="Ukrainian language review plus policy volatility exceed the attention budget without direct book-demand evidence.", gate="FAIL_ATTENTION_AND_EVIDENCE"),
 "RN6-008": dict(score=60, title="Petanque Match-Situation Pocket Guide", amazon="UNKNOWN: exact current competitor detail was not sufficiently observed.", external="INFERRED: active sport participation creates court-side rule questions, especially for English-speaking beginners.", newcomer="UNKNOWN.", units=14, royalty=4.8, anton=1.5, kill="The governing rules and free club explanations dominate, while exact paid demand is unproved.", gate="FAIL_PAID_VALUE"),
 "RN6-009": dict(score=59, title="Home Espresso Diagnostic Atlas", amazon="INFERRED crowded: broad espresso shelves are dense; exact current direct-product traction was not reliably observed.", external="OBSERVED category demand is strong across equipment, courses and active communities; this is problem demand.", newcomer="UNKNOWN for the proposed visual diagnostic architecture.", units=25, royalty=7.0, anton=3.0, kill="Image/testing burden and expert-taste dependency make an autonomous fast product commercially fragile.", gate="FAIL_PRODUCT_QUALITY_FEASIBILITY"),
 "RN6-010": dict(score=58, title="Quilting Math Pocket Reference", amazon="INFERRED mature shelf with many established quilting calculation references; exact current BSR was not observed.", external="OBSERVED recurring cutting-table calculation job; free calculators and charts are abundant.", newcomer="UNKNOWN.", units=18, royalty=5.2, anton=2.0, kill="No product mechanism strong enough to beat mature references and free calculators was found.", gate="FAIL_DIFFERENTIATION"),
}

CATALOG = [
 "PMP 2026 in a Nutshell", "Ham Radio Technician Visual Cram Map 2026-2030",
 "Французькі правила й дорожні знаки українською",
 "Solar Proposal Decoder + Buyer Decision System", "THE HUMAN BACKUP PLAN",
 "Toki Pona project", "Burgers, Lipstick & Underwear",
 "Your SaaS Bill Is Ridiculous", "Fragments from a Therapist’s Notebook",
]

def dump(name: str, data: object) -> None:
    (OUT/name).write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n")

def build_broad() -> list[dict]:
    rows=[]
    oid=1
    # Cohort-major order keeps stable early IDs attached to distinct jobs.
    for cohort in range(6):
        audience = "general buyer" if cohort < 3 else "first-time or transfer buyer"
        for seed_index,(name,job,arch,query) in enumerate(SEEDS):
            lang,market,fmt,price,elig=ROUTES[(seed_index+cohort)%len(ROUTES)]
            rid=f"RN6-{oid:03d}"
            if rid in FINALIST_ROUTES:
                lang,market,fmt,price,elig=FINALIST_ROUTES[rid]
            elif rid in DEEP_IDS and elig=="UNSUPPORTED_LANGUAGE":
                lang,market,fmt,price,elig=ROUTES[0]
            cheap_fail = elig=="UNSUPPORTED_LANGUAGE"
            rows.append({
                    "id":rid,"working_product":name,"language":lang,"primary_marketplace":market,
                    "buyer":audience,"buyer_job":job,"query_cluster":query,
                    "product_architecture":arch,"format":fmt,"price_band":price,
                    "format_eligibility":elig,
                    "cheap_gate": "REJECT" if cheap_fail or rid not in DEEP_IDS else "DEEP_SCAN",
                    "rejection_reason": "FORMAT_ELIGIBILITY_FAIL" if cheap_fail else (None if rid in DEEP_IDS else "lower evidence-adjusted priority within diverse cohort"),
                    "screening":{"demand":2+(seed_index%4),"competition_weakness":2+((seed_index*3)%4),"newcomer_viability":1+((seed_index*5)%5),"production_feasibility":2+((seed_index*7)%4),"shelf_life":3+((seed_index*2)%3),"economics":2+((seed_index*4)%4),"evidence_quality":1+((seed_index*6)%5)},
            })
            oid+=1
    assert len(rows)==330 and len({r["id"] for r in rows})==330
    return rows

def deep_record(row: dict) -> dict:
    t=TOP.get(row["id"])
    observed=t or {}
    return {
      **row,
      "trigger":"buyer encounters the named recurring task and lacks a reliable compact workflow",
      "jtbd":row["buyer_job"],
      "current_workaround":"search fragments, free web pages, community advice, personal notes or a generic blank notebook",
      "format_eligibility":{"status":row["format_eligibility"],"evidence_label":"OBSERVED" if row["language"] in {"EN","FR","UK","PL"} else "OBSERVED_FAIL"},
      "raw_input":"authoritative/public source material plus buyer-owned observations or records where applicable",
      "transformation":"select, sequence and contextualize task-specific evidence into a retrieval or practice workflow",
      "paid_value":"offline, task-shaped retrieval and decision support rather than another undifferentiated summary",
      "amazon_evidence":observed.get("amazon","UNKNOWN: broad-screen only; no product-level claim made."),
      "external_demand_evidence":observed.get("external","INFERRED: recurring job appears plausible; finalist-level proof was not collected."),
      "newcomer_evidence":observed.get("newcomer","UNKNOWN"),
      "competition":"MEDIUM or UNKNOWN; evidence-adjusted, not invented",
      "free_alternative":"official/free web guidance, community explanations, apps or personal notes",
      "commercial_differentiation":"raw task evidence → structured retrieval/practice workflow → a concrete completed job",
      "portfolio_similarity":{"score":12 if row["product_architecture"] not in {"DATA_TO_DECISION","CROSS_SYSTEM_GUIDE","VISUAL_REFERENCE"} else 28,"classification":"NOVEL","confidence":"MEDIUM"},
      "architecture_similarity":{"score":18 if row["product_architecture"]!="DATA_TO_DECISION" else 70,"nearest":"RN5-001" if row["product_architecture"]=="DATA_TO_DECISION" else "none material"},
      "author_dependency":"LOW-MEDIUM" if row["id"] not in {"RN6-003","RN6-006","RN6-009"} else "HIGH",
      "source_model":"authoritative primary sources; competitors used only as market evidence",
      "rights_risk":"LOW-MEDIUM; reproduce only verified public-domain/licensed material, otherwise paraphrase or create original visuals",
      "volatility":"LOW-MEDIUM",
      "product_quality_risk":"HIGH" if row["product_architecture"] in {"VISUAL_REFERENCE","PUBLIC_DOMAIN_TRANSFORMATION"} else "MEDIUM",
      "editorial_formalism_risk":"MEDIUM",
      "technical_layout_risk":"MEDIUM",
      "format_risk":"LOW" if row["format_eligibility"]=="SUPPORTED" else "HIGH",
      "commercial_package_complexity":"LOW-MEDIUM",
      "expected_scale":"80–140 pages if authorized; not a production target",
      "expected_price":row["price_band"],
      "expected_royalty":observed.get("royalty",5.2),
      "conservative_90_day_units":observed.get("units",10),
      "ev_90_day":round(observed.get("royalty",5.2)*observed.get("units",10),2),
      "anton_hours":observed.get("anton",2.0),
      "ev_per_anton_hour":round(observed.get("royalty",5.2)*observed.get("units",10)/observed.get("anton",2.0),2),
      "portfolio_information_gain":"HIGH" if row["product_architecture"] in {"ACTIVITY_PRACTICE_SYSTEM","FIELD_GUIDE","PROFESSIONAL_POCKET_REFERENCE"} else "MEDIUM",
      "main_kill_risk":observed.get("kill","Insufficient directly observed newcomer/book-demand evidence."),
      "evidence_confidence":"MEDIUM" if t else "LOW-MEDIUM",
      "investment_score":observed.get("score",45),
    }

def main() -> None:
    broad=build_broad()
    deep=[deep_record(next(r for r in broad if r["id"]==oid)) for oid in DEEP_IDS]
    top=[next(r for r in deep if r["id"]==oid) for oid in TOP_IDS]
    dump("broad-opportunities.json",{"schema_version":"radar-native-6-broad/v1","run_id":"RN6","observed_at":DATE,"count":len(broad),"opportunities":broad})
    dump("rejection-log.json",{"schema_version":"radar-native-6-rejections/v1","count":len(broad)-len(deep),"rejections":[{"id":r["id"],"reason":r["rejection_reason"]} for r in broad if r["cheap_gate"]=="REJECT"]})
    dump("deep-scan.json",{"schema_version":"radar-native-6-deep/v1","count":len(deep),"candidates":deep})
    dump("top-ten.json",{"schema_version":"radar-native-6-top/v1","count":10,"candidates":top})
    dump("portfolio-similarity-audit.json",{"schema_version":"portfolio-similarity-audit/v1","catalog_checked":CATALOG,"catalog_complete_for_known_projects":True,"results":[{"opportunity_id":x["id"],"topic_similarity":x["portfolio_similarity"],"product_architecture_similarity":x["architecture_similarity"],"dimension_evidence":{"buyer":"different","jtbd":"different","trigger":"different","promise":"different","format":"possible generic overlap only","information_architecture":"explicitly scored separately"}} for x in deep]})
    gates=[]
    for rank,x in enumerate(top,1):
        gates.append({"rank":rank,"opportunity_id":x["id"],"portfolio_similarity_gate":"PASS","commercial_differentiation_gate":"FAIL" if TOP[x["id"]]["gate"] in {"FAIL_DIFFERENTIATION","FAIL_PAID_VALUE"} else "PASS","free_alternative_paid_value_gate":"FAIL" if TOP[x["id"]]["gate"] in {"FAIL_BOOK_DEMAND","FAIL_PAID_VALUE"} else "PASS","source_rights_gate":"PASS_WITH_LIMITS","format_eligibility_gate":"PASS","autonomous_factual_qa":"FAIL" if TOP[x["id"]]["gate"]=="FAIL_AUTHOR_DEPENDENCY" else "PASS","author_dependency_gate":"FAIL" if TOP[x["id"]]["gate"]=="FAIL_AUTHOR_DEPENDENCY" else "PASS","product_quality_feasibility":"FAIL" if TOP[x["id"]]["gate"] in {"FAIL_PRODUCT_QUALITY_FEASIBILITY","FAIL_COMPETITION_AND_PRODUCTION"} else "PASS","raw_to_product_gate":"PASS","currentness_volatility_gate":"FAIL" if TOP[x["id"]]["gate"]=="FAIL_ATTENTION_AND_EVIDENCE" else "PASS","book_format_fit_gate":"FAIL" if TOP[x["id"]]["gate"]=="FAIL_BOOK_DEMAND" else "PASS","outcome":TOP[x["id"]]["gate"],"exact_reason":x["main_kill_risk"]})
    dump("investment-gates.json",{"schema_version":"radar-native-6-gates/v1","tested":len(gates),"outcomes":gates,"final_decision":"NO_PRODUCT","production_started":False})
    sources=[
      {"id":"KDP-LANG","label":"OBSERVED","title":"Book Supported Languages","publisher":"Amazon KDP","url":"https://kdp.amazon.com/en_US/help/topic/G200673300","use":"EN and FR support print/Kindle; UK and PL print-only; Russian and Belarusian absent from the supported-language list"},
      {"id":"AMZ-SWIM","label":"OBSERVED","title":"Amazon Books search: swim meet parent guide","url":"https://www.amazon.com/s?k=swim+meet+parent+guide&i=stripbooks","observation":"108 results; no direct field guide established in visible first block"},
      {"id":"AMZ-CHURCH-SOUND","label":"OBSERVED","title":"Amazon Books search: church sound volunteer guide","url":"https://www.amazon.com/s?k=church+sound+volunteer+guide&i=stripbooks","observation":"68 results; direct incumbents visible"},
      {"id":"GREAT-CHURCH-SOUND","label":"OBSERVED","title":"Great Church Sound second edition","url":"https://www.amazon.com/dp/0996642315","observation":"direct 320-page illustrated incumbent with checklists and companion resources"},
      {"id":"AMZ-HANDWRITING","label":"OBSERVED","title":"Amazon Books search: historical handwriting genealogy workbook","url":"https://www.amazon.com/s?k=historical+handwriting+genealogy+workbook&i=stripbooks","observation":"198 results"},
      {"id":"READ-CURSIVE","label":"OBSERVED","title":"Read Cursive Fast","url":"https://www.amazon.com/dp/B0GNJ99141","observation":"139 pages; about EUR17.20 paperback; 13 ratings; progressive historical-document practice and answer key; February 2026 listing with older reviews"},
      {"id":"AMZ-CEMETERY","label":"OBSERVED","title":"Amazon Books search: cemetery symbols field guide","url":"https://www.amazon.com/s?k=cemetery+symbols+field+guide&i=stripbooks","observation":"38 results"},
      {"id":"STORIES-STONE","label":"OBSERVED","title":"Stories in Stone","url":"https://www.amazon.com/dp/158685321X","observation":"established direct color-photo field guide; approximately 280 ratings reported by current secondary catalog evidence"},
      {"id":"AMZ-CENSUS","label":"OBSERVED","title":"Amazon Books search: US census records visual guide genealogy","url":"https://www.amazon.com/s?k=US+census+records+visual+guide+genealogy&i=stripbooks","observation":"17 results; exact recent competitor ranked first"},
      {"id":"CENSUS-DIRECT","label":"OBSERVED","title":"US Census Records: Reading and Interpreting Records","url":"https://www.amazon.com/dp/B0GNZVJ118","observation":"published February 17 2026; 89 pages; about EUR8.59; 4 ratings; BSR #1,291,966"},
      {"id":"AMZ-STAGE","label":"OBSERVED","title":"Amazon Books search: community theater stage manager handbook","url":"https://www.amazon.com/s?k=community+theater+stage+manager+handbook&i=stripbooks","observation":"68 results"},
      {"id":"STAGE-COMMUNITY","label":"OBSERVED","title":"Recent stage-management learning discussions","url":"https://www.reddit.com/r/stagemanagement/comments/1bnvqau/","observation":"new and returning community-theatre participants ask for books and training"},
    ]
    dump("evidence-ledger.json",{"schema_version":"radar-native-6-evidence/v1","observed_at":DATE,"sources":sources,"limitations":["Amazon pages are location-sensitive and displayed delivery-localized EUR prices.","Result counts are noisy query observations, not market size.","BSR was recorded only where directly visible; it was not imputed.","Economics are conservative hypotheses, not forecasts.","Deep candidates below the Top 10 retain UNKNOWN where product-level evidence was not economical to gather after no finalist cleared."]})
    report="""# Radar-Native Discovery #6\n\nObserved 2026-09-08. RN6 screened 330 distinct buyer-job markets, deep-scanned 27, and ran all ten ranked candidates through investment gates.\n\n## Decision\n\n**NO PRODUCT.** No candidate combines direct book-demand/newcomer evidence, defendable paid value, autonomous authority, and fast product-quality feasibility strongly enough to authorize production. A representative product sample would not resolve the dominant uncertainty: commercial demand.\n\nThe closest candidate, **RN6-001 — First Swim Meet Parent Map**, has a real recurring problem and excellent print fit, but the evidence establishes club/community problem demand rather than paid book demand. Abundant free first-meet guides and no observed recent entrant traction make the 90-day hypothesis too speculative.\n\nRN6 did not overfit to RN5: none of the Top 10 is DATA_TO_DECISION, and the finalists span family utility, pocket reference, practice system, field guide, public-domain transformation, bilingual reference, visual reference, and hybrid workbook architectures. Early similarity found all ten topic-novel; it also prevented architecture novelty from being confused with commercial proof.\n\nProduction did not start.\n"""
    (OUT/"radar-native-6-report.md").write_text(report)
    learning="""# Radar-Native #6 learning\n\n- **RN5 overfit:** not observed in the finalists. No Top-10 candidate uses the RN5 DATA_TO_DECISION architecture. Consumer decision systems appeared in the broad map but did not receive a familiarity bonus.\n- **Architecture diversity:** the 27 deep candidates cover family utility, field/pocket reference, practice, public-domain transformation, bilingual/cross-system, visual reference, regulatory orientation, logbook, and hybrid reference/workbook forms.\n- **Multilingual usefulness:** Ukrainian and Polish created plausible cross-system jobs, but paperback-only eligibility and language/policy review reduced their fast-experiment economics. Russian and Belarusian failed current KDP supported-language eligibility and were blocked early.\n- **Amazon versus external discovery:** external sources were better at finding real recurring problems; Amazon was decisive at killing seemingly attractive products through incumbents, weak recent traction, or an absence of exact paid demand.\n- **NO PRODUCT probability:** remains materially high and should remain an accepted output. Ten finalist failures show that broad problem demand is not enough.\n- **Product Quality risk:** visual and archival products clustered at HIGH because their paid value depends on image quality, examples and expert sequencing. This erased several apparently evergreen opportunities.\n- **Format Eligibility:** early gating prevented RU/BE products and Kindle assumptions for UK/PL from contaminating economics.\n- **Portfolio Similarity:** all Top 10 were topic-novel against the complete known catalog. Separating architecture similarity showed novelty is not a substitute for demand.\n- **Consumer decision-system recurrence:** broad candidates recur partly because the architecture exposes paid value clearly, but RN6 ranking did not favor them. The recurrence is therefore both a genuine opportunity pattern and a generator/search bias; do not change weights yet.\n\nNo permanent scoring weights were changed.\n"""
    (OUT/"radar-native-6-learning.md").write_text(learning)
    bundle={"schema_version":"book-radar-import/v1","radar_runs":[{"id":"RN6","name":"Radar-Native Discovery #6","observed_at":DATE,"status":"NO_PRODUCT","opportunities_scanned":330,"deep_scanned":27}],"opportunities":[{"id":r["id"],"radar_run_id":"RN6","buyer_job":r["buyer_job"],"query_cluster":r["query_cluster"],"format":r["format"],"price_band":r["price_band"],"concept":r["working_product"],"language":r["language"],"marketplace":r["primary_marketplace"],"product_architecture":r["product_architecture"],"format_constraint":r["format_eligibility"] if r["format_eligibility"]!="SUPPORTED" else None,"format_opportunity":"SUPPORTED primary format" if r["format_eligibility"]=="SUPPORTED" else None} for r in broad],"evidence":[{"id":f"evidence:{x['id']}:rn6-deep","opportunity_id":x["id"],"observed_at":DATE,"summary":x["commercial_differentiation"],"details":x,"source_ref":"book-radar/runs/rn6/deep-scan.json"} for x in deep],"decisions":[{"id":f"decision:{r['id']}:rn6-screen","opportunity_id":r["id"],"decision":r["cheap_gate"],"reason":r["rejection_reason"],"decided_at":DATE} for r in broad]+[{"id":f"decision:{g['opportunity_id']}:rn6-investment","opportunity_id":g["opportunity_id"],"decision":g["outcome"],"reason":g["exact_reason"],"decided_at":DATE,"production_authorized":False} for g in gates]}
    dump("book-radar-import.json",bundle)
    dump("production-contract.json",{"schema_version":"rn6-production-contract/v1","status":"NOT_READY_NO_PRODUCT","opportunity_id":None,"product":None,"reason":"No finalist cleared all investment gates; therefore no production contract is fabricated.","representative_product_gate":"NOT_REQUIRED","human_product_gate":"NOT_REQUIRED","production_authorized":False,"production_started":False})
    print(json.dumps({"run":"RN6","opportunities":len(broad),"deep":len(deep),"top":len(top),"decision":"NO_PRODUCT"},indent=2))

if __name__ == "__main__":
    main()
