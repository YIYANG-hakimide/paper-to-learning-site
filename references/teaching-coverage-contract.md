# Teaching Coverage Contract

## Purpose

Prevent all output modes from becoming a beautiful summary that omits the difficult teaching work. Derive coverage requirements from the complete source before storyboarding.

## Teaching Inventory

Create `data/teaching-inventory.json` with these arrays, even when some are empty:

Also record the current source-inventory hash, derivation rules version, `derivation_checked: true`, and `reviewer_status: passed`. An academic paper/report must normally identify at least one hard concept and one central claim; empty arrays cannot be used to bypass teaching coverage.

- `hard_concepts[]`: id, canonical term, source ids, prerequisite dependencies, and why it blocks understanding
- `formula_or_algorithm_items[]`: id, source ids, symbols/steps that need breakdown, and whether a worked example is required
- `experiments[]`: id, source ids, setup, baseline, metric, result evidence ids, and likely novice confusion
- `major_figures[]`: id, source ids, panels/rows/columns that require explanation, and linked claims
- `central_claims[]`: id, source ids, role, baseline, metric/dimension, direction/value, evidence ids, and limitation

Record the inventory path and hash in every mode-specific manifest.

## Coverage Requirements

Every inventory id must map to final output items or an explicit omission allowed by the selected size mode.

- Concise mode may omit secondary items, but never the core method, strongest supporting evidence, or central limitation.
- Medium mode covers every central claim and major method component plus the most important formulas/figures/experiments.
- Detailed mode covers all teaching-inventory items except truly redundant appendix material, with reasons.
- Complete HTML covers all main-text source blocks and all teaching-inventory items.

Record coverage arrays:

- `hard_concept_coverage[]`
- `formula_coverage[]`
- `experiment_coverage[]`
- `major_figure_coverage[]`
- `central_claim_coverage[]`

Each entry names the inventory id, final item/page/block ids, and `covered|omitted` status with reason when omitted.

## Evidence Bundle

For every central method claim or conclusion, create an `evidence_bundle` adapted to the output mode:

- `bundle_id`
- `claim_id`
- `final_item_ids`
- `source_ids`
- `source_excerpt_or_asset`
- `visible_source_cue`
- `chinese_explanation`
- `evidence_meaning`
- `limitation`

Image series: the visible source cue and Chinese explanation must be present in the composed bitmap and OCR-verified.

PPT: the source cue and Chinese explanation must be visible on the page or immediately linked evidence page; DOM/page ids must resolve.

HTML: the original paragraph/figure/formula, Chinese reading, explanation, and limitation stay linked in the reader.

Generated visuals may be part of the explanation but never the sole source asset for a supported conclusion.
