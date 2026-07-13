---
name: paper-to-learning-site
description: "Turn academic papers, PDFs, research reports, or difficult articles into visual-first teaching decks: a sequence of Image 2 or other image-model explainer slides delivered as an interactive 16:9 HTML presentation, PNG slide set, PDF, and optionally Vercel. Also supports a complete bilingual source reader as an optional evidence layer. Use when the user asks for 论文讲解PPT, 论文讲解图, paper explainer deck, visual paper course, bilingual paper explanation, figure/table teaching, or a paper learning website."
---

# Paper To Learning Deck

## Goal

Turn a difficult paper into a coherent visual lesson for a college student with no professional background. The primary product is a reading-first 16:9 teaching deck made from a sequence of explanatory pages and generated teaching images. HTML is the presentation and sharing container, not the product idea itself.

The deck must help the learner answer:

- What problem is the paper solving and why does it matter?
- What prerequisite concepts do I need first?
- What did the authors build, argue, or test?
- How does the method work step by step?
- What does each important figure/table compare?
- What evidence supports each conclusion?
- What remains uncertain or limited?

Keep the former complete bilingual reader as an optional evidence mode, not the default main experience.

## Default Deliverable

Create a reading-first visual deck with:

- one self-contained `index.html` using a fixed 1920x1080 stage scaled to the viewport
- previous/next, keyboard, overview, progress, fullscreen, and direct-slide navigation
- local raster teaching images under `assets/visuals/`
- cropped source figures/tables under `assets/evidence/`
- a structured `data/learning-deck-manifest.json`
- optional per-slide PNG export and one PDF export
- optional Vercel deployment when requested

Default length is 18-36 slides. Split dense ideas into more slides instead of shrinking text or combining unrelated concepts.

## Non-Negotiables

- Run tool and source preflight before extraction or image generation.
- Extract and inventory the whole main paper before outlining. Do not build from only the abstract or selected snippets.
- Organize the deck by learner questions and causal logic, not mechanically by the paper table of contents.
- Use one main teaching question per slide. A slide may contain supporting detail, but must have one obvious cognitive job.
- Make explanatory visuals the main feature. Most teaching slides should contain a substantial generated visual, source figure/table, formula breakdown, or carefully composed evidence graphic.
- Generate at least one teaching visual per major concept and at least one per paper chapter/logic unit when an image materially helps. Prefer several focused visuals over one overloaded poster.
- Use Image 2 / `gpt-image-2` when available. If unavailable, use another real image-generation model or user-configured image route. Record the actual model; never claim Image 2 when another model was used.
- If no image model is available, report the missing route and offer configuration guidance. Use manual SVG/CSS diagrams only after explicit user approval; do not silently downgrade.
- A chat preview does not count. Every generated visual must be a local PNG/JPEG/WebP asset embedded in the deck.
- Choose visual style from the paper's subject, objects, era, emotional tone, source figures, and audience. Do not impose one house style on every paper.
- Generate three genuinely different title/content style previews before the full deck unless the user already chose a direction or explicitly asks to skip previews.
- Keep image labels short and Chinese-dominant for Chinese readers. Put long explanations, citations, exact values, and bilingual text in selectable HTML.
- Do not use generated images as evidence. Generated visuals explain; source text, source figures, tables, formulas, and experiments prove.
- Every important conclusion must name the comparison baseline, metric/dimension, direction or value, source evidence, and limitation.
- Every important paper figure/table must be shown and explained. Crop or split dense multi-panel figures instead of shrinking full-page screenshots.
- Explain prerequisites before paper-specific use: field definition, plain-language analogy, meaning in this paper, author usage, and common misunderstanding.
- Never expose production notes, reader targeting, prompt text, asset status, manifest terms, or internal reasoning in public slides.
- Validate slide overflow, visual legibility, navigation, image loading, source traceability, and export rendering before delivery.

## Intake

Ask these three questions unless already answered or the user says to use defaults:

1. 是否有想重点探讨、重点解释、或者希望读者特别关注的内容？
2. 需要本地 HTML、PNG/PDF 图集，还是还要部署到 Vercel？
3. 默认按“无专业背景大学生”的认知水平解释，可以吗？

Defaults: explain all difficult concepts and evidence; create local HTML plus PNG/PDF-ready deck; target a non-specialist college student.

## Required References

Read before planning:

- `references/intake-and-planning.md`
- `references/pedagogy-rules.md`
- `references/novice-reader-research.md`
- `references/visual-deck-storytelling.md`

Read before visual design and image generation:

- `references/visual-style-routing.md`
- `references/image2-diagram-guidance.md`
- `references/deck-design-quality-gate.md`
- `references/figure-table-explanation.md` when the source contains evidence, equations, charts, or experiments
- `references/image-model-routing.md`

Read before implementation and delivery:

- `references/implementation-and-deploy.md`
- `references/deck-qa-checklist.md`
- `references/qa-checklist.md` only when building the optional full reader

## Workflow

### 1. Preflight And Source Inventory

1. Run `scripts/preflight_learning_site.py --source <paper.pdf>`.
2. Stop on unreadable or truncated sources.
3. Extract the complete main text with stable source ids, section, page, order, normalized snippet, and hash.
4. Inventory all figures, tables, equations, algorithms, appendices, and important examples.
5. Build a prerequisite list, hard-concept list, claim/evidence map, and likely novice misconceptions.
6. Detect available image routes in this order: built-in image generation, configured image skill/tool, OpenAI-compatible image API, another user-configured model. Record the selected route.

### 2. Build The Teaching Story

Create a paper logic map before writing slides:

1. The real-world or intellectual problem.
2. Why existing approaches are insufficient.
3. Prerequisites the learner needs.
4. The author's core move.
5. Components and process in causal order.
6. How data, training, simulation, or evaluation are separated.
7. Experimental setup before results.
8. Evidence, comparisons, and limitations.
9. A final learner reconstruction of the whole paper.

For every planned slide, record:

- `learner_question`
- `one_sentence_answer`
- `source_ids`
- `visual_job`
- `visual_type`
- `evidence_or_illustration`
- `misconception_to_prevent`
- `next_slide_bridge`

Do not create a slide merely because a paper section exists. Create it because the learner needs a question answered.

### 3. Choose Explanation Granularity

- Give one slide to every prerequisite that would block later understanding.
- Give one or more slides to every multi-step mechanism.
- Separate world/data construction, model training, simulation execution, and evaluation when the paper contains them.
- Separate a source figure overview from panel-level interpretation when one slide cannot make labels readable.
- Split long method pipelines into overview, component pages, and a concrete worked example.
- For formulas: show the original formula, symbol meanings, one step at a time, and a tiny numeric or concrete example.
- For results: show experimental setup first, then evidence, then conclusion. Never present the conclusion several slides before the table or figure.
- Use a chapter/section recap framed as “本章核心要点回顾”, including a Feynman-style reconstruction, not an exam-like quiz.

### 4. Design The Visual Language

1. Derive 2-3 plausible styles from the paper itself.
2. Generate three authentic preview slides with real paper content.
3. Choose or obtain the user's choice.
4. Write a compact design brief: typography, palette, material/texture, image style, layout grammar, evidence color, limitation color, and animation behavior.
5. Keep one coherent visual system across the deck while allowing different visual forms for concepts, methods, evidence, formulas, and recaps.

Examples, not fixed templates:

- agent simulation or game world: pixel art, map, rooms, characters, event paths
- history or classical texts: restrained ink, archival paper, maps, timelines, artifact details
- biology or medicine: editorial scientific illustration, labeled structures, process layers
- algorithms or systems: precise technical editorial diagrams, pipelines, architecture cutaways
- social science or humanities: magazine editorial, scenes plus argument maps, timelines
- economics or business: evidence-first report graphics, comparison matrices, causal loops

Do not sacrifice clarity for period styling. A historical deck may use an archival visual language while charts, dates, and citations remain crisp HTML.

### 5. Generate Teaching Images

For each visual:

1. State the local learner question and why prose alone is insufficient.
2. Choose the visual form: scene, process, cycle, cutaway, comparison, timeline, system map, metaphor, data-first editorial graphic, or micro-sequence.
3. Compress in-image copy to 3-7 short Chinese labels and at most 1-3 brief callouts.
4. Put exact data, nuanced explanation, citations, and bilingual passages outside the bitmap.
5. Generate a high-resolution raster asset with safe margins and the deck's chosen style.
6. Inspect labels, arrows, factual objects, crop, and readability. Regenerate failed assets.
7. Save prompt, model, file path, dimensions, source links, teaching purpose, and rejected-attempt reason when relevant.

Do not make every image a flowchart. Vary the visual grammar according to the idea being taught.

### 6. Compose The Deck

- Use a fixed 1920x1080 stage and scale it uniformly; do not reflow slide content on phones.
- Prefer a single self-contained HTML file with local assets and no build requirement.
- Use real deck navigation and accessible keyboard controls.
- Use generated visuals as large primary objects, not tiny thumbnails beside long text.
- For image-led slides, prefer a large image above or full-bleed with concise HTML explanation below/alongside.
- Use source evidence slides for figures, tables, formulas, and quotations, with page/source references.
- Add “查看原文依据” to important claims. It may open a non-obscuring evidence panel or jump to an appendix/evidence slide.
- Keep original-language quotations short on main slides. Put longer bilingual source passages in evidence slides or the optional full reader.
- Preserve a clear progress rhythm: question -> visual explanation -> source evidence -> conclusion -> bridge.

### 7. Validate And Deliver

1. Run `scripts/audit_learning_deck.py <deck-dir-or-index.html> --strict`.
2. Render every slide at 1920x1080 and at one smaller viewport.
3. Check no text/image overlap, clipping, unreadable labels, empty states, or broken navigation.
4. Inspect all generated images visually; OCR alone is insufficient.
5. Verify every important claim returns to the correct source paragraph, figure, table, formula, or experiment.
6. Run three adversarial passes: visual design, novice teaching clarity, and source/evidence fidelity.
7. Export PNG/PDF if requested and verify several exported pages.
8. Deploy to Vercel only after local QA passes.

## Optional Full Reader Mode

Build the former chapter-switching bilingual reader only when the user asks to read substantial original text in-page or when the paper requires close reading. Reuse:

- `assets/reader-runtime.js`
- `references/reader-interactions.md`
- `references/reader-runtime-contract.md`
- `references/layout-and-visual-patterns.md`
- `references/design-quality-gate.md`
- `scripts/audit_learning_site.py`

In this mode, retain paragraph-level original text, Chinese translation, plain-language explanation, inline terms, synchronized notes, figures near claims, and exact source coverage. The visual deck can link into the reader's evidence sections.

## Delivery Standard

The result should feel more useful than a conventional PPT because every page is visually taught, evidence-linked, self-contained enough for asynchronous reading, and still traceable to the paper. It should feel more reliable than a summary website because it does not pretend that decoration or generated diagrams are proof.
