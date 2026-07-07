# QA Checklist

## Three review passes

Use subagents only when the user explicitly requested delegated/subagent review and the current tool policy allows it. Otherwise perform independent manual passes and write down findings before fixing.

1. **Design and interaction**
   - Is the page attractive and specific to this paper?
   - Does the first viewport clearly look like a learning reader, not a generated note?
   - Is there a visible language mode for non-Chinese sources?
   - Does it avoid generic AI/dashboard aesthetics?
   - Does it avoid plain gray/white three-column documentation styling unless the topic explicitly calls for it?
   - Are chapter switching, drawers, term popovers, and close states obvious?
   - Do language controls, term triggers, drawers, and figure panels actually change state, rather than appearing as decorative buttons?
   - Is there no text overlap on mobile and desktop?
   - Is there no horizontal clipping on mobile, especially inside figure/table explanation rows and bilingual paragraph blocks?
   - Does the reader avoid repeated dead-end navigation?

2. **Teaching comprehension**
   - Can a non-specialist college student understand the problem, method, evidence, and conclusion?
   - Are hard terms explained from general definition to paper-specific use?
   - Are chapter logic summaries and checkpoints useful?
   - Are diagrams used where text alone would be dry or abstract?

3. **Source, bilingual, and evidence coverage**
   - Is the main paper text readable in-page?
   - Is the main reading flow paragraph-level and bilingual, rather than selected excerpts plus collapsed raw text?
   - Does every non-Chinese source paragraph have Chinese translation or explanation?
   - Does every long English passage have proportional Chinese explanation?
   - Are all paper figures/tables included near the relevant paragraphs?
   - Does every figure/table explain how to read it, compared with what, conclusion, and limitation?
   - Does `data/learning-site-manifest.json` honestly record source paragraph, figure/table, and generated visual coverage?

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
- the page title and deployment name are paper-specific
