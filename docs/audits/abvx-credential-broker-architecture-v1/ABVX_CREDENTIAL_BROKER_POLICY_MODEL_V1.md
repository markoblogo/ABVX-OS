# ABVX Credential Broker Policy Model V1

## Evaluation

Default deny. Normalize request, authenticate local peer/context, resolve explicit `(project, environment, alias)` mapping, then evaluate every constraint. Any missing, unknown, conflicting or stale field denies. Rules may narrow authority; they cannot widen registry-supported operations. Production writes/database mutations require OWNER_APPROVAL even if a broader AUTO rule exists.

Required request bindings: `agent`, `project`, `credential_id`, `provider`, `operation`, `resource`, `environment`, optional `model`, `purpose`, `estimated_cost`, `max_tokens`, `request_count`, `run_id`, `time_window`, `ttl`. Enforce agent/project identity from broker-owned configuration and peer evidence, not caller-supplied strings alone.

## Modes

| Mode | Behavior |
|---|---|
| `AUTO` | Only exact, preapproved low-risk operation/resource/model within all caps and current budget. |
| `OWNER_APPROVAL` | Queue immutable request summary. Owner approval produces a short-lived, revocable, single-use or narrowly reusable capability. |
| `DENY` | No dispatch; explain safe policy reason without credential/provider diagnostics. |
| `BREAK_GLASS` | Separate owner-only workflow, explicit justification and confirmation, minimum scope/TTL, enhanced audit. Raw value release is unavailable in normal V1. |

Capability claims: `capability_id`, requester identity, project, credential ID, provider, operation, resource constraints, environment, model, call/token/budget ceilings, request digest/nonce, approval ID, issued/expiry time, revocation reference. Never carries a credential, credential-derived fingerprint, or reusable provider token. Authorization is rechecked at use; revocation is immediate for subsequent calls. Daemon restart fails closed if capability/revocation state cannot be restored safely.

## Budget rules

Limit hierarchy: per request <= per run <= project/day; provider and owner ceilings also apply. Atomically reserve estimated maximum before dispatch; track actual provider usage when present, otherwise conservative estimate. Reconcile without releasing budget for uncertain/incomplete calls. Retry attempts consume count and budget. At warning threshold notify in sanitized result; at hard limit deny further call. Unknown model price or token ceiling denies metered call unless explicit owner cap. Day boundary/timezone is policy-defined and auditable. Concurrent reservations must serialize per budget key.

## Example policies (illustrative, inactive)

```yaml
policy_id: jekyll-openai-qa-v1
mode: OWNER_APPROVAL
agent: codex
project: jekyll-toki-pona
credential_id: openai.primary
provider: openai
operation: responses.create
resource: { purpose: translation-qa }
environment: local
models: [OWNER_APPROVED_MODEL_IDS]
limits: { per_request_usd: 0.25, per_run_usd: 2.00, project_day_usd: 2.00,
          max_calls: 20, max_output_tokens: OWNER_SET_CEILING }
ttl: 4h
```

```yaml
policy_id: menton-resend-test-v1
mode: OWNER_APPROVAL
agent: codex
project: menton
credential_id: resend.shared
provider: resend
operation: email.send
resource: { from_domain: OWNER_APPROVED_DOMAIN, recipients: OWNER_APPROVED_TEST_RECIPIENTS }
environment: local
limits: { max_messages: 5, project_day_usd: OWNER_SET_CAP }
ttl: 30m
```

Placeholders are not active values or approvals. Policy files contain no secrets. Class D and Class C default to DENY; unknown provider scopes never imply permission. Read-only operations and production mutations use distinct operations/resources and separate rules.
