# ABVX Broker Same-User Attack Matrix V1

Labels describe the local prototype, not a production security guarantee.

| Attempt | Result | Evidence / limit |
| --- | --- | --- |
| Direct socket request, same UID | NOT BLOCKED | Test connects and obtains a pending request; execution still needs approval/capability. |
| Spoof `agent` field in socket request | POLICY-BLOCKED | Unknown field rejected in synthetic socket test; OS UID is measured by peer API. |
| Reuse another same-UID capability ID | NOT BLOCKED | Bearer reference is usable by another owner process before expiry if discovered; UID binding cannot separate it. |
| Alter capability project/operation/model/budget/call ceiling | POLICY-BLOCKED | New tests deny these mutated records; same-user write access remains. |
| Replay after expiry or revoke | POLICY-BLOCKED | Existing expiry/revoke tests plus new replay test. |
| Unauthorized project/model/purpose | POLICY-BLOCKED | Allowlist and capability scope tests. |
| Raw secret through socket/CLI | POLICY-BLOCKED | Unsupported action and command tests. Direct helper path remains below. |
| Arbitrary URL or Authorization header | POLICY-BLOCKED | Execute request rejects extra fields; provider URL/header are fixed in broker code. |
| Read state files as same UID | NOT BLOCKED | `0600`/`0700` exclude other UIDs, not owner processes. |
| Run raw-get Keychain helper directly | NOT BLOCKED | Helper exposes `get` through stdin/stdout; no login-Keychain unintended-caller test was run. |
| Other macOS user reads socket/state | OS-BLOCKED by mode/UID design; NOT TESTED end to end | No separate-account adversarial test in this gate. |
| Root, stolen login session, direct inherited env key | OUT OF SCOPE | No realistic local isolation claim against these. |

Identifiers are now constrained to 32 lowercase hex characters before file lookup, closing a path-shaped identifier traversal path. A disconnected socket client no longer terminates the daemon. These changes do not turn JSON state into tamper-proof authorization.
