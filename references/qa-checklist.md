# QA Checklist

## Three review passes

Use subagents only when the user explicitly requested delegated/subagent review and the current tool policy allows it. Otherwise perform independent manual passes and write down findings before fixing.

1. **Design and interaction**
   - Is the page attractive and specific to this paper?
   - Does the first viewport clearly look like a learning reader, not a generated note?
   - Has the agent chosen a section-specific source layout strategy instead of forcing every chapter into the same left-right grid?
   - Do prose, method, formula, experiment, and review sections use visibly different rhythms when the content calls for it?
   - Is the original paper text typeset with readable line length, spacing, and paragraph hierarchy, whether it is side-by-side, stacked, interleaved, figure-led, or facsimile-plus-HTML?
   - In the first desktop viewport, can a reviewer see the paper title, language mode, chapter navigation, a real source paragraph, Chinese reading/explanation, and a side note or inline learning affordance?
   - Does the public UI avoid production/audience/process labels such as `面向无专业背景大学生`, `preflight`, `manifest`, `regression`, `生成教学图资产`, or `generated assets`?
   - Do side notes avoid internal reviewer copy such as `读后文时要一直追问`, `作者在哪里证明`, and `哪些结论只是局部实验下成立`?
   - Are side notes specific to the active paragraph, without repeating generic template copy across many blocks?
   - Is there a visible language mode for non-Chinese sources?
   - Does it avoid generic AI/dashboard aesthetics?
   - Does it avoid plain gray/white three-column documentation styling unless the topic explicitly calls for it?
   - Are chapter switching, drawers, term popovers, and close states obvious?
   - Do language controls, term triggers, drawers, and figure panels actually change state, rather than appearing as decorative buttons?
   - If the static reader uses chapter panels, does the implementation use explicit `data-active="true"`/remove state or the bundled `reader-runtime.js`, rather than brittle `toggleAttribute("data-active")` logic?
   - Do interaction labels tell the learner what they will get, for example `解释 Table 2 的提升` or `拆开这个公式`, instead of vague buttons like `查看详情`?
   - Are term triggers underlined or otherwise discoverable inside the original sentence, translation, or explanation, not only in a detached term/tag strip?
   - Do term explanations open beside the active paragraph on desktop, or in a bottom sheet/in-flow accordion on mobile, without hiding the paragraph the reader clicked from?
   - On mobile, does the term explanation preserve context instead of covering most of the active paragraph?
   - Does closing a term explanation return focus or scroll context to the clicked word?
   - Does the side note visibly update when the active paragraph changes?
   - Do interactive controls expose state with `aria-expanded`, `aria-controls`, `aria-current`, or equivalent accessible semantics?
   - Do repeated action buttons name the learning action, figure/table, or chapter instead of generic labels like `打开图表抽屉`?
   - Is there no text overlap on mobile and desktop?
   - Is there no horizontal clipping on mobile, especially inside figure/table explanation rows and bilingual paragraph blocks?
   - Does the reader avoid repeated dead-end navigation?

2. **Teaching comprehension**
   - Can a non-specialist college student understand the problem, method, evidence, and conclusion?
   - Does the opening overview and argument map explain the whole paper before detailed reading?
   - Can each argument-map node jump to the corresponding source paragraph, figure, or evidence module?
   - Does each chapter start with a learner-facing question/evidence map, not a production brief?
   - Are hard terms explained from general definition to paper-specific use?
   - Are terms introduced at the first point where they block comprehension, not later in a separate glossary?
   - Are explanations proportional to source difficulty, so long or dense English passages get more than one generic sentence?
   - Are chapter logic summaries and checkpoints useful?
   - Does each chapter recap include a Feynman-style "用自己的话复述" scaffold, not only multiple-choice buttons?
   - Does chapter recap feedback name concrete evidence such as a table column, figure curve, formula, metric, or prompt block, instead of generic "回到本章关键段落" copy?
   - Are diagrams used where text alone would be dry or abstract?
   - Does each generated diagram have a local teaching job: mechanism, comparison, example, timeline, evidence map, misconception, or "what happens next" bridge?
   - Are generated diagrams and source figures large enough to read, or split into smaller focused visuals?
   - Are formula/math sections broken into symbol meaning, ordinary-language role, and a tiny concrete example?
   - Are experiment/result sections written from the evidence outward: show the figure/table, teach how to read it, then state the conclusion?
   - Does every improvement, efficiency, cost, latency, or quality claim record baseline, metric/dimension, direction/value, evidence, and limitation?
   - Do explanations teach reading strategy: what to inspect, what evidence supports the claim, and what not to over-read?
   - For Chinese-bilingual sites, are generated Image 2 diagrams Chinese-dominant, with English retained only as concise aliases for canonical terms?

3. **Source, bilingual, and evidence coverage**
   - Is the main paper text readable in-page?
   - Is the main reading flow paragraph-level and bilingual, rather than selected excerpts plus collapsed raw text?
   - If original text screenshots are used, are they only for layout-sensitive evidence and paired with selectable source text, Chinese reading, plain explanation, `source_id`, page number, and a reason?
   - Is there no screenshot-only source prose?
   - Does every main reading block have a stable `source_id` or equivalent paragraph anchor that appears in the manifest?
   - Does every non-Chinese source paragraph have both a faithful Chinese translation and a separate plain-language explanation?
   - Does every long English passage have proportional Chinese explanation?
   - Are all paper figures/tables included near the relevant paragraphs?
   - Is each figure/table counted once in a primary evidence position, rather than only in a gallery or drawer?
   - Does every figure/table individually explain how to read it, compared with what, conclusion, and limitation?
   - Are dense figures/tables cropped, split, or shown large enough to read, rather than repeated full-page screenshots compressed into the same card size?
   - If a chart/table has been redrawn, are original values, order, axes, units, and uncertainty preserved and explained in HTML?
   - Are generated Image 2 diagrams embedded near the concept they teach, not collected as a public asset list?
   - Are generated Image 2 diagrams real local bitmap assets loaded by the page, not only chat previews?
   - Does `data/learning-site-manifest.json` record source block ids/hashes, chapter coverage, inline term anchors, figure/table links, generated visual language, and omissions with reasons?
   - For PDF sources, does the source inventory record full/main-text extraction totals in addition to selected rendered blocks?
   - Does the manifest record `source_fidelity`, `claim_evidence_map`, `formula_breakdowns` when relevant, and exact term/figure return-link consistency?
   - Does `source_fidelity` point to a real extraction inventory file and hash, rather than a self-reported sentence?
   - Do claim evidence entries distinguish source claims to verify from supported conclusions, and avoid using generated visuals as proof?
   - Do formula or algorithm breakdowns have visible DOM modules with symbol, step, and example sections?
   - Does the manifest record `layout_strategy`, `source_rendering_modes`, `source_screenshot_blocks`, and `interaction_inventory`?
   - Does public UI text, image alt text, `title`, and `aria-label` avoid production/process wording such as `Generated`, `生成教学图资产`, `prompt summary`, `image prompt`, `preflight`, `manifest`, `reader level`, or `面向无专业背景大学生`? Canonical source terms such as `prompt tuning` are allowed when the paper itself uses them.

## Ten-round regression loop

When maintaining this skill or validating a high-risk site, run and record these ten checks:

1. Known-bad regression sample fails for the intended reason.
2. Desktop first viewport shows paper title, chapter nav, source text, Chinese reading/explanation, and a learning affordance.
3. Mobile viewport has no hidden horizontal overflow.
4. Every chapter/question tab displays real source/translation/explanation content.
5. Every language mode preserves the active paragraph and does not create empty content.
6. Inline terms open without covering the active reading block.
7. Term panels close cleanly and return to the clicked source.
8. Every dense figure/table is readable by default or has a tested large/split view.
9. Every chapter-review choice or problem tab produces meaningful feedback and a visible return-to-evidence path.
10. Mobile dynamic interactions pass: term panel overlap, side-note sync, and review feedback link.
11. Public copy scan passes for side notes, alt text, aria labels, and drawer labels.
12. Claim/evidence traceability passes: strong result claims have a nearby evidence module and `claim_evidence_map` entry.
13. Formula/algorithm traceability passes: each formula or pseudocode module has symbols, steps, and a concrete example.
14. Chapter recap production passes: each chapter has a "用自己的话复述" scaffold with links back to evidence.
15. Public UI copy passes: no `样例`, `demo`, `测试页`, raw source ids such as `lora01`, or audience/build-process wording appears to the reader.

## Novice-reader acceptance

Use this 10-point acceptance test after the three passes:

1. A reader knows within five seconds what paper this is, where to begin, and how to switch chapter/language.
2. Main text is readable in-page, not hidden in a PDF iframe, screenshot, or collapsed raw dump.
3. In complete-reader mode, every expected main-text paragraph is included with original text, Chinese reading, and a plain-language explanation.
4. Long or dense paragraphs have enough Chinese explanation to unpack their variables, claims, steps, or limits.
5. Terms are clickable exactly where they appear in the sentence and open the full explanation ladder.
6. Each chapter starts with a problem map and ends with what the reader should now understand.
7. Figures/tables appear beside the argument and teach how to read evidence before stating conclusions.
8. Original-text layout is chosen for the section, and any facsimile screenshot has a selectable-text fallback.
9. Important conclusions link back to the source paragraph, figure/table, or experiment that supports them.
10. Image 2 diagrams clarify mechanisms in Chinese-dominant visual language and do not expose generation workflow.
11. The page feels like a crafted interactive article or reader product, not a summary page, admin dashboard, or build artifact list.
12. A reader can explain the paper in five slots: problem, method, comparison, evidence, and limitation.

## Final acceptance

Do not call the site complete until:

- the source is readable in-page
- key terms are inline and interactive
- source figures/tables are placed and explained
- generated visuals clarify hard ideas and are real Image 2/image-generation outputs unless a fallback was explicitly approved
- Image 2 chat previews have been persisted as local `.png/.jpg/.webp` assets and loaded in the page; otherwise the site is blocked
- original/source screenshots, if present, are not replacing readable HTML text
- section layouts and interaction modules were chosen for the paper's content, not copied from a single template
- local images load
- popovers/drawers open and close
- no obvious layout overlap exists
- strict audit has been run after the final build; if the audit reports missing interaction logic, missing close states, incomplete figure explanation cues, or mobile overflow, fix the site instead of waiving it
- strict audit has been run against at least one known-bad regression sample when tightening the skill, and the known-bad sample now fails for the intended reasons
- the page title and deployment name are paper-specific
