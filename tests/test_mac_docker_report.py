import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from abvx_harness import mac_docker_report as m


class DockerReportTests(unittest.TestCase):
    def test_fixed_reason_distinguishes_access_and_engine(self):
        self.assertEqual(m.error_kind('permission denied token=private'),'PERMISSION_DENIED')
        self.assertEqual(m.error_kind('Cannot connect to daemon'),'ENGINE_UNREACHABLE')
        self.assertEqual(m.error_kind('unknown secret'),'DOCKER_ACCESS_OR_ENGINE_ERROR')
    def test_api_failure_is_not_complete_and_does_not_leak_error_text(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(m,'STATE',Path(tmp)), patch.object(m.subprocess,'run',return_value=subprocess.CompletedProcess([],1,'','private-token')) as run:
            result=m.collect()
            self.assertEqual(result['status'],'PARTIAL_OR_BLOCKED')
            self.assertNotIn('private-token',str(result))
            self.assertEqual(run.call_count,3)
            for call in run.call_args_list:
                args=call.args[0]
                self.assertNotIn('prune',args)
                self.assertNotIn('run',args)
                self.assertNotIn('start',args)

    def test_readonly_report_has_real_stdout_receipt(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(m,'STATE',Path(tmp)), patch.object(m.subprocess,'run',return_value=subprocess.CompletedProcess([],0,'evidence','')):
            result=m.collect()
            self.assertEqual(result['status'],'COMPLETE')
            self.assertTrue((Path(tmp)/'docker-storage-report.json').exists())
