# Narrative Toki Pona Pipeline Blockers V2

## BLOCKER 1 — Provider path is not production-resolved

**Evidence:** the previous deployed `toki.abvx.xyz/api/translate` probe returned `NOT_FOUND`; the repository does not contain a verified current deployment contract.

**Minimum fix:** choose and test the current provider path, or explicitly restore/update the public deployment. Add a private adapter used by the local runner.

**Regression test:** public health/translate probe plus local provider adapter smoke test.

## BLOCKER 2 — Literary translation adapter is not yet connected

**Evidence:** the new runner can persist and resume blocks, but no approved book-scale translation provider is wired into this repository.

**Minimum fix:** connect a trusted provider adapter with bounded context and model/version recorded in the run manifest.

**Regression test:** rerun the unchanged Jekyll sample and require all blocks to have provider/model metadata and non-empty output.

## BLOCKER 3 — Full semantic regression remains human/editorial

**Evidence:** knowledge/spoiler checks correctly produce review flags but cannot certify voice, ambiguity, or literary adequacy.

**Minimum fix:** complete the model editorial pass and human review queue for the sample before full translation.

**Regression test:** known-failure matrix must be FIXED/IMPROVED or HUMAN_JUDGMENT_REQUIRED with no REGRESSED item.
