# Preflight Tools

Run a mode-aware tool preflight before extracting the source or building the output. Do not wait until the end to discover that PDF extraction, image generation, browser export, or deployment is unavailable.

## Required command

Run:

```bash
python3 /path/to/paper-and-book-to-visual-learning/scripts/resolve_image_route.py \
  --runtime codex \
  --receipt /path/to/real-image-receipt.json \
  --route-journal /path/to/image-route-journal.json

python3 /path/to/paper-and-book-to-visual-learning/scripts/preflight_learning_site.py \
  --mode image-series \
  --image-runtime codex \
  --image-route-receipt /path/to/real-image-receipt.json \
  --image-route-journal /path/to/image-route-journal.json
```

When a source file is already known, run the source-aware check:

```bash
python3 /path/to/paper-and-book-to-visual-learning/scripts/preflight_learning_site.py \
  --source /path/to/paper.pdf \
  --mode presentation-pdf \
  --image-runtime codex \
  --image-route-receipt /path/to/real-image-receipt.json \
  --image-route-journal /path/to/image-route-journal.json
```

Report:

- PDF/text extraction route
- source file readability when `--source` is provided
- figure rendering/cropping route
- a real image-generation route with a local raster receipt
- browser/screenshot verification route for PPT/HTML; image-series mode should not launch a browser unnecessarily
- Vercel route if deployment was requested
- the exact recommended Python executable from `recommended_commands.python`
- blockers and fallbacks

Use the reported `recommended_commands.python` for follow-up extraction/build scripts. Do not assume bare `python3` has the same PDF/image modules as the preflight route; on some machines, `python3` may point to Homebrew or system Python while `pdfplumber`, `pypdf`, or `Pillow` only exist in the bundled Codex runtime.

If `source.errors` says the PDF is unreadable, truncated, missing xref data, or has no extractable first-page text, stop before building the site. Ask for a repaired source or re-download the paper from an authoritative source, then rerun preflight with `--source`.

The shell preflight cannot prove image-generation availability from an environment variable or confirmation flag. It accepts only a real local raster receipt bound to a route-journal success event. In Codex, the system `imagegen` skill is the first route; the model name is learned from the real receipt rather than hardcoded.

Image generation availability has two levels:

1. generation route exists: the agent made a real call through the system `imagegen` route or another approved image tool.
2. local asset route exists: the generated bitmap can be saved into the selected output package and referenced by its mode-specific manifest.

Both must be true for a normal final build. If the tool only returns a chat preview, transient UI image, or no copyable local file path, report `blocked_by_local_image_generation_export` and stop before final delivery unless the user explicitly approves a lower-fidelity fallback. Do not continue by lowering `generated_visuals_expected` to `0`.

Image-series mode adds a third requirement:

3. direct final-page route exists: the model can generate the complete infographic with native Chinese text and save the untouched raster output. The workflow must preserve the raw output and generation receipt for hash comparison.

If the preferred route fails, first retry a transport failure according to the route state machine. In Codex, changing to CLI/API or another model/provider requires user confirmation. Outside Codex, detect configured alternatives and ask the user when several choices exist. Never silently build a post-composed substitute.

## Tool expectations

Prefer these routes:

- PDF metadata/text: `pdfinfo`, `pdftotext`, Python `pdfplumber`, or Python `pypdf`
- PDF page rendering: `pdftoppm` or a reliable Python/PDF rendering route
- image cropping/inspection: Python `Pillow`, `sips`, or ImageMagick
- generated teaching visuals: the Codex system `imagegen` tool first, or the verified external image route outside Codex
- browser QA: bundled Node Playwright with a launchable browser, preferably system Chrome through Playwright; Chrome CLI is only a fallback
- deployment: `vercel` CLI only when the user requested deployment

## Failure policy

- Missing text extraction: stop and ask for a readable source or install route.
- Unreadable source PDF: stop, repair/re-download the file, and rerun `preflight_learning_site.py --source ... --mode ...` before extracting text or figures.
- Missing figure rendering: continue only if figures are not required; otherwise report the blocker.
- Missing image generation or missing local bitmap export: stop before replacing requested generated images with SVG/manual boxes. In Codex, built-in failure requires user confirmation before CLI/API fallback.
- Missing browser automation: block PPT/HTML strict delivery; it is not a blocker for pure image-series mode.
- Playwright package present but no launchable browser: install Playwright browsers or use system Chrome through Playwright before claiming strict browser QA passed.

Do not claim any model name unless it actually produced the final local bitmap assets. Record the real tool, provider, model, request id, asset hash, receipt, and route journal in the selected mode's manifest.
