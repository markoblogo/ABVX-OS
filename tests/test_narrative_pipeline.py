import json
import tempfile
import unittest
from pathlib import Path

from abvx_harness.narrative_pipeline import (
    NarrativeRunner, PipelineConfig, alignment_report, knowledge_spoiler_report,
    LocalModelNarrativeProvider, build_translation_prompt, public_request_allowed, segment_source, validate_names,
)


ROOT = Path(__file__).resolve().parents[1]


class NarrativePipelineTests(unittest.TestCase):
    def test_public_limit_is_preserved_and_internal_is_batched(self):
        self.assertTrue(public_request_allowed("x" * 500))
        self.assertFalse(public_request_allowed("x" * 501))
        self.assertEqual(PipelineConfig(mode="INTERNAL_BOOK_PIPELINE").max_block_chars, 1800)
        with self.assertRaises(ValueError):
            PipelineConfig(mode="PUBLIC", max_block_chars=501)

    def test_stable_blocks_and_resume_only_retries_failed_block(self):
        blocks = segment_source("## A\n\nOne paragraph.\n\nTwo paragraph.", "jekyll")
        with tempfile.TemporaryDirectory() as d:
            calls = []
            runner = NarrativeRunner(d, PipelineConfig(max_retries=0))
            provider = lambda block, context: calls.append(block.block_id) or "sona"
            first = runner.run(blocks, provider, fail_block_ids={blocks[1].block_id})
            self.assertEqual(first[0].status, "SUCCESS")
            self.assertEqual(first[1].status, "FAILED")
            before = len(calls)
            second = runner.run(blocks, provider, fail_block_ids=set())
            self.assertEqual(len(calls), before + 1)
            self.assertEqual(second[1].status, "SUCCESS")
            self.assertEqual([b.block_id for b in first], [b.block_id for b in second])
            manifest = json.loads((Path(d) / "run-manifest.json").read_text())
            self.assertEqual(manifest["sourceBlockCount"], len(blocks))

    def test_alignment_and_names_fail_closed(self):
        blocks = segment_source("A paragraph.", "book")
        from abvx_harness.narrative_pipeline import TranslationBlock
        self.assertEqual(alignment_report(blocks, [TranslationBlock(blocks[0].block_id, blocks[0].source_hash, "sona")])["status"], "PASS")
        ledger = json.loads((ROOT / "JEKYLL_ENTITY_LEDGER_V1.json").read_text())
        registry = {e["id"]: e for e in ledger["entities"]}
        self.assertEqual(validate_names("jan Jekil jan Hata", registry)["status"], "PASS")
        self.assertEqual(validate_names("jan Jekil jan Xata", registry)["status"], "FAIL")

    def test_knowledge_spoiler_is_reviewable_not_overclaimed(self):
        blocks = segment_source("He thought the door was strange.", "book")
        from abvx_harness.narrative_pipeline import TranslationBlock
        report = knowledge_spoiler_report(blocks, [TranslationBlock(blocks[0].block_id, blocks[0].source_hash, "ona li pilin")])
        self.assertEqual(report["status"], "REVIEW")

    def test_provider_prompt_is_block_bounded_and_does_not_use_public_bypass(self):
        block = segment_source("A question?", "book")[0]
        prompt = build_translation_prompt(block, previous="prior", next_text="next")
        self.assertIn("TARGET BLOCK [book:section-001:b0001]", prompt)
        self.assertIn("question into statement", prompt)
        self.assertEqual(LocalModelNarrativeProvider(url="http://127.0.0.1:1").model, "occ-ai/OCC-RAG-0.6B")


if __name__ == "__main__":
    unittest.main()
