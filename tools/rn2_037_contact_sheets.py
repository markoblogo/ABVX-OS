#!/usr/bin/env python3
"""Create RN2-037 print QA contact sheets from rendered page PNGs."""

from pathlib import Path
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"tmp"/"pdfs"/"rn2-037-full-v2"
OUT=ROOT/"books"/"rn2-037"/"qa"/"contact-sheets"
OUT.mkdir(parents=True,exist_ok=True)
files=sorted(SRC.glob("page-*.png"),key=lambda p:int(p.stem.split("-")[-1]))

def sheet(name,pages,cols,thumb_w):
    chosen=[files[p-1] for p in pages]
    tiles=[]
    ratio=10/8; thumb_h=int(thumb_w*ratio)
    for p,f in zip(pages,chosen):
        im=Image.open(f).convert("RGB"); im.thumbnail((thumb_w,thumb_h))
        tile=Image.new("RGB",(thumb_w+12,thumb_h+24),"white"); tile.paste(im,((tile.width-im.width)//2,18))
        ImageDraw.Draw(tile).text((4,3),str(p),fill="black"); tiles.append(tile)
    rows=(len(tiles)+cols-1)//cols
    out=Image.new("RGB",((thumb_w+12)*cols,(thumb_h+24)*rows),(218,218,218))
    for i,t in enumerate(tiles): out.paste(t,((i%cols)*t.width,(i//cols)*t.height))
    out.save(OUT/name,quality=90)

sheet("full-book-contact-sheet.jpg",list(range(1,209)),16,110)

groups_per_ch=[4,4,2,2,3,2,4,2,3,6,3]
openers=[]; visual=[]; p=9
for n in groups_per_ch:
    openers.append(p)
    base=p+2
    for i in range(n):
        visual += [base+i*4+1,base+i*4+2]
    p += 2+n*4
sheet("chapter-opening-contact-sheet.jpg",openers,4,220)
sheet("visual-system-contact-sheet.jpg",visual,10,145)
sheet("representative-page-qa-sheet.jpg",[1,3,5,9,11,12,13,23,24,25,26,99,100,181,201,208],4,220)
sheet("high-risk-page-contact-sheet.jpg",list(range(1,10))+[12]+list(range(180,209)),6,180)
print(OUT)
