# Proof-Preserving Context Compression v0.1

## Purpose

Create smaller ABVX-OS context artifacts without changing canonical facts, provenance, policy, decisions, approval state, privacy classification, or uncertainty.

This contract is an optional preparation step. It does not replace the canonical source, promote data, publish content, or authorize a provider.

## Required input identity

Every run records:

- source path or stable source reference;
- source version, commit, or timestamp;
- content digest when the source was actually read;
- owner and privacy domain;
- baseline word or field count;
- requested output scope.

## Classification

Each sentence or field receives one disposition:

- `KEEP`: information, provenance, structure, or uncertainty remains needed;
- `REMOVE`: provable filler or exact duplicate with no information content;
- `FLAG`: a judgment call, left in the output for owner review.

When uncertain, keep. Never remove or paraphrase canonical IDs, facts, numbers, dates, named entities, source references, policy, decisions, gates, approval state, privacy labels, failure state, or `UNKNOWN`/`UNVERIFIED` evidence.

## Output envelope

```yaml
schema: abvx-proof-preserving-context-compression-v0
status: PROPOSED
source:
  ref: <path-or-stable-id>
  version: <commit-or-timestamp>
  digest: <sha256-or-null>
scope: <project-or-mission-scope>
baseline_count: <integer>
final_count: <integer>
dispositions:
  kept: <integer>
  removed: <integer>
  flagged: <integer>
fidelity_check: PASS | FAIL | UNKNOWN
canonical_source_unchanged: true
owner_review_required: true
```

The durable result is a proposal or evidence artifact under the existing ABVX ownership rules. The source remains canonical. A compressed projection must link back to the source and must not be the only record of an important decision.

## ABVX-OS boundaries

- compress reviewed handoffs, proposals, and evidence notes;
- retain decisive evidence and exact artifact paths;
- keep privacy and approval state visible;
- do not compress away a failed or missing provider result;
- do not write to sibling repositories or invoke external actions;
- do not claim semantic losslessness without a completed fidelity check.

## Review result

Allowed review states are `ACCEPT`, `REVISE`, and `INSUFFICIENT_EVIDENCE`. `ACCEPT` means the projection is usable for the requested bounded context, not that it replaces the canonical source.
