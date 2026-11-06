# ABVX Broker Real-Key Import Readiness V2

**REAL_KEY_IMPORT_READY: YES for the explicitly accepted personal-workstation V1 interface threat model.** This is readiness to start a separate reviewed import/smoke gate, not authorization or evidence that import has happened.

Evidence: no production CLI/IPC/helper action returns a raw secret; synthetic Keychain create/update/use/delete/restart passed on isolated and default paths; an allowed mock provider operation consumed the synthetic value internally and returned a sanitized result; separate same-UID caller probes could not retrieve it through supported interfaces; exact canary scan found zero leakage; redaction and all 24 tests passed. The previous blocker, a directly invokable raw-get helper, was removed.

Accepted limits: owner-UID processes can read/modify local state and can execute arbitrary Python/Keychain APIs outside the broker interface; no signed workload identity, separate service account, or OS-level owner-code isolation is claimed. Existing `OPENAI_API_KEY` remains present by name in this session and was neither read nor migrated. A later gate must use a secure import path and independently verify actual provider/account behavior before retiring any direct environment path.

**NEXT GATE:** ABVX OPENAI REAL KEY IMPORT + MINIMAL LIVE SMOKE V1. Do not begin it as part of this proof.
