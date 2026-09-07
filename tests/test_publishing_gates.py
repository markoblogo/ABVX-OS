import json, tempfile, unittest
from pathlib import Path
from abvx_harness.publishing_gates import validate_product_contract, representative_product_requirement, record_human_product_gate, release_authorization

GOOD={"buyer":"learner","buyer_job":"learn a system","prior_knowledge":"none or adjacent system","confusions":["transfer traps"],"better_or_faster":"recognize and act","paid_value":"curated comparisons","specific_advantage":"two-system map","intentionally_not":"legal advice","product_class":"COMPARISON_GUIDE","dataset_driven":True,"raw_data_transformation":{"raw_source":"two official rule sets","transformation":"comparison graph and explanations","buyer_value":"safe transfer and faster learning"}}

class PublishingGateTests(unittest.TestCase):
    def test_dataset_product_requires_declared_transformation(self):
        bad={**GOOD};bad.pop("raw_data_transformation")
        self.assertEqual(validate_product_contract(bad)["status"],"FAIL")
        self.assertEqual(validate_product_contract(GOOD)["status"],"PASS")
    def test_representative_sample_can_require_human_gate(self):
        r=representative_product_requirement(GOOD,["layout_dependent","prior_knowledge_dependent"])
        self.assertTrue(r["required"]);self.assertTrue(r["human_product_gate_required"])
    def test_human_product_gate_persists(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"state.json";path.write_text(json.dumps(record_human_product_gate({},result="FAIL",finding="slide-like",reviewed_at="2026-09-07")))
            saved=json.loads(path.read_text());self.assertEqual(saved["human_product_gate_history"][0]["result"],"FAIL");self.assertEqual(saved["full_production"],"BLOCKED")
    def test_product_quality_blocks_independently(self):
        gates={k:"PASS" for k in ("market","product_thesis","representative_product","factual_source","language","editorial","product_quality","technical","toc_navigation")};gates["kdp_external_preview"]="HUMAN_PENDING";gates["product_quality"]="FAIL"
        self.assertEqual(release_authorization(gates)["status"],"PRODUCTION_BLOCKED")
    def test_technical_pass_cannot_overwrite_product_fail(self):
        gates={"market":"PASS","product_thesis":"PASS","representative_product":"PASS","factual_source":"PASS","language":"PASS","editorial":"PASS","product_quality":"FAIL","technical":"PASS","toc_navigation":"PASS","kdp_external_preview":"HUMAN_PENDING"}
        self.assertEqual(release_authorization(gates)["failures"],[{"gate":"product_quality","state":"FAIL"}])
    def test_release_requires_every_mandatory_gate(self):
        self.assertEqual(release_authorization({"technical":"PASS"})["status"],"PRODUCTION_BLOCKED")

if __name__=='__main__': unittest.main()
