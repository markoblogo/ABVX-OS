# Jekyll Authenticated Provider Quality Gate V5

Date: 2026-09-21

## Decision

`TUNE_AND_RERUN`

The authenticated provider gate could not reach the OpenAI Responses endpoint from this environment. This is an execution blocker, not evidence that the model or the narrative pipeline is unsuitable. No fallback provider, public translator, fixture output, or invented translation was used.

## Provider/auth result

- Credential presence: `OPENAI_API_KEY` present (value never logged).
- Existing integration reused: `src/abvx_harness/intelligence.py` Responses API client pattern.
- Requested model: `gpt-5.6-sol` (configurable through `JEKYLL_PROVIDER_MODEL`).
- API result: DNS/network failure before an HTTP response: `URLError: [Errno 8] nodename nor servname provided, or not known`.
- Provider smoke: `NOT_RUN — NETWORK_BLOCKED`.
- Five-block calls completed: `0/5`.
- 40-block regression: `NOT_RUN`.
- Full-book readiness: `NOT_READY`.

## Exact smoke selection (recorded, not translated)

1. `jekyll-sample-v2:section-002:b0005` — will and conditional succession language.
2. `jekyll-sample-v2:section-002:b0007` — Utterson's inference and uncertainty.
3. `jekyll-sample-v2:section-002:b0013` — Lanyon's opinion as character speech.
4. `jekyll-sample-v2:section-003:b0028` — letter/document status and reported claim.
5. `jekyll-sample-v2:section-003:b0024` — Jekyll's guarded knowledge without identity disclosure.

The unchanged source blocks and entity ledger are recorded in `artifacts/jekyll-authenticated-provider-gate-v5/provider-gate.json`.

## Required rerun condition

Run the same gate from an environment with DNS/egress access to `api.openai.com`, preserving the existing key boundary and model configuration. Then run the five-block smoke, and only on smoke pass the exact 40-block regression and downstream QA.

## Controls preserved

The public translator is unchanged. No full-book translation, layout, publication, or public artifact was produced.
