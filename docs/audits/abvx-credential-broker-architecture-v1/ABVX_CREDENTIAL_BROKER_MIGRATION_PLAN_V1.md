# ABVX Credential Broker Migration Plan V1

**No migration is authorized or performed by this plan.** Every phase has a stop gate. Existing source remains migration debt until all acceptance criteria pass.

## Universal migration checklist

1. Identify exact source and owner without printing values; map project/environment/operation and remote scope.
2. Import into the selected broker store using a controlled path; verify by broker operation, never by displaying the value.
3. Test broker operation and application integration with fake then approved real credential.
4. Verify provider/remote behavior where needed; capture scope/expiry evidence.
5. Prove rollback path and bounded outage recovery.
6. Only after owner approval, remove old plaintext source and ensure new agent processes do not inherit it.
7. Decide and perform rotation where exposure history warrants; separately approved.
8. Run post-migration source/env/history scan and record residuals.

Never delete a source merely because import succeeded. Stop on unknown value equality, scope, owner or rollback behavior; create explicit identity records rather than merge by variable name.

## Phases

| Phase | Scope and order | Exit gate |
|---|---|---|
| 0 | Architecture, schemas, fake-secret prototype | Keychain/IPC/access prompts, peer identity, redaction, budget concurrency and recovery assumptions validated; no real secret |
| 1 | OpenAI pilot, starting with one project and one operation | Pilot-specific criteria in `ABVX_CREDENTIAL_BROKER_OPENAI_PILOT_V1.md`; separate approval required |
| 2 | Resend plus selected search/news/data APIs | One provider at a time; narrow resources, spend/quota caps, owner-approved adapter and app tests |
| 3 | GitHub bounded operations | Start read-only; inspect remote token scopes; write operations separately approved |
| 4 | Vercel and MN7R runtime/CLI | Class B sandbox/adapter and exact OIDC/database/session semantics reviewed; production mutations need strong approval |
| 5 | WhatsApp worker/session isolation | Worker boundary demonstrated; session access removed from agent path only after app and rollback verification |
| 6 | Remaining plaintext copies and rotation | Exhaustive location/ownership map; remove old paths only after all prior gates and rotation decision; post-scan evidence |

## Current risk queue (from PARTIAL inventory)

Observed high-risk locations include Codex process `OPENAI_API_KEY` (origin unknown), Index `.env.vercel.production`, Index `.env.whatsapp.local`, two WhatsApp session paths, and MN7R `.env`; VERCEL OIDC values were observed in Index, DMVg and Menton `.env.local`. Values were not read or compared. This plan does not assert any are migrated, compromised, expired, equal, or still present now.

## Follow-up hygiene task (parallel, nonblocking for architecture)

Create a separately scoped read-only evidence pass for: exhaustive current-tree and recursive env discovery across named workspaces; reachable Git-history scan; remote credential scope/expiry/rotation metadata inventory; ownership and eventual rotation plan. Preserve UNKNOWN for unavailable remote data and avoid value reads, fingerprints or mutation unless a later explicit gate authorizes them.
