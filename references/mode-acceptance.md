# Mode Acceptance

Use this as the final routing gate. Passing one mode never substitutes for another mode's checks.

## Image Series

Required command:

```bash
python scripts/audit_visual_series.py <output-dir> --source <paper.pdf> --strict --require-pdf
```

Do not deliver unless it verifies direct model output and receipts, two separate opening maps, standalone Chinese OCR, public-copy quality, information density, visual variety, no duplicate pages, album PDF order, and at least two complete review/fix rounds.

## Presentation PDF

Required command:

```bash
python scripts/audit_learning_deck.py <work-dir> --source <paper.pdf> --strict --require-pdf
```

Do not deliver unless every page is 16:9, rendered without overflow or overlap, understandable without narration, Chinese-dominant, and complete without relying on a mechanical character quota. Browser geometry and edge-palette screenshot pixels must show adequate canvas use with no substantially blank lower half on normal body pages; at least 70% of body slides must contain an effective visual object; ordinary pages must keep source screenshots at or below 40% of the stage unless they are dedicated evidence pages; a 20-page deck must contain at least six materially different rendered layouts; and no same/similar structure may run for more than two consecutive teaching pages. Source figures must remain readable and explained, generated-image OCR must be clean, every generated bitmap must be bound to its real receipt/raw output/provider response, all planned generated/image-to-image assets must be fulfilled, and PDF order/rendering must match. PPTX OOXML must independently reproduce the geometry-family, image/source ratio, canvas-use, and lower-half checks, reject oversized one-line body boxes, and expose separate editable title and body/subtitle text shapes on slide 1. At least two complete review/fix rounds must be recorded. Manifest declarations are supporting evidence only, never the final proof of these checks.

## Interactive HTML

Required command:

```bash
python scripts/audit_learning_site.py <site-dir> --strict
```

Do not deliver unless complete/curated scope is explicit and verified against a full stable-id source inventory, every expected non-Chinese paragraph has original text plus faithful Chinese translation plus plain-language explanation, terms are inline, figures are placed and explained, learning-path links return to real source/evidence, every generated bitmap is bound to its real receipt/raw output/provider response, desktop/mobile interactions pass, public copy is clean, and at least two complete review/fix rounds are recorded.

## Shared Rule

Run cheap structure checks first and the selected mode's full strict command last. Report the exact audit result. Never call an artifact complete because another mode's audit passed.
