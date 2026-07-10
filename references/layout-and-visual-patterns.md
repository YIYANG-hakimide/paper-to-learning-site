# Layout And Visual Patterns

Use this file when deciding how the paper reader should look and behave. Do not force one layout such as left-right bilingual columns. Pick the arrangement that helps the reader keep reading and understand evidence.

## Source Rendering Modes

Default to selectable HTML text. Use screenshots only when the original layout itself carries meaning.

- `parallel-bilingual`: original and Chinese reading side by side. Best for short-to-medium paragraphs on desktop.
- `stacked-bilingual`: original first, Chinese reading below, plain explanation after. Best for mobile, dense paragraphs, or narrow screens.
- `interleaved-close-reading`: source sentence or phrase, Chinese translation, then explanation. Best for formulas, definitions, multi-step method paragraphs, or paragraphs packed with terms.
- `figure-led`: figure/table first, then original paragraph and explanation. Best for experiment and data sections where the reader should inspect evidence before accepting the conclusion.
- `facsimile-plus-html`: cropped paper screenshot plus selectable original text, translation, and explanation. Use only for layout-sensitive formulas, tables, multi-column snippets, or pages where PDF typography is needed to understand context.
- `source-hidden-on-demand`: original collapsed only after a visible Chinese reading block. Use sparingly for review mode, never as the main first-pass reading path.

Rules for screenshots:

- Never screenshot normal prose as the only source text.
- If a source screenshot is used, pair it with selectable text, translation/explanation, source id, page number, and a reason such as `formula layout`, `table layout`, or `multi-panel figure`.
- Crop tightly. A giant page screenshot is usually a failure unless the page layout is itself the object of study.
- Do not let all paper figures/tables become same-size full-page screenshots. If several assets share the PDF page dimensions, crop or split them and record the crop/split in the manifest.
- If the image is dense, the default layout should not be a cramped left-image/right-text split. Use image-on-top/text-below, a wide figure band, zoomable evidence view, or split the figure into subfigures.

## Layout Selection

Choose per section, not globally:

- Abstract/introduction: `stacked-bilingual` or `parallel-bilingual` with strong plain-language paragraph notes.
- Method: `interleaved-close-reading`, formula breakdowns, system diagrams, and inline terms.
- Architecture/system papers: reader plus large diagram rail; use hotspots and "follow the data" arrows.
- Experiments/results: `figure-led` with table/figure on one side and "怎么看 / 相比谁 / 结论 / 限制" on the other.
- Dense experiments/results: use a wide source figure/table first, then explanation below, or split into row/panel cards. The reader must be able to inspect labels and numbers before reading the conclusion.
- Evidence before conclusion: when a section claims improvement, competitiveness, superiority, correlation, or failure, place the supporting table/figure/evidence module before or directly beside the conclusion. Do not ask the reader to accept a result before seeing how to read the evidence.
- Claim traceability: record important result/efficiency claims in `claim_evidence_map` with baseline, metric or dimension, direction/value, evidence ids, and limitation. If the site says "更好", "提升", "competitive", "efficient", or "降低成本", the reader should know compared with what and where the evidence is.
- Theory/math: formula card with symbol table, plain example, and derivation steps.
- Survey/related work: timeline, lineage map, comparison table, and chapter checkpoints.
- Long papers: chapter switching plus review cards; do not make one endless page.

On mobile, collapse to one column in this order: source, Chinese reading, explanation, local figure/term controls, then optional deeper panel.

## Interaction Patterns

Borrow learning patterns from strong readers and study apps:

- Anchored annotation: click exact words or table cells; the side panel opens at the relevant definition, evidence, or caveat.
- Right-pane visualizer: clicking a concept can show a formula walkthrough, graph, 2D animation, Image 2 diagram, or source quote.
- Formula breakdown: show the original formula, define every symbol, then give a tiny numeric or concrete example.
- Algorithm walkthrough: for pseudocode, explain line by line what state changes, what input it uses, and how the next line depends on it. Do not rely on a full-page screenshot plus one caption.
- Method chat: for multi-component systems, let components "speak" in a short dialogue only when it clarifies role and order.
- Timeline/lineage: show how previous work leads to the current paper; use it as orientation, not decoration.
- Comparison table: let readers compare methods, baselines, variants, or ablations.
- Knowledge map: 6-25 concept nodes with edges can help review, but it must link back to the exact paragraphs.
- Quiz/Feynman card: after a chapter, ask the reader to explain a term or choose which claim a table supports.
- Feynman scaffold: include at least one structured recap that asks the reader to fill or check "问题是什么 / 方法怎么做 / 相比谁 / 证据是什么 / 不能推出什么". Multiple-choice checks are secondary.
- Review feedback must be evidence-specific. Name the exact table/figure/metric/column/curve/prompt block to inspect, not just "回到本章关键段落".

Use these as learning actions. Avoid interactions that only reveal the same summary again.

## Visual Style Decision

Before coding, write a short design brief:

- paper personality: calm/productive, playful, anime/pixel, editorial, lab notebook, consulting report, etc.
- source artifact cue: figures, screenshots, equations, tables, virtual worlds, datasets, architecture diagrams
- reading density: light first pass, close reading, evidence-heavy, or review-heavy
- layout modes chosen for each chapter type
- visual assets needed: original figures, cropped subfigures, Image 2 diagrams, icons, generated metaphors
- design-system rules: tokens for type, color, spacing, figure sizes, panel behavior, and mobile states. Inspired by design-md style specs, write concrete constraints instead of vague style words.

The style does not need to match Agentopia. Agentopia is only a floor for care and interaction. Aim for a site that feels designed for this paper.

## Verification Expectations

After implementation:

- Serve over HTTP when possible and verify in a browser.
- Check desktop first viewport: paper title, chapter navigation, language mode for non-Chinese papers, source paragraph, Chinese reading, explanation/side note, and at least one term or evidence affordance.
- Check mobile: no horizontal overflow; bilingual blocks stack cleanly; panels are closable.
- Smoke test: switch chapter, switch language, open/close term, open/close figure/table explanation, activate a visual or chapter-review control.
- Check evidence order: result claims should not appear several reading blocks before the figure/table that supports them.
- Check return links: visible figure links, runtime figure metadata, and manifest `linked_source_ids` should point to the same paragraph or claim cluster.
- Check side-note specificity: repeated generic notes mean the page is still a template, even if the source text is present.
- Check formula/algorithm coverage: formulas and pseudocode need `formula_breakdowns[]` with symbols, steps, and a tiny example.
- Record `layout_strategy`, `source_rendering_modes`, `source_screenshot_blocks`, and `interaction_inventory` in the manifest.
- Record `visual_readability_checks` and note whether dense figures used large view, split panels, or image-top layout.

## Reference Inspirations

- `jimliu/baoyu-design`: design process, HTTP preview, screenshot verification, and anti-slop design craft.
- `beltromatti/get-it`: document-anchored concept tags, right-pane visualizers, knowledge graph, review cards, and Feynman-style self-explanation.
- `KaguraTart/paper-to-course`: course modules, timeline, comparison table, formula breakdown, method chat, ablation diagram, and chapter-review components.
- `c-narcissus/agent-paper-grounded-reading`: traceability artifacts and static evidence reader contract.
- `FeijiangHan/PaperForge`: author-reasoning reconstruction, fragile-assumption checks, minimal reproduction, and strongest counterexample thinking.
- `a1henu/paper-reading-skill`: self-contained Chinese explainer pages with intuition-before-math, notation tables, concrete walkthroughs, and pedagogy critique.
