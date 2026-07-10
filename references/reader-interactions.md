# Reader Interactions

## Base frame

Start from "章节地图 + 旁注 + 图表抽屉 + 术语弹窗", then adapt to the paper.

Recommended layout:

- top chapter map with visual landmarks
- main reading panel with source/translation/explanation blocks; layout can be parallel, stacked, interleaved, figure-led, or facsimile-plus-HTML depending on the section
- side learning panel that changes with the active paragraph
- figure/table drawer for close reading
- term popovers opened from underlined inline terms inside the original paragraph, translation, or explanation
- language mode segmented control for non-Chinese sources

## Interaction rules

- Every popover, drawer, bubble, and floating panel must have an obvious close state.
- Term explanations should not hide the active paragraph. On desktop, prefer a right/side panel, adjacent annotation rail, or anchored panel that does not overlap the current `.reading-block`; on mobile, use a bottom sheet or in-flow accordion.
- Mobile term explanations should not cover most of the paragraph the reader clicked from. Prefer an in-flow accordion; if using a bottom sheet, keep it below half the viewport and scroll the trigger sentence above the sheet.
- If a modal or drawer is unavoidable, it must include `回到原词/回到原文`, close on Escape, and return focus to the clicked term.
- Clicking "continue" should move to the next chapter/landmark, not repeat the current content.
- If chapter switching is primary, avoid making the user scroll through unrelated repeated sections.
- Keep terminology and figures close to the paragraph where they matter.
- Terms must be anchored to the exact words they explain. Do not rely on detached tag strips or glossary chips as the only interaction.
- Each paragraph should have a stable anchor so side notes, figure drawers, and popovers can point back to the source sentence.
- Each reading block should expose a stable `data-source-id` that matches the manifest.
- Side panels should track the active paragraph and expose "回到原文" or equivalent anchors for notes, figures, and claims.
- Side-note tracking must be visibly real. Clicking or focusing a different reading block should update the note title/body and return link.
- Side notes should be written as public learning notes: `本段核心`, `为什么重要`, `怎么看证据`, `容易误解`. Do not expose internal process, audit, asset-generation prompts, target-reader, or reviewer-planning language.
- Use semantic highlight colors consistently, for example: method terms, evidence, limitations, and definitions should not share arbitrary colors.
- Let users expand deeper explanations without forcing every detail into the main line.
- Preserve reading flow: the main text should still make sense if all drawers are closed.
- Do not make the reader open an appendix or raw extraction panel to access the paper's real text.
- Do not make a chapter map that only jumps to repeated summaries. Chapter switching should reveal that chapter's original/translation/explanation blocks.
- For layout-sensitive original text, let the reader toggle between `排版截图` and `可选文字`, but keep both tied to the same `data-source-id`.
- Add review actions when useful: "本章核心要点回顾", "用自己的话解释", "看概念图", or "回到证据".
- Chapter recap should include a structured "用自己的话复述" path: problem, method, comparison, evidence, and limitation. It may also include choice buttons, but it should not stop there.
- A knowledge map, chapter-review card, or Feynman card must link back to the paragraph/figure that taught the concept; otherwise it becomes disconnected decoration.
- Review feedback should name exactly what to inspect next: table column, figure panel/curve, formula term, metric, baseline, or prompt block. Avoid generic feedback that only says "回到本章关键段落" or "检查表格、公式或机制".
- Language mode must be a real stateful interaction. It should update visible layers without losing the active chapter, active paragraph, synchronized side note, or open drawer context.
- Do not leave `href="#"`, unlabeled icon controls, repeated "查看详情", or placeholder buttons in the final page.
- Do not leave chapter tabs, question tabs, language modes, review choices, or figure buttons that open a title-only or empty panel. If a control exists, test every state.
- For static HTML, use the bundled `assets/reader-runtime.js` or match its DOM contract. Do not bind chapter navigation with `querySelectorAll('[data-chapter]')`, because reading blocks may also carry `data-chapter`; use `button[data-chapter], a[data-chapter], [role="tab"][data-chapter]`.

## Interaction inventory

Before final delivery, record and test each meaningful interaction:

- trigger: exact button/link/inline term/table cell
- state change: what becomes visible, hidden, active, or selected
- close method: close button, Escape, outside click, back action, or return link
- source linkage: `source_id`, `figure_id`, `claim_id`, or chapter id
- feedback: chapter-review answer, visualizer state, active tab, or highlighted evidence
- focus/return path: after close, the user should be back at the term, figure, table, or paragraph that launched the interaction
- evidence return: chapter-review feedback should include a visible link or button that returns to the source paragraph/table supporting the point
- traceability: term trigger paragraph, runtime term source, manifest `term_anchors`, visible figure return links, runtime figure source, and manifest `linked_source_ids` should agree

Delete interactions that cannot pass this inventory. A static card is better than a fake button.

## Visual design

Choose a style from the paper's subject and artifacts. Examples:

- pixel/game-like for virtual worlds, agents, simulation, or playful AI papers
- editorial/Apple-like for reflective essays or product-like papers
- manga/anime accents when the topic or user asks for it
- consulting-report clarity for business or experiment-heavy reports
- lab-notebook clarity for method-heavy scientific papers
- product-reader clarity for study apps, textbooks, or learning tools

Avoid:

- generic AI gradients, glowing blobs, and empty dashboards
- cards inside cards
- end-loaded figure galleries disconnected from the argument
- text baked into screenshots when it should be selectable HTML
- detached "related terms" rows that force the reader to guess which sentence the term belongs to
- a term popover triggered only from a glossary chip when the term appears unclickable in the paragraph
- visible internal workflow labels such as manifest, preflight, regression, generated asset, reader level, or target audience notes
- modal term explanations that cover the exact paragraph the user was reading
- question or chapter-review tabs that have no source paragraph, evidence, or feedback for choices 3/4/5/6

## Responsive and accessibility checks

- Text must not overlap on mobile or desktop.
- Buttons need visible labels or accessible names.
- Figures need useful alt text.
- Long terms or bilingual labels must wrap cleanly.
- Side panels become bottom sheets or full-width accordions on mobile.
- Keyboard users should be able to reach chapter tabs, term triggers, and drawer close buttons.
