# Implementation And Deploy

## Default output

Create a static site unless the user or existing project requires a framework:

```text
learn-paper-title/
  index.html
  assets/
    figures/
    diagrams/
    screenshots/
  data/
    learning-site-manifest.json
```

Use semantic HTML, scoped CSS, and small vanilla JS for chapter switching, drawers, popovers, figure hotspots, reading progress, and synchronized notes.

## Required content structures

Represent chapters as structured data when possible:

- id
- title
- short purpose
- source paragraphs
- translations/explanations
- terms
- figures/tables
- generated diagrams
- checkpoints
- source paragraph coverage status
- generated visual provenance
- paragraph anchors and inline term anchors
- public UI copy review status
- omitted source blocks with reasons
- per-chapter source coverage
- per-block explanation quality

This prevents repeated content and makes chapter navigation deterministic.

## Manifest

Create `data/learning-site-manifest.json` for every site:

```json
{
  "source_title": "Paper Title",
  "source_language": "en",
  "source_paragraphs_expected": 120,
  "source_paragraphs_rendered": 120,
  "paper_figures_expected": 9,
  "paper_figures_rendered": 9,
  "generated_visuals_expected": 12,
  "generated_visuals_rendered": 12,
  "image_generation_model": "Image 2",
  "public_ui_clean": true,
  "inline_terms_expected": 40,
  "inline_terms_rendered": 40,
  "term_strip_only_count": 0,
  "paragraph_anchors_expected": 120,
  "paragraph_anchors_rendered": 120,
  "generated_visual_language": "zh-dominant",
  "source_blocks": [
    {
      "source_id": "sec3-p04",
      "section_id": "3",
      "page_start": 5,
      "page_end": 5,
      "order": 34,
      "source_text_hash": "sha256:...",
      "source_word_count": 92,
      "rendered_block_id": "block-sec3-p04",
      "chapter_id": "chapter-3"
    }
  ],
  "chapter_coverage": [
    {
      "chapter_id": "chapter-3",
      "expected_source_ids": ["sec3-p04"],
      "rendered_source_ids": ["sec3-p04"],
      "missing_source_ids": [],
      "omitted_source_ids": [],
      "source_word_count": 92,
      "translation_char_count": 214,
      "explanation_char_count": 180
    }
  ],
  "term_anchors": [
    {
      "term_id": "self-attention",
      "trigger_text": "Self-attention",
      "source_id": "sec3-p04",
      "rendered_block_id": "block-sec3-p04",
      "anchor_location": "source_text",
      "char_offset": 12,
      "is_inline": true
    }
  ],
  "omitted_source_blocks": [],
  "tools_used": {
    "pdf_text": "pdfplumber",
    "figure_rendering": "pdftoppm",
    "browser_qa": "system Chrome headless"
  }
}
```

Counts must describe what is rendered in the main reading experience, not what is hidden in a raw appendix.

Use manifest fields to make reader-quality promises auditable:

- `public_ui_clean`: true only after scanning visible text for internal workflow/audience/build notes.
- `inline_terms_rendered`: count terms embedded inside source, translation, or explanation text, not detached glossary chips.
- `term_strip_only_count`: number of term chips that have no inline anchor; should be 0 unless explicitly justified.
- `paragraph_anchors_rendered`: number of source paragraphs with stable ids or `data-source-id`.
- `generated_visual_language`: use values such as `zh-dominant`, `en-dominant`, or `mixed`; Chinese-bilingual sites should usually be `zh-dominant`.
- `source_blocks`: per-paragraph evidence that the page can trace rendered text back to the extracted paper.
- `chapter_coverage`: per-chapter expected/rendered source ids. Do not rely only on total counts.
- `term_anchors`: inline trigger inventory. `is_inline` should be true for the main learning entry point.
- `omitted_source_blocks`: every skipped paragraph/table/appendix block, with a reader-facing reason.

## Static reader standards

- No PDF iframe as primary reading mode.
- A source PDF link can exist as secondary reference.
- Text should be selectable and searchable.
- Main paper text should be paragraph-level bilingual/Chinese reading blocks, not raw `<pre>` dumps.
- Non-Chinese sources should include visible language controls such as `中英 / 中文 / EN only`.
- Figure/table screenshots should be local assets with alt text.
- Generated diagrams should be local bitmap assets from Image 2 or the available image-generation tool, with nearby HTML explanations. Manual SVG diagrams are acceptable only as fallback after telling the user.
- Generated-diagram captions should explain the learning purpose, not expose asset provenance. Avoid public labels like "生成教学图资产", "Generated explainer", or prompt summaries in visible UI.
- Visible buttons should describe the learning action: `读 Figure 1 架构图`, `放大 Table 2 结果表`, `解释 BLEU`, not repeated generic labels like `打开图表抽屉`.
- Use `Learn <paper short title>` as title and deployment name.

## Vercel

If the user asked for Vercel:

1. Verify the local site first.
2. Deploy the static directory.
3. Rename the Vercel project to `learn-<paper-short-title>` when feasible.
4. Open or verify the live deployment URL.
5. Report the URL and any domain limitation separately.

## Validation script

Run:

```bash
python3 /path/to/paper-to-learning-site/scripts/audit_learning_site.py <site-dir-or-index.html>
```

Treat script errors as must-fix unless the output clearly identifies a false positive.
For final delivery, run strict mode:

```bash
python3 /path/to/paper-to-learning-site/scripts/audit_learning_site.py <site-dir-or-index.html> --strict
```
