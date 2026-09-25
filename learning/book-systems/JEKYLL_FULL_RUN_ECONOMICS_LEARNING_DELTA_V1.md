# Jekyll Full-Run Economics Learning Delta V1

Date: 2026-09-23

## Observation

The 462-block Jekyll primary run retained 351 successful GPT-5.6 Sol checkpoints and 111 failures after a generic HTTP 429 at chapter 10, block 14. The owner reported the API balance fell from above $7 to -$0.29. The artifact did not retain the provider error code, so exact quota-vs-rate-limit classification is not possible after the fact. The old runner continued across all remaining blocks after the first exception.

Measured successful usage was 986,926 input tokens, including 985,873 cache-write tokens and zero cached-input tokens; 154,949 output tokens, including 102,724 reasoning tokens; and 126,579 visible translation characters. Current official GPT-5.6 Sol rates reprice these successful calls at about $8.03. The modelled 25,622-word primary cost is about $10.66. The prompt repeated a 9,582-character 24-entry entity ledger; source text averaged 55 words while full input averaged 2,812 tokens. No exact target-only token count or invoice was retained.

## Interpretation

Technical reliability and semantic consistency did not guarantee economical execution. The run optimized completion quality but had no project-level cost preflight, no hard call/token ceiling, and no immediate stop on a persistent account-level error. The repeated ledger and prompt ordering were also inefficient: variable block metadata came before the large reusable ledger, while retained usage showed no cache reads. A smaller model, larger blocks, batching, or a reduced entity subset may lower costs but can alter semantic fidelity, name consistency, alignment, or spoiler handling.

## Practice candidate

Before any large translation run, create a cost preflight with source/block scope, request and token estimates, current official pricing, primary and QA/second-pass cost, verified balance or `UNKNOWN`, owner-approved ceiling, and hard `--max-calls` plus cumulative token caps. On persistent quota/auth/account/model/unknown-429 errors, stop immediately; for explicit transient failures, retry only a bounded number of times and pause if they persist. Store provider/model/prompt version/prompt hash/config per newly generated block. Keep existing successful outputs untouched when evaluating a new prompt/model.

## Next test

If separately authorized: first run a capped, representative prompt-cache or entity-subset pilot; independently test 100–200-word semantic segmentation and 5-block structured batching; compare one cheaper candidate on 10–20 existing Sol blocks. No such test is authorized or executed here. For the current remaining 111 blocks, unchanged Sol prompt/config is the strongest comparability option; compact prompt is conditional on regression; cheaper-model routing is not supported by the current `UNKNOWN_AMBIGUOUS` source-function metadata.

Evidence and structured calculations: [cost postmortem](../../artifacts/jekyll-toki-pona-full-v1/JEKYLL_FULL_RUN_COST_POSTMORTEM_V1.md), [economics JSON](../../artifacts/jekyll-toki-pona-full-v1/JEKYLL_TRANSLATION_ECONOMICS_V1.json), [remaining-work options](../../artifacts/jekyll-toki-pona-full-v1/JEKYLL_REMAINING_111_COMPLETION_OPTIONS_V1.md).
