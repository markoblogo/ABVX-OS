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

class BookExportProfileTests(unittest.TestCase):
    def test_book_export_rejects_large_or_mixed_cohorts_before_writing(self):
        import json
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from abvx_harness.process_learning import main
        base = row('book.production')
        cases = [
            [{**base, 'runId': f'synthetic-{i}'} for i in range(21)],
            [base, {**row('book.radar.research'), 'runId': 'synthetic-other'}],
            [base, {**base, 'runId': 'synthetic-other', 'workflowVersion': 'other-v1'}],
        ]
        with TemporaryDirectory() as directory:
            source, target = Path(directory) / 'rows.json', Path(directory) / 'packet.json'
            for rows in cases:
                source.write_text(json.dumps(rows))
                with self.assertRaises(ValueError):
                    main(['export', '--outcomes', str(source), '--packet-id', 'synthetic-profile',
                          '--observed-at', '2026-10-10T01:00:00Z', '--out', str(target)])
                self.assertFalse(target.exists())

    def test_phase_profile_requires_one_real_gate_and_one_comparable_workload(self):
        from abvx_harness.process_learning import build_book_packet
        base = row('book.production')
        packet = build_book_packet([base], 'synthetic-book-profile', '2026-10-10T01:00:00Z')
        self.assertEqual(validate_packet(packet), packet)
        for edit in (
            lambda r: r.update(evidence=[r['evidence'][1]]),
            lambda r: r['evidence'][0].update(ref='stage:market_evidence_review'),
            lambda r: r['evidence'][0].update(ref='stage:format_qa'),
            lambda r: r['evidence'][1].update(sha256='c' * 64),
            lambda r: r['evidence'].append({'ref': 'workload:other', 'sha256': 'd' * 64}),
        ):
            other = copy.deepcopy(base)
            other['runId'] = 'synthetic-other'
            edit(other)
            with self.assertRaises(ValueError):
                build_book_packet([base, other], 'synthetic-book-profile', '2026-10-10T01:00:00Z')
