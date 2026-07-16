# Model-Generated Diagram Guidance

## Use images as teaching tools

Use a real image-generation model to create visuals that reduce cognitive load. In Codex, always start with the installed system `imagegen` skill and let the current runtime choose its preferred model; learn the actual model name from the receipt. Generated teaching images are the complete final pages in image-series mode, a major visual layer in non-trivial PPTs, and an in-context teaching aid in HTML mode.

Do not silently replace generated teaching images with hand-written SVG, CSS, Canvas, Pillow, or manually assembled diagrams. If the built-in Codex route fails, follow `image-model-routing.md`: retry transport failures, then ask before switching to CLI/API or another model/provider. Outside Codex, use another configured image model only after the route is verified. Image-series mode stops when no capable route exists; PPT/HTML manual fallback still requires a real failed call and explicit approval.

Do not treat an Image 2 chat preview as a delivered asset. A generated teaching image counts only after a real bitmap file is available inside the selected output package and referenced by its mode-specific manifest. PPT/HTML images must also be embedded in the rendered page; image-series assets are themselves the final pages.

Coverage follows the selected output, size mode, and storyboard:

- concise mode prioritizes the core method and strongest blockers; related concepts may share one well-designed visual
- medium mode normally gives each major logic unit a substantial visual treatment
- detailed mode normally gives each major hard concept its own visual or focused micro-sequence
- add visuals for hard terms, method pipelines, world-building, data construction, training loops, experiment setup/comparison, causal/evidence chains, and result interpretation when they materially reduce cognitive load
- most image-series items and PPT teaching pages should contain a substantial visual object; use source evidence, formulas, deterministic charts, or worked examples where generation is the wrong tool
- every non-trivial PPT must embed at least one real generated bitmap, and every storyboard object routed to `generated` or `image-to-image` must be generated rather than redrawn with simple shapes

## Diagram types

Choose the type that fits the learning job:

- process flowchart: step-by-step method
- system architecture map: components and data movement
- concept metaphor: vivid analogy for a hard term
- consulting-style framework: 2x2, layered stack, swimlane, or comparison matrix
- experiment setup diagram: input, intervention, measurement, output
- before/after or baseline/variant comparison
- timeline or chapter bridge
- annotated scene diagram for virtual worlds or simulations
- data-first editorial chart: preserve exact values in HTML/nearby text and use the image to make the comparison readable
- micro-diagram sequence: several smaller images for a complex mechanism instead of one overloaded poster
- character or scene sequence: useful for agents, simulations, history, social interaction, or a concrete worked example
- cutaway or exploded view: useful for systems, devices, biological structures, and layered mechanisms
- map or route: useful for virtual worlds, historical movement, state transitions, and information flow

## Prompt pattern

For generated visuals, specify:

- target learner: non-specialist college student
- learning purpose: the one thing the image must clarify
- visual form: flowchart, scene, metaphor, consulting diagram, etc.
- style tied to source topic, genre, era, objects, and emotional tone, not generic AI aesthetics or one fixed house style
- for Chinese-bilingual sites, use Chinese as the dominant in-image language; include English only as short aliases for canonical terms when helpful
- plan a clear Chinese title, native Chinese explanation, short labels, arrows, and callouts for any mechanism, overview, comparison, architecture, or multi-actor teaching visual
- use enough text to make the image self-explanatory, but split the image when the text becomes crowded or too small
- avoid dense bilingual duplication, citations, or unsupported exact table values baked into the image
- avoid factual scores, rankings, percentages, or improvement claims inside the image unless those values are sourced and also explained in nearby HTML
- choose the aspect ratio from the teaching structure for image series; use fixed 16:9 for PPT; target at least 1536px on the long edge and validate labels at actual final size
- if the concept needs many labels, create several simpler images rather than one crowded image
- produce bitmap assets (`.png`, `.jpg`, or `.webp`) unless the image tool returns another real generated-image format

For unfamiliar or visually specific subjects, create a `visual_reference_record` before prompting:

- what needs verification
- factual sources or reference images consulted
- stable visual cues that must be preserved
- cues that are uncertain, misleading, or must not be copied

Save the final provider-neutral prompt packet and prompt hash so the asset can be reproduced or moved to another model.

Example prompt:

```text
Create a complete Chinese explainer infographic. Topic: supervised fine-tuning in this paper. The image must stand alone. Use the title `监督微调：模型先看示范，再学习怎样回答`. Explain the general definition, a plain classroom analogy, and how this paper applies it. Show three stages: 人类标注样例, 模型练习, 新任务评估. Use a warm pixel-world classroom metaphor, clear arrows, short Chinese callouts, and a readable visual hierarchy. Keep `Supervised Fine-Tuning (SFT)` only as a small alias. Do not add a generic footer, slide frame, page number, source citation, or empty decorative card.
```

## Pairing With Final Output

Every generated image needs an explanation strategy appropriate to the mode:

- image series: the complete title and explanation are generated natively as one full-frame bitmap; no later composition layer is allowed
- PPT: pair the image with exact slide text, citation, and a standalone conclusion
- HTML: pair it with selectable source/translation/explanation text

In every mode, clarify:

- what problem the image helps explain
- how to read it
- how it maps to the source
- what simplification it makes

In image-series mode the image must stand alone, while internal source records still verify factual claims. In PPT/HTML, surrounding exact text and source evidence remain visible.

Generated images need enough native text to explain the visual relationship. Image-series pages may carry substantially more integrated explanation than PPT/HTML diagrams, but the text must remain readable and visually organized.

Plan explanatory text before generation.

- Image series: ask the model to generate the entire final infographic with native Chinese title, explanation, labels, and relationships. If any important text is wrong, regenerate the entire image or switch models.
- PPT/HTML: model-generated diagrams may use native labels, while exact surrounding copy, citations, formulas, and source evidence remain deterministic and selectable.
- Source figures: use real crops and exact annotations only in PPT/HTML. Image-series mode may create an explanatory reinterpretation but must not present generated pixels as original evidence.

Do not generate an unlabeled beautiful scene and try to rescue it with one sentence below the image. The final teaching image must expose its own reading order and element meanings.

Borrow Guizang-style discipline for educational diagrams when appropriate: one central relationship, a clear visual hierarchy, quiet background, strong safe margins, and readable Chinese explanation. If labels are wrong, tiny, or garbled, regenerate instead of accepting or patching the asset.

Do not prompt Chinese-bilingual explainer images with English-only labels such as "Sequential bottleneck" or "Parallel training" unless the user explicitly wants English-only visuals. Prefer `顺序瓶颈 / sequential bottleneck` or just `顺序瓶颈` when the concept is explained nearby in HTML.

Do not create a public section titled like "生成教学图资产" or "Generated assets". Generated images should appear in the chapter where they teach something, with reader-facing labels such as "机制图解", "流程图", "证据地图", or "概念类比".

## Provenance

Record generated visuals in the selected manifest:

- image series: `data/learning-series-manifest.json`
- PPT: `data/learning-deck-manifest.json`
- HTML: `data/learning-site-manifest.json`

- file path
- asset hash, file size, dimensions, and embedded selector when practical
- actual model/tool used; write `Image 2` or `gpt-image-2` only when that model generated the final bitmap
- chapter/section
- teaching purpose
- prompt summary
- prompt language
- in-image text language
- diagram labels and visual semantic map
- scan order and text-integration method
- for image series: raw model output hash, final direct-output hash, generation receipt, and an empty pixel-postprocessing list
- linked source ids or claim ids
- factual values used and their source refs, if any

## Local asset persistence contract

For each generated teaching image:

1. save or copy the bitmap into `assets/images/` for image series, `assets/visuals/` for PPT, or `assets/diagrams/` for HTML
2. put it in the exact storyboard position; embed it in the rendered page for PPT/HTML
3. record the same path in the mode-specific item or `generated_visuals[]`
4. record image dimensions/hash/file size when practical
5. add the image id to the owning image item, presentation page, or HTML chapter/logic-unit coverage
6. keep `generated_visuals_expected` equal to the planned per-chapter/hard-concept count

If any generated image exists only as an in-chat preview, the deck/site is blocked. Record the blocker in QA if useful, but do not call the artifact complete and do not change expected counts to hide the gap.

If a PPT/HTML asset was manually drawn SVG after a real failed model call and explicit approval, mark it as `manual-svg-fallback` and do not count it as an Image 2 generated visual. Image-series mode never accepts this fallback.

For positive tests and final delivery, actually call the selected real image-generation route. Do not create a placeholder PNG, screenshot an SVG, or write a model name in the manifest without a real generated bitmap copied into the correct mode-specific asset directory and placed at the concept it teaches.
