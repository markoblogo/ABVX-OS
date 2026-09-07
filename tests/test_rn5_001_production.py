import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BOOK=ROOT/'books'/'rn5-001'

class RN5001ProductionTests(unittest.TestCase):
    def test_release_gates(self):
        release=json.loads((BOOK/'production'/'release-manifest.json').read_text())
        self.assertEqual(release['status'],'KDP_READY_AWAITING_HUMAN_COVER_AND_PUBLISHING_GATE')
        self.assertTrue(all(v=='PASS' for k,v in release['gates'].items() if k!='kdp_external_preview'))
        self.assertEqual(release['gates']['kdp_external_preview'],'HUMAN_PENDING')

    def test_content_commercial_version_match(self):
        package=json.loads((BOOK/'commercial'/'kdp-commercial-package.json').read_text())
        self.assertEqual(package['content_version'],package['commercial_package_content_version'])
        self.assertEqual(package['open_content_or_layout_correction_gates'],0)
        self.assertEqual(len(package['keywords']),7)
        self.assertEqual(len(package['categories']),3)

    def test_format_gate(self):
        gate=json.loads((BOOK/'production'/'format-eligibility-gate.json').read_text())
        self.assertEqual(gate['paperback']['decision'],'PRODUCED')
        self.assertEqual(gate['kindle']['decision'],'NOT_JUSTIFIED')

    def test_release_qa_and_artifacts(self):
        qa=json.loads((BOOK/'qa'/'release-qa.json').read_text())
        self.assertEqual(qa['status'],'PASS')
        self.assertEqual(qa['pdf_pages'],57)
        self.assertEqual(qa['kdp_rounded_page_count'],58)
        self.assertEqual(qa['content_version'],'RN5-001-v1.1')
        self.assertTrue(qa['checks']['format_layout_gate'])
        self.assertTrue(qa['checks']['callout_collision_qa'])
        self.assertTrue(qa['checks']['callout_optical_spacing_qa'])
        self.assertEqual(len(qa['callout_measurements']),5)
        self.assertTrue((BOOK/'qa/contact-sheets/callout-spacing-contact-sheet.png').exists())
        comparison=json.loads((BOOK/'production'/'rn5-001-trim-size-comparison.json').read_text())
        self.assertEqual(comparison['selected_trim'],'8x10')
        self.assertFalse(comparison['ambiguous'])
        for path in [ROOT/'output/pdf/solar-proposal-decoder-buyer-decision-system-paperback.pdf',BOOK/'production/solar-proposal-decoder-production-master.pdf',BOOK/'qa/contact-sheets/full-book-contact-sheet.png',BOOK/'qa/contact-sheets/high-risk-contact-sheet.png',BOOK/'qa/contact-sheets/worksheet-contact-sheet.png']:
            self.assertTrue(path.exists(),path)

if __name__=='__main__': unittest.main()
