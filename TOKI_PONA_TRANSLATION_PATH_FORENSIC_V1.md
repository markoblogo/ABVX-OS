# Toki Pona Translation Path Forensic V1

Date: 2026-09-21  
Scope: reconstruct the last successful Toki Pona production path before selecting a provider for Jekyll. This is an evidence audit, not authorization to translate Jekyll in full.

## Historical Production Inventory

| Stage | Evidence | Status |
|---|---|---|
| Source preparation | `OD-TP.odt` and public-domain/source text retained in Odyssey worktree | CONFIRMED |
| Toki Pona prose generation | Recorded workflow used ChatGPT continuation/glossary blocks, pasted in controlled batches | CONFIRMED |
| Runtime API/provider | No retained API receipt, model ID, endpoint, or provider log found | UNKNOWN |
| Segmentation | Continuation batches and document insertion points; exact historical chunk schema not retained | LIKELY |
| Human correction | Canonical decisions, manual decisions, controlled-fix logs, and editorial master exist | CONFIRMED |
| Sitelen conversion | Selective `nasin-sitelen-pu` styling and duplicated glossary rendering spans | CONFIRMED |
| Final assembly | LibreOffice ODT → PDF, TOC refresh, QA and KDP layout artifacts | CONFIRMED |

The strongest evidence is the retained Odyssey formatting skill and rollout record, not a speculative current provider configuration.

## Odyssey Reconstruction

### SOURCE → TRANSLATION GENERATION

The source was assembled in `OD-TP.odt`. Translation text was produced through interactive ChatGPT continuation/glossary blocks, then pasted into the document in batches. The retained skill explicitly describes the workflow as staged document production and warns that generated continuation is not automatically translation-verified. **CONFIRMED.**

The historical record does not preserve a provider receipt, API key configuration, model name, request log, or machine batch manifest. Therefore the exact model/API cannot be recovered from repository artifacts. **UNKNOWN.**

### TRANSLATION → EDITORIAL/QA

The document was reviewed with an audit-only ODT/PDF QA layer. A protected editorial master was created, canonical decisions and manual decisions were preserved, and controlled fixes were applied to a copy. The final candidate reached zero recorded QA findings in the local gate. **CONFIRMED.**

### SITELEN

The workflow retained readable Latin Toki Pona plus duplicated rendering spans where appropriate. `Georgia` was applied to Latin text and `nasin-sitelen-pu` to selected sitelen spans. **CONFIRMED.**

### LAYOUT → PUBLICATION ARTIFACT

The final Odyssey candidate was 7 × 10 inches, 629 rendered pages (KDP-effective even count 630), with ODT/PDF artifacts, refreshed TOC, embedded fonts, visual checks, and a release-candidate local preflight. KDP Print Previewer, physical proof, cover, and Kindle packaging were not completed in that run. **CONFIRMED.**

## Other Confirmed Production Paths

Retained landing data confirms completed Toki Pona editions for Marcus Aurelius, Epictetus, Seneca, Cicero, Dao De Jing, and A Christmas Carol, generally described as English reference → Toki Pona → sitelen pona. The public landing repository explicitly says the TP copy is authored separately and that its plugin only changes display layers; it does not translate English at runtime. **CONFIRMED for product/display architecture; UNKNOWN for the exact prose-generation provider.**

No retained machine manifests were found that establish a common API, model, or automated batch runner for those books. Their existence is evidence that a manual/interactive production capability worked in practice, not evidence that the current public endpoint generated them.

## Public Translator History

The current toolkit contains a public short-form translator contract and a Vercel-style API route, but the tested deployed `https://toki.abvx.xyz/api/translate` returned `NOT_FOUND`. Repository evidence does not prove that this route generated the historical books. The landing repository explicitly separates authored TP copy from runtime translation. **Historical book dependency: NO EVIDENCE.**

Decision: treat public deployment as a separate maintenance track. Do not repair or route book production through it as part of this forensic task.

## abvx-local-model-worker Investigation

The worker is a bounded, read-only local model service for explicit-context answers. Its implementation defaults to `occ-ai/OCC-RAG-0.6B`, exposes `/health` and `/v1/answer`, and is referenced by ABVX local-model harness documentation. It is not a Toki Pona-specific translator and no historical Toki Pona production artifact names it as a provider. The worker was unavailable during the Jekyll regression. **Role: CONFIRMED as a general local-model experiment; Toki Pona use: NO EVIDENCE.**

**WAS OCC-RAG ACTUALLY USED FOR TOKI PONA? — NO EVIDENCE / UNKNOWN, not YES.** Choosing it for Jekyll was a convenience-based current-path assumption, not an inference supported by the successful book records.

## Why Jekyll Selected the Wrong/Current Path

The Narrative Pipeline correctly added block IDs, manifests, name controls, knowledge state, spoiler checks, alignment, and resume. It then selected the only explicit ABVX model adapter visible in the current repository. That adapter was not the historical translation generator and was not designed or evidenced for literary Toki Pona. The error was provider reconstruction, not the new control layer.

## Historical vs Current Architecture

### Historical

`source → interactive ChatGPT continuation/glossary batches → human/editorial correction in ODT → selective sitelen styling → LibreOffice PDF/QA`

### Current desired

`source → stable block orchestrator → trusted capable translation provider → name/knowledge/spoiler/alignment QA → human editorial queue → sitelen/layout`

The new control layer remains. Only the provider seam changes.

## Recommended Translation Path

Use a capable authenticated interactive model/provider path equivalent to the historical ChatGPT continuation workflow, with the actual provider/model recorded per run. The historical evidence supports a remote or interactive model path; it does not support OCC-RAG-0.6B as a literary provider.

For Jekyll, use the new 40-block orchestrator with bounded context, ledger-backed names, phrasebook, knowledge/spoiler constraints, and preserved original/revised outputs. The provider must return only the target block. A local provider is optional, not a requirement.

## Minimum Integration Change

1. Add a provider adapter for the approved authenticated model path; do not change public translator limits.
2. Record provider, model/version, configuration, run date, and block-level responses in the existing manifest.
3. Run the unchanged Jekyll sample.
4. Apply existing alignment/name/knowledge/spoiler QA and a bounded second pass to flagged blocks.
5. Stop at the semantic regression gate.

No new orchestration framework is justified. No public endpoint repair is required for this path.

## Evidence Limits

The exact historical model/provider is not retained. “ChatGPT continuation/glossary blocks” is confirmed from the recorded workflow; a specific model name, API route, and automated batch process are not. The next run must therefore label the selected provider as a new explicit run, not retroactively claim it was the historical one.
