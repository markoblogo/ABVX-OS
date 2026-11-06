# ABVX.xyz and ABVX OS operational audit — 2026-10-10

Cost class: NORMAL. Objective: shorten reliable publication/release cycles, reduce request work, repair reproduced defects and prioritize further improvements. Reused the registered content-ops control plane and independent project consumers; donor matrix checked. No replacement CMS, new orchestration platform, paid service, dependency or unattended publication authority.

## Coverage and baseline

ABVXsite was inspected and changed in an independent clean checkout based on production merge `698731c61d39f3373ca7f92ea966bdc61687d299`, not through sibling-repository edits. Coverage: publication/prebuild scripts, CI and feed workflows, content getters and chronology, proxy/CSP, SEO/machine-index checks, representative page rendering and local performance. The site report is `docs/performance-and-release-audit.md` in ABVXsite.

ABVX OS coverage: registry/provider boundaries, publishing preparation/approval/packet emission, state persistence, development dependency/test setup, CLI startup and repository validation. The OS working tree contained unrelated active Book Core/Radar/manuscript work before this task; it was preserved. This is not an exhaustive security review, source-file-by-source-file audit, paid-provider benchmark or a claim of stronger search traffic.

## Implemented fixes

| Area | Reproduced issue | Bounded change | Verification |
| --- | --- | --- | --- |
| Site request work | Warm homepage reread 193 Markdown files; Writing 22 | React server-request cache on common content getters | Same instrumented production server: 104 and 11 reads; Books 112 and Systems 49 unchanged |
| Site deployment waste | Documentation-only edits triggered an application rebuild | Shared explicit build-scope classifier; CI retains all non-build quality gates; Vercel compares previous successful deployment SHA | Git fixture covers unknown history, renames/deletes, failed runtime build followed by docs; conservative full build when uncertain |
| Site proxy | Static media/machine files ran HTML nonce work | Known static paths bypass proxy; global headers remain | HTML CSP QA passes; public machine indexes and existing brand image return 200 with nosniff and no nonce CSP; no blanket static rendering |
| Site SEO gate | Successful build followed by homepage load timeout | Wait for DOM content and actual existing metadata/navigation assertions | All 193 routes/titles, public indexes, dates/localization/mobile navigation pass |
| Publication observability | Release receipts did not expose gate costs | Per-check and total elapsed time on success/failure | Receipt retains measured durations |
| OS approval integrity | Editing an approved item's summary still allowed packet emission | Fingerprint approved publication fields; reject changed or legacy unbound approval before writing packet | Regression failed before fix and passes after; unchanged and explicitly reapproved legacy items still publish |
| OS write resilience | JSON used direct truncating write | Same-directory temporary write, flush/fsync and atomic replace; cleanup on error | Injected replace failure preserves original bytes and removes temp file |
| OS video intake | Upload timestamp alone passed preparation | Require video URL and timestamp together | Orphan date rejected before handoff |
| OS local test setup | Plain `PYTHONPATH=src` missed dependencies; fallback native modules can target a different Python | `bin/check` validates contracts and runs tests, preferring selected environment then existing fallback; no automatic installs | Default Python 3.14 focused suite and isolated Python 3.12 full suite executed |

Approval fingerprint is an integrity guard inside the existing local trust boundary, not a digital signature or a permission redesign. Existing packet/media/source digest checks remain. Atomic replacement prevents partial individual files; it does not claim multi-file transactions or serialized concurrent writers. Older APPROVED records remain readable but require review and reapproval before a new handoff. Already-emitted packets remain historical evidence.

## Measured time and successful checks

- Baseline site main CI run `38073459894`: roughly 61 s, including checkout 12 s, install 11 s, lint 9 s and build 13 s. The highest-value improvement is avoiding needless/repeated release attempts, not removing safety gates.
- Site: 122 content/sync tests, 23 vector tests, validators, lint, local webpack production build and production dependency audit pass (0 reported vulnerabilities). Default CI build remains a separate required gate.
- Local desktop performance smoke: all six representative routes pass, CLS 0 and no broken detected images. Homepage DCL/load/LCP changed from 166/230/180 ms to 96/157/132 ms. These are single local samples, not a field/mobile speed guarantee; deterministic read counts are stronger evidence.
- CSP: six standard routes plus YouTube project route pass. Cases/homepage chronology/media/link checks pass at 390 and 1440 px with no horizontal overflow.
- OS version startup median approximately 68 ms across three local invocations; no meaningful startup problem established. Avoid speculative CLI refactoring.
- OS repository validation passes. Focused final Content Ops suite: 18 tests pass. Supported isolated Python 3.12 full suite: 637 tests, the same two failures and one error seen before these fixes. The other 634 tests pass. Full suite is **not green**.

## Remaining OS failures: preserve evidence

1. `test_book_radar_prior.RetainedPriorIntegrationTests.test_retained_overlay_pmp_surface_and_unchanged_wide`: `Prior evidence changed`. The provenance verifier detects a hash/source mismatch in live working evidence; never refresh an approved digest without reviewing changed bytes.
2. `test_book_core.BookCoreTests.test_valid_gd3_compatibility_load_and_status`: expected `TEXT LOCK: NONE`, current working GD3 state is `LOCKED`. New/uncommitted tests read an evolving book record.
3. `test_book_radar_reachability.ReachabilityCalibrationTests.test_policy_remains_prospective_owner_gated`: expected proposed status, working policy is now owner approved.

These existed in the active tree before this patch. No canonical book state, approved policy, other thread's code or evidence was reverted to make expectations pass. Treat these as separate data/fixture-isolation work, not an install problem and not a successful full OS release. Do not push the whole dirty OS branch.

## Prioritized next work

| Priority / cost | Next action | Completion evidence |
| --- | --- | --- |
| P1 / NORMAL | Isolate Book Core/Radar tests from mutable production records; review retained evidence mismatch with its owning workstream | Disposable fixtures, explicit current policy tests and clean full suite; preserve approved source/state |
| P1 / CHEAP | Use one complete source/media/index batch, one preflight and one PR; read gate durations instead of rerunning successful work | Several release receipts and provider timings, distinct local/preview/production SHA proof |
| P2 / NORMAL | Measure actual public mobile transfer and slow-network LCP on Books/Systems | Resource waterfall + realistic mobile results before derivative/cache changes |
| P2 / NORMAL | Consider stable public-data caching only after production latency measurement | Explicit freshness/key policy preserving nonce/language and future visibility, no all-page static conversion |
| P2 / CHEAP | Review original-content discovery and conversions after enough observations | Page-filtered 28-day Search Console/Plausible comparison; indexing/traffic unknowns retained |

No EXPENSIVE platform rewrite is justified by these measurements. Existing unchanged feed cron jobs already avoid commits and deploys; retain their cadence. Keep ABVX OS and site independent, and continue existing prepare → review/approve → packet → consumer dry-run/apply → local checks → PR → production proof workflow.

## Reproduction and evidence

Site commands: `npm run content:release-check -- --webpack` (local fallback), `npm run qa:seo`, `npm run qa:csp`, `npm run qa:perf`; default build in CI/Vercel. OS: `./bin/check discover -s tests -p test_content_ops.py -q`; isolated full run uses `ABVX_CHECK_PYTHON=/tmp/abvx-os-audit-venv/bin/python ./bin/check`. See `docs/development-checks.md` and updated `docs/abvx-site-publishing.md`.

Local logs retained under `/tmp/abvx-audit-*`, `/tmp/abvx-content-reads-{before,after}.log`, `/tmp/abvx-os-audit-*` and site ignored QA/report folders. They are local diagnostic evidence, not durable public artifacts. The committed findings above retain the decisive counts and failures. Site PR: https://github.com/markoblogo/ABVXsite/pull/53, reviewed source head `70c6156d06eb88ce078d5acaa4a43ea798f0e6ad`. PR CI passed in 57 s, default build included; Vercel Preview succeeded (`6984952304`). Merge SHA `f32b88e286b75fd6aeeb87edc165e7239f665b59`. Production deployment `6984982060` reports success at `2026-10-10T18:23:46Z` for that merge. Canonical `https://abvx.xyz/` returns 200 with nonce CSP and deployment ID `dpl_9b1JiypFgDhZzseLRiKzquNcmuGV`, matching the Vercel production status target. Post-release canonical SEO/discovery checks pass for all 193 routes; 390/1440 px checks pass for cases, media, links, shared Writing/home chronology and catalogue cards. The generated deployment URL may present Vercel's access application; its HTML is not used as site-content proof. OS changes are committed locally only, with unrelated working files excluded.
