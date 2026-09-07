import json, tempfile, unittest
from pathlib import Path
from abvx_harness.publishing_gates import validate_product_contract, validate_commercial_package, representative_product_requirement, record_human_product_gate, release_authorization

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
        gates={k:"PASS" for k in ("market","product_thesis","representative_product","factual_source","language","editorial","product_quality","technical","toc_navigation","commercial_package")};gates["kdp_external_preview"]="HUMAN_PENDING";gates["product_quality"]="FAIL"
        self.assertEqual(release_authorization(gates)["status"],"PRODUCTION_BLOCKED")
    def test_technical_pass_cannot_overwrite_product_fail(self):
        gates={"market":"PASS","product_thesis":"PASS","representative_product":"PASS","factual_source":"PASS","language":"PASS","editorial":"PASS","product_quality":"FAIL","technical":"PASS","toc_navigation":"PASS","commercial_package":"PASS","kdp_external_preview":"HUMAN_PENDING"}
        self.assertEqual(release_authorization(gates)["failures"],[{"gate":"product_quality","state":"FAIL"}])
    def test_release_requires_every_mandatory_gate(self):
        self.assertEqual(release_authorization({"technical":"PASS"})["status"],"PRODUCTION_BLOCKED")

    def test_commercial_package_requires_copy_paste_complete_metadata(self):
        package={"title":"T","subtitle":"S","author":"A","description":"D","keywords":[str(i) for i in range(7)],"categories":["a","b","c"],"paperback_price":18.9,"kindle_price":7.99,"primary_marketplace":"Amazon.fr","format_settings":{"paperback":{},"kindle":{}},"cover_brief":"brief.md","content_version":"V2.1","commercial_package_content_version":"V2.1","open_content_or_layout_correction_gates":0}
        self.assertEqual(validate_commercial_package(package)["status"],"PASS")
        package.pop("paperback_price")
        self.assertEqual(validate_commercial_package(package)["status"],"FAIL")

    def test_commercial_package_cannot_finalize_against_stale_content(self):
        package={"title":"T","subtitle":"S","author":"A","description":"D","keywords":[str(i) for i in range(7)],"categories":["a","b","c"],"paperback_price":18.9,"kindle_price":7.99,"primary_marketplace":"Amazon.fr","format_settings":{"paperback":{},"kindle":{}},"cover_brief":"brief.md","content_version":"V2.1","commercial_package_content_version":"V2","open_content_or_layout_correction_gates":1}
        result=validate_commercial_package(package)
        self.assertEqual(result["status"],"FAIL")
        self.assertIn("content_version.match",result["missing"])
        self.assertIn("open_content_or_layout_correction_gates.zero",result["missing"])

    def test_commercial_false_pass_blocks_kdp_ready(self):
        gates={k:"PASS" for k in ("market","product_thesis","representative_product","factual_source","language","editorial","product_quality","technical","toc_navigation")}
        gates["kdp_external_preview"]="HUMAN_PENDING"
        result=release_authorization(gates)
        self.assertIn({"gate":"commercial_package","state":"MISSING"},result["failures"])

if __name__=='__main__': unittest.main()
