# ABVX Credential Broker Adapter Model V1

## Adapter contract

An adapter is a broker-owned, versioned implementation of a fixed operation schema. It declares provider, operation IDs, execution class, credential IDs/types, input/output schemas, data sensitivity, resource constraints, cost model, timeout, retry policy, output bounds and redaction requirements. Project repositories cannot register adapters at runtime.

### Class A provider adapter

Broker constructs provider request from validated structured input, attaches credential internally, performs operation, parses a narrow response, strips headers/diagnostics, applies exact-value and pattern redaction, records usage/cost, returns bounded result. No arbitrary URL, header, method, code, or provider client injection from agent. Host allowlists and redirect policy prevent credential forwarding to unapproved hosts. Retries are bounded and charged.

### Class B process adapter

Registration pins an owned executable path/version and fixed command template. Inputs are typed fields mapped to arguments; no shell interpolation, arbitrary flags, command string, cwd, env name, or executable path supplied by agent. Workdir is a registered project subdirectory or isolated temp directory. Environment is constructed from an allowlist, never inherited wholesale; credential is present only for exact process lifetime. Set timeout, process-group termination, output byte limits, stdin policy and sanitized error handling. Apply OS sandbox/network restrictions where feasible and prove behavior in fake-secret prototype. If these controls cannot be met, reject or redesign as Class A.

Forbidden pattern: `with-secret <credential> -- <arbitrary command>`. Never pass secret on argv, logs, shell history, error text, or requester-visible environment. A child process can still read its own environment; its code is therefore trusted and security-reviewed.

## Registry and lifecycle

Adapter registry fields: `adapter_id`, `version`, `provider`, `operations`, `execution_class`, `executable_identity`, `input_schema`, `output_schema`, `credential_types`, `resource_allowlist`, `environment_allowlist`, `workdir_policy`, `network_policy`, `timeout_ms`, `retry_policy`, `max_output_bytes`, `redaction_profile`, `cost_model`, `owner`, `status`, `reviewed_at`. Status starts DISABLED; activation requires review and tests. Updates create a new version and review; no in-place silent policy widening.

## Initial adapter candidates

| Operation | Class | V1 boundary |
|---|---|---|
| `openai.responses.create` | A | Fixed endpoint/SDK operation, approved models, bounded input/output tokens, project/purpose and cost caps |
| `github.repo.read` | A | Explicit repository and read-only endpoints; write scopes unknown and excluded |
| `resend.email.send` | A | Approved sender domain and recipients; low message ceiling and approval |
| search/news/data API query | A | Provider-specific operation and request/response schema; D until consumer/scope classified |
| `vercel.deploy` | B | Not enabled in V1; fixed CLI template only after OIDC semantics and environment are audited |
| WhatsApp worker operation | B | Worker retains session; structured approved action only; no session path or state returned |
| MN7R operation | B | Prefer application-owned endpoint/service; database mutations need stronger policy; scopes unknown |

## Compatibility and acceptance

Existing ABVX translation runners that read `OPENAI_API_KEY` need a future thin client/adapter seam: replace direct SDK credential acquisition with a broker operation client while preserving runner input/output contracts and project/purpose identity. Do not adapt by setting the key in parent agent env. Before adoption inventory call sites, map models/tokens/retries, ensure streamed responses are supported safely, and define offline/test fake adapter. CoqPi may continue as an isolated trusted Class B process using Electron safeStorage until broker-native calls demonstrate equivalent behavior.

Adapter acceptance includes schema validation, authorization recheck, no secret in argv/stdin/stdout/stderr/audit, exact known-value redaction, host allowlist, timeout/termination, oversized output handling, replay behavior, budget concurrency, and sanitized failure tests. All acceptance remains future work.
