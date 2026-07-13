#!/usr/bin/env python3
"""Static quality checks for visual paper teaching decks."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image
except Exception:  # Pillow is recommended by preflight but keep the audit readable without it.
    Image = None


BITMAP_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
FORBIDDEN_PUBLIC_TEXT = (
    "面向无专业背景",
    "reader level",
    "prompt summary",
    "generated asset",
    "生成教学图资产",
    "preflight",
    "manifest",
    "regression",
)


def locate(input_path: Path) -> tuple[Path, Path]:
    if input_path.is_dir():
        return input_path, input_path / "index.html"
    return input_path.parent, input_path


def load_manifest(root: Path) -> dict:
    path = root / "data" / "learning-deck-manifest.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"_invalid": True}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def image_dimensions(path: Path) -> tuple[int, int] | None:
    if Image is None:
        return None


def normalized_hash(value: object) -> str:
    return str(value or "").replace("sha256:", "").strip().lower()


def browser_probe(html_path: Path, output_dir: Path) -> tuple[dict | None, str | None]:
    dependency_root = Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies"
    node = dependency_root / "node" / "bin" / "node"
    if not node.exists():
        found = shutil.which("node")
        if not found:
            return None, "Node.js is unavailable for browser rendering."
        node = Path(found)
    env = dict(os.environ)
    node_modules = dependency_root / "node" / "node_modules"
    if node_modules.exists():
        env["NODE_PATH"] = str(node_modules)
    chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    if chrome.exists():
        env["PLAYWRIGHT_CHROME_EXECUTABLE"] = str(chrome)
    output_dir.mkdir(parents=True, exist_ok=True)
    code = r"""
const { chromium } = require('playwright');
const path = require('path');
const { pathToFileURL } = require('url');
(async () => {
  const htmlPath = process.argv[1];
  const outputDir = process.argv[2];
  const executablePath = process.env.PLAYWRIGHT_CHROME_EXECUTABLE || undefined;
  const browser = await chromium.launch({ headless: true, executablePath, args: ['--no-first-run'] });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  await page.goto(pathToFileURL(htmlPath).href, { waitUntil: 'load' });
  await page.evaluate(() => document.fonts && document.fonts.ready);
  const count = await page.locator('.slide, [data-slide]').count();
  const results = [];
  for (let index = 0; index < count; index += 1) {
    await page.evaluate((activeIndex) => {
      const slides = [...document.querySelectorAll('.slide, [data-slide]')];
      slides.forEach((slide, i) => {
        slide.style.position = 'fixed';
        slide.style.inset = '0';
        slide.style.width = '1920px';
        slide.style.height = '1080px';
        slide.style.transform = 'none';
        slide.style.margin = '0';
        slide.style.visibility = i === activeIndex ? 'visible' : 'hidden';
        slide.style.opacity = i === activeIndex ? '1' : '0';
        slide.style.pointerEvents = i === activeIndex ? 'auto' : 'none';
        slide.style.zIndex = i === activeIndex ? '9999' : '-1';
      });
      document.documentElement.style.overflow = 'hidden';
      document.body.style.overflow = 'hidden';
      document.body.style.margin = '0';
    }, index);
    await page.waitForTimeout(30);
    const metrics = await page.locator('.slide, [data-slide]').nth(index).evaluate((slide) => {
      const brokenImages = [...slide.querySelectorAll('img')].filter(img => !img.complete || img.naturalWidth === 0).length;
      const images = [...slide.querySelectorAll('img')].map(img => {
        const box = img.getBoundingClientRect();
        return { width: Math.round(box.width), height: Math.round(box.height), naturalWidth: img.naturalWidth, naturalHeight: img.naturalHeight };
      });
      return {
        scrollWidth: slide.scrollWidth,
        scrollHeight: slide.scrollHeight,
        clientWidth: slide.clientWidth,
        clientHeight: slide.clientHeight,
        brokenImages,
        images
      };
    });
    const screenshot = path.join(outputDir, `slide-${String(index + 1).padStart(2, '0')}.png`);
    await page.screenshot({ path: screenshot, fullPage: false });
    results.push({ index: index + 1, screenshot, ...metrics });
  }
  await browser.close();
  process.stdout.write(JSON.stringify({ slideCount: count, results }));
})().catch(error => { console.error(error && error.stack ? error.stack : String(error)); process.exit(1); });
"""
    try:
        result = subprocess.run(
            [str(node), "-e", code, str(html_path), str(output_dir)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=180,
            env=env,
        )
    except Exception as exc:
        return None, f"Browser rendering failed to run: {exc}"
    if result.returncode != 0:
        return None, f"Browser rendering failed: {(result.stderr or result.stdout).strip()[:400]}"
    try:
        return json.loads(result.stdout), None
    except Exception as exc:
        return None, f"Browser rendering returned invalid JSON: {exc}"
    try:
        with Image.open(path) as image:
            return image.size
    except Exception:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a paper learning deck.")
    parser.add_argument("path", help="Deck directory or index.html")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--skip-browser", action="store_true")
    args = parser.parse_args()

    root, html_path = locate(Path(args.path).expanduser().resolve())
    errors: list[str] = []
    warnings: list[str] = []

    if not html_path.exists():
        errors.append(f"Missing HTML: {html_path}")
        html = ""
    else:
        html = html_path.read_text(encoding="utf-8", errors="replace")

    slides = re.findall(r'<(?:section|article)[^>]+(?:class=["\'][^"\']*\bslide\b|data-slide(?:=|\s))', html, re.I)
    if len(slides) < 8:
        errors.append(f"Too few detectable slides for a teaching deck: {len(slides)}")

    if "1920" not in html or "1080" not in html:
        warnings.append("Could not confirm a fixed 1920x1080 stage in HTML.")

    for token in FORBIDDEN_PUBLIC_TEXT:
        if token.lower() in html.lower():
            errors.append(f"Public HTML contains production wording: {token}")

    if "prefers-reduced-motion" not in html:
        warnings.append("Missing prefers-reduced-motion support.")

    if not re.search(r"(ArrowRight|ArrowLeft|keydown|下一页|上一页)", html, re.I):
        errors.append("No detectable keyboard or previous/next navigation.")

    image_refs = re.findall(r'<img\b[^>]*\bsrc=["\']([^"\']+)["\']', html, re.I)
    local_bitmap_refs = []
    for ref in image_refs:
        if ref.startswith(("data:", "http://", "https://")):
            continue
        asset = (root / ref.split("?", 1)[0].split("#", 1)[0]).resolve()
        if not asset.exists():
            errors.append(f"Missing image asset: {ref}")
            continue
        if asset.suffix.lower() in BITMAP_SUFFIXES:
            local_bitmap_refs.append(ref)

    manifest = load_manifest(root)
    if not manifest:
        errors.append("Missing data/learning-deck-manifest.json")
    elif manifest.get("_invalid"):
        errors.append("Invalid learning-deck-manifest.json")
    else:
        expected_slides = manifest.get("slides_expected")
        rendered_slides = manifest.get("slides_rendered")
        slide_items = manifest.get("slides", [])
        if isinstance(expected_slides, int) and isinstance(rendered_slides, int) and rendered_slides < expected_slides:
            errors.append(f"Manifest reports missing slides: {rendered_slides}/{expected_slides}")
        if isinstance(expected_slides, int) and len(slide_items) != expected_slides:
            errors.append(f"Manifest slide inventory does not match expected count: {len(slide_items)}/{expected_slides}")
        if rendered_slides != len(slides):
            errors.append(f"Rendered slide count does not match detectable HTML slides: manifest={rendered_slides}, html={len(slides)}")

        layout_counts: dict[str, int] = {}
        content_slide_count = 0
        for slide in slide_items:
            for field in ("id", "type", "learner_question", "one_sentence_answer", "layout_family"):
                if not slide.get(field):
                    errors.append(f"Slide inventory entry is missing {field}.")
            if slide.get("type") not in {"title", "divider", "recap", "evidence-appendix"}:
                content_slide_count += 1
                family = str(slide.get("layout_family", ""))
                layout_counts[family] = layout_counts.get(family, 0) + 1
        if content_slide_count and layout_counts:
            dominant_family, dominant_count = max(layout_counts.items(), key=lambda item: item[1])
            if dominant_count / content_slide_count > 0.60 and not manifest.get("layout_repetition_rationale"):
                errors.append(f"One layout family dominates {dominant_count}/{content_slide_count} teaching slides without rationale: {dominant_family}")

        visuals = manifest.get("generated_visuals", [])
        expected_visuals = manifest.get("generated_visuals_expected")
        hard_concepts = [item for item in manifest.get("hard_concepts", []) if item.get("visual_needed", True)]
        logic_units = manifest.get("logic_units", [])
        derived_visual_floor = max(len(hard_concepts), len(logic_units))
        if isinstance(expected_visuals, int) and expected_visuals < derived_visual_floor:
            errors.append(f"generated_visuals_expected is below the derived concept/chapter floor: {expected_visuals}/{derived_visual_floor}")
        if isinstance(expected_visuals, int) and len(visuals) < expected_visuals:
            errors.append(f"Generated visual coverage is incomplete: {len(visuals)}/{expected_visuals}")
        if expected_visuals == 0:
            errors.append("generated_visuals_expected=0 bypasses the visual-first deck contract.")

        seen_hashes: dict[str, str] = {}
        for item in visuals:
            rel = item.get("path", "")
            model = str(item.get("model_name", "")).strip()
            if not rel:
                errors.append("Generated visual is missing a path.")
                continue
            asset = root / rel
            if asset.suffix.lower() not in BITMAP_SUFFIXES or not asset.exists():
                errors.append(f"Generated visual is not a real local bitmap: {rel}")
            else:
                actual_hash = sha256(asset)
                declared_hash = str(item.get("asset_sha256", "")).replace("sha256:", "")
                if not declared_hash:
                    errors.append(f"Generated visual is missing asset_sha256: {rel}")
                elif declared_hash != actual_hash:
                    errors.append(f"Generated visual hash mismatch: {rel}")
                if actual_hash in seen_hashes:
                    errors.append(f"Duplicate generated visual bitmap reused for different entries: {seen_hashes[actual_hash]} and {rel}")
                else:
                    seen_hashes[actual_hash] = rel
                dimensions = image_dimensions(asset)
                if dimensions:
                    width, height = dimensions
                    if width < 1024 or height < 576:
                        errors.append(f"Generated visual resolution is too small for a deck: {rel} ({width}x{height})")
                    if item.get("width_px") != width or item.get("height_px") != height:
                        errors.append(f"Generated visual dimensions are missing or incorrect in manifest: {rel}")
            if rel not in image_refs:
                errors.append(f"Generated visual is not embedded in HTML: {rel}")
            if not model or model.lower() in {"manual", "placeholder", "unknown", "unavailable"}:
                errors.append(f"Generated visual has no real image model provenance: {rel}")
            for field in (
                "teaches_concept",
                "learner_question",
                "linked_source_ids",
                "slide_id",
                "embedded_selector",
                "display_width_px",
                "display_height_px",
                "reviewer_status",
            ):
                if not item.get(field):
                    errors.append(f"Generated visual {rel} is missing {field}.")
            if item.get("crop_checked") is not True:
                errors.append(f"Generated visual has not passed crop inspection: {rel}")
            expected_labels = item.get("expected_labels", [])
            if expected_labels and not item.get("ocr_pass"):
                errors.append(f"Generated visual with text has not passed OCR label comparison: {rel}")
            if item.get("display_width_px", 0) < 700 or item.get("display_height_px", 0) < 390:
                errors.append(f"Generated visual is displayed too small to be a primary teaching object: {rel}")

        source = manifest.get("source_fidelity", {})
        inventory_rel = source.get("inventory_path") if isinstance(source, dict) else None
        inventory = {}
        source_ids: set[str] = set()
        if not inventory_rel:
            errors.append("Source fidelity is missing inventory_path.")
        else:
            inventory_path = root / str(inventory_rel)
            if not inventory_path.exists():
                errors.append(f"Source inventory file does not exist: {inventory_rel}")
            else:
                try:
                    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
                    blocks = inventory.get("all_main_text_blocks", [])
                    source_ids = {str(block.get("source_id")) for block in blocks if block.get("source_id")}
                    if len(blocks) != source.get("main_text_total_blocks"):
                        errors.append("Source inventory block count does not match source_fidelity.main_text_total_blocks.")
                    declared_inventory_hash = normalized_hash(source.get("main_text_inventory_sha256"))
                    if not declared_inventory_hash or declared_inventory_hash != sha256(inventory_path):
                        errors.append("Source inventory hash is missing or does not match the inventory file.")
                    pages = sorted({block.get("page") for block in blocks if isinstance(block.get("page"), int)})
                    expected_pages = inventory.get("main_text_page_count")
                    page_start = inventory.get("main_text_page_start", 1)
                    page_end = page_start + expected_pages - 1 if expected_pages else None
                    if page_end and pages and (pages[0] > page_start or pages[-1] < page_end or set(range(page_start, page_end + 1)) - set(pages)):
                        errors.append("Source inventory page coverage is incomplete or non-contiguous.")
                except Exception:
                    errors.append(f"Source inventory is invalid JSON: {inventory_rel}")

        for slide in slide_items:
            for source_id in slide.get("source_ids", []):
                if source_ids and str(source_id) not in source_ids:
                    errors.append(f"Slide references a missing source id: {source_id}")

        claims = manifest.get("claim_evidence_map", [])
        for claim in claims:
            for field in (
                "claim_role",
                "claim_dom_id",
                "source_ids",
                "comparison_baseline",
                "metric_or_dimension",
                "direction_or_value",
                "evidence_items",
                "limitation",
            ):
                if not claim.get(field):
                    errors.append(f"Claim evidence entry is missing {field}.")
            for source_id in claim.get("source_ids", []):
                if source_ids and str(source_id) not in source_ids:
                    errors.append(f"Claim references a missing source id: {source_id}")
            evidence_items = claim.get("evidence_items", [])
            for evidence in evidence_items:
                for field in ("evidence_id", "evidence_kind", "dom_id", "supports_vs_illustrates"):
                    if not evidence.get(field):
                        errors.append(f"Claim evidence item is missing {field}.")
            if claim.get("claim_role") == "supported_conclusion":
                supporting = [item for item in evidence_items if item.get("supports_vs_illustrates") == "supports" and item.get("evidence_kind") != "generated_visual"]
                if not supporting:
                    errors.append("A supported conclusion has no non-generated supporting evidence.")

        if not source.get("main_text_total_blocks"):
            errors.append("Manifest lacks a complete main-text source inventory.")

        style = manifest.get("design_brief", {})
        for field in (
            "paper_motif",
            "motif_source_basis",
            "visual_direction",
            "typography_plan",
            "evidence_style",
            "forbidden_styles",
            "layout_families",
            "preview_choice_reason",
        ):
            if not style.get(field):
                errors.append(f"Design brief is missing {field}.")

        qa = manifest.get("qa", {})
        for field in ("fixed_stage_checked", "all_slides_rendered", "small_viewport_checked", "visual_inspection_complete"):
            if qa.get(field) is not True:
                errors.append(f"Deck QA has not passed {field}.")
        if len(qa.get("adversarial_passes", [])) < 3:
            errors.append("Deck QA does not record all three adversarial review passes.")

    if len(local_bitmap_refs) < 4:
        warnings.append(f"Only {len(local_bitmap_refs)} local bitmap images are embedded; visual-first coverage may be weak.")

    if args.skip_browser:
        warnings.append("Browser rendering was skipped; slide screenshots and runtime geometry were not verified.")
    elif html_path.exists():
        probe, probe_error = browser_probe(html_path, root / "qa" / "screenshots")
        if probe_error:
            errors.append(probe_error)
        elif probe:
            if probe.get("slideCount") != len(slides):
                errors.append("Browser-rendered slide count does not match static slide count.")
            for result in probe.get("results", []):
                index = result.get("index")
                if result.get("brokenImages"):
                    errors.append(f"Slide {index} has broken images in browser rendering.")
                if result.get("scrollWidth", 0) > result.get("clientWidth", 0) + 2 or result.get("scrollHeight", 0) > result.get("clientHeight", 0) + 2:
                    errors.append(f"Slide {index} overflows its 1920x1080 stage.")
                for image in result.get("images", []):
                    if image.get("width", 0) < 160 or image.get("height", 0) < 90:
                        errors.append(f"Slide {index} contains an unreadably small rendered image: {image.get('width')}x{image.get('height')}.")

    if args.strict:
        errors.extend(warnings)
        warnings = []
    else:
        warnings.extend(errors)
        errors = []

    print(json.dumps({"errors": errors, "warnings": warnings, "summary": {"errors": len(errors), "warnings": len(warnings)}}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
