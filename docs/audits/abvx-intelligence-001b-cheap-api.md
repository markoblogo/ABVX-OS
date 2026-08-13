# ABVX-INTELLIGENCE-001B — Cheap API admission

## Scope

Admit the smallest non-local fallback provider for the existing ABVX intelligence seam:

`LOCAL_LLM -> CHEAP_API -> CODEX_ESCALATION`

This does not create an agent framework, autonomous planner, workflow engine or publication authority.

## Prior state

- `LOCAL_LLM_NOT_ADMITTED`.
- Local Ollama candidates were not reliable enough for the content-enrichment acceptance task.
- No further Ollama/model-download retry was performed.

## Provider boundary

Provider: `cheap.api`

Implementation:

`execute_intelligence_task(root, task_id, context, policy, provider_override="cheap.api")`

Concrete provider:

- OpenAI Responses API
- model: `gpt-5.6-luna`
- auth: `OPENAI_API_KEY` from environment only
- no token values stored or printed
- no SDK dependency added
- no external mutation beyond the bounded API inference call
- `store: false`

Official references used:

- OpenAI API overview / authentication: https://developers.openai.com/api/reference/overview
- Structured outputs: https://developers.openai.com/api/docs/guides/structured-outputs
- Pricing: https://developers.openai.com/api/docs/pricing

## Cost guard

Task-level guard added for `content-enrichment`:

- model: `gpt-5.6-luna`
- reasoning effort: `low`
- max output tokens: `900`
- expected cost class: `CHEAP`
- max estimated cost: `$0.01` per task
- max input chars: inherited from task registry
- max body lines: inherited from task registry

Observed OpenAI pricing for `gpt-5.6-luna` short-context text was used for approximate cost evidence: input `$0.20` / 1M tokens and output `$1.20` / 1M tokens.

## Structured-output correction

Initial real run exposed one harness issue:

- output schema allowed arbitrary `internal_link_suggestions`;
- model returned a string containing an allowed link plus explanatory text;
- post-validation correctly failed closed.

Fix:

- the runtime now binds `internal_link_suggestions.items.enum` to the context-specific allowlist before calling the provider;
- post-validation remains in place.

This makes unsupported links fail at provider-schema level and at ABVX validation level.

## Admission fixture

Fixture:

`content/fixtures/content-publish-005-abvx-marmite-oatmeal.json`

Task:

`content-enrichment`

Command shape:

`./bin/abvx intelligence run --task content-enrichment --file content/fixtures/content-publish-005-abvx-marmite-oatmeal.json --provider cheap.api --json`

## Admission result

After context-bound schema fix:

| Attempt | Status | Latency | Approx cost | Schema | Human correction | Hallucination |
|---|---:|---:|---:|---|---|---|
| 1 | SUCCEEDED | 3001 ms | $0.0004908 | PASS | no | no |
| 2 | SUCCEEDED | 3300 ms | $0.0005196 | PASS | no | no |
| 3 | SUCCEEDED | 3586 ms | $0.0005172 | PASS | no | no |

Artifacts:

- `evidence/intelligence/admission-gpt-5-6-luna-attempt1.runtime.json`
- `evidence/intelligence/admission-gpt-5-6-luna-attempt2.runtime.json`
- `evidence/intelligence/admission-gpt-5-6-luna-attempt3.runtime.json`
- `evidence/intelligence/admission-gpt-5-6-luna.evidence.json`

## Decision

`gpt-5.6-luna` is conditionally admitted as the `CHEAP_API` provider for the single allowlisted task:

`content-enrichment`

It is not admitted for:

- manuscript generation;
- factual research without sources;
- autonomous publication;
- broad portfolio reasoning;
- agent orchestration.

## Remaining boundary

If `cheap.api` fails because credentials are absent, API errors occur, schema validation fails, cost guard is exceeded, or output is unsupported:

`CODEX_ESCALATION`

No silent fallback to unbounded generation is allowed.
