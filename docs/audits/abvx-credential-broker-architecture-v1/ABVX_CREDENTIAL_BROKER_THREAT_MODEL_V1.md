# ABVX Credential Broker Threat Model V1

**Scope:** proposed local macOS broker, registry, policy, Class A adapters, Class B workers, CLI approval, budgets and audit. This is a design threat model, not proof of implementation security.

## Assets and trust boundaries

Assets: provider credentials; WhatsApp session state; database authority; bounded capabilities; provider spend; private request/result data; policy and audit integrity. Trust boundaries: agent to Unix socket; daemon to Keychain; daemon to provider; daemon to adapter child; approval owner to capability ledger; local workspace to broker config; broker to audit file. Assume local agents and project contents may be malicious. Host OS/kernel compromise and owner-session compromise are not contained by a same-user daemon.

## Threats and V1 controls

| Threat | Control | Residual / status |
|---|---|---|
| Malicious or compromised agent requests credentials | No value API; operation allowlist; default deny; binding to project/agent/resource; bounded output | Can misuse any capability granted within its scope; compromised daemon can access credentials |
| Accidental `env`/`printenv` exposure | Future agents must not inherit brokered variables; launch allowlist; migration gate checks environment | Existing `OPENAI_API_KEY` remains exposed until separately removed; this task does not remove it |
| Prompt injection asks agent to reveal secret | No retrieval endpoint; policy independent of prompt; return operation result only | Injection may cause an allowed action or leak sensitive result data |
| Shell command exfiltrates env | No generic `with-secret`; registered command template and fixed executable; minimum env; network/egress restrictions where practical | A permitted executable/adapter may still exfiltrate; OS sandboxing needs prototype |
| Malicious child process | Signed/owned adapter inventory, immutable executable identity, structured args, timeout, cwd restrictions, output cap/redaction | Same-user child may access other same-user files unless OS sandboxed; Class B needs stronger isolation validation |
| Logs/artifacts leak secrets | Central exact-value redaction before output; no raw request/response/header logging; sanitized audit schema | Unknown transformations/encoded values can evade detection; minimize payload logging |
| Compromised repository supplies code/config | Repository is untrusted; project identity from owner registry, not repo claims alone; no repo-defined adapter auto-registration | Compromised code can request allowed operations; review adapter changes before approval |
| Stale plaintext `.env` remains readable | Migration phases; scans and explicit old-path removal gate; do not claim migration complete on import alone | Existing plaintext sources remain high risk until separately migrated and verified |
| Duplicate env names are confused | Explicit project/environment aliases to stable credential IDs; no equality assumptions | Historical copies and unknown scopes remain unresolved |
| Stolen workstation/unlocked session | Keychain OS access controls, owner-only socket/files, short TTL and revocation; screen lock/account controls are host prerequisites | Same-user session or OS compromise can access daemon; V1 is not hardware-backed remote attestation |
| Daemon compromise | Small API, no raw-value endpoint, minimal dependencies, restrictive permissions, schema validation, fail-closed policy, signed release later | Daemon necessarily handles credentials and can be fully compromised; threat remains high impact |
| Malicious adapter | Registration review, pinned executable/hash/version, allowlisted operations/args/env, tests, output controls | Hash pinning alone does not prove safe behavior; adapter supply-chain review required |
| Approval spoofing/replay | Owner-only approval CLI; bind to immutable request digest, nonce, expiry, single-use ID; revocation ledger | Local account compromise can approve; human must inspect scope and target |
| Cost exhaustion without stealing key | Atomic budgets, model allowlist, token/call ceilings, run/day caps, hard stop, retries charged | Estimates/pricing may be stale; provider-side limits recommended as independent cap |
| Audit tampering/deletion | Append-only API and file permissions; sequence/hash chaining considered only for tamper evidence; external replication deferred | Owner/root can alter local files; JSONL is not nonrepudiation |
| WhatsApp session theft | Worker-only session directory and narrow operation interface | Worker/host compromise can act as account; session lifecycle/revocation unknown |

## Out of scope / explicit residuals

V1 does not protect against compromised macOS, root/admin, malware running as the owner, owner approving a malicious request, provider compromise, malicious provider responses, or data exfiltration through an intentionally permitted result. It does not solve unknown remote scopes, credential expiration, or prior exposure. Class C raw access is not a normal capability. Class D is denied pending classification.

## Required security gates

Before pilot: fake-secret prototype; socket permission and peer identity tests; malformed/oversized request tests; policy bypass/replay tests; concurrent budget race tests; exact-value and structured redaction tests; child environment/output leakage tests; daemon restart/revocation tests; adapter allowlist review. Before each real credential import: provider scope review, application operation test, rollback, remote verification as needed, old-path removal gate, rotation decision and post-scan. No such gates are asserted passed here.

## Evidence caveat

The source inventory is PARTIAL: full reachable Git history and recursive env discovery incomplete; remote scopes/expiry/rotation mostly unknown; repeated identifier values were not compared. High findings are exposure paths, not evidence of misuse or confirmed compromise.
