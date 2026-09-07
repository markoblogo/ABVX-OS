#!/usr/bin/env python3
"""Build RN5-001 paid-value prototype #2. This is not the full book."""
from pathlib import Path
import json, re
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen.canvas import Canvas
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'book-radar/runs/rn5/representative-sample-v2'
BASE.mkdir(parents=True,exist_ok=True)
PDF=BASE/'solar-proposal-decoder-buyer-decision-system-prototype-v2.pdf'
QA=BASE/'prototype-v2-qa.json'
W,H=letter; M=48
NAVY=HexColor('#17324D'); BLUE=HexColor('#246A8D'); GOLD=HexColor('#E2A33B')
PALE=HexColor('#F2F5F6'); MID=HexColor('#D6E0E5'); INK=HexColor('#17242D'); GRAY=HexColor('#53616C'); RED=HexColor('#9B3B32'); GREEN=HexColor('#397153')

def wrap(c,text,font,size,width):
    words=text.split(); lines=[]; line=''
    for word in words:
        trial=(line+' '+word).strip()
        if c.stringWidth(trial,font,size)<=width: line=trial
        else:
            if line: lines.append(line)
            line=word
    if line: lines.append(line)
    return lines

def text(c,x,y,text,size=10.5,font='Helvetica',color=INK,width=500,leading=None):
    leading=leading or size*1.34; c.setFont(font,size);c.setFillColor(color)
    for line in wrap(c,text,font,size,width): c.drawString(x,y,line);y-=leading
    return y

def header(c,kicker,title,deck=''):
    c.setFillColor(NAVY);c.rect(0,H-62,W,62,fill=1,stroke=0)
    c.setFillColor(GOLD);c.setFont('Helvetica-Bold',8.5);c.drawString(M,H-20,kicker.upper())
    c.setFillColor(white);c.setFont('Helvetica-Bold',19);c.drawString(M,H-45,title)
    y=H-82
    if deck:y=text(c,M,y,deck,10.5,'Helvetica',GRAY,W-2*M,14)-4
    return y

def footer(c,n):
    c.setStrokeColor(MID);c.line(M,28,W-M,28);c.setFillColor(GRAY);c.setFont('Helvetica',7.5)
    c.drawString(M,16,'Synthetic examples only. Independent educational tool; not engineering, financial, tax, or legal advice.')
    c.drawRightString(W-M,16,f'PROTOTYPE 2  |  {n}')

def card(c,y,title,body,h=None,accent=BLUE,label=None):
    lines=[]
    for para in body:
        lines.extend(wrap(c,para,'Helvetica',10.3,W-2*M-30));lines.append('')
    need=34+(len(lines)-1)*14+12; h=h or need
    c.setFillColor(PALE);c.roundRect(M,y-h,W-2*M,h,7,fill=1,stroke=0)
    c.setFillColor(accent);c.rect(M,y-h,5,h,fill=1,stroke=0)
    c.setFillColor(INK);c.setFont('Helvetica-Bold',11.5);c.drawString(M+16,y-21,title)
    if label:c.setFillColor(accent);c.setFont('Helvetica-Bold',8);c.drawRightString(W-M-12,y-20,label)
    ty=y-41;c.setFillColor(INK);c.setFont('Helvetica',10.3)
    for line in lines:
        if line:c.drawString(M+16,ty,line)
        ty-=14
    return y-h-12

def mini(c,x,y,w,title,lines,h=128,accent=BLUE):
    c.setFillColor(PALE);c.roundRect(x,y-h,w,h,7,fill=1,stroke=0);c.setFillColor(accent);c.rect(x,y-h,4,h,fill=1,stroke=0)
    c.setFillColor(INK);c.setFont('Helvetica-Bold',10.5);c.drawString(x+13,y-19,title);ty=y-38
    for line in lines:
        ty=text(c,x+13,ty,line,8.8,'Helvetica',INK,w-25,11.4)-3
    return y-h

def page1(c):
    y=header(c,'The paid-value test','Decode the proposal. Build the decision.','A blank sheet records numbers. This system teaches you where to find them, what they do not prove, and which written questions close the gaps.')
    y=card(c,y,'The buyer’s workflow',['1. FIND — locate the commercial, technical, performance, scope, warranty, and exclusion sections.','2. EXTRACT — copy facts exactly; label sales claims and missing values.','3. NORMALIZE — calculate comparable metrics and separate cash from financing.','4. CHALLENGE — turn ambiguous claims and mismatched assumptions into written questions.','5. DECIDE — preserve the answers, remaining uncertainty, and reason for the choice.'],178)
    y=card(c,y,'What this is not',['Not an installer ranking, savings promise, engineering design, tax calculation, or substitute for the signed contract. It is a buyer-owned method for interrogating competing proposals.'],76,GRAY)
    y=card(c,y,'The output',['One decision packet: original proposal references, normalized comparison, calculations with limitations, scope and warranty gaps, questions sent, answers received, and the decision with its reason.'],88,GREEN)

def page2(c):
    y=header(c,'1 — Real proposal anatomy','A synthetic proposal fragment','The fragment is original and deliberately resembles the information density—not the design—of a typical sales proposal.')
    c.setFillColor(white);c.setStrokeColor(MID);c.roundRect(M,y-520,W-2*M,520,6,fill=1,stroke=1)
    y-=22;c.setFillColor(NAVY);c.setFont('Helvetica-Bold',15);c.drawString(M+18,y,'SUNRIDGE HOME ENERGY — PROPOSAL S-1047');y-=25
    y=text(c,M+18,y,'Prepared for: Jordan Lee  |  Site: 18 Example Street  |  Valid through: October 14',9.3,'Helvetica',GRAY,W-2*M-36,12)-8
    sections=[
      ('A  SYSTEM','8.2 kW DC • 20 × 410 W Helio H410 panels • GridLink X8 inverter'),
      ('B  ESTIMATED PRODUCTION','Year 1: 11,480 kWh • Usage baseline: 11,300 kWh • “102% offset”'),
      ('C  CASH OPTION','$24,600 before any customer-specific incentive or tax treatment'),
      ('D  FINANCE OPTION','$31,980 principal • 4.99% stated APR • 20 years • $211 estimated monthly payment'),
      ('E  INCLUDED SCOPE','Design, permit filing, standard roof mounting, interconnection submission, monitoring setup'),
      ('F  WARRANTY','25-year panel performance; 12-year product; 10-year workmanship; inverter per manufacturer'),
      ('G  ASSUMPTIONS / EXCLUSIONS','No main-panel upgrade, roof repair, trenching, tree work, or utility-required redesign included. Production model assumes current usage and the shade model dated September 12.'),
    ]
    for title_,body in sections:
        c.setFillColor(PALE);c.roundRect(M+16,y-50,W-2*M-32,50,4,fill=1,stroke=0)
        c.setFillColor(BLUE);c.setFont('Helvetica-Bold',8.5);c.drawString(M+27,y-17,title_)
        text(c,M+27,y-34,body,8.7,'Helvetica',INK,W-2*M-54,10.5);y-=58
    c.setFillColor(RED);c.setFont('Helvetica-Bold',9);c.drawString(M+18,y-2,'A PROPOSAL IS AN INDEX OF CLAIMS. THE SIGNED CONTRACT AND LOAN DISCLOSURES CONTROL.')

def page3(c):
    y=header(c,'1 — Extraction','Where each comparison fact lives','Copy the stated value, record its page or section, then mark whether it is a fact, estimate, sales claim, or missing item.')
    items=[('Cash price','Pricing / cash option','Do not substitute “net after incentives.”'),('Financed principal','Loan option or lender disclosure','Compare with cash price; monthly payment is not principal.'),('System size','System summary','Use DC kW unless every proposal clearly uses the same basis.'),('Equipment','Bill of materials','Capture manufacturer and model, not “Tier 1” or “premium.”'),('Production estimate','Performance section','Also capture weather, shade, degradation, and usage assumptions.'),('Scope','Included work / responsibilities','Find permits, panel work, roof work, trenching, monitoring, inspections.'),('Warranty','Warranty schedule','Separate product, performance, workmanship, labor, and responsible party.'),('Exclusions','Fine print / assumptions','Absence is a gap; it is not proof that work is included.')]
    top=y
    for i,(a,b,d) in enumerate(items):
        col=i%2;row=i//2;x=M+col*258;yy=top-row*132
        mini(c,x,yy,246,a,[f'LOOK IN: {b}',d,'VALUE: __________________','SOURCE PAGE: ______  STATUS: ______'],120,GOLD if i in {1,4,7} else BLUE)

def decoder_page(c,n,title,claims):
    y=header(c,'2 — Claim decoder',title,'A claim is not automatically deceptive. Treat it as a prompt to identify the definition, assumptions, responsible party, and controlling document.')
    for claim,meaning,verify,question in claims:
        y=card(c,y,claim,[f'WHAT IT MAY MEAN — {meaning}',f'WHAT TO VERIFY — {verify}',f'QUESTION TO ASK — {question}'],126,GOLD,'CLAIM → VERIFY')
    footer(c,n);c.showPage()

def page6(c):
    y=header(c,'3 — Calculation layer','Four useful comparison metrics','Each metric answers one narrow question. None identifies the “best installer.”')
    metrics=[
      ('Cash cost per watt','cash price ÷ (DC system kW × 1,000)','Useful for price normalization when scope is comparable. Misleading if roof work, batteries, panel upgrades, or other scope differs.'),
      ('Financed premium over cash','(financed principal − cash price) ÷ cash price × 100%','Shows how much larger the starting principal is. It is not total borrowing cost and may mix fees with changed scope.'),
      ('Total scheduled payments','sum of all scheduled payments shown by the lender','Compare the disclosure, not monthly payment × term when payments can change. Does not model early payoff or opportunity cost.'),
      ('Year-1 production per installed kW','estimated annual kWh ÷ DC system kW','Exposes different production assumptions or designs. It is an estimate—not a guarantee, savings figure, or equipment-quality score.')]
    for title,formula,limit in metrics:y=card(c,y,title,[f'FORMULA — {formula}',f'LIMIT — {limit}'],105,BLUE)

def page7(c):
    y=header(c,'3 — Worked calculation','Calculate, then label the limitation','Synthetic Proposal A: $24,600 cash; $31,980 financed principal; 8.2 kW DC; 11,480 kWh estimated Year-1 production; $211 × 240 scheduled payments if fixed.')
    y=card(c,y,'1  Cash cost per watt',['$24,600 ÷ (8.2 × 1,000) = $3.00/W','Interpretation: a price-normalization starting point. Before comparing, remove or separately label batteries, roof work, service upgrades, and other unequal scope.'],96,GREEN)
    y=card(c,y,'2  Financed premium over cash',['($31,980 − $24,600) ÷ $24,600 = 30.0%','Interpretation: the principal starts 30% above the cash price. This does not include interest and does not prove why the difference exists. Ask for a written breakdown.'],105,GOLD)
    y=card(c,y,'3  Total scheduled payments',['$211 × 240 = $50,640 — only if the payment remains fixed for all 240 months.','Interpretation: use the lender’s official total-of-payments disclosure when available. Check expected prepayments, re-amortization, fees, and payment changes.'],105,RED)
    y=card(c,y,'4  Production per installed kW',['11,480 kWh ÷ 8.2 kW = 1,400 kWh per installed kW in Year 1.','Interpretation: compare the underlying shade, weather, orientation, degradation, downtime, and modeling assumptions before treating a higher result as better.'],105,BLUE)

def page8(c):
    y=header(c,'4 — Decision scenario','Three plausible, non-obvious proposals','The purpose is not to pick a winner. It is to reveal what remains incomparable and what must be asked in writing.')
    data=[('A — lowest cash','$24,600 cash • 8.2 kW • 11,480 kWh • $31,980 financed • $211 × 240','Standard scope; panel upgrade excluded. 10-year workmanship. Production intensity: 1,400 kWh/kW.'),('B — higher price, broader scope','$26,400 cash • 8.0 kW • 10,960 kWh • $26,400 financed • $293 × 144','Main-panel allowance included up to $2,000. 15-year workmanship. Production intensity: 1,370 kWh/kW.'),('C — lowest payment, highest estimate','$25,200 cash • 7.6 kW • 11,400 kWh • $28,980 financed • $169 × 300','Roof work excluded. 5-year workmanship. Model uses optimistic shade assumption. Production intensity: 1,500 kWh/kW.')]
    for title,nums,notes in data:y=card(c,y,title,[nums,notes],125,GOLD if title.startswith('C') else BLUE)
    y=card(c,y,'What the headlines do not settle',['A has the lowest cash price, B includes more scope, and C shows the lowest monthly payment and highest production intensity. None of those facts alone resolves financing cost, assumption quality, warranty value, or site fit.'],82,GRAY)

def page9(c):
    y=header(c,'4 — Normalize economics','Price and payment tell different stories','Synthetic arithmetic for comparison practice; lender disclosures control real financing terms.')
    rows=[('Cash cost per watt','A $3.00','B $3.30','C $3.32'),('Financed premium over cash','A 30.0%','B 0.0%','C 15.0%'),('Stated monthly payment','A $211','B $293','C $169'),('Simple scheduled total*','A $50,640','B $42,192','C $50,700')]
    for label,a,b,d in rows:y=card(c,y,label,[f'{a}     |     {b}     |     {d}'],72,GREEN if 'cost per' in label else BLUE)
    y=card(c,y,'Do not rank yet',['The cheapest $/W excludes B’s panel allowance. The lowest payment has the longest term. A’s and C’s simple totals are similar despite different principal and payment. Verify whether every payment is fixed and obtain official credit disclosures.'],105,RED)
    y=text(c,M,y,'*Illustrative monthly payment × stated number of months. Not a substitute for the lender’s Total of Payments disclosure.',8.8,'Helvetica-Oblique',GRAY,W-2*M,12)

def page10(c):
    y=header(c,'4 — Challenge production','A higher estimate may be a different assumption set','Normalize the estimate, then investigate why the estimates differ.')
    y=card(c,y,'Production intensity',['A: 11,480 ÷ 8.2 = 1,400 kWh/kW','B: 10,960 ÷ 8.0 = 1,370 kWh/kW','C: 11,400 ÷ 7.6 = 1,500 kWh/kW'],100,GREEN)
    y=card(c,y,'Possible explanations—not conclusions',['Roof orientation and array placement; shade model; weather data; system losses; clipping; degradation; downtime; DC versus AC capacity; optimism in the model. A higher number can reflect a better design, a different site model, or simply a different assumption.'],112,GOLD)
    y=card(c,y,'Written questions for C',['Please identify the shade study or site model used for the 11,400 kWh estimate.','Please state the weather dataset, first-year system-loss assumption, and annual degradation assumption.','Please provide the production guarantee, if any, and its remedy and exclusions.'],120,BLUE)
    y=card(c,y,'Boundary',['“100% offset” is generally a modeled annual relationship between estimated production and assumed usage. It does not by itself mean a zero utility bill, uninterrupted backup, or identical monthly production.'],84,GRAY)

def page11(c):
    y=header(c,'4 — Compare scope and warranty','Find who pays when reality differs from the headline','A long warranty is useful only when its covered event, exclusions, labor, remedy, and responsible party are clear.')
    y=card(c,y,'Scope differences',['A: standard installation; service upgrade excluded.','B: allowance up to $2,000 for main-panel work; excess not stated.','C: roof work excluded; responsibility for hidden conditions unclear.'],94,BLUE)
    y=card(c,y,'Warranty differences',['A: 25-year performance, 12-year product, 10-year workmanship.','B: manufacturer terms plus 15-year workmanship; labor detail missing.','C: “25-year warranty” headline, but only 5-year workmanship is visible.'],103,GOLD)
    y=card(c,y,'Questions created by the differences',['A — What is the fixed or estimated price if the service panel must be upgraded?','B — What happens above the $2,000 allowance, and who approves a change order?','C — Which 25-year warranty is meant, who administers it, and are diagnosis, labor, shipping, and roof removal included?'],122,GREEN)
    y=card(c,y,'No automatic winner',['Broader scope may justify a higher price; a longer workmanship term may still contain exclusions; a low cash price may remain attractive if excluded work is unnecessary. The system creates comparable evidence, not a universal ranking.'],86,GRAY)

def page12(c):
    y=header(c,'5 — Question generator','Turn every gap into an installer-specific request','A useful question names the exact proposal, states the unresolved field, and asks for a written answer that can be attached to the decision packet.')
    examples=[('GAP','Proposal A excludes a possible panel upgrade; cost unknown.','QUESTION','“For proposal S-1047, please state the price or pricing method for any required main-panel upgrade and confirm whether it would be handled by change order before work begins.”'),('GAP','Proposal B includes a $2,000 allowance; overage process missing.','QUESTION','“Please define what the panel-work allowance covers, who determines any overage, and whether we approve the final amount in writing before installation.”'),('GAP','Proposal C shows 11,400 kWh but does not identify shade inputs.','QUESTION','“Please provide the shade/site report and list the weather, loss, degradation, and downtime assumptions behind the Year-1 estimate.”'),('GAP','“25-year warranty” does not identify coverage.','QUESTION','“Please separate product, performance, workmanship, labor, and roof-penetration coverage, with term, exclusions, remedy, and responsible party for each.”')]
    for i,(g,gap,q,question) in enumerate(examples):y=card(c,y,f'{i+1}  {g}: {gap}',[f'{q}: {question}'],105,GOLD if i%2 else BLUE)

def page13(c):
    y=header(c,'5 — Sendable output','A concise written-question sheet','The buyer can email this page’s content. No downloadable companion is promised; the paperback itself contains the working packet.')
    y=card(c,y,'Subject: Written clarifications for proposal S-1047',['Thank you for the proposal. I am comparing the written scope and assumptions across several offers. Please answer the questions below in writing and identify any answer that changes the quoted price or schedule.'],96,BLUE)
    qs=['1. Confirm the cash price before customer-specific incentives or tax treatment.','2. Confirm the financed principal and provide the lender disclosure showing payment schedule and total of payments.','3. Identify the shade/site model, weather data, loss assumptions, and degradation used for 11,480 kWh.','4. State the price or pricing method for any required main-panel or roof work.','5. Separate product, performance, workmanship, labor, and roof-penetration warranties.','6. List every permit, inspection, interconnection step, correction, and utility fee included or excluded.']
    y=card(c,y,'Questions',qs,216,GREEN)
    y=card(c,y,'Answer log',['Sent: __________  Reply received: __________  Revised proposal attached: YES / NO','Price changed: YES / NO  Scope changed: YES / NO  New unresolved item: __________________________'],82,GOLD)

def page14(c):
    y=header(c,'6 — Final decision packet','The product’s completed output','A decision packet remains useful after the sale because it records what was represented, clarified, revised, accepted, and left uncertain.')
    y=card(c,y,'Packet contents',['Original proposals and version dates; source-page extraction map; normalized cash and financing comparison; calculations and limitations; production assumptions; equipment and scope differences; warranty responsibility map; questions sent; written replies and revised offers; unresolved items; decision and reason.'],120,GREEN)
    y=card(c,y,'Why this is more than a spreadsheet',['A spreadsheet can calculate after you know what to extract. This system supplies the proposal anatomy, definitions, claim decoder, limitation-aware calculations, scenario walkthrough, gap logic, written-question generator, and evidence trail.'],98,BLUE)
    y=card(c,y,'Why this is more than a calculator or comparison site',['A free calculator estimates performance; it does not reconcile the scope and warranty language in your actual offers. A marketplace may standardize quotes from participating installers; this buyer-owned packet works across any proposals and does not require lead submission.'],108,GOLD)
    y=card(c,y,'Natural product architecture',['PAPERBACK-FIRST REFERENCE + WRITE-IN BUYER SYSTEM, approximately 88–112 pages if the full content earns that space. Roughly half teaches extraction, claims, calculations, scope, warranties, and questions; half provides two complete reusable three-quote decision packets. No external download is required or promised.'],112,NAVY)

def build():
    c=Canvas(str(PDF),pagesize=letter)
    makers=[page1,page2,page3]
    for i,fn in enumerate(makers,1):fn(c);footer(c,i);c.showPage()
    decoder_page(c,4,'Price and payment language',[
      ('“Low monthly payment”','A long term, a temporary payment, an expected prepayment, or a financed principal larger than the cash price.','All scheduled payment amounts and dates; term; APR; principal; fees; expected prepayment; re-amortization; official total of payments.','Please provide the lender disclosure and identify every event that changes the payment.'),
      ('“No money down”','No upfront payment; the customer may still take a loan, lease, PPA, lien, or long-term obligation.','Ownership, principal, total payments, escalation, security interest, transfer, payoff, and cancellation terms.','What obligation begins at signing, and what must be paid or transferred if I sell the home?')])
    decoder_page(c,5,'Warranty, offset, scope, and incentive language',[
      ('“25-year warranty”','A performance warranty, product warranty, installer workmanship warranty, or several different terms.','Covered event, term, exclusions, remedy, labor/shipping, roof removal, and responsible company.','Please separate each warranty and identify who pays labor and removal.'),
      ('“100% offset” / “turnkey” / “free battery”','A modeled annual ratio; a broad scope label; or an incentive/discount embedded elsewhere in pricing.','Usage baseline and model assumptions; written included/excluded scope; cash price with and without battery/incentive and eligibility conditions.','Show the calculation or price difference and identify every assumption and exclusion.')])
    for i,fn in enumerate([page6,page7,page8,page9,page10,page11,page12,page13,page14],6):fn(c);footer(c,i);c.showPage()
    c.save()
    reader=PdfReader(str(PDF));texts=[p.extract_text() or '' for p in reader.pages]
    checks={'page_count_14':len(reader.pages)==14,'letter_size':all(abs(float(p.mediabox.width)-612)<.1 and abs(float(p.mediabox.height)-792)<.1 for p in reader.pages),'all_pages_have_footer':all('PROTOTYPE 2' in t for t in texts),'proposal_anatomy':'PROPOSAL S-1047' in texts[1],'red_flag_decoder':'WHAT IT MAY MEAN' in texts[3] and 'WHAT TO VERIFY' in texts[4],'calculation_layer':'Cash cost per watt' in texts[5] and '$3.00/W' in texts[6],'three_quote_scenario':'A — lowest cash' in texts[7] and 'C — lowest payment' in texts[7],'question_generator':'Turn every gap into an installer-specific request' in texts[11],'final_packet':'Packet contents' in texts[13],'free_alternative_differentiation':'Why this is more than a spreadsheet' in texts[13]}
    QA.write_text(json.dumps({'schema_version':'rn5-001-prototype-v2-qa/v1','status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'pages':len(reader.pages),'production_started':False},indent=2)+'\n')
    print(json.dumps({'pdf':str(PDF),'pages':len(reader.pages),'status':'PASS' if all(checks.values()) else 'FAIL'},indent=2))

if __name__=='__main__':build()
