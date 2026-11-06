# ABVX Credential Broker Architecture V1

**Status:** architecture proposal; implementation not started. **Input inventory:** `docs/audits/abvx-secrets-inventory-v1/`, status PARTIAL.

## Decision

Use a local owner-controlled broker daemon, reached through a Unix domain socket, with a hybrid credential store: macOS Keychain holds individual credential items and protects any broker-only encryption material; a versioned, encrypted local vault stores recoverable secret payloads only if Keychain item backup/restore proves inadequate. V1 should prefer Keychain items and keep the encrypted-vault fallback out until a recovery requirement is demonstrated. Registry metadata and policy are separate, non-secret, versioned files. Never store values in the registry.

This fits one primary owner and many projects while inheriting macOS unlock/access controls and avoiding a custom crypto/key lifecycle. Backup and recovery are intentionally owner-mediated: document credential IDs/scopes and recovery procedure, do not export plaintext backup. Keychain synchronization is not assumed. Rotation remains provider-specific. Auditability comes from stable IDs and events, not secret fingerprints. This choice needs a small fake-credential prototype to establish IPC, Keychain access prompts, item ACL behavior, backup, and recovery before real import.

## Components and trust boundaries

1. **Request client** (Codex/agent/project CLI) submits structured operation, project, purpose, resource, model and limits; it cannot ask for a value.
2. **Local daemon** authenticates local socket peer where available, resolves explicit project identity, evaluates policy and budgets, and dispatches only registered operations.
3. **Approval surface** is CLI for V1, with approval bound to exact request digest and short expiry. A future desktop prompt may improve UX; no web UI.
4. **Class A adapter** calls provider directly; credential remains in broker memory for request lifetime.
5. **Class B runner** starts one registered executable/template with allowlisted structured inputs, minimum environment, controlled cwd, timeout and bounded output. It receives credential; requester does not.
6. **Audit writer** appends sanitized JSONL events. Policy, registry, capability ledger and audit have separate schemas and restrictive owner-only permissions.

Socket: `~/.abvx/credential-broker.sock`, owner-only directory/socket permissions (0700/0600), no TCP listener. Peer credentials are defense-in-depth, not sole authorization; each request must also identify a registered agent/project context and satisfy policy. Daemon restart invalidates outstanding capabilities unless durable revocation/expiry state proves otherwise.

## Registry and identity

Stable IDs name a credential and scope, e.g. `openai.primary`, `vercel.menton`, `mn7r.database`. Each ID is an independent item even if env aliases match. Aliases are explicit tuples `(project, environment, legacy_name) -> credential_id`; ambiguous resolution fails closed. Registry fields: `credential_id`, `provider`, `credential_type`, `owner`, `projects`, `environments`, `allowed_operations`, `execution_class`, `adapter`, `rotation_metadata`, `remote_store`, `status`, `created_at`, `expires_at`, `notes`. Unknown values remain `UNKNOWN`; never assert equal values based on matching variable names.

## Execution classes

- **A:** preferred. Broker owns credential and performs narrowly defined provider operation; returns minimal result, sanitized provider error, usage and cost metadata.
- **B:** registered isolated worker/app operation only. Secret may exist in child environment but not requester environment or output. No arbitrary shell wrapper.
- **C:** inventory confirmed zero. Not available in normal V1. A future genuine raw-value need requires separate break-glass design and explicit owner approval, short TTL, one-use where possible, justification and audit.
- **D:** unknown. Deny dispatch until evidence classifies the integration and names an adapter.

WhatsApp session directories are protected worker state, not scalar secrets: worker owns session path and provides narrow operations. CoqPi retains Electron `safeStorage` for its existing app-managed secrets until a separate integration proves broker operations fit; options are broker-owned provider calls or CoqPi as trusted Class B app. Do not copy ciphertext blindly or treat safeStorage as an agent boundary.

## Policy, budgets and output

Policy binds agent, project, credential, provider, operation, resource, environment, model, per-request/run/project-day budget, request/token ceilings, time window and TTL. Defaults: deny; writes and production mutations require owner approval; Class D/C deny. AUTO is limited to pre-approved, low-impact, capped operations. OWNER_APPROVAL grants revocable capability referencing exact scope and request digest, never secret material. BREAK_GLASS is separate and unavailable to routine agents.

Reserve budget atomically before dispatch, reconcile provider usage after, and charge conservative estimate when actual usage is absent. Hard stop at limit; warnings at configured thresholds; retries count as requests and cost. Local accounting is sufficient for V1 but concurrent requests must not overspend via race. Unknown price/model is denied for metered operations unless an owner-set conservative ceiling exists.

Redact exact active secret values before any output leaves broker, plus authorization/bearer headers, credential-bearing URLs and provider token patterns. Regex is defense-in-depth only. Bound response size; do not return raw headers or full provider diagnostics. Persist no raw payloads by default. Audit records metadata only; secret-derived fingerprints are prohibited absent a documented need.

## CLI and migration boundary

Provide `secrets list/status`, `auth request/approve/deny/revoke`, `run <registered-operation>`, and `audit [filters]`. There is no normal `secrets get`. All outputs are sanitized. This document authorizes no migration, config edit, remote change, deployment, rotation, or removal of inherited `OPENAI_API_KEY`.

Before production use: fake-secret prototype; security review; schema and adapter tests; OpenAI pilot implementation gate. Keep old sources until per-migration verification, rollback, old-path removal approval, rotation assessment, and post-scan pass. See migration plan.

## Evidence limits and open decisions

Inventory found 77 identifier patterns across ten local project paths; 27 A, 32 B, 0 C, 18 D (counts are approximate primary classifications). Six repeated identifier patterns do not establish value equality. Current Codex process had `OPENAI_API_KEY` by name; origin/lifetime unknown. Full reachable history, recursive env discovery, remote scopes/expiry/rotation and cross-value equality remain unverified. The architecture does not claim repository cleanliness or remote completeness.

Open before implementation: verify Keychain ACL and backup behavior; select daemon language/runtime and peer-identity API; settle agent identity provenance and CLI approval UX; freeze OpenAI model allowlist and local pricing source; define provider data retention; investigate existing translation-runner adapter seams. Follow-up hygiene scan is required but does not block this architecture gate.
