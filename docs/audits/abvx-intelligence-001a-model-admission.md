# ABVX-INTELLIGENCE-001A — Local model admission

## Scope

Close the open local-provider admission question from `ABVX-INTELLIGENCE-001` without changing the intelligence architecture.

## Preserved seam

- `execute_intelligence_task(...)`
- allowlisted task registry
- structured output schema contract
- fail-closed behavior
- `LOCAL_LLM -> ESCALATION_REQUIRED` routing
- Content Ops safety boundary

## Test

- task: `content-enrichment`
- fixture: `content/fixtures/content-publish-005-abvx-marmite-oatmeal.json`
- provider: `ollama.local`
- shared contract: `schemas/intelligence_content_enrichment_output.schema.json`

## Models tested

### `qwen3.5:4b`

- attempt 1: empty structured response
- attempt 2: timed out in real `content prepare --intelligence local_llm` path
- attempt 3: empty structured response
- repeatability: `0/3`
- admission: `REJECTED`

### `gemma4:12b`

- attempt 1: timed out at the full bounded window
- repeatability: structural failure
- admission: `REJECTED`

### `gpt-oss:20b`

- attempt 1: timed out at the full bounded window
- repeatability: structural failure
- admission: `REJECTED`

## Result

`LOCAL_LLM_NOT_ADMITTED`

No currently installed local model is operationally good enough for this bounded structured semantic workload on this machine.

## Quality comparison

No local model produced an admitted structured output, so metadata-quality comparison against the approved Marmite reference remains unresolved.

## Routing state after admission bakeoff

- default route remains `LOCAL_LLM -> ESCALATION_REQUIRED`
- practical runtime state for semantic work remains `ESCALATION_REQUIRED`

## Failure behavior

Confirmed:

- empty response -> fail closed
- timeout -> fail closed
- no silent publish
- no silent fallback to model-generated metadata

## Recommended next bounded step

If a paid fallback is approved, the next cheap provider to test should be:

- provider: `OpenAI Responses API`
- model: `GPT-5.6 Luna`

Reason:

- official model docs position it as the cost-sensitive high-volume tier
- current official pricing is materially cheaper than larger general-purpose models
- the task is narrow, structured and low-creativity

This is a recommendation only. No paid provider was wired in this mission.
