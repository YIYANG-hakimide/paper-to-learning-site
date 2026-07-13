# Implementation And Deploy

## Default Deck Package

Create a static, portable package:

```text
learn-paper-title/
  index.html
  assets/
    visuals/       # generated teaching images
    evidence/      # cropped source figures, tables, formulas, screenshots
    fonts/         # optional local fonts
    exports/       # optional slide PNGs and PDF
  data/
    source-inventory.json
    learning-deck-manifest.json
  qa/
    screenshots/
    qa-report.json
```

Prefer one self-contained HTML file with inline CSS/JS and local image assets. No npm or framework should be required to open it unless the user asks for a framework.

## Fixed Stage

- Author every slide at 1920x1080.
- Scale the stage uniformly to fit the viewport; letterboxing is acceptable.
- Do not reflow slide contents for phones.
- Keep navigation UI outside the stage when practical.
- Switch slides with explicit active state, opacity, visibility, and pointer events.
- Support previous/next buttons, ArrowLeft/ArrowRight, Home/End, direct slide links, overview, fullscreen, and progress.
- Respect `prefers-reduced-motion`.

## Slide Data

Represent every slide with structured fields:

- id and order
- chapter/logic unit
- slide type
- learner question
- one-sentence answer
- source ids and evidence ids
- visual id or source figure id
- misconception to prevent
- next-slide bridge
- public-copy-reviewed status

Recommended slide types:

- title
- problem
- prerequisite
- concept
- method-overview
- method-step
- worked-example
- world/data-construction
- training/inference/evaluation separation
- source-figure
- source-table
- formula-breakdown
- result
- limitation
- recap
- evidence/source appendix

## Manifest

Create `data/learning-deck-manifest.json` with at least:

```json
{
  "source_title": "Paper title",
  "source_language": "en",
  "deck_language": "zh-bilingual",
  "slides_expected": 24,
  "slides_rendered": 24,
  "generated_visuals_expected": 13,
  "generated_visuals_rendered": 13,
  "image_generation_route": {
    "provider": "built-in imagegen",
    "model": "gpt-image-2",
    "local_asset_export": true
  },
  "source_fidelity": {
    "inventory_path": "data/source-inventory.json",
    "main_text_total_blocks": 126,
    "main_text_inventory_sha256": "sha256:..."
  },
  "design_brief": {
    "paper_motif": "pixel town and event routes",
    "visual_direction": "warm pixel-world teaching atlas",
    "typography_plan": "clear Chinese sans plus compact English source serif",
    "evidence_style": "crisp paper crops on neutral panels",
    "why_topic_specific": "the source studies a pixel-like simulated town and agents"
  },
  "slides": [
    {
      "id": "slide-08",
      "order": 8,
      "type": "method-step",
      "learner_question": "虚拟人每天如何决定下一步？",
      "one_sentence_answer": "记忆、当前目标和环境共同形成下一步行动。",
      "source_ids": ["sec3-p14", "sec3-p15"],
      "visual_id": "agent-action-loop",
      "misconception_to_prevent": "角色不是预先写死整天脚本",
      "next_slide_bridge": "有了单个角色，还要解释多个角色如何共享世界。"
    }
  ],
  "generated_visuals": [
    {
      "id": "agent-action-loop",
      "path": "assets/visuals/agent-action-loop.png",
      "model_name": "gpt-image-2",
      "teaches_concept": "agent action selection",
      "learner_question": "虚拟人每天如何决定下一步？",
      "visual_type": "pixel-world process scene",
      "in_image_text_language": "zh-dominant",
      "linked_source_ids": ["sec3-p14", "sec3-p15"],
      "asset_verified": true
    }
  ],
  "paper_evidence": [],
  "claim_evidence_map": [],
  "exports": {
    "png_count": 24,
    "pdf_path": "assets/exports/learn-paper.pdf"
  },
  "qa": {
    "fixed_stage_checked": true,
    "all_slides_rendered": true,
    "small_viewport_checked": true,
    "public_copy_clean": true,
    "visual_inspection_complete": true,
    "adversarial_passes": ["design", "novice-learning", "evidence"]
  }
}
```

Counts must describe real rendered assets. Never lower expected image counts because generation failed.

## Image Integration

- Save every generated bitmap under `assets/visuals/`.
- Embed it on the owning slide as a real `<img>` or `<picture>`.
- Give the image enough space to be understood without zooming.
- Keep long teaching copy and exact evidence outside the bitmap.
- Record model, prompt packet, source ids, learner question, dimensions, and asset verification.
- Keep generated explanation visually distinct from source evidence.

## Source Evidence

- Crop figures/tables tightly from the paper.
- Split composite figures when panel-level explanation is required.
- Put page, figure/table number, and linked source ids on the evidence slide or in its evidence panel.
- Preserve exact formulas, numerical values, axes, units, legends, and quotations.
- Add “查看原文依据” for important claims and verify the return target.

## Export

Use Playwright or another browser renderer to capture every fixed-stage slide at 1920x1080. Export one PNG per slide, then combine in order for PDF when requested. Verify at least four representative exports: title, image-led, evidence-led, and densest slide.

## Vercel

Deploy the static folder only after local strict audit and rendered screenshots pass. Use `Learn <paper short title>` as the public name unless the user provides another name. Verify the live URL, assets, keyboard navigation, and at least one evidence link.

## Optional Complete Reader

When the user asks for extensive original-text reading, use the existing reader runtime and `data/learning-site-manifest.json` contract. The deck remains the main explanation path; the reader becomes the detailed evidence layer. Run both `audit_learning_deck.py` and `audit_learning_site.py` when both artifacts are delivered.
