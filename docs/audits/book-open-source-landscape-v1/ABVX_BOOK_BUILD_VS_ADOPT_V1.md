# ABVX Book Build vs Adopt V1

| Capability | Decision | Rationale / boundary |
|---|---|---|
| EPUB/PDF generation | **Keep existing Pandoc + XeLaTeX** | Proven local path and project-specific layouts/contracts already exist; replacing it creates regression risk without demonstrated gap |
| EPUB standards checking | **Adopt EPUBCheck** (isolated validator, pending host prerequisite) | Official W3C/DAISY conformance tool, permissive license, maintained and tested; not a generator or retailer simulator |
| EPUB accessibility checking | **Pilot DAISY Ace** | Established focused tool; keep report advisory plus human review |
| Print PDF checks | **Keep and document current qpdf/Ghostscript/Poppler stack** | Available, integrated local tools; improve contract coverage before adding another engine |
| Radar evidence store | **Build a thin versioned envelope on the existing Radar records** | Existing decision process is valuable; provenance/uncertainty is the gap. Avoid a parallel database/service |
| Amazon marketplace collection | **Do not build a scraper** | Fragile, policy-sensitive, personalized; paid proxies and rate evasion are unacceptable. Use bounded manual observations and owned exports |
| Amazon history dataset | **Defer paid Keepa option** | Stronger history is plausible but requires recurring paid API access; no purchase authorized |
| Bibliographic source connectors | **Adopt thin adapters only after known-record benchmark** | Reuse provider APIs/catalogues; each is discovery evidence, not rights clearance |
| New book factory / generalized orchestration | **Do not build** | Existing capabilities cover core pipeline; a broad replacement is expensive and duplicative |
| KDP upload/preview automation | **Do not build now** | Human/authenticated platform gate; preserve owner control and distinct publication states |
| EPUBBook conversion via Gutenberg Ebookmaker | **Do not adopt as default** | Mature but tailored to Gutenberg conventions and GPL-licensed; inspect compatibility and license before reuse |

Rule: build only the narrow adapter or contract that is missing; adopt maintained standards tools for validation; retain human decisions for rights, editorial acceptance, platform approval, and publication.
