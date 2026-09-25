# Narrative Toki Pona Pipeline V1

Status: internal pre-production implementation. This document describes a local/private production layer; it does not authorize a complete Jekyll translation or publication.

## Architecture

The public translator and the narrative book runner share validation primitives but have different operational boundaries. `PUBLIC` retains the 500-character request limit and lexical validation. `INTERNAL_BOOK_PIPELINE` is a trusted local runner that processes a book as sections and bounded semantic blocks. There is no public `unlimited=true` bypass and no anonymous internal endpoint.

## Public Translator

The existing public service remains outside this repository and was not weakened. Its endpoint must be verified separately at deployment time. The previous `toki.abvx.xyz/api/translate` probe returned `NOT_FOUND`; this pipeline therefore does not hard-code that URL. Public regression is recorded as UNKNOWN until the owning deployment is repaired or its retirement is documented.

## Internal Book Runner

`src/abvx_harness/narrative_pipeline.py` provides a local runner with configurable semantic-block size, bounded attempts, incremental manifest writes, source-hash checks, resume, ordering, and failure visibility. Total book length is unbounded by orchestration; individual requests remain bounded for context quality and recovery.

## Block Model

Each `SourceBlock` carries `book_id`, `section_id`, stable `block_id`, source text/hash, block type, ordinal, speaker slot, knowledge type, entities, and spoiler constraints. Each `TranslationBlock` carries the source hash, output/hash, status, attempts, error, and history. This preserves exact source ↔ output traceability.

Supported block types are `NARRATION`, `DIALOGUE`, `DOCUMENT`, `HEADING`, and the extensible fallback `OTHER`. Detection is intentionally conservative.

## Name Lane

Names are an explicit allowlist derived from the project entity ledger. Ordinary lexical validation remains intact. Unapproved name forms fail; names are never silently replaced with role descriptions. The Jekyll ledger keeps Jekyll and Hyde separate until source disclosure.

## Knowledge State

Blocks receive lightweight metadata such as `NARRATOR_FACT`, `FOCAL_CHARACTER_INFERENCE`, `CHARACTER_OPINION`, `DOCUMENT_CLAIM`, and `DIALOGUE_CLAIM`. This is a review signal, not an automated literary verdict.

## Spoiler Controls

Project rules are data-driven: blocks involving identity, letters, wills, disappearance, or the draught receive review constraints. A bounded checker flags possible premature identity disclosure and claim-to-fact upgrades. It does not claim to prove spoiler-free literature.

## Phrasebook

The Jekyll sample uses a small project phrasebook for legal conditions, documents, laboratory/cabinet distinctions, evidence, confidence, escape/safety, and uncertainty. These remain project configuration, not Jekyll-specific engine branches.

## Alignment QA

Machine checks report missing, duplicate, unknown, empty, source-hash, section, and order failures by exact block ID. Word counts are secondary diagnostics only.

## Review Queue

Review is risk-based: critical entities, documents, legal conditions, medical/scientific claims, ambiguity, knowledge boundaries, spoiler flags, and low confidence are queued first. The queue shows source, output, context, entities, and reason.

## Recovery

The manifest records run ID, pipeline version, mode, source block count, source hashes, output hashes, status, attempts, errors, and history. A failed block is retried alone; a resumed run skips successful blocks with matching source hashes.

## Reproducibility

Run artifacts preserve normalized source blocks, configuration, entity ledger version, phrasebook, constraints, translated blocks, QA reports, and layout output. Literary translation is not promised deterministic; process state is.

## Tests

Focused tests cover public-size enforcement, internal block processing, stable IDs, resume, duplicate/missing alignment, proper-name allowlisting, Jekyll/Hyde distinction, knowledge review, and public/internal configuration separation.

## Known Limitations

The provider adapter is intentionally not an anonymous network bypass. The deployed public endpoint still needs an owner-side deployment decision. The sample rerun proves orchestration and QA plumbing, not final literary quality. Human review remains required for voice, ambiguity, character rhythm, and final Toki Pona adequacy. Full EPUB is not part of this gate.
