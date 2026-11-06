"""Role-stage cache adapter for NarrativeRunner, never a semantic approval engine."""
import hashlib
import json
import re
import time
import urllib.request
from pathlib import Path
from .narrative_pipeline import NarrativeRunner, PipelineConfig, SourceBlock

def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()

def fingerprint(value):
    return digest(json.dumps(value, sort_keys=True, ensure_ascii=False))

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError('LOCAL_ONLY_REDIRECT_REJECTED')

class RoleStages:
    def __init__(self, root, config):
        self.root = Path(root)
        self.config = config
        if config['endpoint'] != 'http://127.0.0.1:11434/api/chat':
            raise ValueError('LOCAL_ONLY_ENDPOINT_REQUIRED')
        allowed_models = config.get('allowed_models', ['qwen3.5:4b', 'translategemma:4b'])
        if set(config['models']) != set(allowed_models) or len(allowed_models) != 2:
            raise ValueError('COMPACT_PAIR_REQUIRED')
        if any(len(d) != 64 or any(c not in '0123456789abcdef' for c in d)
               for d in config['models'].values()):
            raise ValueError('PINNED_DIGEST_REQUIRED')
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        self._verified = False
        self.metrics = {'calls': [], 'cache_hits': 0, 'external_inference_calls': 0, 'external_spend_usd': 0}
        self.root.mkdir(parents=True, exist_ok=True)
        if (self.root/'calls.json').exists():
            self.metrics = json.loads((self.root/'calls.json').read_text())

    def verify_models(self):
        tags = json.load(self.opener.open('http://127.0.0.1:11434/api/tags', timeout=15))
        actual = {m['name']: m['digest'] for m in tags['models']}
        if any(actual.get(m) != d for m, d in self.config['models'].items()):
            raise ValueError('MODEL_DIGEST_MISMATCH')
        self._verified = True
        (self.root/'live-models.json').write_text(json.dumps(tags, indent=2))

    def stage(self, fixture, model, role, prompt, draft='', schema=None):
        options = {**self.config['options'], **self.config.get('role_options', {}).get(role, {})}
        identity = {'source_hash': digest(fixture['source']), 'model_digest': self.config['models'][model],
                    'role': role, 'prompt_version': self.config['prompt_versions'].get(role, 'v1'),
                    'prompt_hash': digest(prompt),
                    'policy_version': self.config.get('role_policy_versions', {}).get(role, self.config['policy_version']),
                    'canon_version': self.config.get('role_canon_versions', {}).get(role, self.config['canon_version']),
                    'input_draft_hash': digest(draft), 'schema': schema, 'options': options, 'thinking': False}
        key = fingerprint(identity)
        run_dir = self.root/'stages'/key
        manifest = run_dir/'run-manifest.json'
        cached = False
        if manifest.exists():
            old_manifest = json.loads(manifest.read_text())
            if len(old_manifest.get('blocks', [])) != 1:
                raise ValueError('CORRUPT_STAGE_BLOCK_COUNT')
            provenance_path = run_dir/'provenance.json'
            if provenance_path.exists():
                provenance = json.loads(provenance_path.read_text())
                if provenance.get('identity') != identity or provenance.get('stage_key') != key:
                    raise ValueError('CORRUPT_STAGE_IDENTITY')
            for item in old_manifest['blocks']:
                if item.get('source_hash') != identity['source_hash'] or item.get('block_id') != fixture['id']:
                    raise ValueError('CORRUPT_STAGE_SOURCE')
                if item['status'] == 'FAILED' and (run_dir/'provenance.json').exists():
                    record = json.loads((run_dir/'provenance.json').read_text())
                    record.update(cache_hit=True, cached_failure=True)
                    self.metrics['cache_hits'] += 1
                    (self.root/'calls.json').write_text(json.dumps(self.metrics, ensure_ascii=False, indent=2))
                    return record
                if item['status'] == 'SUCCESS':
                    if digest(item['translation_text']) != item['translation_hash']:
                        raise ValueError('CORRUPT_STAGE_CACHE')
                    cached = True
        if self.config.get('cache_only') and not cached:
            raise ValueError('CACHE_ONLY_MISS')
        block = SourceBlock('local-ensemble-v1', role, fixture['id'], fixture['source'],
                            identity['source_hash'], 'FIXTURE', 0)
        record = {'fixture': fixture['id'], 'witness': fixture['witness'], 'model': model,
                  'identity': identity, 'stage_key': key, 'prompt': prompt,
                  'prompt_origin': 'HASH_VERIFIED_CACHE_RECONSTRUCTION' if cached else 'LIVE_REQUEST'}
        def provider(block, unused):
            if not self._verified:
                self.verify_models()
            body = {'model': model, 'stream': False, 'think': False, 'keep_alive': '30m',
                    'messages': [{'role': 'user', 'content': prompt}], 'options': options}
            if schema is not None:
                body['format'] = schema
            start = time.monotonic()
            call = dict(record)
            try:
                response = json.load(self.opener.open(urllib.request.Request(self.config['endpoint'],
                    data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'}), timeout=360))
                text = response.get('message', {}).get('content', '')
                load_ns, total_ns = response.get('load_duration'), response.get('total_duration')
                call.update(raw_response=response, output=text, output_hash=digest(text),
                            load_seconds=None if load_ns is None else load_ns/1e9,
                            warm_seconds=None if load_ns is None or total_ns is None else (total_ns-load_ns)/1e9,
                            generated_tokens=response.get('eval_count'), prompt_tokens=response.get('prompt_eval_count'))
                if response.get('model') != model or not text.strip() or response.get('done_reason') == 'length':
                    raise ValueError('UNEXPECTED_EMPTY_OR_TRUNCATED_RESPONSE')
                call['status'] = 'RESPONSE'
                return text
            except Exception as exc:
                call.update(status='FAILED', error=str(exc))
                raise
            finally:
                call['elapsed_seconds'] = time.monotonic()-start
                self.metrics['calls'].append(call)
                (self.root/'calls.json').write_text(json.dumps(self.metrics, ensure_ascii=False, indent=2))
        output = NarrativeRunner(run_dir, PipelineConfig(max_retries=0)).run([block], provider)[0]
        if cached:
            self.metrics['cache_hits'] += 1
        record.update(output=output.translation_text, output_hash=output.translation_hash,
                      status=output.status, error=output.error, cache_hit=cached)
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir/'provenance.json').write_text(json.dumps(record, ensure_ascii=False, indent=2))
        (self.root/'calls.json').write_text(json.dumps(self.metrics, ensure_ascii=False, indent=2))
        return record

ISSUE_TYPES = ['OMISSION','ADDITION','MEANING_SHIFT','SUBJECT_OBJECT_REVERSAL','MODALITY_CHANGE',
               'REGISTER_SHIFT','REALIA_ERROR','METAPHOR_ERROR','TEMPORAL_ERROR','REFERENCE_ERROR','OTHER']
FINDING_SCHEMA = {'type':'object','properties':{'findings':{'type':'array','items':{'type':'object',
    'properties':{**{k:{'type':'string'} for k in ['SOURCE_SPAN','FRENCH_SPAN','SOURCE_MEANING',
        'DRAFT_MEANING','DISCREPANCY']},'ISSUE_TYPE':{'type':'string','enum':ISSUE_TYPES},
        'SEVERITY':{'type':'string','enum':['BLOCKER','MAJOR','MINOR']},'CONFIDENCE':{'type':'number'}},
    'required':['SOURCE_SPAN','FRENCH_SPAN','ISSUE_TYPE','SOURCE_MEANING','DRAFT_MEANING','DISCREPANCY',
        'SEVERITY','CONFIDENCE'],'additionalProperties':False}}},'required':['findings'],'additionalProperties':False}

def validate_findings(raw, source, draft):
    value = json.loads(raw)
    if set(value) != {'findings'} or not isinstance(value['findings'], list):
        raise ValueError('FINDINGS_SCHEMA')
    norm = lambda s: ' '.join(s.split())
    required = set(FINDING_SCHEMA['properties']['findings']['items']['required'])
    for index, original in enumerate(value['findings']):
        f = dict(original)
        value['findings'][index] = f
        if set(f) != required or f['ISSUE_TYPE'] not in ISSUE_TYPES or f['SEVERITY'] not in ['BLOCKER','MAJOR','MINOR']:
            raise ValueError('FINDING_FIELDS')
        if not all(isinstance(f[k], str) for k in required-{'CONFIDENCE'}):
            raise ValueError('FINDING_TYPES')
        if not isinstance(f['CONFIDENCE'], (float,int)) or isinstance(f['CONFIDENCE'],bool) or not 0 <= f['CONFIDENCE'] <= 1:
            raise ValueError('CONFIDENCE_RANGE')
        # Models sometimes wrap quoted spans in additional quotation marks.
        # Strip only boundary quote markup, never fuzzy-match or alter source text.
        for field, text in [('SOURCE_SPAN', source), ('FRENCH_SPAN', draft)]:
            if f[field] and norm(f[field]) not in norm(text):
                candidate = f[field].strip().strip('"\'«»„“”').strip()
                if candidate and norm(candidate) in norm(text):
                    f[field] = candidate
        if not f['SOURCE_SPAN'].strip() or norm(f['SOURCE_SPAN']) not in norm(source):
            raise ValueError('UNWITNESSED_SOURCE_SPAN')
        if not f['FRENCH_SPAN'].strip() and f['ISSUE_TYPE'] != 'OMISSION':
            raise ValueError('EMPTY_DRAFT_SPAN')
        if f['FRENCH_SPAN'] and norm(f['FRENCH_SPAN']) not in norm(draft):
            raise ValueError('INVENTED_DRAFT_SPAN')
        if not all(f[k].strip() for k in ['SOURCE_MEANING','DRAFT_MEANING','DISCREPANCY']):
            raise ValueError('MISSING_SEMANTIC_EVIDENCE')
        if f['DISCREPANCY'].strip().lower().rstrip('.') in {'none','no change','no discrepancy','no difference','no issue'}:
            raise ValueError('NO_DISCREPANCY_IS_NOT_A_FINDING')
        if re.fullmatch(r'different (?:word choice|word order|phrasing|vocabulary),? but (?:same|similar) meaning\.?',
                        f['DISCREPANCY'].strip(), re.I):
            raise ValueError('GENERIC_PARAPHRASE_IS_NOT_SEMANTIC_EVIDENCE')
    return value
