# DONOR-HARVEST-001 — Convert Book Research into ABVX Adoption Plan

Status: STOP_FOR_HUMAN_DECISION
Cost class: NORMAL

## 1. Current ABVX capability baseline

| Area | Current ABVX baseline | Real near-term gap |
| --- | --- | --- |
| Web/public research | manual web work, intake, evidence, project-local sensors, bounded read-only Cortex retrieval | broader external discovery coverage for future target/company search |
| Cortex/context retrieval | `read-only-cortex-context-retrieval` capability, ContextRequest → ContextPack bridge | no broader research/discovery runtime |
| Provider routing | local provider boundaries for context and mission state, donor-first policy | no generic external-action substrate admitted |
| Evidence | machine-readable evidence, portfolio state, lessons, bakeoff harness | no technical trace layer for model/runtime observability |
| Cost classes | CHEAP/NORMAL/EXPENSIVE documented and enforced | no trace-level cost telemetry |
| Agent/tool execution | local-first playbooks, CLI adapters, bounded providers | no justified workflow runtime yet |
| MCP/connectors | existing connected tools already cover several near-term actions | fragmented but adequate for current action volume |
| Gmail/email actions | existing connectors/MCP available | no bulk distribution surface; no repeated outreach loop yet |
| Content publishing | proven project-specific publishing adapters | unrelated to target/outreach runtime |
| Playbooks/workflows | deterministic local playbooks, not an orchestrator | no multi-step external workflow runtime if future volume grows |
| Analytics/observability | project-local Plausible, GSC donor path, ABVX evidence | no technical LLM/workflow observability |
| Target/contact records | portfolio/project state only | no persistent outbound target/contact lifecycle yet |
| Outreach | human-gated, mostly manual/future | no bounded discovery + qualification + follow-up loop yet |
| CRM | no admitted CRM | future operator surface only after real lead volume |
| Presentation generation | Codex Slides already recorded as the narrow donor direction | no reason to add a second presentation runtime now |

## 2. Eight-candidate scorecard

| Donor | ABVX capability | Current ABVX mechanism | Real gap | What donor adds | Duplication risk | Integration surface | Self-host / external service | Cost reality | Maintenance burden | License / practical restriction | Adoption form | Timing | First real acceptance test |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Agent-Reach | external discovery / research sensor | manual web research + evidence + ContextPack | wider source coverage for target/company discovery | source/platform reach without per-site API contracts | medium | optional sensor feeding normalized evidence/context objects | likely self-hosted runtime with auth/cookie/proxy burden | medium | high | scraping breakage and session maintenance | COMPONENT | PILOT_NOW | bounded European agro-broker/company discovery mission with normalized evidence output |
| Composio | authenticated external action substrate | MCP + existing connected tools + local adapters | only if repeated authenticated cross-SaaS actions become painful | broad app integration layer | high | optional action component behind ABVX approval gates | hosted or self-hosted patterns, but extra integration layer either way | medium | medium | duplicate connectivity until a concrete repeated loop exists | COMPONENT | DEFER | one repeated Gmail/GitHub/calendar/CRM action loop that current MCP/connectors cannot cover cleanly |
| Langfuse | technical observability | ABVX business/process evidence only | no trace/span/token/cost/error layer | technical traces, spans, latency, token/cost, eval surface | low | workflow instrumentation for one bounded ABVX path | hosted or self-hosted; both need setup | medium | medium | license/hosting choice must stay explicit | COMPONENT | PILOT_NOW | instrument one ABVX workflow and compare ABVX evidence vs Langfuse trace |
| Activepieces | workflow/orchestration runtime | playbooks + local scripts + approval gates | only after a real multi-step external workflow exceeds playbooks | AI/MCP-oriented workflow runtime | high | future bakeoff competitor only | self-hosted runtime | medium | medium-high | overlaps with n8n and broadens scope fast | PATTERN | DEFER | enter only a bounded workflow-runtime bakeoff if a real approval/action loop outgrows playbooks |
| n8n | workflow/orchestration runtime | playbooks + local scripts + approval gates | same as above | mature automation ecosystem and integrations | high | future runtime under ABVX control plane | self-hosted/runtime service | medium-high | high | too broad unless real workflow volume exists | RUNTIME | PILOT_WHEN_NEEDED | bounded workflow-runtime bakeoff once a real enrichment → approval → action loop exists |
| Twenty | CRM / target lifecycle surface | portfolio/project state, evidence, manual notes | no persistent contact/follow-up lifecycle once outbound volume grows | target/contact/deal operator surface | medium | operator surface under ABVX, not control plane | self-hosted/runtime service | medium-high | high | premature before real pipeline volume | RUNTIME | PILOT_WHEN_NEEDED | pilot only after meaningful target count + concurrent conversations + follow-up burden exist |
| Listmonk | bulk email / newsletter distribution | none admitted; one-to-one actions can stay manual | no broadcast distribution surface if owned audience appears | owned mailing-list and campaign runtime | low-medium | separate distribution runtime | self-hosted/runtime service | medium | medium | not for personalized outreach; audience/consent required | RUNTIME | DEFER | pilot only after real opted-in audience and recurring broadcast need exist |
| Presenton | presentation generation | Codex Slides donor direction + current manual slide path | no current pain beyond normal deck production | alternate AI deck generator | high | comparison-only against existing slide path | external/self-hosted unknown relevance for ABVX | medium | medium | already covered more narrowly by Codex Slides | REFERENCE | PILOT_WHEN_NEEDED | same-brief deck comparison when a real AMI/fund/client deck is needed |

## 3. Candidate decisions

### Agent-Reach

- Decision: keep as an optional discovery component, not a core runtime.
- Why: it addresses the clearest FIND gap without forcing CRM or workflow-engine adoption.
- Risk boundary: scraping/auth/session fragility must stay bounded inside the pilot.

### Langfuse

- Decision: admit only as a technical observability component candidate.
- Why: ABVX evidence already covers business/process truth, but not trace/span/token/cost/error telemetry.
- Boundary: ABVX remains source of truth for process evidence; Langfuse would own only technical traces.

### Activepieces vs n8n

- Decision: NEITHER_YET.
- Lean if a bakeoff becomes necessary: n8n is the stronger benchmark because of maturity and ecosystem breadth.
- Why no pilot now: current ABVX playbooks and local adapters are still the correct scope; a workflow runtime would be premature.

### Composio

- Decision: defer.
- Why: current MCP/connectors already cover the near-term action surface adequately enough that Composio would mostly duplicate connectivity.

### Twenty

- Decision: keep as the leading future CRM runtime candidate, but only when needed.
- Trigger: roughly 50+ live targets, 10+ concurrent conversations, or repeated missed follow-ups across 2+ projects.

### Listmonk

- Decision: defer.
- Trigger: real opted-in audience plus recurring broadcast distribution, not one-to-one outreach.

### Presenton

- Decision: reference only.
- Trigger: a real commercial/fund/client deck where the existing slide path is slow enough to justify a direct comparison.

## 4. Observe → Find → Reason → Act → Learn mapping

| Phase | Current ABVX owner | Candidate fit |
| --- | --- | --- |
| OBSERVE | ABVX evidence, project-local analytics, GSC/Plausible sensors | Langfuse for technical traces only |
| FIND | manual web research, intake, ContextPack | Agent-Reach |
| REASON | ABVX + Cortex qualification, strategy, human approval | no donor selected; keep internal |
| ACT | MCP/connectors, local adapters, human gates | Composio later; n8n/Activepieces only if real workflow runtime becomes necessary |
| LEARN | evidence, lessons, portfolio state | keep internal |

ABVX/Cortex remains the control and decision plane.

## 5. Selected PILOT_NOW donors

1. Agent-Reach
2. Langfuse

Both satisfy a real near-term gap, have bounded acceptance cases, and do not force a platform rewrite.

## 6. Pilot mission A

| Field | Plan |
| --- | --- |
| Mission name | DONOR-PILOT-AGENT-REACH-001 — Bounded Agro Discovery Sensor |
| Problem | future company/broker discovery needs broader source reach than current manual search provides |
| Current baseline | manual web research + intake + evidence + ContextPack |
| Donor role | optional discovery sensor only |
| Real input | one bounded target brief such as European agro brokers / commodity companies |
| Expected output | normalized evidence objects and a compact candidate list with provenance |
| Acceptance criteria | materially better source coverage than current manual path, outputs normalize cleanly, no broad runtime coupling required |
| Cost ceiling | NORMAL |
| Human gates | pilot target brief approval; any authenticated/sensitive source use |
| Stop conditions | auth/proxy burden dominates value; outputs cannot normalize; source fragility is too high |
| Rollback / exit | keep findings as evidence only and return to manual research path |

## 7. Pilot mission B

| Field | Plan |
| --- | --- |
| Mission name | DONOR-PILOT-LANGFUSE-001 — Single-Workflow Technical Trace Comparison |
| Problem | ABVX lacks technical observability for token/cost/latency/error analysis |
| Current baseline | ABVX evidence records business/process outcomes only |
| Donor role | technical trace component only |
| Real input | one existing ABVX workflow with clear request/response boundaries |
| Expected output | one trace set showing spans, model/provider, latency, tokens, errors, and cost where available |
| Acceptance criteria | technical trace adds decision-useful signal beyond ABVX evidence without redefining ABVX state ownership |
| Cost ceiling | NORMAL |
| Human gates | any hosting/license choice; any credential boundary |
| Stop conditions | setup cost exceeds single-workflow learning value; trace ownership becomes architecture creep |
| Rollback / exit | remove instrumentation and keep ABVX evidence as the only source |

## 8. Explicitly deferred or rejected

- Deferred: Composio, Activepieces, n8n, Twenty, Listmonk
- Reference only: Presenton
- Rejected now: adopting both Activepieces and n8n in parallel; adopting a CRM before real outbound volume; adopting bulk-email runtime for one-to-one outreach

## 9. Registry/state changes made

- updated `registries/donor-capability-matrix.json`
  - corrected Agent-Reach and Composio from stale `UNRECORDED`
  - added adoption form, timing, target capability, and first acceptance test
  - added Langfuse, Activepieces, n8n, Twenty, Listmonk, Presenton donor planning entries
- updated `registries/external-candidates/book-factory-003.json`
  - added missing Activepieces evidence entry
- updated `portfolio/lessons.json`
  - recorded the publication-research → donor-intelligence reuse lesson

## 10. Reusable lesson

Publication research can be harvested into donor intelligence.

Preferred loop:

publication research
→ candidate evidence
→ donor matrix
→ capability mapping
→ later adoption decision

This avoids paying twice for the same repository research.
