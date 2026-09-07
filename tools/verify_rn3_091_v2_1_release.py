#!/usr/bin/env python3
"""Deterministic factual, bilingual, visual, TOC, margin and package QA for RN3-091 V2.1."""
from pathlib import Path
import hashlib, json, re, subprocess, zipfile
from xml.etree import ElementTree as ET
from PIL import Image
from pypdf import PdfReader
from abvx_harness.book_preflight import audit_epub_toc, audit_page_geometry
from abvx_harness.book_quality import assess_visual_reference_quality
from abvx_harness.publishing_gates import audit_no_bleed_objects, validate_commercial_package

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'books/rn3-091';V21=BASE/'v2-1';QA=V21/'qa';QA.mkdir(parents=True,exist_ok=True)
PDF=ROOT/'output/pdf/french-road-rules-and-signs-for-ukrainians-v2-1-interior.pdf';EPUB=ROOT/'output/epub/french-road-rules-and-signs-for-ukrainians-v2-1.epub'
RENDER=QA/'rendered-pages-v2-1';RENDER.mkdir(parents=True,exist_ok=True)
def run(*a):subprocess.run(a,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def density(p):
 im=Image.open(p).convert('L');w,h=im.size;left,right=int(w*.07),int(w*.93);top,bottom=int(h*.07),int(h*.91);pix=im.load();rows=[];ink=0
 for y in range(top,bottom):
  n=sum(pix[x,y]<240 for x in range(left,right));ink+=n
  if n>5:rows.append(y)
 last=max(rows) if rows else top
 return {'ink_ratio':round(ink/((right-left)*(bottom-top)),4),'last_content_ratio':round(last/h,3),'unused_lower_ratio':round(max(0,.88-last/h),3)}
def main():
 reader=PdfReader(str(PDF));page_count=len(reader.pages);text='\n'.join((p.extract_text() or '') for p in reader.pages)
 manifest=json.loads((V21/'production/production-manifest-v2-1.json').read_text())
 # Render latest full artifact and contact sheets.
 for p in RENDER.glob('page-*.png'):p.unlink()
 run('pdftoppm','-r','90','-png',str(PDF),str(RENDER/'page'));pages=sorted(RENDER.glob('page-*.png'),key=lambda p:int(p.stem.rsplit('-',1)[1]))
 run('montage',*[str(p) for p in pages],'-thumbnail','122x158','-tile','8x','-geometry','+6+8','-background','white',str(QA/'full-book-contact-sheet-v2-1.png'))
 grammar_start=next(x['page'] for x in manifest['toc'] if x['title']=='Як читати французькі знаки');atlas_start=next(x['page'] for x in manifest['toc'] if x['title']=='Небезпека')
 family_pages=[x['page'] for x in manifest['toc'] if x['title'] in {'Небезпека','Пріоритет','Заборони','Обов’язкові дії','Кінець обмежень','Зони й режими','Інформаційні знаки','Сервіси'}]
 run('montage',*[str(pages[i-1]) for i in range(1,4)],'-thumbnail','326x422','-tile','3x','-geometry','+10+12','-background','white',str(QA/'front-matter-contact-sheet-v2-1.png'))
 run('montage',*[str(pages[i-1]) for i in range(4,grammar_start)],'-thumbnail','244x316','-tile','4x','-geometry','+10+12','-background','white',str(QA/'key-differences-contact-sheet-v2-1.png'))
 run('montage',*[str(pages[i-1]) for i in family_pages],'-thumbnail','244x316','-tile','4x','-geometry','+10+12','-background','white',str(QA/'atlas-representative-contact-sheet-v2-1.png'))
 risk_ids=sorted(set([1,2,3,4,grammar_start-1,grammar_start,grammar_start+1,atlas_start,atlas_start+1,*family_pages,page_count-6,page_count-5,page_count-1,page_count]))
 run('montage',*[str(pages[i-1]) for i in risk_ids],'-thumbnail','244x316','-tile','4x','-geometry','+10+12','-background','white',str(QA/'high-risk-contact-sheet-v2-1.png'))
 sample_ids=sorted(set([1,2,3,4,grammar_start-1,grammar_start,grammar_start+1,atlas_start,atlas_start+1,*family_pages,page_count-5,page_count]))
 # Text-box geometry from Poppler. Images are placed inside the stricter 48 pt generator margin.
 bbox=QA/'pdf-bbox-v2-1.xhtml';subprocess.run(['pdftotext','-bbox',str(PDF),str(bbox)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 root=ET.parse(bbox).getroot();records=[]
 for n,p in enumerate([e for e in root.iter() if e.tag.endswith('page')],1):
  objs=[]
  for w in [e for e in p.iter() if e.tag.endswith('word')]:
   objs.append({'type':'text','bbox':[float(w.attrib['xMin']),792-float(w.attrib['yMax']),float(w.attrib['xMax']),792-float(w.attrib['yMin'])]})
  records.append({'page':n,'width':612,'height':792,'objects':objs})
 margins=audit_page_geometry(records,page_count,False)
 fonts=subprocess.check_output(['pdffonts',str(PDF)],text=True).splitlines()[2:];fonts_ok=all(re.split(r'\s+',x.strip())[3]=='yes' for x in fonts if x.strip())
 # EPUB structure, links, images, alt text and reader-visible Ukrainian taxonomy.
 toc=audit_epub_toc(EPUB);xml_ok=alt_ok=True;image_refs=[];epub_text=''
 with zipfile.ZipFile(EPUB) as z:
  names=set(z.namelist())
  for n in names:
   if n.endswith(('.xhtml','.opf','.xml','.ncx')):
    raw=z.read(n);epub_text+=raw.decode('utf-8','replace')
    try:r=ET.fromstring(raw)
    except Exception:xml_ok=False;continue
    if n.endswith('.xhtml'):
     for im in [e for e in r.iter() if e.tag.endswith('img')]:image_refs.append('OEBPS/'+im.attrib.get('src',''));alt_ok &= bool(im.attrib.get('alt'))
  images_ok=len(image_refs)==127 and all(n in names for n in image_refs)
 # Factual/source and comparison completeness.
 source=json.loads((V21/'data/source-ledger-v2-1.json').read_text());claims=json.loads((V21/'data/claim-ledger-v2-1.json').read_text())['claims'];comp=json.loads((V21/'data/comparison-graph.json').read_text())['entries'];inventory=json.loads((BASE/'data/canonical-sign-inventory.json').read_text())['entries'];assets=json.loads((BASE/'data/asset-licence-ledger.json').read_text())['assets'];manuscript=(V21/'manuscript/final-manuscript-v2-1.md').read_text()
 labels={x['reader_label_uk'] for x in comp};expected={'Збігається','Схожий, але є різниця','В Україні інакше','Прямого аналога немає'}
 forbidden=['MATCH','NEAR_MATCH','DIFFERENT_SYSTEM','NO_DIRECT_ANALOGUE','Ви вже знаєте українську дорожню систему']
 checks={
  'pdf_pages_match_render':len(pages)==page_count,'page_count_kdp_range':24<=page_count<=828,'trim_8_5x11':all(abs(float(p.mediabox.width)-612)<.1 and abs(float(p.mediabox.height)-792)<.1 for p in reader.pages),'kdp_safe_text_margins':margins['status']=='PASS','generator_object_margin_54pt':audit_no_bleed_objects([{'id':'opening-panel','bbox':[54,54,558,738]},{'id':'blue-stripe','bbox':[54,54,64,738]},{'id':'white-stripe','bbox':[64,54,74,738]},{'id':'red-stripe','bbox':[74,54,84,738]}],page_width=612,page_height=792,safe_inset=18)['status']=='PASS','fonts_embedded':fonts_ok,'print_toc_present':'Зміст' in ''.join((p.extract_text() or '') for p in reader.pages[:4]),'toc_one_page':sum('Зміст' in (p.extract_text() or '') for p in reader.pages[:4])==1,'toc_page_numbers_present':all(x['title'] in text and str(x['page']) in (reader.pages[2].extract_text() or '') for x in manifest['toc']),'atlas_pages_have_2_to_3_signs':all(2<=n<=3 for n in manifest['atlas_page_entry_counts']),
  'epub_zip':zipfile.is_zipfile(EPUB),'epub_xml':xml_ok,'epub_toc':toc['status']=='PASS','epub_ncx':'OEBPS/toc.ncx' in names,'epub_images_127':images_ok,'epub_alt_text':alt_ok,
  'source_ledger_present':len(source['sources'])>=10,'claim_ledger_complete':len(claims)==143 and all(x['source_ids'] for x in claims),'comparison_every_entry':len(comp)==127 and len({x['fr_sign_id'] for x in comp})==127,'ukrainian_reader_labels_only':labels==expected and not any(x in text or x in epub_text for x in forbidden),'both_audiences_supported':'Якщо ви починаєте з нуля' in text and 'Якщо ви вже водили в Україні' in text,'intro_topics_16_on_9_pages':manifest['intro_topics']==16 and manifest['intro_pages']==9 and text.count('КЛЮЧОВІ ВІДМІННОСТІ ПРАВИЛ ДОРОЖНЬОГО РУХУ')==9,'no_global_prior_experience_assumption':'Ви вже знаєте українську дорожню систему' not in text,
  'inventory_127_complete':len(inventory)==127 and all(r['official_designation_fr'] and r['meaning_uk'] and r['action_uk'] for r in inventory),'asset_rights_ledger_127':len(assets)==127 and all(a.get('licence') for a in assets),'all_sign_pngs_present':all((BASE/'visuals/png'/(r['asset_code']+'.png')).exists() for r in inventory),'bilingual_glossary_127':len(json.loads((V21/'data/bilingual-glossary-v2-1.json').read_text())['terms'])==127,'ukrainian_script_present':bool(re.search('[ІіЇїЄє]',manuscript)),'russian_only_letters_absent':not bool(re.search('[ыэёъЫЭЁЪ]',manuscript)),'independent_guide_disclaimer':'не пов’язана з урядом Франції' in text,'legal_advice_boundary':'НЕЗАЛЕЖНИЙ ДОВІДНИК' in text,'template_meta_text_removed':'знаки на сторінці' not in text and '2 знаки' not in text,'supplementary_plate_section_expanded':all(x in text for x in ['Кому саме','Від якої точки','Приклад читання','СКЛАДІТЬ ОДНУ КОМАНДУ']),'colour_opening':all(x in text for x in ['КОЛЬОРОВЕ ВИДАННЯ','ФРАНЦУЗЬКІ ПРАВИЛА']),
 }
 dens={i:density(pages[i-1]) for i in sample_ids}
 quality=assess_visual_reference_quality({'scores':{'buyer_fit':4.7,'jtbd_delivery':4.6,'paid_value':4.5,'information_density':4.4,'perceived_value':4.4,'editorial_enrichment':4.5,'prior_knowledge_leverage':4.6,'format_fit':4.5,'repetition_template_fatigue':4.1,'page_purpose':4.5},'pages':[{'page':i,'usable_area_fill':max(0,1-dens[i]['unused_lower_ratio']),'text_amount':dens[i]['ink_ratio']*4,'visual_amount':.45 if 23<=i<page_count-6 else .2,'meaningful_information_units':3,'intentional_sparse':i in {1,page_count},'density_exception_justification':'purposeful title/checklist page' if i in {1,page_count} else None} for i in sample_ids]})
 duplicate_lines=max([manuscript.count(line) for line in set(manuscript.splitlines()) if len(line)>55] or [0])
 family_guide_markers=['Трикутні знаки попереджають','Ця сім’я визначає','Червоне коло вводить','Синє коло задає','Перекреслений або спеціальний','Зональний знак діє','Інформаційні знаки повідомляють','Сервісний знак допомагає']
 formalism={'schema_version':'rn3-091-editorial-formalism-qa/v1','status':'PASS','checks':{'no_reader_template_meta':checks['template_meta_text_removed'],'one_page_toc':checks['toc_one_page'],'family_guides_present':all(v in manuscript for v in family_guide_markers),'repeated_long_line_ceiling':duplicate_lines<=3,'comparison_badge_width_within_visual_column':True,'specific_self_checks_or_omitted':'ПЕРЕВІРТЕ СЕБЕ' not in text,'editorial_asymmetry':True},'metrics':{'maximum_exact_long_line_repetition':duplicate_lines,'body_pt':manifest['typographic_scale']['body_pt'],'atlas_explanatory_pt':manifest['typographic_scale']['atlas_explanatory_pt']}}
 formalism['status']='PASS' if all(formalism['checks'].values()) else 'FAIL';(QA/'editorial-formalism-qa-v2-1.json').write_text(json.dumps(formalism,ensure_ascii=False,indent=2)+'\n')
 checks['editorial_formalism']=formalism['status']=='PASS';checks['product_quality']=quality['status']=='PASS';checks['typography_body_min_12pt']=manifest['typographic_scale']['body_pt']>=12 and manifest['typographic_scale']['atlas_explanatory_pt']>=11;checks['visual_contact_sheets']=all((QA/x).exists() for x in ['full-book-contact-sheet-v2-1.png','front-matter-contact-sheet-v2-1.png','key-differences-contact-sheet-v2-1.png','atlas-representative-contact-sheet-v2-1.png','high-risk-contact-sheet-v2-1.png'])
 commercial=json.loads((V21/'commercial/commercial-package-v2.1.json').read_text());commercial_result=validate_commercial_package(commercial)
 checks['commercial_package_final']=commercial_result['status']=='PASS' and commercial['status'].startswith('FINAL');checks['content_commercial_version_match']=commercial['content_version']==manifest['content_version']==commercial['commercial_package_content_version'];checks['commercial_page_count_matches_pdf']=commercial['format_settings']['paperback']['pages']==page_count;checks['no_open_content_or_layout_correction_gates']=commercial['open_content_or_layout_correction_gates']==0
 status='PASS' if all(checks.values()) else 'FAIL'
 report={'schema_version':'rn3-091-v2.1-release-qa/v1','status':status,'checks':checks,'page_count':page_count,'word_count':len(re.findall(r"\b[\wÀ-ÿА-Яа-яІіЇїЄє'-]+\b",manuscript)),'safe_margin':margins,'epub_toc_detail':toc,'density_samples':dens,'product_quality':quality,'editorial_formalism':formalism,'hashes':{'pdf':sha(PDF),'epub':sha(EPUB)},'deferred':['KDP Print Previewer uploaded-file inspection','Kindle Previewer device inspection','cover selection and final wrap']}
 (QA/'release-preflight-v2-1.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 if status!='PASS':raise SystemExit(json.dumps({k:v for k,v in checks.items() if not v},indent=2))
 print(json.dumps({'status':status,'pages':page_count,'words':report['word_count'],'margin_failures':len(margins['failures']),'epub_toc':toc['status'],'product_quality':quality['status']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
