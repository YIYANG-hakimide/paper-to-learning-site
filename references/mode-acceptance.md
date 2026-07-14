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

Do not deliver unless every page is 16:9, browser-rendered without overflow or overlap, understandable without narration, Chinese-dominant, source figures readable and explained, generated-image OCR clean, PDF order verified, and at least two complete review/fix rounds recorded.

## Interactive HTML

Required command:

```bash
python scripts/audit_learning_site.py <site-dir> --strict
```

Do not deliver unless complete/curated scope is explicit, every expected non-Chinese paragraph has original text plus faithful Chinese translation plus plain-language explanation, terms are inline, figures are placed and explained, learning-path links return to real source/evidence, desktop/mobile interactions pass, and public copy is clean.

## Shared Rule

Run cheap structure checks first and the selected mode's full strict command last. Report the exact audit result. Never call an artifact complete because another mode's audit passed.
