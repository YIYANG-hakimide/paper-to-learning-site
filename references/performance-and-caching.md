# Performance And Caching

## Principle

Spend time on understanding and final quality, not repeated extraction, unnecessary output formats, or regenerating unchanged assets.

## Layered Cache

Do not use one cache key for the whole task. Store layers under a task cache root and include a schema/version in every layer:

- extraction key: source SHA-256 + extraction tool/version + OCR settings
- semantic key: extraction hash + explanation-rules version + source language
- storyboard key: semantic hash + user focus + output mode + requested/resolved size + reader level
- visual key: storyboard item hash + aspect ratio + visual direction + model/provider + prompt hash + quality-rules version
- composition key: visual/evidence hashes + output mode + typography/layout-system version
- deployment/export key: composition hash + renderer/export settings

Cache:

- full text and per-page extraction diagnostics
- source inventory and stable source ids
- rendered PDF pages and accepted figure/table crops
- terms, prerequisites, formulas, claims, and evidence links
- storyboard drafts and accepted visual prompt packets under their mode/focus keys
- final generated assets with prompt/model/aspect-ratio/hash metadata

Invalidate only the affected layer and its downstream dependents. Never reuse a 3:4 image-series composition as a 16:9 PPT page merely because the source paper matches.

## Fast Path

1. Run preflight and source hash check.
2. Reuse a valid cache when available.
3. Skip style previews unless the user requested one.
4. Lock storyboard before expensive generation.
5. Generate 3-6 independent assets per batch, in parallel only when the provider supports it reliably.
6. Run structural checks after every batch.
7. Run OCR and visual inspection only on new or changed images.
8. Run full browser/export/deployment QA once near completion.

## Avoidable Work

- Do not create HTML, PDF, and image-series outputs when only one was selected.
- Do not generate an image for a slide that can be clearer and more accurate as HTML text, a source crop, formula, or deterministic chart.
- Do not regenerate approved PPT/HTML visuals because nearby copy changed. Image-series copy is part of the bitmap, so a copy correction requires regenerating that image.
- Do not render all slides after every small text edit; use changed-page sampling, then one final full render.
- Do not generate visual-style alternatives unless the user asked for them.
- Do not rerun expensive adversarial reviews before the storyboard and first complete draft exist.

## Time Budget Awareness

Estimate workload after storyboard lock. If the detailed mode would require unusually many image calls or a very long run, state the expected count and use the selected scope. Do not quietly expand beyond 36 images/pages.
