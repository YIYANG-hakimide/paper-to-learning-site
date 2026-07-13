# Intake And Planning

## Required Intake

Ask unless already answered:

1. 是否有想重点探讨、重点解释、或者希望读者特别关注的内容？
2. 最终需要：`图片`、`PPT（PDF 演示稿）`、还是 `HTML 交互网页`？
3. 默认按“无专业背景大学生”的认知水平解释，可以吗？

For images or PPT, also ask:

4. 规模选择：`精简（6-10）`、`中等（11-20）`、`详细（21以上）`、还是 `自动判断`？

Use a compact structured intake. Do not ask the user to choose internal implementation details such as layout families, diagram types, extraction tools, or image providers.

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

The story must cover problem, prerequisites, method, worked example when useful, evidence, conclusion, limitations, and learner reconstruction.

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

Images additionally define aspect ratio, information density, contact-sheet rhythm, and image text strategy.

PPT additionally defines 16:9 stage, presentation pacing, section beats, focal scale, and transition behavior.

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
