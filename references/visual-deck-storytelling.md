# Visual Deck Storytelling

## Product Model

Treat the deliverable as a presentation report: designed for explaining the source to other people, while remaining readable after the talk. It is neither source pages pasted into slides nor a decorative summary.

## Storyboard Gate

After source inventory and any user-requested style preview, write the entire storyboard before generating final visuals. Save it as `data/storyboard.json` and lock it only after the narrative arc passes review.

The storyboard must contain:

- `acts[]`: the major teaching movements
- `chapters[]`: coherent learner goals inside each act
- `slides[]`: every final slide in order
- per-slide question, answer, source ids, visual/evidence owner, misconception, transition, and layout family
- `narrative_checks`: prerequisite order, evidence-before-conclusion, training/inference/evaluation separation, and final reconstruction

For PPT, every page also records:

- `presentation_intent`: `present-and-read`
- `communication_job`: what the reader should understand, believe, or be able to judge after this page
- `reasoning_role`: question, definition, mechanism, example, evidence, comparison, conclusion, boundary, or synthesis
- `standalone_takeaway`: the conclusion a reader should retain
- `reader_context`: the minimum context needed on the page
- `so_what`: why the page matters to the paper's argument
- `density_class`: low, medium, or evidence-dense
- `section_reset`: whether this page visibly opens a new chapter
- `scan_order`: the intended reading order
- `explanation_completeness`: whether the page contains the definition/context, reasoning, evidence/example, implication, and boundary needed for its role
- `information_group_count`: the number of distinct, visible teaching groups
- `visual_route`: `generated`, `image-to-image`, `deterministic`, `source-crop`, or a justified combination

Avoid more than three consecutive evidence-dense pages without a reset, synthesis, or example.

The normal act structure is:

1. **进入问题**: what matters and why the existing situation is insufficient.
2. **补齐认知**: prerequisites and analogies needed for the method.
3. **拆开方法**: overview, components, causal sequence, and worked example.
4. **检查证据**: setup, baseline, metric, source figures/tables, and supported conclusions.
5. **形成判断**: limitations, boundaries, implications, and learner reconstruction.

Adapt act names and count to the source. Books/articles may use idea progression, chapter turns, examples, tensions, and synthesis; manuals may use procedure and failure-mode arcs. Never invent experimental or methodological beats solely to fit the paper template. A deck that jumps from attractive concept images to evidence without reasoning bridges fails.

## Mandatory Opening Pages

Do not make the learner infer the paper's structure from a sequence of detail pages.

The opening must cover these jobs before detail:

1. What question the paper asks and its answer.
2. The paper overview: problem, contribution, method/evidence route, and final takeaway.
3. The argument map: how the paper moves from premise to evidence to conclusion.
4. The smallest prerequisite set required for the next section.

The first three jobs may occupy one, two, or three pages according to complexity. A generic agenda does not satisfy any of them.

Only a user-requested lightweight style preview may precede storyboard lock. Every later image must reference an existing storyboard item id.

## Recommended Arc

Use the paper's actual logic, but usually cover these learner questions:

1. 这篇论文到底想解决什么？
2. 为什么这个问题难？
3. 看懂后面前必须知道什么？
4. 以前的方法哪里不够？
5. 作者的关键想法是什么？
6. 整套方法如何运转？
7. 每个关键模块分别做什么？
8. 用一个具体例子跑一遍会发生什么？
9. 作者如何构造数据、世界、角色或实验条件？
10. 哪一步是训练，哪一步是推理、模拟或评估？
11. 实验究竟在比较什么？
12. 图表中的每个轴、行、列、行为或面板是什么意思？
13. 结论相比谁、提升什么、证据在哪里？
14. 哪些结论不能从现有证据推出？
15. 我能否用自己的话复述整篇论文？

Do not force all 15 beats into every paper. Use only the beats that clarify the source, but never omit prerequisites, method, evidence, and limitations.

## Slide Unit Contract

Each slide must have:

- one learner question as the title or clear framing
- a clear answer or judgment
- one dominant teaching object
- one source or evidence link when the slide makes a factual source claim
- one bridge that makes the next slide feel necessary
- one owning act/chapter and one role in the overall arc
- normally 3-7 visible information groups, a recorded scan order, and a standalone reader takeaway
- enough definition, explanation, evidence, and implication to work without a presenter

Dominant teaching objects may be generated illustrations, source figures, tables, formula breakdowns, timelines, annotated screenshots, short quotations, or worked examples.

## Density And Canvas Use

Default to consulting/research-report density, but do not use character quotas as a pass condition. Density is structural: conclusion + explanation chain + evidence/example + implication + boundary, rendered at readable sizes. Do not confuse breathing room with an unused lower half of the page. A page with a sentence plus a few unlabeled boxes is under-taught even when technically legible; copied paragraphs in tiny type fail for the opposite reason.

Split only when the page contains more than one major message or cannot remain legible. Never create extra sparse pages merely to keep every slide minimal, and never solve density by shrinking typography below comfortable reading size.

## Page-Level Visual Routing

Route every substantial visual object before asset production:

- `generated`: concept metaphor, mechanism, architecture, scene, abstract process, or worked example best taught by a capable image model
- `image-to-image`: a source/reference-guided explanatory reinterpretation when the original object needs simplification or consistent art direction; never present it as original evidence
- `deterministic`: exact chart, table, formula, quantitative diagram, timeline, or schematic whose labels/values must remain precise
- `source-crop`: original figure, experiment result, quotation, screenshot, or table that functions as evidence

Use combinations freely. There is no unified visual format: the page's teaching and evidence jobs decide the route.

Every non-trivial deck must contain real image-model output for the teaching objects that need it, and every storyboard item marked `generated` or `image-to-image` must be fulfilled. In Codex, use the installed system `imagegen` skill first. Simple SVG, generic cards, CSS/Canvas/Pillow drawings, and primitive shapes do not satisfy a planned generated visual. A transport retry is allowed; a model/provider downgrade or manual fallback requires user approval.

Use this routing table:

- quantitative data: native editable charts
- exact table or formula: deterministic editable layout
- simple sequence: native editable slide shapes
- complex relationship/network: Graphviz
- sketch-like causal explanation: Excalidraw
- abstract concept, scene, or high-aesthetic educational diagram: ImageGen
- original experimental evidence: tightly cropped, enlarged, or split source object

## Granularity Tests

Split a topic when any answer is yes:

- Does the slide explain more than one new prerequisite?
- Does the mechanism contain more than four meaningful steps?
- Are world construction, data generation, training, execution, and evaluation mixed together?
- Does the learner need to understand an overview before individual parts?
- Does the figure contain panels whose labels become unreadable?
- Does the conclusion contain multiple baselines or metrics?
- Would a concrete example materially reduce abstraction?

## Visual Need Test

Generate or use a visual when the learner needs to understand:

- spatial relationships
- sequence or causality
- multiple actors or components
- before/after state change
- hierarchy or architecture
- repeated cycles or feedback
- comparison across conditions
- a simulation, world, scene, or role interaction
- the meaning of a dense source chart/table
- an analogy that anchors an unfamiliar concept

Use prose when precision, caveat, quotation, or exact definition matters more than shape. The strongest page often combines a large visual with precise native text.

## Evidence Rhythm

Use this order for claims:

1. Explain what was tested.
2. Explain the baseline and metric.
3. Show the source figure/table clearly.
4. Guide the learner to the relevant cell, curve, panel, or behavior.
5. State the supported conclusion.
6. State the limitation.

Never use an Image 2 illustration as step 3. It may appear before step 1 to explain the setup or after step 6 to consolidate understanding.

## Batch Assembly

Produce the deck in small narrative batches, not as an image dump:

1. Generate 3-6 storyboard-owned visuals.
2. Place them into their final slides with HTML explanation and citations.
3. Render a contact sheet for the batch plus the preceding transition slide.
4. Check whether the questions, visual language, and evidence form a coherent sequence.
5. Repair continuity before proceeding.

At the end, render a full-deck contact sheet. A reviewer should be able to infer the story from titles and dominant visual objects alone. If the sequence looks like unrelated posters, revise the storyboard or transitions.

## Recap

Use a final reconstruction page or chapter recap:

- 问题是什么？
- 作者的关键做法是什么？
- 信息或数据如何流动？
- 作者拿什么和什么比较？
- 最重要的证据是什么？
- 仍然不能确定什么？

Avoid exam-like multiple-choice framing unless the user explicitly wants assessment.
