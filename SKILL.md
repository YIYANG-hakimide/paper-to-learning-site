---
name: paper-to-learning-site
description: "Turn academic papers, PDFs, research reports, or difficult articles into one of three guided learning outputs: an ordered album of native model-generated infographics, a reading-first visual consulting report PDF, or an interactive bilingual HTML learning site that can be deployed. Use when the user asks for 论文讲解图, 论文画册, 论文PPT, paper explainer deck, visual paper course, bilingual paper explanation, figure/table teaching, or a paper learning website."
---

# Paper To Learning

## Goal

Turn a difficult paper into a coherent visual lesson for a college student with no professional background. Ask which final form the user needs, then build only that primary output:

1. **图片 / Image series**: an ordered set of high-information explainer images.
2. **PPT / Presentation PDF**: a 16:9 presentation deck delivered as PDF.
3. **HTML / Interactive site**: an interactive, bilingual or Chinese guided reader that can be deployed.

All three modes share the same teaching logic, source fidelity, evidence rules, and paper-specific visual direction. They differ in information density, composition, interaction, export, and QA.

## Mandatory Intake

Ask all unresolved questions in one compact message. Do not spread intake across several turns. The output mode is mandatory unless the user's request already names it; after the mode is known, the user may answer `其余全部默认` and begin immediately.

1. 最终需要：`图片`、`PPT（默认 PDF，可选可编辑 PPTX）`、还是 `HTML`？
2. 是否有想重点探讨、重点解释、或者希望读者特别关注的内容？
3. 默认按“无专业背景大学生”的认知水平解释，可以吗？
4. 图片/PPT 规模：`精简`、`中等`、`详细`、还是 `自动判断`？
5. 是否有视觉风格偏好或参考图？没有则由论文主题自动决定。
6. 是否希望在正式生成前查看内容策划或一张视觉样张？默认都跳过以提高速度。
7. PPT 是否需要可编辑 `.pptx`；HTML 是否需要部署？默认 PPT 只交 PDF，HTML 只交本地包。

Default unresolved values are: no special focus, non-specialist college reader, automatic size, paper-derived visual direction, no planning preview, no sample, PDF-only PPT, local-only HTML. Ask once, then do not add a second confirmation gate unless the user requested a planning preview or sample.

## Output Modes

### Image Series

Create a logically ordered album of native generated infographics. This mode is not a portrait PPT, not a template wrapped around illustrations, and not a folder of unrelated pictures.

- Every final bitmap must be the direct full-frame output of Image 2 / `gpt-image-2` or another real image model. Do not add titles, labels, cards, footers, source crops, or explanatory text with HTML, SVG, Pillow, Canvas, Photoshop, or another compositor afterward.
- When text, facts, or layout are wrong, regenerate the complete image with the image model. Do not repair the page with deterministic overlays. Cropping, padding, screenshotting, and template framing do not turn an illustration into a valid final infographic.
- Every image has a clear Chinese title and enough native in-image explanation to stand alone. Canonical English terms may appear as short aliases.
- Keep one coherent art direction across the album while varying the teaching form: argument map, knowledge map, mechanism diagram, system architecture, experiment flow, causal chain, scene explanation, comparison, or text-led infographic.
- Always include two separate early images: a full-paper logic/argument map and a core-contribution map. Other images are chosen dynamically from hard concepts, methods, system architecture, experiments, evaluation flow, causal/evidence chains, and the user's focus.
- Image mode may reinterpret paper evidence visually, but it does not need to reproduce every source figure/table or display citations inside the image. Keep source traceability in internal data and never invent facts or numbers.
- Use the aspect ratio that best fits the teaching job; keep the album visually coherent even when a justified diagram needs another ratio.
- Deliver only the numbered high-resolution PNG/JPEG/WebP sequence and a page-matched album PDF as user-facing artifacts. Keep contact sheets, storyboard, manifest, prompts, and QA records internal.

### PPT / Presentation PDF

Create a 16:9 visual consulting report that can be understood without a presenter. Deliver PDF by default; provide editable `.pptx` only when requested. An internal HTML stage may be used for exact layout and export, but it is not the requested final product.

- Use fixed 1920x1080 pages with report-level information density, readable hierarchy, and page-specific composition.
- The opening pages must explain what the paper studies, why it matters, and how the full argument unfolds. Combine overview and argument map when the paper is simple; split them when needed.
- Teach the minimum prerequisite knowledge before it is used, then explain remaining terms at their first point of need.
- Organize each page around one core question or conclusion and include enough explanation, evidence, and `so what` for independent reading.
- Use high-quality generated visuals for core concepts, mechanisms, architectures, abstract processes, and worked examples. Do not require a generated image on every page.
- Inventory important source figures/tables. Show, crop, split, enlarge, annotate, or faithfully redraw the important ones. Explain what is tested, how to read the axes/panels, the baseline, metric, result, supported conclusion, and relevant limitation.
- Avoid both empty keynote pages and document dumps. Split overloaded pages instead of shrinking text.
- Export and verify the final PDF page order, crop, font rendering, Chinese readability, figure legibility, and representative dense pages.

### HTML / Interactive Site

Create the guided interactive reader originally developed by this skill.

- Put readable source text in-page; do not use a PDF iframe as the primary experience.
- For non-Chinese sources, provide original text, Chinese translation/reading, and plain-language explanation.
- Keep terms inline at the exact words they explain.
- Put figures/tables beside the relevant claims with interactive close reading.
- Use chapter switching, evidence links, closable explanations, language controls, and responsive layouts.
- Add an opening paper overview, argument route, and prerequisite path. Each argument node should link into the relevant source paragraphs and evidence.
- Use generated teaching visuals where they materially improve understanding.
- Deliver a local static HTML package and deploy to Vercel only when requested.
- Default to a complete guided reader. For very long sources, ask whether a curated reader is acceptable before reducing source coverage; record every omission and reason.

## Size Modes For Images And PPT

- **Concise**: normally 6-10 images/pages. Preserve the problem, essential prerequisite, core method, strongest evidence, conclusion, and limitation. State that secondary detail is omitted.
- **Medium**: 11-20 images/pages. Typical for ordinary papers after automatic sizing; include prerequisites, method steps, a worked example when useful, major evidence, and limitations.
- **Detailed**: 21 or more images/pages. Use for long or concept-heavy papers, full teaching, multiple experiments, or explicit user focus. Avoid exceeding 36 without a clear reason or user approval.
- **Automatic**: calculate from main-text length, hard concepts, method complexity, figures/tables, and requested focus. See `references/output-modes-and-sizing.md`.

Do not hit a target count by adding filler. Do not compress required logic into tiny text merely to stay under the count. If the selected count cannot responsibly cover the user's focus, explain the tradeoff and prioritize the requested scope.

## Non-Negotiables

- Run source/tool preflight before extraction or generation.
- Extract and inventory the complete main paper before selecting content.
- Organize by learner questions and causal logic, not mechanically by the paper table of contents.
- Lock `data/storyboard.json` before final image generation or page implementation. Generate a preview only when the user asked for one.
- Establish the paper overview and argument route before detailed exposition. They may share one image/page when the paper is simple.
- Every final image/page must have an owning storyboard item, source ids, teaching purpose, and previous/next bridge.
- Preserve the teaching functions needed by the paper: problem -> necessary prerequisites -> method/argument -> evidence -> conclusion -> boundaries. Do not force every function into a separate image/page.
- Explain hard terms in this order: field definition, plain analogy, meaning in this paper, author usage, common misunderstanding.
- Separate data/world construction, training, inference/simulation, and evaluation whenever relevant.
- Show experimental setup, baseline, and metric before the result conclusion.
- For multi-stage methods, follow at least one concrete input through the full pipeline so the learner sees what each stage changes.
- Generated visuals explain; source text, source figures/tables, formulas, and experiments prove. Image-series mode keeps this proof link internal rather than forcing source screenshots into every image.
- Every important result names baseline, metric/dimension, direction/value, evidence, and limitation.
- Choose visual style from the paper's topic, era, objects, source artifacts, and emotional tone. Do not force one house style.
- For Chinese readers, use Chinese-dominant public copy. In image-series mode the complete final explanation must be generated natively inside the image; if the model cannot render it correctly, regenerate or switch models.
- A chat preview does not count. Final generated images must be local PNG/JPEG/WebP assets.
- A beautiful unlabeled scene does not count as a teaching diagram. Plan Chinese-dominant titles, labels, callouts, scan order, and visual-to-concept mapping before generation.
- Never expose prompts, QA notes, reader targeting, manifest language, or internal reasoning in the public output.
- Run the public-copy check from `references/public-copy-style.md`; rewrite templated contrast sentences, empty summaries, repeated conclusions, and production-language leakage.

## Required References

Always read before planning:

- `references/intake-and-planning.md`
- `references/pedagogy-rules.md`
- `references/novice-reader-research.md`
- `references/teaching-coverage-contract.md`
- `references/output-modes-and-sizing.md`
- `references/visual-deck-storytelling.md`
- `references/visual-page-teaching-contract.md`
- `references/performance-and-caching.md`
- `references/public-copy-style.md`
- `references/mode-acceptance.md`

Read before visual generation:

- `references/visual-style-routing.md`
- `references/image2-diagram-guidance.md`
- `references/image-model-routing.md`
- `references/figure-table-explanation.md` when evidence, formulas, charts, or experiments exist

Read by selected mode:

- Images: `references/image-series-quality-gate.md`
- PPT: `references/deck-design-quality-gate.md`, `references/deck-qa-checklist.md`, `references/implementation-and-deploy.md`
- HTML: `references/design-quality-gate.md`, `references/reader-interactions.md`, `references/reader-runtime-contract.md`, `references/layout-and-visual-patterns.md`, `references/qa-checklist.md`, `references/implementation-and-deploy.md`
- HTML also always reads `references/learning-site-ux-principles.md`.

## Shared Workflow

### 1. Preflight And Extract Once

1. Inspect the available image tool first when image-series mode is selected, then run `scripts/preflight_learning_site.py --source <paper.pdf> --mode <image-series|presentation-pdf|interactive-html>`. Add `--confirm-image-direct-output` only after confirming untouched raster export plus receipts, and add `--deploy` only when HTML deployment is requested.
2. Stop on unreadable, truncated, or heavily unextractable sources.
3. Create a source-hash cache and reuse extraction, page renders, crops, terms, claims, and evidence inventory across retries or output modes.
4. Extract stable source ids, pages, order, snippets/hashes, figures, tables, formulas, hard concepts, prerequisites, and likely misconceptions.
5. Create `data/teaching-inventory.json` from the full source before storyboarding. It must enumerate hard concepts, formulas/algorithms, experiments, major figures/tables, and central claims that require coverage.

### 2. Decide Scope And Story

1. Apply the selected output and size mode.
2. Build the teaching arc and complete ordered storyboard.
3. Record per item: learner question, one-sentence answer, source ids, teaching role, visual/evidence owner, misconception, layout family, and next bridge.
   - For image/PPT items also record `sequence_role`, `information_groups`, `scan_order`, `reader_takeaway`, and `teaching_units`.
   - For image-series items also record `page_policy`, `aspect_ratio`, `diagram_grammar`, `safe_area`, `exactness_risk`, `text_ownership: in-model`, `forbidden_slide_chrome: true`, and `deletion_test_passed`.
   - For PPT also record `presentation_intent: reading-first`, `communication_job`, `reasoning_role`, `standalone_takeaway`, `reader_context`, `so_what`, `density_class`, `section_reset`, and `scan_order`.
   - For factual PPT items record a reader-visible source cue, not only hidden source ids. Image-series items keep source traceability internal.
4. Validate coverage and remove filler before locking the storyboard.

### 3. Choose Visual Direction Efficiently

- If the user gave a style or reference image, use it as a direction rather than a template.
- Otherwise infer one coherent visual world from the paper's subject, era, objects, evidence, and emotional tone without asking the user to choose among extra options.
- Create a representative preview only when the user requested one.

### 4. Produce In Small Batches

- Work in storyboard batches of 3-6 items.
- Generate only the assets owned by that batch.
- Finalize the batch immediately, then create a contact sheet and check continuity.
- Reuse approved visual motifs and prompt packets. Reuse source crops/components in PPT/HTML only; image-series pages remain direct model outputs.
- When supported, generate independent assets in parallel with a conservative concurrency limit.
- Fix a batch before moving forward. For image-series mode, fixing means regenerating failed full-frame images with the image model, never assembling them from parts afterward.

### 5. Validate By Mode

- Images: export the page-matched album PDF, run `scripts/audit_visual_series.py <output-dir> --source <paper.pdf> --strict --require-pdf`; verify direct model provenance, inspect every final image, the full contact sheet, and the PDF.
- PPT: build and inspect the deck, export PDF, then run the canonical final command `scripts/audit_learning_deck.py <work-dir-or-index.html> --source <paper.pdf> --strict --require-pdf`.
- HTML: run `scripts/audit_learning_site.py <site-dir-or-index.html> --strict`; test desktop/mobile interactions and source coverage.
- For every mode, run structural checks first, then at least two review/fix rounds covering visual design, teaching logic, novice comprehension, factual fidelity, information completeness, public-copy quality, and technical rendering. Record concrete fixes in `qa/qa-report.json`.
- Use `references/mode-acceptance.md` as the final routing gate. A different mode's successful audit never counts.

## Performance Rules

- Build only the selected output. Do not automatically produce images + PDF + HTML together.
- Reuse source extraction and visual assets by source hash.
- Skip style previews unless requested.
- Keep automatic output size proportional to the paper; do not default every paper to 30+ items.
- Use deterministic HTML/CSS for exact text, citations, formulas, and tables in PPT/HTML. Never use it to compose final image-series pages.
- Regenerate only failed assets or pages, not the full set.
- Run cheap structural checks before expensive browser rendering, OCR, image regeneration, or deployment.
- Use fast sampling during iteration, then run full strict QA once the structure stabilizes.
- Treat external design skills as optional accelerators, not hidden dependencies. The paper-specific art direction, reference gathering, prompt packet, fixed-stage, and evidence rules in this skill must remain sufficient when they are absent.

## Delivery

State clearly what was selected and return only the relevant primary artifact:

- Images: numbered image folder, album PDF, and count.
- PPT: final PDF and page count; optional `.pptx` when requested.
- HTML: local `index.html` and deployed URL when requested.

For images/PPT, report the selected and resolved size mode plus actual count. For HTML, report complete/curated scope and source coverage. For every mode, report the image model used, strict audit result, and any intentionally omitted scope.
