# Complete Reader Design Quality Gate

## Benchmark

Use the Agentopia reader quality as historical learning, not a template or ceiling. This file applies to the default complete-reader HTML mode. Choose the visual system that best fits the topic, audience, and source artifacts; do not force the Agentopia pixel style when another editorial, notebook, report, manga, or product-reader style would teach better.

The target is not "pretty enough"; it is a complete guided reader that preserves paragraph-level source text while making concepts and evidence understandable. A beautiful page that hides the source, shrinks evidence, or opens empty interactions fails.

The first viewport should usually include:

- paper-specific title and subtitle
- visible language mode such as `中英 / 中文 / EN only` for non-Chinese papers
- chapter map with visual landmarks or strong section affordances
- main reading card with paragraph-level original text and Chinese reading
- synchronized side note, marginalia, or learning panel
- an inline term trigger or figure/table evidence entry close to the first reading block
- paper-specific visual landmark or teaching image in the first viewport; it can be a cropped source figure, Image 2 mechanism diagram, formula strip, architecture thumbnail, or chapter-map landmark, but it must teach the paper rather than decorate the header
- a visible reading-layout choice that fits the section, not a one-size-fits-all grid
- no visible internal workflow or audience-targeting copy
- paragraph-specific side note copy; repeated "this paragraph advances the chapter" style notes fail because they do not teach the reader what to notice

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
- public image alt/title/aria text that says "Generated explainer", "prompt summary", "image prompt", "asset", or other production wording
- a public "generated image asset" gallery that is not part of the learning path
- identical card rhythm for every section even when the content switches from prose to math, architecture, or experiments
- first viewport with no paper-specific visual landmark, making the page feel like a template with different text
- screenshot-only source prose with no selectable text fallback
- a first screen that is only a hero/cover and makes the reader scroll before seeing real paper text
- a design brief that says only "clean", "modern", "Apple-like", "anime", or "dashboard" without concrete typography, spacing, reading density, and paper-specific motifs
- controls that look clickable but do not change state, do not close, or reopen the same summary everywhere
- term modals or drawers that cover the paragraph containing the clicked word
- dense source figures rendered below about half a desktop column width with no real large view or split-panel alternative
- side notes that read like internal reasoning, prompt plans, audit notes, or production logs
- side notes that repeat the same generic sentence across multiple paragraphs instead of explaining the current paragraph
- chapter/question states that contain only headings, placeholders, or generic summaries
- result claims that appear before the reader has seen the figure/table/evidence needed to judge them
- chapter recap cards that only ask multiple-choice questions and never ask the reader to restate the paper's logic in their own words

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
- Feynman-style recap affordances: "问题是什么 -> 方法怎么做 -> 相比谁 -> 证据是什么 -> 不能推出什么"
- varied but coherent section rhythms: close-reading blocks for dense prose, figure-led layouts for evidence, formula cards for math, and visual modules for abstract mechanisms
- evidence-first modules for tables/figures: a reader should see the chart/table clearly before accepting the written conclusion
- chapter-specific visual landmarks: chapter buttons, side rails, or first cards should expose the paper's own objects, equations, agents, datasets, tables, or mechanisms instead of generic pills

## Product references to borrow from

Use the principle, not the visual skin:

- Readwise Reader / Zotero-style annotations: highlights, notes, and "show in context" links are core reading objects.
- Hypothesis-style anchored annotation: comments attach directly to the source sentence.
- Distill/Observable-style interaction: details-on-demand, small interactive explanations, and visual outputs live beside the prose.
- Science in the Classroom-style annotation: novice explanations overlay the original article instead of replacing it.
- Get It.-style document anchoring: concept tags should open visualizers, review cards, or knowledge-map nodes without replacing the source document.
- Paper-to-course-style learning modules: formula breakdowns, timelines, method chats, comparison tables, ablation diagrams, and chapter reviews are useful when tied to exact paper content.

## Visual direction

Before coding, choose a visual direction and write it down:

- paper topic and emotional tone
- visual metaphor or motif
- typography scale
- color palette
- spacing rhythm and panel density
- source-text line width and bilingual text hierarchy
- semantic colors for terms, evidence, limitations, and definitions
- icon/illustration style
- component shapes and where cards are allowed
- minimum visual sizes for dense source figures, generated diagrams, tables, and zoom panels
- desktop and mobile layout behavior
- first-viewport priority: what must be visible and what can be one click away
- first-viewport visual landmark: which paper-specific visual appears immediately, what it teaches, and why it is not decorative
- `first_viewport_landmarks[]` manifest entry: selector/path, linked source ids, and why the object is paper-specific
- component rhythm plan: which sections use prose close reading, figure-led evidence, formula cards, visual diagrams, comparison boards, and recap cards
- evidence-first plan: where figures/tables appear before conclusions, especially in experiment/result chapters
- how figures and generated diagrams will sit in the reading flow
- which source rendering modes will be used: parallel, stacked, interleaved, figure-led, facsimile-plus-HTML
- which interactive learning modules will be used and why
- for long papers, `section_map[]` and `chapter_landmarks[]` so navigation exposes the paper's structure, evidence, and hard concepts

For academic learning sites, prefer restrained but distinctive design. Use texture, illustration, chapter landmarks, and clear typography; avoid decorative noise.

## First-screen acceptance

Take a desktop screenshot before final delivery. A reviewer should be able to tell within five seconds:

- what paper this is
- that it is a bilingual/source-text reader
- where to start reading
- how to switch chapters
- where explanations and terms will appear
- which visual object makes this paper recognizable
- that the page is not merely a summary cover before the actual reading begins

If not, iterate on layout before polishing content.

## Visual Review Rounds

Run at least these design reviews before final delivery:

1. **Layout rhythm**: sections should not all use the same card pattern. Check that methods, formulas, figures, experiments, and review cards have forms suited to their content.
2. **Reading typography**: CJK/Latin text should have comfortable line height, stable width, `lang` attributes where feasible, and no overlong lines.
3. **Interaction clarity**: every clickable term, figure, visualizer, chapter-review, or chapter control should look clickable and explain what will happen.
4. **Evidence legibility**: every source figure/table and generated explainer should be readable at its default size or have a tested large/split view.
5. **Public-copy hygiene**: side notes, alt text, drawer headings, and aria labels should sound like a teacher, not a build log or self-review.
