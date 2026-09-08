---
name: publishing-visual-explainer
description: Design evidence-backed charts, diagrams, infographics, and explanatory illustrations for books and publishing assets. Use when a visual must clarify a claim, process, comparison, or concept and survive editorial, print, and digital review.
license: MIT
metadata:
  abvx_status: experimental
  abvx_origin: adapted
  upstream: https://github.com/humanlayer/skills/tree/main/plugins/show-me/skills/show-me
---

# Publishing Visual Explainer

Create the smallest visual that answers a real reader question. A visual is optional; do not add one merely to decorate a page or fill a layout slot.

## Start With A Visual Brief

Record:

- the reader question and claim the visual must clarify;
- the target asset and placement: book interior, cover support, article, social post, or sales page;
- the source data or approved manuscript passage;
- required dimensions, color mode, and print or screen constraints;
- rights, attribution, and provenance requirements.

If the claim, source, or intended placement is unclear, stop at a concept sketch.

## Choose The Smallest Useful Form

- Use a deterministic chart for quantitative comparisons or trends. Preserve the source, transformation, units, and relevant caveats. Never invent values to improve composition.
- Use a shallow tree, flow, timeline, map, or Mermaid prototype for structure and sequence. Export final reader-facing work to an editable SVG or an approved print-ready format.
- Use a focused HTML proof when interaction or state comparison improves editorial review. HTML is a review surface, not automatically a publication asset.
- Use generated imagery only for an approved editorial concept whose explanatory value justifies it. Record the generation method and complete the rights and human taste gates.
- Use a short code-shape sketch or PR Lens only for development documentation; do not place software-review visuals in a book merely because they already exist.

Optional local companions such as `show-me`, built-in visualization, and `html-diagram-artifact` may accelerate the appropriate route. The Book Factory must remain usable without them.

## Production Sequence

1. Produce one representative visual before generating a set.
2. Check factual meaning and editorial usefulness separately from visual quality.
3. Obtain human approval for a new visual language or illustration direction.
4. Generate the editable source and the target-format asset from the approved direction.
5. Verify legibility at final size, grayscale behavior when applicable, safe areas, captions, alt text, and page balance.
6. Record the asset, source, placement, provenance, and approval state in the production manifest.

## Output Contract

Return:

- the visual brief;
- one primary asset and its editable source when applicable;
- caption and alt text;
- source and transformation provenance;
- target placement and format;
- technical QA result and separate human visual-approval state.

## Boundaries

- Do not turn an attractive graphic into evidence for an unsupported claim.
- Do not use generic flowcharts when a concrete chart, example, or no visual is clearer.
- Do not mix draft labels, internal paths, prompts, or production notes into reader-facing output.
- Do not treat successful rendering as editorial or publication approval.
- Do not generate a full illustration set before the representative visual is approved.

