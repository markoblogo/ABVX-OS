import json, unittest
from pathlib import Path
from abvx_harness.publishing_gates import validate_product_contract

ROOT=Path(__file__).resolve().parents[1]

class RN5DiscoveryTests(unittest.TestCase):
    def load(self,name):
        return json.loads((ROOT/'book-radar/runs/rn5'/name).read_text())

    def test_broad_and_deep_counts_and_stable_ids(self):
        broad=self.load('broad-opportunities.json')
        deep=self.load('deep-scan.json')
        self.assertEqual(broad['count'],280)
        self.assertEqual(len({x['id'] for x in broad['opportunities']}),280)
        self.assertEqual(deep['count'],24)

    def test_every_requested_language_is_screened(self):
        langs={x['language'] for x in self.load('broad-opportunities.json')['opportunities']}
        self.assertEqual(langs,{'EN','FR','RU','UK','PL','BE'})

    def test_winner_contract_is_complete_and_format_explicit(self):
        contract=self.load('production-contract.json')
        self.assertEqual(validate_product_contract(contract)['status'],'PASS')
        self.assertEqual(contract['status'],'CONDITIONAL_GO_AWAITING_HUMAN_PRODUCT_GATE')
        self.assertEqual(contract['primary_format'],'PAPERBACK')
        self.assertEqual(contract['format_eligibility_status']['PAPERBACK'],'SUPPORTED')

    def test_representative_sample_exists_and_production_did_not_start(self):
        sample=ROOT/'book-radar/runs/rn5/representative-sample/rn5-001-solar-quote-decoder-representative-sample.pdf'
        self.assertTrue(sample.read_bytes().startswith(b'%PDF'))
        self.assertFalse(self.load('preproduction-gates.json')['production_started'])

if __name__=='__main__': unittest.main()
