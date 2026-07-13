# Learning Deck QA Checklist

## Story And Teaching

- [ ] The deck opens with the paper's real problem, not production framing.
- [ ] The outline follows learner questions and causal logic.
- [ ] Prerequisites appear before technical use.
- [ ] World/data construction, training, simulation/inference, and evaluation are separated where relevant.
- [ ] Every hard concept uses the full explanation ladder.
- [ ] Each slide has one clear learner question and one dominant teaching object.
- [ ] Dense ideas are split instead of compressed into tiny text.
- [ ] Recaps ask the learner to reconstruct the logic in their own words.

## Visuals

- [ ] Most teaching slides contain a substantial visual, source evidence object, or formula/example breakdown.
- [ ] Every major concept that benefits from spatial or causal explanation has a generated teaching visual.
- [ ] Generated visuals are local raster assets and use the recorded real model.
- [ ] Visual style is derived from the paper topic and remains coherent across the deck.
- [ ] Generated image labels are short, readable, and Chinese-dominant for Chinese readers.
- [ ] No important generated image is decorative only.
- [ ] No visual is cropped, blurry, too small, or overloaded.
- [ ] Source evidence and generated explanation are visually distinguishable.
- [ ] Every text-bearing generated visual has OCR results compared with the expected labels.
- [ ] Every generated visual records `display_width_px`, `display_height_px`, `crop_checked`, `reviewer_status`, and regeneration reason when it failed.
- [ ] Primary visuals occupy a substantial slide area; dense evidence is at least 1100px wide on stage or has a dedicated split/zoom slide.

## Evidence

- [ ] The complete main paper was inventoried before slide selection.
- [ ] Important paper figures/tables appear in readable form.
- [ ] Multi-panel figures are split or individually annotated when needed.
- [ ] Experimental setup and metric meaning appear before result claims.
- [ ] Every important result states baseline, metric, direction/value, evidence, and limitation.
- [ ] Generated images never serve as the sole proof of a conclusion.
- [ ] “查看原文依据” links or evidence slides land on the correct source object.
- [ ] Exact values, formulas, quotations, and citations are selectable HTML or faithful source crops.

## Design And Runtime

- [ ] Every slide fits the fixed 1920x1080 stage without scrolling.
- [ ] No text or image overlaps at desktop and smaller viewport scales.
- [ ] Typography remains readable when the stage is scaled to a laptop viewport.
- [ ] Previous/next, keyboard, overview, fullscreen, progress, and direct navigation work.
- [ ] No control opens an empty state or blocks the content it explains.
- [ ] Motion supports pacing and respects `prefers-reduced-motion`.
- [ ] Public slides contain no prompt, manifest, QA, reader-level, asset, or internal-review language.
- [ ] The first slide and first content slide feel paper-specific, not templated.
- [ ] Slide `layout_family` distribution was checked; one repeated composition does not dominate without a paper-specific reason.

## Export

- [ ] All local images load with no broken paths.
- [ ] PNG export preserves the complete stage and fonts.
- [ ] PDF export preserves page order, crop, and text legibility.
- [ ] At least the title, one image-led slide, one evidence slide, and one dense slide were inspected after export.
- [ ] Vercel deployment is verified only after local QA passes.

## Adversarial Passes

Run three independent reviews:

1. Visual designer: hierarchy, composition, typography, style coherence, image scale, and anti-template quality.
2. Novice learner: missing prerequisites, unexplained leaps, confusing terms, and whether each image actually teaches.
3. Evidence reviewer: source coverage, claim/evidence linkage, figure/table interpretation, factual labels, and limitations.

Fix concrete findings and rerun the relevant checks before delivery.
