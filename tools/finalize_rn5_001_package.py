#!/usr/bin/env python3
"""Finalize RN5-001 commercial package after content/layout/QA freeze."""
from __future__ import annotations
import json
from pathlib import Path
from abvx_harness.publishing_gates import validate_commercial_package, release_authorization

ROOT=Path(__file__).resolve().parents[1]
BOOK=ROOT/'books'/'rn5-001'; COMM=BOOK/'commercial'; PROD=BOOK/'production'; QA=BOOK/'qa'
COMM.mkdir(parents=True,exist_ok=True)
manifest=json.loads((PROD/'production-manifest.json').read_text())
qa=json.loads((QA/'release-qa.json').read_text())
assert manifest['status']=='CONTENT_LAYOUT_AND_QA_FROZEN' and qa['status']=='PASS'
assert manifest['content_version']=='RN5-001-v1.1' and manifest['trim_name']=='8x10'
assert manifest['pdf_pages']==57 and manifest['kdp_rounded_page_count']==58

description="""Three solar proposals can make three different numbers look decisive. One leads with a low monthly payment. Another leads with annual production. A third shows a “net” price after assumptions. Those headlines are not directly comparable.

Solar Proposal Decoder gives homeowners a buyer-owned method for turning real proposals into one documented decision packet. It teaches you how to:

• locate the cash price, financed principal, system size, equipment, production model, scope, exclusions, and warranty terms;
• separate facts, estimates, sales claims, and missing information;
• calculate cash cost per watt, financed premium, scheduled payments, and production per installed kW—without hiding each metric’s limitations;
• decode claims such as “low monthly payment,” “100% offset,” “turnkey,” and “25-year warranty”;
• turn every material gap into a proposal-specific written question;
• log replies and revised documents; and
• record the final choice, trade-offs, and remaining uncertainty.

The book includes an original synthetic three-quote case plus a practical write-in comparison packet for up to three real proposals. It does not rank installers, promise savings, recommend financing, determine tax eligibility, or replace professional advice. All examples are synthetic, and volatile incentives and utility rules are routed back to the responsible current source."""

categories=[
  {"rank":1,"path":"Crafts, Hobbies & Home > Home Improvement & Design > How-to & Home Improvements","reason":"Primary buyer job is evaluating a major home-improvement proposal before signing.","fallback":"Crafts, Hobbies & Home > Sustainable Living"},
  {"rank":2,"path":"Business & Money > Personal Finance > Money Management","reason":"The system normalizes cash, financing and contractual obligations without giving investment advice.","fallback":"Business & Money > Personal Finance > Budgeting"},
  {"rank":3,"path":"Science & Math > Energy > Solar","reason":"The subject is residential solar and production-model evidence.","fallback":"Engineering & Transportation > Engineering > Energy Production & Extraction"},
]
package={
  "schema_version":"rn5-001-commercial-package/v1",
  "status":"FINAL_AFTER_CONTENT_LAYOUT_QA_FREEZE",
  "title":"Solar Proposal Decoder",
  "subtitle":"A Homeowner's System for Comparing Quotes, Financing, Production Claims, Scope, and Warranties Before Signing",
  "author":"Casey Rowan",
  "author_bio":"Casey Rowan creates independent, source-grounded consumer decision tools. No installer, engineering, financial, tax, legal, or government affiliation is claimed.",
  "description":description,
  "keywords":["residential photovoltaic buyer workbook","compare installer bids","rooftop system financing questions","home energy contract checklist","warranty scope worksheet","production estimate assumptions","before signing contractor agreement"],
  "categories":categories,
  "primary_marketplace":"Amazon.com",
  "planned_formats":["PAPERBACK"],
  "format_eligibility_status":{"PAPERBACK":"SUPPORTED","KINDLE":"SUPPORTED_BUT_NOT_JUSTIFIED"},
  "format_settings":{"language":"English","trim":"8 x 10 in","ink":"Black & white","paper":"White","bleed":"No bleed","cover_finish":"Matte","reading_direction":"Left to right","low_content":"No","large_print":"No","pdf_pages":manifest['pdf_pages'],"kdp_rounded_page_count":manifest['kdp_rounded_page_count'],"isbn":"KDP free ISBN or publisher-owned ISBN — human publishing choice","territories":"All territories where rights are held","expanded_distribution":"Optional; royalty estimated separately"},
  "paperback_price":16.99,
  "printing_cost_usd":2.84,
  "royalty_rate":0.60,
  "estimated_paperback_royalty_usd":7.35,
  "expanded_distribution_royalty_rate":0.40,
  "estimated_expanded_distribution_royalty_usd":3.96,
  "price_checked":"2026-09-08",
  "economics_source":"KDP Paperback Printing Cost and Paperback Royalty official help; large-trim black ink, 24–110 pages uses $2.84 fixed Amazon.com printing cost; $16.99 receives 60% rate.",
  "content_version":"RN5-001-v1.1",
  "commercial_package_content_version":"RN5-001-v1.1",
  "open_content_or_layout_correction_gates":0,
  "cover_brief":{
    "status":"BRIEF_ONLY_AWAITING_HUMAN_COVER_GATE",
    "trim":"8 x 10 in paperback",
    "page_count_for_kdp_template":58,
    "interior":"black ink on white paper, no bleed",
    "finish":"matte",
    "front_cover_hierarchy":["SOLAR PROPOSAL DECODER","A Homeowner's System for Comparing Quotes, Financing, Production Claims, Scope, and Warranties Before Signing","FIND • EXTRACT • NORMALIZE • CHALLENGE • ASK • VERIFY • DECIDE","Casey Rowan"],
    "concept":"A clean consumer-document aesthetic: three offset proposal sheets converge into one organized decision packet. Use a restrained navy, white, pale blue and solar-gold cover palette; no rooftop stock-photo cliché, sunburst, government seal, savings promise, red-alert scam language, or installer endorsement.",
    "back_cover_copy":"Three proposals. Three different headlines. One buyer-owned decision packet. Learn where the important facts live, normalize price and production without hiding assumptions, decode broad sales claims, generate written installer questions, and preserve the answers before signing.",
    "production_instruction":"Generate the final wrap only from the current KDP cover template using 8 x 10 in, black-and-white white-paper interior, and KDP's rounded 58-page count. Keep all live text inside the template safe zone and leave the barcode area clear.",
  },
  "ai_generated_content_disclosure":{"text":"YES","images":"NO","translations":"NO","note":"Answer the live KDP disclosure fields truthfully; KDP wording may change."},
}
result=validate_commercial_package(package)
assert result['status']=='PASS',result
(COMM/'kdp-commercial-package.json').write_text(json.dumps(package,indent=2)+"\n")

card=f"""# RN5-001 — Copy/paste KDP upload card

## Identity

Title: {package['title']}

Subtitle: {package['subtitle']}

Author: {package['author']}

Language: English

Edition: 1

Series: None

## Description

{description}

## Keywords

"""+"\n".join(f"{i}. {v}" for i,v in enumerate(package['keywords'],1))+"""

## Categories — ranked

"""+"\n".join(f"{c['rank']}. {c['path']}\n   Fallback: {c['fallback']}" for c in categories)+f"""

## Paperback settings

- 8 x 10 inches
- Black & white ink on white paper
- No bleed
- Matte cover
- Left-to-right
- Not low-content
- PDF interior pages: {manifest['pdf_pages']}; KDP rounded print count: {manifest['kdp_rounded_page_count']}
- Primary marketplace: Amazon.com
- List price: $16.99
- Printing cost estimate: $2.84
- Standard Amazon royalty estimate: $7.35 per unit
- Expanded Distribution royalty estimate: $3.96 per unit
- ISBN: choose KDP free ISBN or publisher-owned ISBN at upload

## AI-generated content disclosure

- Text: Yes
- Images: No
- Translations: No

## Upload files

- Interior: output/pdf/solar-proposal-decoder-buyer-decision-system-paperback.pdf
- Cover: not yet produced; use the final KDP 58-page template after human cover selection

## Final human publishing gate

1. Choose and approve the final cover direction.
2. Generate cover against the live KDP 58-page template.
3. Upload interior and cover.
4. Inspect every flagged page and representative forms in KDP Print Previewer.
5. Order/inspect a physical proof if desired, then publish.
"""
(COMM/'kdp-upload-card.md').write_text(card)
def display(v):
    if isinstance(v,list): return ' / '.join(map(str,v))
    return str(v)
(COMM/'cover-brief.md').write_text("# Final cover brief\n\n"+"\n\n".join([f"**{k.replace('_',' ').title()}**\n\n{display(v)}" for k,v in package['cover_brief'].items()])+"\n")

format_gate={"schema_version":"rn5-001-format-eligibility/v1","checked":"2026-09-07","language":"English","primary_marketplace":"Amazon.com","paperback":{"platform_support":"SUPPORTED","buyer_utility":"HIGH","commercial_role":"PRIMARY","decision":"PRODUCED"},"kindle":{"platform_support":"SUPPORTED","reflowable_utility":"LOW","commercial_role":"UNCLEAR","reason":"The core job depends on handwriting, roomy three-way matrices, source-page annotation, and a retained physical decision packet. Reflow strips away the primary execution layer; a prose-only Kindle would be a materially different product.","decision":"NOT_JUSTIFIED"},"final_secondary_format_decision":"KINDLE_NOT_PRODUCED"}
(PROD/'format-eligibility-gate.json').write_text(json.dumps(format_gate,indent=2)+"\n")

gates={"market":"PASS","product_thesis":"PASS","representative_product":"PASS","factual_source":"PASS","language":"PASS","editorial":"PASS","product_quality":"PASS","technical":"PASS","toc_navigation":"PASS","commercial_package":"PASS","kdp_external_preview":"HUMAN_PENDING"}
auth=release_authorization(gates)
release={"schema_version":"rn5-001-release-manifest/v1.1","status":"KDP_READY_AWAITING_HUMAN_COVER_AND_PUBLISHING_GATE" if auth['status']=='KDP_READY' else "NOT_READY","content_version":"RN5-001-v1.1","commercial_package_content_version":"RN5-001-v1.1","gates":gates,"authorization":auth,"paperback_pdf":"output/pdf/solar-proposal-decoder-buyer-decision-system-paperback.pdf","production_master":"books/rn5-001/production/solar-proposal-decoder-production-master.pdf","kindle":"NOT_JUSTIFIED","cover":"BRIEF_ONLY","human_actions":["choose final cover","generate cover from live KDP 58-page template","upload files","run KDP Print Previewer","publish"]}
(PROD/'release-manifest.json').write_text(json.dumps(release,indent=2)+"\n")
manifest.update({'status':release['status'],'commercial_package':'PASS','commercial_package_content_version':'RN5-001-v1.1','kindle':'NOT_JUSTIFIED','paperback_price_usd':16.99,'printing_cost_usd':2.84,'estimated_paperback_royalty_usd':7.35,'open_content_or_layout_correction_gates':0})
(PROD/'production-manifest.json').write_text(json.dumps(manifest,indent=2)+"\n")
print(json.dumps({'commercial_package':result['status'],'release':release['status'],'price':16.99,'printing_cost':2.84,'royalty':7.35},indent=2))
