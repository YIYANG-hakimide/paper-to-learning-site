# Visual Deck Storytelling

## Product Model

Treat the deliverable as a visual lesson, not slides pasted from the paper and not a decorative summary. The learner should be able to read the deck alone without a presenter.

## Storyboard Gate

After source inventory and any user-requested style preview, write the entire storyboard before generating final visuals. Save it as `data/storyboard.json` and lock it only after the narrative arc passes review.

The storyboard must contain:

- `acts[]`: the major teaching movements
- `chapters[]`: coherent learner goals inside each act
- `slides[]`: every final slide in order
- per-slide question, answer, source ids, visual/evidence owner, misconception, transition, and layout family
- `narrative_checks`: prerequisite order, evidence-before-conclusion, training/inference/evaluation separation, and final reconstruction

For PPT, every page also records:

- `presentation_intent`: `reading-first`
- `communication_job`: what the reader should understand, believe, or be able to judge after this page
- `reasoning_role`: question, definition, mechanism, example, evidence, comparison, conclusion, boundary, or synthesis
- `standalone_takeaway`: the conclusion a reader should retain
- `reader_context`: the minimum context needed on the page
- `so_what`: why the page matters to the paper's argument
- `density_class`: low, medium, or evidence-dense
- `section_reset`: whether this page visibly opens a new chapter
- `scan_order`: the intended reading order

Avoid more than three consecutive evidence-dense pages without a reset, synthesis, or example.

The normal act structure is:

1. **进入问题**: what matters and why the existing situation is insufficient.
2. **补齐认知**: prerequisites and analogies needed for the method.
3. **拆开方法**: overview, components, causal sequence, and worked example.
4. **检查证据**: setup, baseline, metric, source figures/tables, and supported conclusions.
5. **形成判断**: limitations, boundaries, implications, and learner reconstruction.

Adapt act names and count to the paper, but preserve the learning functions. A deck that jumps from attractive concept images to result charts without these bridges fails.

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
- one source or evidence link when the slide makes a factual paper claim
- one bridge that makes the next slide feel necessary
- one owning act/chapter and one role in the overall arc
- 2-4 visible information groups, a recorded scan order, and a standalone reader takeaway
- enough definition, explanation, evidence, and implication to work without a presenter

Dominant teaching objects may be generated illustrations, source figures, tables, formula breakdowns, timelines, annotated screenshots, short quotations, or worked examples.

## Density

Default to reading-first density. Use page role rather than one universal word limit:

- overview/argument map: normally 250-450 Chinese characters across structured groups
- concept/mechanism page: normally 180-350 characters plus a substantial visual
- evidence/figure page: normally 250-600 characters plus a large readable source object
- conclusion/boundary page: normally 120-300 characters
- citations and footnotes: short, exact, and visibly secondary

Do not confuse breathing room with emptiness. A page with a sentence plus a few unlabeled boxes is under-taught even when it is technically legible. Use `visual-page-teaching-contract.md` to record and review teaching units.

If more explanation is needed, split the page. Never solve density by shrinking typography below comfortable reading size.

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
