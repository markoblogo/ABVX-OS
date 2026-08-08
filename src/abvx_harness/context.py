from __future__ import annotations

import json
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Protocol

from .harness import ValidationError, load_json, now_iso, validate


CORTEX_ABV_RUNTIME = Path("/Volumes/Work/Work/ABVXsite/cortex-abv/private-runtime")
INDEX_CORTEX_ROOT = Path("/Volumes/Work/Work/index")

INDEX_APPROVED_TOP_LEVEL_DIRS = {
    "docs",
    "fixtures",
    "prisma",
    "public",
    "scripts",
    "services",
    "src",
    "tests",
}

INDEX_APPROVED_TOP_LEVEL_FILES = {
    "AGENTS.md",
    "README.md",
    "components.json",
    "eslint.config.mjs",
    "next-env.d.ts",
    "next.config.test.ts",
    "next.config.ts",
    "package-lock.json",
    "package.json",
    "playwright.config.ts",
    "postcss.config.mjs",
    "prisma.config.ts",
    "railway.json",
    "tailwind.config.ts",
    "tsconfig.json",
    "vercel.json",
    "vitest.config.ts",
}


class ContextProvider(Protocol):
    provider_id: str

    def capabilities(self) -> dict[str, Any]: ...

    def health(self) -> dict[str, Any]: ...

    def retrieve(self, request: dict[str, Any]) -> dict[str, Any]: ...


def load_context_request(root: Path, request_path: Path) -> dict[str, Any]:
    value = load_json(request_path)
    schema_path = root / "schemas" / "context_request.schema.json"
    validate(value, load_json(schema_path), schema_path=schema_path, root=root, location=str(request_path))
    return value


def inspect_context_pack(root: Path, pack_id: str, *, output_root: Path | None = None) -> dict[str, Any]:
    pack_path = (output_root or root) / "evidence" / "context-packs" / f"{pack_id}.json"
    if not pack_path.is_file():
        raise ValidationError(f"unknown context pack: {pack_id}")
    value = load_json(pack_path)
    schema_path = root / "schemas" / "context_pack.schema.json"
    validate(value, load_json(schema_path), schema_path=schema_path, root=root, location=str(pack_path))
    return value


def request_context(
    root: Path,
    request_path: Path,
    *,
    output_root: Path | None = None,
    providers: dict[str, ContextProvider] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    output_root = output_root or root
    request = load_context_request(root, request_path)
    pack = assemble_context_pack(root, request, providers=providers, generated_at=generated_at)
    pack_path = output_root / "evidence" / "context-packs" / f"{pack['pack_id']}.json"
    pack_path.parent.mkdir(parents=True, exist_ok=True)
    pack_path.write_text(json.dumps(pack, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    evidence = build_context_evidence(root, request, pack, request_path=request_path, pack_path=pack_path)
    evidence_path = output_root / "evidence" / "integration" / "cortex-integration-002" / f"{request['request_id']}.evidence.json"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "pack_id": pack["pack_id"],
        "pack_path": str(pack_path.relative_to(output_root)),
        "evidence_path": str(evidence_path.relative_to(output_root)),
        "result": evidence["result"],
        "providers": pack["providers"],
        "known_gaps": pack["known_gaps"],
    }


def assemble_context_pack(
    root: Path,
    request: dict[str, Any],
    *,
    providers: dict[str, ContextProvider] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or now_iso()
    provider_map = providers or default_context_providers(root)
    routed_ids = route_provider_ids(request)
    provider_results: list[dict[str, Any]] = []
    knowledge_items: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    proof_assets: list[dict[str, Any]] = []
    known_gaps: list[str] = []
    relevant_projects = _relevant_projects(root, request)
    operational_context = _operational_context(root, request)

    for provider_id in routed_ids:
        provider = provider_map.get(provider_id)
        if provider is None:
            provider_results.append(_provider_status(provider_id, "unavailable", 0, ["provider not configured"], False, False, "DOMAIN_PRIVATE"))
            known_gaps.append(f"{provider_id}: provider not configured.")
            continue
        health = provider.health()
        if not health.get("ok"):
            provider_results.append(_provider_status(provider_id, "unavailable", 0, [str(health.get("reason", "health check failed"))], False, False, "DOMAIN_PRIVATE"))
            known_gaps.append(f"{provider_id}: unavailable ({health.get('reason', 'health check failed')}).")
            continue
        try:
            result = provider.retrieve(request)
        except (OSError, RuntimeError, ValueError) as exc:
            provider_results.append(_provider_status(provider_id, "unavailable", 0, [str(exc)], False, False, request["privacy_domain"]))
            known_gaps.append(f"{provider_id}: unavailable ({exc}).")
            continue
        try:
            _validate_provider_result(provider_id, result)
        except ValidationError as exc:
            provider_results.append(_provider_status(provider_id, "malformed", 0, [str(exc)], False, False, request["privacy_domain"]))
            known_gaps.append(f"{provider_id}: malformed provider result.")
            continue
        provider_results.append({
            "id": provider_id,
            "status": result["status"],
            "items_returned": len(result["items"]),
            "known_gaps": result["known_gaps"],
            "truncated": result["truncated"],
            "available_more": result["available_more"],
            "privacy_classification": result["privacy_classification"],
            "elapsed_ms": result["elapsed_ms"],
        })
        knowledge_items.extend(result["items"])
        sources.extend(result["sources"])
        proof_assets.extend(result["proof_assets"])
        known_gaps.extend(result["known_gaps"])

    max_items = int(request["max_items"])
    truncated = len(knowledge_items) > max_items
    available_more = truncated or any(item["available_more"] for item in provider_results)
    if truncated:
        known_gaps.append("Global context budget truncated retrieved knowledge items.")
        knowledge_items = knowledge_items[:max_items]
    pack = {
        "schema_version": "v1",
        "pack_id": request["request_id"],
        "request": request,
        "providers": provider_results,
        "generated_at": generated_at,
        "operational_context": operational_context,
        "knowledge_items": knowledge_items,
        "relevant_decisions": [],
        "relevant_projects": relevant_projects,
        "proof_assets": _dedupe_dicts(proof_assets),
        "sources": _dedupe_dicts(sources),
        "constraints": {
            "request_privacy_domain": request["privacy_domain"],
            "max_items": max_items,
            "max_excerpt_chars": request["context_budget"]["max_excerpt_chars"],
            "provider_timeout_seconds": request["context_budget"]["provider_timeout_seconds"],
            "token_usage": "NOT_METERED",
            "truncated": truncated,
            "available_more": available_more,
        },
        "known_gaps": _dedupe_strings(known_gaps + _operational_gaps(operational_context, request)),
        "confidence": _confidence(provider_results, knowledge_items),
        "privacy_classification": request["privacy_domain"],
    }
    schema_path = root / "schemas" / "context_pack.schema.json"
    validate(pack, load_json(schema_path), schema_path=schema_path, root=root, location="context_pack")
    return pack


def build_context_evidence(
    root: Path,
    request: dict[str, Any],
    pack: dict[str, Any],
    *,
    request_path: Path,
    pack_path: Path,
) -> dict[str, Any]:
    serialized = json.dumps(pack, indent=2, sort_keys=True) + "\n"
    evidence = {
        "id": f"cortex-integration-002-{request['request_id']}",
        "source": "read-only cortex retrieval context request",
        "timestamp": pack["generated_at"],
        "candidate": "read-only-cortex-retrieval",
        "fixture": request["request_id"],
        "result": _evidence_result(pack),
        "metrics": {
            "execution_mode": "DEEP",
            "providers_used": [provider["id"] for provider in pack["providers"]],
            "items_retrieved": len(pack["knowledge_items"]),
            "known_gaps": len(pack["known_gaps"]),
            "truncated": pack["constraints"]["truncated"],
            "available_more": pack["constraints"]["available_more"],
            "privacy_classification": pack["privacy_classification"],
            "pack_lines": serialized.count("\n"),
            "pack_bytes": len(serialized.encode("utf-8")),
            "token_usage": "NOT_METERED",
        },
        "stdout_ref": "internal:none",
        "stderr_ref": "internal:none",
        "artifact_refs": [
            str(request_path.relative_to(root)),
            str(pack_path.relative_to(root)) if root.resolve() in pack_path.resolve().parents else str(pack_path),
        ],
        "provenance": {
            "recorded_by": "CORTEX-INTEGRATION-002",
            "source_uri": None,
            "observed_at": pack["generated_at"],
        },
        "environment": {
            "repository_path": str(root),
            "cortexabv_runtime_path": str(CORTEX_ABV_RUNTIME),
            "index_cortex_path": str(INDEX_CORTEX_ROOT),
            "production_mutation": False,
        },
    }
    schema_path = root / "schemas" / "evidence_record.schema.json"
    validate(evidence, load_json(schema_path), schema_path=schema_path, root=root, location="context_evidence")
    return evidence


def route_provider_ids(request: dict[str, Any]) -> list[str]:
    hints = [item for item in request.get("provider_hints", []) if item in {"cortexabv", "index-cortex"}]
    if hints:
        return list(dict.fromkeys(hints))
    routed: list[str] = []
    domains = {value.lower() for value in request.get("domains", [])}
    projects = {value.lower() for value in request.get("related_projects", [])}
    if request["privacy_domain"] in {"PERSONAL_PRIVATE", "PROJECT_PRIVATE"} or "azurmenton" in projects or "coqpi" in projects:
        routed.append("cortexabv")
    if {"indices", "index-methodology", "methodology", "market", "pop"} & domains or "index-cortex" in projects:
        routed.append("index-cortex")
    return list(dict.fromkeys(routed))


def default_context_providers(root: Path) -> dict[str, ContextProvider]:
    return {
        "cortexabv": CortexAbvProvider(root),
        "index-cortex": IndexCortexProvider(root),
    }


def _provider_status(provider_id: str, status: str, items_returned: int, known_gaps: list[str], truncated: bool, available_more: bool, privacy: str) -> dict[str, Any]:
    return {
        "id": provider_id,
        "status": status,
        "items_returned": items_returned,
        "known_gaps": known_gaps,
        "truncated": truncated,
        "available_more": available_more,
        "privacy_classification": privacy,
        "elapsed_ms": 0,
    }


def _validate_provider_result(provider_id: str, result: dict[str, Any]) -> None:
    required = {"status", "items", "sources", "proof_assets", "known_gaps", "truncated", "available_more", "privacy_classification", "elapsed_ms"}
    missing = sorted(required - set(result))
    if missing:
        raise ValidationError(f"{provider_id}: malformed provider result missing {missing}")


def _relevant_projects(root: Path, request: dict[str, Any]) -> list[dict[str, Any]]:
    registry = load_json(root / "registries" / "projects.json")
    selected = []
    wanted = {value.lower() for value in request.get("related_projects", [])}
    for entry in registry["entries"]:
        entry_id = str(entry.get("id", "")).lower()
        if entry_id in wanted or entry_id == request.get("consumer", "").lower():
            selected.append({
                "id": entry["id"],
                "name": entry.get("name", entry["id"]),
                "status": entry.get("status", "unknown"),
                "purpose": entry.get("purpose"),
            })
    return selected


def _operational_context(root: Path, request: dict[str, Any]) -> list[dict[str, Any]]:
    state = load_json(root / "portfolio" / "state.json")
    wanted = {value.lower() for value in request.get("related_projects", [])}
    if request.get("consumer") == "coqpi":
        wanted.add("coqpi")
    items = []
    for entry in state["entries"]:
        if entry["project"].lower() not in wanted:
            continue
        items.append({
            "project": entry["project"],
            "operational_state": entry["operational_state"],
            "current_outcome": entry["current_outcome"],
            "next_action": entry["next_action"],
            "waiting_reason": entry["waiting_reason"],
            "human_attention_required": entry["human_attention_required"],
            "evidence_refs": entry["evidence_refs"],
            "source": "ABVX-OS",
        })
    return items


def _operational_gaps(operational_context: list[dict[str, Any]], request: dict[str, Any]) -> list[str]:
    if operational_context:
        return []
    if request.get("related_projects"):
        return ["No matching ABVX operational state was available for the requested projects."]
    return []


def _confidence(provider_results: list[dict[str, Any]], knowledge_items: list[dict[str, Any]]) -> dict[str, str]:
    severe = any(provider["status"] in {"malformed", "unavailable"} for provider in provider_results)
    partial = any(provider["status"] in {"partial", "gap", "denied"} or provider["truncated"] for provider in provider_results)
    if severe and not knowledge_items:
        return {"level": "LOW", "rationale": "No provider returned usable knowledge and at least one provider was unavailable or malformed."}
    if partial or not knowledge_items:
        return {"level": "MEDIUM", "rationale": "Some useful context was returned, but provider gaps, denials or truncation remain."}
    return {"level": "HIGH", "rationale": "Returned context stayed within budget and providers responded without known failures."}


def _evidence_result(pack: dict[str, Any]) -> str:
    provider_statuses = {provider["status"] for provider in pack["providers"]}
    if not pack["knowledge_items"] and provider_statuses <= {"gap", "denied"}:
        return "INCONCLUSIVE"
    if "malformed" in provider_statuses:
        return "FAIL"
    if "unavailable" in provider_statuses and not pack["knowledge_items"]:
        return "FAIL"
    if pack["constraints"]["truncated"] or provider_statuses & {"gap", "denied", "unavailable", "partial"}:
        return "CONDITIONAL_PASS"
    return "PASS"


def _dedupe_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


def _dedupe_dicts(values: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for value in values:
        key = json.dumps(value, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(value)
    return deduped


class CortexAbvProvider:
    provider_id = "cortexabv"

    def __init__(self, root: Path):
        self.root = root
        self.runtime_root = CORTEX_ABV_RUNTIME

    def capabilities(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "read_only": True,
            "supported_tenants": ["cortex-abv-personal", "azur-menton", "index-spike", "monitor-mn7r"],
        }

    def health(self) -> dict[str, Any]:
        artifact = self.runtime_root / "data" / "vector-indexes" / "turbovec-poc" / "index-artifact.v1.json"
        harness = self.runtime_root / "src" / "vector-runtime-controlled-module-harness.mjs"
        if artifact.is_file() and harness.is_file():
            return {"ok": True}
        return {"ok": False, "reason": "local runtime artifact or harness missing"}

    def retrieve(self, request: dict[str, Any]) -> dict[str, Any]:
        if request["privacy_domain"] == "PUBLIC":
            return self._gap("denied", "PUBLIC consumers are not allowed to receive CortexABV private runtime content.")
        tenant_queries = self._tenant_queries(request)
        if not tenant_queries:
            return self._gap("gap", "No supported CortexABV retrieval surface matched the request.")
        started = time.perf_counter()
        items: list[dict[str, Any]] = []
        sources: list[dict[str, Any]] = []
        proof_assets: list[dict[str, Any]] = []
        known_gaps: list[str] = []
        for tenant, query in tenant_queries:
            payload = self._run_query(query, tenant, max_items=int(request["max_items"]))
            if not payload["result"]["candidates"]:
                known_gaps.append(f"CortexABV tenant {tenant} returned no candidate knowledge for this request.")
                continue
            for candidate in payload["result"]["candidates"]:
                doc = payload["documents"].get(candidate["candidateId"], {})
                privacy = _cortexabv_tenant_privacy(tenant)
                items.append({
                    "id": f"{self.provider_id}:{tenant}:{candidate['candidateId']}",
                    "provider": self.provider_id,
                    "category": "project_knowledge" if tenant != "cortex-abv-personal" else "proof_context",
                    "title": doc.get("title", candidate["candidateId"]),
                    "summary": f"CortexABV candidate match in {tenant}; matched terms: {', '.join(candidate.get('matchedTerms', [])) or 'none'}.",
                    "excerpt": f"title={doc.get('title', candidate['candidateId'])}; candidate_id={candidate['candidateId']}; score={candidate['score']}",
                    "privacy_classification": privacy,
                    "confidence": "MEDIUM",
                    "provenance": {
                        "tenant": tenant,
                        "candidate_id": candidate["candidateId"],
                        "evidence_refs": doc.get("evidenceRefs", []),
                    },
                })
                for ref in doc.get("evidenceRefs", []):
                    source = {
                        "provider": self.provider_id,
                        "tenant": tenant,
                        "path": ref.get("path"),
                        "ref": ref.get("ref"),
                        "digest": ref.get("digest"),
                        "privacy_classification": privacy,
                    }
                    sources.append(source)
                    proof_assets.append(source)
        if any(tenant == "cortex-abv-personal" for tenant, _ in tenant_queries):
            known_gaps.append("CortexABV personal retrieval currently exposes only a minimal public-presence baseline, not a rich professional profile or recent-work timeline.")
        if any(tenant == "azur-menton" for tenant, _ in tenant_queries):
            known_gaps.append("CortexABV AzurMenton retrieval currently surfaces a compact guide bundle only; durable decisions and richer editorial history remain absent.")
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        status = "partial" if known_gaps else "ok"
        return {
            "status": status if items else "gap",
            "items": items,
            "sources": _dedupe_dicts(sources),
            "proof_assets": _dedupe_dicts(proof_assets),
            "known_gaps": _dedupe_strings(known_gaps or (["No CortexABV knowledge matched this request."] if not items else [])),
            "truncated": len(items) > int(request["max_items"]),
            "available_more": False,
            "privacy_classification": request["privacy_domain"],
            "elapsed_ms": elapsed_ms,
        }

    def _run_query(self, query: str, tenant: str, *, max_items: int) -> dict[str, Any]:
        script = """
import { loadIndexArtifact, queryCandidates, verifyClaimEvidence } from './src/vector-runtime-controlled-module-harness.mjs';
const query = process.argv[1];
const tenant = process.argv[2];
const artifactPath = process.argv[3];
const topK = Number(process.argv[4] || '4');
const loaded = loadIndexArtifact({ artifactPath });
const result = queryCandidates({ loadedIndex: loaded, query, tenant, topK, minScore: 0.05 });
const documents = Object.fromEntries(loaded.artifact.documents.map((document) => [document.id, document]));
const verification = verifyClaimEvidence({ candidates: result.candidates });
console.log(JSON.stringify({ result, verification, documents }, null, 2));
"""
        artifact_path = str(self.runtime_root / "data" / "vector-indexes" / "turbovec-poc" / "index-artifact.v1.json")
        completed = subprocess.run(
            ["node", "--input-type=module", "-e", script, query, tenant, artifact_path, str(max(2, min(6, max_items)))],
            cwd=self.runtime_root,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "CortexABV query failed")
        payload = json.loads(completed.stdout)
        if not payload.get("verification", {}).get("passed", False):
            raise RuntimeError("CortexABV evidence verification failed")
        return payload

    def _tenant_queries(self, request: dict[str, Any]) -> list[tuple[str, str]]:
        projects = {value.lower() for value in request.get("related_projects", [])}
        domains = {value.lower() for value in request.get("domains", [])}
        queries: list[tuple[str, str]] = []
        if request.get("consumer") == "coqpi" or request["privacy_domain"] == "PERSONAL_PRIVATE":
            queries.append(("cortex-abv-personal", "public presence baseline current project links proof"))
        if "azurmenton" in projects:
            queries.append(("azur-menton", "azurmenton practical local guides faq onboarding place cards"))
        if "index-cortex" in projects or {"indices", "index-methodology", "pop"} & domains:
            queries.append(("index-spike", "index spike public summary updates methodology"))
        if "mn7r" in projects or "monitor" in domains:
            queries.append(("monitor-mn7r", "monitor mn7r repository readiness status"))
        return list(dict.fromkeys(queries))

    def _gap(self, status: str, message: str) -> dict[str, Any]:
        return {
            "status": status,
            "items": [],
            "sources": [],
            "proof_assets": [],
            "known_gaps": [message],
            "truncated": False,
            "available_more": False,
            "privacy_classification": "PROJECT_PRIVATE",
            "elapsed_ms": 0,
        }


class IndexCortexProvider:
    provider_id = "index-cortex"

    def __init__(self, root: Path):
        self.root = root
        self.index_root = INDEX_CORTEX_ROOT

    def capabilities(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "read_only": True,
            "supported_domains": ["indices", "index-methodology", "sources", "observations", "market"],
        }

    def health(self) -> dict[str, Any]:
        if (self.index_root / ".cortex" / "chunk-manifest.json").is_file() and (self.index_root / "package.json").is_file():
            return {"ok": True}
        return {"ok": False, "reason": "Index chunk manifest or package.json missing"}

    def retrieve(self, request: dict[str, Any]) -> dict[str, Any]:
        if request["privacy_domain"] == "EXTERNAL_UNTRUSTED":
            return self._gap("denied", "External untrusted consumers are not allowed to receive Index Cortex internal context.")
        started = time.perf_counter()
        with tempfile.TemporaryDirectory(prefix="abvx-index-context-") as temp:
            out_path = Path(temp) / "context-pack.json"
            cmd = [
                "npm",
                "run",
                "cortex:context-pack",
                "--",
                "--chunks=.cortex/chunk-manifest.json",
                f"--query={_index_query(request)}",
                f"--purpose={_index_purpose(request)}",
                f"--out={out_path}",
                f"--max-evidence={max(2, min(8, int(request['max_items'])))}",
                f"--max-tokens={max(200, int(request['context_budget']['max_excerpt_chars']) * max(1, int(request['max_items'])))}",
                "--owner=index",
                f"--visibility={','.join(_index_visibilities(request['privacy_domain']))}",
            ]
            completed = subprocess.run(
                cmd,
                cwd=self.index_root,
                capture_output=True,
                text=True,
                timeout=int(request["context_budget"]["provider_timeout_seconds"]),
                check=False,
            )
            if completed.returncode != 0:
                raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "Index Cortex context-pack command failed")
            artifact = json.loads(out_path.read_text(encoding="utf-8"))
        items: list[dict[str, Any]] = []
        sources: list[dict[str, Any]] = []
        for evidence in artifact["pack"]["evidence"]:
            url_or_path = evidence["urlOrPath"]
            relative_path = _index_relative_path(url_or_path)
            if not _is_admitted_index_path(relative_path):
                raise RuntimeError(f"Index provider returned a non-admitted source path: {relative_path}")
            privacy = _visibility_to_privacy(evidence["visibility"])
            items.append({
                "id": evidence["id"],
                "provider": self.provider_id,
                "category": "domain_context",
                "title": evidence["title"],
                "summary": evidence["summary"],
                "excerpt": evidence["summary"][: int(request["context_budget"]["max_excerpt_chars"])],
                "privacy_classification": privacy,
                "confidence": "HIGH" if evidence["visibility"] in {"public", "internal"} else "MEDIUM",
                "provenance": {
                    "source_id": evidence["sourceId"],
                    "url_or_path": url_or_path,
                    "visibility": evidence["visibility"],
                },
            })
            sources.append({
                "provider": self.provider_id,
                "source_id": evidence["sourceId"],
                "url_or_path": url_or_path,
                "visibility": evidence["visibility"],
                "privacy_classification": privacy,
            })
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        known_gaps = list(artifact["pack"]["knownGaps"])
        status = "partial" if known_gaps else "ok"
        if not items:
            status = "gap"
            known_gaps.append("Index Cortex returned no admitted knowledge for this request.")
        return {
            "status": status,
            "items": items,
            "sources": _dedupe_dicts(sources),
            "proof_assets": [],
            "known_gaps": _dedupe_strings(known_gaps),
            "truncated": any("omitted" in gap.lower() for gap in known_gaps),
            "available_more": any("omitted" in gap.lower() for gap in known_gaps),
            "privacy_classification": request["privacy_domain"],
            "elapsed_ms": elapsed_ms,
        }

    def _gap(self, status: str, message: str) -> dict[str, Any]:
        return {
            "status": status,
            "items": [],
            "sources": [],
            "proof_assets": [],
            "known_gaps": [message],
            "truncated": False,
            "available_more": False,
            "privacy_classification": "DOMAIN_PRIVATE",
            "elapsed_ms": 0,
        }


def _index_query(request: dict[str, Any]) -> str:
    parts = [
        request["task"],
        request["intent"],
        " ".join(request.get("domains", [])),
        " ".join(request.get("entities", [])),
        " ".join(request.get("related_projects", [])),
    ]
    return " ".join(part for part in parts if part).strip()


def _index_purpose(request: dict[str, Any]) -> str:
    domains = {value.lower() for value in request.get("domains", [])}
    if "pop" in domains:
        return "project-recommendation"
    return "source-review"


def _index_visibilities(privacy_domain: str) -> list[str]:
    if privacy_domain == "PUBLIC":
        return ["public"]
    return ["public", "internal", "protected"]


def _visibility_to_privacy(visibility: str) -> str:
    if visibility == "public":
        return "PUBLIC"
    if visibility == "protected":
        return "PROJECT_PRIVATE"
    return "DOMAIN_PRIVATE"


def _cortexabv_tenant_privacy(tenant: str) -> str:
    if tenant == "cortex-abv-personal":
        return "PERSONAL_PRIVATE"
    return "PROJECT_PRIVATE"


def _index_relative_path(url_or_path: str) -> str:
    _, _, tail = url_or_path.partition(":")
    return tail.split("#", 1)[0]


def _is_admitted_index_path(relative_path: str) -> bool:
    normalized = relative_path.replace("\\", "/")
    if not normalized or normalized.startswith(".") or "/." in normalized:
        return False
    lower = normalized.lower()
    if any(token in lower for token in ["/session/", ".whatsapp-session", ".wwebjs_cache", "/dist/", "/build/", "/.next/", "/coverage/", "/out/", "/tmp/", "/temp/"]):
        return False
    parts = normalized.split("/")
    if len(parts) == 1:
        return parts[0] in INDEX_APPROVED_TOP_LEVEL_FILES or normalized.lower().endswith(".pdf")
    return parts[0] in INDEX_APPROVED_TOP_LEVEL_DIRS
