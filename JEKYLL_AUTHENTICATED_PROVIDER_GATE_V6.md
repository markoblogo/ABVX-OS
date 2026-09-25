# Jekyll Authenticated Provider Gate V6

Date: 2026-09-23

## Result

- Auth: `PASS`
- Provider: OpenAI Responses API
- Model: `gpt-5.6-sol`
- Real provider: `CONFIRMED` from retained local diagnostic evidence and the successful retry.
- Original smoke: 3 completed / 2 incomplete.
- Failed blocks retried: `b0005`, `b0028` only.
- Retry: `reasoning=low`, `max_output_tokens=3000`; both completed with visible output and no incomplete details.
- Five-block completion: 5/5 technically complete.
- Provider smoke: `PASS_WITH_REVIEW`, not unconditional PASS.
- Production reasoning: `LOW_CANDIDATE_UNRESOLVED`.
- 40-block regression: not run.
- Full book: not translated.

## QA

`b0024` passes semantic smoke. The other four are `PASS_WITH_REVIEW`: the translations preserve the tested control boundary sufficiently for a regression continuation, but need independent editorial review for compression, exact three-month conditionality, time phrasing, name policy, and document-claim wording. Provider NOTES were not accepted as evidence.

The canonical mixed-configuration smoke is [JEKYLL_5_BLOCK_REAL_SMOKE_V1.json](artifacts/jekyll-authenticated-provider-gate-v5-debug/JEKYLL_5_BLOCK_REAL_SMOKE_V1.json). It preserves response IDs, usage, status, visible output, and per-block configuration history.

## Decision

`PROCEED_TO_40_BLOCK_REAL_REGRESSION` is authorized only as the next bounded step, not full-book production. The 40-block runner must use low reasoning / 3000 by default, checkpoint every block, resume by source hash, reject empty or incomplete responses, and allow one bounded larger-budget retry for max-token failures.
