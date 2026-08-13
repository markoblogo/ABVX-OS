# BOOK-FACTORY-INDICES-001 — SourcePack normalization

## Scope

Normalize the owner-supplied unusual-indices research document into reusable structured research objects for future BookSpec and market-positioning work.

## Source admitted

- `perplexity-indices-research-docx`
- local file: `/Users/antonbiletskiy-volokh/Downloads/1d3x book1.docx`
- processing mode: `CODEX_ASSISTED_DETERMINISTIC`

## Processing summary

- non-empty paragraphs processed: `3786`
- unique external URLs observed: `388`
- raw candidate mentions normalized: `67`
- duplicates merged into canonical candidates: `43`

## Normalized outputs

- `books/research/unusual-indices/source-document.json`
- `books/research/unusual-indices/normalized-corpus.json`
- `books/research/unusual-indices/commercial-opportunity-report.json`

## Object counts

- `IndexCandidates`: `24`
- `StoryCandidates`: `13`
- `Claims`: `12`
- `SourceCandidates`: `18`

## Strongest commercial candidates

Highest-value candidates for the next BookSpec gate:

- Big Mac Index
- iPhone Work-Time Index
- Working Hours Index
- Cigarette Equivalent Index
- Starbucks Latte Index
- Haircut Index
- Taxi Affordability Index
- Date Night Index
- Baltic Dry Index
- Container Freight Index
- Rent-to-Burger Index
- Minimum Wage Meal Index
- Lipstick Index
- Men’s Underwear Index
- Skyscraper Index

These were selected because they combine reader recognition, surprise, chapter potential and visually explainable comparisons.

## Weak or likely excluded material

- duplicated TOC variants
- generic primer material that can be compressed sharply later
- owner-project promotional framing
- broad AI-governance side paths that outrun the core reader promise

## Owner-project neutrality

Owner-project material was preserved but explicitly tagged as optional context:

- `1D3X`
- `POP`
- `SPIKE`
- `Ciggie Index`

It did not receive ranking advantage in the corpus.

## Verification boundary

This mission did not perform a full source-verification pass.

The corpus now distinguishes:

- `VERIFIED_IN_SOURCE_PACK`
- `NEEDS_PRIMARY_VERIFICATION`
- `SECONDARY_ONLY`
- `UNCLEAR`

Future manuscript work must still verify consequential claims against primary or high-quality sources before publication.

## Commercial conclusion

The corpus is sufficient for the next gate:

- `BOOK-FACTORY-INDICES-002`
- Commercial positioning
- Amazon market validation
- BookSpec approval

It is not yet manuscript-ready.

## RAG assessment

`NOT_NEEDED_YET`

The corpus is still manageable through explicit structured objects and metadata filtering.
