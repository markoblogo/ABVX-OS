# Architecture bakeoff protocol

Use this protocol before permanently integrating a competing component.

1. State the architectural role to fill and the baseline (including “build nothing yet”).
2. Record candidates, versions/commit references, license, data access, and operating assumptions.
3. Prepare representative, redacted fixtures from [acceptance-fixtures.md](acceptance-fixtures.md).
4. Define measurable functional, reliability, latency, isolation, security, cost, maintenance, and exit criteria before running the test.
5. Run the same bounded scenarios for each candidate and preserve logs, outputs, failures, and resource use as Evidence.
6. Classify the result as PASS, CONDITIONAL PASS, or FAIL. Record patterns worth retaining even on failure.
7. Record a Decision and an ApprovalGate. The result must be `STOP_FOR_HUMAN_DECISION` before permanent integration.

No bakeoff authorizes production writes, credential sharing, broad repository access, or a paid service. Conditional passes require explicit conditions, owner, expiry, and re-test date.
