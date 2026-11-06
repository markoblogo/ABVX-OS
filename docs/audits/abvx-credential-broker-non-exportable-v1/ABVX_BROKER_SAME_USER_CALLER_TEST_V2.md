# ABVX Broker Same-User Caller Test V2

A separate Python attacker process ran under the same UID and connected to the production daemon's Unix socket. It received no synthetic credential through any supported broker interface. Classifications:

| Attempt | Result |
| --- | --- |
| Direct socket request | NOT BLOCKED: creates a pending request only |
| Direct invocation of credential helper/service binary | BROKER-BLOCKED: no production credential helper binary/entrypoint remains; `macos_secitem.py get` returned no output |
| Secret retrieval request (`get`) | BROKER-BLOCKED: unsupported IPC action |
| Unsupported IPC operation | BROKER-BLOCKED |
| Capability reused for another purpose/context | POLICY-BLOCKED; same-scope bearer reuse by the same UID remains NOT BLOCKED |
| Capability file tampering | NOT BLOCKED at filesystem layer; tested model escalation was POLICY-BLOCKED on execute |
| Credential-ID/path-shaped capability ID | POLICY-BLOCKED before file access |
| Arbitrary provider URL | POLICY-BLOCKED |
| Arbitrary Authorization header | POLICY-BLOCKED |
| Environment dump request | BROKER-BLOCKED |
| Arbitrary shell command request | BROKER-BLOCKED |
| Direct broker state read | NOT BLOCKED for same UID; observed in attacker process |

This is an interface proof, not protection against arbitrary code executing as the owner. A same-owner process can import the private Python bridge or use OS Keychain APIs independently; macOS login-Keychain access controls and signing identity were not hardened here. Root and full login-session compromise are out of scope.
