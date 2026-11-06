#!/usr/bin/env python3
"""Extract numbered PPTX slides for private editorial review; never publishes."""
import argparse, hashlib, json, os, re, shutil, subprocess, tempfile
from pathlib import Path

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('presentation',type=Path);p.add_argument('--slides',required=True,help='Comma-separated one-based slide numbers');p.add_argument('--output',required=True,type=Path);p.add_argument('--dpi',type=int,default=150);a=p.parse_args()
 source=a.presentation.resolve(strict=True)
 if source.suffix.lower()!='.pptx' or not source.is_file():p.error('A PPTX file is required')
 if not re.fullmatch(r'\d+(,\d+)*',a.slides):p.error('Use comma-separated positive slide numbers')
 slides=[int(n) for n in a.slides.split(',')]
 if not slides or min(slides)<1 or len(set(slides))!=len(slides):p.error('Slide numbers must be positive and unique')
 if not 72<=a.dpi<=300:p.error('DPI must be 72–300')
 for tool in ('soffice','pdfinfo','pdftotext','pdftoppm'):
  if not shutil.which(tool):p.error('Missing executable: '+tool)
 out=a.output.resolve()
 if out.exists():p.error('Output already exists; choose a new private directory')
 out.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='abvx-slide-review-') as tmp:
  t=Path(tmp);pdf=t/(source.stem+'.pdf');profile=(t/'lo-profile').as_uri()
  subprocess.run(['soffice','-env:UserInstallation='+profile,'--headless','--convert-to','pdf','--outdir',str(t),str(source)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=120)
  info=subprocess.check_output(['pdfinfo',str(pdf)],text=True);match=re.search(r'^Pages:\s+(\d+)',info,re.M)
  if not match or max(slides)>int(match.group(1)):raise ValueError('Requested slide number exceeds PDF page count')
  text=subprocess.check_output(['pdftotext','-layout',str(pdf),'-'],text=True).split('\f')
  stage=t/'result';stage.mkdir()
  records=[]
  for n in slides:
   subprocess.run(['pdftoppm','-f',str(n),'-l',str(n),'-singlefile','-png','-r',str(a.dpi),str(pdf),str(stage/f'slide-{n:03}')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=60)
   image=stage/f'slide-{n:03}.png';(stage/f'slide-{n:03}.txt').write_text(text[n-1],encoding='utf-8')
   records.append({'slide':n,'image':image.name,'sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'text':f'slide-{n:03}.txt'})
  manifest={'sourceName':source.name,'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'sourceSlides':int(match.group(1)),'renderedDpi':a.dpi,'slides':records,'note':'Rendered archive material for editorial review. Check owner rights, crop and original-vs-reference status before publication.'}
  (stage/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
  shutil.copytree(stage,out)
 print(json.dumps({'status':'prepared','slides':len(slides),'output':str(out)}))
if __name__=='__main__':main()
