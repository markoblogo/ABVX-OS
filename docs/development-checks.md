# Reproducible local checks

Use a clean branch/export for release checks. The owner workspace may contain private working state and historical evidence that must not be rewritten to satisfy tests. `scripts/check-isolated-books.py` verifies the bounded book regressions without access to operational `books/` or `book-radar/` data.

Ordinary tests use fake credentials and mocked provider calls. Native macOS Keychain lifecycle tests are excluded by default; run the three explicit integration cases only with `ABVX_RUN_KEYCHAIN_TESTS=1` on an authorized disposable test account. This opt-in can touch the logged-in Keychain and is separate from portable regression acceptance. No real API calls or credential migration are part of repository hygiene.

On macOS, use `TMPDIR=/private/tmp` (or another real directory with no symlink ancestors) when running the checks. Exchange-root tests deliberately reject symlink ancestors; the platform default `/var/...` can resolve through `/private/var` and fail that guard. Do not weaken the runtime guard to accommodate a test temporary path.

Run `./bin/check` from any working directory. It prefers dependencies installed in the selected Python environment, then tries the same repository-local Book Core dependency path as `bin/abvx`, fails once with an actionable message when dependencies are missing, validates repository contracts, then runs unit tests. For a focused regression: `./bin/check discover -s tests -p test_content_ops.py -q`. No dependencies are installed automatically and no external actions are authorized.

CI tests Python 3.11, 3.12 and 3.13. A clean isolated local setup matching the audited runtime:

```sh
python3.12 -m venv /tmp/abvx-development-venv
/tmp/abvx-development-venv/bin/python -m pip install -r requirements-dev.txt
ABVX_CHECK_PYTHON=/tmp/abvx-development-venv/bin/python ./bin/check
```

The launcher retains the existing `.tmp/book-core-runtime` fallback. Do not confuse failures from a missing global dependency or unsupported environment with software regressions. Retain full logs locally and report failing test names plus the decisive error. Do not print full transcripts or rewrite approved book state/policies to make a test expectation pass. Tests touching production work state require a separate fixture/isolation review.

Content approvals now bind a SHA-256 fingerprint of the item’s publication fields (payload, media descriptors, metadata, validation and adapter snapshot). Changes after approval block publication before any packet write. Older APPROVED items without a fingerprint remain readable but must be reviewed and approved again before handoff. Previously emitted packets remain historical evidence. Content JSON files use atomic replacement; this prevents partial file truncation, without claiming a multi-file transaction or a concurrent-writer lock.

## Capture operational experience without rerunning checks

```sh
ABVX_CHECK_PYTHON=/path/to/isolated/python ./bin/check --record .tmp/os-learning/new-check.json
```

This runs the normal checks once and records numeric telemetry plus a local proof digest. It makes no Cortex/network call; owner effort and unproven safety stay `UNKNOWN`. Explicitly select outcomes for protected Cortex admission. This opt-in hook avoids running the same checks separately just to create a learning record.

Private canonical-manuscript, retained-market-evidence and historical owner-queue acceptance cases require ABVX_RUN_PRIVATE_SOURCE_TESTS=1 plus the matching private source package. Portable CI uses generated synthetic translation blocks and a separate synthetic observation/revenue policy; private acceptance is not inferred from portable test success.
