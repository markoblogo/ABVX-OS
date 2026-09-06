#!/usr/bin/env python3
"""Build the deterministic RN2-037 8x10-inch visual prototype."""

from pathlib import Path

from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.pagesizes import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas


OUT = Path(__file__).resolve().parents[1] / "output" / "pdf" / "rn2-037-visual-prototype.pdf"
W, H = 8 * inch, 10 * inch
INK = HexColor("#15222A")
MID = HexColor("#55666F")
LIGHT = HexColor("#E8EEF0")
ACCENT = HexColor("#D9E8E2")
ACCENT2 = HexColor("#F2E4C7")


def wrap(c, text, width, font="Helvetica", size=11):
    words, lines, line = text.split(), [], ""
    for word in words:
        trial = (line + " " + word).strip()
        if stringWidth(trial, font, size) <= width:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def text(c, body, x, y, width, size=11, leading=15, font="Helvetica", color=INK):
    c.setFillColor(color)
    c.setFont(font, size)
    for paragraph in body.split("\n"):
        if not paragraph:
            y -= leading * .55
            continue
        for line in wrap(c, paragraph, width, font, size):
            c.drawString(x, y, line)
            y -= leading
    return y


def header(c, n, title, eyebrow="VISUAL CRAM MAP · PROTOTYPE"):
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(44, H - 38, eyebrow)
    c.setStrokeColor(LIGHT)
    c.line(44, H - 45, W - 44, H - 45)
    c.setFont("Helvetica-Bold", 23)
    y = H - 76
    for line in wrap(c, title, W - 88, "Helvetica-Bold", 23):
        c.drawString(44, y, line)
        y -= 27
    c.setFont("Helvetica", 8)
    c.setFillColor(MID)
    c.drawRightString(W - 44, 25, f"{n} / 14")
    return y - 8


def tag(c, label, x, y, width=None):
    width = width or stringWidth(label, "Helvetica-Bold", 8) + 16
    c.setFillColor(INK)
    c.roundRect(x, y - 4, width, 18, 5, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(x + width / 2, y + 2, label)
    return width


def box(c, x, y, w, h, title, body, fill=LIGHT):
    c.setFillColor(fill)
    c.roundRect(x, y - h, w, h, 9, fill=1, stroke=0)
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x + 14, y - 22, title)
    text(c, body, x + 14, y - 42, w - 28, 9.5, 13)


def arrow(c, x1, y1, x2, y2):
    c.setStrokeColor(INK)
    c.setLineWidth(2)
    c.line(x1, y1, x2, y2)
    import math
    a = math.atan2(y2-y1, x2-x1)
    for d in (-0.45, 0.45):
        c.line(x2, y2, x2-10*math.cos(a+d), y2-10*math.sin(a+d))


def circuit_resistor(c, x1, y, x2):
    c.setStrokeColor(INK); c.setLineWidth(2)
    c.line(x1, y, x1+14, y)
    step = (x2-x1-28)/8
    pts = [(x1+14, y)]
    for i in range(1, 9):
        pts.append((x1+14+i*step, y+(8 if i%2 else -8)))
    pts.append((x2-14, y)); pts.append((x2, y))
    p = c.beginPath(); p.moveTo(*pts[0])
    for pt in pts[1:]: p.lineTo(*pt)
    c.drawPath(p)


def page1(c):
    c.setFillColor(INK); c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(ACCENT); c.roundRect(44, H-176, 122, 24, 6, fill=1, stroke=0)
    c.setFillColor(INK); c.setFont("Helvetica-Bold", 10); c.drawCentredString(105, H-168, "PRODUCTION GATE")
    c.setFillColor(white); c.setFont("Helvetica-Bold", 34)
    text(c, "OHM’S LAW\nWITHOUT THE FOG", 44, H-230, W-88, 34, 38, "Helvetica-Bold", white)
    text(c, "A 14-page reading-experience prototype for the Ham Radio Technician Visual Cram Map 2026–2030", 44, H-350, W-105, 15, 21, color=white)
    c.setStrokeColor(ACCENT); c.setLineWidth(4); c.line(44, 150, W-44, 150)
    text(c, "One relationship. Three quantities. Sixteen official question IDs made easier to recognize.", 44, 126, W-88, 11, 16, "Helvetica-Bold", ACCENT)
    c.setFont("Helvetica", 8); c.setFillColor(white); c.drawString(44, 28, "Independent study-aid prototype · not an official exam publication")


def page2(c):
    y = header(c, 2, "The map before the math")
    text(c, "A circuit question usually gives you two quantities and asks for the third. Do not begin with a triangle or a calculator. Begin with the story.", 44, y, W-88, 12, 17)
    centers = [(105, 470, "PUSH", "voltage · E"), (288, 470, "FLOW", "current · I"), (471, 470, "OPPOSITION", "resistance · R")]
    for x, yy, a, b in centers:
        c.setFillColor(ACCENT if a != "OPPOSITION" else ACCENT2); c.circle(x, yy, 54, fill=1, stroke=0)
        c.setFillColor(INK); c.setFont("Helvetica-Bold", 12); c.drawCentredString(x, yy+4, a)
        c.setFont("Helvetica", 9); c.drawCentredString(x, yy-13, b)
    arrow(c, 160, 470, 228, 470); arrow(c, 348, 470, 407, 470)
    box(c, 44, 360, W-88, 92, "The single mental model", "More electrical push produces more flow. More opposition produces less flow. Ohm’s law turns that relationship into arithmetic.", ACCENT)
    tag(c, "POOL LINKS", 44, 220)
    text(c, "T5A05 · T5A11 · T5D01–T5D12", 44, 198, W-88, 10, 14, "Helvetica-Bold")


def page3(c):
    y = header(c, 3, "Name the three quantities")
    box(c, 44, y, W-88, 92, "Voltage (E), measured in volts", "The electrical potential difference—the push available between two points.", ACCENT)
    box(c, 44, y-110, W-88, 92, "Current (I), measured in amperes", "The rate of charge flow through a path. Current is what moves through a component.", LIGHT)
    box(c, 44, y-220, W-88, 92, "Resistance (R), measured in ohms", "How strongly a component opposes current. More resistance means less current when voltage stays fixed.", ACCENT2)
    text(c, "Exam-reading move: circle the two units you are given. The missing unit tells you which form of Ohm’s law to use.", 58, 185, W-116, 13, 18, "Helvetica-Bold")


def page4(c):
    y = header(c, 4, "Choose the formula from the missing piece")
    c.setFillColor(ACCENT2); c.circle(W/2, 438, 118, fill=1, stroke=0)
    c.setStrokeColor(INK); c.setLineWidth(2); c.line(W/2-92, 438, W/2+92, 438); c.line(W/2, 438, W/2, 350)
    c.setFillColor(INK); c.setFont("Helvetica-Bold", 42); c.drawCentredString(W/2, 476, "E")
    c.drawCentredString(W/2-50, 382, "I"); c.drawCentredString(W/2+50, 382, "R")
    formulas = [(44, 256, "Need current?", "I = E ÷ R"), (218, 256, "Need voltage?", "E = I × R"), (392, 256, "Need resistance?", "R = E ÷ I")]
    for x, yy, a, b in formulas:
        box(c, x, yy, 140, 75, a, b, ACCENT)
    text(c, "Memory aid, not magic: the diagram works because the three formulas describe the same relationship.", 58, 142, W-116, 10.5, 15)


def worked(c, n, title, given, ask, formula, math, answer, ids):
    y = header(c, n, title)
    tag(c, "1 · FIND THE GIVEN", 44, y)
    text(c, given, 44, y-30, W-88, 15, 21, "Helvetica-Bold")
    tag(c, "2 · NAME THE MISSING UNIT", 44, y-92)
    text(c, ask, 44, y-122, W-88, 15, 21, "Helvetica-Bold")
    tag(c, "3 · CHOOSE AND SOLVE", 44, y-184)
    box(c, 44, y-220, W-88, 120, formula, f"{math}\n\n{answer}", ACCENT2)
    text(c, "Pool links: " + ids, 44, 115, W-88, 9.5, 13, "Helvetica-Bold", MID)


def page8(c):
    y = header(c, 8, "Series: one path, same current")
    text(c, "If the charge has only one route, every component in that route carries the same current.", 44, y, W-88, 12, 17)
    yy=430; c.setStrokeColor(INK); c.setLineWidth(2); c.line(70, yy, 110, yy); circuit_resistor(c,110,yy,235); circuit_resistor(c,265,yy,390); c.line(235,yy,265,yy); c.line(390,yy,500,yy)
    for x, label in [(172,"R1"),(327,"R2")]: c.setFont("Helvetica-Bold",10); c.drawCentredString(x,yy-28,label)
    arrow(c, 82, yy+22, 140, yy+22); arrow(c, 245, yy+22, 303, yy+22); arrow(c, 400, yy+22, 458, yy+22)
    text(c, "I", 93, yy+45, 30, 11, 14, "Helvetica-Bold"); text(c, "I", 256, yy+45, 30, 11, 14, "Helvetica-Bold"); text(c, "I", 411, yy+45, 30, 11, 14, "Helvetica-Bold")
    box(c,44,320,W-88,86,"Recognition rule","ONE PATH → SAME CURRENT through every component.",ACCENT)
    box(c,44,214,W-88,86,"Do not overlearn","The prototype is testing recognition, not asking you to calculate equivalent resistance beyond the current pool’s needs.",LIGHT)
    text(c,"Pool link: T5D13",44,95,W-88,10,14,"Helvetica-Bold",MID)


def page9(c):
    y = header(c, 9, "Parallel: shared endpoints, same voltage")
    text(c, "If branches connect to the same two points, each branch has the same voltage across it.", 44, y, W-88, 12, 17)
    lx,rx,top,bot=120,456,500,330
    c.setStrokeColor(INK); c.setLineWidth(2); c.line(lx,top,rx,top); c.line(lx,bot,rx,bot); c.line(lx,bot, lx,top); c.line(rx,bot,rx,top)
    for yy in (460,370):
        c.line(250,yy,265,yy); circuit_resistor(c,265,yy,390); c.line(390,yy,405,yy)
        c.line(120,yy,250,yy); c.line(405,yy,456,yy)
    c.setFont("Helvetica-Bold",10); c.drawString(270,477,"R1"); c.drawString(270,387,"R2")
    c.setFont("Helvetica-Bold",11); c.drawString(76,415,"E"); c.drawString(465,415,"E")
    box(c,44,272,W-88,86,"Recognition rule","SAME TWO ENDPOINTS → SAME VOLTAGE across every branch.",ACCENT)
    box(c,44,166,W-88,70,"Fast contrast","Series shares current. Parallel shares voltage.",ACCENT2)
    text(c,"Pool link: T5D14",44,72,W-88,10,14,"Helvetica-Bold",MID)


def page10(c):
    y=header(c,10,"Do not confuse path with position")
    box(c,44,y,W-88,105,"SERIES: trace one uninterrupted route","One route through R1, then R2. Current cannot split. Question cue: “connected in series.”",ACCENT)
    box(c,44,y-127,W-88,105,"PARALLEL: mark the two shared nodes","Each branch begins and ends at the same pair of connection points. Voltage across the branches matches.",ACCENT2)
    box(c,44,y-254,W-88,105,"The visual check","Cover the labels. Can you trace one path, or can you choose between branches? That matters more than whether the drawing is horizontal or vertical.",LIGHT)
    text(c,"Pool links: T5D13–T5D14",44,92,W-88,10,14,"Helvetica-Bold",MID)


def page11(c):
    y=header(c,11,"Meters follow the quantity")
    text(c,"A meter must be connected in a way that lets it observe the quantity you are measuring.",44,y,W-88,12,17)
    box(c,44,y-62,235,130,"VOLTMETER","Measures difference between two points. Connect it across the component—in parallel.",ACCENT)
    box(c,297,y-62,235,130,"AMMETER","Measures flow through a path. Put it into the path—in series.",ACCENT2)
    text(c,"Memory picture",44,312,W-88,10,14,"Helvetica-Bold",MID)
    text(c,"Voltage looks ACROSS. Current goes THROUGH.",44,283,W-88,20,25,"Helvetica-Bold")
    text(c,"Pool links: T7D02–T7D03",44,112,W-88,10,14,"Helvetica-Bold",MID)


def page12(c):
    y=header(c,12,"Sixty-second self-check")
    qs=["1. A 12-volt source drives 4 amperes. What is the resistance?","2. A 10-ohm resistor carries 2 amperes. What voltage is across it?","3. In a series circuit, which quantity is the same through every component?","4. In parallel branches, which quantity is the same across each branch?","5. Does a voltmeter go in series or in parallel?"]
    for i,q in enumerate(qs):
        yy=y-i*94
        text(c,q,44,yy,W-88,11,15,"Helvetica-Bold")
        c.setStrokeColor(MID); c.line(44,yy-42,W-44,yy-42)
    text(c,"Answers and misconception check →",44,94,W-88,10,14,"Helvetica-Bold",MID)


def page13(c):
    y=header(c,13,"Answers: diagnose the mistake")
    answers=[("1 · 3 Ω","R = E ÷ I = 12 ÷ 4. If you multiplied, you answered a voltage question."),("2 · 20 V","E = I × R = 2 × 10. The requested unit—volts—selects the formula."),("3 · Current","Series has one path. The current does not split."),("4 · Voltage","Parallel branches share the same two endpoints."),("5 · Parallel","A voltmeter compares two points; an ammeter is inserted into the current path.")]
    for i,(a,b) in enumerate(answers):
        yy=y-i*94
        box(c,44,yy,W-88,78,a,b,ACCENT if i%2==0 else LIGHT)


def page14(c):
    y=header(c,14,"How the crosswalk behaves")
    text(c,"The finished book teaches concepts in learning order. The crosswalk restores official traceability without turning the main text into 409 sequential mini-essays.",44,y,W-88,11.5,17)
    rows=[("T5D01–T5D03","Formula chooser","pp. 3–4"),("T5D04–T5D12","Worked Ohm’s-law patterns","pp. 5–7"),("T5D13","Series recognition","p. 8"),("T5D14","Parallel recognition","pp. 9–10"),("T7D02–T7D03","Meter placement crossover","p. 11")]
    yy=470
    for q,concept,p in rows:
        c.setFillColor(ACCENT if int(yy)%2==0 else LIGHT); c.roundRect(44,yy-42,W-88,50,5,fill=1,stroke=0)
        c.setFillColor(INK); c.setFont("Helvetica-Bold",10); c.drawString(56,yy-13,q)
        c.setFont("Helvetica",9); c.drawString(158,yy-13,concept); c.drawRightString(W-56,yy-13,p)
        yy-=60
    box(c,44,143,W-88,76,"Source chain","NCVEC 2026–2030 pool → technical source check → original explanation/diagram → claim ledger → ID crosswalk",ACCENT2)
    text(c,"Prototype source basis: NCVEC T5D and T7D; NIST Ohm’s-law relationship; OpenStax series/parallel circuit principles. Exact source records belong in the production claim ledger.",44,52,W-88,8.5,12,color=MID)


def build():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    c=Canvas(str(OUT),pagesize=(W,H),pageCompression=1)
    c.setTitle("RN2-037 Visual Prototype")
    pages=[page1,page2,page3,page4,
           lambda x: worked(x,5,"Worked pattern: find resistance","Given: 12 volts and 4 amperes","Missing: ohms → resistance","R = E ÷ I","R = 12 V ÷ 4 A","R = 3 Ω","T5D03 · T5D06"),
           lambda x: worked(x,6,"Worked pattern: find current","Given: 120 volts and 80 ohms","Missing: amperes → current","I = E ÷ R","I = 120 V ÷ 80 Ω","I = 1.5 A","T5D01 · T5D07"),
           lambda x: worked(x,7,"Worked pattern: find voltage","Given: 2 amperes and 10 ohms","Missing: volts → voltage","E = I × R","E = 2 A × 10 Ω","E = 20 V","T5D02 · T5D12"),
           page8,page9,page10,page11,page12,page13,page14]
    for fn in pages:
        fn(c); c.showPage()
    c.save()
    print(OUT)


if __name__ == "__main__":
    build()
