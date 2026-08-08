# Autonomy policy

Autonomy is evaluated per source and per action. There is no single global autonomy level. A source policy defines what may be done with its inputs; an action policy defines the risk, reversibility, required evidence, and approval needed for that action. The stricter result wins.

| Level | Allowed pattern |
|---|---|
| L0 observe | Read, record, and monitor; no interpretation required |
| L1 classify | Normalize, classify, link, and queue for review |
| L2 research | Gather and summarize evidence without changing external state |
| L3 propose/run | Create a task or run a non-destructive experiment |
| L4 isolated change | Execute a reversible, isolated, locally verified change |
| L5 pre-authorized | Deploy a low-risk, pre-authorized, verified change |
| L6 consequential | External communication, money, permissions, deletion, or other consequential action; approval required unless explicitly whitelisted |

Every action records actor, source policy, action policy, level, inputs, evidence, approval gate, target, result, and rollback/compensation path. Whitelists are narrow, time-bounded, auditable, and revocable. Unknown trust, missing provenance, ambiguous intent, or policy conflict routes to a concise owner question or a stop state.
