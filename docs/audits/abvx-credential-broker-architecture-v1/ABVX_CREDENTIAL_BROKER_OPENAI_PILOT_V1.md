# ABVX Credential Broker OpenAI Pilot V1

**Gate status:** HOLD before implementation. This is a design; no key import, environment removal, provider call, or runner change occurred.

## Target

Future mapping: explicit `(project, environment, OPENAI_API_KEY) -> openai.primary`; do not infer that values in other projects are equal. Agent submits `responses.create` to local broker; broker calls OpenAI and returns bounded response plus sanitized usage/cost. Codex/agents must not inherit the key in the eventual pilot target. Current process exposure is still observed by variable name, origin/lifetime unknown; it remains untouched in this gate.

## Operation request/response

Required request: project, purpose, run ID, approved model ID, input payload/schema, maximum output tokens, timeout, retry ceiling and budget ceiling. Caller cannot set endpoint, auth headers, arbitrary SDK options, credential ID outside explicit project mapping, or provider URL. Broker validates model and token limit, reserves budget atomically, dispatches, reconciles usage, sanitizes errors, and returns only requested response fields. Request and output size caps are needed before implementation.

Policy dimensions: agent, project, `openai.primary`, provider `openai`, operation `responses.create`, purpose, model allowlist, local environment, calls/run, tokens/request and run, cost/request/run/project/day, TTL, timeout and retry count. V1 starts OWNER_APPROVAL for QA runs; AUTO only after bounded routine profile is explicitly reviewed. Deny unapproved model, unknown cost, exceeded usage, stale capability, arbitrary tools/function execution, or unbounded retries. Tool-enabled model operations require a distinct later policy.

## Cost and reliability

Use owner-selected model IDs and conservative local price table with version/effective date; no model or price is selected by this document. Count each attempt; reserve maximum estimated cost before request; use provider-reported token usage for reconciliation where available. Warn at a configured fraction; hard stop at run and project/day ceilings. Prevent parallel overspend with atomic reservations. A request with unavailable pricing requires an explicit owner cap or is denied. Set finite connect/overall timeouts, bounded retries only for classified transient failures, exponential backoff with jitter, and no automatic retry for ambiguous non-idempotent operations without a request-id strategy. Return generic sanitized error class and retryability, not raw SDK exception/headers/body.

## ABVX translation runner compatibility

Inventory confirms ABVX translation/regression scripts use `OPENAI_API_KEY`, but exact runner list and contract must be reconfirmed in implementation gate. Future adapter should replace credential acquisition at a narrow client boundary and preserve each runner's task/result semantics. Pass project and purpose explicitly (e.g. translation, regression QA); never inherit key into the runner/agent process. Preserve supported streaming only if broker can bound/redact it safely; otherwise pilot non-streaming first. Add a fake adapter for offline tests and a compatibility matrix for model, input/output token behavior, retries and structured response parsing. No broad runner refactor without evidence.

## Pilot sequence and gates

1. Fake-secret prototype proves socket, approval digest, capability revocation, Keychain access, atomic budgets and redaction.
2. Select one ABVX project and one QA operation; approve model/token/request/run/day limits and local pricing source.
3. Implement adapter behind disabled-by-default policy; tests cover zero inheritance, denial cases, error sanitization, retries, concurrency and output limits.
4. Owner separately authorizes controlled real credential import and provider call; do not print or compare values.
5. Verify application behavior and provider usage; document rollback and determine whether exposure history calls for rotation.
6. Remove old environment injection only after integration and rollback gates; scan afterward.

## READY/HOLD determination

**HOLD.** Architecture is sufficiently specified for a dedicated implementation proposal, but pilot inputs are not yet resolved: exact runner entrypoints/contracts, approved model IDs, pricing source/version, cost/token ceilings, daemon runtime/identity proof, and Keychain recovery/ACL behavior. The PARTIAL inventory and current `OPENAI_API_KEY` exposure make scoping important; they do not authorize changing it here.
