# Deck Design Quality Gate

## Product Bar

The result must feel like a deliberately art-directed visual lesson, not an AI dashboard, a document pasted into slides, or twenty repetitions of one card layout. It should be more explanatory than a conventional teaching PPT and more evidence-grounded than a visual summary.

It must also feel presentable. Every page needs a clear focal point, readable speaking order, and enough breathing room to work on a projected screen. A correct but report-like PDF fails PPT mode.

## First Two Slides

Within the title slide and first content slide, a reviewer should understand:

- which paper this is
- the real problem or learner question
- the paper-specific visual motif
- the deck's reading density and visual language
- that the first content slide already teaches something

Reject generic agenda slides, audience descriptions, production framing, and template names.

## Preview Difference

When multiple style previews are generated, they must differ in at least three of these dimensions:

- composition system
- typography character
- material/texture
- illustration language
- palette and contrast
- information rhythm

All previews must use real paper content. Do not present recolored versions of the same layout. When the direction is already clear, one well-inspected preview is enough and is preferred for speed.

## Slide Composition Families

Use multiple coherent composition families:

- image-led scene or mechanism
- annotated process or sequence
- source evidence close reading
- formula/worked example
- comparison or baseline board
- timeline/map/system view
- quotation or argument transition
- recap/reconstruction

Record `layout_family` on each slide. No single content layout family should occupy more than about 60% of teaching slides unless the design brief explains why the paper genuinely requires it. Avoid consecutive repetition of the same left-text/right-image composition.

## Presentation Rhythm

Deliberately alternate opening question or tension, visual explanation, concrete example, source evidence, conclusion, and transition. Use section beats to reset attention without adding empty agenda pages.

Read each page aloud during review. If a presenter must read a paragraph verbatim, split or rewrite it. If a page has no obvious first thing to look at, redesign it. Include some low-density, high-impact pages; reserve dense composition for evidence where density is justified.

## Size And Legibility

- A primary generated visual should normally occupy at least 40% of the slide content area.
- A dense source figure or table should normally render at least 1100px wide on the 1920x1080 stage, or receive a dedicated split/zoom slide.
- Generated full-slide teaching images should normally be at least 1536x864; prefer 1920x1080 or larger.
- At a 1366x768 browser viewport, key HTML text and in-image labels must remain comfortably readable. Treat labels whose rendered height is below roughly 16px as a failure.
- Do not place a complex diagram in a thumbnail beside a long paragraph.
- If a figure cannot meet these constraints, split it or use image-above/explanation-below across multiple slides.

## Evidence Styling

Make the distinction visible:

- generated visual: explanation, analogy, mechanism, or orientation
- paper crop: original evidence
- HTML chart/table/formula: precise reconstructed evidence
- conclusion: explicitly linked interpretation
- limitation: a visually consistent caution treatment

Do not let generated images imitate a source-paper screenshot so closely that learners may mistake illustration for evidence.

## Anti-Template Failures

Reject the deck when:

- it uses a generic purple/blue AI gradient with no paper-specific reason
- most pages are nested cards or dashboard panels
- every page repeats the same split layout
- decorative images dominate while mechanisms and evidence remain text-only
- the paper motif appears only on the cover
- title scale, body scale, and visual scale do not change with the teaching job
- source figures are too small to read
- image labels are garbled, tiny, or unrelated
- internal prompt, asset, QA, model, manifest, or reader-level text is public
- animations distract from reading or cause layout shifts
- every page has report-card density and no presentational breathing room
- the deck is merely image-series cards resized onto 16:9 pages

## Required Visual Review

Render every slide, then review:

1. hierarchy and focal point
2. image scale and crop
3. typography and bilingual spacing
4. repeated layout rhythm
5. source/generated distinction
6. label readability
7. overflow, collision, and clipping
8. first-slide and first-content-slide specificity

Record concrete failures and fixes in `qa/qa-report.json`. A manifest checkbox without rendered screenshots is not enough.
