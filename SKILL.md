---
name: paper-to-learning-site
description: Create complete interactive HTML learning websites from academic papers, PDFs, dense reports, or difficult long-form articles. Use when the user asks to turn a paper/article into a bilingual or Chinese in-page reader, chapter-map learning site, term/figure explainer, Image 2 visual teaching aid, static HTML package, or Vercel-deployable site for non-specialist readers.
---

# Paper To Learning Site

## Goal

Turn a difficult paper or long article into a complete, readable, interactive learning website. The site must let a non-specialist learner read the source in-page, understand the logic, and use interaction, visualization, and plain-language explanations to keep moving.

Default reader level: a college student with no professional background in the paper's field.

## Non-Negotiables

- Run a tool preflight before extraction or implementation, and report missing blockers or fallbacks.
- Put readable source text in the page. Do not use a PDF iframe as the primary reading experience.
- The main reading flow must contain paragraph-level source text and explanation. Do not bury the full paper inside a collapsed `<pre>` or appendix panel while showing only selected excerpts.
- For Chinese source material, keep the original Chinese and add "说人话" explanations. For other languages, provide original text, Chinese translation, and Chinese explanations.
- Non-Chinese papers need a visible language mode control such as `中英 / 中文 / EN only` unless the user explicitly rejects it.
- Use chapter-switching or section-switching reading by default, not one undifferentiated long page.
- Keep terms, figures, tables, and side notes attached to the paragraphs they explain.
- Put term triggers inline on the exact source or translated words they explain. Do not place terms only in a detached "related terms" tag strip.
- Explain hard terms before using them: term definition, plain-language analogy, meaning in this paper, how the author uses it, and common misunderstanding.
- Every figure/table from the paper must appear near the relevant argument unless it is truly redundant. Explain how to read it, what comparison it supports, what conclusion follows, and what it does not prove.
- Use Image 2 or the available image generation model generously as a teaching tool: at least one generated explainer image per chapter and one per major hard concept when useful.
- For Chinese or Chinese-bilingual learning sites, generated diagrams should use Chinese-dominant labels and callouts. Keep canonical English terms only when useful, preferably paired with Chinese.
- Do not substitute hand-drawn SVG boxes for Image 2 visuals when the user asked for Image 2 or when an image-generation tool is available. Record generated visual provenance in a manifest.
- Avoid generic "AI dashboard" styling. Choose a visual language tied to the paper, audience, and source artifacts.
- Do not expose internal production notes to readers: no "面向无专业背景大学生", "reader level", "preflight", "manifest", "regression slice", "generated assets", or similar build/test wording in the public UI.
- Before delivery, run a three-pass adversarial review for UI/UX, teaching clarity, bilingual/source coverage, and figure/table explanation coverage.

## Mandatory Intake

Before building a site, ask these three questions unless the user has already answered them in the current thread or explicitly says to proceed with defaults:

1. 是否有想重点探讨、重点解释、或者希望读者特别关注的内容？
2. 是先返回本地 HTML，还是需要部署到 Vercel？
3. 默认按“无专业背景大学生”的认知水平解释，可以吗？

If the user says to proceed with defaults, use:

- focus: explain all hard concepts and experimental evidence thoroughly
- output: local static HTML first
- reader level: non-specialist college student

## Load References

Read these reference files as needed:

- Always read `references/intake-and-planning.md` before planning the site.
- Always read `references/preflight-tools.md` before extracting or building.
- Always read `references/pedagogy-rules.md` before writing explanations.
- Always read `references/novice-reader-research.md` before designing the learning path or review criteria.
- Always read `references/reader-interactions.md` before designing or coding the reader.
- Always read `references/design-quality-gate.md` before implementing visual design.
- Read `references/figure-table-explanation.md` when the source contains figures, tables, charts, equations, experiments, or data.
- Read `references/image2-diagram-guidance.md` before generating or prompting diagrams.
- Read `references/implementation-and-deploy.md` before building the static site or deploying.
- Read `references/qa-checklist.md` before final review.

Use `scripts/preflight_learning_site.py` before implementation. Use `scripts/audit_learning_site.py` after implementation to catch missing local image assets, duplicate ids, weak image alt text, buried source text, weak bilingual coverage, SVG-only generated diagrams, and forbidden PDF-iframe patterns.

## Workflow

1. **Extract and inventory the source**
   - Run `scripts/preflight_learning_site.py` and decide the extraction, image-generation, browser-check, and deployment routes from real tool availability.
   - Extract text into paragraphs with section labels.
   - Extract or crop all paper figures/tables into image assets, splitting large composite figures into meaningful subfigures when that improves comprehension.
   - Build a manifest: sections, expected paragraph count, rendered paragraph count, terms, claims, figures/tables, equations, generated visuals, tools used, and evidence.

2. **Design the learning path**
   - Convert paper sections into a map or chapter navigation.
   - For each chapter, write a short "why this chapter matters" note, a logic summary, and 3-5 learning checkpoints.
   - Decide where each term, generated diagram, source figure/table, and side note belongs in the reading flow.
   - Sketch the first viewport before coding: title, language mode, chapter map, bilingual reading block, and synchronized side note must all be visible or one click away.

3. **Write explanation layers**
   - Keep every main-text source paragraph paired with Chinese translation or explanation according to source language.
   - For non-Chinese sources, make the default reading card a two-column or clearly paired `Original paragraph / Chinese reading` block. Do not provide only selected excerpts plus a collapsed raw-source dump.
   - Add a concise plain-language explanation after each meaningful paragraph or paragraph group.
   - Mark key terms inline inside the original/translation/explanation text with underlines/buttons that open a term popover or side drawer. The trigger text must remain readable as part of the sentence.
   - For hard methods, experiments, and metrics, explain the general concept first, then explain the paper-specific use.

4. **Create visuals**
   - Use source screenshots for original figures/tables, but never screenshot blocks of text that should be selectable HTML text.
   - Use Image 2 diagrams for conceptual understanding: workflows, metaphors, system maps, experiment setup, training loops, comparison summaries, and "what the author is doing next" transitions.
   - If Image 2 is unavailable, stop and tell the user before substituting SVG/manual diagrams. Do not silently downgrade.
   - Generated images may include short labels and a few concise explanatory callouts when that improves comprehension; keep long definitions, bilingual paragraphs, and precise evidence explanations in HTML.
   - For Chinese-bilingual readers, prompt generated images with Chinese labels/callouts first, plus short English term aliases only when needed.

5. **Build the site**
   - Prefer a static HTML/CSS/JS package unless the user asks for a framework or the project already has one.
   - Use a chapter-switching reader with a left learning panel and right bilingual source reader when appropriate.
   - Provide expandable and closable bubbles, drawers, cards, or panels for terms, notes, figures, and logic summaries.
   - Set the page title and deployment name to `Learn <paper short title>` or the best concise paper-specific name.

6. **Validate**
   - Run the site locally or open the HTML directly, depending on the build.
   - Use browser screenshots across desktop and mobile when possible; check that no text overlaps and all popovers/drawers can close.
   - Run `scripts/audit_learning_site.py <site-dir-or-html> --strict`.
   - Perform three review passes: design/interaction, teaching comprehension, and bilingual/source/figure coverage.
   - Fix issues before final delivery.

7. **Deploy only after confirming**
   - If the user requested Vercel, deploy the static site and verify the live URL.
   - If not, return the local HTML path and explain how to open it.

## Delivery Standard

The final site should feel like a guided reading product, not a summary page. A reader should be able to answer:

- What is the paper trying to solve?
- What did the authors build or argue?
- How does each major method work in ordinary language?
- What does each figure/table show, compared with what, and why does it matter?
- What evidence supports the conclusion?
- What remains uncertain or limited?
