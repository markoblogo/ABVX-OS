# Jekyll Real-Provider Regression V3

## Decision

**MODIFY_PROVIDER_AND_RERUN**

The existing trusted internal model path was located: `abvx-local-model-worker` at `http://127.0.0.1:8766/v1/answer`, model default `occ-ai/OCC-RAG-0.6B`. A real adapter was added without changing the public translator or routing through its endpoint. The exact Jekyll sample was segmented into 40 blocks and the first real-provider request was attempted.

The worker was not running: the local probe returned connection failure. Therefore no fixture output was counted as real-provider evidence and no semantic regression claim was made.

## Provider

- Provider: `abvx-local-model-worker`
- Model: configurable via `ABVX_LOCAL_MODEL_ID`, default `occ-ai/OCC-RAG-0.6B`
- Endpoint: configurable via `ABVX_LOCAL_MODEL_URL`, default localhost worker
- Contract: bounded source block plus context/rules; output must be target block only
- Attempt: failed at block `jekyll-sample-v3:section-001:b0001` with `PROVIDER_UNAVAILABLE`

## Exact Sample

The source is unchanged from V1/V2: Chapters II, VI, and VIII representative sample. V1 and fixture-backed V2 remain preserved. V3 source blocks are in `artifacts/jekyll-toki-pona-regression-v3/source-blocks.json`.

## Provider Prompt Contract

The adapter prompt prioritizes meaning, knowledge state, plot logic, speaker identity, uncertainty, readable Toki Pona, and stylistic compression. It explicitly prohibits claim→fact, possibility→certainty, opinion→narrator fact, condition→unconditional event, question→statement, and fear→observed event. Neighboring context is labelled non-translatable; the target block is identified by stable ID.

## Machine Run

The run manifest and provider attempt are preserved in the V3 artifact directory. Because the worker was unavailable, alignment, name, knowledge, spoiler, sitelen, and layout stages were not executed on V3 output. This is a fail-closed result.

## Known-Failure Matrix

No V3 output exists, so the semantic matrix is **NOT RUN**, not “fixed.” The matrix from V2 remains the review baseline. A valid V3 run must reassess unexplained absence, conditional succession, Utterson judgement, Lanyon opinion, safe/escape, grounds for certainty, trust/confidence, lead/move, laboratory/cabinet, names, Poole fear, and identity/spoiler.

## Second Pass

Not run. The second-pass mechanism remains available in the pipeline design, but must only operate on real provider output blocks flagged by QA.

## Review Burden

Measured real-provider review burden: unavailable. The run stopped before the first completed block. No estimate is substituted for an observation.

## Sitelen / Layout

No V3 layout PDF was generated because there was no V3 translation output. The V2 PDF remains the last valid layout proof. This prevents a fixture-backed PDF from being mistaken for a real-provider regression.

## Public Translator

`PUBLIC_DEPLOYMENT_SEPARATE`. The public translator was not modified and no internal mode was exposed anonymously. Its separate deployment can be repaired or retired under its own gate.

## Full-Book Estimate

The canonical source is 25,622 words. After a successful provider run, expected block count must be measured from the actual segmentation (the 1,785-word sample produced 40 blocks). A provisional scale estimate is approximately 575 blocks at the same density, with one provider call per block plus retries. Review burden cannot responsibly be estimated until real output exists.

## Remaining Blockers

1. Start or repair the trusted local model worker, or approve another existing internal provider path.
2. Rerun the unchanged sample and record provider/model/run metadata.
3. Complete semantic matrix, second-pass revision measurement, sitelen, and V3 layout QA.

## Regression Decision

**MODIFY_PROVIDER_AND_RERUN.** This is a finite provider-availability blocker, not a product rejection. No complete Jekyll translation, final paperback, Kindle package, cover, KDP metadata, publication, or upload was started.
