# ABVX Broker Non-Exportable Test Report V1

**Result: 24/24 focused tests PASS.** The prior 21 tests remain passing after one deliberate replacement: the old isolated-Keychain helper test now uses the in-process SecItem bridge. Three new synthetic tests passed: Keychain → mock provider operation/restart/error redaction/canary scan; separate same-UID attacker process; default-Keychain synthetic SecItem lifecycle. The isolated synthetic Keychain test also passed. No OpenAI call or real-key import occurred.

The mock provider observed the expected synthetic value internally; the caller received only sanitized operation output. A provider exception containing that value was redacted before caller output and audit persistence. The scanner reported zero exact canary occurrences in stdout, stderr, broker-managed files and reports. The attacker could read and mutate same-UID state files, as expected, but its tampered model was denied before provider execution.

`OPENAI_API_KEY` was checked for name presence only (`present`); its value was not read. No dependency was installed, no sibling repository was changed, and no commit/deployment occurred. These tests do not prove protection from arbitrary owner-executed code or login-Keychain ACL identity isolation.
