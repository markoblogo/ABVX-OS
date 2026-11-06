"""Private editorial projection and evidence-bound usage reconciliation; no publishing."""
from __future__ import annotations
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from .harness import ValidationError
from .psychology_warehouse import TOPICS, _classify, _inventory, _atomic_json

VERSION = 'psychology-editorial-v1'
TITLES = {
 'SUFFERING_AND_DRAMA':'Страдание, драма и роли', 'TRAUMA':'Травма и восстановление','RELATIONSHIPS':'Отношения и близость',
 'ADDICTION_AND_DEPENDENCE':'Зависимость и созависимость','THERAPY_AND_PSYCHOTHERAPY':'Терапия и изменения',
 'ADAPTATION_AND_COPING':'Адаптация и способы справляться','VIOLENCE_AND_ABUSE':'Насилие и абьюз',
 'ANXIETY_AND_FEAR':'Тревога и страх','GRIEF_AND_LOSS':'Горе и утрата',
 'SELF_AND_IDENTITY':'Идентичность и самоотношение','FAMILY_AND_CHILDHOOD':'Семья и детство',
 'EMOTIONS_AND_MENTAL_HEALTH':'Эмоции и психическое состояние','BOUNDARIES_AND_AGENCY':'Границы и ответственность',
 'NARCISSISM_AND_PERSONALITY':'Личностная динамика и нарциссизм',
 'THINKING_AND_MEANING':'Мышление, смысл и реальность','DESIRE_AND_CHOICE':'Желания, потребности и выбор',
 'WORK_AND_MONEY':'Работа, деньги и деятельность','LIVING_AND_TIME':'Жизнь, время и конечность',
 'BODY_AND_SEXUALITY':'Тело и сексуальность','TOPIC_REVIEW':'Тема требует редакторского решения'}
RULES = {label:r'\b(?:'+'|'.join(re.escape(cue) for cue in cues if len(cue)>=4)+r')\w*' for label,cues in TOPICS.items()}
RULES.update({
 'ANXIETY_AND_FEAR':r'\b(?:трево\w*|страх\w*|страш\w*|боят\w*|бои[тм]\w*|опасност\w*|беспокой\w*|паник\w*|навязчив\w*)',
 'VIOLENCE_AND_ABUSE':r'\b(?:насил\w*|аб[ьъ]юз\w*|оскорблен\w*|войн\w*|унижен\w*)',
 'SUFFERING_AND_DRAMA':r'\b(?:страда\w*|драм\w*|жалост\w*|жалова\w*|несчаст\w*|жертв\w*|мазох\w*|спасател\w*)|\bвторичн\w* выгод\w*',
 'THERAPY_AND_PSYCHOTHERAPY':r'\b(?:терап\w*|психотерап\w*|клиент\w*|сеанс\w*|сесси\w*|супервиз\w*|психолог\w*)',
 'ADAPTATION_AND_COPING':r'\b(?:адаптац\w*|копинг\w*|справля\w*|адаптир\w*|стресс\w*|замиран\w*|замир\w*|регресси\w*|дезорганизац\w*|ресурс\w*|выгора\w*|устал\w*)',
 'FAMILY_AND_CHILDHOOD':r'\b(?:семь\w*|родител\w*|детств\w*|реб[её]н\w*|мама|мамы|маму|мамка|папа|папы|папу|материн\w*|отцов\w*)',
 'RELATIONSHIPS':r'\b(?:отношен\w*|партн[её]р\w*|близ[ок]\w*|любов\w*|любит\w*|одиноч\w*|расстав\w*|разлук\w*|друж\w*|встреч\w*|контакт\w*|привязан\w*)',
 'SELF_AND_IDENTITY':r'\b(?:субъ?ект\w*|личност\w*|самоопредел\w*|самоактивац\w*|эгоцентр\w*)|\b(?:самим|самой) собой\b|\bвнутренн\w* конфликт\w*|\b(?:идентич\w*|самооцен\w*|самоцен\w*|самоотнош\w*|самовоспр\w*|самоуваж\w*|маск\w*)|\b(?:быть|остаться|оставаться) собой\b|\bобраз\w* себя\b|\bкто я\b',
 'BOUNDARIES_AND_AGENCY':r'\b(?:границ\w*|ответствен\w*|автоном\w*|субъектн\w*|самостоят\w*|согласие|согласия|агентност\w*)',
 'EMOTIONS_AND_MENTAL_HEALTH':r'\b(?:эмоци\w*|депресс\w*|подавлен\w*|настроен\w*|чувств\w*|стыд\w*|вина|вины|вину|гнев\w*|злост\w*|радост\w*|завист\w*|пережива\w*|аффект\w*|ярост\w*|раздраж\w*|злоб\w*|обид\w*|невыносим\w*|боль|боли|больно|скука|психическ\w*)',
 'NARCISSISM_AND_PERSONALITY':r'\b(?:нарцисс\w*|погранич\w*|истер\w*|шизоид\w*|неврот\w*|невроз\w*|грандиоз\w*|обесцен\w*)',
 'THINKING_AND_MEANING':r'\b(?:мышл\w*|мысл\w*|убежд[её]н\w*|иллюз\w*|реальн\w*|смысл\w*|понима\w*|знани\w*|истин\w*|иде\w*|бессознатель\w*|проекц\w*|проектив\w*|логик\w*|идея|идеи|справедлив\w*|вера|веры|правил\w*)',
 'DESIRE_AND_CHOICE':r'\b(?:желан\w*|хоч\w*|хотет\w*|потребност\w*|выбор\w*|выбира\w*|решени\w*)',
 'WORK_AND_MONEY':r'\b(?:работ\w*|ден[еь]г\w*|заработ\w*|професси\w*|карьер\w*|труд\w*|деятельност\w*|бизнес\w*|эконом\w*|творче\w*)',
 'LIVING_AND_TIME':r'\b(?:жизн\w*|врем\w*|смерт\w*|счаст\w*|прошл\w*|будущ\w*|настоящ\w*|старост\w*)',
 'BODY_AND_SEXUALITY':r'\b(?:организм\w*|физиоло\w*|психосом\w*|кортизол\w*|желуд\w*|перееда\w*|эякулят\w*|nervus|бдсм|телес\w*|тело|тела|телом|сексу\w*|секс\w*|оргазм\w*|эрот\w*|либидо\w*)'})
DIAGNOSTIC = r'\b(?:погранич\w*|прл\w*|шизо\w*|психоз\w*|психот\w*|диагноз\w*|истерик\w*|невротик\w*|нарцисс\w*)'


def text_key(text: str) -> str:
 return unicodedata.normalize('NFC',text.replace('\r\n','\n').replace('\r','\n')).strip()


def digest(data: bytes) -> str:
 return hashlib.sha256(data).hexdigest()


def read(path: Path) -> Any:
 return json.loads(path.read_text())


def contained(root: Path, name: str) -> Path:
 path=(root/name).resolve()
 if not path.is_relative_to(root.resolve()):raise ValidationError('Series reference escapes private root')
 return path


def build_crosswalk(fragments: list[dict], notes: list[dict]) -> dict:
 if len({n['note_id'] for n in notes})!=len(notes):raise ValidationError('Duplicate warehouse note ID')
 exact=defaultdict(list);parts=defaultdict(list)
 for note in notes:
  if not note.get('current',True):continue
  raw=note['original_text'];trimmed=raw.strip();start=raw.find(trimmed)
  exact[text_key(raw)].append({'noteId':note['note_id'],'relation':'EXACT_TEXT','start':start,'end':start+len(trimmed)})
  boundaries=list(re.finditer(r'(?m)^\*{3,}[ \t]*',raw))
  if boundaries:
   starts=[0]+[m.end() for m in boundaries];ends=[m.start() for m in boundaries]+[len(raw)]
   for begin,end in zip(starts,ends):
    value=raw[begin:end].strip()
    if value:
     offset=raw.find(value,begin,end)
     parts[text_key(value)].append({'noteId':note['note_id'],'relation':'EXACT_DELIMITED_PART','start':offset,'end':offset+len(value)})
 result={}
 for fragment in fragments:
  matches=exact.get(text_key(fragment['source'])) or parts.get(text_key(fragment['source']))
  if not matches:raise ValidationError('Unresolved source boundary: '+fragment['id'])
  result[fragment['id']]=matches
 return result


def classify_fragment(fragment: dict) -> dict:
 text=fragment['source'];evidence={};scores={}
 for label,pattern in RULES.items():
  hits=[m.group().casefold() for m in re.finditer(pattern,text,re.I)]
  if hits:evidence[label]=sorted(set(hits));scores[label]=sum(min(3,count) for count in Counter(hits).values())
 specific={'TRAUMA','GRIEF_AND_LOSS','ADDICTION_AND_DEPENDENCE','NARCISSISM_AND_PERSONALITY'}
 topics=sorted(scores,key=lambda key:(-scores[key],0 if key in specific else 1,key));reasons=set(fragment.get('reviewFlags',[]));base=_classify(text)
 if 'PERSONALLY_IDENTIFYING_DETAIL' in base['privacy_flags']:reasons.add('POSSIBLE_PRIVATE_IDENTIFIER')
 if 'CASE_LIKE_MATERIAL' in base['privacy_flags']:reasons.add('PRACTITIONER_OR_CLIENT_CONTEXT')
 if re.search(DIAGNOSTIC,text,re.I):reasons.add('DIAGNOSTIC_LANGUAGE')
 if base['provenance']['attribution_if_explicit']:reasons.add('NAMED_SOURCE_OR_QUOTATION_REVIEW')
 return {'primaryTopic':topics[0] if topics else 'TOPIC_REVIEW','topics':topics,'topicEvidence':evidence,'reviewReasons':sorted(reasons),'provenance':base['provenance'],'assetType':base['asset_type']['label'],'method':'source-bound lexical evidence plus editorial rules; candidate topics, not human approval'}


def verify_publications(series: Path, registry: dict, queue: dict) -> dict:
 fragments={f['id']:f for f in registry['fragments']};published={}
 for item in queue['items']:
  if not item.get('publishedUrl'):continue
  if item.get('status')!='PUBLISHED_VERIFIED' or not all(item.get(k) is True for k in ['editorialApproved','artworkApproved','sourceReviewApproved']):raise ValidationError('Unverified publication '+item['id'])
  url='https://abvx.xyz/writing/'+item['id']
  if item['publishedUrl']!=url or not re.fullmatch(r'[0-9a-f]{40}',item['deploymentSha']):raise ValidationError('Invalid publication identity')
  for field in ['publishedAt','verifiedAt']:
   if datetime.fromisoformat(item[field].replace('Z','+00:00')).tzinfo is None:raise ValidationError('Timezone required')
  source=contained(series,item['releaseSourceFile']).read_bytes();draft=contained(series,item['draftFile']).read_bytes()
  if digest(source)!=item['releaseSourceSha256'] or digest(draft)!=item['sourceSha256']:raise ValidationError('Approved source hash mismatch')
  receipt=read(contained(series,item['publicationReceipt']))
  if receipt.get('production')!='PASS' or receipt.get('checks')!='PASS' or receipt.get('reviewInspected') is not True or receipt.get('merge')!=item['deploymentSha'] or receipt.get('closeout',{}).get('status')!='RECORDED':raise ValidationError('Production receipt mismatch')
  for fid in item['fragmentIds']:
   f=fragments[fid]
   if fid in published or f.get('publishedUrl')!=url or f.get('deploymentSha')!=item['deploymentSha'] or f.get('publishedAt')!=item['publishedAt'] or not f.get('translation') or f['translation'] not in source.decode():raise ValidationError('Fragment publication mismatch '+fid)
   published[fid]={'url':url,'publishedAt':item['publishedAt'],'verifiedAt':item['verifiedAt'],'deploymentSha':item['deploymentSha'],'receipt':item['publicationReceipt'],'sourceSha256':item['releaseSourceSha256']}
 if {f['id'] for f in fragments.values() if f.get('publishedUrl')}!=set(published):raise ValidationError('Orphan published fragment')
 return published


def reconcile_series(root: Path, series: Path, *, write: bool=False) -> dict:
 root=root.resolve();series=series.resolve();base=root/'psychology-warehouse';state_path=base/'state/warehouse.json';usage_path=base/'usage/ledger.json';registry_path=series/'registry.json'
 paths=[state_path,usage_path,registry_path,series/'queue.json',series/'plan.json',series/'near-duplicates.json']
 decisions_path=base/'editorial/decisions.json'
 if decisions_path.exists():paths.append(decisions_path)
 inputs={p:p.read_bytes() for p in paths};state=json.loads(inputs[state_path]);usage=json.loads(inputs[usage_path]);registry=json.loads(inputs[registry_path]);queue=json.loads(inputs[series/'queue.json']);plans=json.loads(inputs[series/'plan.json'])
 original=contained(series,registry['sourceFile']);source=original.read_bytes();warehouse_source=Path(state['source']['path']);warehouse_bytes=warehouse_source.read_bytes()
 if not digest(source)==digest(warehouse_bytes)==registry['sourceSha256']==state['source']['sha256']:raise ValidationError('Archives are different source versions')
 fs=registry['fragments']
 if len({f['id'] for f in fs})!=len(fs):raise ValidationError('Duplicate native ID')
 for f in fs:
  if digest(f['source'].encode())!=f['sourceSha256']:raise ValidationError('Original fragment hash mismatch '+f['id'])
 mapping=build_crosswalk(fs,state['notes']);published=verify_publications(series,registry,queue)
 registry['editorialProjection']={'version':VERSION,'index':str(base/'editorial/INDEX.md'),'catalogue':str(base/'editorial/catalogue.json'),'osUsageProject':'psychology-notebook'}
 decisions=json.loads(inputs[decisions_path]) if decisions_path in inputs else {'overrides':[],'duplicateGroups':[]}
 if decisions.get('sourceSha256',registry['sourceSha256'])!=registry['sourceSha256']:raise ValidationError('Editorial decisions belong to a different source')
 overrides={x['fragmentId']:x for x in decisions['overrides']}
 if len(overrides)!=len(decisions['overrides']) or set(overrides)-{f['id'] for f in fs}:raise ValidationError('Invalid editorial override IDs')
 reservations=defaultdict(list)
 for post in queue['items']:
  for fid in post['fragmentIds']:reservations[fid].append(post['id'])
 for plan in plans:
  for fid in plan['fragmentIds']:reservations[fid].append(plan['id'])
 if set(reservations)!={f['id'] for f in fs} or any(len(x)!=1 for x in reservations.values()):raise ValidationError('Source assignment is incomplete or overlaps')
 near_pairs=json.loads(inputs[series/'near-duplicates.json'])
 near_members={fid for pair in near_pairs for fid in [pair['left'],pair['right']]}
 rows=[]
 for f in fs:
  row={'fragmentId':f['id'],'sourceSha256':f['sourceSha256'],'warehouseLinks':mapping[f['id']],**classify_fragment(f),'assignedTo':reservations[f['id']][0],'publication':published.get(f['id'])}
  if f['id'] in near_members:row['reviewReasons']=sorted(set(row['reviewReasons']+['NEAR_DUPLICATE_REVIEW']))
  decision=overrides.get(f['id'])
  if decision:
   if decision['sourceSha256']!=f['sourceSha256'] or not decision['topics'] or any(t not in TITLES for t in decision['topics']):raise ValidationError('Editorial decision hash/topic mismatch '+f['id'])
   row.update(primaryTopic=decision['topics'][0],topics=[t for t in decision['topics'] if t!='TOPIC_REVIEW'],reviewReasons=sorted(set(row['reviewReasons']+decision['reviewReasons'])),editorialDecision=decision)
   row['method']='Assistant source-read topical decision; not owner publication approval'
  row['editorialState']='PUBLISHED_VERIFIED' if row['publication'] else 'REVIEW_REQUIRED' if row['reviewReasons'] else 'TOPIC_REVIEW' if not row['topics'] else 'SOURCE_CANDIDATE_NOT_APPROVED'
  rows.append(row);f['warehouseLinks']=mapping[f['id']]
  f['editorialTopics']={'version':VERSION,'primary':row['primaryTopic'],'secondary':[t for t in row['topics'] if t!=row['primaryTopic']],'method':row['method']}
  if f['id'] not in published:f['reviewFlags']=sorted(set(f.get('reviewFlags',[])+row['reviewReasons']))
 reverse=defaultdict(list)
 for row in rows:
  for link in row['warehouseLinks']:reverse[link['noteId']].append(row)
 for note in state['notes']:
  if note['note_id'] in reverse:
   linked=reverse[note['note_id']];note['editorial_series']={'version':VERSION,'fragmentIds':[r['fragmentId'] for r in linked],'topics':sorted({t for r in linked for t in r['topics']}),'publishedUrls':sorted({r['publication']['url'] for r in linked if r['publication']})}
 existing={u.get('usage_id'):u for u in usage['usages'] if u.get('usage_id')}
 if len(existing)!=sum(bool(u.get('usage_id')) for u in usage['usages']):raise ValidationError('Duplicate stable usage ID')
 added=0
 for fid,proof in published.items():
  for link in mapping[fid]:
   key='abvx-series:'+fid+':'+link['noteId'];use={'usage_id':key,'note_id':link['noteId'],'project_id':'psychology-notebook','relation':'PUBLISHED_FRAGMENT','series_fragment_id':fid,'recorded_at':existing[key]['recorded_at'] if key in existing else datetime.now(timezone.utc).isoformat(),'recorded_at_basis':'current reconciliation observation; publication verification time retained separately','basis':'retained source-specific approval and verified production receipt','decision_status':'PUBLISHED_VERIFIED','publication':proof,'source_range':{k:link[k] for k in ['start','end']}}
   if key in existing:
    if existing[key]!=use:raise ValidationError('Existing verified usage conflicts: '+key)
   else:usage['usages'].append(use);added+=1
 state['inventory']=_inventory(state,usage)
 primary=Counter(r['primaryTopic'] for r in rows);cross=Counter()
 for row in rows:
  topics=sorted(row['topics'])
  for i,a in enumerate(topics):
   for b in topics[i+1:]:cross[(a,b)]+=1
 review=Counter(reason for r in rows for reason in r['reviewReasons'])
 report={'version':VERSION,'sourceSha256':registry['sourceSha256'],'fragments':len(rows),'warehouseNotes':len(state['notes']),'unmappedWarehouseNotes':[n['note_id'] for n in state['notes'] if n['note_id'] not in reverse],'mappedFragments':len(mapping),'boundaryPartFragments':sum(any(x['relation']=='EXACT_DELIMITED_PART' for x in links) for links in mapping.values()),'verifiedPublishedFragments':len(published),'usageRecordsAdded':added,'totalSeriesUsageRecords':sum(x.get('project_id')=='psychology-notebook' for x in usage['usages']),'primaryTopics':dict(primary),'overlappingFragments':sum(len(r['topics'])>1 for r in rows),'reviewReasons':dict(review),'unpublishedReviewRequired':sum(r['editorialState']=='REVIEW_REQUIRED' for r in rows),'topicReview':sum(r['editorialState']=='TOPIC_REVIEW' for r in rows),'nonReviewedCandidateFragments':sum(r['editorialState']=='SOURCE_CANDIDATE_NOT_APPROVED' for r in rows),'writeRequested':write,'assistantSourceReadTopicDecisions':len(overrides),'humanSemanticReview':'PARTIAL; source-read decisions counted separately, remaining topics are rule candidates; clinical/provenance clearance pending','bookOverlap':'UNKNOWN; no canonical manuscript locator','originalBytesPreserved':True,'publicationAuthority':False}
 catalogue={'version':VERSION,'sourceSha256':registry['sourceSha256'],'topicLabels':TITLES,'fragments':rows,'topicIntersections':[{'topics':list(k),'count':v} for k,v in cross.most_common()],'nearDuplicateCandidates':json.loads(inputs[series/'near-duplicates.json']),'editorialDuplicateGroups':decisions.get('duplicateGroups',[]),'exactDuplicateGroups':[{'fragmentId':fid,'sourceOccurrences':count} for fid,count in Counter(x['fragmentId'] for x in registry['occurrences']).items() if count>1],'report':{k:v for k,v in report.items() if k not in ['writeRequested','usageRecordsAdded']}}
 if write:
  if original.read_bytes()!=source or warehouse_source.read_bytes()!=warehouse_bytes or any(p.read_bytes()!=value for p,value in inputs.items()):raise ValidationError('Input changed during reconciliation; nothing written')
  # Each replacement is atomic; deterministic usage IDs make interrupted reruns additive and idempotent.
  # No source/queue/plan bytes are written; native registry gains links, editorial topics and additive unpublished-review flags.
  for path,value in [(usage_path,usage),(state_path,state),(registry_path,registry),(base/'editorial/catalogue.json',catalogue),(base/'editorial/last-sync.json',report)]:
   _atomic_json(path,value);path.chmod(0o600)
  render_views(root,series,catalogue,registry)
 return report



def render_views(root: Path, series: Path, catalogue: dict, registry: dict) -> None:
 """Private, disposable reading views; registry remains canonical source."""
 folder=root/'psychology-warehouse/editorial';(folder/'topics').mkdir(exist_ok=True)
 fragments={f['id']:f for f in registry['fragments']};rows=catalogue['fragments'];report=catalogue['report']
 def save(name,text):
  path=folder/name;path.write_text(text);path.chmod(0o600)
 def entry(row,base=''):
  fid=row['fragmentId'];snippet=' '.join(fragments[fid]['source'].split())[:130].replace('|',chr(92)+'|')
  return '- ['+fid+']('+base+'FRAGMENTS.md#'+fid+') — '+snippet+' — '+row['editorialState']+'\n'
 intro='# Psychology Notebook — карта всего архива\n\nЧастная редакторская карта. Исходники, ID, переводы и согласования не переписаны; публикация и расписание не активируются.\n\n'
 intro+='Все '+str(report['fragments'])+' уникальных фрагмента связаны с OS. Подтверждённо опубликовано '+str(report['verifiedPublishedFragments'])+'. Их использование отражено в журнале OS.\n\n'
 intro+='19 рабочих тем; '+str(report['overlappingFragments'])+' фрагментов имеют несколько тем. Основа — правила с видимыми текстовыми признаками; '+str(report['assistantSourceReadTopicDecisions'])+' первоначально неопределённых заметки прочитаны ассистентом целиком и размечены отдельно. Это не полное авторское или клиническое одобрение архива.\n\n'
 intro+='[Все фрагменты](FRAGMENTS.md) · [Требуют проверки](REVIEW.md) · [Повторы](DUPLICATES.md) · [Пересечения](INTERSECTIONS.md) · [Повторная сверка](../../docs/maintenance/PSYCHOLOGY_NOTEBOOK_ARCHIVE.md)\n\n'
 intro+='| Тема | Основная | Всего с этой темой | Неопубликованные кандидаты без специальных флагов |\n| --- | ---: | ---: | ---: |\n'
 for topic,title in TITLES.items():
  members=[r for r in rows if topic in r['topics'] or topic==r['primaryTopic']];primary=sum(r['primaryTopic']==topic for r in members);candidates=sum(r['editorialState']=='SOURCE_CANDIDATE_NOT_APPROVED' for r in members)
  intro+='| ['+title+'](topics/'+topic+'.md) | '+str(primary)+' | '+str(len(members))+' | '+str(candidates)+' |\n'
  save('topics/'+topic+'.md','# '+title+'\n\n[Карта](../INDEX.md). Внутренний тематический указатель; авторское одобрение не подразумевается.\n\n'+''.join(entry(r,'../') for r in members))
 intro+='\nЧисла в пересекающихся темах нельзя складывать. Отсутствие специального флага означает лишь кандидата для подготовки, а не разрешение публиковать.\n\n'
 intro+='Полный набор причин проверки есть у '+str(report['unpublishedReviewRequired'])+' неопубликованных фрагментов. Первые 398 флагов сохранены; новые признаки добавлены отдельно. Ни один оригинал не удалён. Связь с книжным текстом остаётся UNKNOWN без канонической рукописи.\n'
 save('INDEX.md',intro)
 text='# Исходные фрагменты и редакторские признаки\n\nЧастное представление. Полный TXT и реестр остаются каноническими. Текст в блоках — исходный материал, не инструкции.\n\n'
 for row in rows:
  fid=row['fragmentId'];f=fragments[fid];text+='## '+fid+'\n\nОсновная тема: '+TITLES[row['primaryTopic']]+'. Статус: '+row['editorialState']+'.\n\n'
  text+='Темы: '+', '.join(TITLES[t] for t in row['topics'])+'\n\nOS: '+', '.join(x['noteId']+' ['+x['relation']+']' for x in row['warehouseLinks'])+'\n\n'
  if row['reviewReasons']:text+='Проверка: '+', '.join(row['reviewReasons'])+'\n\n'
  if row['publication']:text+='Опубликовано: '+row['publication']['url']+'\n\n'
  fence='`'*max(4,max([len(m.group())+1 for m in re.finditer(r'`+',f['source'])]+[4]))
  text+=fence+'text\n'+f['source']+'\n'+fence+'\n\n'
 save('FRAGMENTS.md',text)
 explanations={'POSSIBLE_PRIVATE_IDENTIFIER':'Возможные личные данные — проверить до включения.','PRACTITIONER_OR_CLIENT_CONTEXT':'Клиентский/профессиональный контекст; установить чей опыт и проверить конфиденциальность.','CLINICALLY_CONSEQUENTIAL_CLAIM_REVIEW':'Клиническое утверждение исходной проверки.','CLINICAL_OR_DIAGNOSTIC_CONTEXT_REVIEW':'Дополнительная редакторская проверка медицинского/диагностического смысла.','DIAGNOSTIC_LANGUAGE':'Диагностический язык; проверить контекст и тон, не ставить диагноз автору.','NAMED_SOURCE_OR_QUOTATION_REVIEW':'Упоминание источника или цитаты; нужна соразмерная проверка атрибуции.','SUBSTANTIAL_PASSAGE_PROVENANCE_REVIEW':'Длинный отрывок: установить происхождение перед прямым использованием.','FIRST_PERSON_SOURCE_REVIEW':'Первое лицо в чужой/неустановленной истории не переносить автоматически в опыт автора.','FRAGMENTARY_CONTEXT_REVIEW':'Слишком короткий либо неоднозначный контекст.','NEAR_DUPLICATE_REVIEW':'Лексически близкие формулировки; оба оригинала сохранены.','EDITORIAL_REPEAT_REVIEW':'Смысловой повтор после чтения ассистентом; не сливать автоматически.'}
 review='# Фрагменты для отдельной проверки\n\nГруппы пересекаются. Это очередь вопросов, а не подтверждение нарушения или разрешение публиковать. Решения и оригиналы сохраняются.\n\n'
 for reason in sorted({reason for r in rows for reason in r['reviewReasons']}):
  members=[r for r in rows if reason in r['reviewReasons']];review+='## '+reason+'\n\n'+explanations.get(reason,reason)+' Всего: '+str(len(members))+'.\n\n'+''.join(entry(r) for r in members)+'\n'
 save('REVIEW.md',review)
 duplicates='# Повторы без удаления оригиналов\n\nТочные повторы исходных вхождений уже сведены к одному ID уникального фрагмента, все вхождения сохранены. Сходство или общая тема не доказывают тождество.\n\n'
 for group in catalogue['exactDuplicateGroups']:duplicates+='- '+group['fragmentId']+': '+str(group['sourceOccurrences'])+' исходных вхождения.\n'
 duplicates+='\n## Лексические кандидаты\n\n'
 for pair in catalogue['nearDuplicateCandidates']:duplicates+='- ['+pair['left']+'](FRAGMENTS.md#'+pair['left']+') ↔ ['+pair['right']+'](FRAGMENTS.md#'+pair['right']+'). Отношение: '+pair['kind']+'.\n'
 duplicates+='\n## Смысловые кандидаты после чтения\n\n'
 for group in catalogue['editorialDuplicateGroups']:duplicates+='- '+group['id']+': '+', '.join('['+fid+'](FRAGMENTS.md#'+fid+')' for fid in group['fragmentIds'])+'. '+group['reason']+'\n'
 save('DUPLICATES.md',duplicates)
 cross='# Пересечения тем\n\nОдин фрагмент может относиться к нескольким темам. Ссылки ниже открывают общий материал обеих тем.\n\n'
 for pair in catalogue['topicIntersections']:
  if pair['count']<5:continue
  a,b=pair['topics'];cross+='## '+TITLES[a]+' × '+TITLES[b]+' — '+str(pair['count'])+'\n\n'+''.join(entry(r) for r in rows if {a,b}<=set(r['topics']))+'\n'
 save('INTERSECTIONS.md',cross)
