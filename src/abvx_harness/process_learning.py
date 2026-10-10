"""Explicit local OS/Cortex exchange. Telemetry only; no remote calls or adoption."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

WORKFLOWS = {'book.radar.research', 'book.production', 'site.content.publish', 'os.maintenance'}
ID = re.compile(r'[a-zA-Z0-9][a-zA-Z0-9:._-]{0,119}\Z')
OUTCOME_KEYS = {'schemaVersion','kind','tenant','runId','workflowId','workflowVersion','origin','startedAt',
                'completedAt','status','elapsedSeconds','ownerMinutes','reworkCount','qualityGate','safetyGate','evidence'}
PACKET_KEYS = {'schemaVersion','kind','packetId','direction','source','classification','dataKind','observedAt',
               'provenance','permittedUse','returnAuthority','payload'}
PROPOSAL_KEYS = {'schemaVersion','kind','tenant','proposalId','workflowId','baselineVersion','candidateVersion','change',
                'sourcePacketId','sourcePayloadDigest','baselineRunIds','heldOutRunIds','baseline','heldOut','status',
                'reasons','authority','executionAuthorized','ownerReviewRequired','proposalDigest'}


def _shape(value, keys):
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError('Unexpected process contract fields')


def _id(value):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise ValueError('Invalid opaque identifier')


def _integer(value):
    if type(value) is not int or not 0 <= value <= 9007199254740991:
        raise ValueError('Invalid nonnegative metric')


def _time(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z', value):
        raise ValueError('Invalid UTC timestamp')
    return datetime.fromisoformat(value.replace('Z','+00:00'))


def _canonical(value):
    # JSON number encoding shared with the JS consumer; reject nonfinite values.
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError('Nonfinite number')
        return int(value) if value.is_integer() else value
    if isinstance(value, list):
        return [_canonical(v) for v in value]
    if isinstance(value, dict):
        return {k:_canonical(v) for k,v in value.items()}
    return value


def digest(value):
    return hashlib.sha256(json.dumps(_canonical(value), sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def validate_outcome(value):
    _shape(value, OUTCOME_KEYS)
    if type(value['schemaVersion']) is not int or value['schemaVersion'] != 1 or value['kind'] != 'AbvxOsProcessOutcome' or value['tenant'] != 'abvx-os':
        raise ValueError('Wrong OS tenant/version')
    _id(value['runId']); _id(value['workflowVersion'])
    if value['workflowId'] not in WORKFLOWS or value['origin'] not in {'OBSERVED','SYNTHETIC'} or value['status'] not in {'PASS','FAIL','CANCELLED'}:
        raise ValueError('Invalid process state')
    for key in ('qualityGate','safetyGate'):
        if value[key] not in {'PASS','FAIL','UNKNOWN'}:
            raise ValueError('Invalid process gate')
    _integer(value['reworkCount'])
    if type(value['elapsedSeconds']) not in (int,float) or not math.isfinite(value['elapsedSeconds']) or not 0<=value['elapsedSeconds']<=9007199254740991:
        raise ValueError('Invalid elapsed metric')
    if value['ownerMinutes'] != 'UNKNOWN':
        _integer(value['ownerMinutes'])
    if _time(value['completedAt'])<_time(value['startedAt']) or abs((_time(value['completedAt']) - _time(value['startedAt'])).total_seconds() - value['elapsedSeconds'])>0.01:
        raise ValueError('Elapsed time does not match observation')
    if not isinstance(value['evidence'], list) or not 1 <= len(value['evidence']) <= 20:
        raise ValueError('Process evidence required')
    for ref in value['evidence']:
        _shape(ref, {'ref','sha256'}); _id(ref['ref'])
        if not isinstance(ref['sha256'], str) or not re.fullmatch('[a-f0-9]{64}', ref['sha256']):
            raise ValueError('Invalid evidence digest')
    return value


def build_packet(outcomes, packet_id, observed_at):
    _id(packet_id); observed = _time(observed_at)
    if not isinstance(outcomes, list) or not 1 <= len(outcomes) <= 100:
        raise ValueError('Select between 1 and 100 outcomes')
    for row in outcomes:
        validate_outcome(row)
        if _time(row['completedAt']) > observed:
            raise ValueError('Future process outcome')
    if len({r['runId'] for r in outcomes}) != len(outcomes):
        raise ValueError('Duplicate OS run ID')
    if len({r['origin'] for r in outcomes}) != 1:
        raise ValueError('Synthetic and observed outcomes cannot be mixed')
    payload = {'schemaVersion':1, 'kind':'AbvxOsProcessOutcomeBatch', 'tenant':'abvx-os', 'outcomes':outcomes}
    return {'schemaVersion':1, 'kind':'CortexABVImportPacket', 'packetId':packet_id,
            'direction':'inbound_to_cortex_abv', 'source':{'kind':'owned_project_ecosystem','id':'abvx-os'},
            'classification':'protected', 'dataKind':'abvx_os_process_outcomes', 'observedAt':observed_at,
            'provenance':[{'kind':'abvx_os_outcome_batch','ref':packet_id,'digest':digest(payload)}],
            'permittedUse':['private_context'], 'returnAuthority':'none', 'payload':payload}


def validate_packet(packet):
    _shape(packet, PACKET_KEYS)
    _shape(packet['payload'], {'schemaVersion','kind','tenant','outcomes'})
    expected = build_packet(packet['payload']['outcomes'], packet['packetId'], packet['observedAt'])
    if digest(packet) != digest(expected):
        raise ValueError('OS packet profile or payload digest mismatch')
    return packet


def inspect_proposal(packet, proposal, current_version):
    validate_packet(packet); _shape(proposal, PROPOSAL_KEYS); _id(current_version)
    material = {k:v for k,v in proposal.items() if k != 'proposalDigest'}
    if proposal['proposalDigest'] != digest(material):
        raise ValueError('Optimization proposal digest mismatch')
    if type(proposal['schemaVersion']) is not int or proposal['schemaVersion'] != 1 or proposal['kind'] != 'AbvxOsOptimizationProposal' or proposal['tenant'] != 'abvx-os':
        raise ValueError('Wrong proposal tenant/version')
    if proposal['authority'] != 'none' or proposal['executionAuthorized'] is not False or proposal['ownerReviewRequired'] is not True:
        raise ValueError('Optimization must not carry execution authority')
    _id(proposal['proposalId']); _id(proposal['candidateVersion'])
    if proposal['baselineVersion'] != current_version or proposal['candidateVersion'] == current_version:
        raise ValueError('Stale workflow version')
    if proposal['sourcePacketId'] != packet['packetId'] or proposal['sourcePayloadDigest'] != digest(packet['payload']):
        raise ValueError('Optimization source batch mismatch')
    if proposal['workflowId'] not in WORKFLOWS or proposal['change'] not in {'BATCH_VALIDATION','REUSE_VERIFIED_CONTEXT','EARLY_INPUT_VALIDATION'}:
        raise ValueError('Unsupported optimization scope')
    ids=[]; groups=[]
    lookup={r['runId']:r for r in packet['payload']['outcomes']}
    for key, version in [('baselineRunIds',current_version),('heldOutRunIds',proposal['candidateVersion'])]:
        if not isinstance(proposal[key], list):
            raise ValueError('Explicit cohorts required')
        rows=[]
        for rid in proposal[key]:
            _id(rid); row=lookup.get(rid)
            if not row or row['workflowId'] != proposal['workflowId'] or row['workflowVersion'] != version:
                raise ValueError('Cohort outside workflow/version')
            rows.append(row); ids.append(rid)
        groups.append(rows)
    if len(set(ids)) != len(ids):
        raise ValueError('Baseline and held-out runs overlap')
    def metrics(rows):
        if not rows: return None
        return {'elapsedSeconds':median(r['elapsedSeconds'] for r in rows),
                'ownerMinutes':'UNKNOWN' if any(r['ownerMinutes']=='UNKNOWN' for r in rows) else median(r['ownerMinutes'] for r in rows),
                'reworkCount':median(r['reworkCount'] for r in rows)}
    before, after = map(metrics, groups)
    if proposal['baseline'] != before or proposal['heldOut'] != after:
        raise ValueError('Optimization metrics mismatch')
    reasons=[]; all_rows=sum(groups, [])
    if len({tuple(sorted((e['ref'],e['sha256']) for e in ( [e for e in row['evidence'] if e['ref'].startswith('workload:')] or row['evidence'] ))) for row in all_rows})>1: reasons.append('WORKLOAD_NOT_COMPARABLE')
    if any(len(rows)<5 for rows in groups): reasons.append('INSUFFICIENT_INDEPENDENT_RUNS')
    if any(r['status']!='PASS' or r['qualityGate']!='PASS' or r['safetyGate']!='PASS' for r in all_rows): reasons.append('QUALITY_OR_SAFETY_NOT_ESTABLISHED')
    if any(r['ownerMinutes']=='UNKNOWN' for r in all_rows): reasons.append('OWNER_EFFORT_UNKNOWN')
    if before and after:
        if after['elapsedSeconds'] >= before['elapsedSeconds']: reasons.append('NO_TIME_IMPROVEMENT')
        if before['ownerMinutes']!='UNKNOWN' and after['ownerMinutes']!='UNKNOWN' and after['ownerMinutes']>before['ownerMinutes']: reasons.append('OWNER_EFFORT_INCREASED')
        if after['reworkCount']>before['reworkCount']: reasons.append('REWORK_INCREASED')
    if any(r['origin']!='OBSERVED' for r in all_rows): reasons.append('SYNTHETIC_EVIDENCE_ONLY')
    expected_status='INSUFFICIENT_EVIDENCE' if reasons else 'ELIGIBLE_FOR_OWNER_REVIEW'
    if proposal['status'] != expected_status or proposal['reasons'] != reasons:
        raise ValueError('Optimization qualification mismatch')
    return {'schemaVersion':1,'kind':'AbvxOsOptimizationReview','proposalId':proposal['proposalId'],
            'proposalDigest':proposal['proposalDigest'],'workflowId':proposal['workflowId'],
            'currentVersion':current_version,'status':'PENDING_OWNER_REVIEW' if not reasons else 'BLOCKED_INSUFFICIENT_EVIDENCE',
            'reasons':reasons,'executionAuthorized':False}


def inspect_candidate(context, candidate, current_version, packets):
    """Import a model suggestion for review only, never execution or measured promotion."""
    _id(current_version)
    _shape(context, {'schemaVersion','kind','tenant','workflowId','query','asOf','retrievalMode','eligibleRuns','results','authority','executionAuthorized'})
    if type(context['schemaVersion']) is not int or context['schemaVersion']!=1 or context['kind']!='AbvxOsExperienceContext' or context['tenant']!='abvx-os' or context['workflowId'] not in WORKFLOWS or context['authority']!='none' or context['executionAuthorized'] is not False:
        raise ValueError('Scoped OS context required')
    _integer(context['eligibleRuns'])
    if not isinstance(context['asOf'],str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z',context['asOf']):
        raise ValueError('Valid UTC context observation required')
    as_of=datetime.fromisoformat(context['asOf'].replace('Z','+00:00'))
    if not isinstance(packets,list) or not 1<=len(packets)<=100:raise ValueError('Explicit OS source batches required')
    source_batches={}
    for packet in packets:
        validate_packet(packet)
        if packet['packetId'] in source_batches:raise ValueError('Duplicate source batch')
        source_batches[packet['packetId']]=packet
    if not isinstance(context['results'],list) or not 1<=len(context['results'])<=20 or context['eligibleRuns']<len(context['results']):
        raise ValueError('Bounded retrieved evidence required')
    lookup={}
    for result in context['results']:
        _shape(result, {'outcome','sourcePacketId','sourcePayloadDigest'})
        row=validate_outcome(result['outcome']);_id(result['sourcePacketId'])
        if row['workflowId']!=context['workflowId'] or row['runId'] in lookup or not re.fullmatch('[a-f0-9]{64}',result['sourcePayloadDigest']):
            raise ValueError('Wrong or duplicate context evidence')
        source=source_batches.get(result['sourcePacketId'])
        if not source or digest(source['payload'])!=result['sourcePayloadDigest'] or not any(digest(r)==digest(row) for r in source['payload']['outcomes']) or _time(row['completedAt'])>as_of:
            raise ValueError('Retrieved evidence not grounded in OS source batches')
        lookup[row['runId']]=result
    if candidate.get('status')=='READY_FOR_ANALYSIS':
        _shape(candidate, {'schemaVersion','kind','tenant','status','workflowId','contextDigest','sources','authority','executionAuthorized','candidateDigest'})
        material={k:v for k,v in candidate.items() if k!='candidateDigest'}
        expected=[{'runId':rid,'sourcePacketId':r['sourcePacketId'],'sourcePayloadDigest':r['sourcePayloadDigest']} for rid,r in lookup.items()]
        if candidate['schemaVersion']!=1 or candidate['kind']!='AbvxOsLearningCandidate' or candidate['tenant']!='abvx-os' or candidate['workflowId']!=context['workflowId'] or candidate['authority']!='none' or candidate['executionAuthorized'] is not False or candidate['candidateDigest']!=digest(material) or candidate['contextDigest']!=digest(context) or candidate['sources']!=expected or any(r['outcome']['workflowVersion']!=current_version or r['outcome']['ownerMinutes']=='UNKNOWN' or r['outcome']['qualityGate']!='PASS' or r['outcome']['safetyGate']!='PASS' for r in lookup.values()):
            raise ValueError('Readiness not grounded in complete current evidence')
        return {'schemaVersion':1,'kind':'AbvxOsLearningReview','candidateDigest':candidate['candidateDigest'],'workflowId':context['workflowId'],'currentVersion':current_version,'status':'RECORDED_READY_FOR_ANALYSIS','executionAuthorized':False}
    if candidate.get('status')=='INSUFFICIENT_METRICS':
        _shape(candidate, {'schemaVersion','kind','tenant','status','workflowId','contextDigest','findings','sources','authority','executionAuthorized','candidateDigest'})
        material={k:v for k,v in candidate.items() if k!='candidateDigest'}
        if type(candidate['schemaVersion']) is not int or candidate['schemaVersion']!=1 or candidate['kind']!='AbvxOsLearningCandidate' or candidate['tenant']!='abvx-os' or candidate['workflowId']!=context['workflowId'] or candidate['authority']!='none' or candidate['executionAuthorized'] is not False or candidate['candidateDigest']!=digest(material) or candidate['contextDigest']!=digest(context):
            raise ValueError('Invalid metric diagnosis')
        if any(r['outcome']['workflowVersion']!=current_version for r in lookup.values()):
            raise ValueError('Stale diagnosis evidence')
        checks=[('OWNER_EFFORT_UNKNOWN',lambda r:r['ownerMinutes']=='UNKNOWN'),('QUALITY_NOT_ESTABLISHED',lambda r:r['qualityGate']!='PASS'),('SAFETY_NOT_ESTABLISHED',lambda r:r['safetyGate']!='PASS')]
        findings=[{'code':code,'runIds':[rid for rid,r in lookup.items() if missing(r['outcome'])]} for code,missing in checks]
        findings=[f for f in findings if f['runIds']]
        sources=[{'runId':rid,'sourcePacketId':r['sourcePacketId'],'sourcePayloadDigest':r['sourcePayloadDigest']} for rid,r in lookup.items()]
        if not findings or digest(candidate['findings'])!=digest(findings) or digest(candidate['sources'])!=digest(sources):
            raise ValueError('Metric findings not grounded in source batches')
        return {'schemaVersion':1,'kind':'AbvxOsLearningReview','candidateDigest':candidate['candidateDigest'],'workflowId':context['workflowId'],'currentVersion':current_version,'status':'NEEDS_MEASUREMENT','findings':findings,'executionAuthorized':False}
    _shape(candidate, {'schemaVersion','kind','tenant','status','workflowId','contextDigest','modelProvider','model','change','rationale','runIds','sources','limitations','authority','executionAuthorized','ownerReviewRequired','candidateDigest'})
    material={k:v for k,v in candidate.items() if k!='candidateDigest'}
    if candidate['candidateDigest']!=digest(material) or candidate['contextDigest']!=digest(context):
        raise ValueError('Candidate context or digest mismatch')
    if type(candidate['schemaVersion']) is not int or candidate['schemaVersion']!=1 or candidate['kind']!='AbvxOsLearningCandidate' or candidate['tenant']!='abvx-os' or candidate['workflowId']!=context['workflowId'] or candidate['status']!='PENDING_TRIAL' or candidate['modelProvider']!='local-ollama' or candidate['authority']!='none' or candidate['executionAuthorized'] is not False or candidate['ownerReviewRequired'] is not True:
        raise ValueError('Model candidate must be review only')
    _id(candidate['model'])
    if candidate['change'] not in {'BATCH_VALIDATION','REUSE_VERIFIED_CONTEXT','EARLY_INPUT_VALIDATION'} or not isinstance(candidate['rationale'],str) or not 1<=len(candidate['rationale'])<=1000:
        raise ValueError('Unsupported candidate scope')
    ids=candidate['runIds']
    if not isinstance(ids,list) or not 1<=len(ids)<=20 or len(set(ids))!=len(ids):
        raise ValueError('Bounded unique run citations required')
    for rid in ids:
        _id(rid)
        if rid not in lookup or lookup[rid]['outcome']['workflowVersion']!=current_version:
            raise ValueError('Unknown or stale candidate evidence')
    expected=[{'runId':rid,'sourcePacketId':lookup[rid]['sourcePacketId'],'sourcePayloadDigest':lookup[rid]['sourcePayloadDigest']} for rid in ids]
    if candidate['sources']!=expected or candidate['limitations']!=['MODEL_SUGGESTION_NOT_MEASURED_GAIN','INDEPENDENT_BASELINE_AND_HELD_OUT_TRIAL_REQUIRED']:
        raise ValueError('Candidate citations or limitations changed')
    return {'schemaVersion':1,'kind':'AbvxOsLearningReview','candidateDigest':candidate['candidateDigest'],'workflowId':context['workflowId'],'currentVersion':current_version,'status':'PENDING_OWNER_TRIAL_REVIEW','executionAuthorized':False}


def _write_once(path, value):
    path=Path(path); payload=json.dumps(value, sort_keys=True, indent=2)+'\n'
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_text() != payload: raise ValueError('Destination already contains different evidence')
        return
    with path.open('x', encoding='utf-8') as handle: handle.write(payload)


def record_check(root, check, record_path):
    commands={'isolated-books':[sys.executable,str(root/'scripts/check-isolated-books.py')],
              'contract-checks':['/bin/sh',str(root/'bin/check')],
              'maintenance-tests':[sys.executable,'-m','unittest','discover','-s','tests','-p','test_maintenance.py','-q']}
    if check not in commands: raise ValueError('Unknown read-only check')
    root=root.resolve(); path=Path(record_path).resolve()
    if not path.is_relative_to(root/'.tmp') or path.exists(): raise ValueError('Record a new check under ignored .tmp/')
    start=datetime.now(timezone.utc); tick=time.monotonic()
    import os
    check_env={**os.environ,'ABVX_CHECK_PYTHON':sys.executable}
    process=subprocess.run(commands[check], cwd=root, capture_output=True,env=check_env)
    elapsed=round(time.monotonic()-tick,6); end=datetime.now(timezone.utc)
    proof=process.stdout+process.stderr
    row={'schemaVersion':1,'kind':'AbvxOsProcessOutcome','tenant':'abvx-os','runId':path.stem,
         'workflowId':'os.maintenance','workflowVersion':'maintenance-v1','origin':'OBSERVED',
         'startedAt':start.isoformat(timespec='milliseconds').replace('+00:00','Z'),'completedAt':end.isoformat(timespec='milliseconds').replace('+00:00','Z'),
         'status':'PASS' if process.returncode==0 else 'FAIL','elapsedSeconds':elapsed,
         'ownerMinutes':'UNKNOWN','reworkCount':0,'qualityGate':'PASS' if process.returncode==0 else 'FAIL',
         'safetyGate':'PASS' if check=='isolated-books' and process.returncode==0 else 'UNKNOWN',
         'evidence':[{'ref':'check:'+check,'sha256':hashlib.sha256(proof).hexdigest()}]}
    validate_outcome(row)
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.with_suffix('.log').open('xb') as handle:handle.write(proof)
    _write_once(path,row)
    return row


def main(argv=None, root=None):
    parser=argparse.ArgumentParser(description=__doc__); sub=parser.add_subparsers(dest='action',required=True)
    export=sub.add_parser('export'); export.add_argument('--outcomes',required=True);export.add_argument('--packet-id',required=True);export.add_argument('--observed-at',required=True);export.add_argument('--out',required=True)
    review=sub.add_parser('inspect-proposal');review.add_argument('--packet',required=True);review.add_argument('--proposal',required=True);review.add_argument('--current-version',required=True)
    suggestion=sub.add_parser('inspect-candidate');suggestion.add_argument('--context',required=True);suggestion.add_argument('--candidate',required=True);suggestion.add_argument('--current-version',required=True);suggestion.add_argument('--packets',required=True)
    record=sub.add_parser('record-check');record.add_argument('check',choices=['isolated-books','maintenance-tests','contract-checks']);record.add_argument('--out',required=True)
    args=parser.parse_args(argv)
    if args.action=='export':
        packet=build_packet(json.loads(Path(args.outcomes).read_text()),args.packet_id,args.observed_at);_write_once(args.out,packet)
        print(f'Prepared protected OS packet: {len(packet["payload"]["outcomes"])} outcomes. No import performed.')
    elif args.action=='inspect-proposal':
        value=inspect_proposal(json.loads(Path(args.packet).read_text()),json.loads(Path(args.proposal).read_text()),args.current_version)
        print(json.dumps(value,sort_keys=True))
    elif args.action=='inspect-candidate':
        value=inspect_candidate(json.loads(Path(args.context).read_text()),json.loads(Path(args.candidate).read_text()),args.current_version,json.loads(Path(args.packets).read_text()))
        print(json.dumps(value,sort_keys=True))
    else:
        value=record_check(root or Path(__file__).resolve().parents[2],args.check,args.out)
        print(f'Observed {args.check}: {value["status"]}; owner effort UNKNOWN.')
        return 0 if value['status']=='PASS' else 1
    return 0


if __name__=='__main__':
    try: raise SystemExit(main())
    except (ValueError,OSError) as error: raise SystemExit(f'OS learning exchange blocked: {error}')
