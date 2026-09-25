import importlib.util, io, json, os, tempfile, unittest, urllib.error
from pathlib import Path
from contextlib import redirect_stderr
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('full',ROOT/'scripts/run_jekyll_full_translation_v1.py'); full=importlib.util.module_from_spec(spec); spec.loader.exec_module(full)
class FullJekyllRunnerTests(unittest.TestCase):
 def test_canonical_source_and_segmentation(self):
  text,_=full.source_hash_check(); blocks,chapters=full.segment(text); self.assertEqual(len(text.split()),25622); self.assertEqual(len(chapters),10); self.assertEqual(len(blocks),462); self.assertEqual(len({b['blockId'] for b in blocks}),462)
 def test_dry_run_no_api(self):
  with tempfile.TemporaryDirectory(): self.assertEqual(full.main(['--dry-run']),0)
 def test_insufficient_quota_is_persistent_and_safe(self):
  exc=urllib.error.HTTPError('https://api.openai.com/v1/responses',429,'Too Many Requests',{},io.BytesIO(b'{"error":{"type":"insufficient_quota","code":"insufficient_quota","message":"private detail"}}'))
  result=full.classify_provider_error(exc)
  self.assertEqual(result['category'],'PERSISTENT_QUOTA')
  self.assertTrue(result['hardStop'])
  self.assertEqual(result['metadata'],{'httpStatus':429,'errorType':'insufficient_quota','errorCode':'insufficient_quota'})
  self.assertNotIn('private detail',str(result))
  exc.close()
 def test_rate_limit_429_is_distinct_and_transient(self):
  exc=urllib.error.HTTPError('https://api.openai.com/v1/responses',429,'Too Many Requests',{},io.BytesIO(b'{"error":{"type":"rate_limit_error","code":"rate_limit_exceeded"}}'))
  result=full.classify_provider_error(exc)
  self.assertEqual(result['category'],'TRANSIENT_RATE_LIMIT')
  self.assertFalse(result['hardStop'])
  self.assertTrue(result['retryable'])
  exc.close()
 def test_unclassified_429_fails_closed(self):
  exc=urllib.error.HTTPError('https://api.openai.com/v1/responses',429,'Too Many Requests',{},io.BytesIO(b'{"error":{"message":"not retained"}}'))
  result=full.classify_provider_error(exc)
  self.assertEqual(result['category'],'PERSISTENT_UNKNOWN_429')
  self.assertTrue(result['hardStop'])
  exc.close()
 def test_auth_and_model_errors_hard_stop(self):
  auth=urllib.error.HTTPError('https://api.openai.com/v1/responses',401,'Unauthorized',{},io.BytesIO(b'{"error":{"type":"authentication_error","code":"invalid_api_key"}}'))
  model=urllib.error.HTTPError('https://api.openai.com/v1/responses',404,'Not Found',{},io.BytesIO(b'{"error":{"type":"invalid_request_error","code":"model_not_found"}}'))
  self.assertTrue(full.classify_provider_error(auth)['hardStop'])
  self.assertEqual(full.classify_provider_error(model)['category'],'PERSISTENT_MODEL')
  auth.close(); model.close()
 def test_persistent_quota_stops_before_later_blocks(self):
  exc=urllib.error.HTTPError('https://api.openai.com/v1/responses',429,'Too Many Requests',{},io.BytesIO(b'{"error":{"type":"insufficient_quota","code":"insufficient_quota"}}'))
  with tempfile.TemporaryDirectory() as temp, patch.object(full,'OUT',Path(temp)), patch.object(full.v7,'call',side_effect=exc) as call, patch.dict(os.environ,{'OPENAI_API_KEY':'test-only'}):
   self.assertEqual(full.main(['--max-calls','462','--max-input-tokens','2000000']),2)
   call.assert_called_once()
   manifest=json.loads((Path(temp)/'run-manifest.json').read_text())
   failure=json.loads((Path(temp)/'failures.json').read_text())
   self.assertEqual(manifest['unattempted'],461)
   self.assertEqual(manifest['stopReason'],'PERSISTENT_QUOTA')
   self.assertEqual(failure[0]['attempts'][0]['errorMetadata']['errorCode'],'insufficient_quota')
   self.assertNotIn('message',failure[0]['attempts'][0])
  exc.close()
 def test_cost_preflight_requires_call_and_usage_budgets(self):
  with tempfile.TemporaryDirectory() as temp, patch.object(full,'OUT',Path(temp)), patch.object(full.v7,'call') as call, patch.dict(os.environ,{'OPENAI_API_KEY':'test-only'}), redirect_stderr(io.StringIO()) as err:
   self.assertEqual(full.main(['--max-calls','1']),2)
   call.assert_not_called()
   self.assertIn('COST_PREFLIGHT_REQUIRED',err.getvalue())
 def test_call_and_usage_budgets_stop_the_run(self):
  payload={'status':'completed','incomplete_details':None,'id':'resp-test','output':[{'type':'message','content':[{'type':'output_text','text':'TRANSLATION: toki pona\nNOTES: NONE'}]}],'usage':{'input_tokens':10,'input_tokens_details':{'cached_tokens':0,'cache_write_tokens':10},'output_tokens':8,'output_tokens_details':{'reasoning_tokens':2}}}
  with tempfile.TemporaryDirectory() as temp, patch.object(full,'OUT',Path(temp)), patch.object(full.v7,'call',return_value=payload) as call, patch.dict(os.environ,{'OPENAI_API_KEY':'test-only'}):
   self.assertEqual(full.main(['--max-calls','1','--max-input-tokens','100','--max-output-tokens-total','100']),2)
   call.assert_called_once()
   manifest=json.loads((Path(temp)/'run-manifest.json').read_text())
   summary=json.loads((Path(temp)/'usage-summary.json').read_text())
   checkpoint=json.loads((Path(temp)/'blocks'/'jekyll-full-v1__chapter-01__block-0001.json').read_text())
   self.assertEqual(manifest['completed'],1)
   self.assertEqual(manifest['unattempted'],461)
   self.assertEqual(manifest['stopReason'],'MAX_CALLS_BUDGET_REACHED')
   self.assertEqual(summary['inputTokens'],10)
   self.assertEqual(summary['cacheWriteInputTokens'],10)
   self.assertEqual(summary['reasoningTokens'],2)
   self.assertEqual(checkpoint['model'],'gpt-5.6-sol')
   self.assertEqual(checkpoint['promptVersion'],'jekyll-full-v1-prompt-v1')
   self.assertEqual(len(checkpoint['promptHash']),64)
   self.assertEqual(checkpoint['configuration']['reasoning'],'low')
 def test_input_token_budget_stops_after_observed_usage(self):
  payload={'status':'completed','incomplete_details':None,'id':'resp-test','output':[{'type':'message','content':[{'type':'output_text','text':'TRANSLATION: toki pona\nNOTES: NONE'}]}],'usage':{'input_tokens':10,'input_tokens_details':{'cached_tokens':0,'cache_write_tokens':10},'output_tokens':8,'output_tokens_details':{'reasoning_tokens':2}}}
  with tempfile.TemporaryDirectory() as temp, patch.object(full,'OUT',Path(temp)), patch.object(full.v7,'call',return_value=payload) as call, patch.dict(os.environ,{'OPENAI_API_KEY':'test-only'}):
   self.assertEqual(full.main(['--max-calls','5','--max-input-tokens','10']),2)
   call.assert_called_once()
   manifest=json.loads((Path(temp)/'run-manifest.json').read_text())
   self.assertEqual(manifest['completed'],1)
   self.assertEqual(manifest['unattempted'],461)
   self.assertEqual(manifest['stopReason'],'MAX_INPUT_TOKENS_BUDGET_REACHED')
if __name__=='__main__': unittest.main()
