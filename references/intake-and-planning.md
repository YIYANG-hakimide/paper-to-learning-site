# Intake And Planning

## Required intake questions

Ask before implementation unless the user already answered or explicitly asked to proceed with defaults:

1. 是否有想重点探讨、重点解释、或者希望读者特别关注的内容？
2. 需要本地 HTML、PNG/PDF 图集，还是还要部署到 Vercel？
3. 默认按“无专业背景大学生”的认知水平解释，可以吗？

If the user is impatient or says "直接做", use defaults and state them briefly before starting.

## Source inventory

Create a working inventory before designing:

- source files and URLs
- document title and best short title
- source language
- sections/chapters
- paragraph count per section
- all figures, tables, charts, equations, screenshots, appendices
- key terms and prerequisites
- claims and evidence
- reader pain points likely to block comprehension
- available tools from preflight: extraction, figure rendering, Image 2/image generation, browser QA, deployment

## Teaching Deck Outline

Before designing, convert the paper into learner questions. For every planned slide, record:

- learner question
- one-sentence answer
- prerequisite dependency
- source ids and page numbers
- visual teaching job
- generated illustration or source evidence
- misconception to prevent
- next-slide bridge

Default to a reading-first 18-36 slide deck. Use more slides when the paper has multiple prerequisites, a long method pipeline, composite figures, or several experimental claims.

## Paper-Specific Design Brief

Before implementation, write a design brief with concrete rules, not mood words:

- paper personality and reader emotion
- source artifact motif: figures, equations, screenshots, tables, architecture diagrams, or visual scenes
- typography roles for original text, Chinese reading, plain explanation, notes, captions, controls, formulas/code
- color semantics for terms, evidence, limitations, definitions, and active state
- spacing rhythm, source-text line width, and reading density
- component rules for title, concept, method, worked-example, evidence, formula, comparison, recap, and source slides
- fixed-stage behavior: 1920x1080 composition, viewport scaling, navigation, overview, fullscreen, and reduced motion
- figure/table strategy: large view, split panels, image-top/text-bottom, or redraw/annotation approach
- what this paper-specific site should avoid, such as generic AI gradients, dashboard grids, tiny figures, or decorative images

This is inspired by design-system `DESIGN.md` files: colors, typography, components, and states should be explicit enough that another agent can implement them.

## Completeness Rule

The deck must not be built from only the abstract or selected convenient snippets. Inventory the whole main paper, then ensure every central claim, method component, important figure/table, and limitation is represented in the learning path.

For default deck mode:

- main slides explain and visualize the paper's logic
- evidence slides preserve important original quotations, figures, tables, formulas, and page references
- each important claim links to exact source ids
- longer original text may live in evidence slides or the optional full reader

For optional complete-reader mode, every included main-section paragraph still needs:

- original paragraph or faithful source text
- translation if the source is not Chinese
- plain-language explanation
- links to terms, figures, equations, or notes when relevant

For very long papers, deliver in stages only after telling the user exactly what is included in the current version and what is deferred. Main text comes before appendix deep dives unless the user asks otherwise.

Do not satisfy "complete paper text" by hiding raw extraction inside a collapsed `<pre>` block. The main reader must expose paragraph-level source text paired with translation/explanation. Collapsed raw source can be a secondary appendix only.

## Architecture Decision

Default to a fixed-stage visual teaching deck:

- one learner question per slide
- generated teaching images as large primary objects
- source evidence slides for tables, figures, formulas, and quotations
- chapter/logic-unit divider and recap slides
- overview and direct navigation
- optional evidence panel or linked complete reader

Build a chapter-switching reader only when the user explicitly asks for extensive in-page source reading:

- top or side chapter map
- right/main reading pane with original/translation/explanation
- left or side learning pane for synchronized notes, terms, figures, and chapter logic
- drawers or popovers for deep explanations
- visible language mode controls for non-Chinese sources

Adapt when the source suggests a better form:

- experimental paper: evidence trail and figure-led reading
- systems paper: architecture map plus step-by-step walkthrough
- theory paper: concept ladder plus proof/argument map
- survey/report: topic atlas plus comparison tables
- narrative essay: scene/argument timeline plus close reading notes

## Naming

Use `Learn <paper short title>` for the deck title, package folder, and Vercel project name unless the user provides a name.
