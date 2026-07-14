# Preflight Tools

Run a mode-aware tool preflight before extracting the source or building the output. Do not wait until the end to discover that PDF extraction, image generation, browser export, or deployment is unavailable.

## Required command

Run:

```bash
python3 /path/to/paper-to-learning-site/scripts/preflight_learning_site.py --mode image-series --confirm-image-direct-output
```

When a source file is already known, run the source-aware check:

```bash
python3 /path/to/paper-to-learning-site/scripts/preflight_learning_site.py --source /path/to/paper.pdf --mode presentation-pdf
```

Report:

- PDF/text extraction route
- source file readability when `--source` is provided
- figure rendering/cropping route
- Image 2 or image-generation route
- browser/screenshot verification route for PPT/HTML; image-series mode should not launch a browser unnecessarily
- Vercel route if deployment was requested
- the exact recommended Python executable from `recommended_commands.python`
- blockers and fallbacks

Use the reported `recommended_commands.python` for follow-up extraction/build scripts. Do not assume bare `python3` has the same PDF/image modules as the preflight route; on some machines, `python3` may point to Homebrew or system Python while `pdfplumber`, `pypdf`, or `Pillow` only exist in the bundled Codex runtime.

If `source.errors` says the PDF is unreadable, truncated, missing xref data, or has no extractable first-page text, stop before building the site. Ask for a repaired source or re-download the paper from an authoritative source, then rerun preflight with `--source`.

The shell preflight cannot prove Image 2 availability by itself. It must report `manual_checks.image_generation`, and the main agent must confirm that the current Codex turn exposes an Image 2 or image generation tool before promising generated teaching diagrams.

Image generation availability has two levels:

1. generation route exists: the agent can call Image 2 or an approved image-generation tool.
2. local asset route exists: the generated bitmap can be saved into the selected output package and referenced by its mode-specific manifest.

Both must be true for a normal final build. If the tool only returns a chat preview, transient UI image, or no copyable local file path, report `blocked_by_local_image_generation_export` and stop before final delivery unless the user explicitly approves a lower-fidelity fallback. Do not continue by lowering `generated_visuals_expected` to `0`.

Image-series mode adds a third requirement:

3. direct final-page route exists: the model can generate the complete infographic with native Chinese text and save the untouched raster output. The workflow must preserve the raw output and generation receipt for hash comparison.

If the preferred model fails, detect another configured image model first. If no capable route exists, ask the user how to connect one; do not silently build a post-composed substitute.

## Tool expectations

Prefer these routes:

- PDF metadata/text: `pdfinfo`, `pdftotext`, Python `pdfplumber`, or Python `pypdf`
- PDF page rendering: `pdftoppm` or a reliable Python/PDF rendering route
- image cropping/inspection: Python `Pillow`, `sips`, or ImageMagick
- generated teaching visuals: Image 2 or the current image generation tool
- browser QA: bundled Node Playwright with a launchable browser, preferably system Chrome through Playwright; Chrome CLI is only a fallback
- deployment: `vercel` CLI only when the user requested deployment

## Failure policy

- Missing text extraction: stop and ask for a readable source or install route.
- Unreadable source PDF: stop, repair/re-download the file, and rerun `preflight_learning_site.py --source ... --mode ...` before extracting text or figures.
- Missing figure rendering: continue only if figures are not required; otherwise report the blocker.
- Missing Image 2/image generation, or missing local bitmap export for generated images: stop before replacing requested generated images with SVG/manual boxes.
- Missing browser automation: block PPT/HTML strict delivery; it is not a blocker for pure image-series mode.
- Playwright package present but no launchable browser: install Playwright browsers or use system Chrome through Playwright before claiming strict browser QA passed.

Do not claim that Image 2 was used unless it actually produced the final local bitmap assets. Record the real model in `learning-series-manifest.json`, `learning-deck-manifest.json`, or `learning-site-manifest.json` according to mode.
