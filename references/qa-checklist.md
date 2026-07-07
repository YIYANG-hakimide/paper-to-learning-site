# QA Checklist

## Three review passes

Use subagents only when the user explicitly requested delegated/subagent review and the current tool policy allows it. Otherwise perform independent manual passes and write down findings before fixing.

1. **Design and interaction**
   - Is the page attractive and specific to this paper?
   - Does the first viewport clearly look like a learning reader, not a generated note?
   - In the first desktop viewport, can a reviewer see the paper title, language mode, chapter navigation, a real source paragraph, Chinese reading/explanation, and a side note or inline learning affordance?
   - Does the public UI avoid production/audience/process labels such as `面向无专业背景大学生`, `preflight`, `manifest`, `regression`, `生成教学图资产`, or `generated assets`?
   - Is there a visible language mode for non-Chinese sources?
   - Does it avoid generic AI/dashboard aesthetics?
   - Does it avoid plain gray/white three-column documentation styling unless the topic explicitly calls for it?
   - Are chapter switching, drawers, term popovers, and close states obvious?
   - Do language controls, term triggers, drawers, and figure panels actually change state, rather than appearing as decorative buttons?
   - Are term triggers underlined or otherwise discoverable inside the original sentence, translation, or explanation, not only in a detached term/tag strip?
   - Do interactive controls expose state with `aria-expanded`, `aria-controls`, `aria-current`, or equivalent accessible semantics?
   - Do repeated action buttons name the learning action, figure/table, or chapter instead of generic labels like `打开图表抽屉`?
   - Is there no text overlap on mobile and desktop?
   - Is there no horizontal clipping on mobile, especially inside figure/table explanation rows and bilingual paragraph blocks?
   - Does the reader avoid repeated dead-end navigation?

2. **Teaching comprehension**
   - Can a non-specialist college student understand the problem, method, evidence, and conclusion?
   - Does each chapter start with a learner-facing question/evidence map, not a production brief?
   - Are hard terms explained from general definition to paper-specific use?
   - Are terms introduced at the first point where they block comprehension, not later in a separate glossary?
   - Are explanations proportional to source difficulty, so long or dense English passages get more than one generic sentence?
   - Are chapter logic summaries and checkpoints useful?
   - Are diagrams used where text alone would be dry or abstract?
   - Do explanations teach reading strategy: what to inspect, what evidence supports the claim, and what not to over-read?
   - For Chinese-bilingual sites, are generated Image 2 diagrams Chinese-dominant, with English retained only as concise aliases for canonical terms?

3. **Source, bilingual, and evidence coverage**
   - Is the main paper text readable in-page?
   - Is the main reading flow paragraph-level and bilingual, rather than selected excerpts plus collapsed raw text?
   - Does every main reading block have a stable `source_id` or equivalent paragraph anchor that appears in the manifest?
   - Does every non-Chinese source paragraph have Chinese translation or explanation?
   - Does every long English passage have proportional Chinese explanation?
   - Are all paper figures/tables included near the relevant paragraphs?
   - Is each figure/table counted once in a primary evidence position, rather than only in a gallery or drawer?
   - Does every figure/table individually explain how to read it, compared with what, conclusion, and limitation?
   - Are generated Image 2 diagrams embedded near the concept they teach, not collected as a public asset list?
   - Does `data/learning-site-manifest.json` record source block ids/hashes, chapter coverage, inline term anchors, figure/table links, generated visual language, and omissions with reasons?
   - Does public UI text, image alt text, `title`, and `aria-label` avoid production/process wording such as `Generated`, `生成教学图资产`, `prompt`, `preflight`, `manifest`, `reader level`, or `面向无专业背景大学生`?

## Novice-reader acceptance

Use this 10-point acceptance test after the three passes:

1. A reader knows within five seconds what paper this is, where to begin, and how to switch chapter/language.
2. Main text is readable in-page, not hidden in a PDF iframe, screenshot, or collapsed raw dump.
3. Every included main-text paragraph has original text, Chinese reading, and a plain-language explanation.
4. Long or dense paragraphs have enough Chinese explanation to unpack their variables, claims, steps, or limits.
5. Terms are clickable exactly where they appear in the sentence and open the full explanation ladder.
6. Each chapter starts with a problem map and ends with what the reader should now understand.
7. Figures/tables appear beside the argument and teach how to read evidence before stating conclusions.
8. Important conclusions link back to the source paragraph, figure/table, or experiment that supports them.
9. Image 2 diagrams clarify mechanisms in Chinese-dominant visual language and do not expose generation workflow.
10. The page feels like a crafted interactive article or reader product, not a summary page, admin dashboard, or build artifact list.

## Final acceptance

Do not call the site complete until:

- the source is readable in-page
- key terms are inline and interactive
- source figures/tables are placed and explained
- generated visuals clarify hard ideas and are real Image 2/image-generation outputs unless a fallback was explicitly approved
- local images load
- popovers/drawers open and close
- no obvious layout overlap exists
- strict audit has been run after the final build; if the audit reports missing interaction logic, missing close states, incomplete figure explanation cues, or mobile overflow, fix the site instead of waiving it
- strict audit has been run against at least one known-bad regression sample when tightening the skill, and the known-bad sample now fails for the intended reasons
- the page title and deployment name are paper-specific
