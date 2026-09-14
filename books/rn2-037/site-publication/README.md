# RN2-037 site publication handoff

The first Book Factory → KDP observation → ABVXsite card MVP package.

## Current state

- KDP Kindle and paperback formats: observed `LIVE` on 2026-09-14.
- Canonical copy: final RN2-037 commercial package.
- Primary site media: owner-supplied promotional print, not the cover.
- Consumer files: validated and pushed to ABVXsite branch `codex/ecosystem-registry-v1` at commit `97732fe`; merge and public deployment remain separate evidence gates.

## Consumer apply boundary

1. Keep the card in the existing `Standalone books / Business, AI & Marketing` group; no catalogue taxonomy change is required.
2. Copy `abvxsite-book-card.md` into `content/books/ham-radio-technician-visual-cram-map-2026-2030.md`.
3. Copy the WebP/AVIF/PNG assets into `public/media/books/ham-radio-technician-visual-cram-map-2026-2030/`, using `promo.webp` as the card source.
4. Run `npm run content:validate`, `npm run build`, and the relevant visual QA.
5. Stop at the normal commit/push/deploy approval boundary. The owner authorized commit and push on 2026-09-14; deployment still requires separate proof.
