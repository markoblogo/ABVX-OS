# Remaining 111 Jekyll Blocks — Completion Options

Status: analysis only. No API calls, top-up, or translations authorized by this audit. The reported API balance is -$0.29, so every live option remains stopped pending an owner-authorized balance and spending ceiling.

## Ranked options

### 1. Unchanged Sol, unchanged prompt, same 111 IDs — safest known baseline

- Primary estimate: **$2.54** using the observed Sol usage profile.
- With one full Sol-sized second pass on all 111: planning total **about $5.08**; targeted second pass on the 56 generic spoiler-flagged blocks: **about $3.82** primary + QA proxy.
- Implementation: none beyond the runner safety/provenance changes. Per-block comparability with the existing 351 is highest.
- Risk: lowest model/prompt drift; still requires ordinary editorial/semantic QA. Use new `--max-calls` and at least one token cap.
- Current decision: only path supported without an untested model or prompt. Do not run until separately authorized.

### 2. Same Sol, target/neighbor entity subset — lower cost, needs a prompt regression

- Primary estimate: **about $1.76** for 111, a character-proportional estimate retaining all nine complete spoiler-critical ledger entries.
- With QA on 56 flagged blocks at the primary-call proxy: **about $3.04** combined.
- Implementation: low/medium. Keep source block IDs; attach a prompt version and exact per-block prompt hash. Do not mutate old 351 records.
- Risk: medium. Smaller entity context must be checked for name consistency and inference/spoiler leakage. A changed prompt must pass a bounded regression before production scale.
- Comparability: same model and IDs, changed prompt; not directly identical to the original 351 protocol.

### 3. Batch five blocks per Sol request — possible repeated-context savings, higher alignment risk

- Approximate calls: 23 instead of 111; primary estimate **about $1.34** before output-format overhead.
- Implementation: medium. Require machine-checkable `BLOCK_ID` + translation mapping, all-or-nothing validation, and per-block provenance/checkpoint extraction.
- Risk: high: one response failure can affect five blocks; alignment drift, cross-block inference, and spoiler leakage become harder to isolate.
- Comparability: lower; one request now shares context across blocks. Requires a small local/mock contract test and an approved provider pilot before use.

### 4. Batch ten blocks per Sol request — lowest batch estimate, not recommended first

- Approximate calls: 12; primary estimate **about $1.21** before output-format overhead.
- Risk: very high. Average observed output usage projects to roughly 4,400 total output tokens per 10-block response, above the current 3,000-token primary cap. Raising the cap and handling partial structured output adds failure/retry surface.
- Use only after a five-block pilot proves alignment, mapping, and resume semantics.

### 5. Cheaper primary model with Sol QA — lowest model-cost hypothesis, not yet safe

At current official short-context rates, holding Sol's token counts constant, 111 primary calls project to: GPT-5.6 Terra **$1.37**, GPT-5.6 Luna **$0.14**, GPT-6 Luna **$0.064**. Add a Sol-sized QA pass on all 111 (about **$2.54**), and the rough primary+QA totals become $3.91, $2.68, or $2.60 respectively. Output/reasoning usage and quality may differ, so these are not quotes.

- Implementation: medium; use explicit model/prompt/config/hash per block and retain the 351 Sol outputs unchanged.
- Risk: high until a 10–20-block regression compares semantic fidelity, review burden, completion, literary quality, and cost.
- Current metadata does not provide a reliable low-risk routing set: all 111 are in the first-person statement chapter and all knowledge states are `UNKNOWN_AMBIGUOUS`. Fifty-five lack the generic spoiler flag, but that does not establish narrator-fact status.
- The requested regression is designed by this option but **not run**.

## Block size and shared input

The remaining 6,228 words yield naive counts of 63 / 42 / 32 calls at 100 / 150 / 200 words per semantic block, respectively, versus 111 now. Whole-source arithmetic gives 257 / 171 / 129 instead of 462. Real counts will be higher if dialogue, document, knowledge-state, spoiler, or alignment boundaries require splits. Larger blocks reduce repeated fixed input but may raise response-length/truncation and review risks. Do not merge or resegment any of the successful 351.

For batching, the fixed instructions + ledger are about 95.7% of prompt characters; block text and block-specific metadata remain per-block. Under the simple character-proportional model, a 5-block request pays about 23.5% and a 10-block request about 13.9% of current input tokens per block. The output side is not reduced. These estimates exclude IDs, structured wrappers, larger output caps, and errors.

Prompt caching is a separate option: the current prompt's stable text is only 626 characters before variable block metadata; the 9,582-character full ledger comes after it. OpenAI documentation says GPT-5.6+ requires an exact reusable prefix of at least 1,024 visible tokens. Reordering stable instructions and ledger ahead of variable fields may enable cache reads, but no local evidence shows a cache hit in either this full run or the retained V7 40-block run. Do not budget cache savings until an authorized pilot records `cached_tokens` and `cache_write_tokens`.

## Cost preflight before any completion

The preflight must record:

1. Remaining source words/blocks, selected strategy, estimated calls, and retry allowance.
2. Input/output token assumptions and current official rates for the exact model, including cache-write pricing and reasoning billed as output.
3. Primary, regression, semantic-QA, and targeted second-pass estimates.
4. API balance only if directly verified; otherwise `UNKNOWN`. Never infer it from past spend.
5. Owner-approved dollar ceiling, `--max-calls`, and at least one cumulative usage cap: `--max-input-tokens` or `--max-output-tokens-total`.

The runner stops when a persistent provider error is received. Explicit transient rate limits/network/server errors get at most three attempts and then pause. Token caps are checked against observed usage after each response, so they may overshoot by one call; max-calls is an exact request ceiling. The live runner now refuses to run pending blocks without a call ceiling and at least one cumulative token ceiling.

**Recommendation:** do not select a completion path today. If a future authorized run prioritizes comparability, use option 1. If reducing fixed prompt cost matters and a bounded regression passes, option 2 is the lowest-risk optimization. Do not choose a cheaper model or batch solely from arithmetic.
