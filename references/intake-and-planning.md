# Intake And Planning

## Required Intake

Ask every unresolved item once in one compact message. Output mode has no default unless the request already implies it. After mode selection, the user may answer `其余全部默认`.

1. 输出：`图片`、`PPT（默认 PDF）`、或 `HTML`。
2. 重点关注的问题。
3. 是否接受“无专业背景大学生”的默认认知水平。
4. 图片/PPT 的规模：精简、中等、详细、自动。
5. 是否有风格描述或参考图；没有则自动决定。
6. 是否要先看内容策划；是否要先生成一张样图。两项默认关闭。
7. PPT 是否需要 `.pptx`；HTML 是否需要部署。两项默认关闭。

Defaults: no special focus, non-specialist college reader, automatic size, paper-derived visual direction, no planning preview, no sample, PDF-only PPT, local-only HTML. Do not ask about layout families, diagram taxonomies, providers, extraction tools, or other internal implementation details. Do not create a second approval step when the user chose the fast/default path.

For HTML, default to `complete` source coverage. If the source is unusually long or the user asks for a quick guide, ask whether `curated` is acceptable before omitting main-text blocks.

## Source Inventory

Inventory before designing:

- source title, language, file hash, page count, sections, and main-text blocks
- all important figures, tables, charts, equations, algorithms, screenshots, and appendices
- prerequisite concepts and terminology dependencies
- method stages, actors, data flow, training/inference/evaluation layers
- claims, baselines, metrics, evidence, and limitations
- likely novice misconceptions
- available extraction, rendering, image generation, OCR, browser, PDF export, and deployment routes

## Scope Plan

Record:

- selected `output_mode`: `image-series`, `presentation-pdf`, or `interactive-html`
- selected `size_mode`: `concise`, `medium`, `detailed`, or `automatic`; omit fixed count for HTML
- target and maximum item count
- included focus areas
- intentionally omitted secondary scope
- source coverage and evidence coverage expectations

## Storyboard

Convert the paper into learner questions before final generation. Each image/page/chapter needs:

- learner question and one-sentence answer
- act/chapter and learning role
- prerequisite dependency
- source ids and page numbers
- visual teaching job or evidence object
- misconception to prevent
- previous/next bridge
- layout/composition family

The story must establish the whole-paper question and argument route before detail. Include prerequisites, methods, experiments, evidence, conclusions, boundaries, and reconstruction only where the source and selected mode need them.

For image series, mark two required early items:

- `fixed-context`: the paper's question, thesis, and argument route
- `fixed-core-contribution`: the paper's main contribution, mechanism, or finding

All other items are dynamic. Related teaching needs may share one image when they form one coherent learner question and remain readable.

## Mode-Specific Design Brief

Write concrete design rules derived from the paper:

- paper personality, era, emotional tone, and recognizable objects
- visual thesis and source basis
- typography, palette, texture/material, illustration language, and evidence style
- semantic colors for definition, process, evidence, comparison, and limitation
- composition families and repetition limits
- source figure/table/formula strategy
- public-copy tone and reader level
- specific styles to avoid

Images additionally define aspect ratio strategy, album rhythm, native in-model Chinese text strategy, direct-output provenance, and forbidden post-composition operations.

PPT additionally defines a 16:9 self-reading report stage, conclusion-led titles, evidence density, section logic, generated-visual ownership, and source-figure explanation strategy.

HTML additionally defines source-text hierarchy, bilingual layout, navigation, interactions, mobile behavior, and deployment target.

Mood words such as “clean”, “Apple-like”, “anime”, “ancient”, or “professional” are not enough without typography, composition, evidence, and topic-specific rules.

## Completeness

All modes must inventory the whole main paper, even when the selected output is concise.

- Concise images/PPT may curate secondary material but must preserve central method, strongest evidence, and limitation.
- Medium/detailed outputs must expand prerequisite, method, experiments, and figure explanations proportionally.
- HTML must state whether it is a complete or curated reader. Complete mode requires paragraph-level source coverage.
- Never hide missing understanding behind a decorative image or generic summary.

## Naming

Use `Learn <paper short title>` for title and package naming unless the user provides another name. Add mode suffixes only when multiple outputs are requested later, such as `-images`, `-presentation`, or `-site`.
