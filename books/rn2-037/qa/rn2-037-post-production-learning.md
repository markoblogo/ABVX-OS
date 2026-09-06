# RN2-037 post-production learning

## Actual state

Production completed on September 6, 2026. The final package contains a 208-page 8 x 10 black-and-white paperback and EPUB 3 Kindle edition. Kindle is publishing; paperback is under KDP review. The recorded commercial package used $6.99 Kindle and $17.99 paperback prices; storefront confirmation remains pending. Anton made zero subject-matter decisions. Actual Anton time was not measured and is deliberately not substituted with the original estimate.

## POST_PREFLIGHT_FALSE_NEGATIVES

The internal PASS missed four reader-visible/release-blocking classes later caught by human review or KDP: KDP live-area failures, overlapping information-page text, corrupted/duplicated SVG labels, and omitted print/Kindle contents. These were corrected before or during final submission. They are production-system false negatives, not miscellaneous editorial fixes.

## Reusable correction

The generic preflight now calculates KDP live area from page count, binding side and bleed; treats dense pages as high risk; fails obvious text collisions and missing/duplicated SVG labels; fails missing print or Kindle contents; and requires a high-risk contact sheet. Raster legibility still routes to visual review. KDP Previewer remains the final external gate.

Original Radar estimates and the initial production-result evidence remain unchanged. This record adds actual evidence separately.
