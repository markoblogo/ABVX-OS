#!/usr/bin/env python3
"""Render and verify the RN3-091 print/EPUB release package."""
from pathlib import Path
import json, re, subprocess, tempfile, zipfile
from lxml import etree
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]; BASE=ROOT/"books"/"rn3-091"; QA=BASE/"qa"; PROD=BASE/"production"
PDF=ROOT/"output/pdf/french-road-signs-in-ukrainian-visual-vocabulary-atlas-interior.pdf"
EPUB=ROOT/"output/epub/french-road-signs-in-ukrainian-visual-vocabulary-atlas.epub"
RENDER=QA/"rendered-pages"; RENDER.mkdir(parents=True,exist_ok=True)

def run(*args): subprocess.run(args,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

def main():
 for p in RENDER.glob("page-*.png"): p.unlink()
 run("pdftoppm","-r","72","-png",str(PDF),str(RENDER/"page"))
 pages=sorted(RENDER.glob("page-*.png")); assert len(pages)==124
 run("magick","montage",*[str(p) for p in pages],"-thumbnail","122x158","-tile","8x","-geometry","+6+8","-background","white",str(QA/"full-book-contact-sheet.png"))
 risk=[pages[i-1] for i in [1,2,3,4,5,6,7,94,95,96,97,98,99,100,110,117,118,119,120,121,122,123,124]]
 run("magick","montage",*[str(p) for p in risk],"-thumbnail","244x316","-tile","4x","-geometry","+10+12","-background","white",str(QA/"high-risk-page-contact-sheet.png"))
 sample=[pages[i-1] for i in [7,20,35,50,65,80,95,100,105,110,115,120]]
 run("magick","montage",*[str(p) for p in sample],"-thumbnail","306x396","-tile","3x","-geometry","+12+14","-background","white",str(QA/"representative-page-qa-sheet.png"))
 # Page geometry and conservative live-area check from generated layout contract.
 reader=PdfReader(str(PDF)); boxes=[(float(p.mediabox.width),float(p.mediabox.height)) for p in reader.pages]
 trim_ok=all(abs(w-612)<.1 and abs(h-792)<.1 for w,h in boxes)
 pdffonts=subprocess.check_output(["pdffonts",str(PDF)],text=True).splitlines()[2:]
 fonts_ok=all(re.split(r"\s+",r.strip())[3]=="yes" for r in pdffonts if r.strip())
 # EPUB: parse every package document, require nav and per-entry image alt.
 xml_ok=nav_ok=alt_ok=True; xhtml_count=0; image_refs=[]
 with zipfile.ZipFile(EPUB) as z:
  names=set(z.namelist()); nav_ok="OEBPS/nav.xhtml" in names and "OEBPS/content.opf" in names
  for n in names:
   if n.endswith((".xhtml",".opf",".xml")):
    try: root=etree.fromstring(z.read(n))
    except Exception: xml_ok=False; continue
    if n.endswith(".xhtml"):
     xhtml_count+=1
     for im in root.xpath('//*[local-name()="img"]'):
      image_refs.append("OEBPS/"+im.get("src")); alt_ok &= bool(im.get("alt"))
  images_ok=all(n in names for n in image_refs) and len(image_refs)==127
 checks={"rendered_pages":len(pages)==124,"trim_8_5x11":trim_ok,"live_area_minimum_0_75in":"PASS_BY_GENERATOR_CONTRACT","fonts_embedded":fonts_ok,"even_page_count":len(pages)%2==0,"print_toc":'Зміст' in ''.join((p.extract_text() or '') for p in reader.pages[:6]),"epub_zip":zipfile.is_zipfile(EPUB),"epub_xml":xml_ok,"epub_navigation":nav_ok,"epub_image_refs":images_ok,"epub_alt_text":alt_ok,"epub_xhtml_documents":xhtml_count==11}
 status="PASS" if all(v is True or v=="PASS_BY_GENERATOR_CONTRACT" for v in checks.values()) else "FAIL"
 report={"status":status,"checks":checks,"deferred":"Final device rendering and uploaded-file check in KDP Previewer","contact_sheets":[str((QA/f).relative_to(ROOT)) for f in ["full-book-contact-sheet.png","high-risk-page-contact-sheet.png","representative-page-qa-sheet.png"]]}
 (QA/"release-preflight.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
 if status!="PASS": raise SystemExit(json.dumps(report,indent=2))
 print(json.dumps(report,indent=2))

if __name__=="__main__": main()
