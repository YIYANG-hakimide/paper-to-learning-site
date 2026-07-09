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
- When a source file path is known, run `scripts/preflight_learning_site.py --source <path>` before extraction. If the PDF is unreadable, truncated, missing xref data, or has no extractable text sample, stop and ask for a repaired source or re-download it from an authoritative source.
- Put readable source text in the page. Do not use a PDF iframe as the primary reading experience.
- The main reading flow must contain paragraph-level source text and explanation. Do not bury the full paper inside a collapsed `<pre>` or appendix panel while showing only selected excerpts.
- For Chinese source material, keep the original Chinese and add "说人话" explanations. For other languages, provide original text, Chinese translation, and Chinese explanations.
- Non-Chinese papers need a visible language mode control such as `中英 / 中文 / EN only` unless the user explicitly rejects it.
- Use chapter-switching or section-switching reading by default, not one undifferentiated long page.
- Choose source/translation layout per section: side-by-side, stacked, interleaved close reading, figure-led, or facsimile-plus-HTML. Do not force one layout everywhere.
- Use cropped source screenshots only for layout-sensitive formulas, tables, figures, or page context, and always pair screenshots with selectable source text, Chinese reading, and explanation.
- Keep terms, figures, tables, and side notes attached to the paragraphs they explain.
- Put term triggers inline on the exact source or translated words they explain. Do not place terms only in a detached "related terms" tag strip.
- Term explanations must not obscure the paragraph being read. On desktop prefer an adjacent side panel or non-overlapping anchored panel; on mobile use a closable bottom sheet or in-flow accordion.
- Mobile term panels must preserve reading context. Prefer in-flow accordion or a bottom sheet below half the viewport; if a bottom sheet is used, opening it should keep the triggering sentence visible above the sheet.
- Term triggers must wrap the full term or phrase. Never split a normal word with an inserted button, and never create nested term buttons or raw HTML inside `data-term`.
- Explain hard terms before using them: term definition, plain-language analogy, meaning in this paper, how the author uses it, and common misunderstanding.
- Every figure/table from the paper must appear near the relevant argument unless it is truly redundant. Explain how to read it, what comparison it supports, what conclusion follows, and what it does not prove.
- Complex figures/tables must be readable by default or have a real large-view mode. If side-by-side layout makes the image small, use image-on-top/text-below, a wide evidence module, or split the visual into smaller subfigures.
- Use Image 2 or the available image generation model generously as a teaching tool: at least one generated explainer image per chapter and one per major hard concept when useful.
- Each generated teaching image must solve a local reading problem: record the concept taught, reader question, linked source ids, and why an image is needed. Do not use generated images as decorative galleries.
- For Chinese or Chinese-bilingual learning sites, generated diagrams should use Chinese-dominant labels and callouts. Keep canonical English terms only when useful, preferably paired with Chinese.
- Do not substitute hand-drawn SVG boxes for Image 2 visuals when the user asked for Image 2 or when an image-generation tool is available. Record generated visual provenance in a manifest.
- Avoid generic "AI dashboard" styling. Choose a visual language tied to the paper, audience, and source artifacts.
- Do not expose internal production notes to readers: no "面向无专业背景大学生", "reader level", "preflight", "manifest", "regression slice", "generated assets", or similar build/test wording in the public UI.
- Side notes must be public teaching copy, not internal reasoning or reviewer instructions. Use labels such as "本段核心", "为什么重要", "怎么看证据", and "容易误解"; avoid copy like "读后文时要一直追问".
- Side notes must be paragraph-specific. Do not repeat generic copy such as "这一段正在推进本章主线" across many reading blocks.
- Result, efficiency, cost, quality, or improvement claims must be evidence-linked. Record `claim_role`, baseline, metric/dimension, direction/value, `evidence_items[]`, and limitation in `claim_evidence_map`.
- Distinguish `source_claim_to_verify` from `supported_conclusion`. A paper's abstract can state a claim before experiments, but the page must visibly tell the reader it still needs later evidence.
- Do not use generated diagrams as proof of experimental/result claims. Generated visuals may illustrate; source paragraphs, source figures/tables, formulas, or experiments must support.
- Formula, algorithm, or pseudocode sections need a visible DOM module: original formula/line, symbol table, step explanation, and a tiny concrete example. Record it in `formula_breakdowns[]`.
- Chapter, review/question, language, term, figure, and visualizer states must never be empty. Remove or implement controls before delivery.
- Chapter recap must include a Feynman-style "用自己的话复述" scaffold in addition to any choice buttons, and it must link missing pieces back to evidence.
- Before delivery, run a three-pass adversarial review for UI/UX, teaching clarity, bilingual/source coverage, and figure/table explanation coverage.
- Before delivery, create and validate an interaction inventory: trigger, state change, close method, keyboard or return path, and linked source ids for chapter switching, language mode, term popovers, figure/table panels, chapter recap/review cards, and visualizers.
- Chapter recap/review feedback must show an explicit "回到原文/回到证据" path and highlight or focus the supporting reading block. Do not rely only on hidden `data-source-id` values.
- Before delivery, make the manifest prove completeness: `source_paragraphs_expected/rendered`, `source_blocks` with hashes/snippets, `chapter_coverage`, `term_anchors`, `term_explanations`, `paper_figures`, `generated_visuals`, and runtime/QA checks must match the page.
- Before delivery, make traceability exact: `source_fidelity` points to a real extraction inventory with hash, term anchors match the DOM trigger paragraph and runtime term source, and figure return links match the same source cluster recorded in the manifest.
- Before delivery, record `first_viewport_landmarks[]` so the first screen has a paper-specific visual object, not only title text. For long papers, also record `section_map[]` and `chapter_landmarks[]`.
- When maintaining this skill or tightening quality gates, run at least ten concrete regression/interaction checks and make a known-bad sample fail for the intended reasons before claiming improvement.

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
- Always read `references/learning-site-ux-principles.md` before visual design, implementation, and final QA.
- Always read `references/reader-interactions.md` before designing or coding the reader.
- Always read `references/reader-runtime-contract.md` before implementing chapter switching, language modes, side notes, term panels, figure panels, or chapter recap/review cards.
- Always read `references/layout-and-visual-patterns.md` before deciding page layout, reading modes, interaction modules, or visual style.
- Always read `references/design-quality-gate.md` before implementing visual design.
- Read `references/figure-table-explanation.md` when the source contains figures, tables, charts, equations, experiments, or data.
- Read `references/image2-diagram-guidance.md` before generating or prompting diagrams.
- Read `references/implementation-and-deploy.md` before building the static site or deploying.
- Read `references/qa-checklist.md` before final review.

Use `scripts/preflight_learning_site.py --source <paper.pdf>` before implementation when a source file is available; otherwise run `scripts/preflight_learning_site.py` and validate the source as soon as it arrives. Use `scripts/audit_learning_site.py` after implementation to catch missing local image assets, duplicate ids, weak image alt text, buried source text, weak bilingual coverage, SVG-only generated diagrams, forbidden PDF-iframe patterns, broken inline term markup, empty chapter/question/language states, term panels covering the active reading block, unreadably small figures, non-public side-note copy, and strict browser probe failures.

## Workflow

1. **Extract and inventory the source**
   - Run `scripts/preflight_learning_site.py --source <paper.pdf>` when a source path is known, or `scripts/preflight_learning_site.py` otherwise. Decide the extraction, image-generation, browser-check, and deployment routes from real tool availability and source readability.
   - If source preflight reports an unreadable/truncated PDF, stop before extraction, figure rendering, image generation, or site building. Ask for a repaired PDF or re-download from an authoritative source, then rerun source preflight.
   - Extract text into paragraphs with section labels, stable `source_id`s, source page/section, source order, and a text hash or normalized snippet for verification.
   - Extract or crop all paper figures/tables into image assets, splitting large composite figures into meaningful subfigures when that improves comprehension.
   - Build a manifest: sections, expected paragraph count, rendered paragraph count, per-block coverage, terms, inline anchors, claims, figures/tables, equations, generated visuals, tools used, and evidence.
   - Store source fidelity evidence in the manifest: each rendered source block needs `source_id`, `rendered_block_id`, `source_text_hash` or `normalized_snippet`, section/page, and chapter id.
   - Add `source_fidelity` with extraction artifact or inventory path and `paragraph_alignment_checked=true` after checking rendered source against the extracted source.

2. **Design the learning path**
   - Convert paper sections into a map or chapter navigation.
   - For each chapter, write a short "why this chapter matters" note, a logic summary, and 3-5 learning checkpoints that become "本章核心要点回顾" actions, not exam-like quizzes.
   - Decide where each term, generated diagram, source figure/table, and side note belongs in the reading flow.
   - Choose a reading layout mode for each chapter/section: parallel, stacked, interleaved, figure-led, or facsimile-plus-HTML.
   - Write a design brief that turns visual direction into UI decisions: typography scale, source text width, color semantics, spacing rhythm, component shapes, mobile behavior, and first-viewport priority.
   - Treat the design brief like a mini design-system file: it must specify tokens, component rules, layout behavior, and paper-specific avoidances, not just "modern", "Apple-like", or "anime".
   - Design from novice reader behavior: preserve the original, scaffold how to read it, teach prerequisite concepts at the moment of need, then ask the reader to inspect evidence before accepting a conclusion.
   - Plan evidence before conclusion: for every claim that something is better, faster, cheaper, more competitive, or improved, place the table/figure/evidence module before or directly beside the claim and record it in `claim_evidence_map`.
   - Sketch the first viewport before coding: title, language mode, chapter map, bilingual reading block, and synchronized side note must all be visible or one click away.
   - Choose and record the first-viewport landmark: source figure crop, Image 2 mechanism image, formula strip, algorithm snippet, table crop, or concept map. It must teach a paper-specific object.

3. **Write explanation layers**
   - Keep every main-text source paragraph paired with Chinese translation or explanation according to source language.
   - For non-Chinese sources, make the default reading card a two-column or clearly paired `Original paragraph / Chinese reading` block. Do not provide only selected excerpts plus a collapsed raw-source dump.
   - Add a plain-language explanation after each meaningful paragraph or paragraph group. Long or concept-dense original passages need proportional Chinese explanation, not a one-sentence gloss.
   - Mark key terms inline inside the original/translation/explanation text with underlines/buttons that open a term popover or side drawer. The trigger text must remain readable as part of the sentence.
   - Keep any bottom/side glossary as a secondary index only. It must never be the only place where a term is clickable.
   - For hard methods, experiments, and metrics, explain the general concept first, then explain the paper-specific use.

4. **Create visuals**
   - Use source screenshots for original figures/tables, but never screenshot blocks of text that should be selectable HTML text.
   - If preserving original text layout is important, use a cropped facsimile screenshot beside selectable source text. Screenshot-only prose is not acceptable.
   - For every source figure/table, place it next to the argument it supports and explain it individually. Do not rely on one global "figure drawer" explanation for multiple charts.
   - For multi-panel or dense source figures, either crop/split the panels or give the source image a large evidence position before explanatory text.
   - Use Image 2 diagrams for conceptual understanding: workflows, metaphors, system maps, experiment setup, training loops, comparison summaries, and "what the author is doing next" transitions.
   - Add learning interactions where useful: formula breakdowns, lineage timelines, method chats, comparison tables, ablation diagrams, concept maps, "本章核心要点回顾", or Feynman-style "用自己的话复述" checks.
   - For algorithms, formulas, and pseudocode, create `formula_breakdowns[]` entries with symbols, steps, and a small example instead of only screenshotting the page.
   - For every generated visual, record `teaches_concept`, `reader_question`, `why_image_needed`, source links, language style, and factual-value provenance in the manifest.
   - If Image 2 is unavailable, stop and tell the user before substituting SVG/manual diagrams. Do not silently downgrade.
   - Generated images may include short labels and a few concise explanatory callouts when that improves comprehension; keep long definitions, bilingual paragraphs, and precise evidence explanations in HTML.
   - For Chinese-bilingual readers, prompt generated images with Chinese labels/callouts first, plus short English term aliases only when needed.

5. **Build the site**
   - Prefer a static HTML/CSS/JS package unless the user asks for a framework or the project already has one.
   - Prefer copying or inlining `assets/reader-runtime.js` and following `references/reader-runtime-contract.md` for chapter switching, language mode, side notes, term panels, figure panels, and chapter recap/review cards.
   - Use a chapter-switching reader with a left learning panel and right bilingual source reader when appropriate.
   - Do not assume the reading pane must be left/right. Use stacked or interleaved layouts when they read better, and make mobile a first-class layout.
   - Provide expandable and closable bubbles, drawers, cards, or panels for terms, notes, figures, and logic summaries.
   - Make language mode real: `中英` shows original and Chinese reading, `中文` hides or de-emphasizes original text with a return-to-original affordance, and `EN only` preserves source text and anchors. Keep active paragraph, side notes, and drawers synchronized.
   - Remove or implement empty interactions. Buttons with no state change, repeated generic drawers, `href="#"` dead links, review cards without evidence-linked feedback, or controls that reopen the same summary are not acceptable.
   - Implement terms as context-preserving reader aids: adjacent panel on desktop, bottom sheet or in-flow accordion on mobile, close/Escape support, return-to-source link, and focus return.
   - Make synchronized side notes real: every active reading block should provide a note title/body or note text, and focusing a different block should visibly update the side note.
   - Write side notes as local teaching comments. Each note should identify what this paragraph contributes, which term/evidence to inspect, or what readers may misunderstand.
   - Do not hand-roll brittle state toggles such as `toggleAttribute("data-active", true)` for chapter panels. Active panels must be explicitly marked `data-active="true"` and inactive panels hidden.
   - Use reader-facing UI labels only. Replace production labels such as "generated asset" with learning labels such as "机制图解", "证据读法", or "概念地图".
   - Set the page title and deployment name to `Learn <paper short title>` or the best concise paper-specific name.

6. **Validate**
   - Run the site locally or open the HTML directly, depending on the build.
   - Use browser screenshots across desktop and mobile when possible; check that no text overlaps and all popovers/drawers can close.
   - Run `scripts/audit_learning_site.py <site-dir-or-html> --strict`.
   - Use `--expected-source-blocks <count>` when the extraction inventory knows the expected number of main reading blocks.
   - Perform at least three review passes: design/interaction, teaching comprehension, and bilingual/source/figure coverage. For each pass, record concrete fixes made or concrete reasons no fix was needed.
   - Check claim/evidence traceability manually: choose several "提升/更好/competitive/efficient" claims and verify the page shows evidence before the conclusion, the manifest records `claim_evidence_map`, and return links land on the correct source block.
   - For skill maintenance or regression hardening, run the ten-round acceptance loop in `references/learning-site-ux-principles.md` and record which checks passed or failed.
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
