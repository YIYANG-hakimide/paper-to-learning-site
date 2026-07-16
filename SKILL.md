---
name: paper-and-book-to-visual-learning
description: "Turn papers, books, chapters, articles, research reports, white papers, manuals, PDFs, or other difficult long-form sources into one of three guided visual-learning outputs: a native model-generated infographic album for self-study, a dense presentation report delivered as PDF plus editable PPTX, or an interactive bilingual HTML reader. Use when the user asks to visualize or explain a paper, book, article, report, or long text; make 论文讲解图, 书籍图册, 文章可视化, 论文PPT, research presentation, visual learning album, bilingual close reading, figure/table teaching, or a source learning website."
---

# Paper and Book to Visual Learning

## Goal

Turn a difficult long-form source into a coherent visual lesson for a college student with no professional background. Papers remain a primary use case, but the source may also be a book, chapter, article, report, white paper, manual, or another substantial text. Ask which final form the user needs, then build only that primary output:

1. **学习图册 / Image album**: an ordered set of high-information, model-generated explainer images for self-study.
2. **PPT / Presentation report**: a dense, editable 16:9 consulting-style report for presenting and later reading, delivered as PPTX plus PDF.
3. **HTML / Interactive site**: an interactive, bilingual or Chinese guided reader that can be deployed.

All three modes share the same teaching logic, source fidelity, evidence rules, and source-specific visual direction. Image series is optimized for personal study; PPT is optimized for presenting and discussing with others; HTML is optimized for interactive close reading. They differ in information density, composition, interaction, export, and QA.

## Mandatory Intake

Ask all unresolved questions in one compact message. Do not spread intake across several turns. The output mode is mandatory unless the user's request already names it; after the mode is known, the user may answer `其余全部默认` and begin immediately.

1. 最终需要哪一种？
   - `学习图册`：信息密度最高，适合自己学习；每页是生图模型直接生成的完整讲解图，并附顺序一致的 PDF。
   - `PPT`：可编辑，适合讲述、汇报和分享；默认交付 PPTX + PDF，信息密度接近演示型咨询报告。
   - `HTML`：可交互、可扩展，适合逐段精读、双语对照和继续补充。
2. 是否有想重点探讨、重点解释、或者希望读者特别关注的内容？
3. 默认按“无专业背景大学生”的认知水平解释，可以吗？
4. 图片/PPT 规模：`精简`、`中等`、`详细`、还是 `自动判断`？
5. 是否有视觉风格偏好或参考图？没有则由原始材料主题自动决定。
6. 是否希望在正式生成前查看内容策划或一张视觉样张？默认都跳过以提高速度。
7. HTML 是否需要部署？默认 PPT 同时交 PDF 与可编辑 `.pptx`，HTML 只交本地包。

Default unresolved values are: no special focus, non-specialist college reader, automatic size, source-derived visual direction, no planning preview, no sample, PDF-plus-PPTX delivery, local-only HTML. Ask once, then do not add a second confirmation gate unless the user requested a planning preview or sample.

## Output Modes

### Image Album

Create a logically ordered album of native generated infographics. This mode is not a portrait PPT, not a template wrapped around illustrations, and not a folder of unrelated pictures.

- Every final bitmap must be the direct full-frame output of a real image model. In Codex, use the built-in system `imagegen` skill first and let it choose the current preferred model. Do not add titles, labels, cards, footers, source crops, or explanatory text with HTML, SVG, Pillow, Canvas, Photoshop, or another compositor afterward.
- When text, facts, or layout are wrong, regenerate the complete image with the image model. Do not repair the page with deterministic overlays. Cropping, padding, screenshotting, and template framing do not turn an illustration into a valid final infographic.
- Every image has a clear Chinese title and enough native in-image explanation to stand alone. Canonical English terms may appear as short aliases.
- Keep one coherent art direction across the album while varying the teaching form: argument map, knowledge map, mechanism diagram, system architecture, experiment flow, causal chain, scene explanation, comparison, or text-led infographic.
- Always include two separate early images: a full-source reading/argument map and a core-idea/contribution map. Other images are chosen dynamically from hard concepts, chapter logic, methods, system architecture, examples, experiments, evaluation flow, causal/evidence chains, and the user's focus.
- Image mode may reinterpret source evidence visually, but it does not need to reproduce every source figure/table or display citations inside the image. Keep source traceability in internal data and never invent facts or numbers.
- Use the aspect ratio that best fits the teaching job; keep the album visually coherent even when a justified diagram needs another ratio.
- Deliver only the numbered high-resolution PNG/JPEG/WebP sequence and a page-matched album PDF as user-facing artifacts. Keep contact sheets, storyboard, manifest, prompts, and QA records internal.

### PPT / Presentation Report

Create a 16:9 presentation report for explaining the source to other people. It must work during a live presentation and remain understandable when read afterward. Deliver both PDF and editable `.pptx` by default.

- Use the current official `Presentations` skill and its editable presentation engine. In Codex, read the installed Presentations skill before authoring and use its required artifact-tool workflow. Do not use screenshot-only decks, `python-pptx`, or a stack of flattened full-slide images as the editable PPTX.
- Use fixed 16:9 pages with consulting/research-report information density, readable hierarchy, and page-specific composition.
- The opening pages must explain what the source examines, why it matters, its answer or central ideas, and how the full reasoning unfolds. Combine overview and argument map when the source is simple; split them when needed.
- Teach the minimum prerequisite knowledge before it is used, then explain remaining terms at their first point of need.
- Organize each page around one conclusion-led message, but do not mistake one message for one sentence. A normal teaching page should combine the conclusion, structured explanation, evidence/example, implication, and relevant boundary. Judge completeness from the rendered page, not from a mechanical character quota.
- Before layout, create a page-level visual inventory and route each object to generated visual, image-to-image reinterpretation, deterministic diagram/chart/table/formula, or faithful source crop. Use all routes when the source needs them; there is no single required format.
- For every non-trivial PPT, make real image-model calls for the concepts, mechanisms, architectures, scenes, abstract processes, and worked examples that benefit from illustrative explanation. In Codex, the first route is the system `imagegen` skill. Do not silently replace planned generated visuals with generic cards, simple shapes, CSS, SVG, Canvas, or Pillow drawings.
- Route exact data to native editable charts, exact tables/formulas to deterministic layout, simple flows to native editable slide shapes, complex networks to Graphviz, sketch-like explanations to Excalidraw, abstract/high-aesthetic explanations to ImageGen, and original evidence to tightly cropped or enlarged source objects.
- Inventory important source figures/tables. Show, crop, split, enlarge, annotate, or faithfully redraw the important ones. Explain what is tested, how to read the axes/panels, the baseline, metric, result, supported conclusion, and relevant limitation.
- Avoid both empty keynote pages and unstructured document dumps. Density must come from structured reasoning and evidence, not tiny type or copied paragraphs. Split only when the page has more than one major message or cannot stay readable.
- Export and verify both PPTX and PDF: page order, crop, font rendering, Chinese readability, figure legibility, and editable title/body/chart/table/shape integrity. Render a contact sheet plus every full-size page and compare PPTX/PDF outputs.
- About 20 pages should use at least six genuinely different composition families; a similar structure must not repeat more than twice in sequence. At least 70% of teaching pages need a meaningful visual object, and ordinary pages should not be dominated by raw source screenshots.
- After at least two repair rounds, if the PPT still fails the strict visual, narrative, editability, or rendering gate, do not deliver the bad deck. Ask whether the user wants another PPT repair round or a newly generated learning album; never switch modes silently or rename slide screenshots as an album.

### HTML / Interactive Site

Create the guided interactive reader originally developed by this skill.

- Put readable source text in-page; do not use a PDF iframe as the primary experience.
- For non-Chinese sources, provide original text, Chinese translation/reading, and plain-language explanation.
- Keep terms inline at the exact words they explain.
- Put figures/tables beside the relevant claims with interactive close reading.
- Use chapter switching, evidence links, closable explanations, language controls, and responsive layouts.
- Add an opening source overview, argument/reading route, and prerequisite path. Each node should link into the relevant source paragraphs and evidence.
- Use generated teaching visuals where they materially improve understanding.
- Deliver a local static HTML package and deploy to Vercel only when requested.
- Default to a complete guided reader. For very long sources, ask whether a curated reader is acceptable before reducing source coverage; record every omission and reason.

## Size Modes For Images And PPT

- **Concise**: normally 6-10 images/pages. Preserve the problem, essential prerequisite, core method, strongest evidence, conclusion, and limitation. State that secondary detail is omitted.
- **Medium**: 11-20 images/pages. Typical for ordinary sources after automatic sizing; include prerequisites, method or argument steps, a worked example when useful, major evidence, and limitations.
- **Detailed**: 21-36 images/pages. Use for long or concept-heavy sources, full teaching, multiple evidence sections, or explicit user focus. Exceed 36 only with a clear reason and user approval.
- **Automatic**: calculate from main-text length, hard concepts, method complexity, figures/tables, and requested focus. See `references/output-modes-and-sizing.md`.

Do not hit a target count by adding filler. Do not compress required logic into tiny text merely to stay under the count. If the selected count cannot responsibly cover the user's focus, explain the tradeoff and prioritize the requested scope.

## Non-Negotiables

- Run source/tool preflight before extraction or generation.
- When any teaching visual is required, call a real image-generation model. Never describe a hand-drawn SVG, CSS composition, Canvas/Pillow output, or manually assembled diagram as model-generated.
- Detect the runtime before choosing an image route. In Codex, always read and use the installed system `imagegen` skill at `$CODEX_HOME/skills/.system/imagegen/SKILL.md` first. If the built-in route fails, distinguish a transport retry from a model/provider downgrade; never silently skip generation or switch to an older model.
- Outside Codex, inspect available image tools and configured APIs. If none exists, ask the user to configure one before image-dependent work. If several providers/models exist and no clear current default is available, ask which route to use.
- Identify the source type and requested scope before extraction. For full books or very long collections, confirm whole-source versus selected-volume/chapter scope and create a volume/chunk plan before compressing content.
- Extract and inventory the complete in-scope source before selecting content.
- Organize by learner questions and causal/argument logic, not mechanically by the source table of contents.
- Lock `data/storyboard.json` before final image generation or page implementation. Generate a preview only when the user asked for one.
- Establish the source overview and argument/reading route before detailed exposition. They may share one image/page when the source is simple.
- Every final image/page must have an owning storyboard item, source ids, teaching purpose, and previous/next bridge.
- Preserve the teaching functions needed by the source. Papers/reports usually follow problem -> prerequisites -> method/argument -> evidence -> conclusion -> boundaries; books/articles may follow central question -> idea/chapter progression -> examples -> synthesis -> tensions; manuals may follow goal -> prerequisites -> procedure -> worked example -> failure modes. Do not invent experiments, methods, or contributions that the source does not contain.
- Explain hard terms in this order: field definition, plain analogy, meaning in this paper, author usage, common misunderstanding.
- Separate data/world construction, training, inference/simulation, and evaluation whenever relevant.
- Show experimental setup, baseline, and metric before the result conclusion.
- For multi-stage methods, follow at least one concrete input through the full pipeline so the learner sees what each stage changes.
- Generated visuals explain; source text, source figures/tables, formulas, and experiments prove. Image-series mode keeps this proof link internal rather than forcing source screenshots into every image.
- Every important result names baseline, metric/dimension, direction/value, evidence, and limitation.
- Choose visual style from the source's topic, genre, era, objects, artifacts, and emotional tone. Do not force one house style.
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
- PPT also always reads `references/presentation-production.md` before authoring.
- HTML: `references/design-quality-gate.md`, `references/reader-interactions.md`, `references/reader-runtime-contract.md`, `references/layout-and-visual-patterns.md`, `references/qa-checklist.md`, `references/implementation-and-deploy.md`
- HTML also always reads `references/learning-site-ux-principles.md`.

## Shared Workflow

### 1. Preflight And Extract Once

1. Inspect the runtime and available image/deck tools first. When image album or PPT mode is selected, resolve and record a real image route with `scripts/resolve_image_route.py`; then run `scripts/preflight_learning_site.py --source <source-file> --mode <image-series|presentation-pdf|interactive-html> --image-route-receipt <receipt.json> --image-route-journal <journal.json>`. A command-line flag must never be accepted as proof that generation worked. Add `--deploy` only when HTML deployment is requested.
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
   - For PPT also record `presentation_intent: present-and-read`, `communication_job`, `reasoning_role`, `standalone_takeaway`, `reader_context`, `so_what`, `density_class`, `section_reset`, `scan_order`, `text_character_count`, `information_group_count`, and `visual_route`.
   - For factual PPT items record a reader-visible source cue, not only hidden source ids. Image-series items keep source traceability internal.
4. Validate coverage and remove filler before locking the storyboard.

### 3. Choose Visual Direction Efficiently

- If the user gave a style or reference image, use it as a direction rather than a template.
- Otherwise infer one coherent visual world from the source's subject, genre, era, objects, evidence, and emotional tone without asking the user to choose among extra options.
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
- PPT: build with the official Presentations workflow, inspect the editable deck, export PDF, verify generated-visual receipts, real layout variety, page utilization, evidence balance, and editable objects, then run the canonical final command `scripts/audit_learning_deck.py <work-dir-or-index.html> --source <source-file> --strict --require-pdf`.
- HTML: run `scripts/audit_learning_site.py <site-dir-or-index.html> --strict`; test desktop/mobile interactions and source coverage.
- For every mode, run structural checks first, then at least two review/fix rounds covering visual design, teaching logic, novice comprehension, factual fidelity, information completeness, public-copy quality, and technical rendering. Record concrete fixes in `qa/qa-report.json`.
- Use `references/mode-acceptance.md` as the final routing gate. A different mode's successful audit never counts.

## Performance Rules

- Build only the selected output. Do not automatically produce images + PDF + HTML together.
- Reuse source extraction and visual assets by source hash.
- Skip style previews unless requested.
- Keep automatic output size proportional to the in-scope source; do not default every source to 30+ items. Books may require volumes or chapter batches rather than one over-compressed artifact.
- Use deterministic HTML/CSS for exact text, citations, formulas, and tables in PPT/HTML. Never use it to compose final image-series pages.
- Regenerate only failed assets or pages, not the full set.
- Run cheap structural checks before expensive browser rendering, OCR, image regeneration, or deployment.
- Use fast sampling during iteration, then run full strict QA once the structure stabilizes.
- Treat external design skills as optional accelerators, not hidden dependencies. The source-specific art direction, reference gathering, prompt packet, fixed-stage, and evidence rules in this skill must remain sufficient when they are absent.

## Delivery

State clearly what was selected and return only the relevant primary artifact:

- Images: numbered image folder, album PDF, and count.
- PPT: final PDF, editable `.pptx`, and page count.
- HTML: local `index.html` and deployed URL when requested.

For images/PPT, report the selected and resolved size mode plus actual count. For HTML, report complete/curated scope and source coverage. For every mode, report the actual image tool/provider/model used, strict audit result, and any intentionally omitted scope. Never claim a model name that is not present in a real generation receipt.
