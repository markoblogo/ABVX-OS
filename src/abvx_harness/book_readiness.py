"""Derived, private editorial inventory over existing site sources and OS intakes.

No manuscript export, network, scoring mutation, research execution or publication.
"""
from __future__ import annotations
import argparse
import fcntl
import hashlib
import html
import json
import math
import os
import re
import tempfile
from collections import Counter
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo
from .harness import ValidationError

VERSION = 1
STAGES = ('collecting', 'outline_ready', 'manuscript_candidate', 'editorial_review')
BASE = 'https://abvx.xyz'

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

def stamp():
    return datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')

def directory(root):
    return Path(root) / '.tmp/book-readiness'

def read(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default

def atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, ensure_ascii=False, indent=2) + '\n' if not isinstance(value, str) else value
    fd, temp = tempfile.mkstemp(dir=path.parent, prefix='.' + path.name)
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(text); f.flush(); os.fsync(f.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp): os.unlink(temp)

@contextmanager
def locked(root):
    d = directory(root); d.mkdir(parents=True, exist_ok=True)
    if d.is_symlink(): raise ValidationError('Readiness directory cannot be a symlink')
    with (d / 'lock').open('a') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        yield

def policy(root):
    c = read(Path(root) / 'book-radar/readiness-policy.json')
    if not isinstance(c, dict) or c.get('schema_version') != VERSION:
        raise ValidationError('Readiness policy v1 required')
    ids = set()
    for item in c['candidates']:
        if not re.fullmatch(r'[a-z0-9-]+', item['id']) or item['id'] in ids:
            raise ValidationError('Unique safe candidate ID required')
        ids.add(item['id'])
        if item['selector'] not in {'kitchen-recipes','kitchen-stories','working-stories','psychology-notebook','art'}:
            raise ValidationError('Unsupported candidate selector')
        lo, hi = item['target_pages']
        if not 1 <= lo <= hi <= 2000: raise ValidationError('Invalid planning page range')
        for level in ('outline','manuscript'):
            for key in ('entries','words','themes'):
                x = item[level][key]
                if isinstance(x,bool) or not isinstance(x,int) or x < 0: raise ValidationError('Nonnegative editorial target required')
    if not 1 <= c['review_interval_days'] <= 366: raise ValidationError('Invalid review interval')
    for key in ('prose_words_per_page','illustrated_words_per_page','visual_pages_per_asset','front_matter_pages'):
        lo,hi = c['page_model'][key]
        if not 0 <= lo <= hi or (key.endswith('words_per_page') and lo == 0):
            raise ValidationError('Invalid page model')
    return c

def parse_source(text):
    m = re.fullmatch(r'---\s*\n(.*?)\n---\s*\n(.*)', text, re.S)
    if not m: raise ValidationError('Expected complete JSON-frontmatter source')
    d = json.loads(m[1])
    if not isinstance(d,dict) or not d.get('slug') or not d.get('title'):
        raise ValidationError('Source requires slug and title')
    return d,m[2]

def plain(text):
    text = re.sub(r'(?ms)^```.*?^```[^\n]*', '', text)
    text = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'https?://\S+', '', text)
    return html.unescape(text)

def words(text):
    # Declared-English prose only; Latin-script tokens, not headings/frontmatter URLs/code.
    return re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]+(?:['’\-][A-Za-zÀ-ÖØ-öø-ÿ]+)*", text)

def metrics(body, language):
    text = plain(body)
    tokens = words(text) if language == 'en' else []
    chunks = []
    for i, block in enumerate(re.split(r'\n\s*\n', text)):
        ts = words(block) if language == 'en' else []
        if ts: chunks.append({'hash':digest([t.casefold() for t in ts]),'words':len(ts),'shared_dedup':len(ts)>=20})
    return {'english_words':len(tokens),'body_hash':digest(text.split()),'chunks':chunks}

def canonical(d, working=False):
    path = d.get('canonicalPath') or ('/writing/working-stories/' if working else '/writing/') + d['slug']
    if not path.startswith('/') or path.startswith('//') or '?' in path or '#' in path:
        raise ValidationError('Unsafe canonical source path')
    return BASE + path.rstrip('/')

def source_documents(root,site):
    from .runtime_publication import runtime_inventory
    runtime=runtime_inventory(site)
    index = read(site/'public/content-index.json')
    if runtime:
        combined={i['canonicalUrl']:i for i in runtime[2]['items']}
        for i in (index or {}).get('items',[]):
            if i.get('canonicalUrl') not in runtime[4]:combined[i['canonicalUrl']]=i
        index={'items':list(combined.values())}
    if not isinstance(index,dict) or not isinstance(index.get('items'),list):
        raise ValidationError('Existing deployed content index is required')
    indexed = {i.get('canonicalUrl') for i in index['items']}
    docs = {}; provenance = {}; drafts = []
    # OS intakes are references, never a second canonical content store.
    for p in sorted((Path(root)/'content/items').glob('*.json')):
        item = read(p)
        if item.get('project') != 'abvxsite': continue
        payload = item.get('payload',{})
        if not payload.get('source_markdown'): continue
        d,b = parse_source(payload['source_markdown'])
        if d.get('type') not in {'working-story','note','article','review','build_log','other','recipe'}: continue
        url = canonical(d,d.get('type')=='working-story')
        refs = provenance.setdefault(url,[])
        refs.append({'intake_id':item['id'],'item_file':str(p),'source_refs':payload.get('source_refs',[]),'source_sha256':payload.get('source_sha256'),'media_assets':payload.get('media_assets',[]),'handoff_status':item['status']})
        drafts.append((url,d,b,str(p),False))
    withdrawn=runtime[1] if runtime else set()
    if runtime:docs.update(runtime[0])
    for folder in ('writing','working-stories'):
        for p in sorted((site/'content'/folder).glob('*.md')):
            if p.name.startswith('_'): continue
            d,b = parse_source(p.read_text())
            url = canonical(d,folder=='working-stories')
            if runtime and url in runtime[4]:continue
            if url in docs and not (runtime): raise ValidationError('Conflicting canonical sources: '+url)
            docs[url]=(d,b,str(p),True)
    # Accepted/prepared Psychology Notebook drafts already have native frontmatter.
    for p in sorted((site/'exports/psychology-notebook/posts').glob('*.md')):
        d,b = parse_source(p.read_text()); url=canonical(d)
        if url not in docs and url not in withdrawn: docs[url]=(d,b,str(p),False)
    for url,d,b,p,_ in drafts:
        if url not in docs and url not in withdrawn: docs[url]=(d,b,p,False)
    return docs,provenance,indexed,len({u for u in indexed if u and urlsplit(u).hostname not in {'abvx.xyz','www.abvx.xyz'}})

def file_asset(site,src,**extra):
    asset={'src':src,'available':False,'sha256':None,'original_available':False,'rights':'UNKNOWN',**extra}
    if isinstance(src,str) and src.startswith('/media/'):
        p=(site/'public'/src.lstrip('/')).resolve()
        if not p.is_relative_to((site/'public').resolve()): raise ValidationError('Media path escapes public root')
        if p.is_file(): asset.update(available=True,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
        elif src.startswith('/media/writing/runtime/'):
            from .runtime_publication import runtime_inventory
            runtime=runtime_inventory(site)
            record=runtime[3].get(src.rsplit('/',1)[-1]) if runtime else None
            if record and record.get('publicPath')==src:asset.update(available=True,sha256=record['sha256'],availability_evidence='COMMITTED_RUNTIME_ASSET_UNVERIFIED_HTTP')
    return asset

def original_evidence(asset,refs):
    out=[]
    for ref in refs:
        for item in ref['media_assets']:
            if item.get('target') != asset['src'] and item.get('sha256') != asset['sha256']: continue
            src=Path(item.get('source',''))
            if src.is_file(): out.append({'path':str(src),'role':'approved_source_asset','available':True})
            process=read(src.parent/'photo-processing.json',{})
            for photo in process.get('photos',[]):
                if photo.get('editedSha256') == asset['sha256']:
                    p=Path(photo['original'])
                    if p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==photo['originalSha256']:
                        out.append({'path':str(p),'role':'original_photograph','available':True})
            auth=read(src.parent/'authorization-and-source.json',{})
            for p in (src.parent/'source').glob('*original*'):
                if p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==auth.get('originalCoverSha256'):
                    out.append({'path':str(p),'role':'original_illustration','available':True})
    asset['source_assets']=out
    asset['original_available']=any(x['role'].startswith('original_') for x in out)

def collect(root,site,old,config,as_of):
    docs,provenance,indexed,external = source_documents(root,site)
    claims=read(directory(root)/'owner-claims.json',{})
    overlap=read(directory(root)/'existing-book-overlap.json',{})
    psych_root=site/'exports/psychology-notebook'
    psych=read(psych_root/'registry.json',{})
    art=read(psych_root/'artwork/registry.json',{}).get('artworks',[])
    art_by_src={x.get('sharedAssetTarget'):x for x in art}
    archive_ok=bool(claims.get('psychology_archive_sha256')) and claims['psychology_archive_sha256']==psych.get('sourceSha256')
    articles={};analyzed=0;reused=0
    for url,(d,body,p,is_native) in docs.items():
        fingerprint=digest([d,body]); prev=old.get('articles',{}).get(url)
        if prev and prev.get('source_hash')==fingerprint:
            m=prev['metrics'];reused+=1
        else:
            m=metrics(body,d.get('language','en'));analyzed+=1
        tags=sorted(set(d.get('tags',d.get('topics',[]))))
        is_psych='psychology-notebook' in tags or d['slug'].startswith('psychology-notebook-')
        collection='psychology-notebook' if is_psych else d.get('collection') or ('working-stories' if d.get('type')=='working-story' else 'general-writing')
        status='published' if is_native and url in indexed and d.get('visibility','draft')=='public' else 'draft'
        if (d.get('publishedAt') or d.get('date') or '') > as_of: status='scheduled'
        if d.get('visibility')=='private': status='private'
        assets=[]
        for name in ('media','heroImage','coverImage'):
            if d.get(name) and d[name]['src'] not in [a['src'] for a in assets]: assets.append(file_asset(site,d[name]['src'],kind='cover'))
        for image in d.get('illustrations',[]):
            if image['src'] not in [a['src'] for a in assets]: assets.append(file_asset(site,image['src'],kind='illustration',caption=image.get('caption')))
        refs=provenance.get(url,[])
        for a in assets:
            original_evidence(a,refs)
            art_source=art_by_src.get(a['src']) or next((art_by_src[media['target']] for ref in refs for media in ref['media_assets'] if media.get('sha256')==a['sha256'] and media.get('target') in art_by_src),None)
            if art_source:
                original=psych_root/art_source['privateOriginal']
                a['original_available']=original.is_file() and hashlib.sha256(original.read_bytes()).hexdigest()==art_source['sourceSha256']
                a['source_assets'].append({'path':str(original),'role':'original_artwork','available':a['original_available']})
                a['rights']='OWNER_CONFIRMED' if art_source['sourceSha256'] in claims.get('artwork_source_hashes',[]) else 'UNKNOWN'
        annotation=config.get('article_annotations',{}).get(d.get('id',d.get('story_id',d['slug'])),{})
        if annotation.get('source_hash') not in (None,fingerprint): annotation={}
        rights='OWNER_CONFIRMED' if is_psych and archive_ok else 'UNKNOWN'
        rights_basis=digest(claims) if rights=='OWNER_CONFIRMED' else None
        if annotation.get('rights')=='cleared' and annotation.get('source_hash')==fingerprint and annotation.get('evidence'):
            rights='EVIDENCE_CONFIRMED';rights_basis=annotation['evidence']
        if annotation.get('rights')=='blocked': rights='BLOCKED'
        if annotation.get('visual_rights')=='cleared' and annotation.get('source_hash')==fingerprint and annotation.get('evidence'):
            for asset in assets:asset.update(rights='EVIDENCE_CONFIRMED',rights_basis=annotation['evidence'])
        links=re.findall(r'\]\(([^)]+)\)',body)
        links += [x.get('url','') for x in d.get('links',[])]
        if d.get('caseStudy'): links.append(d['caseStudy']['url'])
        related=sorted(set(x for x in links if x.startswith(('/books/','/work/',BASE+'/books/',BASE+'/work/'))))
        existing_books=[claims['existing_book_url']] if is_psych and claims.get('existing_book_url') else []
        limitations=[]
        if rights=='UNKNOWN': limitations.append('Text republication rights not recorded; inventory volume is provisional')
        if rights=='BLOCKED': limitations.append('Explicit rights restriction')
        if is_psych: limitations.append('Existing-book fragment overlap NOT_MAPPED; new-volume word count UNKNOWN')
        if d.get('book',{}).get('include') is False or d.get('book',{}).get('status')=='excluded' or annotation.get('exclude'):
            limitations.append('Excluded by existing editorial selection')
        types='notebook' if is_psych else 'case_study' if collection=='working-stories' else 'recipe' if d.get('recipe') else d.get('type','essay')
        articles[url] = {
            'id': d.get('id', d.get('story_id', d['slug'])),
            'canonical_url': url,
            'title': d['title'],
            'collection': collection,
            'series': sorted(set([x for x in [d.get('series'), *d.get('seriesSlugs', [])] if x] + (['borscht-stories'] if 'borscht-stories' in tags else []) + (['psychology-notebook'] if is_psych else []))),
            'status': status,
            'language': d.get('language', 'en'),
            'content_type': types,
            'english_word_count': m['english_words'],
            'source_file': p,
            'source_hash': fingerprint,
            'metrics': m,
            'assets': assets,
            'provenance': refs,
            'related_projects': d.get('relatedSlugs', []),
            'existing_relationships': related,
            'existing_books': sorted(set(existing_books + [x if x.startswith('https:') else BASE + x for x in related if '/books/' in x])),
            'book_selection': d.get('book'),
            'rights': rights,
            'rights_basis': rights_basis,
            'limitations': limitations,
            'tags': tags,
            'potential_books': [],
            'publication_basis': 'native source and deployed index' if status == 'published' else 'source exists; no publication inferred',
            'new_book_words': None if is_psych else m['english_words'],
        }
        comparison=overlap.get('articles',{}).get(url,{})
        if is_psych and comparison.get('source_hash')==fingerprint:
            articles[url]['existing_book_comparison']={'book_url':overlap['book_url'],'manuscript_sha256':overlap['manuscript_sha256'],'fragments':[{k:f[k] for k in ('fragment_hash','words','status','book_paragraph')} for f in comparison['fragments']]}
            articles[url]['existing_books']=sorted(set(articles[url]['existing_books']+[overlap['book_url']]))
            articles[url]['limitations']=[x for x in articles[url]['limitations'] if not x.startswith('Existing-book fragment overlap')]+['Exact existing-book overlap mapped; paraphrases/translation variants and new-volume eligibility still require review']
    # Art remains linked to its existing source registry, never copied into another content DB.
    for row in art:
        key='art:'+row['id'];src=row.get('sharedAssetTarget');asset=file_asset(site,src,kind='artwork')
        original=psych_root/row['privateOriginal'];asset['original_available']=original.is_file() and hashlib.sha256(original.read_bytes()).hexdigest()==row['sourceSha256']
        asset['source_assets']=[{'path':str(original),'role':'original_artwork','available':asset['original_available']}]
        if not asset['available']:
            derivative=psych_root/row['derivativeFile']
            if derivative.is_file():asset.update(available=True,sha256=hashlib.sha256(derivative.read_bytes()).hexdigest(),private_derivative=str(derivative))
        rights='OWNER_CONFIRMED' if row['sourceSha256'] in claims.get('artwork_source_hashes',[]) else 'UNKNOWN'
        asset['rights']=rights
        articles[key] = {
            'id': row['id'],
            'canonical_url': None,
            'title': 'Sketchbook artwork ' + str(row.get('displayNumber', row['id'])),
            'collection': 'art',
            'series': ['sketchbook'],
            'status': 'published' if any((x.get('publicationStatus') == 'PUBLISHED_VERIFIED' for x in row.get('usedBy', []))) else 'draft',
            'language': None,
            'content_type': 'artwork',
            'english_word_count': 0,
            'source_file': str(psych_root / 'artwork/registry.json'),
            'source_hash': row['sourceSha256'],
            'metrics': {'english_words': 0, 'body_hash': row['sourceSha256'], 'chunks': []},
            'assets': [asset],
            'provenance': {'registry_id': row['id'], 'owner_provenance': row.get('ownerProvenance'), 'used_by': row.get('usedBy', [])},
            'related_projects': row.get('relatedProjectUrls', []),
            'existing_relationships': [],
            'existing_books': [],
            'book_selection': None,
            'rights': rights,
            'rights_basis': digest(claims) if rights == 'OWNER_CONFIRMED' else None,
            'limitations': [] if rights == 'OWNER_CONFIRMED' else ['Visual republication rights not recorded'],
            'tags': ['sketchbook'],
            'potential_books': [],
            'publication_basis': 'existing artwork use registry',
            'new_book_words': 0,
        }
    return articles,{'analyzed':analyzed,'reused':reused,'external_metadata_only_excluded':external},claims

def selected(a,selector):
    if selector=='kitchen-recipes':return a['collection']=='kitchen-notes' and a['content_type']=='recipe'
    if selector=='kitchen-stories':return a['collection']=='kitchen-notes'
    return a['collection']==selector

def page_ranges(count,visuals,c):
    p=c['page_model'];wlo,whi=p['prose_words_per_page'];ilo,ihi=p['illustrated_words_per_page'];vlo,vhi=p['visual_pages_per_asset'];flo,fhi=p['front_matter_pages']
    # Round outward to blocks of four: explicitly uncertain planning, never a print layout.
    rounded=lambda lo,hi:[int(math.floor(lo/4)*4),int(math.ceil(hi/4)*4)]
    return {'manuscript':rounded(count/whi+flo,count/wlo+fhi),'illustrated':rounded(count/ihi+visuals*vlo+flo,count/ilo+visuals*vhi+fhi),'basis':'ESTIMATE: configurable density, 0.5–1 visual pages per asset, front matter; no trim-size/layout proof'}

def candidates(articles,config,assessments,old):
    definitions=list(config['candidates'])
    for name,terms in config.get('emerging_themes',{}).items():
        matches=[a for a in articles.values() if a['status']=='published' and a['english_word_count']>=config['substantial_entry_words'] and any(re.search(r'(?<![a-z])'+re.escape(t)+r'(?![a-z])',' '.join(a['tags'])+' '+a['title'].casefold()) for t in terms)]
        if len(matches)>=config['emerging_min_entries'] and len({a['collection'] for a in matches})>=config['emerging_min_collections']:
            definitions.append({'id':'emerging-'+name,'title':'Emerging: '+name.replace('-',' '),'selector':'emerging','members':[a['id'] for a in matches],'target_pages':[120,200],'outline':{'entries':6,'words':10000,'themes':3},'manuscript':{'entries':20,'words':36000,'themes':4,'visual_coverage':0},'personal_value':'Cross-collection topic hypothesis; coherence requires editorial assessment'})
    result={}
    for d in definitions:
        members=sorted([a for a in articles.values() if (a['id'] in d.get('members',[]) if d['selector']=='emerging' else selected(a,d['selector']))],key=lambda a:(a['status']!='published',a['id']))
        for a in members:a['potential_books'].append(d['id'])
        available=[a for a in members if (a['status']=='published' or d['selector']=='art') and a['language'] in ('en',None) and a['rights']!='BLOCKED' and 'Excluded by existing editorial selection' not in a['limitations']]
        seen=set();unique=[];duplicates=[];chunks=set();word_count=0;cleared=0;visuals=set();originals=set()
        for a in available:
            bh=a['metrics']['body_hash']
            if bh in seen:duplicates.append(a['id']);continue
            seen.add(bh);unique.append(a)
            for i,ch in enumerate(a['metrics']['chunks']):
                k=ch['hash'] if ch['shared_dedup'] else (a['id'],i)
                if k in chunks:continue
                chunks.add(k);word_count+=ch['words']
                if a['rights'] in ('OWNER_CONFIRMED','EVIDENCE_CONFIRMED'):cleared+=ch['words']
            for asset in a['assets']:
                if asset['available']:visuals.add(asset['sha256'])
                if asset['original_available']:originals.add(asset['sha256'] or asset['src'])
        substantial=sum(a['english_word_count']>=config['substantial_entry_words'] or d['selector']=='art' for a in unique)
        topics=Counter(t for a in unique for t in a['tags'] if t not in {'saved-find','kitchen-notes','psychology-notebook','sketchbook'})
        diversity=len(topics) if d['selector']!='art' else (1 if unique else 0)
        fingerprint=digest([(a['id'],a['source_hash'],[(v['src'],v['sha256']) for v in a['assets']]) for a in members]);assessment=assessments.get(d['id'],{})
        current=assessment.get('member_digest')==fingerprint
        cohesion=assessment.get('cohesion')=='confirmed' and current
        pages=page_ranges(word_count,len(visuals),config)
        coverage=sum(any(x['available'] for x in a['assets']) for a in unique)/max(1,len(unique))
        visual_rights_coverage=sum(any(x['available'] and x.get('rights') in ('OWNER_CONFIRMED','EVIDENCE_CONFIRMED') for x in a['assets']) for a in unique)/max(1,len(unique))
        gaps=[];stage='collecting';outline=d['outline'];target=d['manuscript']
        if substantial>=outline['entries'] and word_count>=outline['words'] and diversity>=outline['themes']:stage='outline_ready'
        for label,value,wanted in [('substantial entries',substantial,target['entries']),('unique English words',word_count,target['words']),('topic diversity',diversity,target['themes'])]:
            if value<wanted:gaps.append(f'{label}: {value} available; planning reference {wanted} (not a writing quota)')
        if coverage<target.get('visual_coverage',0):gaps.append('Visual coverage below the illustrative planning reference')
        if visual_rights_coverage<target.get('visual_coverage',0):gaps.append('Book-republication rights for planned visuals need confirmation')
        estimated=pages['illustrated' if target.get('visual_coverage') else 'manuscript']
        pagination=estimated[1]>=d['target_pages'][0] and estimated[0]<=d['target_pages'][1]
        if not pagination:gaps.append('Estimated pagination does not yet overlap the planning range')
        if not cohesion:gaps.append('Current-source thematic cohesion and chapter structure need editorial confirmation')
        restrictions=sum(a['rights']=='UNKNOWN' for a in unique)
        if restrictions:gaps.append(f'Republication rights unresolved for {restrictions} entries; volume is provisional')
        if d.get('inventory_only'):gaps.append('Thematic inventory only; map fragment overlap with the existing book before a new-volume proposal')
        novel=None if any(a['new_book_words'] is None for a in unique) else word_count
        if stage=='outline_ready' and all([substantial>=target['entries'],word_count>=target['words'],diversity>=target['themes'],coverage>=target.get('visual_coverage',0),pagination,cohesion,restrictions==0,visual_rights_coverage>=target.get('visual_coverage',0),assessment.get('gaps_resolved') is True,not d.get('inventory_only')]):stage='manuscript_candidate'
        if stage=='manuscript_candidate' and assessment.get('accepted_for_editorial_review') is True:stage='editorial_review'
        recipes=sum(a['content_type']=='recipe' for a in unique);cases=sum(a['content_type']=='case_study' for a in unique)
        known_overlap={f['fragment_hash']:f['words'] for a in unique for f in a.get('existing_book_comparison',{}).get('fragments',[]) if f['status']=='exact'}
        result[d['id']] = {
            'id': d['id'],
            'title': d['title'],
            'stage': stage,
            'entries': len(unique),
            'substantial_entries': substantial,
            'published_entries': sum((a['status'] == 'published' for a in unique)),
            'draft_entries': sum((a['status'] != 'published' for a in members)),
            'draft_english_words': sum((a['english_word_count'] for a in members if a['status'] != 'published')),
            'unique_english_words': word_count,
            'rights_cleared_words': cleared,
            'new_book_words': novel,
            'known_book_overlap_fragments': len(known_overlap),
            'known_book_overlap_words': sum(known_overlap.values()),
            'recipes': recipes,
            'cases': cases,
            'visual_assets': len(visuals),
            'original_assets_confirmed': len(originals),
            'visual_coverage': round(coverage, 3),
            'visual_rights_coverage': round(visual_rights_coverage, 3),
            'theme_count': diversity,
            'top_topics': topics.most_common(8),
            'page_estimates': pages,
            'target_pages': d['target_pages'],
            'thresholds': {'outline': outline, 'manuscript': target},
            'member_ids': [a['id'] for a in members],
            'member_digest': fingerprint,
            'duplicate_articles': duplicates,
            'gaps': gaps,
            'personal_portfolio_value': d['personal_value'],
            'editorial_assessment': 'CURRENT_SOURCE_CONFIRMED' if cohesion else 'PENDING',
            'commercial_potential': 'NOT_ASSESSED',
            # Market research precedes manuscript readiness; publication gates stay unchanged.
            'market_assessment_eligible': stage in ('outline_ready', 'manuscript_candidate', 'editorial_review') and not d.get('inventory_only', False) and bool(unique),
            'inventory_only': bool(d.get('inventory_only', False)),
            'eligible_member_ids': [a['id'] for a in unique],
            'production_authorized': False,
            'existing_books': sorted({b for a in members for b in a['existing_books']}),
            'next_action': 'Map the existing-book overlap; retain rights-confirmed thematic inventory' if d.get('inventory_only') else 'Define a reader and purchase reason; compare the coherent subset with market alternatives while retaining editorial/rights gaps' if stage == 'outline_ready' else 'Review the available archive; no writing quota' if stage == 'collecting' else 'Request a bounded Multi-Market assessment and editorial decision; no production',
        }
    return result

def refresh(root,site,*,as_of=None,review=False,if_due=False):
    site=Path(site).resolve();today=as_of or datetime.now(ZoneInfo('Europe/Paris')).date().isoformat();date.fromisoformat(today)
    with locked(root):
        c=policy(root);old=read(directory(root)/'state.json',{})
        if old and old.get('schema_version')!=VERSION:raise ValidationError('Unknown readiness state version')
        if old.get('site_root') and old['site_root']!=str(site):raise ValidationError('Readiness source root changed; review explicitly before replacing inventory')
        articles,scan,claims=collect(root,site,old,c,today)
        assessments=old.get('editorial_assessments',{})
        cs=candidates(articles,c,assessments,old)
        events=list(old.get('milestones',[]));transitions=list(old.get('transitions',[]))
        ever={(e['candidate'],e['stage']) for e in events if e.get('kind','milestone')=='milestone'}
        for cid,item in cs.items():
            previous=old.get('candidates',{}).get(cid,{}).get('stage','collecting')
            if item['stage']==previous:continue
            transition={'id':digest([cid,previous,item['stage'],item['member_digest'],digest(c)])[:20],'candidate':cid,'from_stage':previous,'stage':item['stage'],'observed_at':stamp(),'basis':'First observed current inventory; not a historical threshold date','delivered_at':None}
            if transition['id'] not in {x['id'] for x in transitions}:transitions.append(dict(transition))
            regression=STAGES.index(item['stage'])<STAGES.index(previous)
            if regression or (cid,item['stage']) not in ever:
                transition['kind']='regression' if regression else 'milestone'
                if transition['id'] not in {x['id'] for x in events}:events.append(transition)

        last=old.get('last_editorial_review');due=not last or (date.fromisoformat(today)-date.fromisoformat(last)).days>=c['review_interval_days']
        monthly=old.get('monthly_analysis',{})
        if review and (not if_due or due):
            monthly={cid:{'member_digest':x['member_digest'],'analysis_digest':digest([x['member_digest'],x['top_topics'],x['gaps'],x['page_estimates']]),'topics':x['top_topics'],'gaps':x['gaps'],'duplicate_articles':x['duplicate_articles'],'method':'Source-bound deterministic topic/volume/gap analysis; not a human literary-quality judgment'} if monthly.get(cid,{}).get('analysis_digest')!=digest([x['member_digest'],x['top_topics'],x['gaps'],x['page_estimates']]) else monthly[cid] for cid,x in cs.items()}
            last=today
        state = {
            'schema_version': VERSION,
            'site_root': str(site),
            'updated_at': stamp(),
            'as_of': today,
            'policy_digest': digest(c),
            'claims_digest': digest(claims),
            'articles': articles,
            'candidates': cs,
            'scan': scan,
            'milestones': events,
            'transitions': transitions,
            'editorial_assessments': assessments,
            'last_editorial_review': last,
            'monthly_review_due': not last or (date.fromisoformat(today) - date.fromisoformat(last)).days >= c['review_interval_days'],
            'monthly_analysis': monthly,
            'source_of_truth': 'Existing site Markdown or authenticated runtime export, discovery index, OS intakes and artwork registry; this is a regenerable projection',
            'production_authorized': False,
            'network_requests': 0,
        }
        # Generate before committing so analysis/render failures never replace the inventory.
        rendered=render(state)
        atomic(directory(root)/'state.json',state)
        atomic(directory(root)/'report.md',rendered)
        return state

def render(s):
    rows=['# Book Readiness Radar',f"Observed: {s['as_of']}. Planning estimates, not confirmed print layouts.",'','| Candidate | Published/available entries | Unique EN words | Rights-confirmed words | Recipe / case | Stage | Prose pages | Illustrated pages |','|---|---:|---:|---:|---:|---|---|---|']
    for x in s['candidates'].values():
        pages=x['page_estimates'];pr=lambda r:f'~{r[0]}–{r[1]}'
        rows.append(f"| {x['title']} | {x['entries']} available ({x['published_entries']} published; {x['draft_entries']} drafts) | {x['unique_english_words']} | {x['rights_cleared_words']} | {x['recipes']} / {x['cases']} | {x['stage']} | {pr(pages['manuscript'])} | {pr(pages['illustrated'])} |")
    for x in s['candidates'].values():
        rows.extend(['',f"## {x['title']}",f"Visual assets: {x['visual_assets']}; originals with retained proof: {x['original_assets_confirmed']}. Draft English words: {x['draft_english_words']}. New-book words: {x['new_book_words'] if x['new_book_words'] is not None else 'UNKNOWN (existing-book overlap unmapped)'}. Target: {x['target_pages'][0]}–{x['target_pages'][1]} pages.",f"Personal/portfolio: {x['personal_portfolio_value']}",f"Editorial: {x['editorial_assessment']}. Commercial: {x['commercial_potential']}. Eligible for bounded market assessment: {x['market_assessment_eligible']}.",f"Next: {x['next_action']}",f"Confirmed exact reuse in existing book: {x['known_book_overlap_fragments']} fragments / {x['known_book_overlap_words']} words. Not-matched text is not automatically new."])
        rows.extend('- '+gap for gap in x['gaps'])
        if x['existing_books']:rows.append('Existing books: '+', '.join(x['existing_books']))
    pending=[e for e in s['milestones'] if not e['delivered_at']]
    rows.extend(['','## Newly observed milestones',*([f"- {e['id']}: {e['candidate']} → {e['stage']}" for e in pending] or ['- None.'])])
    rows.extend(['',f"Monthly review due: {s['monthly_review_due']}. Last: {s['last_editorial_review'] or 'not performed'}. Incremental scan: {s['scan']['analyzed']} analyzed, {s['scan']['reused']} reused.",'Rights not recorded means UNKNOWN. Inventory rights confirmation is separate from book production approval. No market research, manuscript generation, KDP submission or publication was launched.',''])
    return '\n'.join(rows)

def acknowledge(root,event_id):
    with locked(root):
        path=directory(root)/'state.json';s=read(path)
        matches=[e for e in s['milestones'] if event_id=='all' or e['id']==event_id]
        if not matches:raise ValidationError('Unknown milestone notification')
        for e in matches:e['delivered_at']=e['delivered_at'] or stamp()
        atomic(path,s);atomic(directory(root)/'report.md',render(s))
        return {'acknowledged':len(matches),'authority':'Notification delivery only; no editorial/production approval'}

def assess(root,candidate,receipt):
    with locked(root):
        path=directory(root)/'state.json';s=read(path)
        if candidate not in s['candidates']:raise ValidationError('Unknown candidate')
        if not receipt.get('evidence') or receipt.get('cohesion') not in ('confirmed','pending'):
            raise ValidationError('Source-bound editorial assessment and evidence required')
        if receipt.get('member_digest')!=s['candidates'][candidate]['member_digest']:raise ValidationError('Assessment source digest is stale')
        for k in ('gaps_resolved','accepted_for_editorial_review'):
            if k in receipt and not isinstance(receipt[k],bool):raise ValidationError('Editorial decision must be boolean')
        s['editorial_assessments'][candidate]=receipt;atomic(path,s)
        return {'recorded':candidate,'next':'refresh inventory to evaluate the source-bound milestone','production_authorized':False}

def research_handoff(root, as_of=None):
    """Source-bound early material leads, never market evidence or permission."""
    source = directory(root) / 'state.json'
    result = {'status': 'UNAVAILABLE', 'observed_as_of': None, 'requested_as_of': as_of,
              'source_report': str((directory(root) / 'report.md').resolve()),
              'source_inventory': str(source.resolve()), 'inventory_sha256': None,
              'candidates': [], 'withheld': [], 'production_authorized': False,
              'market_evidence': False}
    if not source.is_file():
        result['reason'] = 'Readiness inventory unavailable; not an empty archive'
        return result
    try:
        raw = source.read_bytes(); state = json.loads(raw)
        if not isinstance(state, dict) or state.get('schema_version') != VERSION or not isinstance(state.get('candidates'), dict) or not isinstance(state.get('articles'), dict):
            raise ValueError('Invalid inventory shape')
        observed = date.fromisoformat(state['as_of'])
        requested = date.fromisoformat(as_of) if as_of else observed
        result.update(observed_as_of=state['as_of'], inventory_sha256=hashlib.sha256(raw).hexdigest())
        if observed > requested:
            result.update(status='FUTURE_EXCLUDED', reason='Do not attach future material to an earlier report')
            return result
        result['status'] = 'CURRENT' if observed == requested else 'RETAINED_REFRESH_REQUIRED'
        articles = {a['id']: a for a in state['articles'].values()}
        for cid, candidate in state['candidates'].items():
            stage = candidate.get('stage')
            inventory_only = candidate.get('inventory_only', candidate.get('new_book_words') is None)
            if inventory_only:
                result['withheld'].append({'candidate_id': cid, 'reason': 'EXISTING_BOOK_OVERLAP_REVIEW_REQUIRED'})
                continue
            if stage not in ('outline_ready', 'manuscript_candidate', 'editorial_review'):
                continue
            ids = candidate.get('eligible_member_ids', candidate.get('member_ids', []))
            members = [articles[i] for i in ids if i in articles
                       and articles[i].get('rights') != 'BLOCKED'
                       and 'Excluded by existing editorial selection' not in articles[i].get('limitations', [])
                       and (articles[i].get('status') == 'published' or articles[i].get('collection') == 'art')]
            if not members or not candidate.get('member_digest'):
                result['withheld'].append({'candidate_id': cid, 'reason': 'NO_BOUND_USABLE_MATERIAL'})
                continue
            refs = [{'id': a['id'], 'url': a.get('canonical_url'), 'source_hash': a['source_hash'],
                     'rights': a.get('rights', 'UNKNOWN')} for a in members]
            material_digest = digest([candidate['member_digest'], refs, candidate.get('gaps', []),
                                      candidate.get('editorial_assessment'), state.get('policy_digest'), state.get('claims_digest')])
            result['candidates'].append({
                'id': 'readiness:' + cid, 'candidate_id': cid, 'title': candidate['title'],
                'source_kind': 'OWN_ARCHIVE', 'status': 'RESEARCH', 'editorial_stage': stage,
                'member_digest': candidate['member_digest'], 'material_review_digest': material_digest,
                'observed_as_of': state['as_of'], 'freshness': result['status'],
                'source_report': result['source_report'], 'source_refs': refs,
                'available_entries': candidate['entries'], 'unique_english_words': candidate['unique_english_words'],
                'visual_assets': candidate['visual_assets'], 'gaps': list(candidate.get('gaps', [])),
                'existing_books': list(candidate.get('existing_books', [])),
                'purpose': 'Compare reader/purchase reason, demand and competitors; available material is not paid demand',
                'commercial_potential': 'NOT_ASSESSED', 'production_authorized': False})
        return result
    except (ValueError, KeyError, TypeError, OSError) as error:
        result.update(status='BLOCKED', candidates=[], reason='Invalid or unreadable readiness inventory: ' + type(error).__name__)
        return result


def research_queue(root, as_of=None):
    return research_handoff(root, as_of)['candidates']


def refresh_for_weekly(root, as_of):
    """Refresh remembered local sources for an actual current run, not a replay."""
    today = datetime.now(ZoneInfo('Europe/Paris')).date().isoformat()
    if as_of != today:
        return {'status': 'NOT_REFRESHED_HISTORICAL_RUN'}
    try:
        old = read(directory(root) / 'state.json', {})
        if not old.get('site_root'):
            return {'status': 'UNAVAILABLE', 'reason': 'No remembered source root'}
        refresh(root, old['site_root'], as_of=as_of, review=True, if_due=True)
        return {'status': 'REFRESHED', 'as_of': as_of}
    except (ValueError, KeyError, TypeError, OSError) as error:
        return {'status': 'BLOCKED', 'reason': 'Readiness refresh failed: ' + type(error).__name__,
                'inventory_preserved': True}


def weekly_handoff(root, as_of):
    """One refreshed snapshot shared by the isolated report and commercial loader."""
    refreshed = refresh_for_weekly(root, as_of)
    handoff = research_handoff(root, as_of)
    handoff['refresh_result'] = refreshed
    if refreshed['status'] == 'BLOCKED':
        handoff['status'] = 'REFRESH_BLOCKED'
        handoff['reason'] = refreshed['reason'] + '; retained material is not freshly verified'
        for row in handoff['candidates']:
            row['freshness'] = 'REFRESH_BLOCKED'
    return handoff


def after_publication(root,site):
    if not (Path(root)/'book-radar/readiness-policy.json').exists():return {'status':'NOT_CONFIGURED'}
    try:
        s=refresh(root,site)
        return {'status':'REFRESHED','articles':len(s['articles']),'pending_milestones':sum(not e['delivered_at'] for e in s['milestones']),'report':'.tmp/book-readiness/report.md'}
    except Exception as exc:
        # Publication has already succeeded. A failed projection cannot undo its receipt.
        try:atomic(directory(root)/'last-error.json',{'observed_at':stamp(),'error':str(exc),'inventory_preserved':True})
        except OSError:pass
        return {'status':'FAILED','inventory_preserved':True,'error':str(exc)}

def main(argv,root):
    parser=argparse.ArgumentParser(prog='./bin/abvx book-radar readiness')
    parser.add_argument('action',choices=['refresh','review','report','ack','assess','compare-book']);parser.add_argument('id',nargs='?');parser.add_argument('--site-root',type=Path);parser.add_argument('--as-of');parser.add_argument('--if-due',action='store_true');parser.add_argument('--json',action='store_true');parser.add_argument('--file',type=Path);parser.add_argument('--book-url')
    a=parser.parse_args(argv)
    if a.action=='compare-book':
        from .book_readiness_overlap import compare_book
        old=read(directory(root)/'state.json',{});site=a.site_root or old.get('site_root')
        if not site or not a.file or not a.book_url:raise ValidationError('Site root, --file manuscript and --book-url required')
        comparison=compare_book(root,site,a.file,a.book_url)
        value={'summary':comparison['summary'],'manuscript_english_words':comparison['manuscript_english_words'],'report':'.tmp/book-readiness/existing-book-overlap.md','new_book_words':'UNKNOWN until unresolved variants are reviewed'}
    elif a.action in ('refresh','review'):
        old=read(directory(root)/'state.json',{});site=a.site_root or old.get('site_root')
        if not site:raise ValidationError('--site-root required for initial inventory')
        s=refresh(root,site,as_of=a.as_of,review=a.action=='review',if_due=a.if_due)
        value=s if a.json else render(s)
    elif a.action=='ack':value=acknowledge(root,a.id)
    elif a.action=='assess':
        if not a.file:raise ValidationError('Assessment receipt file required')
        value=assess(root,a.id,read(a.file))
    else:
        s=read(directory(root)/'state.json')
        if not s:raise ValidationError('Refresh inventory first')
        value=s if a.json else render(s)
    print(value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,indent=2))
    return 0
