# ABVX Broker Secret Canary Report V1

**Exact canary occurrences outside authorized synthetic Keychain/test memory: 0** in the automated synthetic operation scenario. A unique runtime-generated canary was created in an isolated temporary Keychain, updated, internally used twice by the mock provider (including after broker/Keychain object restart), and deliberately embedded in a mock provider error. The broker returned a sanitized result/error. The test scanned captured stdout, stderr, broker audit, request/capability/state files, and generated reports for the exact updated canary; no occurrence was found. The isolated Keychain was excluded as authorized storage and deleted during cleanup.

The separate same-UID attacker test returned booleans only; no secret was supplied to that process. The default-Keychain lifecycle used another unique synthetic value, then deleted the item. No real credential value was read, printed, stored in reports or used for an API call.
