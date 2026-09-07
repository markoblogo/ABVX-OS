import json, tempfile, unittest
from pathlib import Path
from abvx_harness.publishing_gates import audit_no_bleed_objects, assess_format_eligibility, validate_product_contract, validate_commercial_package, validate_callout_layout, validate_format_layout, representative_product_requirement, record_human_product_gate, release_authorization

GOOD={"buyer":"learner","buyer_job":"learn a system","prior_knowledge":"none or adjacent system","confusions":["transfer traps"],"better_or_faster":"recognize and act","paid_value":"curated comparisons","specific_advantage":"two-system map","intentionally_not":"legal advice","primary_format":"PAPERBACK","secondary_formats":["KINDLE"],"format_eligibility_status":{"PAPERBACK":"SUPPORTED","KINDLE":"SUPPORTED"},"format_specific_commercial_role":{"PAPERBACK":"PRIMARY","KINDLE":"SECONDARY"},"product_class":"COMPARISON_GUIDE","dataset_driven":True,"raw_data_transformation":{"raw_source":"two official rule sets","transformation":"comparison graph and explanations","buyer_value":"safe transfer and faster learning"}}

class PublishingGateTests(unittest.TestCase):
    def test_format_eligibility_is_versioned_and_fails_closed(self):
        records=[
            {"language":"UK","format":"PAPERBACK","platform":"KDP","marketplace":"ALL","status":"SUPPORTED","checked_at":"2026-09-07","confidence":"HIGH"},
            {"language":"UK","format":"KINDLE","platform":"KDP","marketplace":"ALL","status":"UNSUPPORTED","checked_at":"2026-09-07","confidence":"HIGH"},
        ]
        result=assess_format_eligibility(language="UK",marketplace="Amazon.fr",formats=["PAPERBACK","KINDLE","HARDCOVER"],support_records=records)
        self.assertEqual(result["formats"]["PAPERBACK"]["status"],"SUPPORTED")
        self.assertFalse(result["formats"]["KINDLE"]["production_allowed"])
        self.assertEqual(result["formats"]["HARDCOVER"]["status"],"UNVERIFIED")

    def test_contract_requires_explicit_format_plan(self):
        bad={**GOOD};bad.pop("format_eligibility_status")
        result=validate_product_contract(bad)
        self.assertEqual(result["status"],"FAIL")
        self.assertIn("format_eligibility_status",result["missing"])

    def test_no_bleed_full_page_object_reproduces_external_margin_failure(self):
        result=audit_no_bleed_objects([{"id":"background","bbox":[0,0,612,792]}],page_width=612,page_height=792,safe_inset=18)
        self.assertEqual(result["status"],"FAIL")
        self.assertEqual(result["failures"][0]["id"],"background")

    def test_no_bleed_inset_decoration_passes(self):
        result=audit_no_bleed_objects([{"id":"opening-panel","bbox":[54,54,558,738]}],page_width=612,page_height=792,safe_inset=18)
        self.assertEqual(result["status"],"PASS")

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

    def test_commercial_package_only_requires_prices_for_planned_supported_formats(self):
        package={"title":"T","subtitle":"S","author":"A","description":"D","keywords":[str(i) for i in range(7)],"categories":["a","b","c"],"paperback_price":18.9,"primary_marketplace":"Amazon.fr","format_settings":{"paperback":{}},"cover_brief":"brief.md","content_version":"V2.1.1","commercial_package_content_version":"V2.1.1","open_content_or_layout_correction_gates":0,"planned_formats":["PAPERBACK"],"format_eligibility_status":{"PAPERBACK":"SUPPORTED","KINDLE":"UNSUPPORTED"}}
        self.assertEqual(validate_commercial_package(package)["status"],"PASS")
        package["planned_formats"].append("KINDLE")
        result=validate_commercial_package(package)
        self.assertEqual(result["status"],"FAIL")
        self.assertIn("format_eligibility_status.KINDLE.SUPPORTED",result["missing"])

    def test_commercial_false_pass_blocks_kdp_ready(self):
        gates={k:"PASS" for k in ("market","product_thesis","representative_product","factual_source","language","editorial","product_quality","technical","toc_navigation")}
        gates["kdp_external_preview"]="HUMAN_PENDING"
        result=release_authorization(gates)
        self.assertIn({"gate":"commercial_package","state":"MISSING"},result["failures"])

    def test_format_layout_gate_requires_real_trim_evidence_and_writable_forms(self):
        good={"trim_candidates":[{"trim":"7x10"},{"trim":"8x10"}],"selected_trim":"8x10","callout_layout":{"space_before_pt":18,"space_after_body_pt":18,"space_after_heading_pt":22,"internal_padding_pt":12,"overlap_count":0,"measured":[{"id":"A","before_gap_pt":18,"after_gap_pt":22,"following_type":"HEADING"}]},"form_layout":{"short_row_min_pt":28,"long_row_min_pt":48,"three_column_answer_width_in":1.75,"editorial_asymmetry":True},"chapter_end_whitespace_signal_pages":[]}
        self.assertEqual(validate_format_layout(good)["status"],"PASS")
        bad={**good,"callout_layout":{"space_before_pt":2,"space_after_body_pt":2,"space_after_heading_pt":2,"internal_padding_pt":2,"overlap_count":1,"measured":[{"id":"A","before_gap_pt":2,"after_gap_pt":2,"following_type":"BODY"}]},"chapter_end_whitespace_signal_pages":[11]}
        result=validate_format_layout(bad)
        self.assertEqual(result["status"],"FAIL")
        self.assertIn("chapter_end_whitespace_signal_pages.empty",result["failures"])

    def test_callout_collision_and_optical_spacing_are_independent(self):
        record={"space_before_pt":4,"space_after_body_pt":4,"space_after_heading_pt":4,"internal_padding_pt":12,"overlap_count":0,"measured":[{"id":"Q","before_gap_pt":4,"after_gap_pt":4,"following_type":"BODY"}]}
        result=validate_callout_layout(record)
        self.assertEqual(result["collision"]["status"],"PASS")
        self.assertEqual(result["optical_spacing"]["status"],"FAIL")

if __name__=='__main__': unittest.main()
