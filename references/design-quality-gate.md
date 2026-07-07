# Design Quality Gate

## Benchmark

Use the Agentopia reader quality as a floor, not a template or ceiling. The first viewport should immediately feel like a designed learning product, not an internal generated note. For each paper, choose the visual system that best fits the topic, audience, and source artifacts; do not force the Agentopia pixel style when another editorial, notebook, report, manga, or product-reader style would teach better.

The first viewport should usually include:

- paper-specific title and subtitle
- visible language mode such as `中英 / 中文 / EN only` for non-Chinese papers
- chapter map with visual landmarks or strong section affordances
- main reading card with paragraph-level original text and Chinese reading
- synchronized side note, marginalia, or learning panel
- an inline term trigger or figure/table evidence entry close to the first reading block
- paper-specific visual assets or generated illustrations
- no visible internal workflow or audience-targeting copy

## Fail states

Reject and redesign if the page looks like any of these:

- generic gray/white admin dashboard
- plain three-column documentation layout with little typographic hierarchy
- tiny SVG flow boxes used as the main "generated diagrams"
- all source figures or tables pushed to the end
- full paper text hidden in collapsed raw `<pre>` blocks while the main reader shows only excerpts
- no language mode for non-Chinese material
- no theme derived from the paper topic, figures, audience, or user preference
- hero or intro copy that says who the generator targeted, e.g. "面向无专业背景大学生", instead of speaking directly to the reader about what they will understand
- interaction hints that are visually ambiguous, such as a lone underlined term outside the paragraph with no nearby explanation of what clicking does
- public image alt/title/aria text that says "Generated explainer", "prompt", "asset", or other production wording
- a public "generated image asset" gallery that is not part of the learning path

## Reader Product Bar

Aim beyond a static web page:

- paragraph-level focus, with active paragraph state and synchronized side notes
- inline annotations attached to exact words, sentences, figures, and table cells
- clean reading mode plus optional original PDF/page context for layout-sensitive evidence
- semantic highlight colors with a visible or discoverable legend
- figure/table close-reading panels that teach how to inspect evidence, not just show screenshots
- short "what to look for" prompts before hard sections and "what you should now know" after them
- reader actions that feel learnable: define term, inspect evidence, compare baseline, show limitation, jump to next claim
- review affordances after each chapter: checkpoint, concept recap, and "next section asks..." bridge

## Product references to borrow from

Use the principle, not the visual skin:

- Readwise Reader / Zotero-style annotations: highlights, notes, and "show in context" links are core reading objects.
- Hypothesis-style anchored annotation: comments attach directly to the source sentence.
- Distill/Observable-style interaction: details-on-demand, small interactive explanations, and visual outputs live beside the prose.
- Science in the Classroom-style annotation: novice explanations overlay the original article instead of replacing it.

## Visual direction

Before coding, choose a visual direction and write it down:

- paper topic and emotional tone
- visual metaphor or motif
- typography scale
- color palette
- icon/illustration style
- how figures and generated diagrams will sit in the reading flow

For academic learning sites, prefer restrained but distinctive design. Use texture, illustration, chapter landmarks, and clear typography; avoid decorative noise.

## First-screen acceptance

Take a desktop screenshot before final delivery. A reviewer should be able to tell within five seconds:

- what paper this is
- that it is a bilingual/source-text reader
- where to start reading
- how to switch chapters
- where explanations and terms will appear

If not, iterate on layout before polishing content.
