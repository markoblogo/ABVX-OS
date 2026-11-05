import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from abvx_harness import youtube_framewright_auto as A, framewright_wire as W, youtube as Y
from test_youtube_intelligence import API,CLOCK,packet

class AutoRunTest(unittest.TestCase):
    def test_default_does_not_create_state(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            self.assertEqual(A.before_run(root,Y.config()['channel_id']),[])
            self.assertEqual(A.after_run(root,root/'run')['result'],'disabled')
            self.assertEqual(list(root.iterdir()),[])
    def test_absent_exchange_is_pending_without_new_tree(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);missing=root/'unmounted'/'exchange'
            (root/'framewright-exchange.json').write_text(json.dumps({'version':1,'enabled':True,'exchange_root':str(missing)}))
            self.assertEqual(A.before_run(root,Y.config()['channel_id']),[])
            self.assertEqual(json.loads((root/'framewright-exchange-last.json').read_text())['result'],'pending');self.assertFalse(missing.exists())
    def test_normal_mocked_run_exports_without_new_api_calls(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);exchange=root/'exchange';exchange.mkdir()
            from abvx_harness.youtube_framewright_exchange import configure
            configure(exchange,Y.config()['channel_id']);A.enable(root,exchange)
            api=API();result=Y.run(root,'auto',packet(),api,CLOCK)
            self.assertIn(result['status'],['COMPLETE','PARTIAL_DATA'])
            self.assertEqual(json.loads((root/'framewright-exchange-last.json').read_text())['result'],'exported')
            self.assertEqual(len(list((exchange/'radar/outbox').glob('*.json'))),1)
            self.assertFalse((root/'experiments').exists())
            reference=API();Y.run(root/'disabled','baseline',packet(),reference,CLOCK)
            self.assertEqual(api.invocations,reference.invocations)
    def test_unexpected_optional_hook_failure_preserves_completed_run(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'framewright-exchange.json').write_text('{}')
            with patch.object(A,'after_run',side_effect=RuntimeError('synthetic hook error')):
                result=Y.run(root,'failure',packet(),API(),CLOCK)
            self.assertIn(result['status'],['COMPLETE','PARTIAL_DATA'])
    def test_optional_old_links_do_not_expand_primary_acquisition(self):
        from test_youtube_intelligence import video,VIDEO
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'framewright-exchange.json').write_text('{}');api=API([video(published='2020-01-01T12:00:00Z')])
            with patch.object(A,'before_run',return_value=[VIDEO]),patch.object(A,'after_run',return_value={'result':'pending'}):
                result=Y.run(root,'optional',packet(),api,CLOCK)
            baseline=API([video(published='2020-01-01T12:00:00Z')]);Y.run(root/'baseline','plain',packet(),baseline,CLOCK)
            self.assertEqual(api.invocations,baseline.invocations)
