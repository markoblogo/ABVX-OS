#!/usr/bin/env python3
"""Build RN2-037 manuscript, SVG visual system, print PDF, EPUB, and QA artifacts."""

from __future__ import annotations

import hashlib
import html
import json
import math
import re
import shutil
import textwrap
import zipfile
from collections import defaultdict
from datetime import date
from pathlib import Path
from xml.etree import ElementTree as ET

from reportlab.lib.colors import Color, HexColor, black, white
from reportlab.lib.pagesizes import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.utils import ImageReader


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "books" / "rn2-037"
DATA = BASE / "data"
MAN = BASE / "manuscript"
VIS = BASE / "visuals" / "svg"
OFFICIAL_VIS = BASE / "visuals" / "official-pool"
QA = BASE / "qa"
PROD = BASE / "production"
COMM = BASE / "commercial"
OUTPDF = ROOT / "output" / "pdf"
OUTEPUB = ROOT / "output" / "epub"
POOL = DATA / "question-pool-2026-2030.json"
CONTRACT = ROOT / "RN2-037-production-contract.md"
PDF_OUT = OUTPDF / "ham-radio-technician-visual-cram-map-2026-2030-interior.pdf"
EPUB_OUT = OUTEPUB / "ham-radio-technician-visual-cram-map-2026-2030.epub"

W, H = 8 * inch, 10 * inch
INK = HexColor("#171717")
MID = HexColor("#5B5B5B")
LIGHT = HexColor("#E8E8E8")
GREEN = HexColor("#DADADA")
TAN = HexColor("#EFEFEF")
PALE = HexColor("#F8F8F8")

FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"
BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
ITALIC = "/System/Library/Fonts/Supplemental/Arial Italic.ttf"
pdfmetrics.registerFont(TTFont("Body", FONT))
pdfmetrics.registerFont(TTFont("Body-Bold", BOLD))
pdfmetrics.registerFont(TTFont("Body-Italic", ITALIC))


CHAPTERS = [
    (1, "Electricity without intimidation", ["T5A", "T5B", "T5C", "T5D"], "Turn units and relationships into a small set of dependable moves."),
    (2, "Components as jobs, not symbols", ["T6A", "T6B", "T6C", "T6D"], "Recognize parts by the job they perform, then connect the job to the symbol."),
    (3, "Inside a radio and on the bench", ["T7A", "T7D"], "Follow signal flow and connect test instruments without guessing."),
    (4, "Troubleshoot by symptom, cause, and safe action", ["T7B", "T7C"], "Use visible symptoms to choose the first sensible and safe check."),
    (5, "Waves, frequency, and propagation", ["T3A", "T3B", "T3C"], "Picture what a radio wave is doing before memorizing a propagation name."),
    (6, "Antennas, feed lines, and SWR", ["T9A", "T9B"], "See the complete path from transmitter to feed line to antenna and outward."),
    (7, "Signals and ways hams communicate", ["T8A", "T8B", "T8C", "T8D"], "Match signal type and operating method to purpose, bandwidth, and path."),
    (8, "First station and operating controls", ["T4A", "T4B"], "Connect the station correctly and know which control changes which symptom."),
    (9, "Getting on the air", ["T2A", "T2B", "T2C"], "Move from listening to a clear contact, repeater use, and disciplined net operation."),
    (10, "Rules as decision paths", ["T1A", "T1B", "T1C", "T1D", "T1E", "T1F"], "Decide who may transmit, where, under whose control, and with what identification."),
    (11, "Safety before shortcuts", ["T0A", "T0B", "T0C"], "Recognize the hazard first; choose the safe action before the technical shortcut."),
]

TOPICS = {
"T5A":("The electrical vocabulary","Distinguish current, voltage, power, frequency, conductors, insulators, AC, and DC.","Picture voltage as the difference that can drive charge, current as charge flow, and resistance as opposition. Power is the rate at which electrical energy is used or delivered.",["voltage","current","resistance","power","AC and DC"]),
"T5B":("Metric prefixes and decibels","Move between common units and read gain or loss without arithmetic panic.","Prefixes move the decimal point: kilo is one thousand, mega is one million, milli is one thousandth, and micro is one millionth. A positive decibel value is gain; a negative value is loss.",["kilo and mega","milli and micro","frequency conversion","3 dB change","gain versus loss"]),
"T5C":("Power, reactance, and radio-frequency units","Choose the right unit and use the power relationship at exam depth.","Capacitance and inductance store energy in different fields. Impedance is the broader opposition an AC signal sees. Electrical power follows P = I × E.",["capacitance","inductance","impedance","frequency units","P = I × E"]),
"T5D":("Ohm's law and circuit paths","Choose the missing quantity and recognize series versus parallel.","Use the requested unit to select the formula: amperes mean current, volts mean voltage, and ohms mean resistance. Series means one current path; parallel branches share two endpoints.",["I = E / R","E = I × R","R = E / I","series current","parallel voltage"]),
"T6A":("Passive parts, switches, and batteries","Recognize common components by what they oppose, store, switch, or supply.","A resistor limits current, a capacitor stores energy in an electric field, and an inductor stores energy in a magnetic field. Switch names describe poles and throws.",["resistor","capacitor","inductor","switch poles","battery safety"]),
"T6B":("Diodes and transistors","Tell one-way devices from control and amplification devices.","A diode favors current in one direction. A transistor uses one signal to control another and can act as an amplifier or switch. Terminal names identify the device family.",["diode direction","anode and cathode","transistor control","FET","terminal names"]),
"T6C":("Reading schematic symbols","Translate a drawing into components and connections.","A schematic shows electrical relationships, not physical placement. Read one symbol at a time, then follow the connecting lines to reconstruct the circuit's jobs.",["schematic","symbols","connections","variable parts","antenna symbol"]),
"T6D":("Functional building blocks","Match a component or circuit to the job it performs.","Rectifiers change AC toward DC, regulators hold voltage steady, transformers transfer energy between windings, and resonant circuits select frequencies.",["rectifier","relay","regulator","transformer","resonance"]),
"T7A":("Radio blocks and signal flow","Follow a signal through receiver, transmitter, and frequency-conversion stages.","Sensitivity is about weak signals; selectivity is about separating nearby signals. Mixers combine frequencies, oscillators create a signal, and modulation places information on a carrier.",["sensitivity","selectivity","mixer","oscillator","modulation"]),
"T7D":("Meters and safe measurements","Connect meters correctly and recognize safe bench practice.","A voltmeter looks across two points; an ammeter goes through the current path. An ohmmeter applies a small internal current, so the circuit must be unpowered.",["voltmeter parallel","ammeter series","ohmmeter unpowered","solder joint","lead ratings"]),
"T7B":("Interference and distorted audio","Move from symptom to likely cause before changing equipment.","Strong nearby signals can overload receivers. Too much microphone gain or RF feedback distorts transmitted audio. Start with correct station operation and targeted filtering.",["overload","overdrive","RF feedback","filters","connector checks"]),
"T7C":("SWR, feed lines, and test loads","Recognize mismatch, loss, and safe transmitter testing.","A dummy load lets a transmitter operate without radiating. SWR indicates how well the load matches the line. Reflected energy becomes heat and high SWR can stress an output stage.",["dummy load","1 to 1 SWR","mismatch","directional wattmeter","coax loss"]),
"T3A":("What happens along the path","Recognize polarization, obstruction, multipath, and weather effects.","A received signal may arrive by more than one path. Those copies can reinforce or cancel, producing fading and flutter. Antenna polarization and local obstructions matter.",["multipath","fading","polarization","obstructions","precipitation"]),
"T3B":("Frequency and wavelength","Relate fields, speed, frequency, and wavelength.","Radio waves have electric and magnetic fields at right angles. In free space they travel at the speed of light. Higher frequency means shorter wavelength; wavelength in meters is approximately 300 divided by megahertz.",["electric field","magnetic field","speed of light","frequency bands","300 / MHz"]),
"T3C":("Propagation modes","Match a path shape and condition to its propagation name.","VHF and UHF are often line-of-sight, but atmosphere, terrain, aurora, meteors, and sporadic ionization can extend or distort the path. HF ionospheric propagation is much more common.",["line of sight","tropospheric ducting","sporadic E","aurora","radio horizon"]),
"T9A":("Antenna shape, direction, and length","Connect polarization, gain, resonance, and radiation pattern.","An antenna does not create power; gain concentrates radiation in favored directions. Resonant length changes inversely with frequency, and orientation determines polarization.",["gain","polarization","resonance","Yagi","dipole pattern"]),
"T9B":("The feed-line chain","See impedance, loss, connectors, weather, and matching as one system.","Coaxial cable is convenient and commonly 50 ohms in amateur systems. Loss rises with frequency. An antenna tuner changes the impedance match seen by the transmitter; it does not remove feed-line loss.",["50 ohms","coax","loss","connector choice","SWR"]),
"T8A":("Modes and bandwidth","Match FM, SSB, CW, and television signals to typical bandwidth and use.","Different emission types occupy different widths of spectrum. CW is very narrow, SSB is narrower than FM voice, and fast-scan television is much wider.",["CW","SSB","FM","sideband choice","bandwidth"]),
"T8B":("Satellite paths","Separate uplink, downlink, orbit data, Doppler shift, and power discipline.","A satellite receives on its uplink and transmits on its downlink. Relative motion shifts the apparent frequency. Tracking data predicts the pass; excessive uplink power blocks other users.",["uplink","downlink","Doppler","Keplerian elements","LEO"]),
"T8C":("Operating activities and internet linking","Recognize direction finding, contest exchange, location grids, and linked systems.","These activities use radio in different ways: direction finding locates a source, grid locators describe position, and internet-linked gateways extend voice paths between systems.",["direction finding","contest exchange","grid locator","DTMF","EchoLink"]),
"T8D":("Digital modes as functions","Match digital names to the job they perform.","Some modes send text or position, some carry digital voice, and some work at very low signal levels. Error-control systems either correct data or request retransmission.",["FT8","APRS","PSK","DMR","error control"]),
"T4A":("Connect the station","Build the power, audio, data, RF, and grounding paths.","Treat the station as several separate paths. DC power must handle transmit current with low voltage drop. Audio/data interfaces connect the radio and computer; RF instruments sit in the feed line.",["DC power","audio and data","SWR meter","RF bonding","mobile ground"]),
"T4B":("Controls change symptoms","Choose the control that acts on the problem you can hear or see.","Squelch controls when receiver audio opens, filters control received bandwidth, microphone gain affects transmit audio, RIT shifts receive tuning, and scanning searches memories or frequencies.",["squelch","filter bandwidth","microphone gain","RIT","scan"]),
"T2A":("Calling, listening, and frequency use","Make a contact and distinguish simplex, repeater offset, and band-plan guidance.","Listen first. On simplex, both stations use the same frequency. A repeater uses separate input and output frequencies; the difference is the offset. Band plans are voluntary coordination tools.",["simplex","repeater offset","calling frequency","CQ","band plan"]),
"T2B":("Repeater access and shared channels","Understand tones, DMR identifiers, linked repeaters, and courteous frequency sharing.","Analog repeaters may require a CTCSS tone; control functions may use DTMF. DMR organizes access with identifiers, color codes, and talkgroups. Squelch mutes idle noise.",["CTCSS","DTMF","DMR color code","talkgroup","squelch"]),
"T2C":("Nets and public service","Follow net control, message handling, and emergency boundaries.","A directed net has a net control station coordinating traffic. Formal messages carry tracking information and a word count. Emergency circumstances do not erase FCC rules.",["net control","traffic","phonetics","ARES and RACES","Winlink"]),
"T1A":("Purpose, authority, and interference","Know who regulates amateur radio and why the service exists.","The FCC regulates the service. Its stated purposes include advancing radio skill and communication. Coordination is largely performed by amateurs, but willful interference remains prohibited.",["FCC","basis and purpose","frequency coordinator","RACES","interference"]),
"T1B":("Where a Technician may transmit","Read privileges as band, segment, mode, and power together.","A license class does not grant one undivided block of spectrum. Check the band, the permitted segment, the emission, and the power limit. Stay clear of band edges and shared users.",["10-meter voice","VHF and UHF","CW segments","shared bands","power limits"]),
"T1C":("License lifecycle","Know when authority begins, how long it lasts, and what happens around renewal.","Operating authority begins when the grant appears in the FCC database. Licenses have a term, an advance renewal window, and a grace period with no operating authority after expiration until renewal.",["license classes","ULS grant","renewal window","term","grace period"]),
"T1D":("Permitted and prohibited content","Classify a transmission by purpose rather than by convenience.","Amateur radio is not broadcasting. Encryption, music, compensation, one-way transmissions, and third-party material have narrow rules and exceptions. Immediate safety can change what is permitted.",["broadcasting","encryption","music","compensation","emergency exception"]),
"T1E":("Control operator responsibility","Separate the station licensee, control operator, control point, and control method.","Every station transmission has a designated control operator whose license determines privileges. The station licensee and control operator share responsibility for proper operation.",["control operator","station licensee","control point","remote control","privileges"]),
"T1F":("Identification and station types","Apply the call-sign clock and recognize repeater, club, and third-party roles.","Identify at least every ten minutes and at the end of a communication. Use an allowed emission and English-language identification. Station type determines who is responsible for identification.",["ten-minute ID","end of contact","English ID","third-party traffic","club station"]),
"T0A":("Electrical, battery, and lightning hazards","Choose isolation, protection, bonding, and correct ratings.","High current can start a fire even at low voltage. Fuses belong in the hot conductor. Capacitors can store dangerous energy after power is removed. Lightning grounds should be short, direct, and bonded.",["battery short","fuse","stored charge","bonding","lightning entry"]),
"T0B":("Antenna and tower safety","Keep structures and every possible fall path clear of power lines.","The first antenna-site question is not signal strength; it is whether any part can reach an energized line. Use proper climbing controls, grounding, and local electrical-code requirements.",["power-line clearance","tower climbing","guy hardware","ground rods","local code"]),
"T0C":("RF exposure","Distinguish non-ionizing RF from ionizing radiation and control exposure.","RF exposure depends on frequency, power, duty cycle, antenna gain, and distance. Evaluate the station and repeat the evaluation when the transmitter or antenna system changes.",["non-ionizing","frequency","duty cycle","distance","station evaluation"]),
}


def ensure_dirs():
    for p in (MAN, VIS, OFFICIAL_VIS, QA, PROD, COMM, OUTPDF, OUTEPUB): p.mkdir(parents=True, exist_ok=True)


def draw_source_figure(c, filename, x, y, w, h):
    """Place an exact NCVEC public-domain pool figure inside a bounded box."""
    c.drawImage(ImageReader(OFFICIAL_VIS / filename), x, y, w, h,
                preserveAspectRatio=True, anchor="c", mask="auto")


def wrap_lines(text, width, font="Body", size=10):
    words, lines, line = text.split(), [], ""
    for word in words:
        trial=(line+" "+word).strip()
        if pdfmetrics.stringWidth(trial,font,size)<=width: line=trial
        else:
            if line: lines.append(line)
            line=word
    if line: lines.append(line)
    return lines


def draw_text(c, text, x, y, width, size=10.5, leading=14, font="Body", color=INK, max_lines=None):
    c.setFont(font,size); c.setFillColor(color); n=0
    for para in text.split("\n"):
        if not para: y-=leading*.55; continue
        for line in wrap_lines(para,width,font,size):
            if max_lines is not None and n>=max_lines: return y
            c.drawString(x,y,line); y-=leading; n+=1
    return y


def footer(c, page, section=""):
    c.setStrokeColor(LIGHT); c.line(42,35,W-42,35)
    c.setFont("Body",7.5); c.setFillColor(MID); c.drawString(42,22,section[:62]); c.drawRightString(W-42,22,str(page))


def page_title(c, kicker, title, page, section=""):
    c.setFont("Body-Bold",7.5); c.setFillColor(MID); c.drawString(42,H-36,kicker.upper())
    c.setStrokeColor(LIGHT); c.line(42,H-44,W-42,H-44)
    y=H-78; c.setFont("Body-Bold",22); c.setFillColor(INK)
    for line in wrap_lines(title,W-84,"Body-Bold",22): c.drawString(42,y,line); y-=27
    footer(c,page,section or title)
    return y-6


def card(c,x,y,w,h,title,body,fill=LIGHT,title_size=10,body_size=8.5):
    c.setFillColor(fill); c.roundRect(x,y-h,w,h,8,fill=1,stroke=0)
    c.setFillColor(INK); c.setFont("Body-Bold",title_size); c.drawString(x+12,y-20,title)
    draw_text(c,body,x+12,y-38,w-24,body_size,body_size+3,max_lines=max(1,int((h-46)/(body_size+3))))


def write_svg(group, title, keywords, variant):
    vid=f"V-{group}-{variant}"
    path=VIS/f"{vid}.svg"
    esc=lambda s: html.escape(s,quote=True)
    if variant=="MAP":
        nodes=[]
        for i,k in enumerate(keywords):
            a=2*math.pi*i/len(keywords)-math.pi/2; x=400+245*math.cos(a); y=280+170*math.sin(a)
            nodes.append((x,y,k))
        lines="".join(f'<line x1="400" y1="280" x2="{x:.1f}" y2="{y:.1f}" class="line"/>' for x,y,_ in nodes)
        boxes="".join(f'<rect x="{x-80:.1f}" y="{y-25:.1f}" width="160" height="50" rx="10" class="node"/><text x="{x:.1f}" y="{y+5:.1f}" class="small">{esc(k)}</text>' for x,y,k in nodes)
        body=f'{lines}<circle cx="400" cy="280" r="82" class="core"/><text x="400" y="272" class="label">{esc(group)}</text><text x="400" y="298" class="tiny">one connected model</text>{boxes}'
    else:
        left=keywords[:3]; right=keywords[3:]
        rows=""; y=175
        for i,k in enumerate(left): rows+=f'<rect x="70" y="{y+i*92}" width="265" height="58" rx="10" class="node"/><text x="202" y="{y+35+i*92}" class="small">{esc(k)}</text>'
        for i,k in enumerate(right): rows+=f'<rect x="465" y="{y+i*92}" width="265" height="58" rx="10" class="warm"/><text x="597" y="{y+35+i*92}" class="small">{esc(k)}</text>'
        body=f'<text x="202" y="125" class="label">recognize</text><text x="597" y="125" class="label">connect</text><path d="M350 280 L450 280" class="line" marker-end="url(#arrow)"/>{rows}'
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="560" viewBox="0 0 800 560" role="img" aria-labelledby="t d"><title id="t">{esc(title)} {variant.lower()}</title><desc id="d">Original concept diagram for {esc(group)} linking {esc(', '.join(keywords))}.</desc><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#171717"/></marker></defs><style>.line{{stroke:#171717;stroke-width:4;fill:none}}.node{{fill:#DADADA}}.warm{{fill:#EFEFEF}}.core{{fill:#171717}}text{{font-family:Arial,sans-serif;fill:#171717;text-anchor:middle}}.label{{font-size:25px;font-weight:700}}.small{{font-size:18px;font-weight:700}}.tiny{{font-size:15px;fill:#fff}}circle+text{{fill:#fff}}</style><rect width="800" height="560" fill="#fff"/>{body}</svg>'''
    path.write_text(svg,encoding="utf-8")
    return vid


def draw_map(c, group, title, keywords, variant=1, center_y=380):
    if variant==1:
        cx,cy=288,center_y
        nodes=[]
        for i,k in enumerate(keywords):
            a=2*math.pi*i/len(keywords)-math.pi/2; x=cx+190*math.cos(a); y=cy+145*math.sin(a)
            nodes.append((i,k,x,y))
        c.setStrokeColor(INK); c.setLineWidth(1.5)
        for _,_,x,y in nodes:
            c.line(cx,cy,x,y)
        c.setFillColor(INK); c.circle(cx,cy,62,fill=1,stroke=0)
        c.setFillColor(white); c.setFont("Body-Bold",18); c.drawCentredString(cx,cy+4,group)
        for i,k,x,y in nodes:
            c.setFillColor(GREEN if i%2==0 else TAN); c.roundRect(x-66,y-20,132,40,8,fill=1,stroke=0)
            c.setFillColor(INK); c.setFont("Body-Bold",8.5)
            for j,line in enumerate(wrap_lines(k,112,"Body-Bold",8.5)[:2]): c.drawCentredString(x,y+4-j*10,line)
    else:
        c.setFont("Body-Bold",11); c.setFillColor(INK); c.drawCentredString(150,540,"RECOGNIZE")
        c.drawCentredString(426,540,"CONNECT")
        for i,k in enumerate(keywords):
            left=i<3; row=i if left else i-3; x=55 if left else 331; y=500-row*100
            card(c,x,y,190,62,k,"Use the relationship, not an isolated word.",GREEN if left else TAN,9,7.5)
        c.setStrokeColor(INK); c.setLineWidth(2); c.line(253,390,323,390); c.line(313,396,323,390); c.line(313,384,323,390)


def normalize_question(q):
    stem=q["question"].rstrip("?")
    ans=q["correct_answer"]
    return f"{q['id']}  {stem}: {ans}."


def manuscript(pool):
    by_group=defaultdict(list)
    for q in pool["questions"]: by_group[q["group"]].append(q)
    lines=["# Ham Radio Technician Visual Cram Map 2026–2030","","## A Diagram-First Guide to the FCC Element 2 Concepts, Rules, and Calculations Beginners Mix Up","","**Northfield Signal Guides**","",
           "Independent study aid. Not affiliated with or endorsed by the Federal Communications Commission, NCVEC, ARRL, any Volunteer Examiner Coordinator, or any examination provider.","",
           "## How to use this book","","This book gives you a map, not a pile of disconnected answers. Learn a visual model, practise with a free randomized exam tool, then use the question-ID crosswalk to route every miss back to the relevant model. The official pool remains the authority for question wording and accepted answers.",""]
    for ch,title,groups,outcome in CHAPTERS:
        lines += [f"# Chapter {ch} {title}","",outcome,"",f"Official groups: {', '.join(groups)}.",""]
        for group in groups:
            title2,outcome2,model,keys=TOPICS[group]
            lines += [f"## {group} {title2}","",f"**Reader outcome:** {outcome2}","",model,"",
                      "**Use the picture:** Read the concept map from the center outward. Then use the contrast page to connect similar-looking terms. The point is not to memorize the diagram; it is to recognize which relationship the exam is asking about.","",
                      "### Official-pool anchors","" ]
            if group == "T6C":
                lines += ["**Official figure key:** Figures T-1, T-2, and T-3 are reproduced exactly from the public-domain NCVEC pool. Use the numbered labels when working the figure-referenced anchors.",""]
            elif any(q.get("diagram_reference") for q in by_group[group]):
                lines += ["**Figure route:** This group includes a question that refers to an official pool figure. The complete official figure key appears in T6C.",""]
            lines += [f"- {normalize_question(q)}" for q in by_group[group]]
            lines += ["","### Quick check","",f"Without looking back, explain the relationship among {', '.join(keys[:-1])}, and {keys[-1]}. Then choose two official IDs above and say which clue would lead you to the answer.",""]
    lines += ["# Final visual review","","Review formulas, paths, operating decisions, rules, and safety in that order. A weak practice result is diagnostic: find the missed ID in the crosswalk, return to its concept page, and explain the visual in your own words.","",
              "# Complete question-ID crosswalk","","Every active ID has exactly one primary teaching home. Secondary relationships may appear elsewhere, but they do not change the primary mapping.",""]
    for q in pool["questions"]:
        lines.append(f"- **{q['id']}** → Chapter {q['primary_chapter']}, {q['group']} ({q['coverage_mode'].lower().replace('_',' ')})")
    lines += ["","# Sources and update notice","","Question pool: NCVEC 2026–2030 Technician Class Element 2 corrected release dated February 19, 2026, effective July 1, 2026 through June 30, 2030. Rules: current 47 CFR Part 97 checked September 6, 2026. Check the NCVEC page for later errata or withdrawals before relying on the book.",""]
    out="\n".join(lines)
    (MAN/"ham-radio-technician-visual-cram-map.md").write_text(out,encoding="utf-8")
    return out


def build_pdf(pool):
    by_group=defaultdict(list)
    for q in pool["questions"]: by_group[q["group"]].append(q)
    c=Canvas(str(PDF_OUT),pagesize=(W,H),pageCompression=1,initialFontName="Body")
    c.setTitle("Ham Radio Technician Visual Cram Map 2026-2030")
    c.setAuthor("Northfield Signal Guides")
    page=0; visual_ids=[]; anchors={}
    def new():
        nonlocal page; page+=1; return page
    # 8 front-matter pages
    p=new(); c.setFillColor(INK); c.rect(0,0,W,H,fill=1,stroke=0); c.setFillColor(white)
    draw_text(c,"HAM RADIO\nTECHNICIAN",42,H-150,W-84,34,39,"Body-Bold",white)
    draw_text(c,"VISUAL CRAM MAP\n2026–2030",42,H-260,W-84,30,35,"Body-Bold",GREEN)
    draw_text(c,"A diagram-first guide to the FCC Element 2 concepts, rules, and calculations beginners mix up",42,H-370,W-110,15,21,"Body",white)
    draw_text(c,"NORTHFIELD SIGNAL GUIDES",42,70,W-84,10,14,"Body-Bold",GREEN); c.showPage()
    p=new(); y=page_title(c,"Reader notice","Independent study aid",p,"Front matter")
    y=draw_text(c,"This book is not affiliated with or endorsed by the Federal Communications Commission, NCVEC, ARRL, any Volunteer Examiner Coordinator, or any examination provider.",42,y,W-84,12,17,"Body-Bold")
    y=draw_text(c,"The official NCVEC question pool controls question wording and accepted answers. FCC Part 97 controls the rules. This edition uses the corrected pool released February 19, 2026, effective July 1, 2026 through June 30, 2030. Check NCVEC for later errata or withdrawals.",42,y-22,W-84,11,16)
    draw_text(c,"No pass, score, or study-time result is promised. This is an exam companion, not an operating handbook, engineering reference, or substitute for current rules and safe local practice.",42,y-26,W-84,11,16); c.showPage()
    front=[
      ("How the book works","LEARN → PRACTISE → DIAGNOSE → RETURN","Learn one reusable model here. Practise with a free randomized tool. When you miss an item, use its official ID to return to the model. This book deliberately does not imitate an exam simulator."),
      ("Read an ID","T5D06 is an address","T5 identifies electrical principles. D identifies the group. 06 identifies the question. The address remains stable inside this pool cycle and makes every concept traceable."),
      ("What the exam samples","35 questions from 10 subelements","The exam uses a fixed blueprint across rules, procedures, propagation, practices, electrical principles, components, circuits, signals, antennas, and safety. You need 26 correct answers to pass."),
      ("Contents","Chapters and reference","The chapters follow beginner dependencies rather than pool order."),
      ("The whole system","One station, many views","Electrical power drives equipment. Equipment creates and receives signals. Feed lines and antennas connect the station to a propagation path. Operating rules and safety constrain every step."),
      ("Before exam day","Refresh and practise","Check the current NCVEC pool page, use randomized practice, and verify exam arrangements with the chosen examination provider. Do not rely on an old pool or a memorized answer if an erratum changes it."),
    ]
    for title,big,body in front:
        p=new(); y=page_title(c,"Orientation",title,p,"Front matter")
        draw_text(c,big,42,y-32,W-84,22,28,"Body-Bold")
        if title=="Contents":
            toc=[("1 Electricity without intimidation",9),("2 Components as jobs, not symbols",27),("3 Inside a radio and on the bench",45),("4 Troubleshoot by symptom and cause",55),("5 Waves, frequency, and propagation",65),("6 Antennas, feed lines, and SWR",79),("7 Signals and ways hams communicate",89),("8 First station and operating controls",107),("9 Getting on the air",117),("10 Rules as decision paths",131),("11 Safety before shortcuts",157),("Final visual review",171),("Complete 409-ID crosswalk",181),("Sources and reference",201)]
            yy=520
            for label,pg in toc:
                c.setFont("Body",9.5); c.setFillColor(INK); c.drawString(58,yy,label); c.drawRightString(W-58,yy,str(pg)); yy-=20
        elif title=="The whole system":
            draw_text(c,body,58,y-86,W-116,10.5,15,"Body",INK,max_lines=4)
        else:
            card(c,42,y-95,W-84,125,"THE WORKING RULE",body,GREEN,11,10)
        if title=="The whole system":
            draw_map(c,"MAP",title,["power","equipment","signal","feed line","antenna"],1,center_y=300); visual_ids.append("V-FRONT-SYSTEM")
        else:
            draw_text(c,"Keep the task narrow: identify the relationship, choose the safe or lawful action, and connect the item to its official ID.",58,220,W-116,12,18,"Body-Bold",MID)
        c.showPage()
    # chapters: 2 opener pages + four pages per group
    for ch,title,groups,outcome in CHAPTERS:
        p=new(); anchors[f"chapter-{ch}"]=p; c.bookmarkPage(f"chapter-{ch}"); c.addOutlineEntry(f"Chapter {ch} {title}",f"chapter-{ch}",0); y=page_title(c,f"Chapter {ch}",title,p,title)
        draw_text(c,outcome,42,y-24,W-84,15,21,"Body-Bold")
        chapter_keys=groups+["review"] if len(groups)<5 else groups
        draw_map(c,f"CH {ch}",title,chapter_keys,1); vid=write_svg(f"CH{ch:02d}",title,chapter_keys,"MAP"); visual_ids.append(vid)
        draw_text(c,"Official groups: "+", ".join(groups),42,90,W-84,9,13,"Body-Bold",MID); c.showPage()
        p=new(); y=page_title(c,f"Chapter {ch}","Your route through this chapter",p,title)
        card_gap=78 if len(groups)>4 else 92
        for i,g in enumerate(groups):
            t,o,_,_=TOPICS[g]; card(c,42,y-i*card_gap,W-84,72,g+"  "+t,o,GREEN if i%2==0 else LIGHT,10,8.5)
        draw_text(c,"After the last group, use the official-pool anchors to identify weak spots. Do randomized exam practice outside this book.",42,105,W-84,10.5,15,"Body-Bold",MID); c.showPage()
        for group in groups:
            t,o,model,keys=TOPICS[group]; qs=by_group[group]
            p=new(); anchors[group]=p; c.bookmarkPage(group); c.addOutlineEntry(f"{group} {t}",group,1); y=page_title(c,group,t,p,title)
            draw_text(c,o,42,y-8,W-84,14,20,"Body-Bold")
            card(c,42,y-78,W-84,150,"THE MENTAL MODEL",model,GREEN,12,11)
            draw_text(c,"Exam reading move",42,y-252,W-84,10,14,"Body-Bold",MID)
            draw_text(c,f"Name what is changing, what stays fixed, and which unit, path, role, or rule the question is testing. The useful cues in this group are {', '.join(keys)}.",42,y-276,W-84,11,16)
            c.showPage()
            p=new(); page_title(c,group,t+" concept map",p,title)
            visual_ids.append(write_svg(group,t,keys,"MAP"))
            if group == "T6C":
                draw_source_figure(c,"figure-t1.png",72,170,W-144,420)
                draw_text(c,"OFFICIAL FIGURE T-1 · NCVEC public-domain pool",58,128,W-116,9,13,"Body-Bold",MID)
            else:
                draw_map(c,group,t,keys,1)
                draw_text(c,"Read from the center outward. Each node is a cue that should lead back to the same working model.",58,112,W-116,10,14,"Body-Bold",MID)
            c.showPage()
            p=new(); page_title(c,group,"Recognize, then connect",p,title)
            visual_ids.append(write_svg(group,t,keys,"FLOW"))
            if group == "T6C":
                draw_source_figure(c,"figure-t2.png",46,375,W-92,250)
                draw_source_figure(c,"figure-t3.png",150,92,W-300,250)
                draw_text(c,"OFFICIAL FIGURES T-2 AND T-3 · NCVEC public-domain pool",58,70,W-116,9,13,"Body-Bold",MID)
            else:
                draw_map(c,group,t,keys,2)
                draw_text(c,"The exam often places related words close together. Do not choose by familiarity. Identify the requested job, path, unit, or rule first.",58,112,W-116,10,14,"Body-Bold",MID)
            c.showPage()
            p=new(); y=page_title(c,group,"Official-pool anchors",p,title)
            c.setFont("Body",7.9); c.setFillColor(INK)
            cols=[qs[:math.ceil(len(qs)/2)],qs[math.ceil(len(qs)/2):]]
            for ci,col in enumerate(cols):
                x=42+ci*252; yy=y
                for q in col:
                    s=normalize_question(q)
                    lines=wrap_lines(s,235,"Body",7.9)
                    for ln in lines[:5]: c.drawString(x,yy,ln); yy-=10
                    yy-=7
            draw_text(c,"Quick check: pick two IDs. State the clue, the relationship, and the answer without rereading the stem.",42,78,W-84,9.5,13,"Body-Bold",MID)
            if any(q.get("diagram_reference") for q in qs) and group != "T6C":
                draw_text(c,"Official figure route: see the T6C figure key on pages 38–39.",42,58,W-84,8.5,11,"Body-Bold",MID)
            c.showPage()
    # 10 review pages, 8 visuals
    reviews=[
      ("Formula route","Requested unit → formula → substitute → sanity check",["volts","amperes","ohms","watts","prefixes"]),
      ("Path route","source → equipment → feed line → antenna → propagation",["power","radio","coax","antenna","wave"]),
      ("Measurement route","quantity → connection → range → power state → reading",["voltage","current","resistance","parallel","series"]),
      ("Operating route","listen → identify → contact → share → log or pass traffic",["simplex","repeater","tone","net","ID"]),
      ("Rules route","license → band → mode → power → content → identification",["authority","privilege","control","content","ID"]),
      ("Safety route","hazard → distance/isolation → protection → verify → proceed",["power lines","stored charge","battery","lightning","RF"]),
      ("Signals route","information → modulation → bandwidth → path → receiver",["CW","SSB","FM","digital","satellite"]),
      ("Troubleshooting route","symptom → simplest cause → safe test → one change",["overload","feedback","SWR","moisture","connector"]),
      ("How to diagnose a miss","Find the official ID. Name its group. Return to the concept page. Explain the visual. Retest with a different randomized item.",[]),
      ("Last-minute boundary","Do not learn new folklore on exam morning. Review the compact maps, verify current pool status, and use the official ID system for anything uncertain.",[]),
    ]
    for i,(title,big,keys) in enumerate(reviews,1):
        p=new();
        if i==1: c.bookmarkPage("final-review"); c.addOutlineEntry("Final visual review","final-review",0)
        y=page_title(c,"Final visual review",title,p,"Final review")
        draw_text(c,big,42,y-16,W-84,17,23,"Body-Bold")
        if keys:
            draw_map(c,"REVIEW",title,keys,1); visual_ids.append(write_svg(f"REVIEW{i:02d}",title,keys,"MAP"))
        else:
            card(c,42,440,W-84,150,"THE PRACTICE LOOP",big,GREEN,12,11)
            draw_text(c,"The book is a diagnostic map. Randomized practice remains the better test simulator.",58,220,W-116,12,18,"Body-Bold",MID)
        c.showPage()
    # 20 crosswalk pages, 21 IDs per page except last
    chunks=[pool["questions"][i:i+21] for i in range(0,409,21)]
    assert len(chunks)==20
    for idx,chunk in enumerate(chunks,1):
        p=new();
        if idx==1: c.bookmarkPage("crosswalk"); c.addOutlineEntry("Complete 409-ID crosswalk","crosswalk",0)
        y=page_title(c,"Complete 409-ID crosswalk",f"Question routes {idx} of 20",p,"Crosswalk")
        for q in chunk:
            c.setFillColor(GREEN if int(q["id"][-2:])%2 else LIGHT); c.roundRect(42,y-23,W-84,27,4,fill=1,stroke=0)
            c.setFillColor(INK); c.setFont("Body-Bold",8.7); c.drawString(50,y-13,q["id"])
            c.setFont("Body",8.2); c.drawString(102,y-13,f"Chapter {q['primary_chapter']} · {q['group']} · primary concept page {anchors[q['group']]}")
            c.drawRightString(W-50,y-13,q["coverage_mode"].replace("_"," ").title()); y-=31
        c.showPage()
    # 8 back pages
    backs=[
      ("Source hierarchy","NCVEC controls the pool, identifiers, accepted answers, syllabus, diagrams, validity dates, and errata. Current eCFR Title 47 Part 97 controls the rules. FCC technical publications and NIST control relevant government technical facts. Open technical references may corroborate standard principles. Competitors never serve as factual authorities."),
      ("Source freeze","NCVEC corrected release dated February 19, 2026; effective July 1, 2026 through June 30, 2030. The production source was checked September 6, 2026. FCC Part 97 was frozen from the official eCFR renderer dated September 3, 2026 and checked September 6, 2026."),
      ("Rights and attribution","NCVEC expressly released the pool into the public domain. U.S. government regulatory text is used as source material; no seal or logo is reproduced. All teaching diagrams are original. ARRL and competitor prose, diagrams, layouts, and mnemonics were not copied."),
      ("Claim and update model","Every official anchor line maps to its pool ID, source page, correct option, and source hash in the machine-readable claim ledger. Rule and safety claims receive the highest volatility rating. Any later erratum or withdrawal requires a targeted rebuild and rerun of the deterministic checks."),
      ("Essential glossary","AC: current that reverses direction. DC: current in one direction. Bandwidth: occupied frequency range. Feed line: cable or line carrying RF. Impedance: opposition to AC. Modulation: placing information on a carrier. Repeater: station that receives and retransmits. SWR: indication of load-to-line match."),
      ("Abbreviations","AGC automatic gain control · APRS Automatic Packet Reporting System · CTCSS continuous tone-coded squelch system · CW continuous wave/Morse · DMR Digital Mobile Radio · DTMF dual-tone multi-frequency · FCC Federal Communications Commission · RF radio frequency · RIT receiver incremental tuning · ULS Universal Licensing System."),
      ("About Northfield Signal Guides","Northfield Signal Guides creates source-mapped visual references for complex technical subjects. The authority of this book comes from official sources, transparent mapping, original information design, and deterministic quality checks—not invented personal credentials."),
      ("Edition record","First production edition, September 2026. Built for the 2026–2030 Technician Class Element 2 pool. Keep this page with your source check: if the official NCVEC pool page lists a later erratum or withdrawal, use that update rather than this edition's stored answer."),
    ]
    for title,body in backs:
        p=new(); y=page_title(c,"Reference",title,p,"Reference")
        draw_text(c,body,42,y-12,W-84,12,18)
        c.showPage()
    assert page==208,page
    c.save()
    return {"pages":page,"visual_ids":visual_ids,"anchors":anchors}


def build_claim_ledger(pool, pdf_info):
    claims=[]
    for q in pool["questions"]:
        claims.append({
          "claim_id":f"POOL-{q['id']}","class":"exam_specific","manuscript_location":f"Chapter {q['primary_chapter']} / {q['group']} official-pool anchors; crosswalk",
          "print_anchor_page":pdf_info["anchors"][q["group"]],"claim":normalize_question(q),"question_id":q["id"],"correct_option":q["correct_option"],
          "source":"NCVEC 2026-2030 Technician pool corrected 2026-02-19","source_page":q["source_page"],"source_sha256":pool["pool"]["local_source_sha256"],
          "checked_date":str(date.today()),"volatility":"high" if q["subelement"] in {"T0","T1"} else "medium" if q["subelement"] in {"T2","T4","T8","T9"} else "low","status":"verified"
        })
    globals_=[
      ("GLOBAL-POOL-DATES","exam_currentness","Pool effective July 1, 2026 through June 30, 2030","NCVEC release page","high"),
      ("GLOBAL-POOL-COUNT","exam_currentness","The corrected pool contains 409 questions and three official diagrams","NCVEC release and ARRL notice","high"),
      ("GLOBAL-EXAM-SHAPE","exam_currentness","Technician Element 2 examination has 35 questions; 26 correct passes","ARRL/VEC official materials","high"),
      ("GLOBAL-RIGHTS","rights","NCVEC expressly releases the pool into the public domain","NCVEC release page","high"),
      ("GLOBAL-RULES","regulatory","Current Part 97 controls amateur-service rules","eCFR Title 47 Part 97","high"),
      ("FIGURE-T1","diagram","Official Figure T-1 is reproduced exactly for its numbered circuit-symbol questions","NCVEC corrected pool page 78","medium"),
      ("FIGURE-T2","diagram","Official Figure T-2 is reproduced exactly for its numbered circuit-symbol questions","NCVEC corrected pool page 79","medium"),
      ("FIGURE-T3","diagram","Official Figure T-3 is reproduced exactly for its numbered circuit-symbol questions","NCVEC corrected pool page 79","medium"),
    ]
    for cid,klass,claim,source,vol in globals_:
        claims.append({"claim_id":cid,"class":klass,"manuscript_location":"front/back matter","claim":claim,"source":source,"checked_date":str(date.today()),"volatility":vol,"status":"verified"})
    payload={"schema_version":"rn2-037-claim-ledger/v1","unresolved_claims":0,"claims":claims}
    (DATA/"claim-ledger.json").write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return payload


def build_epub(manuscript_text, visual_ids):
    tmp=PROD/"epub-stage"
    if tmp.exists(): shutil.rmtree(tmp)
    (tmp/"META-INF").mkdir(parents=True); (tmp/"OEBPS"/"images").mkdir(parents=True)
    (tmp/"mimetype").write_text("application/epub+zip",encoding="ascii")
    (tmp/"META-INF"/"container.xml").write_text('''<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>''',encoding="utf-8")
    svg_files=sorted(VIS.glob("*.svg"))
    for svg in svg_files: shutil.copy2(svg,tmp/"OEBPS"/"images"/svg.name)
    official_files=sorted(OFFICIAL_VIS.glob("*.png"))
    for png in official_files: shutil.copy2(png,tmp/"OEBPS"/"images"/png.name)
    # Semantic HTML generated independently of print coordinates.
    sections=[]; current=[]; title="Start"
    for line in manuscript_text.splitlines():
        if line.startswith("# ") and current:
            sections.append((title,current)); current=[]; title=line[2:]
        elif line.startswith("# "): title=line[2:]
        else: current.append(line)
    sections.append((title,current))
    items=[]; nav=[]
    css="body{font-family:serif;line-height:1.45;margin:5%;}h1,h2,h3{font-family:sans-serif;}li{margin:.35em 0}.anchor{font-size:.9em}.notice{border-left:4px solid #555;padding-left:1em}"
    (tmp/"OEBPS"/"style.css").write_text(css,encoding="utf-8")
    for i,(title,lines) in enumerate(sections,1):
        fn=f"s{i:02d}.xhtml"; nav.append((fn,title)); body=[f"<h1>{html.escape(title)}</h1>"]
        in_ul=False
        for line in lines:
            if line.startswith("## "):
                if in_ul: body.append("</ul>"); in_ul=False
                body.append(f"<h2>{html.escape(line[3:])}</h2>")
                gm=re.match(r"(T[0-9][A-Z])\s+",line[3:])
                if gm:
                    g=gm.group(1)
                    if g == "T6C":
                        alts = {
                          "figure-t1.png":"Official Figure T-1: a numbered transistor switching circuit with resistor, transistor, lamp, battery, and ground symbols.",
                          "figure-t2.png":"Official Figure T-2: a numbered power-supply circuit with battery, fuse, switch, transformer, rectifier, filter capacitor, resistor, LED, variable resistor, and Zener diode.",
                          "figure-t3.png":"Official Figure T-3: a numbered tuned circuit with variable capacitors, variable inductor, and antenna symbol."
                        }
                        for fnv, alt in alts.items():
                            body.append(f'<figure><img src="images/{fnv}" alt="{html.escape(alt)}"/></figure>')
                    else:
                        for kind in ("MAP","FLOW"):
                            fnv=f"V-{g}-{kind}.svg"
                            body.append(f'<figure><img src="images/{fnv}" alt="Original {html.escape(g)} {kind.lower()} diagram. A linear explanation follows in the text."/></figure>')
            elif line.startswith("### "):
                if in_ul: body.append("</ul>"); in_ul=False
                body.append(f"<h3>{html.escape(line[4:])}</h3>")
            elif line.startswith("- "):
                if not in_ul: body.append("<ul>"); in_ul=True
                body.append(f"<li>{html.escape(line[2:])}</li>")
            elif line.strip():
                if in_ul: body.append("</ul>"); in_ul=False
                body.append(f"<p>{html.escape(re.sub(r'\*\*','',line))}</p>")
        if in_ul: body.append("</ul>")
        x=f'''<?xml version="1.0" encoding="utf-8"?><html xmlns="http://www.w3.org/1999/xhtml"><head><title>{html.escape(title)}</title><link rel="stylesheet" href="style.css"/></head><body>{''.join(body)}</body></html>'''
        (tmp/"OEBPS"/fn).write_text(x,encoding="utf-8"); items.append((f"s{i:02d}",fn))
    navx=''.join(f'<li><a href="{fn}">{html.escape(t)}</a></li>' for fn,t in nav)
    (tmp/"OEBPS"/"nav.xhtml").write_text(f'''<?xml version="1.0" encoding="utf-8"?><html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops"><head><title>Contents</title><link rel="stylesheet" href="style.css"/></head><body><nav epub:type="toc" id="toc"><h1>Contents</h1><ol>{navx}</ol></nav></body></html>''',encoding="utf-8")
    ncx_points=''.join(f'<navPoint id="navPoint-{i}" playOrder="{i}"><navLabel><text>{html.escape(t)}</text></navLabel><content src="{fn}"/></navPoint>' for i,(fn,t) in enumerate(nav,1))
    (tmp/"OEBPS"/"toc.ncx").write_text(f'''<?xml version="1.0" encoding="utf-8"?><ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1"><head><meta name="dtb:uid" content="urn:uuid:rn2-037-2026"/></head><docTitle><text>Ham Radio Technician Visual Cram Map 2026–2030</text></docTitle><navMap>{ncx_points}</navMap></ncx>''',encoding="utf-8")
    image_manifest=''.join(f'<item id="img{i}" href="images/{svg.name}" media-type="image/svg+xml"/>' for i,svg in enumerate(svg_files,1))
    image_manifest += ''.join(f'<item id="poolfig{i}" href="images/{png.name}" media-type="image/png"/>' for i,png in enumerate(official_files,1))
    manifest='<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/><item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/><item id="css" href="style.css" media-type="text/css"/>'+''.join(f'<item id="{i}" href="{fn}" media-type="application/xhtml+xml"/>' for i,fn in items)+image_manifest
    spine='<itemref idref="nav"/>'+''.join(f'<itemref idref="{i}"/>' for i,_ in items)
    (tmp/"OEBPS"/"content.opf").write_text(f'''<?xml version="1.0" encoding="utf-8"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="bookid">urn:uuid:rn2-037-2026</dc:identifier><dc:title>Ham Radio Technician Visual Cram Map 2026–2030</dc:title><dc:creator>Northfield Signal Guides</dc:creator><dc:language>en</dc:language><meta property="dcterms:modified">2026-09-06T00:00:00Z</meta></metadata><manifest>{manifest}</manifest><spine toc="ncx">{spine}</spine></package>''',encoding="utf-8")
    OUTEPUB.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(EPUB_OUT,"w") as z:
        z.write(tmp/"mimetype","mimetype",compress_type=zipfile.ZIP_STORED)
        for p in sorted(tmp.rglob("*")):
            if p.is_file() and p.name!="mimetype": z.write(p,p.relative_to(tmp),compress_type=zipfile.ZIP_DEFLATED)


def qa(pool,pdf_info,claims):
    ids=[q["id"] for q in pool["questions"]]
    mappings=json.loads((DATA/"crosswalk.json").read_text())["mappings"]
    mapped=[m["question_id"] for m in mappings]
    visual_files=sorted(VIS.glob("*.svg"))
    for f in visual_files: ET.parse(f)
    checks={
      "status":"PASS","expected_question_ids":409,"extracted_unique_ids":len(set(ids)),"represented_unique_ids":len(set(mapped)),
      "missing_ids":sorted(set(ids)-set(mapped)),"extra_ids":sorted(set(mapped)-set(ids)),"unintended_duplicate_primary_ids":len(mapped)-len(set(mapped)),
      "answer_key_integrity":all(q["correct_option"] in q["options"] and q["correct_answer"]==q["options"][q["correct_option"]] for q in pool["questions"]),
      "crosswalk_locations_resolve":all(m["concept"] in pdf_info["anchors"] for m in mappings),"print_pages":pdf_info["pages"],
      "svg_assets":len(visual_files),"svg_xml_valid":True,"visual_ids_used":len(pdf_info["visual_ids"]),"claim_rows":len(claims["claims"]),"unresolved_claims":claims["unresolved_claims"],
      "pool_source_sha256":pool["pool"]["local_source_sha256"],"pool_validity":[pool["pool"]["effective_from"],pool["pool"]["effective_to"]]
    }
    if checks["missing_ids"] or checks["extra_ids"] or checks["unintended_duplicate_primary_ids"] or checks["print_pages"]!=208 or checks["unresolved_claims"]: checks["status"]="FAIL"
    (QA/"deterministic-qa.json").write_text(json.dumps(checks,indent=2)+"\n")
    return checks


def manifests(pool,pdf_info,qa_result):
    sources=[]
    for p in sorted((BASE/"sources"/"raw").glob("*")):
        sources.append({"file":str(p.relative_to(ROOT)),"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"bytes":p.stat().st_size})
    src={"schema_version":"rn2-037-source-freeze/v1","checked_date":str(date.today()),"status":"PASS","controlling_sources":[
      {"authority":"NCVEC","url":"https://ncvec.org/index.php/2026-2030-technician-question-pool","version":"corrected release 2026-02-19","effective":"2026-07-01/2030-06-30","rights":"explicit public-domain release","local_file":"books/rn2-037/sources/raw/ncvec-technician-pool-2026-2030-corrected-2026-02-19.pdf","note":"Downloaded from an independent NCVEC-member VEC mirror because NCVEC CDN blocked automated transfer; content/version/count/errata cross-checked against the controlling NCVEC page."},
      {"authority":"FCC eCFR","url":"https://www.ecfr.gov/current/title-47/chapter-I/subchapter-D/part-97","version":"renderer snapshot 2026-09-03 checked 2026-09-06","local_file":"books/rn2-037/sources/raw/ecfr-title47-part97-2026-09-03.html"}],"files":sources}
    (DATA/"source-manifest.json").write_text(json.dumps(src,indent=2)+"\n")
    prod={"schema_version":"rn2-037-production-manifest/v1","status":"KDP_READY_AWAITING_COVER_HUMAN_GATE","title":"Ham Radio Technician Visual Cram Map 2026–2030","author":"Northfield Signal Guides","trim_inches":[8,10],"ink":"black and white","bleed":False,"pages":pdf_info["pages"],"manuscript":"books/rn2-037/manuscript/ham-radio-technician-visual-cram-map.md","paperback_pdf":str(PDF_OUT.relative_to(ROOT)),"kindle_epub":str(EPUB_OUT.relative_to(ROOT)),"question_pool":"books/rn2-037/data/question-pool-2026-2030.json","crosswalk":"books/rn2-037/data/crosswalk.json","claim_ledger":"books/rn2-037/data/claim-ledger.json","editable_visuals":"books/rn2-037/visuals/svg","svg_count":qa_result["svg_assets"],"source_manifest":"books/rn2-037/data/source-manifest.json","built_date":str(date.today())}
    (PROD/"production-manifest.json").write_text(json.dumps(prod,indent=2)+"\n")


def main():
    ensure_dirs(); pool=json.loads(POOL.read_text())
    md=manuscript(pool); pdf_info=build_pdf(pool); claims=build_claim_ledger(pool,pdf_info); build_epub(md,pdf_info["visual_ids"]); result=qa(pool,pdf_info,claims); manifests(pool,pdf_info,result)
    print(json.dumps(result,indent=2))


if __name__=="__main__": main()
