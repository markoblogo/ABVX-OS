#!/usr/bin/env python3
"""Finalize RN5-001 commercial package after content/layout/QA freeze."""
from __future__ import annotations
import json
from pathlib import Path
from abvx_harness.publishing_gates import validate_commercial_artifacts, validate_commercial_package, release_authorization

ROOT=Path(__file__).resolve().parents[1]
BOOK=ROOT/'books'/'rn5-001'; COMM=BOOK/'commercial'; PROD=BOOK/'production'; QA=BOOK/'qa'
COMM.mkdir(parents=True,exist_ok=True)
manifest=json.loads((PROD/'production-manifest.json').read_text())
qa=json.loads((QA/'release-qa.json').read_text())
assert manifest.get('content_frozen') and manifest.get('layout_frozen') and qa['status']=='PASS'
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
  "schema_version":"rn5-001-commercial-package/v2",
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
  "pricing":{
    "price_status":"FINAL",
    "final_price_version":"RN5-001-v1.1",
    "final_content_version":"RN5-001-v1.1",
    "final_layout_version":"RN5-001-v1.1",
    "formats":{
      "PAPERBACK":{
        "recommended_list_price":16.99,
        "currency":"USD",
        "primary_marketplace":"Amazon.com",
        "acceptable_test_range":{"minimum":15.99,"maximum":17.99,"currency":"USD"},
        "production_or_delivery_cost":2.84,
        "royalty_rate_tier":"60% Amazon marketplace royalty tier",
        "estimated_royalty_per_sale":7.35,
        "pricing_rationale":"The direct proposal-decoder niche remains visibly underserved. Current adjacent homeowner solar paperbacks cluster around EUR 12.90–17.20 in the Amazon.com France-delivery view. The 8 x 10 write-in decision system offers more transaction-specific utility than a general guide, while $16.99 remains inside the visible substitute band and preserves a $7.35 estimated Amazon.com royalty.",
        "date_checked":"2026-09-08",
        "final_trim":"8 x 10 in",
        "final_page_count":58,
        "ink":"Black & white",
        "paper":"White",
        "final_printing_cost":2.84
      }
    }
  },
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
- ISBN: choose KDP free ISBN or publisher-owned ISBN at upload

## PRICING

- Primary marketplace: Amazon.com
- Paperback recommended list price: $16.99 USD
- Acceptable test range: $15.99–$17.99 USD
- Printing cost: $2.84
- Royalty tier: 60% on Amazon.com at this list price
- Estimated royalty: approximately $7.35 per sale
- Expanded Distribution: NO initially — the product is a specialized direct-to-consumer workbook, while Expanded Distribution reduces the estimated royalty to $3.96 and does not guarantee retailer or library orders.
- Other marketplace prices: use KDP-converted equivalents as the initial treatment, then review the live values for obvious outliers before publication.
- Price last verified: September 8, 2026
- Confirm the live printing cost and royalty in KDP immediately before publication; this confirmation does not replace the $16.99 recommendation.

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
metadata=f"""# RN5-001 — final KDP metadata card

## Identity

- Title: {package['title']}
- Subtitle: {package['subtitle']}
- Author: {package['author']}
- Language: English
- Edition: 1
- Series: None

## Description

{description}

## Keywords

"""+"\n".join(f"{i}. {v}" for i,v in enumerate(package['keywords'],1))+"""

## Categories

"""+"\n".join(f"{c['rank']}. {c['path']}" for c in categories)+"""

## Paperback format

- 8 x 10 inches; black-and-white ink on white paper; no bleed; matte cover
- 57 PDF pages / 58 KDP pages
- Not low-content; not large print

## PRICING

- Recommended list price: $16.99 USD
- Primary marketplace: Amazon.com
- Acceptable test range: $15.99–$17.99 USD
- Printing cost: $2.84
- Royalty tier: 60%
- Estimated royalty: approximately $7.35 per Amazon.com sale
- Price status: FINAL
- Price version: RN5-001-v1.1
- Price checked: September 8, 2026
"""
(COMM/'metadata-card.md').write_text(metadata)
pricing_analysis="""# RN5-001 final pricing analysis

## Recommendation

**Recommended Amazon.com paperback list price: $16.99 USD.**

Acceptable controlled test range: **$15.99–$17.99 USD**. Price status: **FINAL** for RN5-001-v1.1.

## Frozen production inputs

- Trim: 8 x 10 inches
- Final KDP page count: 58
- Interior: black ink on white paper
- Printing cost: $2.84 on Amazon.com
- Royalty tier: 60% at $16.99
- Estimated standard royalty: (0.60 × $16.99) − $2.84 = **$7.35**
- Estimated Expanded Distribution royalty: (0.40 × $16.99) − $2.84 = **$3.96**

## Current market evidence

The September 8, 2026 Amazon.com search view, displayed for delivery to France, showed current adjacent homeowner-solar paperbacks at EUR 12.90, EUR 15.48, and EUR 17.20. Examples included *The Homeowner's Solar Survival Guide* (EUR 12.90), *Solar System Sizing Workbook 2026* (EUR 15.48), and *Kick Your Electric Bill To The Curb* and *Solar Without the Scam* (EUR 17.20). The earlier exact-query check found no direct solar-proposal-comparison workbook.

These displayed EUR prices are directional substitute evidence, not Amazon.com USD list-price inputs. The final product is a specialized 8 x 10 reference-plus-write-in decision system rather than a generic solar introduction. $16.99 places it near the upper-middle of the visible substitute shelf without charging an unsupported premium.

## Distribution decision

Do not enable Expanded Distribution initially. The product is specialized and direct-to-consumer; the lower $3.96 estimated royalty is not justified by any demonstrated bookstore or library demand, and enrollment does not guarantee orders.

Use KDP-converted prices for other marketplaces initially and review the live grid for obvious outliers. Confirm KDP's live cost and royalty immediately before publication; this does not replace the frozen $16.99 recommendation.

## Sources

- Amazon.com live search evidence checked September 8, 2026; results displayed in EUR because the delivery context was France.
- KDP Paperback Printing Cost: https://kdp.amazon.com/en_US/help/topic/G201834340
- KDP Paperback Royalty: https://kdp.amazon.com/en_US/help/topic/G201834330
- KDP Print Book Pricing: https://kdp.amazon.com/en_US/help/topic/G8BKPU9AGVZSF9QF
- KDP Expanded Distribution: https://kdp.amazon.com/en_US/help/topic/GQTT4W3T5AYK7L45
"""
(COMM/'pricing-analysis.md').write_text(pricing_analysis)
def display(v):
    if isinstance(v,list): return ' / '.join(map(str,v))
    return str(v)
(COMM/'cover-brief.md').write_text("# Final cover brief\n\n"+"\n\n".join([f"**{k.replace('_',' ').title()}**\n\n{display(v)}" for k,v in package['cover_brief'].items()])+"\n")

format_gate={"schema_version":"rn5-001-format-eligibility/v1","checked":"2026-09-07","language":"English","primary_marketplace":"Amazon.com","paperback":{"platform_support":"SUPPORTED","buyer_utility":"HIGH","commercial_role":"PRIMARY","decision":"PRODUCED"},"kindle":{"platform_support":"SUPPORTED","reflowable_utility":"LOW","commercial_role":"UNCLEAR","reason":"The core job depends on handwriting, roomy three-way matrices, source-page annotation, and a retained physical decision packet. Reflow strips away the primary execution layer; a prose-only Kindle would be a materially different product.","decision":"NOT_JUSTIFIED"},"final_secondary_format_decision":"KINDLE_NOT_PRODUCED"}
(PROD/'format-eligibility-gate.json').write_text(json.dumps(format_gate,indent=2)+"\n")

artifact_result=validate_commercial_artifacts(package,{
  "commercial_package":(COMM/'kdp-commercial-package.json').read_text(),
  "metadata_card":metadata,
  "kdp_upload_card":card,
  "pricing_analysis":pricing_analysis,
  "book_radar_record":(ROOT/'book-radar'/'state.json').read_text(),
})
gates={"market":"PASS","product_thesis":"PASS","representative_product":"PASS","factual_source":"PASS","language":"PASS","editorial":"PASS","product_quality":"PASS","technical":"PASS","toc_navigation":"PASS","commercial_package":"PASS" if result['status']=='PASS' and artifact_result['status']=='PASS' else "FAIL","kdp_external_preview":"HUMAN_PENDING"}
auth=release_authorization(gates)
release={"schema_version":"rn5-001-release-manifest/v1.2","status":"KDP_READY_AWAITING_HUMAN_COVER_AND_PUBLISHING_GATE" if auth['status']=='KDP_READY' else "NOT_READY","content_version":"RN5-001-v1.1","commercial_package_content_version":"RN5-001-v1.1","final_layout_version":"RN5-001-v1.1","final_price_version":"RN5-001-v1.1","price_status":"FINAL","pricing_hard_gate":gates['commercial_package'],"gates":gates,"authorization":auth,"paperback_pdf":"output/pdf/solar-proposal-decoder-buyer-decision-system-paperback.pdf","production_master":"books/rn5-001/production/solar-proposal-decoder-production-master.pdf","kindle":"NOT_JUSTIFIED","cover":"BRIEF_ONLY","human_actions":["choose final cover","generate cover from live KDP 58-page template","upload files","run KDP Print Previewer","publish"]}
(PROD/'release-manifest.json').write_text(json.dumps(release,indent=2)+"\n")
manifest.update({'status':release['status'],'commercial_package':gates['commercial_package'],'commercial_package_content_version':'RN5-001-v1.1','final_price_version':'RN5-001-v1.1','final_layout_version':'RN5-001-v1.1','price_status':'FINAL','paperback_price_usd':16.99,'printing_cost_usd':2.84,'estimated_paperback_royalty_usd':7.35,'open_content_or_layout_correction_gates':0})
(PROD/'production-manifest.json').write_text(json.dumps(manifest,indent=2)+"\n")
print(json.dumps({'commercial_package':result['status'],'artifact_consistency':artifact_result['status'],'pricing_hard_gate':gates['commercial_package'],'release':release['status'],'price':16.99,'printing_cost':2.84,'royalty':7.35},indent=2))
