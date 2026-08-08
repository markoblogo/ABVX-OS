# AzurMenton Strategy Gap Report

Audit: PROJECT-ONBOARDING-002. Observed 2026-08-08 at commit `98d1c45`. The AzurMenton worktree was clean before and after inspection; no application files, deployment, production data, or infrastructure were changed.

## 1. Executive summary

AzurMenton is a working Next.js/TypeScript multilingual product with a strong typed content graph, practical guide, stay planning, apartment funnel, review-first event workflow, and solid crawl/analytics primitives. It is not yet the “most complete, practical and up-to-date” live Menton resource: event freshness/coverage is the largest product gap, guide freshness is only partly machine-visible, and booking observability stops at a manual inquiry rather than a confirmed booking.

Strategy is clear enough for one bounded development slice, but not for broad platform extraction or publishing investment. Preserve the current product and use its existing content and event contracts as the foundation.

## 2. Actual current architecture (Goal A)

- Next.js 16 App Router, React 19, strict TypeScript, Tailwind 4; Vercel deployment with Cloudflare DNS.
- Repository-local typed source of truth under `src/content`; no CMS, database, admin panel, or persistent runtime content store.
- Localized routes for EN/FR/IT/UK with canonical URLs, hreflang, sitemap, OpenGraph/Twitter metadata, JSON-LD, and `llms.txt`.
- Guide, place/map, stay-plan, transport/tool, event, and apartment domains are linked through typed slugs/IDs and related-content rendering.
- Three apartments; availability is read-only external iCal preview; inquiry is validated server-side, Turnstile-protected, rate-limited, sent through Resend, and manually confirmed.
- Events use a source registry, three automated HTML adapters, manual sources/inbox, normalization/dedupe, relevance states, date status, editorial batches, image rights states, and explicit publish.
- Analytics uses Plausible funnel events and Vercel Web Vitals; the dashboard is local/read-only and contains no PII.
- Tests, lint, typecheck, preflight, image checks, and build are required by CI. Documentation is distributed across README/docs; no top-level `ARCHITECTURE.md` was found.

## 3. Current product map (Goal B)

| Surface | Classification | Evidence |
|---|---|---|
| Discover Menton | FUNCTIONAL | localized home, guide collection, guide intents, SEO routes |
| Plan a stay | STRONG | stay plans, apartments, transport, weather, map, related guides |
| What to do now | PARTIAL | events and date filters exist, but current source coverage is narrow/static |
| Practical help | STRONG | practical guides, map taxonomy, airport/transport/weather tools |
| Nearby options | FUNCTIONAL | Monaco/Nice/Ventimiglia/Sanremo records and stricter relevance policy |
| Apartments | STRONG | three detailed apartments, availability preview, protected manual inquiry |
| Books/publishing | ABSENT | roadmap only; no Living Guide or Book Factory implementation |
| Local media | ABSENT | no Media Resource integration or distribution pipeline |
| Multilingual experience | FUNCTIONAL | four locales and localized route/SEO infrastructure; translation polish varies |

## 4. Strong foundations; do not rebuild

Keep the existing content graph, localization/SEO primitives, manual booking safety boundary, event review-first workflow, typed source registries, and aggregate privacy-safe funnel contract. Replacing these with a CMS, database, new analytics vendor, or generalized city framework now would add risk without addressing the product gap.

## 5. Highest-leverage gaps

1. Fresh, useful event discovery for Menton first; nearby events need strict relevance.
2. Uniform guide provenance/review/freshness signals for practical claims.
3. A measured path from content discovery to inquiry and, where possible, owner-confirmed outcome.
4. Product positioning and navigation should make “Menton guide first, apartments second” explicit without weakening rental conversion.
5. Editorial workload is still manual at the source-review and publication gates.

## 6. Events deep dive (Goal C)

The model supports event identity, occurrences, date status, series, city/location, interest, related guides/places, source URL, image kind/rights, and relevance reason. There are 24 published JSON records observed, 43 date-status fields in the broader model, seven registered primary sources, and three automated adapters. Menton, Monaco, and Ventimiglia sources remain manual because stable structured records were not confirmed; automated sources are only a partial calendar.

The workflow is safe but explains the static surface: ingest → prepare → inspect queues → explicit selected publish, with no CMS, no automatic publication, and narrow source coverage. It has deterministic date handling/dedupe and expiration-aware statuses, but update cadence and source verification still depend on human review. The smallest future path is a report-only freshness/relevance queue over existing published events and source cadence, then a measured date-window surface; neither is implemented here.

## 7. Guide freshness (Goal D)

Guides are typed, localized, related to places/events/apartments, and include `sourceStatus` plus some publication metadata. The audit observed 78 `sourceStatus` fields but only 10 `publishedOn` fields and no uniform `updatedOn`, `reviewedOn`, `lastVerified`, or freshness marker in the inspected guide/place source. This supports editorial review but not reliable stale-claim detection across the corpus. Practical claims about hours, prices, routes, access, transport, and seasonal conditions can mislead if not rechecked. The content is structurally suitable for a future Living Publication, provided publication later consumes only reviewed/current records and carries date/update notes.

## 8. Booking funnel (Goal E)

The intended path is content/home/stay/apartment/event/guide CTA → `/check-availability` → validated inquiry. CTA attribution carries locale, source page type, and source slug; analytics includes view, form start, success, and error. Turnstile, rate limiting, size limits, server validation, read-only iCal checks, Resend, and explicit manual confirmation are appropriate safeguards. The main friction is manual confirmation and lack of CRM/confirmed-booking linkage. The funnel is not overly aggressive: guide/event/stay content can lead to apartments, but measurement of actual downstream revenue remains partial.

## 9. SEO, discovery, and AI discovery (Goal F)

Strong technical baseline: locale alternates, canonicals, sitemap, robots API exclusion, metadata, OpenGraph/Twitter, structured data, internal related links, and `llms.txt`. Guide/event discoverability is structurally present. High-leverage gaps are not a speculative SEO rebuild: validate content freshness and intent coverage, verify real Search Console/discovery data, and align top-level positioning with the guide-first product definition. No live search or AI referral baseline was present in repository evidence.

## 10. Analytics and economic observability (Goal G)

The existing contract measures CTA source, locale, content type/slug, availability view, form start, request success/error, and aggregate form context without PII. A local read-only Plausible dashboard exists. Unknowns are the production baseline, content/event usage levels, traffic-source mix, and what portion of inquiries becomes a confirmed booking because the owner process is manual and outside the repository. Do not add another vendor before using the existing contract and obtaining a baseline.

## 11. Publishing readiness (Goal H / strategic frame)

Repository-local typed content, event records, source links, review queues, and explicit Git publication are a credible source for a future free Living Menton Guide. The missing pieces are a reviewed subset policy, uniform freshness/rights metadata, versioned generation, and owner visual review. Paid books and Book Factory remain roadmap items and must not be started in this onboarding audit.

## 12. Media Resource readiness (Goal H)

Natural future producers are important guide creation/update, major event publication, new apartment/video media, seasonal stay content, and future book releases. Potential surfaces are the site, downloadable Living Guide, direct booking funnel, social/email channels, and future book/distribution surfaces. There is currently no standardized Media Event emission or Media Resource integration.

## 13. Reusable City Engine candidates (Goal I)

- CLEARLY_REUSABLE: localization, canonical/hreflang/sitemap/structured-data primitives; generic Guide/Place/Event/Source concepts.
- POTENTIALLY_REUSABLE: event ingestion/dedupe/relevance review, freshness metadata, booking attribution, Living Publication source, media-event producers.
- MENTON_SPECIFIC: apartment inventory, owner/contact/availability facts, Menton-centered relevance thresholds, local source list, coordinates, brand and editorial facts.

Do not extract these yet. Keep generic concepts generic when future work naturally touches them.

## 14. Risks and technical debt

- Live events can be stale or incomplete despite a safe publication workflow.
- Practical guide freshness is not uniformly machine-detectable.
- Manual booking operations prevent end-to-end economic attribution.
- Some locale copy is deterministic fallback rather than fully human-polished translation.
- Event source adapters cover only selected calendars; manual review burden remains.
- Architecture context is distributed; the missing top-level `ARCHITECTURE.md` increases onboarding cost.
- Production deployment, Search Console data, Plausible baseline, and confirmed booking data were not verified in this read-only audit.

## 15. Recommended roadmap

### NOW

1. **Event freshness/relevance report** — Outcome: better “today/tomorrow/weekend” usefulness; value high; effort M; risk source instability; dependencies owner-approved primary sources; evidence: seven sources, only three automated, explicit review workflow.
2. **Guide freshness audit** — Outcome: safer practical claims and Living Guide readiness; value high; effort M; risk metadata work without editorial capacity; dependencies source/review policy; evidence: 78 source-status fields, only 10 publication dates, no uniform freshness marker.
3. **Baseline existing booking funnel** — Outcome: understand qualified traffic → inquiry; value high; effort S; risk Plausible data may be sparse; dependencies local read-only Stats API access and owner review; evidence: existing privacy-safe funnel/dashboard.
4. **Guide-first discovery/CTA review** — Outcome: more qualified traffic and apartment inquiries without aggressive selling; value medium/high; effort S; risk messaging changes can affect conversion; dependencies strategy wording and existing analytics baseline; evidence: guide/stay/event CTAs already carry source attribution.
5. **Editorial maintenance cadence** — Outcome: lower manual staleness risk; value medium; effort S/M; risk cadence becomes checklist overhead; dependencies event/guide freshness reports; evidence: explicit Git/review-first workflows and manual sources.

### NEXT

Implement the selected event date-window experience after the report proves source coverage; formalize reviewed guide subset and freshness fields; improve owner inquiry outcome capture without adding a CRM prematurely.

### LATER

Living Guide generation, paid books/distribution, standardized Media Resource events, and carefully extracted reusable city capabilities. City Engine/AzurNantes is P3 and should remain deferred.

## 16. Exactly one first bounded implementation slice

**Event freshness and coverage report (report-only, no public route or auto-publish).** Read the existing published events and source registry, classify records into Today/Tomorrow/This weekend/Next 7 days/date-range coverage, and flag stale/unknown source cadence, missing date status, and manual-source gaps. Emit a reviewable artifact and aggregate measurement plan; preserve all current production behavior. This is small enough to bound, produces immediate editorial value, and directly tests the largest strategic gap.

## 17. Strategy clarity

Sufficiently clear for one bounded development mission and for preserving the current booking path. Not sufficient for broad City Engine extraction, Living Publication generation, or monetization implementation without human decisions on freshness standards, event breadth, and guide-first positioning.

## 18. Human strategic questions

1. Should the primary public promise explicitly lead with “Menton guide” while apartments remain the conversion path?
2. What minimum event freshness/coverage standard makes “today/tomorrow/weekend” trustworthy enough to publish?
3. Which practical guide claims require dated primary-source verification before entering a future Living Guide?
4. What owner-side signal, short of a CRM, is acceptable for measuring inquiry → confirmed booking?
5. Which first distribution surface matters for the Living Guide: site download, email, or another owner-selected channel?

## ABVX onboarding / decision gate

Changed only ABVX-OS registry, machine-readable capability/security snapshots, evidence, and this report. AzurMenton application files are untouched; no deployment, City Engine, Book Factory, Living Publication, Media Resource, or analytics integration was started. **STOP_FOR_HUMAN_DECISION.**
