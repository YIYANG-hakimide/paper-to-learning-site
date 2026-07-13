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
    try:
        with Image.open(path) as image:
            return image.size
    except Exception:
        return None


def normalized_hash(value: object) -> str:
    return str(value or "").replace("sha256:", "").strip().lower()


def command_path(name: str) -> str | None:
    dependency_root = Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies"
    for candidate in (dependency_root / "bin" / "override" / name, dependency_root / "bin" / name):
        if candidate.exists():
            return str(candidate)
    return shutil.which(name)


def validate_pdf(pdf_path: Path, expected_pages: int, qa_dir: Path) -> list[str]:
    issues: list[str] = []
    if not pdf_path.exists() or pdf_path.stat().st_size < 1024:
        return ["Final presentation PDF is missing or suspiciously small."]
    if not pdf_path.read_bytes()[:5] == b"%PDF-":
        issues.append("Final presentation export is not a valid PDF file.")
        return issues
    pdfinfo = command_path("pdfinfo")
    if not pdfinfo:
        issues.append("pdfinfo is unavailable; final PDF page count and dimensions cannot be verified.")
        return issues
    result = subprocess.run([pdfinfo, str(pdf_path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
    if result.returncode != 0:
        issues.append(f"pdfinfo could not read final PDF: {(result.stderr or result.stdout).strip()[:240]}")
        return issues
    pages_match = re.search(r"^Pages:\s+(\d+)", result.stdout, re.M)
    pages = int(pages_match.group(1)) if pages_match else None
    if pages != expected_pages:
        issues.append(f"Final PDF page count does not match deck: pdf={pages}, slides={expected_pages}.")
    size_match = re.search(r"^Page size:\s+([0-9.]+)\s+x\s+([0-9.]+)", result.stdout, re.M)
    if not size_match:
        issues.append("Could not verify final PDF page dimensions.")
    else:
        width, height = float(size_match.group(1)), float(size_match.group(2))
        if height <= 0 or abs((width / height) - (16 / 9)) > 0.03:
            issues.append(f"Final PDF page ratio is not 16:9: {width}x{height}.")
    renderer = command_path("pdftoppm")
    if renderer and pages:
        qa_dir.mkdir(parents=True, exist_ok=True)
        for page_number in sorted({1, max(1, (pages + 1) // 2), pages}):
            output_stem = qa_dir / f"pdf-page-{page_number:03d}"
            render = subprocess.run(
                [renderer, "-f", str(page_number), "-l", str(page_number), "-singlefile", "-png", "-r", "72", str(pdf_path), str(output_stem)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=60,
            )
            rendered = output_stem.with_suffix(".png")
            if render.returncode != 0 or not rendered.exists() or rendered.stat().st_size < 1024:
                issues.append(f"Failed to render representative PDF page {page_number}.")
    return issues


def audit_teaching_coverage(root: Path, manifest: dict, size_mode: str, html: str, errors: list[str]) -> int:
    meta = manifest.get("teaching_fidelity", {})
    rel = meta.get("inventory_path")
    if not rel or not (root / str(rel)).exists():
        errors.append("Missing data/teaching-inventory.json or teaching_fidelity.inventory_path.")
        return 0
    path = root / str(rel)
    try:
        inventory = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        errors.append("Teaching inventory is invalid JSON.")
        return 0
    if normalized_hash(meta.get("inventory_sha256")) != sha256(path):
        errors.append("Teaching inventory hash is missing or incorrect.")
    if inventory.get("derivation_checked") is not True or inventory.get("reviewer_status") != "passed":
        errors.append("Teaching inventory derivation/review has not passed.")
    if normalized_hash(inventory.get("source_inventory_sha256")) != normalized_hash(manifest.get("source_fidelity", {}).get("main_text_inventory_sha256")):
        errors.append("Teaching inventory is not linked to the current source inventory hash.")
    if not inventory.get("hard_concepts"):
        errors.append("Teaching inventory must identify at least one hard concept.")
    if not inventory.get("central_claims"):
        errors.append("Teaching inventory must identify at least one central claim.")
    groups = {
        "hard_concepts": "hard_concept_coverage",
        "formula_or_algorithm_items": "formula_coverage",
        "experiments": "experiment_coverage",
        "major_figures": "major_figure_coverage",
        "central_claims": "central_claim_coverage",
    }
    for inventory_key, coverage_key in groups.items():
        entries = inventory.get(inventory_key)
        coverage = manifest.get(coverage_key)
        if not isinstance(entries, list):
            errors.append(f"Teaching inventory must contain {inventory_key}[].")
            continue
        if not isinstance(coverage, list):
            errors.append(f"Manifest must contain {coverage_key}[].")
            continue
        by_id = {str(item.get("inventory_id")): item for item in coverage if isinstance(item, dict) and item.get("inventory_id")}
        for entry in entries:
            item_id = str(entry.get("id", ""))
            item = by_id.get(item_id)
            if not item:
                errors.append(f"Teaching inventory item has no coverage entry: {inventory_key}:{item_id}")
                continue
            status = item.get("status")
            level = entry.get("required_level", "core")
            omission_allowed = level == "secondary" or (level == "major" and size_mode == "concise")
            if status == "omitted":
                if not omission_allowed or not item.get("reason"):
                    errors.append(f"Required teaching item was omitted without an allowed reason: {inventory_key}:{item_id}")
            elif status != "covered" or not item.get("final_item_ids"):
                errors.append(f"Teaching coverage must be covered with final_item_ids: {inventory_key}:{item_id}")
    central_claim_ids = {str(item.get("id")) for item in inventory.get("central_claims", []) if item.get("id")}
    bundles = manifest.get("evidence_bundles", [])
    bundle_claim_ids = {str(item.get("claim_id")) for item in bundles if isinstance(item, dict) and item.get("claim_id")}
    missing = central_claim_ids - bundle_claim_ids
    if missing:
        errors.append(f"Central claims are missing evidence bundles: {sorted(missing)}")
    for bundle in bundles:
        for field in ("bundle_id", "claim_id", "final_item_ids", "source_ids", "source_excerpt_or_asset", "visible_source_cue", "chinese_explanation", "evidence_meaning", "limitation", "source_cue_dom_id"):
            if not bundle.get(field):
                errors.append(f"Evidence bundle is missing {field}.")
        cue_id = str(bundle.get("source_cue_dom_id", ""))
        if cue_id and not re.search(rf'id=["\']{re.escape(cue_id)}["\']', html):
            errors.append(f"Evidence bundle source cue is not visible in HTML: {cue_id}")
    levels = {"concise": {"core"}, "medium": {"core", "major"}, "detailed": {"core", "major", "secondary"}}
    return sum(
        1
        for item in inventory.get("hard_concepts", [])
        if item.get("visual_needed") is True and item.get("required_level", "core") in levels.get(size_mode, {"core"})
    )


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
      const generatedVisuals = [...slide.querySelectorAll('[data-generated-visual-id] img, img[data-generated-visual-id], figure[data-generated-visual-id] img')].map(img => {
        const box = img.getBoundingClientRect();
        return { width: Math.round(box.width), height: Math.round(box.height), areaRatio: (box.width * box.height) / (1920 * 1080) };
      });
      const bodyText = [...slide.querySelectorAll('h1,h2,h3,p,li,blockquote,td,th,.label,.caption')]
        .filter(el => !el.closest('.footnote,.citation,footer'));
      const projectedFonts = bodyText.map(el => parseFloat(getComputedStyle(el).fontSize || '0') * (1366 / 1920)).filter(Boolean);
      const nestedCards = slide.querySelectorAll('[class~="card"] [class~="card"], [data-card] [data-card]').length;
      return {
        scrollWidth: slide.scrollWidth,
        scrollHeight: slide.scrollHeight,
        clientWidth: slide.clientWidth,
        clientHeight: slide.clientHeight,
        brokenImages,
        images,
        generatedVisuals,
        textChars: (slide.innerText || '').replace(/\s+/g, '').length,
        projectedMinBodyPx: projectedFonts.length ? Math.min(...projectedFonts) : null,
        nestedCards
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
def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a paper learning deck.")
    parser.add_argument("path", help="Deck directory or index.html")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--skip-browser", action="store_true")
    parser.add_argument("--require-pdf", action="store_true", help="Require the final presentation PDF export")
    args = parser.parse_args()

    root, html_path = locate(Path(args.path).expanduser().resolve())
    errors: list[str] = []
    warnings: list[str] = []

    if not html_path.exists():
        errors.append(f"Missing HTML: {html_path}")
        html = ""
    else:
        html = html_path.read_text(encoding="utf-8", errors="replace")

    slide_tags = re.findall(r'<(?:section|article)[^>]+(?:class=["\'][^"\']*\bslide\b|data-slide(?:=|\s))[^>]*>', html, re.I)
    slides = slide_tags
    html_slide_ids = []
    for tag in slide_tags:
        match = re.search(r'data-slide-id=["\']([^"\']+)["\']', tag, re.I)
        if match:
            html_slide_ids.append(match.group(1))
    if len(slides) < 6:
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
        if str(manifest.get("manifest_schema_version")) != "0.3":
            errors.append("Deck manifest schema version must be 0.3.")
        if manifest.get("output_mode") != "presentation-pdf":
            errors.append("Deck manifest output_mode must be presentation-pdf.")
        size_mode = manifest.get("size_mode")
        if size_mode not in {"concise", "medium", "detailed"}:
            errors.append("Deck manifest must record resolved size_mode.")
        if manifest.get("size_mode_requested") == "automatic":
            sizing = manifest.get("automatic_sizing", {})
            for field in ("complexity_score", "score_breakdown", "target_min", "target_max", "maximum_count", "resolved_count", "rationale"):
                if sizing.get(field) in (None, "", []):
                    errors.append(f"Automatic sizing is missing {field}.")
        expected_slides = manifest.get("slides_expected")
        rendered_slides = manifest.get("slides_rendered")
        slide_items = manifest.get("slides", [])
        manifest_slide_ids = [str(item.get("id")) for item in slide_items if item.get("id")]
        if manifest.get("size_mode_requested") == "automatic":
            sizing = manifest.get("automatic_sizing", {})
            if sizing.get("resolved_count") != len(slide_items) or not sizing.get("target_min", 0) <= len(slide_items) <= sizing.get("target_max", 0):
                errors.append("Automatic page count is outside its recorded target range or resolved_count.")
        if isinstance(expected_slides, int) and isinstance(rendered_slides, int) and rendered_slides < expected_slides:
            errors.append(f"Manifest reports missing slides: {rendered_slides}/{expected_slides}")
        if isinstance(expected_slides, int) and len(slide_items) != expected_slides:
            errors.append(f"Manifest slide inventory does not match expected count: {len(slide_items)}/{expected_slides}")
        if rendered_slides != len(slides):
            errors.append(f"Rendered slide count does not match detectable HTML slides: manifest={rendered_slides}, html={len(slides)}")
        if len(html_slide_ids) != len(slides):
            errors.append("Every HTML slide must have a stable data-slide-id.")
        elif html_slide_ids != manifest_slide_ids:
            errors.append("HTML data-slide-id order does not match manifest slide order.")
        if size_mode == "concise" and (len(slide_items) > 10 or (len(slide_items) < 6 and not manifest.get("shorter_user_approved"))):
            errors.append("Concise presentation must contain 6-10 pages unless a shorter set was explicitly approved.")
        if size_mode == "medium" and not 11 <= len(slide_items) <= 20:
            errors.append("Medium presentation must contain 11-20 pages.")
        if size_mode == "detailed" and len(slide_items) < 21:
            errors.append("Detailed presentation must contain at least 21 pages.")
        if len(slide_items) > 36 and not manifest.get("over_36_user_approved"):
            errors.append("Presentation exceeds 36 pages without explicit approval.")
        derived_teaching_visual_floor = audit_teaching_coverage(root, manifest, size_mode, html, errors)

        storyboard_meta = manifest.get("storyboard", {})
        storyboard_rel = storyboard_meta.get("path")
        storyboard = {}
        if not storyboard_rel:
            errors.append("Manifest is missing storyboard.path.")
        else:
            storyboard_path = root / str(storyboard_rel)
            if not storyboard_path.exists():
                errors.append(f"Storyboard file does not exist: {storyboard_rel}")
            else:
                try:
                    storyboard = json.loads(storyboard_path.read_text(encoding="utf-8"))
                    declared_storyboard_hash = normalized_hash(storyboard_meta.get("sha256"))
                    if not declared_storyboard_hash or declared_storyboard_hash != sha256(storyboard_path):
                        errors.append("Storyboard hash is missing or does not match the storyboard file.")
                except Exception:
                    errors.append(f"Storyboard is invalid JSON: {storyboard_rel}")
        if storyboard_meta.get("locked_before_final_generation") is not True:
            errors.append("Storyboard was not locked before final teaching-image generation.")
        storyboard_slides = storyboard.get("slides", []) if isinstance(storyboard, dict) else []
        storyboard_slide_ids = [str(item.get("id")) for item in storyboard_slides if item.get("id")]
        declared_storyboard_order = [str(item) for item in storyboard_meta.get("slide_id_order", [])]
        if storyboard_slide_ids != manifest_slide_ids or declared_storyboard_order != manifest_slide_ids:
            errors.append("Storyboard, manifest, and declared slide-id order do not match exactly.")
        acts = storyboard.get("acts", []) if isinstance(storyboard, dict) else []
        if len(acts) < 3:
            errors.append("Storyboard has too few teaching acts to establish a coherent learning arc.")
        required_arc_roles = {"problem", "prerequisite", "method", "evidence", "limitation"}
        arc_roles = {str(item.get("learning_role")) for item in acts if item.get("learning_role")}
        if not required_arc_roles.issubset(arc_roles):
            errors.append("Storyboard does not cover the complete problem/prerequisite/method/evidence/limitation arc.")

        layout_counts: dict[str, int] = {}
        content_slide_count = 0
        evidence_dense_streak = 0
        max_evidence_dense_streak = 0
        low_density_count = 0
        section_reset_count = 0
        for slide in slide_items:
            for field in ("id", "type", "learner_question", "one_sentence_answer", "layout_family"):
                if not slide.get(field):
                    errors.append(f"Slide inventory entry is missing {field}.")
            for field in ("presentation_beat", "spoken_takeaway", "density_class", "reveal_order", "estimated_seconds"):
                if slide.get("type") not in {"title", "evidence-appendix"} and slide.get(field) in (None, "", []):
                    errors.append(f"Presentation slide {slide.get('id')} is missing {field}.")
            if slide.get("type") not in {"title", "evidence-appendix"} and "section_reset" not in slide:
                errors.append(f"Presentation slide {slide.get('id')} is missing section_reset.")
            density = slide.get("density_class")
            if density == "evidence-dense":
                evidence_dense_streak += 1
                max_evidence_dense_streak = max(max_evidence_dense_streak, evidence_dense_streak)
            else:
                evidence_dense_streak = 0
            if density == "low":
                low_density_count += 1
            if slide.get("section_reset") is True:
                section_reset_count += 1
            if slide.get("estimated_seconds") not in (None, "") and (not isinstance(slide.get("estimated_seconds"), (int, float)) or slide.get("estimated_seconds") <= 0):
                errors.append(f"Presentation slide {slide.get('id')} has invalid estimated_seconds.")
            if slide.get("type") not in {"title", "divider", "recap", "evidence-appendix"}:
                content_slide_count += 1
                family = str(slide.get("layout_family", ""))
                layout_counts[family] = layout_counts.get(family, 0) + 1
        if content_slide_count and layout_counts:
            dominant_family, dominant_count = max(layout_counts.items(), key=lambda item: item[1])
            if dominant_count / content_slide_count > 0.60 and not manifest.get("layout_repetition_rationale"):
                errors.append(f"One layout family dominates {dominant_count}/{content_slide_count} teaching slides without rationale: {dominant_family}")
        if max_evidence_dense_streak > 3:
            errors.append("Presentation contains more than three consecutive evidence-dense pages without a reset.")
        if low_density_count == 0:
            errors.append("Presentation has no low-density emphasis or transition page.")
        if size_mode in {"medium", "detailed"} and section_reset_count < 2:
            errors.append("Medium/detailed presentation needs at least two visible section resets.")

        visuals = manifest.get("generated_visuals", [])
        expected_visuals = manifest.get("generated_visuals_expected")
        hard_concepts = [item for item in manifest.get("hard_concepts", []) if item.get("visual_needed", True)]
        logic_units = manifest.get("logic_units", [])
        derived_visual_floor = max(len(hard_concepts), len(logic_units), derived_teaching_visual_floor)
        if isinstance(expected_visuals, int) and expected_visuals < derived_visual_floor:
            errors.append(f"generated_visuals_expected is below the derived concept/chapter floor: {expected_visuals}/{derived_visual_floor}")
        if isinstance(expected_visuals, int) and len(visuals) < expected_visuals:
            errors.append(f"Generated visual coverage is incomplete: {len(visuals)}/{expected_visuals}")
        if expected_visuals == 0:
            errors.append("generated_visuals_expected=0 bypasses the visual-first deck contract.")

        seen_hashes: dict[str, str] = {}
        visual_ownership: dict[str, list[str]] = {}
        for slide in slide_items:
            visual_id = slide.get("owned_visual_id") or slide.get("visual_id")
            if visual_id:
                visual_ownership.setdefault(str(visual_id), []).append(str(slide.get("id")))
        for item in visuals:
            rel = item.get("path", "")
            model = str(item.get("model_name", "")).strip()
            visual_id = str(item.get("id", ""))
            if not visual_id:
                errors.append(f"Generated visual is missing id: {rel or '[no path]'}")
            owners = visual_ownership.get(visual_id, [])
            if len(owners) != 1:
                errors.append(f"Generated visual must have exactly one owning slide: {visual_id or rel} owners={owners}")
            elif item.get("slide_id") != owners[0]:
                errors.append(f"Generated visual slide_id does not match its owning slide: {visual_id or rel}")
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
            if not claim.get("visible_source_cue") or not claim.get("source_cue_dom_id"):
                errors.append("Claim evidence entry lacks a reader-visible source cue.")
            elif not re.search(rf'id=["\']{re.escape(str(claim.get("source_cue_dom_id")))}["\']', html):
                errors.append(f"Claim source cue DOM id is not visible in HTML: {claim.get('source_cue_dom_id')}")
            if claim.get("claim_role") == "supported_conclusion":
                supporting = [item for item in evidence_items if item.get("supports_vs_illustrates") == "supports" and item.get("evidence_kind") != "generated_visual"]
                if not supporting:
                    errors.append("A supported conclusion has no non-generated supporting evidence.")

        if not source.get("main_text_total_blocks"):
            errors.append("Manifest lacks a complete main-text source inventory.")

        style = manifest.get("design_brief", {})
        for field in (
            "art_direction_thesis",
            "paper_motif",
            "motif_source_basis",
            "topic_specific_objects",
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
        for field in (
            "fixed_stage_checked",
            "all_slides_rendered",
            "small_viewport_checked",
            "visual_inspection_complete",
            "full_deck_contact_sheet_checked",
            "presentation_read_aloud_checked",
            "presentation_rhythm_checked",
            "projected_legibility_checked",
        ):
            if qa.get(field) is not True:
                errors.append(f"Deck QA has not passed {field}.")
        if qa.get("orphan_generated_visuals") != 0:
            errors.append("Deck QA reports orphan generated visuals.")
        if len(qa.get("adversarial_passes", [])) < 3:
            errors.append("Deck QA does not record all three adversarial review passes.")
        contact_sheet_rel = qa.get("contact_sheet_path")
        if not contact_sheet_rel or not (root / str(contact_sheet_rel)).exists():
            errors.append("Deck QA does not provide a real full-deck contact sheet.")
        elif Image is not None:
            try:
                with Image.open(root / str(contact_sheet_rel)) as contact_sheet:
                    contact_sheet.verify()
            except Exception:
                errors.append("Full-deck contact sheet is not a valid image.")
        qa_report_path = root / "qa" / "qa-report.json"
        if not qa_report_path.exists():
            errors.append("Missing qa/qa-report.json.")
        else:
            try:
                qa_report = json.loads(qa_report_path.read_text(encoding="utf-8"))
            except Exception:
                qa_report = {}
            if not qa_report:
                errors.append("Invalid qa/qa-report.json.")
            else:
                if qa_report.get("final_status") not in {"passed", "clean"}:
                    errors.append("QA report final_status is not passed/clean.")
                if qa_report.get("unresolved_blockers") or qa_report.get("remaining_errors"):
                    errors.append("QA report still contains unresolved blockers or errors.")
        if args.require_pdf:
            exports = manifest.get("exports", {})
            pdf_rel = exports.get("pdf_path")
            if not pdf_rel:
                errors.append("Final presentation PDF export is missing.")
            else:
                pdf_path = root / str(pdf_rel)
                errors.extend(validate_pdf(pdf_path, len(slide_items), root / "qa" / "pdf-render-check"))
                declared_pdf_hash = normalized_hash(exports.get("pdf_sha256"))
                if pdf_path.exists() and (not declared_pdf_hash or declared_pdf_hash != sha256(pdf_path)):
                    errors.append("Final PDF hash is missing or does not match the exported file.")

    if len(local_bitmap_refs) < 4:
        warnings.append(f"Only {len(local_bitmap_refs)} local bitmap images are embedded; visual-first coverage may be weak.")

    visual_root = root / "assets" / "visuals"
    if visual_root.exists() and manifest and not manifest.get("_invalid"):
        declared_paths = {str(item.get("path")) for item in manifest.get("generated_visuals", []) if item.get("path")}
        packaged_paths = {
            str(path.relative_to(root))
            for path in visual_root.rglob("*")
            if path.is_file()
            and path.suffix.lower() in BITMAP_SUFFIXES
            and "previews" not in path.parts
            and "rejected" not in path.parts
        }
        orphan_paths = sorted(packaged_paths - declared_paths)
        if orphan_paths:
            errors.append(f"assets/visuals contains orphan bitmaps not owned by manifest slides: {orphan_paths[:8]}")

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
                generated = result.get("generatedVisuals", [])
                if generated and max(item.get("areaRatio", 0) for item in generated) < 0.20:
                    errors.append(f"Slide {index} generated teaching visual occupies less than 20% of the page.")
                if result.get("textChars", 0) > 900:
                    errors.append(f"Slide {index} is too text-dense for presentation mode: {result.get('textChars')} visible characters.")
                if result.get("projectedMinBodyPx") is not None and result.get("projectedMinBodyPx") < 12:
                    errors.append(f"Slide {index} body text becomes too small at 1366x768 projection: {result.get('projectedMinBodyPx'):.1f}px.")
                if result.get("nestedCards", 0) > 0:
                    errors.append(f"Slide {index} contains nested card-like components, which harms presentation hierarchy.")

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
