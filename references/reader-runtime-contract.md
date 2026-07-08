# Reader Runtime Contract

Use this when implementing the static HTML reader. Prefer copying `assets/reader-runtime.js` into the output site or inlining it after the page data. It exists to prevent common failures: empty chapter tabs, broken language modes, term popovers covering the reading paragraph, figure drawers that are not actually larger, and repeated chapter-review feedback.

## Runtime data

Define these before loading the runtime:

```html
<script>
window.LEARNING_SITE_TERMS = {
  "self-attention": {
    title: "Self-attention / 自注意力",
    field: "术语本义：同一序列内部的位置互相查看并加权汇总信息。",
    plain: "说人话：一句话里的每个词都能直接看句中其他词。",
    paper: "本文指代：Transformer 用它替代 RNN/CNN 的核心序列计算。",
    use: "作者怎么用：encoder 和 decoder 都使用 self-attention，decoder 还加 mask。",
    misread: "常见误解：attention 权重能辅助解释，但不等于严格因果证明。",
    source_id: "sec3-p04"
  }
};
window.LEARNING_SITE_FIGURES = {
  "table-2": {
    title: "Table 2: 翻译质量与训练成本",
    path: "assets/figures/table-2.png",
    alt: "Table 2 BLEU scores and training costs",
    note: "它是什么：... 怎么看：... 相比谁：... 结论是什么：... 不能推出什么：...",
    source_id: "res-01"
  }
};
window.LEARNING_SITE_REVIEW_FEEDBACK = {
  "chapter-3": {
    "baseline": "核心回顾：这章要回到 Table 2，看 Transformer big 与 ConvS2S 的 BLEU 和训练 FLOPs。",
    "summary-only": "再补一步：先说明比较对象、指标方向和限制，再说结论。"
  }
};
</script>
```

Each review choice may also use `data-feedback` and `data-source-id`. Do not rely on generic fallback feedback. Legacy `window.LEARNING_SITE_QUIZ_FEEDBACK`, `data-quiz`, and `data-quiz-choice` are still accepted for old sites, but new sites should use review/recap naming.

## DOM contract

Use these selectors:

- chapter controls: `button[data-chapter]`, `a[data-chapter]`, or `[role="tab"][data-chapter]`
- chapter panels: `[data-chapter-panel="chapter-id"]`
- language controls: `button[data-mode]`, `a[data-mode]`, or `[role="tab"][data-mode]`
- reading blocks: `.reading-block[data-source-id]`
- source layers: `.source-text`, `.translation-text`, `.plain-text`
- inline terms: `.term[data-term]` or `[data-term-id]`, placed inside source/translation/explanation text
- source figures/tables: `.source-figure[data-figure-id]` with a local `img`
- figure triggers: `[data-figure]` or `[data-figure-id]`
- chapter recap/review cards: `[data-review]` or `.review-card`, with choices using `[data-review-choice]`
- close buttons: `[data-close]`, `[data-close-panel]`, or `.close-drawer`

Do not bind chapter switching to all `[data-chapter]` elements. Reading blocks often carry `data-chapter` for coverage, but they are not navigation controls.

## Required panels

Term panel should be a side rail on desktop and a bottom sheet or in-flow panel on mobile:

```html
<aside id="term-panel" class="term-side-panel" aria-hidden="true" hidden>
  <button type="button" data-close aria-label="关闭术语解释">关闭</button>
  <h2 data-term-title></h2>
  <p><strong>术语本义</strong><span data-term-field></span></p>
  <p><strong>说人话</strong><span data-term-plain></span></p>
  <p><strong>本文指代</strong><span data-term-paper></span></p>
  <p><strong>作者怎么用</strong><span data-term-use></span></p>
  <p><strong>常见误解</strong><span data-term-misread></span></p>
  <a data-term-back href="#">回到原词</a>
</aside>
```

Figure panel must show a genuinely larger image than the inline thumbnail and keep interpretation nearby:

```html
<aside id="figure-panel" class="figure-panel" aria-hidden="true" hidden>
  <button type="button" data-close aria-label="关闭图表解读">关闭</button>
  <h2 data-figure-title></h2>
  <img data-figure-img alt="">
  <p data-figure-note></p>
  <a data-figure-back href="#">回到原文</a>
</aside>
```

Side note synchronization should use stable selectors. Each `.reading-block` should provide `data-note-title` and `data-note`, or an in-block `[data-note-title]` plus `[data-note-text]`. The side rail should expose `[data-side-note-title]`, `[data-side-note-text]`, and `[data-side-note-link]`:

```html
<aside id="side-note" data-side-note>
  <h2>本段核心</h2>
  <p data-side-note-title></p>
  <p data-side-note-text></p>
  <a data-side-note-link href="#">回到原文</a>
</aside>
```

Clicking or focusing a different reading block must visibly update this note. Do not render a static-looking synchronized side note.

## Safe state rules

- Use `panel.setAttribute("data-active", "true")` for the active chapter and `panel.removeAttribute("data-active")` for inactive panels.
- Never use `toggleAttribute("data-active", true)` with CSS like `[data-active="true"]`; it creates `data-active=""`, so the active panel becomes invisible.
- Pair `[data-active="true"]` with `hidden` for inactive panels:

```css
.chapter-panel[hidden] { display: none; }
.chapter-panel[data-active="true"] { display: block; }
```

- Language mode should update `body[data-mode]` while keeping the active paragraph and side note.
- Close/Escape must set `aria-expanded="false"` on the trigger and return focus to the source word, figure, or review control.
- Term panels should not be centered modals on desktop. If a drawer is unavoidable, it must not cover more than a small part of the active reading block.
- On mobile, prefer in-flow accordions or bottom sheets below half the viewport. Opening a term should keep the triggering sentence visible above the explanation.
- Chapter recap/review feedback should append a visible `回到原文证据` link to the supporting reading block.

## Layout defaults

- Desktop: use a reader grid with navigation, main source text, and side learning rail. Keep the main source text at a stable readable width.
- Mobile: one column in this order: source, Chinese reading, plain explanation, local figure/term controls, optional deeper panels.
- Dense figures/tables: default to image-on-top/text-below or wide evidence modules. Use side-by-side only when labels remain readable.
- Generated Image 2 diagrams: place near the concept they teach, not in an asset gallery.

## Audit-friendly checklist

Before strict audit, manually test:

1. Click every chapter control and confirm real reading blocks appear.
2. Toggle every language mode and confirm source/chinese layers remain paired.
3. Click at least five terms, close them, and confirm focus or scroll returns.
4. Open every figure/table large view; the large view must be meaningfully larger than the inline image.
5. Click every chapter-review choice; feedback must mention chapter-specific evidence or source ids.
6. On mobile, open terms and confirm the explanation does not cover most of the active paragraph.
7. Focus two different reading blocks and confirm the side note changes.
8. Search visible UI for internal words: `preflight`, `manifest`, `regression`, `source_id`, `stacked-bilingual`, `generated assets`, `面向无专业背景大学生`.
