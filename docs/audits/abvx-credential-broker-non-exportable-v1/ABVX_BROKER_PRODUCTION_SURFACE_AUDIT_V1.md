# ABVX Broker Production Surface Audit V1

**Production operations returning raw secret: 0.** `bin/abvx-secrets` only invokes the Python broker. `macos_secitem.py` has no CLI dispatch. The old `keychain_helper.swift` source was removed, and no compiled helper matching `keychain-helper-*` was found in the standard broker bin directory at this gate.

| Surface | Purpose / authorization | Internal secret access | Raw secret return |
| --- | --- | --- | --- |
| CLI `serve` | Start owner-UID socket; local operator | Only for later approved executes | No |
| CLI `list`, `status` | Presence metadata; local filesystem user | Existence query only | No |
| CLI `request` / IPC `request` | Create pending scoped request; same owner UID at socket | No | No |
| CLI `approve` | Interactive terminal owner approval | No | No |
| CLI `revoke` | Revoke capability; local filesystem user | No | No |
| CLI `run` / IPC `execute` | Approved, scoped provider operation; same UID and valid capability at socket | Yes, transiently | No; only sanitized provider result |
| CLI `audit` | Read local audit events; local filesystem user | No | No in broker-generated events |

Unsupported CLI commands fail argument parsing. Unsupported socket actions, including `get`, `export_secret`, environment dump and shell execution, are rejected. Caller-supplied URL and Authorization header are rejected by the execute schema. `SecItemStore._read_for_provider` is an internal Python method, not a supported CLI/IPC operation; arbitrary owner-code invocation remains outside this V1 boundary.
