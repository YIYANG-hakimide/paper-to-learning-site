# Novice Reader Research

Use these user-centered constraints when designing image series, presentation PDFs, or interactive readers. The target reader is not simply "low background"; they are trying to build reading strategies while also understanding the paper.

## Observed Pain Points

- Novice readers often lack formal training in how to read primary scientific literature; simply giving them a PDF does little to develop expert-like reading strategies. Source: Journal of Microbiology & Biology Education, "From Novice To Expert" (https://journals.asm.org/doi/10.1128/jmbe.00126-22).
- Expert readers reread, summarize, use prior knowledge, underline important information, and take notes much more than novices. Design should scaffold these behaviors rather than assume they happen naturally.
- Students can become frustrated when they cannot connect a paper to the bigger picture or when jargon blocks progress. Source: JMBE scaffolded module (https://journals.asm.org/doi/10.1128/jmbe.00177-22).
- Annotated primary literature helps by overlaying explanations on the original text, without rewriting the text away. Source: The Node / Science in the Classroom summary (https://thenode.biologists.com/introducing-introductory-biology-students-to-primary-scientific-literature-why-it-matters/education/).
- Figures are a major comprehension bottleneck. Treat figures and tables as evidence to be read, not decoration or appendix material.
- Novices often read linearly and accept the author's conclusion before inspecting methods or data. The site should slow them down at evidence points with "先看表怎么读" interactions.
- Novices also confuse layers: simulated environment versus generated dataset, data collection versus model training, training improvement versus evaluation improvement. Separate these layers visually and verbally.

## Design Responses

- Start each chapter with a problem map: what question is this section answering, what evidence will appear, and what the reader should know after.
- In PPT mode, keep exact source quotations, figures, tables, formulas, page references, and evidence cues visible at the points where claims are taught. In image mode, keep source traceability internal and use generated explanation rather than source screenshots. In complete HTML mode, keep paragraph-level original text visible and annotated. No mode may replace the paper with unsupported summaries.
- Attach definitions, examples, and "why this matters" to the exact sentence, term, figure, table cell, or equation where the reader needs them.
- Encourage expert-like reading behaviors: summarize the current paragraph, inspect the data before accepting the conclusion, compare claim versus evidence, and note uncertainty.
- Use progressive detail appropriate to the medium: separate images/pages for deeper explanation, and details-on-demand interactions in HTML.
- For experiments and tables, provide an evidence routine before the conclusion: setup, metric, baseline, comparison, result, limitation.
- Keep UI copy reader-facing. Say "先看作者要解决的问题" rather than "面向无专业背景大学生".
- Use chapter checkpoints as learning actions, not decorative summaries: "我能解释 X", "我能读懂 Table 2 的比较对象", "我知道这个图不能证明什么".

## Skill Implications

- The artifact is a learning scaffold first and a summary second.
- PPT must retain visible source evidence cues and page references. Image series retains source evidence internally. Complete HTML retains paragraph-level original text because annotations teach how to read the paper rather than replacing it.
- Every major figure/table should be introduced before its conclusion, so the reader learns to inspect evidence.
- Term explanations should appear at the point of confusion, not in a separate glossary route.
- Generated diagrams should externalize hidden structure: actors, steps, data flow, training loop, comparison baseline, and uncertainty.

## Learning Modes To Support

- **Guided image series**: high-information visual route that can be read as an ordered album.
- **Presentation PDF**: question-led, reading-first visual report with focal visuals, evidence, conclusions, and limitations that remain understandable without a presenter.
- **Close reading**: paragraph-level original/translation with inline terms and side notes.
- **Evidence mode**: figures/tables next to claims, with how-to-read guidance.
- **Review mode**: checkpoints, flashcard-like terms, and chapter summaries.

## Product Inspirations

- Readwise Reader treats highlighting and annotations as first-class reading objects and supports images, tables, rich text, PDFs, keyboard reading, term simplification, and search (https://readwise.io/read).
- Hypothesis emphasizes highlight/comment directly over source content, turning passive assignments into active reading (https://web.hypothes.is/).
- Zotero keeps annotation colors, note extraction, and "show on page" links back to the original PDF context (https://www.zotero.org/support/pdf_reader).
- Distill describes "details-on-demand" as a way to reduce cognitive load while keeping a high-level overview visible (https://distill.pub/2020/communicating-with-interactive-articles/).
- Observable notebooks show how text, code, visual output, and inputs can live in one shareable document for interactive understanding (https://observablehq.com/documentation/notebooks/).
