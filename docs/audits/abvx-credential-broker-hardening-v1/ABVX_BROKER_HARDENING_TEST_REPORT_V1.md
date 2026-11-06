# ABVX Broker Hardening Test Report V1

**Result: 21/21 focused tests passed** on macOS, including the original 18 tests and three new synthetic cases (identifier traversal, mutated capability scope, UID/expiry replay). The socket test additionally rejects a spoofed agent field and unsupported direct secret retrieval. The original mock provider never made an OpenAI request. A race in the test's daemon restart readiness check was corrected; the daemon now handles a client disconnect during response. No real key, real provider call, paid dependency, or sibling repository was used.

Synthetic `SecItem` isolated-Keychain probe: compiled with the local Swift toolchain; add/read/update/delete succeeded. It did not test login-Keychain ACL, signing identity, unrelated process access, or a real credential. The existing fake isolated-Keychain lifecycle test also passed.

State modes: broker creates directories `0700`, JSON/audit/lock files `0600`, socket `0600`; existing integration test asserted socket and temporary Keychain modes. Same-UID read/write is a known limit. `OPENAI_API_KEY_PRESENT=True` in this process was observed by checking the name only; value and source were not inspected.

The workspace contains extensive unrelated pre-existing modified/untracked files. This gate changed only the broker Python file, its focused test, a synthetic Swift probe, and this hardening report folder. No Git commit or deployment was made.
