"""Source-bound sync adapter for the existing Nantes review and catalog.

No network, mail, calendar, submission or model calls. Transport is the owner's
already-connected remote device; source assertions remain auditable reports.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import re
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

from .harness import ValidationError, load_json, now_iso
from .nantes_radar import STATE, context_pack, digest, transaction

PRIMARY_CHAT = '6ac8a06b-fae0-83ed-b55e-fd23524d85f9'
CONFIG = Path('opportunities/private/sync-config.json')
FIELDS = ['status', 'application_status', 'owner_decision']
VALUES = {
    'status': {'UNKNOWN','OPEN','CLOSED','BLOCKED','IN_PROGRESS','COMPLETED'},
    'owner_decision': {'UNKNOWN','PURSUE','DEFERRED','DECLINED','WITHDRAWN','ON_HOLD'},
    'application_status': {'UNKNOWN','NOT_APPLIED','SUBMITTED','ACKNOWLEDGED','INTERVIEW_INVITED','INTERVIEW_SCHEDULED','INTERVIEW_COMPLETED','REJECTED','OFFER_RECEIVED','OFFER_ACCEPTED','WITHDRAWN','NO_RESPONSE'},
}


def read(root: Path):
    packet = context_pack(root)
    config = load_json(root / CONFIG) if (root / CONFIG).exists() else {}
    packet['local_sync'] = 'REMOTE_CONNECTED_DEVICE'
    packet['sync'] = {'schema_version': 'v1', 'run_id': str(uuid4()), 'device_id': config.get('device_id'), 'file': str(root / 'opportunities/private/sync-inbox.json'), 'allowed_fields': FIELDS, 'allowed_values': {k: sorted(v) for k,v in VALUES.items()}, 'source_kinds': ['chat_user','gmail_message','assistant_proposal'], 'max_updates': 25, 'command': str(root / 'bin/abvx') + ' opportunities sync-apply --file ' + str(root / 'opportunities/private/sync-inbox.json'), 'note': 'Fresh catalog read; no authority to send or change Gmail/Calendar.'}
    packet['sync']['file'] = str(root / 'opportunities/private' / ('sync-inbox-' + packet['sync']['run_id'] + '.json'))
    packet['sync']['command'] = str(root / 'bin/abvx') + ' opportunities sync-apply --file ' + packet['sync']['file']
    packet['sync']['packet_template'] = {'schema_version': 'v1', 'run_id': packet['sync']['run_id'], 'expected_digest': packet['catalog_digest'], 'updates': []}
    return packet


def strict(value, keys):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValidationError('sync object has missing or unsupported fields')


def validate_packet(packet):
    strict(packet, {'schema_version','run_id','expected_digest','updates'})
    if packet['schema_version'] != 'v1' or not isinstance(packet['run_id'],str) or not re.fullmatch(r'[a-zA-Z0-9-]{8,80}',packet['run_id']):
        raise ValidationError('invalid sync version/run ID')
    if not isinstance(packet['expected_digest'],str) or not re.fullmatch(r'[0-9a-f]{64}',packet['expected_digest']):
        raise ValidationError('sync needs a valid catalog digest')
    if not isinstance(packet['updates'],list) or len(packet['updates'])>25:
        raise ValidationError('sync update count exceeds limit')
    for update in packet['updates']:
        strict(update, {'opportunity_id','changes','source'})
        if not isinstance(update['opportunity_id'],str):
            raise ValidationError('invalid opportunity ID')
        changes=update['changes'];source=update['source']
        if not isinstance(changes,dict) or not changes or set(changes)-set(FIELDS):
            raise ValidationError('unsupported sync changes; no external-action fields exist')
        for field,value in changes.items():
            if not isinstance(value,str) or value not in VALUES[field]:
                raise ValidationError('unsupported status or decision value')
        strict(source, {'kind','message_id','ref','text','quote'})
        if not all(isinstance(v,str) for v in source.values()) or not 1<=len(source['text'])<=8000 or not 1<=len(source['quote'])<=2000:
            raise ValidationError('source needs bounded original text and exact quote')
        if source['quote'] not in source['text'] or not source['message_id'].strip():
            raise ValidationError('source quote not found in original message')
        url=urlsplit(source['ref'])
        if url.scheme!='https' or url.username or url.password:
            raise ValidationError('invalid source URL')
        if source['kind'] in {'chat_user','assistant_proposal'}:
            if url.hostname!='chatgpt.com' or url.path!='/c/'+PRIMARY_CHAT or parse_qs(url.query).get('messageId')!=[source['message_id']]:
                raise ValidationError('only source messages from the unified review chat are accepted')
        elif source['kind']=='gmail_message':
            if url.hostname!='mail.google.com' or not url.fragment or 'owner_decision' in changes:
                raise ValidationError('mail evidence cannot establish an owner decision')
        else:
            raise ValidationError('unsupported source kind')


def apply(root: Path, packet):
    validate_packet(packet)
    with transaction(root) as state:
        sync=state.setdefault('review_sync',{'receipts':{},'events':{},'proposals':[]})
        fingerprint=digest(packet)
        existing=sync['receipts'].get(packet['run_id'])
        if existing:
            if existing['packet_digest']!=fingerprint:
                raise ValidationError('sync run ID reused with changed payload')
            return {**existing,'replayed':True}
        if digest(state.get('opportunities',[]))!=packet['expected_digest']:
            raise ValidationError('catalog changed; sync-read and reconcile before retry')
        index={o['id']:o for o in state.get('opportunities',[])}
        if any(u['opportunity_id'] not in index for u in packet['updates']):
            raise ValidationError('unknown opportunity; source-backed intake required before sync')
        applied=queued=skipped=0
        for update in packet['updates']:
            event_id=digest(update)
            if event_id in sync['events']:
                skipped+=1
                continue
            source=update['source'];entry=index[update['opportunity_id']]
            if source['kind']=='assistant_proposal':
                sync['proposals'].append({'id':event_id,**update,'recorded_at':now_iso(),'status':'REVIEW','authority':'ADVISORY_ONLY'})
                queued+=1
            else:
                before={k:entry.get(k,'UNKNOWN') for k in update['changes']}
                # Do not erase established values merely because a new source is silent.
                changes={k:v for k,v in update['changes'].items() if v!='UNKNOWN' and entry.get(k)!=v}
                if changes:
                    previous=deepcopy(entry)
                    entry.update(changes)
                    if source['ref'] not in entry['source_refs']:
                        entry['source_refs'].append(source['ref'])
                    role='user' if source['kind']=='chat_user' else 'tool'
                    for field,value in changes.items():
                        entry.setdefault('observations',[]).append({'field':field,'claim':value+'; source quote: '+source['quote'],'source_role':role,'source_ref':source['ref'],'occurred_at':None})
                    state['history'].append({'opportunity_id':entry['id'],'origin':'connected-review-sync','recorded_at':now_iso(),'occurred_at':None,'previous_record':previous,'changes':changes,'source':source,'verification':'SOURCE_REPORTED_NOT_INDEPENDENTLY_VERIFIED','event_id':event_id})
                    applied+=1
                else:
                    skipped+=1
            sync['events'][event_id]={'run_id':packet['run_id'],'source_ref':source['ref']}
        receipt={'run_id':packet['run_id'],'packet_digest':fingerprint,'before_digest':packet['expected_digest'],'after_digest':digest(state.get('opportunities',[])),'applied':applied,'queued':queued,'skipped':skipped,'recorded_at':now_iso(),'external_actions':'NONE','replayed':False}
        sync['receipts'][packet['run_id']]=receipt
        return receipt
