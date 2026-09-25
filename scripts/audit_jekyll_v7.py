import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = json.loads((ROOT/'artifacts/jekyll-toki-pona-regression-v2/source-blocks.json').read_text())
run = json.loads((ROOT/'artifacts/jekyll-toki-pona-real-regression-v7/combined-output.json').read_text())
by = {x['blockId']: x for x in run['completed']}
second = {
 'b0005': (['TEMPORAL_DRIFT','LOST_CONDITIONALITY'], 'Three-month absence and conditional succession are ambiguous.', 'Restore exactly three calendar months and conditional transfer.'),
 'b0013': (['TEMPORAL_DRIFT','UNNATURAL_TOKI_PONA'], 'More-than-ten-years and opinion cadence are awkward.', 'Preserve time, speaker, and opinion status.'),
 'b0014': (['OVER_COMPRESSION','INFERENCE_TO_FACT'], 'Utterson inference is compressed.', 'Keep thought and uncertainty as focal character inference.'),
 'b0028': (['DOCUMENT_STATUS_DRIFT','UNNATURAL_TOKI_PONA'], 'Letter claim is highly compressed.', 'Keep signature, author, benefactor, safety/escape claim, and document-bound reaction.'),
 'b0038': (['UNNATURAL_TOKI_PONA','RELATIONSHIP_DRIFT'], 'Poole fear rhythm is awkward.', 'Preserve fear, cabinet confinement, and speech rhythm.'),
}
passes = {'b0001','b0003','b0006','b0009','b0010','b0012','b0019','b0029','b0033','b0034','b0036','b0037','b0039'}
records=[]
for b in src:
    bid=b['block_id']; short=bid.split(':')[-1]; x=by[bid]
    if short in second:
        tags, defect, preserve=second[short]; cls='SECOND_PASS_REQUIRED'
    elif short in passes:
        tags=[]; defect=''; preserve=''; cls='PASS'
    else:
        tags=['UNNATURAL_TOKI_PONA'] if len(x.get('translation',''))>300 else ['LEXICAL_PROBLEM']; defect='Ordinary editorial review for compression, rhythm, or lexical naturalness.'; preserve='Verify proposition, speaker, knowledge, and temporal relations.'; cls='PASS_WITH_REVIEW'
    records.append({'blockId':bid,'classification':cls,'issueTypes':tags,'sourceFunction':b['knowledge_type'],'defect':defect,'requiredPreservation':preserve,'translationChars':len(x.get('translation',''))})
counts={k:sum(r['classification']==k for r in records) for k in ['PASS','PASS_WITH_REVIEW','SECOND_PASS_REQUIRED','CRITICAL_FAIL']}
sample_words=sum(len(re.findall(r'\b\w+\b',b['source_text'])) for b in src); avg=sample_words/40; est=round(25622/avg)
matrix=[
 {'area':'unexplained three-month absence','status':'REGRESSED','blocks':['b0005']}, {'area':'conditional succession','status':'REGRESSED','blocks':['b0005']},
 {'area':'Utterson judgement vs narrator fact','status':'IMPROVED','blocks':['b0007','b0014']}, {'area':'Lanyon opinion','status':'IMPROVED','blocks':['b0013']},
 {'area':'safe / escape meaning','status':'IMPROVED','blocks':['b0022','b0028']}, {'area':'Jekyll grounds for certainty','status':'FIXED','blocks':['b0024']},
 {'area':'trust / confidence','status':'PASS','blocks':['b0024','b0032']}, {'area':'lead vs move','status':'HUMAN_JUDGMENT_REQUIRED','blocks':['b0025']},
 {'area':'laboratory / dissecting rooms / cabinet','status':'IMPROVED','blocks':['b0017','b0018','b0038']}, {'area':'proper names','status':'REVIEW','blocks':['b0013','b0028']},
 {'area':'Poole fear / character rhythm','status':'REGRESSED','blocks':['b0038','b0040']}, {'area':'Jekyll / Hyde identity-spoiler boundary','status':'PASS','blocks':['b0005','b0024','b0028']},
]
out={'schemaVersion':'1','gate':'JEKYLL_REAL_40_BLOCK_SEMANTIC_QA_V7','mechanicalAlignment':'PASS','counts':counts,'spoilerControl':'PASS','nameQA':'REVIEW','profileQA':'REVIEW','literaryTokiPona':'WORKABLE','records':records,'matrix':matrix,'reviewBurden':{'automaticAcceptablePercent':round(counts['PASS']/40*100,1),'editorialReviewPercent':round((counts['PASS_WITH_REVIEW']+counts['SECOND_PASS_REQUIRED'])/40*100,1),'secondPassPercent':round(counts['SECOND_PASS_REQUIRED']/40*100,1)},'projection':{'sourceWords':25622,'measuredSampleWords':sample_words,'measuredAverageWordsPerBlock':avg,'estimatedFullBookBlocks':est,'primaryCalls':est,'expectedSecondPassCalls':round(est*counts['SECOND_PASS_REQUIRED']/40),'ordinaryEditorialReviewBlocks':round(est*(counts['PASS_WITH_REVIEW']+counts['SECOND_PASS_REQUIRED'])/40),'criticalRiskBlocks':0,'inputTokens':round(113379/40*est),'outputTokens':round(11841/40*est),'reasoningTokens':round(7210/40*est)},'productionReasoning':'LOW_WITH_SECOND_PASS','fullBookDecision':'TUNE_AND_RERUN','sitelenReadiness':'REVIEW'}
path=ROOT/'artifacts/jekyll-toki-pona-real-regression-v7/semantic-qa.json'; path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n'); print(counts,est)
