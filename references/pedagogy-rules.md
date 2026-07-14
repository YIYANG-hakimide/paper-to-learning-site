# Pedagogy Rules

## Default learner

Assume a college student who can read carefully but lacks professional background in the paper domain. Do not skip prerequisite knowledge.

“College level” means the reader can follow a careful argument, basic quantitative comparison, and ordinary abstraction. It does not mean they already know the field's jargon, standard model architectures, training procedures, statistical conventions, or how to read academic figures.

## Explanation ladder

For each hard concept, write in this order:

1. **术语本义**: what the term generally means in the field.
2. **说人话**: a concrete analogy or everyday explanation.
3. **本文指代**: what exactly it means in this paper.
4. **作者怎么用**: where it appears in the method, experiment, or argument.
5. **常见误解**: what readers might wrongly infer.

Never explain only "what the paper says" when the reader first needs the concept itself.

For foundational terms such as supervised fine-tuning, rejection sampling, attention, ablation, BLEU, p-value, likelihood, encoder, or simulation, assume the reader has never learned the term. Start with the field meaning before the paper-specific meaning.

## Paragraph treatment

This section is mandatory for interactive HTML and becomes source-grounding guidance for image/PPT modes.

For each paragraph or small paragraph group:

- show source text
- for every non-Chinese source paragraph, add a faithful Chinese translation
- add a separate plain-language explanation; translation cannot replace explanation
- add a short "这段在推进什么" explanation
- add "所以呢" when the paragraph contains a claim, result, or methodological step
- add inline term triggers for concepts that would block understanding
- write a paragraph-specific side note or marginal note; do not reuse a generic "this paragraph advances the chapter" sentence

Avoid a tiny Chinese summary after a large English passage. Long source passages need proportional explanation.

For dense paragraphs, unpack the paragraph's moving parts:

- what the sentence is trying to establish
- what variables, components, or actors are involved
- what step happens first, second, and next
- what conclusion follows
- what a novice might confuse

If a source paragraph is long or contains formulas, experimental claims, or several technical nouns, one generic Chinese sentence is not enough.

## Mode Adaptation

### Image Series

- Teach prerequisites before paper-specific usage.
- Use one main question and 2-4 supporting visual groups per image.
- Include enough Chinese explanation for the image to stand alone; do not rely on a separate caption file.
- Use concrete examples and visual analogies, then state where the analogy stops being accurate.
- Keep claims internally linked to source evidence; do not force citations or source crops into the generated image.

### Presentation PDF

- Keep the visible page dense enough to read independently while preserving hierarchy.
- Put one clear reader-facing conclusion or answer on each page.
- Use a worked example before abstract evidence when it materially helps novices.
- Move nuance into a second page rather than shrinking copy.
- The PDF should read like a designed visual consulting report, not a paper document pasted into slides.

### Interactive HTML

- Preserve paragraph-level original/translation/explanation in complete-reader mode.
- Keep definitions, figures, formulas, and notes attached to the exact reading position.
- Allow details on demand without obscuring the source context.

## Inline terms

Term triggers must be embedded on the exact word or phrase inside the original paragraph, Chinese translation, or plain-language explanation. A separate "相关术语" strip is not enough, because it breaks the reader's ability to connect the concept to the sentence.

Use this pattern:

```html
The model uses <button class="term" data-term="self-attention">self-attention</button> to compare positions.
```

Do not use this as the only term entry point:

```html
<div class="term-strip"><button class="term">Self-attention</button></div>
```

If the source term is English and the site is Chinese-bilingual, the trigger can show both when space allows: `自注意力 / self-attention`. The popover should still include the full explanation ladder.

## Chapter logic

Each chapter needs:

- one sentence purpose
- 3-5 step logic chain
- key terms
- key figure/table links
- "读完你应该知道" checkpoint
- next-chapter bridge: why the paper moves from this section to the next

Use game-like or map-like interaction only when it helps orientation. Do not let decoration replace explanation.

## Evidence and claims

For each important conclusion, answer:

- Compared with what?
- Based on which table/figure/experiment?
- What changed?
- How large or meaningful is the change?
- What can we conclude?
- What can we not conclude?

When a conclusion uses words like "improves", "better", "training", "simulation", or "learned", name the object precisely. Explain whether the paper means a model's score improved, an agent's behavior changed, a simulated world produced data, a training dataset was constructed, or a human-facing evaluation changed.

For every important claim, preserve the exact teaching chain:

- claim: what the paper says
- comparison: compared with what baseline or condition
- metric/dimension: score, cost, latency, memory, behavior, human rating, or qualitative observation
- evidence: figure/table/paragraph id and what the reader should inspect
- limitation: what this evidence does not prove

Record this in the manifest as `claim_evidence_map` so future reviewers can audit the page instead of trusting the prose.

## Chapter recap

Chapter recaps should help the reader produce understanding, not just click the right answer.

Add a short Feynman-style scaffold such as:

- 问题是什么？
- 方法怎么做？
- 相比谁？
- 证据是什么？
- 不能推出什么？

Choice buttons are allowed, but they do not replace this scaffold.

## Tone

Write like a good teaching assistant:

- specific, concrete, calm
- no generic "AI-powered" marketing copy
- no empty praise of the paper
- no unexplained jargon
- no decorative summaries that hide missing evidence
- no public-facing production notes such as "面向无专业背景大学生", "本次测试", "preflight", "manifest", "regression", "generated assets", or "reader level"
- describe what the chapter helps the reader understand, not what audience profile the generator was targeting
