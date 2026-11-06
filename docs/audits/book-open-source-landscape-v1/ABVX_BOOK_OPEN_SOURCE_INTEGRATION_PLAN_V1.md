# ABVX Book Open-Source Integration Plan V1

**Decision:** approve the sequence below as recommendations only. No implementation or dependencies were added. Revisit after reviewing this audit and the existing capability registries.

| Priority | Integration | Scope | Acceptance gate | Cost |
|---|---|---|---|---|
| NOW-1 | EPUBCheck | Pin official release, invoke as isolated CLI against generated EPUB; persist version + JSON/text report | Valid and intentionally-invalid fixtures produce expected exit/results; existing proof EPUB report reviewed; no build output mutation | CHEAP after Java is available |
| NOW-2 | DAISY Ace | Optional isolated CLI check after EPUBCheck, report-only | Human review confirms report usefulness and false-positive handling; never equate automated report with accessible publication | CHEAP/NORMAL |
| NOW-3 | Radar evidence envelope | Extend existing record only after schema review: source, URL/query, locale, captured-at, observed fields, method, confidence, raw-snapshot reference | Existing records parse; old records remain valid; personal/context fields and uncertainty retained | NORMAL |
| LATER | BnF / Open Library / Google Books discovery adapters | One provider at a time, read-only, rate/policy compliant; normalize identifiers, edition, language, translation references | Known-record benchmark plus explicit false-negative review; no rights conclusions | NORMAL |
| DEFER | Keepa data adapter | No purchase now; separate approval, credential plan, bounded ASIN pilot, spend cap and cancellation date | Compare signal quality with manual snapshots; value over existing evidence proven | EXPENSIVE |

## Controls

- Preserve existing Radar rules/package and capability registry semantics. Ukrainian Modernism remains `NEEDS_RESEARCH`; its full research stays deferred pending infrastructure audit and is not a task in this plan.
- No Amazon scraping, proxies, authenticated browsing, automatic listing changes, publishing, purchases, API subscriptions, or third-party data spend.
- Validators consume copies or immutable proof outputs. Raw documents and production masters remain untouched.
- Keep Kindle Previewer/KDP acceptance human controlled. Standards conformance, accessibility automation, visual rendering, platform preview, and public availability are distinct gates.
- Before schema change, inspect all consumers and provide versioned backward compatibility. Update capability and donor registries only after a working, tested implementation; this audit alone is not implementation evidence.

## Sequencing

1. Resolve Java runtime availability through the normal approved environment path; then validate the existing design-proof EPUB with pinned EPUBCheck.
2. If useful, run DAISY Ace on that same proof and capture a reviewed report.
3. Present the Radar evidence-envelope schema proposal; wait for the normal architecture/schema gate before editing consumer records.
4. Pilot one bibliographic source against a small fixed, owner-selected known-record set.
5. Reassess Keepa only if free/manual sources leave a material gap and a separate spend approval is obtained.

No code/config tests were run because no code/config changed. The local validation attempt and blocker are recorded in the audit.
