# Jekyll Full Run Cost Postmortem V1

Date: 2026-09-23. No provider calls or translations were made during this audit.

## Finding

The run has 351 usable, source-hash-matching GPT-5.6 Sol primary checkpoints and 111 failed/untranslated blocks. The first recorded failure is chapter 10, block 14, HTTP 429. The old runner logged only the generic HTTP status, then continued its outer block loop, producing 110 more failed calls. Owner-reported account balance moved from above $7 to -$0.29; that strongly supports credit/quota exhaustion, but the old artifact cannot distinguish `insufficient_quota` from a transient `rate_limit_exceeded` because it did not retain the response code/body.

The 351 completions remain valid and resume-compatible. None were overwritten, regenerated, invalidated, or resegmented. The exact current remainder is 111 blocks / 6,228 English source words.

## Cost

Retained usage from the 351 successful responses is 986,926 input tokens (985,873 cache writes, zero cache reads), 154,949 output tokens (102,724 reasoning tokens included), 1,141,875 total tokens, and 126,579 visible translation characters. The separate usage summary had zero token totals; summing per-block Responses usage repaired this reporting gap in the runner.

At official GPT-5.6 Sol short-context rates verified 2026-09-23—$4/M ordinary input, $0.40/M cached input, $5/M cache writes, $20/M output—the retained success usage reprices to **$8.03**, about **$0.023 per successful block** or **$0.416 per 1,000 source words**. The measured-unit projection is **$10.66 for the 25,622-word source** and **$10.40 for a 25,000-word book**. The owner's approximate balance report implies more than $7.29 was spent; it is corroborative, not an exact invoice.

Remaining primary-call projections from that actual Sol profile: unchanged Sol **$2.54**; compact target/neighbor entity ledger on Sol **about $1.76** (requires regression); GPT-5.6 Terra **$1.37**, GPT-5.6 Luna **$0.14**, GPT-6 Luna **$0.064** (model quality untested); 5-block batch Sol **about $1.34**, 10-block batch **about $1.21** (alignment/failure risk, and 10-block average output exceeds the current 3,000-token response cap). Every alternative is a usage-based estimate, not an invoice or quality verdict.

## Economics diagnosis

The target is only about 55 words per call. Average request usage was 2,812 input tokens. Exact target-only token counts are unavailable; a character-proportional estimate assigns about 78 tokens to the target. The full 24-entry, 9,582-character ledger is about 89.8% of average prompt characters and was repeated on every block. Variable block fields appear before the ledger, so its long content could not be reused as a stable prefix. Both this run and the retained V7 40-block usage records show zero cached input tokens; cached-input savings were not observed.

An offline deterministic subset simulation—target entities + previous/next same-chapter entities + full records for all nine spoiler-critical entities—reduces ledger size by 55.6%, and full prompt characters by about 49.9%. Projected saving: about 1,404 input tokens/request, 493k tokens across 351 requests, or about $2.46 at observed cache-write rates. A different prompt version must not be silently mixed into this run.

The remaining work is all Chapter 10, “Henry Jekyll’s Full Statement of the Case.” Its current metadata has 104 `NARRATION`, 7 `DOCUMENT`, 56 generic spoiler constraints, and `UNKNOWN_AMBIGUOUS` knowledge state for all 111. Because it is one first-person statement, existing tags do not establish low-risk narrator facts. No block is currently proven safe for cheaper-model routing.

**Pipeline economics status: UNACCEPTABLE as an ungated run.** The token spend itself is modest in absolute USD, but the job was launched without a cost ceiling against an available balance below the projected full-run amount, and the persistent error caused 110 avoidable follow-up calls. Technical completion/semantic reliability did not imply economical execution.

## Changes and gates

The runner now classifies quota, auth/account, unsupported-model, transient rate-limit, network/server, and unknown errors using only safe HTTP status/type/code metadata. Quota and unknown 429 errors stop immediately. Explicit transient 429s and transient network/server errors get at most three attempts; if exhausted, the run pauses. Future live runs require `--max-calls` and at least one cumulative input/output-token cap. A token cap may overshoot by one request because actual usage arrives after the response; `--max-calls` remains the request hard limit.

The safest supported completion path is **not to resume now**. After an explicitly approved balance and ceiling, use the unchanged Sol model/prompt/IDs with the caps, at about $2.54 primary cost. A prompt-reduced Sol path is about $1.76 but needs a bounded regression first. Do not top up, resume, change model, batch, resegment, generate sitelen, or build the book without separate authorization.

Detailed calculations and remaining-work ranking: [economics JSON](JEKYLL_TRANSLATION_ECONOMICS_V1.json), [completion options](JEKYLL_REMAINING_111_COMPLETION_OPTIONS_V1.md), [detailed cost audit](JEKYLL_FULL_RUN_COST_ECONOMICS_AUDIT_V1.md). Book Factory learning is appended as [BSL-019](../../learning/book-systems/JEKYLL_FULL_RUN_ECONOMICS_LEARNING_DELTA_V1.md).

## Verification

- Focused Jekyll runner tests: pass (10).
- Full suite: pass (210 tests).
- `./bin/abvx validate`: PASS (rerun after the final edits).
- No API calls. No existing successful block or failed historical record changed. No commit made.
