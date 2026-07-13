---
name: paper-to-learning-site
description: "Turn academic papers, PDFs, research reports, or difficult articles into one of three guided learning outputs: an ordered series of high-information generated explainer images, a presentation-style PDF deck, or an interactive bilingual HTML learning site that can be deployed. Use when the user asks for 论文讲解图, 论文画册, 论文PPT, paper explainer deck, visual paper course, bilingual paper explanation, figure/table teaching, or a paper learning website."
---

# Paper To Learning

## Goal

Turn a difficult paper into a coherent visual lesson for a college student with no professional background. Ask which final form the user needs, then build only that primary output:

1. **图片 / Image series**: an ordered set of high-information explainer images.
2. **PPT / Presentation PDF**: a 16:9 presentation deck delivered as PDF.
3. **HTML / Interactive site**: an interactive, bilingual or Chinese guided reader that can be deployed.

All three modes share the same teaching logic, source fidelity, evidence rules, and paper-specific visual direction. They differ in information density, composition, interaction, export, and QA.

## Mandatory Intake

Ask before implementation unless already answered or the user explicitly asks for defaults:

1. 是否有想重点探讨、重点解释、或者希望读者特别关注的内容？
2. 最终需要哪种产出：`图片`、`PPT（PDF 演示稿）`、还是 `HTML 交互网页`？
3. 默认按“无专业背景大学生”的认知水平解释，可以吗？

If the user selects **图片** or **PPT**, also ask:

4. 内容规模：`精简（6-10 张/页）`、`中等（11-20 张/页）`、`详细（21 张/页以上）`，还是 `自动判断`？

Use one compact structured intake when the environment supports it. If the user says “默认”, choose the output only when their request already implies it; otherwise ask for output mode because it materially changes the product. For image/PPT size, default to automatic.

## Output Modes

### Image Series

Create a logically ordered visual album, not slide screenshots and not a folder of unrelated illustrations.

- Default canvas: 3:4 portrait for reading and sharing; adapt when the user names another channel or ratio.
- Each image may carry more information than a presentation slide, but must still answer one main learner question.
- Use Image 2 / `gpt-image-2` or another real image model for the final raster images.
- Use varied forms according to content: scene, process, timeline, comparison, architecture, annotated evidence, data-first graphic, concept map, scientific illustration, or consulting-style page.
- Put concise explanation, key labels, and source/page cues directly into the composition when readable.
- Keep exact numbers, quotations, equations, and evidence faithful; use carefully composed source crops or deterministic overlays when generation could distort them.
- Deliver the numbered PNG/JPEG/WebP sequence, contact sheet, storyboard, manifest, and QA report. Do not build HTML or PDF unless requested.

### PPT / Presentation PDF

Create a presentation-oriented 16:9 deck and deliver a PDF. An internal HTML stage may be used for layout and export, but it is not the requested final product unless the user also asks for HTML.

- Use fixed 1920x1080 pages.
- Favor speaking and showing: larger focal visuals, shorter copy, clearer pacing, chapter beats, and deliberate transitions.
- A page should usually communicate one idea within several seconds, while evidence pages may be denser.
- Generate teaching visuals as large primary objects; use source figures/tables/formulas for proof.
- Export and verify the final PDF page order, crop, font rendering, and representative pages.
- Deliver the PDF plus optional numbered page PNGs and source package. Do not present the internal HTML as the main deliverable.

### HTML / Interactive Site

Create the guided interactive reader originally developed by this skill.

- Put readable source text in-page; do not use a PDF iframe as the primary experience.
- For non-Chinese sources, provide original text, Chinese translation/reading, and plain-language explanation.
- Keep terms inline at the exact words they explain.
- Put figures/tables beside the relevant claims with interactive close reading.
- Use chapter switching, evidence links, closable explanations, language controls, and responsive layouts.
- Use generated teaching visuals where they materially improve understanding.
- Deliver a local static HTML package and deploy to Vercel only when requested.
- Default to a complete guided reader. For very long sources, ask whether a curated reader is acceptable before reducing source coverage; record every omission and reason.

## Size Modes For Images And PPT

- **Concise**: normally 6-10 images/pages. Preserve the problem, essential prerequisite, core method, strongest evidence, conclusion, and limitation. State that secondary detail is omitted.
- **Medium**: 11-20 images/pages. Default for most ordinary papers; include prerequisites, method steps, a worked example, major evidence, and limitations.
- **Detailed**: 21 or more images/pages. Use for long or concept-heavy papers, full teaching, multiple experiments, or explicit user focus. Avoid exceeding 36 without a clear reason or user approval.
- **Automatic**: calculate from main-text length, hard concepts, method complexity, figures/tables, and requested focus. See `references/output-modes-and-sizing.md`.

Do not hit a target count by adding filler. Do not compress required logic into tiny text merely to stay under the count. If the selected count cannot responsibly cover the user's focus, explain the tradeoff and prioritize the requested scope.

## Non-Negotiables

- Run source/tool preflight before extraction or generation.
- Extract and inventory the complete main paper before selecting content.
- Organize by learner questions and causal logic, not mechanically by the paper table of contents.
- Lock `data/storyboard.json` before final image generation or page implementation. Only lightweight style previews may precede storyboard lock.
- Every final image/page must have an owning storyboard item, source ids, teaching purpose, and previous/next bridge.
- Preserve the arc: problem -> prerequisites -> method -> evidence -> conclusion -> limitation -> learner reconstruction.
- Explain hard terms in this order: field definition, plain analogy, meaning in this paper, author usage, common misunderstanding.
- Separate data/world construction, training, inference/simulation, and evaluation whenever relevant.
- Show experimental setup, baseline, and metric before the result conclusion.
- Generated visuals explain; source text, source figures/tables, formulas, and experiments prove.
- Every important result names baseline, metric/dimension, direction/value, evidence, and limitation.
- Choose visual style from the paper's topic, era, objects, source artifacts, and emotional tone. Do not force one house style.
- For Chinese readers, use Chinese-dominant labels and keep long, precise copy outside unreliable generated text when necessary.
- A chat preview does not count. Final generated images must be local PNG/JPEG/WebP assets.
- Never expose prompts, QA notes, reader targeting, manifest language, or internal reasoning in the public output.

## Required References

Always read before planning:

- `references/intake-and-planning.md`
- `references/pedagogy-rules.md`
- `references/novice-reader-research.md`
- `references/teaching-coverage-contract.md`
- `references/output-modes-and-sizing.md`
- `references/visual-deck-storytelling.md`
- `references/performance-and-caching.md`

Read before visual generation:

- `references/visual-style-routing.md`
- `references/image2-diagram-guidance.md`
- `references/image-model-routing.md`
- `references/figure-table-explanation.md` when evidence, formulas, charts, or experiments exist

Read by selected mode:

- Images: `references/image-series-quality-gate.md`
- PPT: `references/deck-design-quality-gate.md`, `references/deck-qa-checklist.md`, `references/implementation-and-deploy.md`
- HTML: `references/design-quality-gate.md`, `references/reader-interactions.md`, `references/reader-runtime-contract.md`, `references/layout-and-visual-patterns.md`, `references/qa-checklist.md`, `references/implementation-and-deploy.md`

## Shared Workflow

### 1. Preflight And Extract Once

1. Run `scripts/preflight_learning_site.py --source <paper.pdf> --mode <image-series|presentation-pdf|interactive-html>` and add `--deploy` only when HTML deployment is requested.
2. Stop on unreadable, truncated, or heavily unextractable sources.
3. Create a source-hash cache and reuse extraction, page renders, crops, terms, claims, and evidence inventory across retries or output modes.
4. Extract stable source ids, pages, order, snippets/hashes, figures, tables, formulas, hard concepts, prerequisites, and likely misconceptions.
5. Create `data/teaching-inventory.json` from the full source before storyboarding. It must enumerate hard concepts, formulas/algorithms, experiments, major figures/tables, and central claims that require coverage.

### 2. Decide Scope And Story

1. Apply the selected output and size mode.
2. Build the teaching arc and complete ordered storyboard.
3. Record per item: learner question, one-sentence answer, source ids, teaching role, visual/evidence owner, misconception, layout family, and next bridge.
   - For PPT also record `presentation_beat`, `spoken_takeaway`, `density_class`, `section_reset`, `reveal_order`, and `estimated_seconds`.
   - For factual image/PPT items record a reader-visible source cue, not only hidden source ids.
4. Validate coverage and remove filler before locking the storyboard.

### 3. Choose Visual Direction Efficiently

- If the user gave a style or the paper has a strong natural visual language, infer one direction and create one representative preview.
- Generate three alternatives only when the user requests options or the visual direction is genuinely ambiguous.
- Style previews are not final content and must not multiply the final generation workload.

### 4. Produce In Small Batches

- Work in storyboard batches of 3-6 items.
- Generate only the assets owned by that batch.
- Compose or finalize the batch immediately, then create a contact sheet and check continuity.
- Reuse approved visual motifs, components, source crops, and prompt packets; do not regenerate unchanged assets.
- When supported, generate independent assets in parallel with a conservative concurrency limit.
- Fix a batch before moving forward. Do not generate all images first and assemble the story at the end.

### 5. Validate By Mode

- Images: run `scripts/audit_visual_series.py <output-dir> --strict`; inspect every final image and the full contact sheet.
- PPT: build and inspect the deck, export PDF, then run the canonical final command `scripts/audit_learning_deck.py <work-dir-or-index.html> --strict --require-pdf`.
- HTML: run `scripts/audit_learning_site.py <site-dir-or-index.html> --strict`; test desktop/mobile interactions and source coverage.
- For every mode, run design, novice-learning, and evidence-fidelity reviews. Record concrete fixes in `qa/qa-report.json`.

## Performance Rules

- Build only the selected output. Do not automatically produce images + PDF + HTML together.
- Reuse source extraction and visual assets by source hash.
- Prefer one inferred style preview when the direction is clear.
- Keep automatic output size proportional to the paper; do not default every paper to 30+ items.
- Use deterministic HTML/CSS for exact text, citations, formulas, and tables instead of asking the image model to redraw them repeatedly.
- Regenerate only failed assets or pages, not the full set.
- Run cheap structural checks before expensive browser rendering, OCR, image regeneration, or deployment.
- Use fast sampling during iteration, then run full strict QA once the structure stabilizes.
- Treat external design skills as optional accelerators, not hidden dependencies. The paper-specific art direction, reference gathering, prompt packet, fixed-stage, and evidence rules in this skill must remain sufficient when they are absent.

## Delivery

State clearly what was selected and return only the relevant primary artifact:

- Images: numbered image folder/contact sheet and count.
- PPT: final PDF and page count.
- HTML: local `index.html` and deployed URL when requested.

For images/PPT, report the selected and resolved size mode plus actual count. For HTML, report complete/curated scope and source coverage. For every mode, report the image model used, strict audit result, and any intentionally omitted scope.
