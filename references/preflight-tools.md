# Preflight Tools

Run a tool preflight before extracting the source or building the site. Do not wait until the end to discover that PDF extraction, Image 2 generation, or browser screenshots are unavailable.

## Required command

Run:

```bash
python3 /path/to/paper-to-learning-site/scripts/preflight_learning_site.py
```

Report:

- PDF/text extraction route
- figure rendering/cropping route
- Image 2 or image-generation route
- browser/screenshot verification route
- Vercel route if deployment was requested
- the exact recommended Python executable from `recommended_commands.python`
- blockers and fallbacks

Use the reported `recommended_commands.python` for follow-up extraction/build scripts. Do not assume bare `python3` has the same PDF/image modules as the preflight route; on some machines, `python3` may point to Homebrew or system Python while `pdfplumber`, `pypdf`, or `Pillow` only exist in the bundled Codex runtime.

The shell preflight cannot prove Image 2 availability by itself. It must report `manual_checks.image_generation`, and the main agent must confirm that the current Codex turn exposes an Image 2 or image generation tool before promising generated teaching diagrams.

## Tool expectations

Prefer these routes:

- PDF metadata/text: `pdfinfo`, `pdftotext`, Python `pdfplumber`, or Python `pypdf`
- PDF page rendering: `pdftoppm` or a reliable Python/PDF rendering route
- image cropping/inspection: Python `Pillow`, `sips`, or ImageMagick
- generated teaching visuals: Image 2 or the current image generation tool
- browser QA: Playwright with Chromium, or system Chrome headless screenshot
- deployment: `vercel` CLI only when the user requested deployment

## Failure policy

- Missing text extraction: stop and ask for a readable source or install route.
- Missing figure rendering: continue only if figures are not required; otherwise report the blocker.
- Missing Image 2/image generation: stop before replacing requested generated images with SVG/manual boxes.
- Missing browser automation: at minimum use system Chrome headless screenshot if available; otherwise state that visual QA is incomplete.

Do not claim that Image 2 was used unless an image-generation tool actually produced bitmap assets or the current environment records generated image outputs.
