# ABVX Credential Broker Decision Record V1

**Decision:** propose a local Unix-socket daemon and Keychain-first hybrid storage; brokered Class A operations are preferred, registered isolated Class B adapters are bounded exceptions, C is break-glass only, D is denied pending evidence.

## Context

The authoritative local credential inventory is PARTIAL. It observed 77 credential identifier patterns and several agent-readable local paths; the current Codex child environment contained `OPENAI_API_KEY` by name. Values were not printed, compared, migrated, rotated, or remotely verified. Six recurring identifier names do not prove equality. History discovery, recursive environment discovery, and remote scope/expiry/rotation metadata are incomplete.

## Decisions

1. Agents request operations/capabilities; normal API never returns raw credential values.
2. Keychain is the primary secret store for the single-owner macOS workstation; encrypted vault backup is deferred unless fake-secret recovery validation requires it. Registry/policy remain non-secret and separate.
3. Local daemon uses owner-only Unix socket, no TCP listener. V1 approval is CLI-based and binds exact request scope/digest to revocable expiring capability.
4. Class A is preferred. Class B uses registered adapters, structured inputs, minimum environment, timeout and sanitized bounded output; arbitrary shell-with-secret is forbidden.
5. Budgets reserve atomically, cap per request/run/project-day, count retries, hard-stop, and reconcile actual provider usage where available.
6. Audit uses versioned sanitized append-only JSONL; no raw values/payloads/headers or secret-derived fingerprints.
7. WhatsApp session state remains in protected worker boundary. CoqPi `safeStorage` is retained pending a justified integration choice.
8. No production code or migration in this gate. All legacy sources remain until migration checklists and approval pass.

## Alternatives considered

- Keychain only: simplest secret lifecycle, native owner-session protection; recovery/export and daemon access prompts need validation.
- Encrypted vault only: portable/backup-friendly, but creates custom encryption, master-key and recovery burden; not selected as primary.
- Hybrid: selected as direction, with Keychain primary and vault fallback deferred, avoiding premature custom storage.
- Per-agent env injection: rejected as normal path because it returns raw value to the process and preserves accidental/malicious exfiltration paths.
- Arbitrary command wrapper: rejected because any child command could print or transmit injected credentials.

## Risks / unresolved decisions

Keychain ACL and recovery behavior, agent identity provenance, runtime language, OS child-process sandboxing, local price source, approved models and migration scope remain unresolved. Daemon compromise and same-user malware remain residual high-impact risks. Inventory incompleteness remains explicit; it does not block architecture but does block claims of exhaustive coverage.

## Gate result

**ARCHITECTURE: REVIEW** — coherent proposal; owner decisions and fake-secret prototype gates remain. **OPENAI PILOT: HOLD.**

No implementation, real secret migration, `.env` change, remote configuration change, deployment, rotation or inherited environment modification was performed.

**Next gate:** `ABVX CREDENTIAL BROKER OPENAI PILOT IMPLEMENTATION V1` (separate authorization; do not begin automatically).
