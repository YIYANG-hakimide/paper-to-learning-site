# Image 2 Diagram Guidance

## Use images as teaching tools

Use Image 2 or the available image generation tool to create diagrams that reduce cognitive load. Generate more visuals when the paper has abstract mechanisms, multi-step methods, experiments, or unfamiliar terms.

Do not silently replace requested Image 2 diagrams with hand-written SVG diagrams. If no image-generation tool is available, stop and report that generated teaching visuals are blocked or ask whether a lower-fidelity SVG fallback is acceptable.

Minimum default:

- at least one generated explainer image per chapter
- one generated image for each major hard concept
- additional images for method pipelines, world-building, data construction, training loops, experiment comparisons, and result interpretation

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

## Prompt pattern

For generated visuals, specify:

- target learner: non-specialist college student
- learning purpose: the one thing the image must clarify
- visual form: flowchart, scene, metaphor, consulting diagram, etc.
- style tied to paper topic, not generic AI aesthetics
- for Chinese-bilingual sites, use Chinese as the dominant in-image language; include English only as short aliases for canonical terms when helpful
- allow short in-image labels and 1-3 concise explanatory callouts when they make the diagram easier to read
- avoid long paragraphs, dense bilingual text, citations, or exact table values baked into the image
- avoid factual scores, rankings, percentages, or improvement claims inside the image unless those values are sourced and also explained in nearby HTML
- leave clean areas for HTML labels or expanded explanations when needed
- output should be legible at web card size
- produce bitmap assets (`.png`, `.jpg`, or `.webp`) unless the image tool returns another real generated-image format

Example prompt:

```text
Create a clean explainer diagram for a Chinese-bilingual learning site. Topic: supervised fine-tuning in this paper. Show three stages: 人类标注样例, 模型练习, 新任务评估. Use a warm pixel-world classroom metaphor with small characters, arrows, and simple icons. Use Chinese labels and 1-2 brief Chinese callouts inside the image; include short English aliases only when useful. Keep detailed definitions and bilingual explanation for nearby HTML. Avoid generic neon AI dashboard style.
```

## HTML pairing

Every generated image needs nearby HTML explanation:

- what problem the image helps explain
- how to read it
- how it maps to the paper
- what simplification it makes

Do not rely on an image alone for factual explanation.

Small amounts of text inside generated images are useful for orientation. The rule is "brief and visual", not "text-free": use short stage names, arrows, labels, or callout phrases inside the bitmap, then put the full teaching explanation in selectable HTML.

Do not prompt Chinese-bilingual explainer images with English-only labels such as "Sequential bottleneck" or "Parallel training" unless the user explicitly wants English-only visuals. Prefer `顺序瓶颈 / sequential bottleneck` or just `顺序瓶颈` when the concept is explained nearby in HTML.

Do not create a public section titled like "生成教学图资产" or "Generated assets". Generated images should appear in the chapter where they teach something, with reader-facing labels such as "机制图解", "流程图", "证据地图", or "概念类比".

## Provenance

Record generated visuals in `data/learning-site-manifest.json`:

- file path
- model/tool used
- chapter/section
- teaching purpose
- prompt summary
- prompt language
- in-image text language
- linked source ids or claim ids
- factual values used and their source refs, if any

If the asset was manually drawn SVG, mark it as `manual-svg-fallback` and do not count it as an Image 2 generated visual.
