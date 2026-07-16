# Implementation And Delivery

## Build Only The Selected Mode

Do not automatically generate all formats.

### Image Series

```text
learn-paper-images/
  assets/images/           # numbered final images only
  assets/exports/
    learn-paper-album.pdf  # one final image per page, same order
  data/source-inventory.json
  data/storyboard.json
  data/learning-series-manifest.json
  qa/ocr/                 # actual OCR output, one text artifact per final image
  qa/contact-sheet.jpg
  qa/qa-report.json
```

Final names should preserve order, such as `001-problem.png`, `002-prerequisite.png`. Put previews and rejected attempts outside `assets/images/`.

### Presentation PDF

```text
learn-paper-presentation/
  deck.mjs                 # editable artifact-tool source
  assets/visuals/
  assets/evidence/
  assets/exports/
    pages/                 # optional numbered PNGs
    learn-paper.pptx       # editable primary deliverable
    learn-paper.pdf        # matched reading/export copy
  data/source-inventory.json
  data/storyboard.json
  data/learning-deck-manifest.json
  qa/ocr/                 # OCR output for generated text-bearing visuals
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

Always pass the original source path to the final audit. The audit must compare the requested file hash and PDF page count with `source_fidelity.source_pdf_sha256` and `source_fidelity.page_count`. A package built from another paper is a P0 failure even when its internal manifest is self-consistent.

Use `manifest_schema_version: "0.5"` for image-series and presentation manifests. Use `0.4` for HTML after adding the shared learning path and argument map.

## Image-Series Native Generation

- Choose the aspect ratio from the teaching structure; portrait is common but not mandatory.
- Generate each complete final page in one image-model call with its title, Chinese explanation, labels, relationships, and visual hierarchy already integrated.
- Do not compose exact copy, citations, source figures, labels, or slide chrome after generation. Regenerate the full image when model text is unreliable.
- Save the raw model output and copy it unchanged into `assets/images/`; hashes must match.
- Preserve a shared design system across the sequence while varying visual form.
- Create a contact sheet after each batch and one final contact sheet.
- Export the album PDF and run `audit_visual_series.py <output-dir> --source <paper.pdf> --strict --require-pdf` before delivery.
- Use `scripts/build_image_album_pdf.py assets/images assets/exports/learn-paper-album.pdf` for the standard one-image-per-page export.

## Presentation Production

- In Codex, read the current official `Presentations` skill and use its `@oai/artifact-tool` workflow. Outside Codex, require an equivalent editable presentation engine.
- Author every page at 16:9 and keep titles, body copy, charts, tables, shapes, and layout objects editable. Generated explanatory images may remain high-resolution bitmaps.
- Do not use a PDF-to-slide conversion, screenshots of HTML pages, or one flattened image per slide as the PPTX implementation.
- Use a self-reading consulting-report rhythm: page-specific layouts, conclusion-led titles, visible evidence, and enough explanation to work without narration.
- Route visuals deliberately: native charts for data, native shapes for simple flows, deterministic typesetting for exact tables/formulas, Graphviz for complex topology, Excalidraw for sketch explanations, ImageGen for abstract or high-aesthetic teaching visuals, and source crops for evidence.
- Render every page from PPTX, export PDF, and compare page order, crops, fonts, visual placement, and editability. Contact-sheet review alone is insufficient.
- Run `audit_learning_deck.py <work-dir> --source <paper.pdf> --strict`, export PDF, then rerun with `--source <paper.pdf> --strict --require-pdf`.
- Inspect title, image-led, evidence-led, densest, and closing pages in the final PDF.
- If two full repair rounds still fail strict PPT QA, stop and ask whether to continue repairing the PPT or start a separate native learning-album run. Do not switch modes automatically.

## Interactive HTML

- Keep source text selectable and searchable.
- For non-Chinese papers, implement real `中英 / 中文 / EN only` modes unless rejected.
- Attach term explanations to inline words, not detached glossary chips.
- Keep figures/tables beside their claims and provide how-to-read guidance.
- Ensure drawers, notes, bubbles, and panels open and close without covering the reading context.
- Test chapter, language, term, figure, evidence-return, and recap states on desktop and mobile.
- Include an opening paper overview and argument route whose nodes link to the corresponding source blocks and evidence.
- Run `audit_learning_site.py --strict` before local delivery or deployment.

## Source Evidence For PPT And HTML

- Crop figures/tables tightly; split composite panels when necessary.
- Preserve exact formulas, numerical values, axes, units, legends, quotations, and page references.
- Keep generated explanation visibly distinct from source evidence.
- Every important claim must return to the correct source object.

## Vercel

Deploy only interactive HTML unless the user explicitly wants a presentation or image gallery hosted. Verify the live URL, local assets, key interactions, and deployment name after strict local QA.

## Reusing Work Later

If the user later requests another output mode, reuse the source-hash cache, evidence crops, approved generated visuals, and teaching story where appropriate. Redesign the composition and density for the new mode rather than mechanically converting pages.
