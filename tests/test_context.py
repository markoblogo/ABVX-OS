import json
import tempfile
import unittest
from pathlib import Path

from abvx_harness.context import (
    _is_admitted_index_path,
    _build_professional_items,
    _filter_owner_fact_candidates_for_request,
    _professional_inventory,
    assemble_context_pack,
    inspect_context_pack,
    load_context_request,
    request_context,
    route_provider_ids,
)
from abvx_harness.harness import ValidationError, validate_repository


ROOT = Path(__file__).resolve().parents[1]


class FakeProvider:
    def __init__(self, provider_id, *, health_ok=True, result=None, reason="unavailable"):
        self.provider_id = provider_id
        self._health_ok = health_ok
        self._result = result
        self._reason = reason

    def capabilities(self):
        return {"provider_id": self.provider_id, "read_only": True}

    def health(self):
        return {"ok": True} if self._health_ok else {"ok": False, "reason": self._reason}

    def retrieve(self, request):
        if isinstance(self._result, Exception):
            raise self._result
        return self._result


class ContextTests(unittest.TestCase):
    def test_repository_documents_validate(self):
        checked = validate_repository(ROOT)
        self.assertIn("context/requests/coqpi-preparation.json", checked)

    def test_route_providers_is_explicit(self):
        request = load_context_request(ROOT, ROOT / "context" / "requests" / "unusual-indices-book.json")
        self.assertEqual(route_provider_ids(request), ["cortexabv", "index-cortex"])

    def test_professional_inventory_and_item_building_are_bounded_and_proof_backed(self):
        request = load_context_request(ROOT, ROOT / "context" / "requests" / "coqpi-preparation.json")
        surfaces = {
            "presence_index": {
                "entities": [
                    {
                        "id": "project:agent-skills",
                        "kind": "project",
                        "name": "Agent Skills",
                        "summary": "AI-native validated workflows for product work.",
                        "canonicalUrl": "https://example.com/agent-skills",
                        "attributes": {
                            "status": "live",
                            "updatedAt": "2026-07-01",
                            "tags": ["ai-dev", "validation", "workflows"],
                            "links": [{"type": "github", "url": "https://github.com/example/agent-skills"}],
                        },
                        "provenance": [{"kind": "content_frontmatter", "path": "content/work/agent-skills.md", "digest": "a" * 64}],
                    },
                    {
                        "id": "publication:future-proof",
                        "kind": "publication",
                        "name": "Future-Proof Productivity",
                        "summary": "AI and workflow design for knowledge work.",
                        "canonicalUrl": "https://example.com/future-proof",
                        "attributes": {
                            "status": "released",
                            "updatedAt": "2026-06-01",
                            "tags": ["AI", "automation", "future of work"],
                            "links": [{"type": "kindle", "url": "https://example.com/future-proof/kindle"}],
                        },
                        "provenance": [{"kind": "content_frontmatter", "path": "content/books/future-proof.md", "digest": "b" * 64}],
                    },
                ],
                "relations": [],
            },
            "project_registry": {
                "entries": [
                    {
                        "id": "repository:github:example/agent-skills",
                        "repository": {"provider": "github", "url": "https://github.com/example/agent-skills"},
                        "project": {"id": "project:agent-skills"},
                        "publicChannels": [{"type": "site", "url": "https://example.com/agent-skills"}],
                    }
                ]
            },
        }
        inventory = _professional_inventory(surfaces)
        self.assertEqual(inventory["capabilities"], "STRONG")
        self.assertEqual(inventory["books_publications"], "STRONG")
        self.assertEqual(inventory["professional_goals"], "MISSING")
        items, sources, proof_assets, gaps, available_more = _build_professional_items(request, surfaces["presence_index"], surfaces["project_registry"])
        self.assertFalse(available_more)
        self.assertGreaterEqual(len(items), 4)
        self.assertEqual(items[0]["category"], "current_focus")
        self.assertEqual(items[0]["privacy_classification"], "PUBLIC")
        self.assertTrue(any(item["title"] == "Agent Skills" for item in items))
        self.assertTrue(any(asset["url"] == "https://github.com/example/agent-skills" for asset in proof_assets))
        self.assertTrue(any("Professional goals/current collaboration preference" in gap for gap in gaps))

    def test_owner_fact_candidates_are_filtered_for_public_requests(self):
        request = load_context_request(ROOT, ROOT / "context" / "requests" / "coqpi-preparation.json")
        public_request = dict(request)
        public_request["privacy_domain"] = "PUBLIC"
        receipt = {
            "candidates": [
                {
                    "memoryId": "mem:personal:goal-current-opportunities",
                    "content": "Public-safe goal.",
                    "metadata": {"privacyClassification": "PUBLIC_SAFE"},
                    "claimEvidence": [],
                },
                {
                    "memoryId": "mem:personal:communication-mode",
                    "content": "Private communication preference.",
                    "metadata": {"privacyClassification": "PERSONAL_PRIVATE"},
                    "claimEvidence": [],
                },
            ]
        }
        public_candidates = _filter_owner_fact_candidates_for_request(public_request, receipt)
        private_candidates = _filter_owner_fact_candidates_for_request(request, receipt)
        self.assertEqual(len(public_candidates), 1)
        self.assertEqual(public_candidates[0]["memoryId"], "mem:personal:goal-current-opportunities")
        self.assertEqual(len(private_candidates), 2)

    def test_small_pack_request_validates(self):
        checked = validate_repository(ROOT)
        self.assertIn("context/requests/coqpi-preparation-small.json", checked)

    def test_mixed_provider_partial_success_is_explicit(self):
        request = load_context_request(ROOT, ROOT / "context" / "requests" / "unusual-indices-book.json")
        providers = {
            "cortexabv": FakeProvider("cortexabv", result={
                "status": "gap",
                "items": [],
                "sources": [],
                "proof_assets": [],
                "known_gaps": ["No personal author knowledge matched this request."],
                "truncated": False,
                "available_more": False,
                "privacy_classification": "PERSONAL_PRIVATE",
                "elapsed_ms": 5,
            }),
            "index-cortex": FakeProvider("index-cortex", result={
                "status": "ok",
                "items": [{
                    "id": "index:1",
                    "provider": "index-cortex",
                    "category": "domain_context",
                    "title": "Index methodology",
                    "summary": "Bounded methodology context.",
                    "excerpt": "Bounded methodology context.",
                    "privacy_classification": "DOMAIN_PRIVATE",
                    "confidence": "HIGH",
                    "provenance": {"url_or_path": "index-platform:docs/cortex-artifact-pipeline.md#0"},
                }],
                "sources": [{"provider": "index-cortex", "url_or_path": "index-platform:docs/cortex-artifact-pipeline.md#0"}],
                "proof_assets": [],
                "known_gaps": [],
                "truncated": False,
                "available_more": False,
                "privacy_classification": "DOMAIN_PRIVATE",
                "elapsed_ms": 10,
            }),
        }
        pack = assemble_context_pack(ROOT, request, providers=providers, generated_at="2026-08-08T00:00:00Z")
        self.assertEqual(len(pack["knowledge_items"]), 1)
        self.assertEqual(pack["providers"][0]["status"], "gap")
        self.assertEqual(pack["providers"][1]["status"], "ok")
        self.assertIn("No personal author knowledge matched this request.", pack["known_gaps"])

    def test_public_request_can_deny_private_provider(self):
        request = load_context_request(ROOT, ROOT / "context" / "requests" / "coqpi-preparation.json")
        request["privacy_domain"] = "PUBLIC"
        providers = {
            "cortexabv": FakeProvider("cortexabv", result={
                "status": "partial",
                "items": [{
                    "id": "cortexabv:public:goal",
                    "provider": "cortexabv",
                    "category": "professional_goal",
                    "title": "Current professional opportunity goals",
                    "summary": "Open to product-lead and consulting opportunities.",
                    "excerpt": "privacy=PUBLIC_SAFE",
                    "privacy_classification": "PUBLIC",
                    "confidence": "HIGH",
                    "provenance": {"source": "tenant-memory-bank"},
                }],
                "sources": [{"provider": "cortexabv", "path": "examples/personal-professional-canonical-facts.v1.json#facts[0]"}],
                "proof_assets": [],
                "known_gaps": ["Private professional-preparation preferences remain admitted in CortexABV but were withheld from PUBLIC projection."],
                "truncated": False,
                "available_more": False,
                "privacy_classification": "PUBLIC",
                "elapsed_ms": 1,
            }),
        }
        pack = assemble_context_pack(ROOT, request, providers=providers, generated_at="2026-08-08T00:00:00Z")
        self.assertEqual(pack["providers"][0]["status"], "partial")
        self.assertEqual(pack["privacy_classification"], "PUBLIC")
        self.assertEqual(pack["operational_context"], [])

    def test_provider_unavailable_becomes_explicit_gap(self):
        request = load_context_request(ROOT, ROOT / "context" / "requests" / "index-pop-methodology.json")
        providers = {
            "index-cortex": FakeProvider("index-cortex", health_ok=False, reason="chunk manifest missing"),
        }
        pack = assemble_context_pack(ROOT, request, providers=providers, generated_at="2026-08-08T00:00:00Z")
        self.assertEqual(pack["providers"][0]["status"], "unavailable")
        self.assertIn("chunk manifest missing", pack["known_gaps"][0])

    def test_no_relevant_knowledge_is_explicit(self):
        request = load_context_request(ROOT, ROOT / "context" / "requests" / "azurmenton-editorial.json")
        providers = {
            "cortexabv": FakeProvider("cortexabv", result={
                "status": "gap",
                "items": [],
                "sources": [],
                "proof_assets": [],
                "known_gaps": ["No CortexABV knowledge matched this request."],
                "truncated": False,
                "available_more": False,
                "privacy_classification": "PROJECT_PRIVATE",
                "elapsed_ms": 1,
            }),
        }
        pack = assemble_context_pack(ROOT, request, providers=providers, generated_at="2026-08-08T00:00:00Z")
        self.assertEqual(pack["providers"][0]["status"], "gap")
        self.assertEqual(pack["confidence"]["level"], "MEDIUM")

    def test_malformed_provider_result_fails_closed_without_silent_success(self):
        request = load_context_request(ROOT, ROOT / "context" / "requests" / "coqpi-preparation.json")
        providers = {
            "cortexabv": FakeProvider("cortexabv", result={"status": "ok"}),
        }
        pack = assemble_context_pack(ROOT, request, providers=providers, generated_at="2026-08-08T00:00:00Z")
        self.assertEqual(pack["providers"][0]["status"], "malformed")
        self.assertEqual(pack["confidence"]["level"], "LOW")

    def test_budget_exceeded_marks_truncated(self):
        request = load_context_request(ROOT, ROOT / "context" / "requests" / "index-pop-methodology.json")
        request["max_items"] = 1
        providers = {
            "index-cortex": FakeProvider("index-cortex", result={
                "status": "partial",
                "items": [
                    {
                        "id": "item-1",
                        "provider": "index-cortex",
                        "category": "domain_context",
                        "title": "One",
                        "summary": "one",
                        "excerpt": "one",
                        "privacy_classification": "DOMAIN_PRIVATE",
                        "confidence": "HIGH",
                        "provenance": {"url_or_path": "index-platform:docs/a.md#0"},
                    },
                    {
                        "id": "item-2",
                        "provider": "index-cortex",
                        "category": "domain_context",
                        "title": "Two",
                        "summary": "two",
                        "excerpt": "two",
                        "privacy_classification": "DOMAIN_PRIVATE",
                        "confidence": "HIGH",
                        "provenance": {"url_or_path": "index-platform:docs/b.md#0"},
                    }
                ],
                "sources": [],
                "proof_assets": [],
                "known_gaps": ["Some matched chunks were omitted by maxEvidence or maxTokens constraints."],
                "truncated": True,
                "available_more": True,
                "privacy_classification": "DOMAIN_PRIVATE",
                "elapsed_ms": 10,
            }),
        }
        pack = assemble_context_pack(ROOT, request, providers=providers, generated_at="2026-08-08T00:00:00Z")
        self.assertTrue(pack["constraints"]["truncated"])
        self.assertTrue(pack["constraints"]["available_more"])

    def test_request_and_inspect_round_trip(self):
        request_path = ROOT / "context" / "requests" / "index-pop-methodology.json"
        providers = {
            "index-cortex": FakeProvider("index-cortex", result={
                "status": "ok",
                "items": [{
                    "id": "index:1",
                    "provider": "index-cortex",
                    "category": "domain_context",
                    "title": "Index methodology",
                    "summary": "Bounded methodology context.",
                    "excerpt": "Bounded methodology context.",
                    "privacy_classification": "DOMAIN_PRIVATE",
                    "confidence": "HIGH",
                    "provenance": {"url_or_path": "index-platform:docs/cortex-artifact-pipeline.md#0"},
                }],
                "sources": [{"provider": "index-cortex", "url_or_path": "index-platform:docs/cortex-artifact-pipeline.md#0"}],
                "proof_assets": [],
                "known_gaps": [],
                "truncated": False,
                "available_more": False,
                "privacy_classification": "DOMAIN_PRIVATE",
                "elapsed_ms": 10,
            }),
        }
        with tempfile.TemporaryDirectory() as temp:
            output_root = Path(temp)
            result = request_context(ROOT, request_path, output_root=output_root, providers=providers, generated_at="2026-08-08T00:00:00Z")
            pack = inspect_context_pack(ROOT, result["pack_id"], output_root=output_root)
            self.assertEqual(pack["pack_id"], "index-pop-methodology")
            self.assertEqual(len(pack["knowledge_items"]), 1)
            evidence = json.loads((output_root / result["evidence_path"]).read_text())
            self.assertEqual(evidence["result"], "PASS")

    def test_index_non_admitted_path_fails_closed(self):
        self.assertFalse(_is_admitted_index_path(".wwebjs_cache/file.json"))
        self.assertFalse(_is_admitted_index_path("tmp/file.json"))
        self.assertFalse(_is_admitted_index_path(".next/server/app.js"))
        self.assertTrue(_is_admitted_index_path("docs/cortex-artifact-pipeline.md"))


if __name__ == "__main__":
    unittest.main()
