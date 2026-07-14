# Learning Site UX Principles

Use this reference before visual design, implementation, and final QA. The target is a guided reader that teaches the source, not a summary page with decorative interactions.

## Product Bar

The site must be clearer than a well-made teaching PPT because it has the original source, interactive evidence, and return paths in one place.

Every major screen should answer:

- What am I reading now?
- Where is the original source text?
- What does the Chinese reading/explanation correspond to?
- Which word, figure, table, or claim can I inspect?
- How do I return to the paragraph I came from?

Before the first detailed chapter, the reader also needs:

- a compact whole-paper overview
- an argument map showing how the claims and evidence connect
- the smallest prerequisite path needed for the next chapter
- clickable routes from overview/argument nodes into the exact source paragraphs and figures

## Design-System Brief

Before coding, write a mini `DESIGN.md` for the paper. Borrow the `awesome-design-md` habit of turning style into explicit tokens and rules, not vibes:

- visual direction and source-artifact motif
- typography scale for paper text, Chinese reading, notes, and controls
- color roles for terms, evidence, limitations, and review actions
- layout modes per chapter type
- component rules for reading blocks, side notes, figures, term panels, chapter reviews, and big-image views
- mobile behavior for every panel
- examples of what this paper's site should avoid

Do not copy a brand skin. Apple-like restraint, Claude-like warmth, pixel/game style, manga accents, report clarity, or lab-notebook density are directions only after they are translated into this paper's content and reading tasks.

## Reader Interactions

- Inline terms should open an adjacent side panel on desktop, not a centered modal that hides the paragraph. On mobile, use a bottom sheet or in-flow accordion with a clear close state.
- Mobile term explanations must preserve context: avoid bottom sheets taller than half the viewport unless the explanation is in-flow, and keep the triggering sentence visible.
- A term explanation must preserve context: highlight the trigger word, include a `回到原词/回到原文` path, and return focus to the trigger on close.
- Side notes are public teaching copy. They may say `本段核心`, `为什么重要`, `怎么看证据`, or `容易误解`; they must not contain internal process, audit, asset-generation prompts, asset-management notes, or production thinking.
- Chapter, question, language, term, and figure controls must never open empty shells. Each state needs real content, a return path, and a next learning action.
- A question or chapter-review mode cannot replace the paper. It must link back to the exact source paragraph or figure that taught the answer.
- Synchronized side notes must actually change with the active paragraph; a static note rail that looks synchronized is misleading.

## Visual And Figure Layout

- Complex source figures, tables, heatmaps, and generated explainer images need enough area to read labels. If the default card makes the image small, use image-on-top/text-below, a wide evidence module, or split the visual into smaller panels.
- "Zoom" must be real: the large view should render larger than the thumbnail, allow scrolling or panning when needed, and keep the interpretation text nearby.
- Treat source figures/tables as evidence modules: show the visual first when the conclusion depends on it, then explain how to read it.
- For chart/table screenshots, either crop to the relevant subfigure or redraw/annotate a data-first explainer. Do not force a huge composite image into a tiny side-by-side grid.
- Generated Image 2 visuals should use short Chinese labels and a few callouts. Long explanations belong in HTML beside the image.

## Public-Copy Hygiene

Forbidden in public UI, alt text, side notes, and aria labels:

- build words: `preflight`, `manifest`, `regression`, `prompt summary`, `image prompt`, `生成 prompt`, `generated asset`, `生成教学图资产`
- audience/process labels: `面向无专业背景大学生`, `reader level`, `本次测试`
- internal reviewer phrasing: `读后文时要一直追问`, `作者在哪里证明`, `哪些结论只是局部实验下成立`
- internal implementation labels: `source_id`, `source block`, `stacked-bilingual`, `parallel-bilingual`, `figure-led`, `interleaved-close-reading`
- placeholders: `待补`, `coming soon`, `undefined`, `null`

Rewrite them as reader-facing learning copy.

Also apply `public-copy-style.md`: remove repeated `不是……而是……`, empty transitions, inflated AI language, duplicate conclusions, and page copy that sounds like a generation brief.

Do not treat canonical source terms as forbidden just because they contain a sensitive word. For example, a paper about `prompt tuning` may show and translate that term. What is forbidden is production copy such as `image prompt`, `prompt summary`, `生成 prompt`, or visible instructions about how assets were generated.

## Ten-Round Acceptance Loop

When maintaining this skill or validating a new site, run at least ten checks:

1. Known-bad regression sample fails for the intended reasons.
2. Desktop first viewport shows title, chapter navigation, real source text, Chinese reading/explanation, and a learning affordance.
3. Mobile viewport has no hidden horizontal overflow.
4. Every chapter tab shows real source/translation/explanation content.
5. Every language mode preserves source anchors and does not create empty blocks.
6. Inline terms open without obscuring the active reading block.
7. Term close returns focus or scroll position to the trigger.
8. Every source figure/table is readable in default view or has a real large view.
9. Every chapter-review/question choice produces meaningful feedback and links back to evidence.
10. Mobile dynamic checks pass: term sheet overlap, side-note sync, and review return-to-evidence.
11. Side notes, alt text, labels, and drawer copy contain no production/internal language.
