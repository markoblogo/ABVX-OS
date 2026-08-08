# Domain model

Entities are minimal records with stable IDs, timestamps where relevant, provenance, and relations. Relations are graph edges (`subject`, `predicate`, `object`, optional evidence and confidence), not assumptions that everything belongs to one hierarchy.

| Entity | Purpose | Typical relations |
|---|---|---|
| Project | Independently owned product/repository/workstream | has outcome, mission, task, capability |
| Outcome | Desired measurable result | served by mission, supported by evidence |
| Mission | Bounded pursuit of an outcome | decomposes to tasks, emits events |
| Task | Actionable unit with owner/status | belongs to mission, affects project |
| Event | Immutable intake or system occurrence | from source, relates to entities, routes to work |
| Source | Origin and trust/policy boundary | emits events, permits actions |
| Person | Human identity or participant | owns, approves, belongs to organization |
| Organization | Company, group, or external body | owns project, publishes source |
| Opportunity | Potential value/revenue/relationship | supported by evidence, becomes mission |
| RevenueAsset | Asset that may produce or enable revenue | linked to project, channel, opportunity |
| MediaChannel | Distribution surface | publishes content, reaches audience segment |
| ContentAsset | Text, image, audio, video, or package | derived from event, published to channel |
| ProofAsset | Evidence of capability, outcome, or reputation | supports decision/opportunity |
| AudienceSegment | Useful grouping of people/needs | connected by affinity edges |
| AffinityEdge | Weighted relationship between entities/segments | has confidence, source, expiry |
| Capability | Internal function or reusable implementation | provided by project/provider, evaluated |
| ExternalCandidate | OSS/API/MCP capability under review | candidate for capability, has decision |
| Experiment | Time-bounded test of a hypothesis | uses fixtures, produces evidence |
| Decision | Recorded choice and alternatives | based on evidence, has approval gate |
| Evidence | Observable support or counterevidence | attached to claims, decisions, outcomes |
| ApprovalGate | Required human/policy checkpoint | governs decision or action |

Canonical relations should carry `relation_type`, `source`, `confidence`, `observed_at`, and optional `valid_until`. Avoid deriving authority solely from a label or model inference.
