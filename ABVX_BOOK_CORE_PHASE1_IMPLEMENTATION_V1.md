# ABVX Book Core Phase 1 Implementation V1

Date: 2026-09-30\
Scope: bounded local infrastructure only

## Outcome

**BOOK CORE PHASE 1: REVIEW** — implementation and verification passed; the required protected-file hash snapshot was captured after the first scoped code edit rather than before it. No protected path was written by this implementation, and the snapshot was rechecked after tests, but the original pre-edit hash step was missed. This process deviation prevents an unqualified PASS.

Book Three creative Gate A remains **NOT AUTHORIZED** and **NOT STARTED**.

## Implemented

- Added `src/abvx_harness/book_core/` as the single shared implementation for generic SHA-256/ref validation, identity and bounded state contracts, event/hash-chain validation, conditional locks and successor relations, validator-result proof rules, module-profile composition, null-preserving prospective metrics, and generic read-only registry facades.
- Added a thin GD3 compatibility adapter and routed `book status <book_id>` / `book validate <book_id>` through the registry facade. A new-format adapter supplies registered project/state/ledger paths; the generic validate facade loads them, verifies refs/hashes, identity, state/event agreement and lock applicability, then runs the adapter's applicable validators. The registered production consumer remains GD3 only; unknown IDs fail without filesystem discovery.
- Moved SHA-256 helpers and the shared PASS-requires-proof decision into the core. GD3 retains a compatibility serializer for its existing result schema and keeps its domain-specific canon, retailer, illustration/Pictiq and production checks.
- Added offline `SERIES_FICTION`/GD3 and `CONVENTIONAL_TRANSLATION` fixtures. The translation policy requires source and translation locks, leaves text lock UNKNOWN, and marks canon/art/render/build locks NOT_APPLICABLE. Translation does not require fiction architecture, series position or Pictiq.
- Added 35 focused core tests. No new package dependency was introduced.

## Compatibility and boundaries

- GD3 state and event ledger remain in their original schema and byte format. Their existing validator remains authoritative through the adapter; no hashes or history were synthesized into the legacy ledger.
- The new event contract is available for prospective consumers: unique ID, contiguous sequence, exact book ID, timestamp, evidence policy, predecessor event hash, state-after hash and event hash. OWNER_DECISION requires a trusted PROJECT evidence reference; the actor label alone is insufficient.
- Omitted lock applicability resolves to UNKNOWN. NOT_APPLICABLE requires an explicit policy; an absent required lock resolves to UNKNOWN, never PASS. Replacements must name an existing same-kind predecessor; the predecessor is not edited.
- PASS validator results require input and evidence refs. UNKNOWN/N/A require reasons. OWNER_ACCEPTED_EXCEPTION remains distinct from PASS and requires scope, accepted risk and a local owner-decision proof ref.
- Metrics are prospective only. Missing values stay null; file timestamps are not converted into owner effort.
- This is a bounded semantic/runtime subset of the design schema, not complete JSON Schema enforcement. `jsonschema`, `fastjsonschema`, AJV/Draft 2020-12 CLI support were not available locally; `requirements-dev.txt` contains only pypdf. No large validator dependency was added.

FULL_DRAFT_2020_12_SCHEMA_VALIDATION: **NO**

## Verification

| Acceptance check | Result |
|---|---|
| One generic core implementation | PASS |
| GD3 compatibility and existing status semantics | PASS |
| GD3 state/event bytes | UNCHANGED in read-only facade tests |
| Generic identity/state/events/locks/validator contract | PASS (bounded subset) |
| Generic status/validate facades | PASS; registry only |
| Synthetic series-fiction and translation profiles | PASS |
| Prospective metrics/null handling | PASS |
| Locked book content changed | NO |
| Book Three creative work | NOT STARTED |
| External API calls / external writes | 0 / 0 |

- Focused core suite: **36/36 PASS**.
- Existing GD3 foundation regression suite, unchanged: **44/44 PASS**.
- Combined run: **80/80 PASS**.
- `./bin/abvx book status gd3`: returned the established Book Three identity, `CURRENT STAGE: NOT_STARTED`, `CURRENT GATE: A_PENDING`, and `OWNER ACTION REQUIRED: AUTHORIZE GATE A — CONCEPT + ARCHITECTURE DEVELOPMENT`.
- `./bin/abvx book validate gd3`: completed with `OVERALL: REVIEW`; all recorded checks were PASS or NOT_APPLICABLE except `VISIBLE_CONTENTS: UNKNOWN`. REVIEW is preserved and was not promoted to PASS.

## Protected-file hashes

The following snapshot was taken after the scoped implementation patch and before final verification. All 16 hashes were rechecked after the combined test run and matched. Because the pre-first-edit snapshot was missed, this inventory is not represented as a pre-implementation baseline.

| Protected file | SHA-256 |
|---|---|
| `books/rn10-003/manuscript/GOOD_DOG_BAD_SYSTEM_TEXT_LOCK_V1.md` (Book One locked manuscript) | `7e7349fb5f07548d344b1a4a462137fcbe76bca1696ef1f1cc30211f2c061e81` |
| `books/rn10-003/GOOD_DOG_BAD_SYSTEM_TEXT_LOCK_V1.md` (lock record) | `8d4054415e63bc6473fc2fa9bd1a62374cfeb71f37dca79a80e42e832586aea1` |
| `books/rn10-003/GOOD_DOG_BOOK_TWO_TEXT_LOCK_V1.md` | `3d29eb6e5e201b0b3805d92ca7b38d965d8bdfdad46a49ff8077ce425fb70a44` |
| `artifacts/jekyll-toki-pona-full-v1/MANUSCRIPT_JEKYLL_TOKI_PONA_LATIN_TEXT_LOCK_V1.md` | `a174999649808399aa49e5b8ff3319b89e30f39a78118be83d53bc93e37fd5ef` |
| `books/rn10-003/GOOD_DOG_BOOK_THREE_STATE_V1.json` | `31dbf80e755533241d754b43048796761df785cb2f3aa3c01bf31be16a877e55` |
| `books/rn10-003/GOOD_DOG_BOOK_THREE_EVENT_LEDGER_V1.jsonl` | `8ee2f93754bf95f6fd302881fbe5f2267f9b9896fcc3926ea4c894eec0a0aeb8` |
| `books/rn10-003/GOOD_DOG_SERIES_PUBLICATION_CANON_V4.md` | `80dc1861e5d3fae5a74aaf606d3cffc029b63c444a9a4ba902a376eb79999561` |
| `books/rn10-003/GOOD_DOG_SERIES_PUBLICATION_CANON_V4.json` | `46c837f6bd8de83f106900071883698dca00487c04c2e76ea2c8818e2fe53612` |
| `books/rn10-003/GOOD_DOGS_CANONICAL_MANIFEST_V6.json` | `64b88cc24106c3d8b615b123ab1ea3a8c993ce35375ab95a25b50346024edb3c` |
| `learning/book-systems/records.jsonl` | `9d47cd254f6fac141399ff77d829fd893fd51f63c06dd6bf372d292a1d51649b` |
| `ABVX_BOOK_FACTORY_CROSS_PIPELINE_AUDIT_V1.md` | `b5695296ff924bff5ed3450ca4468e6e3c44d6c3117ad5d17a0cabd26251c109` |
| `ABVX_BOOK_CORE_ARCHITECTURE_V1.md` | `50b01563ffa6a48a0f97bec0286c687cfdd83ce5615b9ef469fe663e2bfb4881` |
| `ABVX_BOOK_TYPE_MODULES_V1.md` | `d2764b8a5c2d3441c4af47db1e3f1ed66c9110cbfc72964be534150294f4aaf2` |
| `ABVX_BOOK_CORE_STATE_SCHEMA_V1.json` | `83a0a3255f0c2b947558109a81b2946c627cbd0195323ef8635aa2f58d84c90e` |
| `ABVX_BOOK_PRODUCTION_LEARNING_REGISTRY_V1.json` | `2390593823916f36bd4dbfa9b871de8ccc0e45fa78d1403740e21402f9e8d27b` |
| `ABVX_BOOK_FACTORY_IMPLEMENTATION_PLAN_V1.md` | `e9be601af03fbf845e315d3921d7f3454bd59f4e52f4ebed942419e9ea3ea69a` |

## Files changed by this implementation

Created:

- `src/abvx_harness/book_core/__init__.py`
- `tests/test_book_core.py`
- `tests/fixtures/book_core/conventional_translation/identity.json`
- `tests/fixtures/book_core/conventional_translation/lock-policy.json`
- `tests/fixtures/book_core/series_fiction/profile.json`
- `ABVX_BOOK_CORE_PHASE1_IMPLEMENTATION_V1.md` (this report)

Modified within the user's pre-existing dirty worktree:

- `src/abvx_harness/book_three.py`
- `src/abvx_harness/__main__.py`

No other pre-existing dirty files were intentionally edited. No manuscript, canonical state, history, learning ledger, production artifact, or registry was modified.

## Known limitations / Phase 2 blockers

- The GD3 legacy ledger has no new-format per-event hash-chain fields; compatibility deliberately validates its existing format rather than rewriting it.
- No canonical state/event writer, transactional reducer, event replay migration, or single-writer persistence was added.
- The production registry currently contains GD3 only. The translation consumer is a synthetic test fixture, not a migrated title or filesystem-discovered book.
- Full Draft 2020-12 schema validation remains unavailable without an approved local validator/dependency decision.
- Dependency DAG/STALE propagation, build manifests, Contents/format adapters, production rendering and builders, retailer integrations/writes, learning automation, and additional book migrations are deferred per Phase 1 scope.

NEXT GATE: **ABVX BOOK CORE PHASE 2 — PRODUCTION FOUNDATION**\
AUTHORIZED: **NO**\
BOOK THREE GATE A: **AUTHORIZED: NO**
