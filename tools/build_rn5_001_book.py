#!/usr/bin/env python3
"""Build the RN5-001 paperback production master and machine-readable ledgers."""
from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
from pathlib import Path

from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / "books" / "rn5-001"
MANUSCRIPT = BOOK / "manuscript" / "solar-proposal-decoder-buyer-decision-system.md"
PDF = ROOT / "output" / "pdf" / "solar-proposal-decoder-buyer-decision-system-paperback.pdf"
MASTER = BOOK / "production" / "solar-proposal-decoder-production-master.pdf"
PROD = BOOK / "production"
DATA = BOOK / "data"
QA = BOOK / "qa"

W, H = letter
INNER = 0.72 * inch
OUTER = 0.62 * inch
TOP = 0.62 * inch
BOTTOM = 0.62 * inch
INK = HexColor("#1B2630")
NAVY = HexColor("#17324D")
BLUE = HexColor("#2C6B88")
PALE = HexColor("#EEF3F5")
MID = HexColor("#CCD8DD")
GRAY = HexColor("#52616B")
LIGHT = HexColor("#F7F8F8")


def register_fonts() -> None:
    base = Path("/System/Library/Fonts/Supplemental")
    fonts = {
        "ABVX": base / "Arial.ttf",
        "ABVX-Bold": base / "Arial Bold.ttf",
        "ABVX-Italic": base / "Arial Italic.ttf",
        "ABVX-BoldItalic": base / "Arial Bold Italic.ttf",
    }
    for name, path in fonts.items():
        pdfmetrics.registerFont(TTFont(name, str(path)))
    pdfmetrics.registerFontFamily(
        "ABVX", normal="ABVX", bold="ABVX-Bold", italic="ABVX-Italic", boldItalic="ABVX-BoldItalic"
    )


register_fonts()


class BookDocTemplate(BaseDocTemplate):
    def __init__(self, filename: str):
        super().__init__(
            filename,
            pagesize=letter,
            leftMargin=INNER,
            rightMargin=OUTER,
            topMargin=TOP,
            bottomMargin=BOTTOM,
            title="Solar Proposal Decoder",
            author="Casey Rowan",
            subject="Independent homeowner proposal-comparison and decision system",
        )
        frame = Frame(INNER, BOTTOM, W - INNER - OUTER, H - TOP - BOTTOM, id="normal", showBoundary=0)
        self.addPageTemplates(PageTemplate(id="book", frames=[frame], onPage=self.decorate))

    def decorate(self, canvas, doc):
        n = canvas.getPageNumber()
        if n == 1:
            return
        canvas.saveState()
        canvas.setStrokeColor(MID)
        canvas.setLineWidth(0.45)
        canvas.line(INNER, 43, W - OUTER, 43)
        canvas.setFont("ABVX", 7.4)
        canvas.setFillColor(GRAY)
        canvas.drawString(INNER, 30, "SOLAR PROPOSAL DECODER")
        canvas.drawRightString(W - OUTER, 30, str(n))
        canvas.restoreState()

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph):
            style = flowable.style.name
            if style in {"Part", "H1", "H2"}:
                level = {"Part": 0, "H1": 0, "H2": 1}[style]
                text = flowable.getPlainText()
                key = f"h-{self.page}-{abs(hash(text))}"
                self.canv.bookmarkPage(key)
                self.canv.addOutlineEntry(text, key, level=level, closed=False)
                self.notify("TOCEntry", (level, text, self.page, key))


styles = getSampleStyleSheet()
BODY = ParagraphStyle("Body", fontName="ABVX", fontSize=10.8, leading=15.2, textColor=INK, spaceAfter=7.5)
BODY_FIRST = ParagraphStyle("BodyFirst", parent=BODY, firstLineIndent=14)
SMALL = ParagraphStyle("Small", parent=BODY, fontSize=8.5, leading=11.6, textColor=GRAY)
BULLET = ParagraphStyle("Bullet", parent=BODY, leftIndent=15, firstLineIndent=-9, bulletIndent=4, spaceAfter=4.5)
H1 = ParagraphStyle("H1", fontName="ABVX-Bold", fontSize=20, leading=23, textColor=NAVY, spaceBefore=12, spaceAfter=10)
H2 = ParagraphStyle("H2", fontName="ABVX-Bold", fontSize=14.5, leading=18, textColor=NAVY, spaceBefore=11, spaceAfter=6)
H3 = ParagraphStyle("H3", fontName="ABVX-Bold", fontSize=11.4, leading=14, textColor=BLUE, spaceBefore=8, spaceAfter=4)
PART = ParagraphStyle("Part", fontName="ABVX-Bold", fontSize=22, leading=26, textColor=NAVY, spaceBefore=30, spaceAfter=14)
QUOTE = ParagraphStyle("Quote", parent=BODY, leftIndent=18, rightIndent=10, borderColor=BLUE, borderWidth=1.2, borderPadding=10, backColor=PALE, spaceBefore=7, spaceAfter=10)
CELL = ParagraphStyle("Cell", fontName="ABVX", fontSize=8.3, leading=10.2, textColor=INK)
CELL_B = ParagraphStyle("CellB", parent=CELL, fontName="ABVX-Bold")
FORM_LABEL = ParagraphStyle("FormLabel", fontName="ABVX-Bold", fontSize=8.6, leading=10.4, textColor=NAVY)
FORM_TEXT = ParagraphStyle("FormText", fontName="ABVX", fontSize=8.2, leading=10.2, textColor=INK)


def P(text: str, style=BODY):
    text = html.escape(text).replace("-&gt;", "→")
    return Paragraph(text, style)


def title_page():
    return [
        Spacer(1, 0.55 * inch),
        HRFlowable(width="100%", thickness=8, color=NAVY, spaceAfter=28),
        Paragraph("SOLAR<br/>PROPOSAL<br/>DECODER", ParagraphStyle("Title", fontName="ABVX-Bold", fontSize=34, leading=36, textColor=NAVY)),
        Spacer(1, 18),
        Paragraph("A Homeowner's System for Comparing Quotes, Financing, Production Claims, Scope, and Warranties Before Signing", ParagraphStyle("Subtitle", fontName="ABVX", fontSize=16, leading=21, textColor=BLUE, spaceAfter=32)),
        Table([[P("FIND", CELL_B), P("EXTRACT", CELL_B), P("NORMALIZE", CELL_B), P("CHALLENGE", CELL_B)],
               [P("ASK", CELL_B), P("VERIFY", CELL_B), P("DOCUMENT", CELL_B), P("DECIDE", CELL_B)]],
              colWidths=[(W-INNER-OUTER)/4]*4, rowHeights=[34,34],
              style=TableStyle([("BACKGROUND",(0,0),(-1,0),PALE),("BACKGROUND",(0,1),(-1,1),LIGHT),("GRID",(0,0),(-1,-1),0.5,MID),("ALIGN",(0,0),(-1,-1),"CENTER"),("VALIGN",(0,0),(-1,-1),"MIDDLE")])) ,
        Spacer(1, 32),
        Paragraph("CASEY ROWAN", ParagraphStyle("Author", fontName="ABVX-Bold", fontSize=12, leading=15, textColor=INK)),
        Spacer(1, 6),
        P("Independent consumer study aid", SMALL),
        Spacer(1, 0.65 * inch),
        HRFlowable(width="100%", thickness=1.2, color=BLUE),
        PageBreak(),
    ]


def reader_notice(text: str):
    return [
        Paragraph("READER NOTICE", PART),
        P("Copyright © 2026 Casey Rowan. All rights reserved.", SMALL),
        Spacer(1, 5),
        *parse_lines(text.splitlines()[2:]),
        Spacer(1, 8),
        P("Edition 1.0 · Source refresh: September 7, 2026", SMALL),
        PageBreak(),
    ]


def toc_page():
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle("TOC0", fontName="ABVX-Bold", fontSize=9.2, leading=12.4, textColor=NAVY, leftIndent=0, firstLineIndent=0, spaceBefore=2),
        ParagraphStyle("TOC1", fontName="ABVX", fontSize=8.4, leading=10.8, textColor=INK, leftIndent=14, firstLineIndent=0),
    ]
    return [Paragraph("CONTENTS", PART), toc, PageBreak()]


def parse_lines(lines: list[str]):
    out = []
    para = []
    quote = []

    def flush_para():
        nonlocal para
        if para:
            out.append(P(" ".join(x.strip() for x in para), BODY_FIRST))
            para = []

    def flush_quote():
        nonlocal quote
        if quote:
            text = "<br/>".join(html.escape(x.lstrip("> ")) for x in quote if x.strip("> "))
            out.append(Paragraph(text, QUOTE))
            quote = []

    i = 0
    while i < len(lines):
        raw = lines[i].rstrip()
        s = raw.strip()
        if s.startswith("[WORKSHEET:"):
            flush_para(); flush_quote()
            out.extend(worksheet(s[11:-1]))
        elif s.startswith(">"):
            flush_para(); quote.append(s)
        elif not s:
            flush_para(); flush_quote()
        elif s == "---":
            flush_para(); flush_quote(); out.append(Spacer(1, 5)); out.append(HRFlowable(width="100%", thickness=.7, color=MID, spaceAfter=6))
        elif s.startswith("# PART"):
            flush_para(); flush_quote(); out.extend([PageBreak(), Paragraph(html.escape(s[2:]), PART)])
        elif s.startswith("# "):
            flush_para(); flush_quote(); out.append(Paragraph(html.escape(s[2:]), H1))
        elif s.startswith("## "):
            flush_para(); flush_quote(); out.append(Paragraph(html.escape(s[3:]), H2))
        elif s.startswith("### "):
            flush_para(); flush_quote(); out.append(Paragraph(html.escape(s[4:]), H3))
        elif re.match(r"^[-*] ", s):
            flush_para(); flush_quote(); out.append(Paragraph("• " + html.escape(s[2:]), BULLET))
        elif re.match(r"^\d+\. ", s):
            flush_para(); flush_quote(); out.append(Paragraph(html.escape(s), BULLET))
        elif s.isupper() and len(s) < 90:
            flush_para(); flush_quote(); out.append(Paragraph(html.escape(s), H3))
        else:
            flush_quote(); para.append(s)
        i += 1
    flush_para(); flush_quote()
    return out


def line_rows(labels, height=25):
    return [[P(label, FORM_LABEL), ""] for label in labels], [1.65*inch, 5.15*inch], [height]*len(labels)


def form_table(labels, heights=None, widths=None):
    rows = [[P(label, FORM_LABEL), ""] for label in labels]
    heights = heights or [27]*len(rows)
    widths = widths or [1.75*inch, 5.05*inch]
    return Table(rows, colWidths=widths, rowHeights=heights, repeatRows=0,
                 style=TableStyle([("GRID",(0,0),(-1,-1),.55,MID),("BACKGROUND",(0,0),(0,-1),PALE),("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),7),("RIGHTPADDING",(0,0),(-1,-1),7),("TOPPADDING",(0,0),(-1,-1),6)]))


def matrix(title, rows, left=1.75*inch, row_h=38):
    data = [[P("FIELD", CELL_B), P("PROPOSAL A", CELL_B), P("PROPOSAL B", CELL_B), P("PROPOSAL C", CELL_B)]]
    data += [[P(r, FORM_LABEL), "", "", ""] for r in rows]
    return [Paragraph(title, H2), Table(data, colWidths=[left]+[(W-INNER-OUTER-left)/3]*3, rowHeights=[26]+[row_h]*len(rows), repeatRows=1,
      style=TableStyle([("GRID",(0,0),(-1,-1),.55,MID),("BACKGROUND",(0,0),(-1,0),NAVY),("TEXTCOLOR",(0,0),(-1,0),colors.white),("BACKGROUND",(0,1),(0,-1),PALE),("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),5),("TOPPADDING",(0,0),(-1,-1),5)]))]


def worksheet(name: str):
    common = [P("Write the exact stated value and its proposal page/section. Use NOT LOCATED rather than guessing.", SMALL)]
    if name == "proposal-register":
        return [PageBreak(), Paragraph("Proposal register", H1), *common, form_table(["Property / project","Proposal A — company, ID, date","Proposal B — company, ID, date","Proposal C — company, ID, date","Decision deadline claimed","My actual decision deadline","Files saved at / folder","People included in review"],[35,48,48,48,35,35,35,35])]
    if name == "document-inventory":
        return [PageBreak(), Paragraph("Document inventory", H1), P("Mark RECEIVED, REQUESTED, N/A, or NOT LOCATED for each proposal.", SMALL), *matrix("Documents supplied",["Full proposal + version date","Installation contract","Cash-price page","Lender disclosure / agreement","Lease or PPA agreement","System layout","Equipment datasheets","Production / shade report","Warranty documents","Scope + exclusions","Cancellation / transfer terms"],1.55*inch,31)]
    if name.startswith("extract-"):
        letter_name = name[-1].upper()
        pages=[]
        groups=[
            ("Commercial extraction",["Transaction type","Gross cash price","Discounts / adders","Financed principal","APR and term","Payment schedule","Expected prepayment / change","Lease/PPA rate + escalator","Cancellation / transfer"]),
            ("System and production extraction",["DC system size","Module make/model/count","Inverter make/model/AC size","Battery model/capability","Year-1 production","Usage baseline / offset","Shade/weather source","Loss + degradation assumptions","Guarantee + remedy"]),
            ("Scope and warranty extraction",["Roof / structural","Electrical / service","Permits / inspections","Interconnection / utility","Trenching / site work","Allowances / change orders","Product/performance warranties","Workmanship / roof coverage","Labor / responsible party"]),
        ]
        for idx,(title,labels) in enumerate(groups):
            pages.extend([PageBreak(),Paragraph(f"Proposal {letter_name}: {title}", H1), *common, form_table(labels,[47]*len(labels))])
        return pages
    if name == "price-comparison":
        return [PageBreak(),*matrix("Normalized price comparison",["Gross cash price","DC system watts","Raw cash $/W","Battery / unequal scope","Adjusted view (labeled)","Deposit / milestones","Largest price contingency","Source references"],1.55*inch,43)]
    if name == "financing-comparison":
        return [PageBreak(),*matrix("Financing / contract comparison",["Amount financed / principal","Difference vs cash","APR","Term","Payment levels + dates","Expected prepayment","Official total of payments","Fees / balloon","Security interest","Early payoff","Sale / transfer","Source references"],1.62*inch,34)]
    if name == "system-comparison":
        return [PageBreak(),*matrix("System comparison",["DC / AC capacity","Modules","Inverter / optimizers","Battery / backup loads","Mounting / layout","Monitoring","Substitution clause","Function that matters","Source references"],1.58*inch,41)]
    if name == "production-comparison":
        return [PageBreak(),*matrix("Production-model comparison",["Year-1 kWh","kWh per installed kW","Usage baseline","Offset definition","Shade / site source","Weather source","Loss assumptions","Degradation / availability","Utility/export assumptions","Guarantee + remedy","Unresolved difference"],1.62*inch,36)]
    if name == "scope-comparison":
        return [PageBreak(),*matrix("Scope and responsibility",["Roof / reroofing","Structural work","Main panel / service","Trenching / conduit","Permits / corrections","Inspection / rework","Interconnection / utility","HOA / other approvals","Monitoring / commissioning","Exclusions / allowances","Change-order control"],1.62*inch,36)]
    if name == "warranty-comparison":
        return [PageBreak(),*matrix("Warranty responsibility map",["Module product","Module performance","Inverter / optimizer","Battery","Installer workmanship","Roof penetrations","Production guarantee","Labor / diagnosis","Shipping / removal","Transfer / registration","Responsible company"],1.62*inch,36)]
    if name.startswith("questions-"):
        letter_name=name[-1].upper(); rows=[]
        for i in range(1,7):
            rows.append([P(f"{i}. GAP / SOURCE",FORM_LABEL),"",P("QUESTION / DOCUMENT REQUEST",FORM_LABEL),""])
        data=[]
        for r in rows:
            data.append(r[:2]); data.append(r[2:])
        return [PageBreak(),Paragraph(f"Proposal {letter_name}: written questions",H1),P("Name the proposal and source. Ask for a number, definition, responsibility, or controlling document.",SMALL),Table(data,colWidths=[1.35*inch,5.45*inch],rowHeights=[24,49]*6,style=TableStyle([("GRID",(0,0),(-1,-1),.55,MID),("BACKGROUND",(0,0),(0,-1),PALE),("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),6),("TOPPADDING",(0,0),(-1,-1),5)]))]
    if name == "answer-log":
        return [PageBreak(),*matrix("Answer and revision log",["Question ID","Sent / received","Answer status","Written answer source","Price effect","Scope/design effect","Revised document + date","Still unresolved"],1.45*inch,43)]
    if name == "pause-check":
        labels=["Transaction / owner clear","Cash vs financed basis clear","All payment changes clear","Incentive assumptions separated","Exact system identified","Production differences explained","Roof/electrical exposure clear","Scope/change orders clear","Warranty responsibility clear","Transfer/cancellation clear","Conflicts resolved in writing"]
        data=[[P("CHECK",CELL_B),P("YES / NO",CELL_B),P("EVIDENCE OR REQUIRED ACTION",CELL_B)]]+[[P(x,FORM_LABEL),"",""] for x in labels]
        return [PageBreak(),Paragraph("Pause-condition review",H1),P("A NO does not automatically reject the proposal. It means the decision packet is incomplete.",SMALL),Table(data,colWidths=[2.25*inch,.8*inch,3.75*inch],rowHeights=[27]+[37]*len(labels),style=TableStyle([("GRID",(0,0),(-1,-1),.55,MID),("BACKGROUND",(0,0),(-1,0),NAVY),("TEXTCOLOR",(0,0),(-1,0),colors.white),("BACKGROUND",(0,1),(0,-1),PALE),("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),6),("TOPPADDING",(0,0),(-1,-1),5)]))]
    if name == "decision-record":
        return [PageBreak(),Paragraph("Decision record",H1),P("Record the reason, not just the winner. Acknowledge remaining uncertainty.",SMALL),form_table(["Decision date","Selected proposal / no decision","Transaction type","Main reasons","Trade-offs accepted","Material facts relied on","Documents controlling decision","Remaining uncertainty","Independent advice obtained","Next action / deadline"],[30,38,30,68,60,68,48,60,42,42]),Spacer(1,8),P("This record documents a process; it does not guarantee performance, savings, service, or legal outcome.",SMALL)]
    return []


def build_ledgers():
    sources = [
        {"id":"DOE-INSTALLER","authority":"U.S. Department of Energy","title":"Decisions, Decisions: Choosing a Solar Installer","url":"https://www.energy.gov/cmei/systems/articles/decisions-decisions-choosing-solar-installer","checked":"2026-09-07","supports":["compare several bids","installer transparency and credentials","roof questions","cash cost per watt"]},
        {"id":"DOE-HOME","authority":"U.S. Department of Energy","title":"Homeowner's Guide to Solar","url":"https://www.energy.gov/cmei/systems/homeowners-guide-solar","checked":"2026-09-07","supports":["production estimates","finance-model overview","current-program refresh warning"]},
        {"id":"DOE-BID","authority":"U.S. Department of Energy","title":"WAP Solar Bid Request Template","url":"https://www.energy.gov/sites/default/files/2024-02/wap-solar-bid-request-template_022624.pdf","checked":"2026-09-07","supports":["proposal field anatomy","system, price, production, scope and warranty fields"]},
        {"id":"CFPB-SOLAR","authority":"Consumer Financial Protection Bureau","title":"Issue Spotlight: Solar Financing","url":"https://www.consumerfinance.gov/data-research/research-reports/issue-spotlight-solar-financing/","checked":"2026-09-07","supports":["cash versus financed principal","fees and markups","tax-credit assumptions","expected prepayments","re-amortization","uncertain savings"]},
        {"id":"FTC-HOME","authority":"Federal Trade Commission","title":"Solar Power for Your Home","url":"https://consumer.ftc.gov/articles/solar-power-your-home","checked":"2026-09-07","supports":["utility fixed charges","bid comparison","leases and PPAs","warranties","repairs","transfer and contracts"]},
        {"id":"FTC-SCAM","authority":"Federal Trade Commission","title":"Solar energy is rising in popularity. So are the scams","url":"https://consumer.ftc.gov/consumer-alerts/2024/09/solar-energy-rising-popularity-so-are-scams","checked":"2026-09-07","supports":["pressure tactics","unsupported government/free claims","review before signing"]},
        {"id":"NREL-PVWATTS","authority":"National Renewable Energy Laboratory","title":"PVWatts Calculator and technical documentation","url":"https://pvwatts.nrel.gov/","checked":"2026-09-07","supports":["production estimate purpose","input and loss categories"]},
        {"id":"IRS-REFRESH","authority":"Internal Revenue Service","title":"Residential Clean Energy Credit","url":"https://www.irs.gov/credits-deductions/residential-clean-energy-credit","checked":"2026-09-07","supports":["incentive volatility only"],"note":"Book states no current percentage or eligibility rule; consumer must verify current personal treatment."},
    ]
    claims = [
        {"id":"C01","claim":"DOE recommends comparing quotes and describes cash cost per watt as cost divided by capacity in watts.","sources":["DOE-INSTALLER"],"volatility":"LOW","status":"VERIFIED"},
        {"id":"C02","claim":"CFPB documents solar-specific loan cases where financed principal includes fees or markups above cash price.","sources":["CFPB-SOLAR"],"volatility":"MEDIUM","status":"VERIFIED"},
        {"id":"C03","claim":"Some solar loans can assume a large prepayment and later payment change or re-amortization.","sources":["CFPB-SOLAR"],"volatility":"MEDIUM","status":"VERIFIED"},
        {"id":"C04","claim":"Personal tax benefit is not guaranteed merely because a proposal assumes one.","sources":["CFPB-SOLAR","IRS-REFRESH"],"volatility":"HIGH","status":"VERIFIED_WITH_REFRESH_BOUNDARY"},
        {"id":"C05","claim":"FTC consumer guidance distinguishes purchase, lease, and PPA structures and advises detailed bid/contract comparison.","sources":["FTC-HOME"],"volatility":"LOW","status":"VERIFIED"},
        {"id":"C06","claim":"Utility fixed charges can remain even when solar reduces purchased kWh.","sources":["FTC-HOME"],"volatility":"HIGH_LOCAL","status":"VERIFIED_GENERAL_ONLY"},
        {"id":"C07","claim":"PVWatts estimates production for grid-connected PV systems and models multiple system-loss categories.","sources":["NREL-PVWATTS"],"volatility":"LOW","status":"VERIFIED"},
        {"id":"C08","claim":"DOE advises asking about roof condition, repairs, damage/leak responsibility, installer transparency and warranty coverage.","sources":["DOE-INSTALLER"],"volatility":"LOW","status":"VERIFIED"},
        {"id":"C09","claim":"A government bid template demonstrates the practical relevance of defined system, production, price, scope and warranty fields.","sources":["DOE-BID"],"volatility":"LOW","status":"VERIFIED"},
        {"id":"C10","claim":"All prices, equipment, companies and worked scenarios in the book are synthetic.","sources":[],"volatility":"NONE","status":"AUTHOR_CONTROLLED"},
        {"id":"C11","claim":"Federal, state, utility, incentive and financing specifics require refresh rather than evergreen numeric advice.","sources":["IRS-REFRESH","DOE-HOME","CFPB-SOLAR"],"volatility":"HIGH","status":"CONTROLLED_BY_EXCLUSION_AND_REFRESH"},
    ]
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA/"source-ledger.json").write_text(json.dumps({"schema_version":"rn5-001-source-ledger/v1","checked":"2026-09-07","sources":sources},indent=2)+"\n")
    (DATA/"claim-ledger.json").write_text(json.dumps({"schema_version":"rn5-001-claim-ledger/v1","claims":claims},indent=2)+"\n")
    (DATA/"volatility-ledger.json").write_text(json.dumps({"schema_version":"rn5-001-volatility-ledger/v1","high_volatility":["federal tax incentives","state and local incentives","utility tariffs and export compensation","net-metering rules","financing products and rates","program eligibility"],"manuscript_policy":"No current numeric advice. Verify directly with responsible authority or provider before reliance.","prepublication_refresh_required":True},indent=2)+"\n")


def build():
    for d in (PDF.parent, PROD, DATA, QA): d.mkdir(parents=True, exist_ok=True)
    raw = MANUSCRIPT.read_text()
    blocks = [b.strip() for b in raw.split("\n---\n")]
    story = []
    story.extend(title_page())
    story.extend(reader_notice(blocks[1]))
    story.extend(toc_page())
    story.extend(parse_lines("\n---\n".join(blocks[2:]).splitlines()))
    doc = BookDocTemplate(str(PDF))
    doc.multiBuild(story)
    embedded = PDF.with_name(PDF.stem + "-embedded.pdf")
    subprocess.run([
        "gs", "-q", "-dNOPAUSE", "-dBATCH", "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4", "-dEmbedAllFonts=true", "-dSubsetFonts=true",
        "-dPDFSETTINGS=/prepress", f"-sOutputFile={embedded}", str(PDF)
    ], check=True)
    embedded.replace(PDF)
    shutil.copyfile(PDF, MASTER)
    build_ledgers()
    reader = PdfReader(str(PDF))
    words = len(re.findall(r"\b[A-Za-z0-9][A-Za-z0-9'/-]*\b", raw))
    pages = len(reader.pages)
    manifest = {
        "schema_version":"rn5-001-production-manifest/v1",
        "status":"CONTENT_AND_LAYOUT_BUILT_AWAITING_QA",
        "content_version":"RN5-001-v1.0",
        "title":"Solar Proposal Decoder",
        "subtitle":"A Homeowner's System for Comparing Quotes, Financing, Production Claims, Scope, and Warranties Before Signing",
        "author":"Casey Rowan",
        "format":"paperback",
        "trim_inches":[8.5,11],
        "bleed":False,
        "ink":"black and white",
        "paper":"white",
        "binding":"paperback",
        "pages":pages,
        "word_count":words,
        "body_font":"Arial embedded",
        "body_size_pt":10.8,
        "minimum_margin_inches":0.62,
        "manuscript":str(MANUSCRIPT.relative_to(ROOT)),
        "paperback_pdf":str(PDF.relative_to(ROOT)),
        "production_master":str(MASTER.relative_to(ROOT)),
        "kindle":"NOT_JUSTIFIED_PENDING_FORMAT_GATE_RECORD",
        "synthetic_examples_only":True,
    }
    (PROD/"production-manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps(manifest,indent=2))


if __name__ == "__main__":
    build()
