# KDP Slot Policy V1

Effective 2026-10-07. Each UTC week starts Sunday 00:00. Per format (ebook, paperback, hardcover), creation ≤2 and first submission ≤2 are independent limits. An old draft consumes first-submission quota when first submitted. Updating a previously submitted title consumes no new-title submission; an UPDATE needs prior submission evidence for that same title-format.

Verified public primary source: [KDP Create a Book, French official help](https://kdp.amazon.com/fr_FR/help/topic/G202172740), section “Limites de création et d’envoi de nouveaux livres”, retrieved 2026-10-07. It states both two-title limits, per-format independence, first submission including older drafts, update exclusion, and Sunday midnight UTC reset. Some English cached versions still show older creation limits; the French official page supports the complete current policy. No account was accessed.

Ledger `slot_events`: distinct event ID, title/KDP-object identity, format, CREATION/FIRST_SUBMISSION/UPDATE, timezone-aware timestamp, commercial line and evidence. Duplicate creation/first-submission events for one title-format are rejected. If a deleted title is recreated as a genuinely different KDP object, its ledger identity must be distinct; do not reuse an ID to conceal creation usage. No events are invented from a live date.

`slot_reconciliations` assert evidence-backed complete capture for a format/week. Missing reconciliation → UNKNOWN usage → BLOCKED. `slot_history_complete_since` concerns complete first-submission coverage across all formats for the rolling-slot denominator; default UNKNOWN. Owner reconciliation must include older submitted titles needed for later UPDATE validation. Future/partial ledger events cannot certify current capacity. The week containing 2026-10-07 starts 2026-10-04; the next reset is 2026-10-11 00:00 UTC. This is not a claim that the account quota is currently exhausted or available.

Default paperback slot 1: EXPLOIT/SCALE; slot 2: EXPLORE. This is a preference, not a quota. The owner-selected C01 → Carmilla order is an explicit strategy override, with no auto-fill or automatic scheduling. Every paperback needs a recorded YES to: “If only one paperback slot remained this week, would we still use it for this title?” NO or UNKNOWN blocks the gate. A reset alone does not clear readiness/qualification/owner-review gates.

Classes are exclusive: EXPLOIT = adjacent paid line; EXPLORE = independent discovery; SERIES_BET = deliberate series/read-through test; SCALE = commercially validated follow-on. EXPLOIT needs paid evidence; SCALE needs commercial validation. Existing launched series classification does not consume current slots or schedule an extension.

Fields returned: KDP_SLOT_CLASS, KDP_SLOT_WEEK, KDP_SLOT_STATUS, KDP_SLOT_OPPORTUNITY_COST. Gate checks creation capacity only if a new KDP object still needs creation, and checks first-submission capacity separately. Clear gates yield ELIGIBLE_FOR_OWNER_REVIEW, never automatic authorization.

eBook capacity is separate: natural exploit/scale editions, intentional series fiction or eBook-native opportunities. Paper-native C01 gets no artificial Kindle version. Good Dogs is already live, outside the queue.

Experiment cost records separate cash, agent time, owner time, calendar time and qualitative slot opportunity cost. Numeric time/cash estimates should carry units, ranges, assumptions and evidence. UNKNOWN remains valid. Slot cost describes displaced choices and is never converted to invented euros. Existing historical costs are preserved.
