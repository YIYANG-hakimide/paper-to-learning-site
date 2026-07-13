# Image 2 Diagram Guidance

## Use images as teaching tools

Use Image 2 or the best available real image-generation model to create visuals that reduce cognitive load. Generated teaching images are the primary feature of the default learning deck, not a decorative supplement.

Do not silently replace generated teaching images with hand-written SVG diagrams. If Image 2 is unavailable, follow `image-model-routing.md` and use another configured image model that returns local raster assets. If no real image route exists, stop and ask whether a lower-fidelity manual fallback is acceptable.

Do not treat an Image 2 chat preview as a delivered website asset. A generated teaching image counts only after a real bitmap file is available inside the site package and referenced by both HTML and manifest.

Minimum default:

- at least one generated explainer image per chapter
- one generated image for each major hard concept
- additional images for method pipelines, world-building, data construction, training loops, experiment comparisons, and result interpretation
- most teaching slides should contain a substantial visual object; use source evidence, formulas, or worked examples where generation is not the right tool

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
- style tied to paper topic, era, objects, and emotional tone, not generic AI aesthetics or one fixed house style
- for Chinese-bilingual sites, use Chinese as the dominant in-image language; include English only as short aliases for canonical terms when helpful
- allow short in-image labels and 1-3 concise explanatory callouts when they make the diagram easier to read
- avoid long paragraphs, dense bilingual text, citations, or exact table values baked into the image
- avoid factual scores, rankings, percentages, or improvement claims inside the image unless those values are sourced and also explained in nearby HTML
- leave clean areas for HTML labels or expanded explanations when needed
- target a native 16:9 teaching image of at least 1536x864 when the visual owns most of a deck slide; validate labels at the image's actual rendered slide size
- if the concept needs many labels, create several simpler images rather than one crowded image
- produce bitmap assets (`.png`, `.jpg`, or `.webp`) unless the image tool returns another real generated-image format

Example prompt:

```text
Create a clean explainer diagram for a Chinese-bilingual learning site. Topic: supervised fine-tuning in this paper. Show three stages: 人类标注样例, 模型练习, 新任务评估. Use a warm pixel-world classroom metaphor with small characters, arrows, and simple icons. Use Chinese labels and 1-2 brief Chinese callouts inside the image; include short English aliases only when useful. Keep detailed definitions and bilingual explanation for nearby HTML. Avoid generic neon AI dashboard style.
```

## Slide Pairing

Every generated image needs nearby selectable HTML explanation:

- what problem the image helps explain
- how to read it
- how it maps to the paper
- what simplification it makes

Do not rely on an image alone for factual explanation.

Small amounts of text inside generated images are useful for orientation. The rule is "brief and visual", not "text-free": use short stage names, arrows, labels, or callout phrases inside the bitmap, then put the full teaching explanation in selectable HTML.

Borrow Guizang-style discipline for educational diagrams when appropriate: one central relationship, 3-5 short Chinese labels, quiet background, strong safe margins, and no dense legend inside the bitmap. If labels are wrong, tiny, or garbled, regenerate instead of accepting the asset.

Do not prompt Chinese-bilingual explainer images with English-only labels such as "Sequential bottleneck" or "Parallel training" unless the user explicitly wants English-only visuals. Prefer `顺序瓶颈 / sequential bottleneck` or just `顺序瓶颈` when the concept is explained nearby in HTML.

Do not create a public section titled like "生成教学图资产" or "Generated assets". Generated images should appear in the chapter where they teach something, with reader-facing labels such as "机制图解", "流程图", "证据地图", or "概念类比".

## Provenance

Record generated visuals in `data/learning-deck-manifest.json` for deck mode or `data/learning-site-manifest.json` for complete-reader mode:

- file path
- asset hash, file size, dimensions, and embedded selector when practical
- actual model/tool used; write `Image 2` or `gpt-image-2` only when that model generated the final bitmap
- chapter/section
- teaching purpose
- prompt summary
- prompt language
- in-image text language
- linked source ids or claim ids
- factual values used and their source refs, if any

## Local asset persistence contract

For each generated teaching image:

1. save or copy the bitmap into `assets/visuals/` for deck mode or `assets/diagrams/` for reader mode
2. embed that exact relative path in the relevant teaching slide or reading flow
3. record the same path in `generated_visuals[]`
4. record image dimensions/hash/file size when practical
5. add the image id to the owning slide and chapter/logic-unit coverage
6. keep `generated_visuals_expected` equal to the planned per-chapter/hard-concept count

If any generated image exists only as an in-chat preview, the deck/site is blocked. Record the blocker in QA if useful, but do not call the artifact complete and do not change expected counts to hide the gap.

If the asset was manually drawn SVG, mark it as `manual-svg-fallback` and do not count it as an Image 2 generated visual.

For positive tests and final delivery, actually call the selected real image-generation route. Do not create a placeholder PNG, screenshot an SVG, or write a model name in the manifest without a real generated bitmap copied into `assets/visuals/` or `assets/diagrams/` and embedded near the concept it teaches.
