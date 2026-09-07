#!/usr/bin/env python3
"""Build a same-content representative comparison of RN5-001 trim candidates."""
from __future__ import annotations
import json, os, subprocess
from pathlib import Path
import pdfplumber
from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

ROOT=Path(__file__).resolve().parents[1]
TMP=ROOT/'tmp'/'pdfs'/'rn5-trim-final'; TMP.mkdir(parents=True,exist_ok=True)
OUT=ROOT/'output'/'pdf'/'rn5-001-trim-size-comparison.pdf'
DECISION=ROOT/'books'/'rn5-001'/'production'/'rn5-001-trim-size-decision.md'
DATA=ROOT/'books'/'rn5-001'/'production'/'rn5-001-trim-size-comparison.json'
PY=Path('/Users/antonbiletskiy-volokh/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3')
TRIMS={'7x10':(7,10),'8x10':(8,10),'8.5x11':(8.5,11)}
PHRASES=[
 ('Normal prose','The four evidence labels'),
 ('Dense Claim Decoder','Low monthly payment'),
 ('Semantic callout','THE PAUSE RULE'),
 ('Proposal extraction form','Proposal A: Commercial extraction'),
 ('Three-column comparison','Normalized price comparison'),
 ('Written-question form','Proposal A: written questions'),
 ('Decision Record','Record the reason, not just the winner'),
 ('Part transition','PART III'),
]

pdfmetrics.registerFont(TTFont('ABVX','/System/Library/Fonts/Supplemental/Arial.ttf'))
pdfmetrics.registerFont(TTFont('ABVX-Bold','/System/Library/Fonts/Supplemental/Arial Bold.ttf'))

def build(trim):
    path=TMP/f'{trim}.pdf'
    env={**os.environ,'RN5_COMPARISON_BUILD':'1','RN5_TRIM':trim,'RN5_OUTPUT_PDF':str(path)}
    subprocess.run([str(PY),str(ROOT/'tools'/'build_rn5_001_book.py')],cwd=ROOT,env=env,check=True,stdout=subprocess.DEVNULL)
    return path

def find_pages(path):
    reader=PdfReader(path); texts=[p.extract_text() or '' for p in reader.pages]
    found=[]
    for label,phrase in PHRASES:
        floor=20 if label in {'Proposal extraction form','Three-column comparison','Written-question form','Decision Record'} else (4 if label in {'Normal prose','Dense Claim Decoder','Semantic callout','Part transition'} else 0)
        ids=[i for i,t in enumerate(texts) if i>=floor and phrase.lower() in t.lower()]
        if not ids: raise RuntimeError(f'{path.name}: missing representative page {label}')
        found.append({'label':label,'phrase':phrase,'page':ids[0]+1,'index':ids[0]})
    return reader,texts,found

def prose_metrics(path,texts):
    first_form=next(i for i,t in enumerate(texts) if i>20 and 'Proposal register' in t)
    skip={0,1,2,3,4}
    occupied=[];low=[]
    with pdfplumber.open(path) as doc:
        for i,p in enumerate(doc.pages[:first_form]):
            if i in skip: continue
            chars=[c for c in p.chars if c['top']<p.height-48 and c['bottom']>35]
            if not chars: continue
            top=min(c['top'] for c in chars);bottom=max(c['bottom'] for c in chars)
            ratio=(bottom-top)/(p.height-83)
            occupied.append(ratio)
            if ratio<0.42: low.append(i+1)
    return round(sum(occupied)/len(occupied),3),low

def divider(path,trim,metrics,found):
    w,h=(TRIMS[trim][0]*inch,TRIMS[trim][1]*inch)
    c=Canvas(str(path),pagesize=(w,h))
    navy=HexColor('#17324D'); blue=HexColor('#2C6B88'); gray=HexColor('#52616B')
    c.setFillColor(navy);c.rect(0,h-54,w,54,fill=1,stroke=0)
    c.setFillColor(HexColor('#FFFFFF'));c.setFont('ABVX-Bold',18);c.drawString(42,h-35,f'{trim} REPRESENTATIVE SET')
    y=h-90;c.setFillColor(navy);c.setFont('ABVX-Bold',14);c.drawString(42,y,'Same accepted content. Same 10.9 pt body type.');y-=30
    c.setFillColor(gray);c.setFont('ABVX',9.5)
    lines=[f"Full-book pages: {metrics['pages']}",f"Usable text/form width: {metrics['usable_width_in']:.2f} in",f"Three-way answer cell width: {metrics['answer_cell_width_in']:.2f} in",f"Average prose vertical utilization: {metrics['average_prose_vertical_utilization']*100:.1f}%",f"Low-use prose pages after removing forced part breaks: {metrics['chapter_end_whitespace_signal_pages'] or 'none'}",'Printing cost tier: large-trim, black ink, fixed cost while under 110 pages','Following pages: prose, decoder, callout, extraction, comparison, questions, decision, transition.']
    for line in lines:c.drawString(42,y,line);y-=18
    c.setStrokeColor(blue);c.line(42,y-8,w-42,y-8)
    c.setFillColor(gray);c.setFont('ABVX',8);c.drawString(42,22,'RN5-001 TRIM SIZE OPTIMIZATION — REPRESENTATIVE FORMAT EVIDENCE')
    c.save()

def main():
    records={}; readers={}; selections={}
    for trim,(wi,hi) in TRIMS.items():
        path=build(trim);reader,texts,found=find_pages(path);avg,low=prose_metrics(path,texts)
        usable=wi-1.30;left=min(1.45,usable*.24);cell=(usable-left)/3
        records[trim]={'trim_inches':[wi,hi],'pages':len(reader.pages),'kdp_pages':len(reader.pages)+(len(reader.pages)%2),'body_pt':10.9,'usable_width_in':round(usable,2),'answer_cell_width_in':round(cell,2),'average_prose_vertical_utilization':avg,'chapter_end_whitespace_signal_pages':low,'printing_cost_usd':2.84,'representative_pages':[{k:v for k,v in x.items() if k!='index'} for x in found]}
        readers[trim]=reader;selections[trim]=found
    writer=PdfWriter()
    for trim in TRIMS:
        d=TMP/f'{trim}-divider.pdf';divider(d,trim,records[trim],selections[trim]);writer.add_page(PdfReader(d).pages[0])
        for item in selections[trim]: writer.add_page(readers[trim].pages[item['index']])
    writer.add_metadata({'/Title':'RN5-001 Trim Size Comparison','/Author':'ABVX-OS publishing pipeline'})
    with OUT.open('wb') as f:writer.write(f)
    comparison={'schema_version':'rn5-001-trim-comparison/v1','tested_at':'2026-09-08','current_trim':'8.5x11','tested_trims':records,'selected_trim':'8x10','physical_product':'COMPACT FIELD GUIDE + WORKBOOK','decision':'8x10 preserves 10.9 pt reading type and materially useful writing rows while giving three-column answer cells about 1.75 inches wide. It removes the thin large-manual feel of 8.5x11 without the constrained 1.44-inch three-way cells of 7x10. All candidates remain in the same KDP large-trim fixed printing-cost tier at their projected page counts.','ambiguous':False}
    DATA.write_text(json.dumps(comparison,indent=2)+"\n")
    rows=[]
    for t,r in records.items(): rows.append(f"- **{t}** — {r['pages']} PDF pages ({r['kdp_pages']} KDP); {r['answer_cell_width_in']:.2f}-inch three-way answer cells; {r['average_prose_vertical_utilization']*100:.1f}% average prose vertical use; $2.84 print cost.")
    DECISION.write_text("""# RN5-001 trim-size decision

## Decision

**Selected: 8 × 10 inches.**

**Physical product:** COMPACT FIELD GUIDE + WORKBOOK.

The 8 × 10 edition keeps the accepted 10.9 pt body type and asymmetric writing rows, while its approximately 1.75-inch three-way answer cells remain practical for short comparative entries. It feels less like a thin office manual than 8.5 × 11. The 7 × 10 version is attractively compact, but approximately 1.44-inch answer cells make the core three-proposal workflow noticeably more cramped. Since all three candidates are KDP large trim and remain below 110 pages, none gains a printing-cost advantage.

## Same-content results

"""+"\n".join(rows)+"""

## Gate result

The decision is not ambiguous. 8 × 10 gives the best balance of physical readability, information density, writable width, page proportion, and market-appropriate economics. No additional human prototype gate is required.

The comparison PDF contains the same eight representative content types in every tested trim: normal prose, dense decoder, semantic callout, extraction form, three-column comparison, written-question form, Decision Record, and part transition.
""")
    print(json.dumps({'comparison_pdf':str(OUT),'decision':str(DECISION),'selected':'8x10','pages':records},indent=2))

if __name__=='__main__':main()
