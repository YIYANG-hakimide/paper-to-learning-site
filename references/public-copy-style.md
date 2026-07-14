# Public Copy Style

Apply this check to image OCR text, PPT visible text, HTML copy, alt text, titles, labels, notes, and controls.

## Voice

Write like a strong teacher, an evidence-minded consultant, and a careful science editor. Use concrete nouns, explicit relationships, and paper-specific language. Explain what happens, why it happens, what the evidence shows, and where the boundary lies.

Use Chinese as the main language for Chinese readers. Keep canonical English terms only when they help recognition, normally on first use.

## Never Publish Internal Process

Do not expose:

- target-reader notes such as `面向无专业背景大学生`
- prompts, model names, generation steps, asset labels, storyboard language, QA notes, source ids, manifest fields, or reviewer instructions
- phrases such as `本页旨在让用户理解`, `这里需要告诉读者`, `生成教学图`, `测试页`, `回归样本`, or `验收时检查`

Convert internal intent into direct teaching copy. For example, replace `这里需要让用户理解拒绝采样` with `拒绝采样：先生成多个候选，再按规则留下更合适的结果`.

## Anti-Template Rules

Rewrite when any pattern dominates:

- repeated `不是……而是……`, `不仅……更……`, or `从……到……` framing
- empty transitions such as `接下来我们深入探索`, `值得注意的是`, `不难发现`, or `由此可见`
- inflated words such as `赋能`, `颠覆`, `全新范式`, `革命性`, or `重塑` without source evidence
- repeated conclusions that restate the title without adding mechanism or evidence
- identical title syntax, paragraph rhythm, or card labels on most pages
- vague claims such as `效果更好`, `能力提升`, or `表现优秀` without baseline, metric, direction, and evidence

Do not ban a phrase mechanically when the source quotation requires it. Flag repeated or unnecessary use and rewrite in context.

## Delivery Check

Before delivery, inspect public copy in context and confirm:

1. Every sentence is useful to the learner, not to the production team.
2. Technical terms are defined before they carry argumentative weight.
3. Claims name the compared object and evidence when relevant.
4. Page titles state a question, conclusion, or concrete topic.
5. Adjacent pages do not repeat the same summary in different words.
6. Generated-image OCR contains no garbled text or production residue.
