# ABVX Book Radar Evidence Contracts V1

This is the shared contract for `RADAR_EVIDENCE_SCHEMA_V1`, `RADAR_SOURCE_PROVENANCE_V1`, `BIBLIOGRAPHIC_RESEARCH_CONTRACT_V1`, `RIGHTS_EVIDENCE_CONTRACT_V1`, `TRANSLATION_EXISTENCE_CONTRACT_V1`, and `AMAZON_OBSERVATION_CONTRACT_V1`. It adds an evidence/provenance layer; it does not replace Radar interpretation, cohort logic, scoring, or commercial/editorial separation.

## Canonical flow

`COLLECTOR / SOURCE → RAW EVIDENCE → NORMALIZER → ABVX EVIDENCE RECORD → RADAR INTERPRETATION`

Third-party tools can collect or transform observations; only ABVX records canonical evidence classes, source status, provenance, and uncertainty. Existing discoverability/click/conversion distinctions, `NO_MEANINGFUL_QUERY`, `DISCOVERED_TOO_DEEP`, evidenced `NOT_INDEXED`, D0/D7/D14/D30, cohorts, commercial/editorial split, append-only learning, and scoring remain unchanged.

## RADAR_EVIDENCE_SCHEMA_V1

Machine contract: `schemas/radar_evidence.schema.json`. Required fields include stable `evidence_id`; observation timestamp; source type/name; collection method; marketplace/catalogue; query; typed entity and identifiers; raw-evidence pointer; normalized value; evidence class; confidence; personalization and location context; tool/collector versions; collection status/error class; notes. `schemas/bibliographic_research.schema.json` supplies the common catalogue-query/result shape.

Evidence classes are mutually explicit: `DIRECT_STRUCTURED_DATA`, `DIRECT_PAGE_OBSERVATION`, `THIRD_PARTY_HISTORICAL_DATA`, `BIBLIOGRAPHIC_RECORD`, `INSTITUTIONAL_SOURCE`, `SEARCH_PROXY`, `MANUAL_INPUT`, `INFERENCE`. Never silently upgrade a proxy or inference into a direct record.

## RADAR_SOURCE_PROVENANCE_V1

Retain raw response/page capture separately when permitted; store normalized records with an immutable raw pointer. Raw evidence must exclude credentials, cookies, API secrets, and personal account tokens. A failure record retains the query/source and failure information; it must not be normalized as an empty result. Version collectors and normalizers; keep derived claims separately linked to their source evidence IDs.

Collection statuses: `SUCCESS`, `NO_RESULT`, `COLLECTION_FAILED`, `BLOCKED`, `CAPTCHA`, `UNSUPPORTED_MARKETPLACE`, `AUTH_REQUIRED`, `RATE_LIMITED`, `UNKNOWN_FAILURE`. Only a completed observation can support a positive or negative source claim. Failed collection is not absence.

## BIBLIOGRAPHIC_RESEARCH_CONTRACT_V1

Each search observation records catalogue/provider, exact query, name/title variants, jurisdiction/language filters, record IDs/URIs, hit type, edition/language, retrieval date, result status, raw pointer, and limitations. Adapters may target BnF, SUDOC, Open Library, Internet Archive, Wikisource/MediaWiki, Project Gutenberg, Google Books, or another qualified institutional catalogue. The common contract is implemented; remote adapters are not. Provider records support discovery, not rights conclusions.

## RIGHTS_EVIDENCE_CONTRACT_V1

Machine contract: `schemas/rights_evidence.schema.json`. Store author identity, death date and its evidence references, original publication date, edition date, jurisdiction, applicable term/rule reference, source-edition status, uncertainty/exception notes, evidence IDs, review date, and decision `PASS|FAIL|REVIEW`. Preserve `REVIEW` whenever a material fact or legal interpretation is unresolved. The record is an evidence organizer, not legal advice or an automated clearance engine.

## TRANSLATION_EXISTENCE_CONTRACT_V1

Machine contract: `schemas/translation_existence.schema.json`. Store outcome `NO_COMPLETE_TRANSLATION_FOUND|COMPLETE_TRANSLATION_EXISTS|UNCERTAIN`, catalogues actually searched, author/title variants, target language, record hits and record types, full/excerpt/thesis/fragment distinction, search date, raw pointers, and caveats. `NONE_FOUND` means only that the documented searches returned no complete translation; it never means “never translated.” If a search fails, is blocked, or only a non-exhaustive source was checked, outcome stays `UNCERTAIN`.

## AMAZON_OBSERVATION_CONTRACT_V1

Apply [market context policy V1](book-radar-market-context-v1.md) to new captures:
EN content → Amazon.com with US delivery; FR content → Amazon.fr with France
delivery. An unsigned session alone does not verify the delivery country.
Record mismatches in limitations/comparability; preserve historical raw records
and frozen cohort contexts rather than relabeling them as target-market evidence.

Machine contract: `schemas/amazon_observation.schema.json`. Record marketplace, query, ASIN, observed organic position/depth, sponsored position, module type, personalized state (`TRUE|FALSE|UNKNOWN`), signed-in state, delivery location, price, BSR, ratings/review count, availability, format linkage, method, timestamp, raw pointer, and collector/tool versions. `SPONSORED`, `PREVIOUSLY_VIEWED_MODULE`, and `RECOMMENDATION_MODULE` are not organic results. Unknown personalization is excluded from organic-discovery counts. Do not infer sales from BSR.

## Integration boundary

No Keepa subscription; its future source class is supported but not active. KDP Scout is not integrated; the audit supported borrowing record/snapshot patterns only and left any static local pilot for later. EPUBCheck and Ace state: `NOT_PILOTED_ENVIRONMENT_BLOCKED`; Factory follow-up remains separate. No scoring or cohort changes are authorized by this contract.
