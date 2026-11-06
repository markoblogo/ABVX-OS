"""Read-only quotation comparison against an owner-supplied DOCX/Kindle package.

No document execution, extraction of active resources, book editing or upload.
"""
from __future__ import annotations
import io
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile
from .book_readiness import (BASE, atomic, digest, directory, locked, plain, read,
                            source_documents, stamp, words, ValidationError)


def tokens(text):
    text=unicodedata.normalize('NFKC',text).replace('’',"'").replace('‘',"'")
    return [t.casefold() for t in words(plain(text))]


def document_bytes(path):
    with ZipFile(path) as archive:
        if 'word/document.xml' in archive.namelist():return Path(path).read_bytes()
        names=[x for x in archive.namelist() if x.lower().endswith('.docx')]
        if len(names)!=1:raise ValidationError('One unambiguous DOCX manuscript is required')
        if archive.getinfo(names[0]).file_size>20_000_000:raise ValidationError('Manuscript package exceeds bounded input size')
        return archive.read(names[0])


def paragraphs(data):
    with ZipFile(io.BytesIO(data)) as doc:
        info=doc.getinfo('word/document.xml')
        if info.file_size>20_000_000:raise ValidationError('Document text exceeds bounded input size')
        xml=ElementTree.fromstring(doc.read(info))
    ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    out=[]
    for i,p in enumerate(xml.findall('.//w:p',ns),1):
        text=''.join(t.text or '' for t in p.findall('.//w:t',ns)).strip()
        if text:out.append({'paragraph':i,'text':text,'tokens':tokens(text)})
    if not out:raise ValidationError('Manuscript contains no readable paragraphs')
    return out


def fragments(body):
    # Current native notebook posts separate observations with thematic breaks.
    for block in re.split(r'\n\s*---\s*\n',body):
        paras=[p for p in re.split(r'\n\s*\n',block.strip()) if p.strip()]
        paras=[p for p in paras if not p.startswith('#') and not (p.startswith('_') and p.endswith('_'))]
        text='\n\n'.join(paras).strip()
        if text:yield text


def compare_book(root,site,source,book_url):
    if not book_url.startswith(BASE+'/books/'):raise ValidationError('Existing canonical ABVX book URL required')
    raw=document_bytes(source);ps=paragraphs(raw);full=' '+' '.join(t for p in ps for t in p['tokens'])+' '
    docs,_,_,_=source_documents(root,Path(site));articles={};totals={'exact':0,'near_for_review':0,'not_matched':0,'short_unresolved':0}
    for url,(d,body,p,is_native) in docs.items():
        if not re.match(r'^psychology-notebook-\d+',d['slug']):continue
        results=[]
        for n,text in enumerate(fragments(body),1):
            ts=tokens(text);normalized=' '.join(ts);status='short_unresolved';match=None;ratio=None
            if len(ts)>=4:
                if ' '+normalized+' ' in full:
                    status='exact';match=next((x for x in ps if ' '+normalized+' ' in ' '+' '.join(x['tokens'])+' '),None);ratio=1
                else:
                    scored=[(SequenceMatcher(None,ts,x['tokens'],autojunk=False).ratio(),x) for x in ps if len(x['tokens'])>=4 and .4<=len(ts)/len(x['tokens'])<=2.5]
                    best=max(scored,key=lambda x:x[0]) if scored else (0,None)
                    ratio=round(best[0],3)
                    if best[0]>=.7:status='near_for_review';match=best[1]
                    else:status='not_matched'
            totals[status]+=1
            results.append({'number':n,'fragment_hash':digest(ts),'text':text,'words':len(ts),'status':status,'similarity':ratio,'book_paragraph':match['paragraph'] if match else None,'book_text':match['text'] if match else None})
        articles[url]={'id':d.get('id',d['slug']),'source_hash':digest([d,body]),'source_file':p,'source_is_native':is_native,'fragments':results}
    from hashlib import sha256
    source_hash=sha256(raw).hexdigest()
    result = {
        'schema_version': 1,
        'observed_at': stamp(),
        'book_url': book_url,
        'input_file': str(Path(source).resolve()),
        'input_sha256': sha256(Path(source).read_bytes()).hexdigest(),
        'manuscript_sha256': source_hash,
        'manuscript_english_words': sum((len(x['tokens']) for x in ps)),
        'manuscript_paragraphs': len(ps),
        'method': 'Case/typographic punctuation normalized English token sequence for exact matches; SequenceMatcher >=0.70 flags review only; fragments shorter than four words remain unresolved',
        'limitations': ['NOT_MATCHED is not proof of novelty: translations, paraphrases and coverage in other editions are unresolved', 'No page numbers inferred from DOCX paragraph indices', 'No literary authorship, ownership or commercial value inferred from similarity'],
        'summary': totals,
        'articles': articles,
        'publication_or_production_authorized': False,
    }
    lines=['# Psychology Notebook — existing-book quotation comparison','',f'Book: {book_url}',f'Manuscript: {source_hash}; {result["manuscript_english_words"]} English words, {len(ps)} nonempty paragraphs.',f'Summary: {totals}','',*result['limitations'],'']
    for a in articles.values():
        lines.extend(['## '+a['id'],'','| Fragment | Result | Book paragraph | Notebook text | Book text |','|---:|---|---:|---|---|'])
        for f in a['fragments']:
            cell=lambda x:(x or '').replace('|','\\|').replace('\n',' ')
            lines.append(f"| {f['number']} | {f['status']} | {f['book_paragraph'] or ''} | {cell(f['text'])} | {cell(f['book_text'])} |")
        lines.append('')
    with locked(root):
        target=directory(root)/'sources'/f'{source_hash}.docx';target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists() and target.read_bytes()!=raw:raise ValidationError('Stored manuscript hash collision')
        if not target.exists():target.write_bytes(raw)
        result['retained_manuscript']=str(target)
        atomic(directory(root)/'sources'/f'comparison-{source_hash}.json',result)
        atomic(directory(root)/'existing-book-overlap.json',result)
        atomic(directory(root)/'existing-book-overlap.md','\n'.join(lines))
    return result
