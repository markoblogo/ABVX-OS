# ABVX Broker Real-Key Import Readiness V1

**REAL_KEY_IMPORT_READY: NO**

**LOCAL_HARDENING_STATUS: PARTIAL.** Policy scope, identifier validation, owner-UID binding, socket resilience, fake Keychain lifecycle and a modern synthetic `SecItem` probe have evidence. The production helper still has a directly invokable raw-secret retrieval action, and no stable OS-enforced signed identity or login-Keychain ACL was proven. Same-user state is mutable. The current agent environment still contains the `OPENAI_API_KEY` variable name; its value was not read.

**ACCEPTED_LIMITS:** same-owner processes can access owner-only files and the socket; PID/path metadata is for audit; mock provider results do not prove real model entitlement, billing or successful integration. These limits are acceptable for the synthetic pilot. Direct raw helper access is a blocker for the real import goal.

**NEXT GATE (one):** design and prove a policy-enforcing Keychain access service with protected installation/state, using synthetic data and an unintended same-user caller test, then reassess import readiness. A separate macOS service account is the strongest local option; a signed helper is useful only if it cannot be invoked to return a raw secret and its signing/upgrade identity is verified. Real-key import and smoke testing require a later explicit gate.
