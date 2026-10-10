"""Prepared book rules reuse the released outcome/privacy boundary."""
import copy, unittest
from abvx_harness.process_learning import build_packet, validate_packet

def row(workflow):
 return {'schemaVersion':1,'kind':'AbvxOsProcessOutcome','tenant':'abvx-os','runId':'synthetic-book-phase','workflowId':workflow,'workflowVersion':'book-phase-v1','origin':'SYNTHETIC','startedAt':'2026-10-10T00:00:00Z','completedAt':'2026-10-10T00:00:10Z','status':'FAIL','elapsedSeconds':10,'ownerMinutes':'UNKNOWN','reworkCount':1,'qualityGate':'UNKNOWN','safetyGate':'PASS','evidence':[{'ref':'stage:editorial_review','sha256':'a'*64},{'ref':'workload:book-phase-profile','sha256':'b'*64}]}

class BookExchangeRulesTests(unittest.TestCase):
 def test_book_workflows_preserve_failed_and_unknown_observations(self):
  for workflow in ('book.radar.research','book.production'):
   packet=build_packet([row(workflow)],'synthetic-phase-batch','2026-10-10T01:00:00Z');validate_packet(packet)
   self.assertEqual(packet['payload']['outcomes'][0]['qualityGate'],'UNKNOWN');self.assertEqual(packet['payload']['outcomes'][0]['ownerMinutes'],'UNKNOWN')
   self.assertEqual(packet['returnAuthority'],'none');self.assertEqual(packet['permittedUse'],['private_context'])
 def test_business_data_and_manuscripts_cannot_enter_os_book_envelope(self):
  packet=build_packet([row('book.production')],'synthetic-phase-batch','2026-10-10T01:00:00Z')
  for edit in (lambda p:p['payload']['outcomes'][0].update(manuscript='synthetic private text'),lambda p:p['payload'].update(tenant='business-cortex-supervision'),lambda p:p.update(dataKind='cortex_business_evaluation_summary')):
   changed=copy.deepcopy(packet);edit(changed)
   with self.assertRaises(ValueError):validate_packet(changed)
