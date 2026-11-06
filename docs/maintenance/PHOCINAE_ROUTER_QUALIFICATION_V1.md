# Phocinae decision-router candidate v1

Status: isolated Mac pilot completed on 2026-10-10; not qualified for the tested OS routing task. Weights/runtime are installed only under ignored `.tmp/phocinae-pilot-20261010/`; Cortex activation remains disabled. See [measured report](PHOCINAE_MAC_PILOT_2026-10-10.md).

Primary sources checked:
- https://huggingface.co/Phocinae/Phocinae-Largha-150M-v1
- https://github.com/Phocinae/Phocinae-Largha-150M-v1

The author identifies Apache-2.0 weights with an MIT mmBERT-small base, 144.3M parameters, FP16 storage about 289 MB, and a specialised typed-decision interface (`noul`, `choice`, `score`). It does not generate explanations or perform RAG synthesis. Advertised GPU latency is for RTX 5090; the author's CPU single-thread median is 1.64 seconds per five-question case. Mac performance remains unmeasured here.

The reported 55% fewer LLM calls/99.36% retained-subset accuracy is a fitted benchmark/selective-routing result; the confidence threshold was swept on evaluation data. It is not expected OS performance. The author also discloses JevBench 54.55%, below its acceptance gate, and shipped calibration ECE 0.2519. English/translated-Chinese evidence does not establish Russian/Ukrainian quality.

## Proposed placement

Deterministic schema, tenant, provenance, expiry and authority checks run first. The tiny model can later classify eligible, redacted process context into `USE_EXISTING_PLAYBOOK`, `RETRIEVE_MORE_EVIDENCE`, `REQUEST_LOCAL_LLM_ANALYSIS`, or `OWNER_REVIEW_REQUIRED`. Low-confidence, contradictory or unsupported inputs must escalate. A yes/no model may not grant approvals, decide rights/safety, delete data or establish quality/efficiency gains.

Keep it independent of the optional Ollama reasoner. Reuse the upstream Python engine directly for a bounded local test; do not add a server/listener/scheduler just to run a classifier. Do not copy custom model code blindly or use `trust_remote_code`.

## Qualification milestone

1. Pin an upstream release/commit and verify weight SHA-256; inspect the runtime/dependency closure and licence notices.
2. Install only in an isolated local environment; keep weights, datasets and receipts ignored. No change to OS/core dependencies.
3. Evaluate a reviewed OS-specific synthetic/redacted set, including Russian/Ukrainian needs if applicable, with a separate calibration and held-out split. Compare deterministic routing, tiny-model routing and LLM escalation.
4. Measure cold/warm latency, RSS, coverage, wrong confident decisions, calibration, and total owner/LLM cost on the actual Mac. Unknown labels remain unknown.
5. Enable only after held-out acceptance and owner approval, initially in shadow mode. Retain rejected cases; no automatic training or authority promotion.

Do not delay the verified OS telemetry/retrieval integration for this optional candidate. This qualification is a later bounded experiment, not a second platform implementation.

## Measured disposition

Apple M4/16 GiB: CPU warm choice ≈30 ms, five-question request ≈113 ms; peak process memory 1.3–2.0 GB. The frozen OS routing holdout matched 34/48 cases; same-field deterministic rules matched 48/48. No confidence threshold qualified on the separate calibration set. A yes/no supplementary probe matched 7/12; option reversal changed 4/16 English decisions. Keep this a rejected domain qualification, with evidence retained and no automatic routing. The newly disclosed training/test overlap in the author card strengthens the need for an independent task-specific acceptance set.
