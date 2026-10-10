# Phocinae on this Mac — isolated pilot, 2026-10-10

**Decision: keep Phocinae outside the OS/Cortex routing path.** The model runs quickly once loaded, but its current out-of-domain routing and yes/no reliability do not qualify. Deterministic rules already solve the tested structured decisions with much lower overhead. Weights and the isolated environment remain available for reproducible experiments; no model service, training, core dependency change or Cortex activation occurred.

## Device and pinned inputs

- Apple M4, 10 CPU cores, 16 GiB memory, arm64, macOS 26.6.2.
- Model v1.1 revision `5300e85a7d991f4f0cdb68dc25813f76902752d4`; runtime `705508c33f185aee6a838379502e7a87caa0e138`. Runtime version metadata 0.1.5; package `__version__` remains 0.1.0, so the commit is the identity.
- Weight SHA-256 verified against the author: `b6472511eea30729985374f43968cf7f4b16bbe0827de6c6ca07cf92afbb778a`.
- 144,292,867 loaded parameters; 288,603,268-byte FP16 checkpoint. The official engine uses FP32 on CPU and MPS.
- Python 3.12 / PyTorch 2.8.0 / NumPy 2.3.3 in a separate environment. Dependency check passed. Model files approximately 322 MiB; environment approximately 544 MiB. Exact dependencies and every downloaded file digest are retained locally.
- Apache-2.0 model/runtime with MIT base notice inspected. Only the reviewed engine/model/tokenizer/safetensors path was imported. No Transformers remote code, pickled checkpoint or server install/start was used. Python socket connection/bind and process-launch events were denied during inference; only model/runtime/dependency download stages used network access.

## Performance

| Measurement | Observed result |
| --- | --- |
| CPU, 4 threads, one warm choice request | p50 30.0 ms; maximum of 8 calls 34.5 ms |
| CPU, five typed questions in one request | p50 113.1 ms; maximum of 8 calls 137.3 ms |
| CPU thread-count probe: 1 / 4 / 8 | p50 45.1 / 30.4 / 32.0 ms |
| Metal MPS FP32, same one-choice request | p50 33.1 ms; maximum of 8 calls 106.9 ms |
| First CPU process: import / engine load / first request | 28.60 / 10.50 / 1.59 s |
| Separate CPU restart: import / engine load / first request | 6.72 / 11.52 / 0.97 s |
| Separate MPS process: import / engine load / first request | 6.67 / 12.07 / 6.41 s |
| Observed CPU process peak RSS | 1.32–2.02 GB |
| MPS process peak RSS | 2.00 GB; GPU unified-memory allocation not independently measured |
| Structured-rule function, 7,200 calls | median below 0.001 ms; timing noise dominates this trivial in-process function |

All latency includes tokenizer, model forward and decoding. Performance requests are short, repeated states; the held-out requests used at most 167 encoded tokens. This is not a long-document or throughput benchmark. Eight samples give a descriptive maximum, not a robust tail-latency estimate. Background workload, thermal state and OS filesystem cache were not controlled. MPS required a permitted local GPU probe because the default sandbox reported it unavailable; the GPU run stayed offline. GPU quality was not separately evaluated. Starting a new Python process per decision would pay the startup/load cost and erase the warm-latency advantage.

## Frozen OS-specific evaluation

72 synthetic cases were frozen before inference: 8 calibration families × EN/RU/UK = 24 cases; 16 separate held-out families × EN/RU/UK = 48 cases. All translations of a family stay within one split. Labels are agent-authored from explicit OS policy, not owner-labelled production outcomes; language variants are correlated. No benchmark author's training/test data, real manuscripts, customer data, credentials or personal OS history were used.

Four routes: reuse a verified playbook; retrieve missing evidence; request review-only local model analysis; obtain owner review. Each case contains the same explicit structured flags for both the rule baseline and the model, alongside translated prose. Model options use descriptive labels. This is an evaluation of this candidate adapter and domain, not all possible Phocinae uses.

| Language | Correct held-out cases | Accuracy |
| --- | --- | --- |
| EN | 13/16 | 81.25% |
| RU | 11/16 | 68.75% |
| UK | 10/16 | 62.50% |
| Combined | 34/48 | 70.83% |
| Structured rules, same recorded flags | 48/48 | 100% |

By route, the model was correct for reuse 2/12, missing evidence 8/12, local analysis 12/12, owner review 12/12. Without a confidence gate it suggested 18 LLM-analysis routes where the policy calls for 12; this is a route-count diagnostic, not actual measured LLM cost or saved owner time. The rules are deliberately narrow and exact; their 100% result does not establish free-text understanding.

## Confidence, stability and typed decisions

Threshold selection was locked using only the 24 calibration cases. The predeclared gate required at least six accepted calibration cases with ≥95% accepted accuracy; none of thresholds 0.5/0.6/0.7/0.8/0.9/0.95/0.99 qualified. Consequently the qualified router accepts zero held-out cases and escalates all 48; no useful LLM-call reduction is established.

For descriptive comparison only, the author's fixed 0.6 threshold accepted 1/48 held-out cases, correctly. That case already required owner review under deterministic policy, so it creates no useful shortcut after mandatory policy checks. This threshold was not chosen from held-out results and is not enabled.

Reversing the four option descriptions changed 4/16 English held-out decisions. This protocol differs from the author's benchmark and cannot be compared numerically with its flip score.

A separate, uncalibrated yes/no probe matched 7/12 explicit statement/evidence labels (58.33%). Two incorrect negatives exceeded 0.6 confidence. This small supplementary probe is not a production accuracy estimate, but it is insufficient evidence for a general yes/no gate. Score output stayed in the specified 2–10 range; score accuracy was not tested because no independently grounded ordinal rubric was supplied.

The published upstream example was reproduced exactly: answers `false / option 0 / score 3`, confidences `0.668 / 0.409 / 0.1633`, input tokens 146, output tokens 0. Together with the verified weight digest this provides a useful loader/runtime compatibility check; it does not qualify our task routing.

## Recommendation and next gate

1. Retain deterministic checks for structured OS fields; they handle this use case more cheaply and reliably.
2. Keep local model synthesis optional for genuinely unresolved analysis. Confidence never grants execution or approval.
3. Do not enable Phocinae automatically, and do not train on this held-out set. A later specialised NLP task needs its own owner-reviewed labels, calibration split and unseen acceptance set. Fine-tuning or a new adapter is a separate experiment, not a remedy assumed to work.

The current gate (≥95% accepted held-out accuracy, ≥50% coverage, no accepted owner-boundary misses) was not met. The result is a retained negative qualification, not a global judgment about the model.

## Evidence and reproduction

Local pilot directory: `.tmp/phocinae-pilot-20261010/` (ignored by Git).

- `cases.json`, `plan.json`: frozen inputs/splits and acceptance.
- `benchmark.py`, `perf_probe.py`: minimal offline direct-engine runners.
- `download-manifest.json`, `requirements.lock`: pinned assets/dependency closure.
- `calibration.json`, `predictions.json`, `result.json`, `perf-cpu.json`, `perf-mps.json`, `receipt.json`: full results and digests.
- Dataset SHA-256: `3899653ff028d7aba616b0dc1758428aab9b07c5423cd787be1d05eb9f268477`.

Run the existing isolated runner to reproduce; it writes generated results only inside the pilot folder. No activation, copying into Cortex or external model endpoint is required. These are local experiment artifacts; the report alone is not a portable model distribution.

Primary author sources: [model card](https://huggingface.co/Phocinae/Phocinae-Largha-150M-v1), [runtime](https://github.com/Phocinae/phocinae-server). The model card checked on 2026-10-10 additionally disclosed error-correction training drawn from typed-decisions test rows; author aggregate scores are not independent OS-domain acceptance evidence.
