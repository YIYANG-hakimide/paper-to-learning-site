# Output Modes And Sizing

## Mode Decision

Ask for one primary output:

- `image-series`: direct model-generated, high-information infographics plus a page-matched album PDF
- `presentation-pdf`: a 16:9 self-reading visual consulting report exported as PDF
- `interactive-html`: interactive bilingual/Chinese source reader and deployable website

Do not silently produce all modes. Reuse cached work only when the user later requests another mode.

## Automatic Count

Automatic count applies to image series and presentation PDF.

Build a complexity score after source inventory:

- main-text pages: 1 point per 4 pages, capped at 6
- hard prerequisite concepts: 1 point each, capped at 6
- method stages that need separate explanation: 1 point each, capped at 6
- important source figures/tables/formulas: 1 point per 2 objects, capped at 6
- multiple experimental settings or datasets: 1 point each, capped at 4
- explicit user focus areas: add 1-3 points depending on breadth

Choose:

- score 0-7: concise, normally 7-10 items
- score 8-15: medium, normally 12-18 items
- score 16+: detailed, normally 21-32 items

When automatic is requested, record `size_mode_requested: automatic`, resolved `size_mode`, complexity score/breakdown, a target range, maximum count, final resolved count, and rationale. The resolved count may move inside the target range after removing filler; it does not need to equal an early single-number estimate.

Use judgment. A short but mathematically difficult paper may need medium detail; a long survey may need a curated medium deck unless the user asks for exhaustive coverage.

## Mode-Specific Density

### Image Series

- Concise: 6-10 images
- Medium: 12-18 images
- Detailed: 21-30 images, rarely above 36
- Each image is a complete native generated infographic with a visible Chinese title and sufficient integrated explanation.
- Always establish the paper argument and core contribution early. Choose later images dynamically from concepts, method, architecture, experiments, evaluation, causal/evidence chains, and user focus.
- The whole-paper context map and core-contribution map are always two separate images, including concise mode.
- Image mode covers fewer details than PPT at the same nominal size; prioritize the ideas that most benefit from visual explanation.

### Presentation PDF

- Concise: 6-10 pages
- Medium: 12-20 pages
- Detailed: 21-36 pages
- Use report-level density for independent reading. A page should contain the conclusion, explanation, evidence, and implication needed to stand alone.
- Split dense evidence into dedicated pages rather than shrinking it. Do not add empty transition pages merely to imitate a keynote deck.
- Detailed PPT coverage is broader than detailed image-series coverage and should include important source figures/tables and experimental interpretation.

### Interactive HTML

Do not ask for a fixed page count. Size the site by paper chapters, source coverage, interactions, and user focus. The user may request a curated or complete reader; make scope explicit.

## Tradeoffs

- Concise mode may omit secondary experiments, related work detail, appendix analyses, and minor ablations.
- Medium mode should preserve all central method steps and strongest evidence.
- Detailed image series should deepen the most visual core ideas without pretending to reproduce the full paper.
- Detailed PPT should include prerequisite ladders, worked examples, panel-level figure explanations, major ablations, and limitations.
- No mode may omit the source of a central conclusion or present a generated visual as evidence.
