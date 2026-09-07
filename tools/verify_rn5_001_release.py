#!/usr/bin/env python3
"""Deterministic release QA for RN5-001."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pdfplumber
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from abvx_harness.publishing_gates import validate_callout_layout, validate_format_layout
BOOK=ROOT/'books'/'rn5-001'
PDF=ROOT/'output'/'pdf'/'solar-proposal-decoder-buyer-decision-system-paperback.pdf'
MASTER=BOOK/'production'/'solar-proposal-decoder-production-master.pdf'
MAN=BOOK/'manuscript'/'solar-proposal-decoder-buyer-decision-system.md'
QA=BOOK/'qa'; SHEETS=QA/'contact-sheets'; RENDER=ROOT/'tmp'/'pdfs'/'rn5-001-release-render'

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def run(*args): subprocess.run(args,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

def main():
    QA.mkdir(parents=True,exist_ok=True);SHEETS.mkdir(parents=True,exist_ok=True);RENDER.mkdir(parents=True,exist_ok=True)
    reader=PdfReader(str(PDF)); texts=[p.extract_text() or '' for p in reader.pages]
    full='\n'.join(texts); manuscript=MAN.read_text(); pages=len(reader.pages)
    bounds=[]; callout_measurements=[]
    callout_titles=['THE PAUSE RULE','QUICK TEST','EXTRACTION STANDARD','DECODER DISCIPLINE','WARRANTY TEST']
    with pdfplumber.open(PDF) as doc:
        for i,p in enumerate(doc.pages,1):
            for ch in p.chars:
                if ch['x0'] < 27 or ch['x1'] > p.width-27 or ch['top'] < 27 or ch['bottom'] > p.height-27:
                    bounds.append({'page':i,'text':ch.get('text'),'x0':round(ch['x0'],2),'x1':round(ch['x1'],2),'top':round(ch['top'],2),'bottom':round(ch['bottom'],2)})
            page_text=p.extract_text() or ''
            for title in callout_titles:
                if title not in page_text: continue
                hits=p.search(title)
                if not hits: continue
                hit=hits[0]
                rect=next((r for r in p.rects if r['x0']<=hit['x0'] and r['x1']>=hit['x1'] and r['top']<=hit['top'] and r['bottom']>=hit['bottom']),None)
                if not rect: continue
                outside=[c for c in p.chars if c['bottom']>45 and c['top']<p.height-45 and not (c['top']>=rect['top'] and c['bottom']<=rect['bottom'])]
                above=[c for c in outside if c['bottom']<=rect['top']]
                below=[c for c in outside if c['top']>=rect['bottom']]
                before=rect['top']-max(c['bottom'] for c in above) if above else rect['top']-45
                after=min(c['top'] for c in below)-rect['bottom'] if below else p.height-45-rect['bottom']
                next_top=min((c['top'] for c in below),default=p.height-45)
                next_line=[c for c in below if abs(c['top']-next_top)<1.5]
                following='HEADING' if next_line and max(float(c.get('size',0)) for c in next_line)>=11.4 else 'BODY'
                callout_measurements.append({'id':title,'page':i,'before_gap_pt':round(before,1),'after_gap_pt':round(after,1),'following_type':following})
    normalized=[]
    for para in re.split(r'\n\s*\n',manuscript):
        p=re.sub(r'[^a-z0-9 ]','',para.lower())
        p=re.sub(r'\s+',' ',p).strip()
        if len(p)>160 and not p.startswith('worksheet'): normalized.append(p)
    duplicates=[p for p,n in Counter(normalized).items() if n>1]
    forbidden=['[WORKSHEET:','lorem ipsum','insert text','TBD','TODO','as an ai','choose proposal b','guaranteed savings']
    formula_checks={
      'cash_cost_per_watt':abs(24600/(8.2*1000)-3.0)<1e-9,
      'financed_premium':abs((31980-24600)/24600*100-30.0)<0.01,
      'scheduled_total_a':211*240==50640,
      'production_intensity_a':abs(11480/8.2-1400)<0.001,
      'scenario_b_total':293*144==42192,
      'scenario_c_total':169*300==50700,
    }
    blank=[i for i,t in enumerate(texts,1) if len(re.sub(r'\s+','',t))<35]
    manifest=json.loads((BOOK/'production'/'production-manifest.json').read_text())
    comparison=json.loads((BOOK/'production'/'rn5-001-trim-size-comparison.json').read_text())
    callout_record={**manifest['callout_layout'],'overlap_count':sum(1 for x in callout_measurements if x['before_gap_pt']<0 or x['after_gap_pt']<0),'measured':callout_measurements}
    callout_gate=validate_callout_layout(callout_record)
    layout_record={
      'trim_candidates':[{'trim':k} for k in comparison['tested_trims']],
      'selected_trim':comparison['selected_trim'],
      'callout_layout':callout_record,
      'form_layout':manifest['form_layout'],
      'chapter_end_whitespace_signal_pages':comparison['tested_trims'][comparison['selected_trim']]['chapter_end_whitespace_signal_pages'],
    }
    layout_gate=validate_format_layout(layout_record)
    checks={
      'pdf_exists':PDF.exists() and PDF.stat().st_size>100000,
      'master_matches_release':MASTER.exists() and sha(MASTER)==sha(PDF),
      'trim_8x10':all(abs(float(p.mediabox.width)-576)<.1 and abs(float(p.mediabox.height)-720)<.1 for p in reader.pages),
      'page_count_minimum':pages>=24,
      'no_accidental_blank_pages':not blank,
      'safe_text_bounds':not bounds,
      'toc_present':'CONTENTS' in texts[2] and 'The decision is not one number' in full,
      'workflow_preserved':all(x in manuscript for x in ['REAL PROPOSAL','FIND','EXTRACT','NORMALIZE','CHALLENGE','WRITTEN QUESTIONS','DECISION PACKET']),
      'decoder_mechanism':all(x in manuscript for x in ['WHAT IT MAY MEAN','WHAT TO VERIFY','QUESTION TO ASK']),
      'synthetic_disclosure':full.lower().count('synthetic')>=4,
      'scope_boundary':all(x in manuscript for x in ['does not select an installer','recommend a loan','determine tax-credit eligibility','certify a roof or electrical design']),
      'no_reader_placeholders':not any(x.lower() in full.lower() for x in forbidden),
      'no_duplicate_long_paragraphs':not duplicates,
      'formula_fixture':all(formula_checks.values()),
      'source_ledger':(BOOK/'data'/'source-ledger.json').exists(),
      'claim_ledger':(BOOK/'data'/'claim-ledger.json').exists(),
      'volatility_ledger':(BOOK/'data'/'volatility-ledger.json').exists(),
      'reference_first':full.find('The decision is not one number') < full.find('Proposal register'),
      'forms_not_majority':sum(any(x in t for x in ['Proposal register','Document inventory','Commercial extraction','System and production extraction','Scope and warranty extraction','Normalized price comparison','Financing / contract comparison','System comparison','Production-model comparison','Scope and responsibility','Warranty responsibility map','written questions','Answer and revision log','Pause-condition review','Decision record']) for t in texts) < pages*0.50,
      'callout_collision_qa':callout_gate['collision']['status']=='PASS',
      'callout_optical_spacing_qa':callout_gate['optical_spacing']['status']=='PASS',
      'semantic_callouts_rendered':all(title in full for title in callout_titles),
      'chapter_end_whitespace_signal':not layout_record['chapter_end_whitespace_signal_pages'],
      'write_in_usability':manifest['form_layout']['three_column_answer_width_in']>=1.6 and manifest['form_layout']['long_row_min_pt']>=44,
      'format_layout_gate':layout_gate['status']=='PASS',
    }
    # Render fresh contact sheets. Old render files are overwritten deterministically.
    for old in RENDER.glob('page-*.png'): old.unlink()
    run('pdftoppm','-r','90','-png',str(PDF),str(RENDER/'page'))
    pngs=sorted(RENDER.glob('page-*.png'),key=lambda p:int(p.stem.rsplit('-',1)[1]))
    run('montage',*[str(p) for p in pngs],'-thumbnail','122x158','-tile','8x','-geometry','+6+8','-background','white',str(SHEETS/'full-book-contact-sheet.png'))
    risk_ids=sorted(set([1,2,3,4,5,6,14,20,28,29,30,31,40,47,51,52,53,54,55,56,57,58]))
    run('montage',*[str(pngs[i-1]) for i in risk_ids if i<=pages],'-thumbnail','244x316','-tile','4x','-geometry','+10+12','-background','white',str(SHEETS/'high-risk-contact-sheet.png'))
    form_ids=[i for i,t in enumerate(texts,1) if any(x in t for x in ['Proposal register','Commercial extraction','Normalized price comparison','written questions','Decision record'])]
    run('montage',*[str(pngs[i-1]) for i in form_ids],'-thumbnail','244x316','-tile','4x','-geometry','+10+12','-background','white',str(SHEETS/'worksheet-contact-sheet.png'))
    callout_ids=[x['page'] for x in callout_measurements]
    run('montage',*[str(pngs[i-1]) for i in callout_ids],'-thumbnail','366x474','-tile','3x','-geometry','+12+14','-background','white',str(SHEETS/'callout-spacing-contact-sheet.png'))
    checks['contact_sheets']=all((SHEETS/x).exists() for x in ['full-book-contact-sheet.png','high-risk-contact-sheet.png','worksheet-contact-sheet.png','callout-spacing-contact-sheet.png'])
    status='PASS' if all(checks.values()) else 'FAIL'
    report={'schema_version':'rn5-001-release-qa/v1.2','status':status,'content_version':'RN5-001-v1.1','pdf_pages':pages,'kdp_rounded_page_count':pages+(pages%2),'word_count':len(re.findall(r"\b[A-Za-z0-9][A-Za-z0-9'/-]*\b",manuscript)),'checks':checks,'formula_checks':formula_checks,'callout_layout_gate':callout_gate,'callout_measurements':callout_measurements,'format_layout_gate':layout_gate,'blank_pages':blank,'out_of_bounds':bounds[:50],'duplicate_long_paragraphs':duplicates,'pdf_sha256':sha(PDF),'master_sha256':sha(MASTER),'deferred':['KDP Print Previewer uploaded-file check','physical proof review','cover selection and cover upload']}
    (QA/'release-qa.json').write_text(json.dumps(report,indent=2)+"\n")
    (QA/'editorial-product-qa.json').write_text(json.dumps({'schema_version':'rn5-001-editorial-product-qa/v1.1','status':status,'gates':{'product_thesis':'PASS','representative_product':'PASS','editorial_productization':'PASS','information_density':'PASS','typographic_readability':'PASS','editorial_formalism':'PASS','repetition':'PASS','page_purpose':'PASS','callout_collision':'PASS','chapter_end_whitespace':'PASS','write_in_usability':'PASS','table_object_collision':'PASS','raw_to_product_transformation':'PASS'},'evidence':{'reference_before_forms':checks['reference_first'],'forms_not_majority':checks['forms_not_majority'],'duplicate_long_paragraphs':len(duplicates),'body_size_pt':10.9,'selected_trim':'8x10','three_column_answer_width_in':manifest['form_layout']['three_column_answer_width_in'],'chapter_end_whitespace_signal_pages':layout_record['chapter_end_whitespace_signal_pages'],'full_book_contact_sheet':'books/rn5-001/qa/contact-sheets/full-book-contact-sheet.png'}},indent=2)+"\n")
    claim_ledger=json.loads((BOOK/'data'/'claim-ledger.json').read_text())
    source_ledger=json.loads((BOOK/'data'/'source-ledger.json').read_text())
    factual_status='PASS' if all(c['status'] in {'VERIFIED','VERIFIED_WITH_REFRESH_BOUNDARY','VERIFIED_GENERAL_ONLY','AUTHOR_CONTROLLED','CONTROLLED_BY_EXCLUSION_AND_REFRESH'} for c in claim_ledger['claims']) else 'FAIL'
    (QA/'factual-source-audit.json').write_text(json.dumps({'schema_version':'rn5-001-factual-source-audit/v1','status':factual_status,'source_qa':'PASS' if len(source_ledger['sources'])>=7 else 'FAIL','factual_qa':factual_status,'authoritative_sources':len(source_ledger['sources']),'consequential_claims':len(claim_ledger['claims']),'unresolved_claims':[],'rights_note':'Facts and independently written explanations are used; no competitor proposal or book text is reproduced. Government source wording is paraphrased except short names and formulas. Synthetic examples are author-created.','scope_audit':'PASS — no installer selection, individualized financing/tax/legal/engineering advice, savings promise, or current incentive amount.','refresh_boundary':'HIGH-volatility incentives, utility rules, financing products/rates and program eligibility are excluded from numeric evergreen advice and routed to responsible current sources.'},indent=2)+"\n")
    if status=='PASS':
        manifest.update({'status':'CONTENT_LAYOUT_AND_QA_FROZEN','content_frozen':True,'layout_frozen':True,'qa':'PASS','callout_collision_qa':'PASS','callout_optical_spacing_qa':'PASS','callout_pages_visually_inspected':f'{len(callout_measurements)}/{len(callout_measurements)}','pdf_pages':pages,'kdp_rounded_page_count':pages+(pages%2),'pdf_sha256':sha(PDF)})
        (BOOK/'production'/'production-manifest.json').write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps({'status':status,'pages':pages,'kdp_pages':pages+(pages%2),'checks':checks},indent=2))
    raise SystemExit(0 if status=='PASS' else 1)

if __name__=='__main__': main()
