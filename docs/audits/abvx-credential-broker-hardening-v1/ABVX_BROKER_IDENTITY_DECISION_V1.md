# ABVX Broker Identity Decision V1

**Decision:** keep the owner-UID Unix socket plus broker policy for this bounded pilot. Treat PID, executable path and request metadata as audit hints only. This is not a cryptographic workload identity. Do not import a real key at this gate.

| Option | Finding |
| --- | --- |
| A: UID/PID plus capabilities | UID is kernel supplied and excludes other accounts; all processes of this owner share it. PID is transient. Current capability adds approval, project, operation, model, purpose, budget and expiry. |
| B: process name/path/ancestry | Observable but mutable or reproducible by the same user; no authorization authority. |
| C: Team ID/designated requirement | Useful only with a stable trusted signing identity and a Keychain ACL or OS-enforced client check. No Developer ID is assumed. Ad-hoc signatures have no protected signing identity. |
| D: signed client helper | Adds little while the same owner can invoke the helper directly. A helper is useful only when it itself enforces policy and cannot be replaced by the caller. |
| E: separate macOS account | Meaningful local isolation for state and Keychain access; requires install/operations design and is a separate gate. |
| F: XPC code requirement | Potential native client attestation with a signed service/client, but a larger redesign and still requires protection of service state and helper invocation. |

Agent-to-daemon direct access remains the smallest pilot path. The `abvx` CLI is a convenience client, not a trusted mediator. Socket requests do not accept caller-supplied `agent` identity; owner approval is required before execute. The capability's recorded UID is checked on execute, but this cannot distinguish two processes of the owner. No security decision is based on executable basename.

Apple explains designated requirements and trusted anchors in [TN3127](https://developer.apple.com/documentation/technotes/tn3127-inside-code-signing-requirements) and [Code Signing In Depth](https://developer.apple.com/library/archive/technotes/tn2206/). The latter describes Keychain use of stable code identity and that self-signed identities can work in some local policies; such an identity has not been established here.
