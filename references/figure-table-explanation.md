# Figure, Table, Data, And Experiment Explanations

## Placement

Show each important source figure/table at the point where its claim is taught in PPT and HTML. In HTML this means near the paragraph; in PPT it means the relevant page or an immediately following evidence page. Do not place all figures at the end by default.

Image-series mode does not need to reproduce or screenshot the paper's figures/tables. It may generate a conceptual explanation of a central experiment or result, while internal evidence records preserve factual traceability.

Each figure/table needs a primary reading position. Galleries, drawers, or zoom views are secondary and do not count as coverage unless the figure/table also appears beside the relevant argument.

For large composite figures:

- keep one overview image if useful
- split into subfigures
- explain each subfigure beside or below it
- use callouts or numbered hotspots when the visual has multiple parts
- if splitting is not feasible, place the full image in a wide image-first module and put explanation below it
- provide a real large-view mode when labels, axes, or table cells are not readable in the default module

For tables:

- place the table on one side and the explanation on the other when space allows
- if the table becomes too small in side-by-side layout, put the table above and explanation below, or split rows/groups into separate cards
- explain rows, columns, metrics, and baselines before discussing conclusions
- highlight the cells that support the current claim
- state the exact comparison: "compared with X, Y is higher/lower by Z" when the source supports it
- avoid saying "提升" or "更好" without naming the baseline, metric, direction, and limitation
- when the page states a result claim, add or update `claim_evidence_map` so the exact table/figure cells and limitations can be audited

## Explanation template

For every figure/table, include:

- **它是什么**: what kind of evidence this is.
- **怎么看**: axes, rows, columns, legends, metrics, units, or components.
- **相比谁**: baseline, control group, previous method, ablation, or earlier condition.
- **结论是什么**: the exact claim supported.
- **为什么重要**: how it advances the paper's argument.
- **不能推出什么**: limitation or common over-reading.
- **回到原文**: which paragraph/claim it supports.

If a figure/table has multiple panels, repeat the template at panel level or provide hotspots that reveal panel-specific explanations. A single generic caption is not enough for a complex multi-panel figure.

The visible "回到原文" link, runtime figure metadata, and manifest `linked_source_ids` must point to the same source paragraph or claim cluster. A figure that returns to the wrong paragraph fails the learning loop.

## Experiments

Before results, explain:

- task setup
- input/output
- what is being measured
- why the metric matters
- what a higher/lower number means
- what the baseline represents

For ablations, explain what was removed or changed and why that reveals causality.

For training/evaluation papers, distinguish:

- simulation or data generation
- training data construction
- model training/fine-tuning
- evaluation task
- observed performance improvement

Readers often confuse "the simulated world improved" with "the model improved after training"; explicitly separate them when relevant.

For algorithm screenshots or formula pages, do not treat the screenshot as a normal figure. Add a line-level breakdown:

- original formula or pseudocode line
- symbol or variable meanings
- what changes after this line runs
- a tiny numeric or concrete example
- which later claim depends on this line

The breakdown must be visible in the final output, not only recorded in the manifest. Use a dedicated PPT item or a visible HTML formula module. Image-series mode includes a formula only when it is a selected core teaching target and the image model can render it correctly. For HTML, use an element such as `data-formula-breakdown="adam-update"` and record the same id in `formula_breakdowns[].formula_dom_id`.

## Claim Evidence Map

For result, cost, quality, latency, memory, or efficiency claims, add `claim_evidence_map[]` entries:

- `claim_role`: `source_claim_to_verify` when the paragraph states a paper claim that later evidence must verify, or `supported_conclusion` when the page presents it as supported.
- `claim_dom_id`: the visible claim block, image item, presentation page, or HTML paragraph.
- `source_ids`: source paragraphs containing the claim.
- `comparison_baseline`: what it is compared with.
- `metric_or_dimension`: score, cost, memory, latency, task quality, behavior, or qualitative dimension.
- `direction_or_value`: what changed and in which direction.
- `evidence_items[]`: each item needs `evidence_id`, `evidence_kind`, `dom_id`, and `supports_vs_illustrates`.
- `limitation`: what the evidence does not prove.

Generated teaching visuals should use `supports_vs_illustrates: illustrates`. They should not be the only proof for a `supported_conclusion`.

## Screenshots

Use source screenshots in PPT/HTML for figures, tables, UI captures, diagrams, and visual evidence. Do not screenshot long text blocks. Crop tightly enough that the reader can see the relevant evidence without opening a giant image. Do not insert source screenshots into final image-series pages.

If a screenshot contains multiple logical panels, crop each panel separately when the reader needs panel-level interpretation. A single giant screenshot plus one generic caption is not enough for a dense table or multi-panel figure.

## Redrawn Data Visuals

When using Image 2 or another illustration model to reinterpret a chart/table as a teaching visual for PPT/HTML, inherit the data semantics only:

- keep chart type, title, axis labels, units, ranges, tick labels, category order, values, and uncertainty/error bars
- discard cramped screenshot styling, arbitrary colors, shadows, and weak layout
- keep exact values in deterministic layout or source crops and in the manifest when values appear in the image/PPT/HTML
- reject attractive visuals with wrong values, swapped order, missing axes, or unreadable labels
