# Implementation And Delivery

## Build Only The Selected Mode

Do not automatically generate all formats.

### Image Series

```text
learn-paper-images/
  assets/images/           # numbered final images only
  assets/evidence/         # source crops used in compositions
  data/source-inventory.json
  data/storyboard.json
  data/learning-series-manifest.json
  qa/contact-sheet.jpg
  qa/qa-report.json
```

Final names should preserve order, such as `001-problem.png`, `002-prerequisite.png`. Put previews and rejected attempts outside `assets/images/`.

### Presentation PDF

```text
learn-paper-presentation/
  index.html               # internal fixed-stage source
  assets/visuals/
  assets/evidence/
  assets/exports/
    pages/                 # optional numbered PNGs
    learn-paper.pdf        # primary deliverable
  data/source-inventory.json
  data/storyboard.json
  data/learning-deck-manifest.json
  qa/screenshots/
  qa/contact-sheet.jpg
  qa/qa-report.json
```

The PDF is the user-facing primary output. The HTML stage is an implementation artifact unless the user also requests it.

### Interactive HTML

```text
learn-paper-site/
  index.html
  assets/reader-runtime.js
  assets/figures/
  assets/diagrams/
  data/source-inventory.json
  data/learning-site-manifest.json
  qa/screenshots/
  qa/qa-report.json
```

Use static HTML/CSS/JS unless a framework is required. Copy or inline `assets/reader-runtime.js` and follow `reader-runtime-contract.md`.

## Shared Structured Data

Before final generation, create and lock `data/storyboard.json`. Record output mode, size mode, acts/chapters, exact item order, learner questions, answers, source ids, visual/evidence owners, misconceptions, layout families, and next bridges.

Manifest counts must match real artifacts. Store source inventory path/hash, storyboard path/hash, image provider/model, design brief, claim/evidence map, generated asset hashes/dimensions, and concrete QA results.

Use `manifest_schema_version: "0.3"` for all three mode-specific manifests.

## Image-Series Composition

- Use the selected aspect ratio, normally 3:4 portrait.
- Compose exact Chinese copy, citations, values, equations, and labels deterministically when model-generated text is unreliable.
- Preserve a shared design system across the sequence while varying visual form.
- Create a contact sheet after each batch and one final contact sheet.
- Run `audit_visual_series.py --strict` before delivery.

## Presentation Stage

- Author every page at 1920x1080.
- Scale uniformly; do not responsive-reflow page contents.
- Use the internal HTML stage to ensure exact typography, citations, formulas, charts, and image placement.
- Use large focal visuals and presentation pacing rather than image-series density.
- Export pages with Playwright or another reliable browser renderer.
- Run `audit_learning_deck.py --strict`, export PDF, then rerun with `--strict --require-pdf`.
- Inspect title, image-led, evidence-led, densest, and closing pages in the final PDF.

## Interactive HTML

- Keep source text selectable and searchable.
- For non-Chinese papers, implement real `中英 / 中文 / EN only` modes unless rejected.
- Attach term explanations to inline words, not detached glossary chips.
- Keep figures/tables beside their claims and provide how-to-read guidance.
- Ensure drawers, notes, bubbles, and panels open and close without covering the reading context.
- Test chapter, language, term, figure, evidence-return, and recap states on desktop and mobile.
- Run `audit_learning_site.py --strict` before local delivery or deployment.

## Source Evidence

- Crop figures/tables tightly; split composite panels when necessary.
- Preserve exact formulas, numerical values, axes, units, legends, quotations, and page references.
- Keep generated explanation visibly distinct from source evidence.
- Every important claim must return to the correct source object.

## Vercel

Deploy only interactive HTML unless the user explicitly wants a presentation or image gallery hosted. Verify the live URL, local assets, key interactions, and deployment name after strict local QA.

## Reusing Work Later

If the user later requests another output mode, reuse the source-hash cache, evidence crops, approved generated visuals, and teaching story where appropriate. Redesign the composition and density for the new mode rather than mechanically converting pages.
