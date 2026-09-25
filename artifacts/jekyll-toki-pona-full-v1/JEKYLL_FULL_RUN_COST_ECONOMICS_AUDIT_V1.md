# Jekyll Full Run — Cost Failure and Economics Audit

Audit date: 2026-09-23  
Scope: retained local artifacts and runner behavior only. No API calls were made; no translation was resumed.

## Executive result

- The 351 successful checkpoints remain resume-compatible: each matches the canonical block ID and source hash. The other 111 blocks have no successful checkpoint; expected remaining work is 111.
- The first recorded error is `jekyll-full-v1:chapter-10:block-0014`: HTTP 429, `Too Many Requests`. The old record did not retain the response body or provider error code. The owner's report that the API balance moved from over $7 to -$0.29 strongly supports credit/quota exhaustion, but the stored artifact alone cannot distinguish quota exhaustion from a transient rate limit.
- The old runner caught an exception inside the per-block attempt loop, then continued its outer loop over the remaining blocks. That is why it issued the other 110 failed calls.
- Runner failure handling now extracts only safe status/type/code metadata, immediately stops on quota, billing, authentication, account, model, other non-retryable, or unknown 429 failures, and gives explicit transient rate limits/network failures at most three attempts before pausing the run. A stopped run records the unattempted count. Existing checkpoints were not changed.

## Checkpoint and usage reconciliation

The segmentation manifest contains 462 blocks for a 25,622-word normalized source. There are 462 per-block records: 351 successful and 111 failed. All 351 successes pass the current resume predicate (`success` plus matching `sourceHash`); no checkpoint was regenerated or invalidated.

Retained successful-response usage, summed from the 351 block files:

- Successful blocks: 351; API calls: 462 total, including 111 failed calls; retries: 0.
- Successful source words: 19,306; average per successful block: 55.0 words.
- Input tokens: 986,926, of which 985,873 were cache-write tokens and 0 were cached-input tokens; ordinary uncached/non-write input: 1,053.
- Output tokens: 154,949; reasoning tokens: 102,724, included within output tokens rather than an additional billed category.
- Total tokens: 1,141,875 (input + output; reasoning is a subset of output).
- Visible translation characters: 126,579.

Failed calls have no retained response usage. The old `usage-summary.json` reports zero token totals even though successful block records retain usage; the checkpoint records are therefore the usage source of truth. The updated runner now aggregates input, cached input, cache writes, output, reasoning, retries, and visible translation characters for future runs.

## Cost estimate

OpenAI's current official GPT-5.6 Sol pricing lists short-context rates of $4/M input, $0.40/M cached input, $5/M cache writes, and $20/M output. Cache writes are priced at 1.25× uncached input; reasoning tokens are billed as output tokens ([model pricing](https://developers.openai.com/api/docs/models/gpt-5.6-sol), [API pricing](https://developers.openai.com/api/docs/pricing), [reasoning-token billing](https://developers.openai.com/api/docs/guides/reasoning)). The observed prompts are far below the long-context threshold.

Applying those current rates to retained successful usage—not claiming this is an invoice—gives:

- Ordinary input: 1,053 × $4/M = $0.0042.
- Cached input: 0 × $0.40/M = $0.0000.
- Cache writes: 985,873 × $5/M = $4.9294.
- Output, including reasoning: 154,949 × $20/M = $3.0990.
- Total input-side cost, including cache writes: $4.9336.
- Estimated total for 351 successful blocks: **$8.0326**.

This is about **$0.0229 per successful block**, **$0.416 per 1,000 English source words**, and **$4.161 per 10,000 words**. Linear projections from the observed successful blocks are **$10.66 for the 25,622-word Jekyll source** and **$10.40 for a 25,000-word future book**, before retries, QA, or rework. These are projections, not budgets or guarantees.

The owner-reported balance change (starting above $7, ending at -$0.29) implies a spend greater than $7.29. That supports the order of magnitude of the token-based estimate. It cannot reconcile to the cent because the opening balance was approximate, and no billing ledger was inspected. Failed-call charges are also not inferable from their local records.

## Prompt-overhead findings

Each successful block averaged 2,812 measured input tokens to translate 55 source words (about 298 source characters): 51.1 billed prompt-input tokens per source word. Exact source-only tokenization was not retained and no local GPT tokenizer is installed, so any component token split is an estimate. A character-proportional estimate assigns roughly 78 of the 2,812 input tokens to target text—about 2.8%; the rest is instructions and context.

The prompt repeats the actual full 24-entry ledger from `artifacts/jekyll-toki-pona-regression-v2/entity-name-registry.json` in every request: 9,582 characters / about 1,011 whitespace-delimited words, about 89.8% of prompt characters. Static translation instructions are about 626 characters; chapter/block metadata and constraints average about 164 characters. The target averages about 298 characters. The prompt layout places variable chapter/block data before the ledger, so the long ledger is not part of the repeated identical prefix. Retained usage shows 985,873 cache-write tokens and zero cache reads; the full-run records therefore show no realized cache-read savings. The retained V7 40-block usage summary also reports zero cached input tokens, despite the attached task's note that some V7 calls cached input; that note is not reproducible from the local V7 checkpoints available here.

### Deterministic subset estimate

Offline simulation over all 462 source blocks used: exact entity aliases present in the target; aliases in the immediately preceding/following block in the same chapter; and the complete entries for all nine spoiler-critical entities. This conservative policy selects an average of 10.3 of 24 entries and reduces repeated ledger text from 9,582 to about 4,254 characters (55.6%). On character-proportional allocation, that is about 49.9% of the full prompt and roughly 1,404 input tokens saved per request, or about 493,000 tokens across 351 successful-sized requests. At the observed cache-write rate that would be approximately $2.46 saved on those 351 requests; a full-book-sized projection is about $3.27. Token/cost savings are estimates because the API does not provide per-prompt-component token attribution.

Do not apply this prompt change to the existing run: resuming with a changed prompt would mix prompt versions in one translation. Before a future run, version a prompt that uses target + adjacent context + global spoiler guard, and record its prompt hash in every checkpoint. Consider keeping global spoiler rules compact rather than repeating all nine full critical-entity records.

## Static contract, blocks, batching, and cache

The invariant instruction text is 626 characters, about 5.9% of prompt characters. It can be rewritten into a compact versioned contract, but is a smaller cost target than the ledger. Preserve its safeguards: epistemic source/modality, uncertainty and conditions, speaker/document status, temporal/character relations, and spoiler boundary. Some repeated rules are already represented by per-block fields, but all current `knowledgeType` values are `UNKNOWN_AMBIGUOUS`, `speaker` and `entities` are empty, and the generic spoiler flag is coarse. Do not remove a safeguard on the assumption that current metadata replaces it. Local profile/config storage improves maintainability but does not itself remove request tokens.

The 2026-09-23 official prompt-caching guide says GPT-5.6+ needs a matching reusable prefix of at least 1,024 visible tokens; reuse is exact-prefix and setting dependent. Here, the stable prose is only 626 characters, followed by variable chapter/type/constraint fields, with the large ledger after those fields. That ordering cannot present the large common ledger as an identical prefix. The 0 cached tokens in both retained full-run and V7 usage corroborate the absence of observed cache reads. Reordering stable contract + global profile/ledger before variable block data should make a cache pilot possible, not guarantee a hit. Record `cached_tokens` and `cache_write_tokens` in that pilot. See [OpenAI prompt-caching guidance](https://developers.openai.com/api/docs/guides/prompt-caching).

The 25,622-word source divided mechanically gives approximate block/call counts of 257 at 100 words, 171 at 150, and 129 at 200, versus 462 now (44%, 63%, and 72% fewer calls). For the remaining 6,228 words, the arithmetic is 63, 42, or 32 calls versus 111. These are lower-bound estimates: semantic boundaries, dialogue, documents, and alignment can increase them. Larger coherent blocks amortize fixed instructions/metadata/ledger input; total translation output should remain roughly source-proportional, but longer outputs increase truncation/retry and alignment risk. Do not resegment the existing 351 records.

Batching 5 or 10 source blocks per provider request would reduce the repeated fixed prompt. A character-based estimate (fixed instruction + ledger shared once, target and per-block metadata still repeated) reduces input tokens to about 23.5% or 13.9% of current for those calls, with same output usage; estimated Sol primary cost for 111 blocks becomes about $1.34 or $1.21 rather than $2.54. These estimates exclude block-ID/schema overhead. Five-block output averages roughly 2,200 total output tokens using the observed profile and may fit the current 3,000 cap; ten averages roughly 4,400 and would need a higher cap. Batch failure affects 5–10 translations at once, and exact output-to-source mapping, cross-block leakage, and resumability become new risks. Treat batching as a prototype, not the preferred completion path.

## Model comparison and remaining-work economics

Current official standard short-context API prices applied to the observed token profile (same usage assumed; no quality claim):

- GPT-5.6 Sol: $8.03 / 351 calls; $2.54 / remaining 111.
- GPT-5.6 Terra: $4.33 / 351; $1.37 / 111.
- GPT-5.6 Luna: $0.43 / 351; $0.14 / 111.
- GPT-6 Luna: $0.20 / 351; $0.064 / 111.

These projections use the same 2,812 input and 441 output tokens per block as Sol. Models can use different reasoning/output tokens and produce different quality. Sol is not established as economically necessary for all primary blocks, but neither Terra nor Luna is established as equivalent. A future 10–20-block candidate-model comparison can reuse existing Sol translations as references; at listed rates, candidate-generation inference for that many blocks would be under $0.02 even for GPT-5.6 Terra (excluding QA and evaluation). Do not run this comparison until authorized.

The remaining 111 blocks contain 6,228 words and all belong to Chapter 10, “Henry Jekyll’s Full Statement of the Case.” Saved metadata says 104 `NARRATION`, 7 `DOCUMENT`, 56 generic spoiler-constrained, 0 dialogue; all 111 have `knowledgeType=UNKNOWN_AMBIGUOUS`. Because the whole chapter is a first-person statement/document context, its `NARRATION` tag does not prove narrator-fact status. The metadata cannot safely route any block to a cheaper model automatically yet. Fifty-five blocks lack the generic spoiler flag, but should be treated only as candidates for a human-reviewed regression set, not certified low-risk work.

At current per-call usage, finishing only the remaining 111 with unchanged Sol costs about $2.54. A same-Sol target/neighbor ledger prompt is about $1.76 by the character-proportional estimate, but it is a material prompt change and requires a bounded regression before use. Targeted Sol QA on the 56 flagged blocks costs about $1.28 at the primary-call cost proxy; QA on all 111 costs about $2.54. A QA prompt will differ, so these are planning proxies, not quotes. A candidate-model primary plus Sol QA on all blocks would project about $2.60 with GPT-6 Luna primary, or about $2.68 with GPT-5.6 Luna primary; quality and prompt effects are untested. The “cheapest safe” option currently supported without a model or prompt regression is unchanged Sol on remaining IDs, $2.54 primary, under cost preflight and the new call/token caps.

## Factory learning and cost preflight

This run demonstrates: **technically reliable does not imply economically efficient**. Completion and semantic reliability were optimized; estimated whole-book cost, available balance, and a persistent-provider-error stop were not gated. This is recorded as the Book Factory learning delta `BSL-019`.

Before a future large API job, require a cost preflight record containing: source words/blocks; estimated request count and retries; observed or estimated input/output tokens; current official model and cache-write/read prices; projected primary, QA, and targeted second-pass costs; available balance only if verifiably known; owner-approved ceiling; and the runner's call/token caps. The runner now requires `--max-calls` plus at least one cumulative input/output token cap for a live run. Usage is learned after each response, so a token cap can overshoot by at most one call; max-calls is the hard request ceiling. An absent or negative known balance is a stop, not an auto-top-up trigger.

See [structured economics](JEKYLL_TRANSLATION_ECONOMICS_V1.json), [remaining-111 options](JEKYLL_REMAINING_111_COMPLETION_OPTIONS_V1.md), and [factory learning delta](../../learning/book-systems/JEKYLL_FULL_RUN_ECONOMICS_LEARNING_DELTA_V1.md). No model was changed, and no provider run, regression, translation, illustration, or book build was started.

## Failure-policy change and tests

The updated runner stores only HTTP status, normalized provider error type/code, classification, and retry number—never the raw error body/message. Explicit `rate_limit_exceeded` remains `TRANSIENT_RATE_LIMIT`; explicit quota/billing errors are `PERSISTENT_QUOTA`; an unclassified 429 fails closed as `PERSISTENT_UNKNOWN_429`. Authentication/account and unsupported-model errors hard-stop. Transient network/rate-limit/server errors get bounded retries and pause the run if exhausted. Resume continues to skip successful matching checkpoints.

Focused tests cover quota classification and safe metadata, transient 429 distinction, fail-closed unknown 429, auth/model hard stops, and actual outer-loop stopping after a persistent quota error. No live provider call is part of tests.

## Economics actions for the next authorized run

1. Keep hard-stop behavior; add an explicit owner-controlled spend/call ceiling before any production run. Do not infer remaining API credit from local usage.
2. Prototype semantically coherent larger blocks (for example 200–300 source words) against the existing quality regression before full production. Fewer requests reduce repeated fixed prompt and cache-write overhead, but do not merge across dialogue, document, or knowledge-boundary changes.
3. Replace the full repeated entity ledger with a versioned target/neighbor subset and compact global spoiler guard. Preserve full ledger as source-of-truth outside per-block prompts.
4. Put stable instructions and compact global policy first, before dynamic chapter/block fields, then verify actual `cached_tokens` in a small approved run; do not assume prefix caching will work.
5. Treat a cheaper model as a bakeoff candidate only. Translation quality, narrative knowledge state, and spoiler handling must pass the existing regression before cost becomes the deciding factor.

No model, prompt, block segmentation, or production artifact was changed as part of this economics audit. The only behavior change is safe failure classification/stopping and complete usage aggregation for a future authorized run.
