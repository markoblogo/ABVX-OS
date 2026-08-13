# ABVX-INTELLIGENCE-001

## Scope

Create the smallest donor-first internal intelligence seam for bounded semantic work inside ABVX-OS, without building an agent framework, RAG layer, or external orchestration system.

## Local environment observed

- Ollama binary present at `/usr/local/bin/ollama`
- Ollama server reachable on `http://127.0.0.1:11434`
- Installed models observed:
  - `qwen3.5:4b`
  - `qwen2.5-coder-3b-continue:latest`
  - `gemma4:12b`
  - `gpt-oss:20b`
- No `ollama` Python package installed
- No `openai` Python package installed

## Donor evaluation

### Existing ABVX / registry context reviewed

- `registries/capabilities.json`
- `registries/donor-capability-matrix.json`
- `registries/external-candidates/book-factory-001.json`
- `registries/external-candidates/book-factory-003.json`

### Candidate classification

- Direct Ollama HTTP API
  - class: `RUNTIME`
  - role: local structured semantic execution
  - decision: `SELECTED`
  - reason: already installed, removable, no new dependency burden

- Ollama OpenAI-compatible API
  - class: `REFERENCE`
  - role: fallback transport pattern
  - decision: `NOT_NEEDED_V1`
  - reason: direct local API is smaller

- Dify
  - class: `PATTERN`
  - role: broader workflow / RAG platform
  - decision: `REJECTED_FOR_SCOPE`
  - reason: too large for this seam

- LangChain / LlamaIndex
  - class: `PATTERN`
  - role: framework abstraction
  - decision: `REJECTED_FOR_SCOPE`
  - reason: unnecessary for a single local-first task seam

## Implemented seam

### Capability

- Added `internal-intelligence-runtime` to `registries/capabilities.json`
- Added allowlisted task registry in `registries/intelligence-tasks.json`

### Contract

`execute_intelligence_task(root, task_id, context, policy)`

Required result shape:

- `status`
- `provider`
- `model`
- `execution_tier`
- `latency_ms`
- `usage`
- `locality`
- `validation`
- `failure_reason`
- `output`
- `policy`

### Execution routing

- `DETERMINISTIC`
- `LOCAL_LLM`
- `CHEAP_API`
- `CODEX_ESCALATION`

Current v1 routing:

- preferred: `LOCAL_LLM`
- fallback: `CODEX_ESCALATION`

No automatic Codex invocation is performed.

## Initial task registry

Only one task was admitted:

- `content-enrichment`

Input bounds:

- max chars: `16000`
- max body lines: `48`

Validation:

- JSON schema
- allowlisted internal links only
- non-empty tags
- non-empty summary

## Acceptance case

- selected input:
  `content/fixtures/content-publish-005-abvx-marmite-oatmeal.json`

- reference metadata was used only for post-run comparison, not as model input

## Real invocation result

### Command

`./bin/abvx intelligence run --task content-enrichment --file content/fixtures/content-publish-005-abvx-marmite-oatmeal.json --json`

### Observed outcome

- provider: `ollama.local`
- selected model: `qwen3.5:4b`
- status: `ESCALATION_REQUIRED`
- execution tier: `CODEX_ESCALATION`
- failure reason: `empty model response`

Runtime artifact:

- `evidence/intelligence/content-publish-005-abvx-marmite-oatmeal.runtime.json`

## Additional local probes

These were bounded technical probes, not accepted task runs:

- `gemma4:12b` trivial JSON probe
  - outcome: timed out
- `qwen2.5-coder-3b-continue:latest` trivial JSON probe
  - outcome: timed out

Conclusion:

The local provider seam is technically wired, but the currently installed models are not yet operationally admitted for this bounded structured-output task on this machine.

## Content Ops integration

Added optional mode:

`./bin/abvx content prepare --file <path> --intelligence local_llm`

Observed result for the same acceptance fixture:

- content item remained `BLOCKED`
- blocker:
  `internal intelligence failed closed: timed out`
- deterministic enrichment was preserved only as inspection fallback
- no publish path was opened

This satisfies fail-closed behavior.

## Quality / hallucination assessment

No accepted semantic output was produced from a real local model run, so hallucination assessment is `NOT_PROVEN`.

Because the runtime escalated fail-closed, it did not create a bad publish packet or silently mutate a consumer path.

## Cost / resource result

- runtime code footprint stayed bounded
- no new dependency added
- no external API required
- local inference latency on the installed models was not operationally acceptable for this acceptance case

Codex-saving estimate if the provider later becomes operational:

- `MEDIUM`

Reason:

Routine Content Ops enrichment would move from a full Codex mission to a one-command local semantic pass plus human review.

## Langfuse seam

Preferred future instrumentation point:

- `src/abvx_harness/intelligence.py`
- `execute_intelligence_task(...)`

Langfuse remains paused and was not integrated.

## Unusual Indices readiness

The seam is structurally ready for future:

- source classification
- source summary
- relevance ranking

But provider admission is not ready yet, so it should not be used for unattended semantic work in the Unusual Indices mission.

## Recommendation

### Admit now

- the bounded internal intelligence contract
- the allowlisted task registry
- the fail-closed Content Ops integration seam

### Do not admit yet

- local Ollama provider as production-ready semantic runtime

### Next bounded step

Choose one and rerun this same acceptance case:

1. explicitly admit and test one known-good structured-output local model
2. configure one cheap API route for `CHEAP_API`
3. keep the seam dormant and use `CODEX_ESCALATION` until provider admission is approved
