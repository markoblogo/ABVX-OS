from __future__ import annotations

import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from abvx_harness.__main__ import main
from abvx_harness.content_ops import inspect_content_item, prepare_content_item
from abvx_harness.harness import validate_repository
from abvx_harness.intelligence import execute_intelligence_task, run_content_enrichment


ROOT = Path(__file__).resolve().parents[1]


def _fake_ollama_response(*, model: str, prompt: str, schema: dict, timeout_seconds: int) -> dict:
    return {
        "response": json.dumps(
            {
                "proposed_title": None,
                "seo_title": "Marmite Oatmeal",
                "meta_description": "A simple savoury oatmeal with Marmite, butter and rolled oats.",
                "tags": ["marmite", "breakfast", "cookbook"],
                "topics": ["savory breakfast", "simple cooking", "cookbook notes"],
                "primary_entities": ["Marmite", "Anton BV"],
                "machine_summary": "A short note about savory oatmeal made with Marmite, butter and rolled oats.",
                "internal_link_suggestions": ["/writing", "/books"],
            }
        ),
        "prompt_eval_count": 123,
        "eval_count": 56,
        "total_duration": 987654321,
        "_elapsed_ms": 42,
    }


def _fake_openai_response(*, model: str, prompt: str, schema: dict, timeout_seconds: int, max_output_tokens: int, reasoning_effort: str) -> dict:
    return {
        "status": "completed",
        "output": [
            {"type": "reasoning", "content": []},
            {
                "type": "message",
                "content": [
                    {
                        "type": "output_text",
                        "text": json.dumps(
                            {
                                "proposed_title": None,
                                "seo_title": "Marmite Oatmeal",
                                "meta_description": "A simple savoury oatmeal with Marmite, butter and rolled oats.",
                                "tags": ["marmite", "breakfast", "cookbook"],
                                "topics": ["savory breakfast", "simple cooking", "cookbook notes"],
                                "primary_entities": ["Marmite", "Anton BV"],
                                "machine_summary": "A short note about savory oatmeal made with Marmite, butter and rolled oats.",
                                "internal_link_suggestions": ["/writing", "/books"],
                            }
                        ),
                    }
                ],
            },
        ],
        "usage": {
            "input_tokens": 400,
            "output_tokens": 200,
            "total_tokens": 600,
        },
        "_elapsed_ms": 64,
    }


class IntelligenceTests(unittest.TestCase):
    def _root(self) -> Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        for directory in ("schemas", "content", "events", "evidence", "registries"):
            shutil.copytree(ROOT / directory, root / directory)
        return root

    def test_content_enrichment_task_returns_validated_structured_output(self):
        root = self._root()
        fixture = json.loads((root / "content" / "fixtures" / "content-publish-005-abvx-marmite-oatmeal.json").read_text())
        with patch("abvx_harness.intelligence._select_local_model", return_value="qwen3.5:4b"), patch("abvx_harness.intelligence._run_ollama_generate", side_effect=_fake_ollama_response):
            result = execute_intelligence_task(
                root,
                task_id="content-enrichment",
                provider_override="ollama.local",
                context={
                    "content_id": fixture["id"],
                    "project": fixture["project"],
                    "surface": fixture["surface"],
                    "kind": fixture["kind"],
                    "language": "English",
                    "title": fixture["title"],
                    "summary": fixture["summary"],
                    "body_lines": fixture["payload"]["body_lines"],
                    "source_refs": fixture["payload"]["source_refs"],
                    "locales": fixture["locales"],
                    "suggest_title_if_missing": False,
                    "allowed_internal_links": ["/writing", "/books", "/about", "/work"],
                    "deterministic_slug": fixture["slug"],
                    "hreflang": {"en": "/writing/marmite-oatmeal"},
                },
                runtime_stem=fixture["id"],
            )
        self.assertEqual(result["status"], "SUCCEEDED")
        self.assertEqual(result["execution_tier"], "LOCAL_LLM")
        self.assertEqual(result["output"]["internal_link_suggestions"], ["/writing", "/books"])
        self.assertTrue((root / "evidence" / "intelligence" / f"{fixture['id']}.runtime.json").is_file())

    def test_content_prepare_with_local_llm_records_runtime_artifacts(self):
        root = self._root()
        with patch("abvx_harness.intelligence._select_local_model", return_value="qwen3.5:4b"), patch("abvx_harness.intelligence._run_ollama_generate", side_effect=_fake_ollama_response):
            item = prepare_content_item(root, "content/fixtures/content-publish-005-abvx-marmite-oatmeal.json", intelligence_mode="local_llm")
        self.assertEqual(item["status"], "PREPARED")
        self.assertGreaterEqual(len(item["artifact_refs"]), 2)
        self.assertEqual(inspect_content_item(root, item["id"])["enrichment"]["tags"], ["marmite", "breakfast", "cookbook"])

    def test_cheap_api_provider_returns_validated_structured_output(self):
        root = self._root()
        fixture = json.loads((root / "content" / "fixtures" / "content-publish-005-abvx-marmite-oatmeal.json").read_text())
        with patch("abvx_harness.intelligence._run_openai_responses", side_effect=_fake_openai_response):
            result = execute_intelligence_task(
                root,
                task_id="content-enrichment",
                provider_override="cheap.api",
                context={
                    "content_id": fixture["id"],
                    "project": fixture["project"],
                    "surface": fixture["surface"],
                    "kind": fixture["kind"],
                    "language": "English",
                    "title": fixture["title"],
                    "summary": fixture["summary"],
                    "body_lines": fixture["payload"]["body_lines"],
                    "source_refs": fixture["payload"]["source_refs"],
                    "locales": fixture["locales"],
                    "suggest_title_if_missing": False,
                    "allowed_internal_links": ["/writing", "/books", "/about", "/work"],
                    "deterministic_slug": fixture["slug"],
                    "hreflang": {"en": "/writing/marmite-oatmeal"},
                },
                runtime_stem="cheap-api-test",
            )
        self.assertEqual(result["status"], "SUCCEEDED")
        self.assertEqual(result["provider"], "cheap.api")
        self.assertEqual(result["model"], "gpt-5.6-luna")
        self.assertEqual(result["execution_tier"], "CHEAP_API")
        self.assertLess(result["usage"]["estimated_cost_usd"], 0.01)

    def test_content_prepare_blocks_when_local_llm_fails_closed(self):
        root = self._root()
        with patch("abvx_harness.intelligence._select_local_model", return_value="qwen3.5:4b"), patch("abvx_harness.intelligence._run_ollama_generate", side_effect=TimeoutError("timed out")):
            item = prepare_content_item(root, "content/fixtures/content-publish-005-abvx-marmite-oatmeal.json", intelligence_mode="local_llm")
        self.assertEqual(item["status"], "BLOCKED")
        self.assertTrue(any("internal intelligence failed closed" in blocker for blocker in item["validation"]["blockers"]))

    def test_cli_intelligence_run_outputs_json(self):
        root = self._root()
        output = io.StringIO()
        with patch("abvx_harness.intelligence._select_local_model", return_value="qwen3.5:4b"), patch("abvx_harness.intelligence._run_ollama_generate", side_effect=_fake_ollama_response), contextlib.redirect_stdout(output):
            exit_code = main(["intelligence", "run", "--task", "content-enrichment", "--file", "content/fixtures/content-publish-005-abvx-marmite-oatmeal.json", "--provider", "ollama.local", "--json"], root=root)
        self.assertEqual(exit_code, 0)
        self.assertEqual(json.loads(output.getvalue())["status"], "SUCCEEDED")

    def test_repository_validation_covers_intelligence_registry_and_runtime_schema(self):
        checked = validate_repository(ROOT)
        self.assertIn("registries/intelligence-tasks.json", checked)

    def test_run_content_enrichment_escalates_when_model_unavailable(self):
        root = self._root()
        with patch("abvx_harness.intelligence._select_local_model", return_value=None):
            result = run_content_enrichment(root, "content/fixtures/content-publish-005-abvx-marmite-oatmeal.json", provider="ollama.local")
        self.assertEqual(result["status"], "ESCALATION_REQUIRED")
        self.assertEqual(result["execution_tier"], "CODEX_ESCALATION")


if __name__ == "__main__":
    unittest.main()
