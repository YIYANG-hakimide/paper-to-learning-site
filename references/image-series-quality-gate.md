# Image Series Quality Gate

## Product Bar

The result is an ordered visual album, not presentation screenshots, isolated illustrations, or social cards with repeated templates. Each image should stand on its own while making the next image feel necessary.

It must be both informative and aesthetically authored. Reviewers should be able to identify the paper-specific art direction, not merely approve legibility.

## Sequence

- Lock the storyboard before final generation.
- Number every final image and preserve exact order.
- Keep a visible arc: problem, prerequisite, method, evidence, conclusion, limitation, recap.
- Use transitions or recurring visual motifs so the sequence feels authored as one work.
- Create a full contact sheet and verify the story remains legible at overview scale.
- Record an art-direction thesis, paper-specific visual objects, typography/material rules, and forbidden generic styles.

## Information Density

- Image pages may be denser than presentation pages.
- Use one dominant question plus 2-4 supporting information groups.
- Prefer large diagrams, structured labels, comparisons, timelines, and evidence callouts over long paragraphs.
- Split any page whose labels or evidence become too small.

## Visual Variety

Vary the explanatory form according to content while keeping one visual system:

- scene or metaphor
- mechanism/process
- architecture or layered system
- before/after or baseline comparison
- timeline/map
- annotated source evidence
- deterministic data graphic
- formula/worked example
- limitation and recap map

Reject a series that repeats the same title-top/cards-below template throughout.

Reject a series that is technically correct but visually flat, generic, excessively text-heavy, or made from diagrams that could belong to any paper.

## Accuracy

- Generated images may explain but may not invent data or serve as proof.
- Exact figures, values, quotations, formulas, dates, and table cells must come from source-linked assets or deterministic overlays.
- OCR all generated text-bearing images and compare key labels.
- Distinguish source evidence from generated explanation visually.
- Inspect every final image with visual understanding, then inspect the contact sheet for beauty, rhythm, variety, and narrative continuity.

## Packaging

- Store only final owned images in `assets/images/`.
- Store previews and rejected attempts outside the final image sequence.
- Deliver `001-...png` ordering, contact sheet, `data/storyboard.json`, `data/learning-series-manifest.json`, and `qa/qa-report.json`.
- No final bitmap may be orphaned or referenced by more than one storyboard item without an explicit reuse reason.
