# PLATFORM-CONSTITUTION-001 — ABVX operating constitution and autonomy gap audit

Date: Monday, August 10, 2026
Cost class: CHEAP

Scope: policy, autonomy, and roadmap clarification only. No new subsystem, UI, runtime refactor, or automatic permission expansion.

## External reference

The owner supplied a Mast Group AI-first constitution reference (`constitution-for-agent.md`) as an external pattern source. This audit does not copy that document. It uses it only to sharpen ABVX's own operating stance as a one-person operating system.

## Twelve-principle audit

| Principle area | Status | Existing ABVX evidence | Concrete gap | Does it matter now? | Cheapest next improvement |
|---|---|---|---|---|---|
| 1. Explicit operating target beyond throughput | PARTIAL | `docs/product-vision.md`, donor-first policy, mission evidence, portfolio strategy all imply economic and durable-asset goals | No canonical single operating-constitution document stated the full target function | Yes | Add `docs/operating-constitution.md` target function |
| 2. Clear human-owned strategic layer | STRONG | `docs/autonomy-policy.md`, human queue, ADRs such as FOUNDATION-003A, portfolio state waiting gates | Human strategic priority changes are not always turned into durable decision records | Yes | Add decision-memory pattern and use it later |
| 3. Clear AI observation boundary | STRONG | autonomy policy, read-only Cortex retrieval, analytics observation docs, validation commands | Observation sources are distributed across docs rather than summarized once | Low | Summarize in operating constitution |
| 4. Clear AI proposal boundary | STRONG | publish handoffs, audits, donor evaluations, content ops control plane, bakeoff reports | No single ladder view tied proposals to autonomy levels | Medium | Add autonomy ladder mapping |
| 5. Clear autonomous execution boundary | PARTIAL | local validation, deterministic playbook replay, evidence generation, state exports | L1 vs future L2 routine execution was implicit, not explicit | Yes | Add L0-L4 ladder and list promotion candidates without enabling them |
| 6. Hard approval gates for consequential actions | STRONG | live microphone gate in CoqPi state, mission gates, deployment/publication review patterns, fail-closed mission-state boundary | Some publication and ops paths rely on convention more than one canonical constitution text | Medium | Consolidate policy in constitution |
| 7. Verifiable decision quality | STRONG | ADRs, audits, validation tiers, evidence model, schema validation, replayable playbooks | Strategic human decisions outside technical ADRs are less normalized | Yes | Decision-candidate path later |
| 8. Durable decision memory | WEAK | ADRs, portfolio state, strategy, lessons, evidence refs, Cortex retrieval bridge | Many product pauses, architecture choices, and priority shifts can remain implicit or scattered | Yes | Introduce smallest future decision-candidate contract |
| 9. Outcome and learning loop | PARTIAL | `portfolio/lessons.json`, evidence records, project events, analytics observations, bakeoff outputs | Expected outcome / hypothesis is not consistently normalized before action | Yes | Add minimal expected-outcome contract to future evidence/state work |
| 10. Owner model / operator context | PARTIAL | human queue, portfolio state constraints, current waiting reasons, interaction preferences in policy/docs | No explicit operator input model for attention cost, workload, or working mode | Medium | Define later as bounded operator input, not surveillance |
| 11. Donor-first process adaptation | STRONG | `docs/donor-first-policy.md`, donor matrix, capabilities registry, repeated thin-adapter choices | None material | Yes, but already covered | Preserve explicitly in constitution |
| 12. Multi-founder synchronization / shared leadership operating cadence | NOT_APPLICABLE_YET | ABVX is explicitly one-person today | Not relevant until ABVX stops being single-owner operated | No | Keep out of near-term work |

## Current autonomy ladder assessment

### L0 OBSERVE

Already operational:

- `./bin/abvx validate`
- schema and registry inspection
- read-only Cortex context retrieval
- analytics observation capture model
- health/freshness observations
- bakeoff evidence inspection

### L1 PROPOSE

Already operational:

- audit reports and ADR proposals
- content ops packets and publication handoffs
- roadmap corrections
- portfolio state updates
- donor/provider recommendations

### L2 ROUTINE EXECUTION

Technically closest candidates, but not enabled by this mission:

1. deterministic validation
2. compact evidence recording
3. routine analytics observation capture
4. known publication playbooks
5. known metadata enrichment
6. known health observation capture

Promotion blockers:

- no explicit ladder document before now
- some human gates still convention-based
- no durable decision-candidate layer for cases where routine work changes policy assumptions

### L3 BOUNDED OPTIMIZATION

Weak today. ABVX has bounded validation tiers and replay logic, but not a policy-approved parameter-tuning layer. This is correctly not enabled.

### L4 STRATEGIC

Clearly human-owned and should remain so.

## Decision-memory gap

ABVX captures mission and technical provider decisions relatively well through ADRs and evidence. It captures owner strategic intent less reliably when the change is:

- a product pause;
- a publication-architecture choice;
- a priority reorder;
- a scope veto;
- a human timing gate.

Smallest future mechanism:

human decision
→ decision candidate
→ owner review
→ durable decision
→ Cortex retrieval eligibility

This should be implemented only if it can reuse existing evidence/decision structures with a thin adapter or minimal schema.

## Outcome / learning loop audit

Already present:

- action evidence
- run results
- compact project events
- portfolio lessons
- analytics observations
- state updates

Missing minimum contract:

- explicit expected outcome or hypothesis before execution
- explicit comparison between expected and actual outcome
- systematic path from repeated lesson to policy/process correction

This is a meaningful gap because ABVX increasingly runs cross-project operational loops where learning quality matters as much as raw completion.

## Owner model audit

Current support is bounded and useful but incomplete:

- priorities exist in portfolio state and strategy
- human-only blockers and waiting reasons are recorded
- communication readiness has been captured where explicitly provided
- not-before dates and attention gating already exist

What is missing is not more surveillance. It is a small operator input model for work-relevant context such as:

- current focus
- acceptable interruption cost
- current workload/context-switch pressure
- explicitly declared communication or availability constraints

This matters, but it should follow the decision-memory and outcome-loop improvements, not precede them.

## Top three high-ROI gaps

Ranked by impact × leverage ÷ attention cost:

1. Human decision-candidate capture  
   Highest leverage because it improves strategy continuity, retrieval quality, and autonomy safety across every active project.

2. Expected-outcome → actual-outcome learning contract  
   High leverage because it improves evidence quality, lesson quality, and future routine automation decisions.

3. Explicit autonomy ladder and future L2 promotion policy  
   Useful now because playbooks, validation, and observation loops already exist, but should not be promoted implicitly.

Deferred for now:

- richer operator input model
- any multi-founder process layer
- L3 optimization mechanisms

## Roadmap correction

The existing roadmap was too coarse and no longer reflected the current execution order. It should preserve the owner's current economic sequence:

1. Content Ops completion and real publications
2. 1D3X UGA → POP bounded replacement
3. AMI final editorial completion
4. AMI + Cortex public project projection on ABVX
5. CoqPi live validation / communication readiness
6. real Opportunity/Search/Outreach campaigns
7. Book Factory MVP and publication throughput
8. Public Surface Health and broader analytics/media loops as scheduled

Constitution-derived platform work should be inserted only when it cheaply strengthens those loops.

## Conclusion

ABVX is already strong on donor-first behavior, evidence, validation, and hard human gates. Its main gap is not autonomy ambition. Its main gap is durable memory for important human decisions and a tighter expected-outcome learning contract. That is the cheapest path to make future autonomy safer and more useful without building another framework.
