# Book Radar market context policy V1

Owner decision: 2026-10-04. Applies prospectively to discovery, wide screening,
Shelf Intelligence and new retail observation cohorts.

## Primary market follows content language

| Content language | Primary marketplace | Delivery country | Search language |
|---|---|---|---|
| English (EN) | Amazon.com / United States | United States | English |
| French (FR) | Amazon.fr / France | France | French |

Content language means the language of the intended book/readership, not the
browser, operating system or owner's account interface. Other languages and
secondary country markets require an explicit target-market decision; do not
infer them from the owner's location. Cross-market observations remain separate
and cannot substitute for the primary market.

## Before capturing retail evidence

1. Confirm the marketplace domain and visible delivery country. Amazon.com with
   “Deliver to France” is insufficient for a US domestic observation.
2. Prefer an unsigned browser/session. A French owner account or local geolocation
   must not silently select the English-language research market. Signing out
   alone does not establish the correct delivery country.
3. Confirm the search language, sort, Books/format filters and signed-in state.
   Retain the visible context with timestamp, query, evidence pointer and sponsored
   placements. Country changes require the applicable browser-setting authorization;
   an approved research ZIP is a context, not a personal address.

Use an explicit research delivery location within the target country when the
site requires a postal code. New York 10001 and Paris 75001 are usable research
contexts; retain the exact chosen location consistently for repeated captures.
Currency and UI language alone are not proof of the correct market.

## Mismatch and historical comparability

A mismatched delivery country or marketplace is **NOT_COMPARABLE_FOR_TARGET_MARKET**.
Unknown country or signed-in/personalization context stays **UNKNOWN**. Preserve
the raw observation and label the limitation; do not promote it as primary-market
demand, entry, rank, discovery or absence evidence. Correct the context and make
a separately timestamped capture within the authorized budget before relying on
it. Record repeat acquisition attempts and their cost explicitly.

The status above is an operator-policy label, not a new enum inserted into legacy
machine schemas. Use their existing comparability/limitations fields. This policy
does not add an automatic market-context validator to the current offline engine.

Do not rewrite old snapshots, their market labels, scoring or conclusions. A
historical English observation from Amazon.fr, or Amazon.com with France delivery,
describes that observed context; it does not establish the US market. Review any
future use of it accordingly. Frozen controlled T7/T14 cohorts keep their original
routes and delivery contexts to preserve within-cohort comparability. The current
controlled-protocol checklist's legacy France context is a historical exception,
not the default for a new English market scan. A US replacement cohort must be
declared separately; do not silently switch a frozen series midstream.

This decision changes prospective research context only. It does not authorize
new scans, scoring changes, deep collection, spending, production or publication.
