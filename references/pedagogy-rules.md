# Pedagogy Rules

## Default learner

Assume a college student who can read carefully but lacks professional background in the paper domain. Do not skip prerequisite knowledge.

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

For each paragraph or small paragraph group:

- show source text
- add translation when needed
- add a short "这段在推进什么" explanation
- add "所以呢" when the paragraph contains a claim, result, or methodological step
- add inline term triggers for concepts that would block understanding

Avoid a tiny Chinese summary after a large English passage. Long source passages need proportional explanation.

For dense paragraphs, unpack the paragraph's moving parts:

- what the sentence is trying to establish
- what variables, components, or actors are involved
- what step happens first, second, and next
- what conclusion follows
- what a novice might confuse

If a source paragraph is long or contains formulas, experimental claims, or several technical nouns, one generic Chinese sentence is not enough.

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

## Tone

Write like a good teaching assistant:

- specific, concrete, calm
- no generic "AI-powered" marketing copy
- no empty praise of the paper
- no unexplained jargon
- no decorative summaries that hide missing evidence
- no public-facing production notes such as "面向无专业背景大学生", "本次测试", "preflight", "manifest", "regression", "generated assets", or "reader level"
- describe what the chapter helps the reader understand, not what audience profile the generator was targeting
