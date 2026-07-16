# Teaching Coverage Contract

## Purpose

Prevent all output modes from becoming a beautiful summary that omits the difficult teaching work. Derive coverage requirements from the complete source before storyboarding.

## Teaching Inventory

Create `data/teaching-inventory.json` with these arrays, even when some are empty:

Also record source type and in-scope range, the current source-inventory hash, derivation rules version, `derivation_checked: true`, and `reviewer_status: passed`. An academic paper/report must normally identify at least one hard concept and one central claim; a book/article must normally identify central ideas plus supporting examples or argument steps; a manual must identify procedures and failure modes. Empty arrays cannot be used to bypass teaching coverage.

- `hard_concepts[]`: id, canonical term, source ids, prerequisite dependencies, why it blocks understanding, `first_use_item_id`, definition item ids, field definition, plain analogy, source-specific meaning, author usage, and common misunderstanding
- `formula_or_algorithm_items[]`: id, source ids, symbols/steps that need breakdown, and whether a worked example is required
- `experiments[]`: id, source ids, setup, baseline, metric, result evidence ids, and likely novice confusion
- `major_figures[]`: id, source ids, panels/rows/columns that require explanation, and linked claims
- `central_claims[]`: id, source ids, role, baseline, metric/dimension, direction/value, evidence ids, and limitation

Every inventory entry also records `mode_requirement` with `image-series`, `presentation-pdf`, and `interactive-html` values: `must-cover`, `optional`, or `not-applicable`. Decide these values from the complete in-scope source, selected size, and user focus before storyboarding.

Record the inventory path and hash in every mode-specific manifest.

## Coverage Requirements

Every inventory id must receive a mode-specific selection decision before storyboarding.

- Image series prioritizes selected hard concepts, core methods/architecture, central experiments/evaluation, causal/evidence chains, and central claims. It does not need to reproduce every major source figure or formula.
- PPT concise mode may omit secondary items, but never the core method, strongest supporting evidence, or central limitation.
- PPT medium mode covers every central claim and major method component plus the most important formulas/figures/experiments.
- PPT detailed mode covers all teaching-inventory items except truly redundant appendix material, with reasons.
- Complete HTML covers all main-text source blocks and all teaching-inventory items.

Record coverage arrays appropriate to the mode:

- `hard_concept_coverage[]`
- `formula_coverage[]`
- `experiment_coverage[]`
- `major_figure_coverage[]`
- `central_claim_coverage[]`

Each entry names the inventory id, whether it was selected for this mode, final item/page/block ids, and `covered|omitted` status with reason when omitted.

## Evidence Bundle

For every central method claim or conclusion, create an `evidence_bundle` adapted to the output mode:

- `bundle_id`
- `claim_id`
- `final_item_ids`
- `source_ids`
- `source_excerpt_or_asset` for PPT/HTML, or `source_excerpt_sha256` for image series
- `visible_source_cue` for PPT/HTML
- `chinese_explanation`
- `evidence_meaning`
- `limitation` when relevant

Image series: the Chinese explanation must be present in the native generated bitmap and OCR-verified. Source traceability remains internal; citations and source crops are not required inside the image.

PPT: the source cue and Chinese explanation must be visible on the page or immediately linked evidence page; DOM/page ids must resolve.

HTML: the original paragraph/figure/formula, Chinese reading, explanation, and limitation stay linked in the reader.

Generated visuals may be part of the explanation but never the sole source asset for a supported conclusion.
