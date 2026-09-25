import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
a = json.loads((root / 'artifacts/jekyll-authenticated-provider-gate-v5-debug/diagnostic.json').read_text())['blocks']
b = json.loads((root / 'artifacts/jekyll-authenticated-provider-gate-v5-debug/failed-smoke-retry-low.json').read_text())['blocks']
by = {x['blockId']: x for x in a + b}
qa = {
 'jekyll-sample-v2:section-002:b0005': {'result':'PASS_WITH_REVIEW','issues':['exact three-month condition needs editorial correction; output is complete but current phrasing is ambiguous']},
 'jekyll-sample-v2:section-002:b0007': {'result':'PASS_WITH_REVIEW','issues':['inference remains a thought; translation is compressed and needs literary review']},
 'jekyll-sample-v2:section-002:b0013': {'result':'PASS_WITH_REVIEW','issues':['Lanyon opinion and speech act preserved; name note requires independent name-policy review; time phrasing is awkward']},
 'jekyll-sample-v2:section-003:b0024': {'result':'PASS','issues':['bounded certainty and withheld grounds preserved; no identity reveal']},
 'jekyll-sample-v2:section-003:b0028': {'result':'PASS_WITH_REVIEW','issues':['document status preserved; claim wording and literary compression require editorial review']},
}
records = []
for bid in ['jekyll-sample-v2:section-002:b0005','jekyll-sample-v2:section-002:b0007','jekyll-sample-v2:section-002:b0013','jekyll-sample-v2:section-003:b0024','jekyll-sample-v2:section-003:b0028']:
 x = by[bid]; x['qa'] = qa[bid]; records.append(x)
out = {'schemaVersion':'1','gate':'JEKYLL_5_BLOCK_REAL_SMOKE_V1','provider':'OpenAI Responses API','model':'gpt-5.6-sol','realProvider':True,'configurations':{'originalSuccessful':'medium/2400','retryFailed':'low/3000'},'blocks':records,'providerSmoke':'PASS_WITH_REVIEW','productionReasoning':'LOW_CANDIDATE_UNRESOLVED'}
path = root / 'artifacts/jekyll-authenticated-provider-gate-v5-debug/JEKYLL_5_BLOCK_REAL_SMOKE_V1.json'
path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
print(path)
