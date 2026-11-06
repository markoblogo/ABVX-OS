# Local book-model qualification — v1

Use the existing NarrativeRunner / Conventional Translation module with a thin language profile. Do not build another book or translation engine. The Liubchenko pilot packet is in `books/research/liubchenko-v1/local-model-preparation-v1/`.

## Local-only boundary

Generation endpoint must be `http://127.0.0.1:11434/api/chat`. Disable HTTP proxies and redirects in the adapter. Allow only explicitly installed local model names; reject cloud names and pin the installed model-manifest digest. No external inference fallback. A public model-weight download is a distinct owner-authorized installation operation; never upload the manuscript or scans as part of installation.

## Recovery and qualification

1. Check idle/active local workers before restarting. Preserve models and other projects. Record hardware, Ollama version, installed model digests and current disk/RAM availability. An HTTP health response does not prove generation.
2. Test a tiny completion with a realistic cold-start deadline. Separate model-load latency from token generation. Keep context/options constant and test one loaded model at a time. Do not benchmark a cold read while installing large weights. Discard overlapping-load timings as clean speed comparisons; retain them as observations.
3. Compare identical witnessed passages: an ordinary paragraph, a figurative or archaic passage, and negation/agency or a dense ending. Retain raw source/output, actual elapsed/load time, prompt/output tokens and output words. Review additions, omissions, changed modality, subject/object reversals, terms, paragraph structure and register. A fluent response is not semantic admission.
4. Test scan reading independently with a manually checked whole-page reference, including a page with mixed authors or apparatus. Prefer explicit source-region cropping and page mapping over trusting a model to obey exclusion instructions. OCR similarity is a diagnostic, never a 100% source-coverage claim.
5. Exercise the existing core on retained real local responses: structural alignment, unchanged-source resume without provider calls, profile/model/source cache isolation and corrupt-output hash rejection. Treat literary, source and production admission as separate gates.

## Runtime profile

The adapter and benchmark scripts are retained in the pilot packet. Use fixed context/options, small source blocks, serial execution, a cold-start deadline with margin, and a bounded keep-alive. Pin model digest and profile fingerprint in the run path; verify source/output hashes before resume. Record failed calls and actual retries/repairs separately. Never replace unavailable metrics with zero.

TranslateGemma's model card describes 2K input context and a specific user-only translation template. Keep input within that bound even if the runtime advertises a larger architectural context. The tested runtime setting was 4096 total context tokens, with small inputs; it is not evidence for translating an entire book in one request.

`SUCCESS` in NarrativeRunner means a nonempty persisted response. It does not mean SOURCE PASS, LITERARY PASS or TEXT LOCK. Translation model qualification does not close the source-witness gate. Maintain per-work source provenance, source coverage, section coverage, alignment and emendations; then perform whole-volume editorial and continuity QA.

## Removal decision

Unloaded models use disk space, not resident inference RAM. Deleting unused weights will not repair mistranslation or cold-start configuration. Preserve models with other-project uses. Choose removal only after replacement qualification and an actual storage need; retain a manifest/digest and reinstall path. The Liubchenko preparation does not authorize publication, cover creation or worldwide rights.

## Provider references

- https://docs.ollama.com/troubleshooting
- https://ollama.com/library/translategemma:4b
- https://huggingface.co/google/translategemma-4b-it
