# Revenue V2 verification

Verified 2026-10-07, local workspace only. Implementation status: PASS; owner operating-model acceptance: APPROVED FOR OPERATING USE (2026-10-07).

- New revenue tests: 18/18 PASS (external-only boundary and nested-field rejection; Lane E repeated objects; frozen qualification; post-qualification classes; Sunday UTC boundary; separate formats/actions; UPDATE exclusion; unknown quota; one-slot NO; artificial eBook block; exposure stages and UNKNOWN demand; canonical derived metrics; missing member/window/currency handling; matched-cohort read-through; corrected Good Dogs queue; historical file preservation).
- `./bin/abvx validate`: PASS, including strict revenue model schema and semantic validation.
- Full `test_book_radar*.py` suite: 257 tests, 255 pass, 1 failure and 1 error outside the new feature. `test_retained_overlay_pmp_surface_and_unchanged_wide` rejects a changed prior-evidence hash. `test_policy_remains_prospective_owner_gated` expects PROPOSED_PENDING_OWNER_REVIEW but the retained policy is OWNER_APPROVED_PROSPECTIVE. These legacy modules, inputs and assertions were not changed to make the run pass. The full suite is not claimed green.
- Protected baseline: all 18 files byte-identical after implementation: canonical `book-radar/state.json`, existing scoring-model files, and existing Amazon Market Discovery V0 packet files. Consequently historical opportunity observations, scores, decisions and actuals within that state remain unchanged.
- Read-only growth CLI executed successfully as of 2026-10-07. Rolling 30d, MoM, incomplete Good Dogs outcomes and unobserved slot history remain UNKNOWN. Stoic lifetime figures preserve original 2026-10-02 observation dates and estimate status.
- Archive file inventory confirmed sources for System, District and Authority in `/Volumes/Work/books archive/GD`; no manuscript read, altered or produced. All-three LIVE status is current owner testimony and retained registry evidence, not a new retailer capture.

Owner model-review gate completed. The owner explicitly accepts the two documented failures as KNOWN LEGACY FAILURES, NON-BLOCKING FOR REVENUE V2; historical evidence, policy state and assertions are not modified to turn them green. Remaining title-specific operating checks: reconcile quota from account evidence, record the one-slot answer, link independent C01 qualification and check actual submission readiness. Carmilla remains the owner-selected next paperback candidate after C01. Good Dogs remains observation-only and extension HOLD. No next LitRPG Book 1 production is queued.

Books produced NO. Historical scores/outcomes changed NO. KDP account accessed NO. Public official help read YES. Ads started NO. Release submitted NO. Production authorized NO.

Owner priorities now also include D2D exploitation of eligible existing original-IP catalog, independent of scarce new KDP paperback slots. Model acceptance records this strategy; no distribution operation or new broad discovery scan was run.
