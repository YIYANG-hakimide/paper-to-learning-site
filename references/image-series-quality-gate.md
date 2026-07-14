# Image Series Quality Gate

## Product Bar

The result is an ordered visual album, not presentation screenshots, isolated illustrations, or social cards with repeated templates. Each image should stand on its own while making the next image feel necessary.

It must be both informative and aesthetically authored. Reviewers should be able to identify the paper-specific art direction, not merely approve legibility.

## Sequence

- Lock the storyboard before final generation.
- Number every final image and preserve exact order.
- Establish the full-paper context/argument map and the core-contribution map before detailed images.
- Choose the remaining sequence dynamically from the paper's concepts, methods, architecture, experiments, evaluation, causal/evidence chains, findings, and user focus.
- Do not force a separate limitation or recap image when it would be low-value; the selected size mode controls how far beyond the core explanation the album goes.
- Use transitions or recurring visual motifs so the sequence feels authored as one work.
- Create a full contact sheet and verify the story remains legible at overview scale.
- Record an art-direction thesis, paper-specific visual objects, typography/material rules, and forbidden generic styles.
- Put both required fixed images within the opening sequence as two separate final images.

## Information Density

- Image pages should carry high visual information density without adopting presentation-page chrome or card layouts.
- Use one dominant learner question or relationship plus the supporting information needed to answer it.
- Every non-cover image needs a visible scan order and enough integrated labels/callouts to explain the main visual without relying on a generic footer sentence.
- Prefer large diagrams, structured labels, comparisons, timelines, causal maps, and short explanation blocks over a slide-like stack of cards.
- Split any page whose labels or evidence become too small.
- Do not optimize for a fixed word count. The image must explain the topic fully while remaining legible at its final viewing size.

## Visual Variety

Vary the explanatory form according to content while keeping one visual system:

- scene or metaphor
- mechanism/process
- architecture or layered system
- before/after or baseline comparison
- timeline/map
- generated experiment/evidence-chain explanation
- conceptual data comparison without pretending to reproduce the source chart
- formula/worked example
- limitation and recap map

Reject a series that repeats the same title-top/cards-below template throughout.

Do not repeat one main composition for more than three consecutive images. Medium and detailed albums should normally use at least four materially different composition families.

Reject a series that is technically correct but visually flat, generic, excessively text-heavy, or made from diagrams that could belong to any paper.

Use the deletion test: if removing the main image leaves almost the entire explanation intact, the image is decorative and does not count as a teaching visual. The visual must carry a causal, spatial, comparative, sequential, or quantitative relationship.

## Native Generation Contract

- Every final image uses `production_method: model-single-pass`.
- The final bitmap must byte-match the saved raw model output. Copying or renaming the file is allowed; pixel editing, cropping, padding, compositing, annotation, source insertion, and text overlays are not.
- The generation record must include the provider, model, unique request id, prompt hash, captured provider/tool response, run receipt, raw path/hash, direct-output declaration, and `pixel_postprocess_operations: []`.
- Save raw bitmaps under `raw/model-outputs/`, captured tool/provider responses under `raw/provider-responses/`, and JSON receipts under `raw/receipts/`. Receipt schema v1 records provider, model, request id, prompt hash, and output hash; all values must match the response record, manifest, and final bitmap.
- `text_integration.mode` must be `in-model`.
- A wrong title, label, paragraph, fact, or structure requires full-image regeneration or a provider switch.
- Reject title-top/illustration-middle/footer-summary compositions when they read as a portrait slide rather than one integrated infographic.
- Reject repeated slide chrome: page rails, footers, page numbers, source bars, fixed card grids, or identical title boxes across the album.

## Accuracy

- Verify the requested source file hash and page count against the final manifest before any other review.
- Generated images may explain but may not invent data or serve as proof.
- Avoid exact values, quotations, formulas, dates, and table cells unless the model can reproduce them accurately and the internal source trace verifies them. Prefer conceptual explanation in image mode.
- OCR all generated text-bearing images and compare key labels.
- Reject any final image containing replacement boxes, garbled formulas, cropped branches, or leftover template rails/sidebars.
- Inspect every final image with visual understanding, then inspect the contact sheet for beauty, rhythm, variety, and narrative continuity.
- Verify every image title and standalone explanation through actual OCR and visual inspection.

## Packaging

- Store only final owned images in `assets/images/`.
- Store previews and rejected attempts outside the final image sequence.
- Deliver `001-...png` ordering and a page-matched album PDF. Keep the contact sheet, storyboard, manifest, OCR, prompts, and QA report as internal package evidence.
- No final bitmap may be orphaned, duplicated, or reused for another storyboard item.
- The album PDF must contain exactly one final image per page in the same order and aspect ratio; verify all pages after export.
