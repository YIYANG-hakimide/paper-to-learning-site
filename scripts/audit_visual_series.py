#!/usr/bin/env python3
"""Strict static checks for ordered paper explainer image series."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image, ImageChops, ImageStat
except Exception:
    Image = None
    ImageChops = None
    ImageStat = None


BITMAP_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
FORBIDDEN_PUBLIC_PATTERNS = (
    (r"面向无专业背景(?:大学生)?|面向初学者", "audience targeting"),
    (r"本页旨在|这里需要(?:让|告诉)(?:用户|读者)|需要让(?:用户|读者)", "internal teaching intent"),
    (r"生成教学图|generated asset|prompt summary|image prompt|manifest|preflight|regression|测试页|回归样本", "production language"),
    (r"值得注意的是|不难发现|接下来(?:我们)?(?:将)?深入|由此可见", "generic transition"),
    (r"赋能|颠覆|全新范式|革命性|重塑", "inflated generic wording"),
)


def chinese_ratio(text: str) -> float:
    chinese = len(re.findall(r"[\u3400-\u9fff]", text))
    latin = len(re.findall(r"[A-Za-z]", text))
    return chinese / max(1, chinese + latin)


def public_copy_issues(text: str) -> list[str]:
    issues: list[str] = []
    for pattern, label in FORBIDDEN_PUBLIC_PATTERNS:
        if re.search(pattern, text, re.I):
            issues.append(label)
    if len(re.findall(r"不是[^。！？\n]{0,36}而是", text)) > 1:
        issues.append("repeated not-but contrast syntax")
    if len(re.findall(r"不仅[^。！？\n]{0,36}(?:更|还)", text)) > 1:
        issues.append("repeated not-only contrast syntax")
    if len(re.findall(r"从[^。！？\n]{1,24}到[^。！？\n]{1,24}", text)) > 3:
        issues.append("repeated from-to framing")
    return issues


def validate_native_generation_contract(item: dict, asset: Path | None = None, root: Path | None = None) -> list[str]:
    issues: list[str] = []
    if item.get("production_method") != "model-single-pass":
        issues.append("production_method must be model-single-pass")
    integration = item.get("text_integration", {})
    if integration.get("mode") != "in-model":
        issues.append("text_integration.mode must be in-model")
    if integration.get("planned_before_generation") is not True:
        issues.append("in-model text was not planned before generation")
    provenance = item.get("generation_provenance", {})
    for field in (
        "provider",
        "model",
        "request_id",
        "prompt_sha256",
        "run_receipt_path",
        "run_receipt_sha256",
        "provider_response_path",
        "provider_response_sha256",
        "raw_output_path",
        "raw_output_sha256",
    ):
        if not provenance.get(field):
            issues.append(f"generation_provenance is missing {field}")
    if provenance.get("final_asset_is_direct_output") is not True:
        issues.append("final_asset_is_direct_output must be true")
    if item.get("model_name") and provenance.get("model") and str(item.get("model_name")) != str(provenance.get("model")):
        issues.append("model_name does not match generation_provenance.model")
    if provenance.get("pixel_postprocess_operations") not in ([], None):
        issues.append("pixel_postprocess_operations must be empty")
    if provenance.get("pixel_postprocess_operations") is None:
        issues.append("pixel_postprocess_operations must be recorded")
    if asset and asset.exists():
        package_root = root or asset.parents[2]
        raw_rel = provenance.get("raw_output_path")
        raw_path = (package_root / str(raw_rel)).resolve() if raw_rel else None
        if raw_path:
            try:
                raw_path.relative_to(package_root.resolve() / "raw" / "model-outputs")
            except ValueError:
                issues.append("raw_output_path must be under raw/model-outputs")
        if raw_path and raw_path == asset.resolve():
            issues.append("raw model output path must differ from the final asset path")
        if not raw_path or not raw_path.exists():
            issues.append("raw model output is missing")
        else:
            raw_hash = file_hash(raw_path)
            if clean_hash(provenance.get("raw_output_sha256")) != raw_hash:
                issues.append("raw_output_sha256 is missing or incorrect")
            if raw_hash != file_hash(asset):
                issues.append("final bitmap does not byte-match the raw model output")
        receipt_rel = provenance.get("run_receipt_path")
        receipt_path = (package_root / str(receipt_rel)).resolve() if receipt_rel else None
        if receipt_path:
            try:
                receipt_path.relative_to(package_root.resolve() / "raw" / "receipts")
            except ValueError:
                issues.append("run_receipt_path must be under raw/receipts")
        if not receipt_path or not receipt_path.exists():
            issues.append("generation run receipt is missing")
        elif clean_hash(provenance.get("run_receipt_sha256")) != file_hash(receipt_path):
            issues.append("run_receipt_sha256 is missing or incorrect")
        else:
            receipt = load_json(receipt_path)
            if receipt.get("schema_version") != 1:
                issues.append("generation receipt schema_version must be 1")
            expected_receipt = {
                "provider": provenance.get("provider"),
                "model": provenance.get("model"),
                "prompt_sha256": clean_hash(provenance.get("prompt_sha256")),
                "output_sha256": clean_hash(provenance.get("raw_output_sha256")),
                "request_id": provenance.get("request_id"),
            }
            for field, expected in expected_receipt.items():
                actual = clean_hash(receipt.get(field)) if field.endswith("sha256") else receipt.get(field)
                if not expected or actual != expected:
                    issues.append(f"generation receipt does not match {field}")
        response_rel = provenance.get("provider_response_path")
        response_path = (package_root / str(response_rel)).resolve() if response_rel else None
        if response_path:
            try:
                response_path.relative_to(package_root.resolve() / "raw" / "provider-responses")
            except ValueError:
                issues.append("provider_response_path must be under raw/provider-responses")
        if not response_path or not response_path.exists():
            issues.append("provider/tool response record is missing")
        elif clean_hash(provenance.get("provider_response_sha256")) != file_hash(response_path):
            issues.append("provider_response_sha256 is missing or incorrect")
        else:
            response_text = response_path.read_text(encoding="utf-8", errors="replace")
            for expected in (str(provenance.get("request_id", "")), str(provenance.get("model", "")), clean_hash(provenance.get("raw_output_sha256"))):
                if expected and expected not in response_text:
                    issues.append("provider/tool response record is not bound to request/model/output")
    return issues


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clean_hash(value: object) -> str:
    return str(value or "").replace("sha256:", "").strip().lower()


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def command_path(name: str) -> str | None:
    dependency_root = Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies"
    for candidate in (dependency_root / "bin" / "override" / name, dependency_root / "bin" / name):
        if candidate.exists():
            return str(candidate)
    return shutil.which(name)


def validate_album_pdf(
    pdf_path: Path,
    expected_pages: int,
    target_ratio: str,
    image_paths: list[Path],
    qa_dir: Path,
) -> list[str]:
    issues: list[str] = []
    if not pdf_path.exists() or pdf_path.stat().st_size < 1024:
        return ["Album PDF is missing or suspiciously small."]
    if pdf_path.read_bytes()[:5] != b"%PDF-":
        return ["Album export is not a valid PDF file."]
    pdfinfo = command_path("pdfinfo")
    if not pdfinfo:
        return ["pdfinfo is unavailable; album PDF page count and ratio cannot be verified."]
    result = subprocess.run([pdfinfo, str(pdf_path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
    if result.returncode != 0:
        return [f"pdfinfo could not read album PDF: {(result.stderr or result.stdout).strip()[:240]}"]
    pages_match = re.search(r"^Pages:\s+(\d+)", result.stdout, re.M)
    pages = int(pages_match.group(1)) if pages_match else None
    if pages != expected_pages:
        issues.append(f"Album PDF page count does not match image series: pdf={pages}, images={expected_pages}.")
    size_match = re.search(r"^Page size:\s+([0-9.]+)\s+x\s+([0-9.]+)", result.stdout, re.M)
    expected_ratios = {"3:4": 3 / 4, "4:3": 4 / 3, "16:9": 16 / 9}
    if size_match and target_ratio in expected_ratios:
        width, height = float(size_match.group(1)), float(size_match.group(2))
        if height <= 0 or abs((width / height) - expected_ratios[target_ratio]) > 0.06:
            issues.append(f"Album PDF ratio does not match image target {target_ratio}: {width}x{height}.")
    elif target_ratio in expected_ratios:
        issues.append("Could not verify album PDF page dimensions.")
    renderer = command_path("pdftoppm")
    if renderer and pages and Image is not None and ImageChops is not None and ImageStat is not None:
        qa_dir.mkdir(parents=True, exist_ok=True)
        for page_number, reference_path in enumerate(image_paths, 1):
            output_stem = qa_dir / f"album-page-{page_number:03d}"
            render = subprocess.run(
                [renderer, "-f", str(page_number), "-l", str(page_number), "-singlefile", "-png", "-r", "36", str(pdf_path), str(output_stem)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=60,
            )
            rendered_path = output_stem.with_suffix(".png")
            if render.returncode != 0 or not rendered_path.exists():
                issues.append(f"Could not render album PDF page {page_number} for order verification.")
                continue
            try:
                with Image.open(reference_path) as reference, Image.open(rendered_path) as rendered:
                    reference_thumb = reference.convert("RGB").resize((240, 320))
                    rendered_thumb = rendered.convert("RGB").resize((240, 320))
                    delta = sum(ImageStat.Stat(ImageChops.difference(reference_thumb, rendered_thumb)).mean) / 3
                if delta > 18:
                    issues.append(f"Album PDF page {page_number} does not visually match the numbered source image (mean delta {delta:.1f}).")
            except Exception:
                issues.append(f"Could not compare album PDF page {page_number} with its numbered source image.")
    return issues


def detect_repeated_slide_chrome(paths: list[Path]) -> list[str]:
    if len(paths) < 6 or Image is None or ImageChops is None or ImageStat is None:
        return []
    signatures: list[tuple[object, object]] = []
    try:
        for path in paths:
            with Image.open(path) as image:
                gray = image.convert("L")
                width, height = gray.size
                top = gray.crop((0, 0, width, max(1, int(height * 0.14)))).resize((96, 16))
                bottom = gray.crop((0, max(0, int(height * 0.90)), width, height)).resize((96, 12))
                signatures.append((top.copy(), bottom.copy()))
    except Exception:
        return ["Could not inspect image edge bands for repeated slide chrome."]
    threshold_count = max(4, int(len(paths) * 0.60))
    for index, (top, bottom) in enumerate(signatures):
        matches = 1
        for other_index, (other_top, other_bottom) in enumerate(signatures):
            if other_index == index:
                continue
            top_delta = sum(ImageStat.Stat(ImageChops.difference(top, other_top)).mean)
            bottom_delta = sum(ImageStat.Stat(ImageChops.difference(bottom, other_bottom)).mean)
            if top_delta < 2.5 and bottom_delta < 2.5:
                matches += 1
        if matches >= threshold_count:
            return [f"Repeated near-identical top/bottom rails detected across {matches}/{len(paths)} images; the album may be portrait slides with shared chrome."]
    return []


def has_review_lenses(passes: list[dict]) -> bool:
    lens_text = " ".join(str(item.get("lens", "")).lower() for item in passes if isinstance(item, dict))
    return (
        any(token in lens_text for token in ("visual", "design", "美观", "视觉"))
        and any(token in lens_text for token in ("information", "completeness", "信息", "完整"))
        and any(token in lens_text for token in ("narrative", "novice", "logic", "叙事", "新手", "逻辑"))
    )


def has_full_review_lenses(passes: list[dict]) -> bool:
    lens_text = " ".join(str(item.get("lens", "")).lower() for item in passes if isinstance(item, dict))
    groups = (
        ("visual", "design", "美观", "视觉"),
        ("information", "completeness", "信息", "完整"),
        ("narrative", "teaching", "logic", "叙事", "教学", "逻辑"),
        ("novice", "comprehension", "新手", "理解"),
        ("factual", "evidence", "accuracy", "事实", "证据", "准确"),
        ("copy", "ai tone", "public", "文案", "ai味", "公开"),
        ("technical", "render", "ocr", "技术", "渲染"),
    )
    return all(any(token in lens_text for token in group) for group in groups)


def run_actual_ocr(paths: list[Path]) -> tuple[dict[str, dict] | None, str | None]:
    if not paths:
        return {}, None
    swift = command_path("swift")
    vision_script = Path(__file__).with_name("ocr_images_vision.swift")
    if swift and vision_script.exists() and sys.platform == "darwin":
        result = subprocess.run(
            [swift, str(vision_script), *[str(path.resolve()) for path in paths]],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=max(120, len(paths) * 20),
        )
        if result.returncode != 0:
            return None, f"Apple Vision OCR failed: {(result.stderr or result.stdout).strip()[:400]}"
        try:
            records = json.loads(result.stdout)
            return {str(Path(record["path"]).resolve()): record for record in records}, None
        except Exception as exc:
            return None, f"Apple Vision OCR returned invalid JSON: {exc}"
    tesseract = command_path("tesseract")
    if tesseract:
        records: dict[str, dict] = {}
        for path in paths:
            result = subprocess.run([tesseract, str(path), "stdout", "-l", "chi_sim+eng"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)
            if result.returncode != 0:
                return None, f"Tesseract OCR failed for {path.name}: {(result.stderr or result.stdout).strip()[:300]}"
            records[str(path.resolve())] = {"path": str(path.resolve()), "text": result.stdout, "confidence": 1.0, "error": None}
        return records, None
    return None, "No executable OCR route found. Install Tesseract or use macOS with Swift/Vision."


def audit_teaching_coverage(root: Path, manifest: dict, size_mode: str, errors: list[str]) -> None:
    meta = manifest.get("teaching_fidelity", {})
    rel = meta.get("inventory_path")
    if not rel or not (root / str(rel)).exists():
        errors.append("Missing data/teaching-inventory.json or teaching_fidelity.inventory_path.")
        return
    path = root / str(rel)
    inventory = load_json(path)
    if not inventory:
        errors.append("Teaching inventory is invalid JSON.")
        return
    if clean_hash(meta.get("inventory_sha256")) != file_hash(path):
        errors.append("Teaching inventory hash is missing or incorrect.")
    if inventory.get("derivation_checked") is not True or inventory.get("reviewer_status") != "passed":
        errors.append("Teaching inventory derivation/review has not passed.")
    if clean_hash(inventory.get("source_inventory_sha256")) != clean_hash(manifest.get("source_fidelity", {}).get("main_text_inventory_sha256")):
        errors.append("Teaching inventory is not linked to the current source inventory hash.")
    if not inventory.get("hard_concepts"):
        errors.append("Teaching inventory must identify at least one hard concept.")
    if not inventory.get("central_claims"):
        errors.append("Teaching inventory must identify at least one central claim.")
    source_has_experiments = inventory.get("source_has_experiments", inventory.get("paper_has_experiments"))
    if source_has_experiments is None:
        errors.append("Teaching inventory must record source_has_experiments.")
    elif source_has_experiments is True and not inventory.get("experiments"):
        errors.append("Teaching inventory says the source has experiments but experiments[] is empty.")
    final_items = {str(item.get("id")): item for item in manifest.get("items", []) if item.get("id")}
    for concept in inventory.get("hard_concepts", []):
        for field in ("term", "plain_label", "field_definition", "plain_explanation", "author_usage", "common_misunderstanding", "definition_item_ids", "first_use_item_id", "visible_definition_labels"):
            if not concept.get(field):
                errors.append(f"Hard concept {concept.get('id', '[unknown]')} is missing {field}.")
        if not (concept.get("source_specific_meaning") or concept.get("paper_specific_meaning")):
            errors.append(f"Hard concept {concept.get('id', '[unknown]')} is missing source_specific_meaning.")
        concept_id = str(concept.get("id", ""))
        visible_labels = {str(value) for value in concept.get("visible_definition_labels", [])}
        for item_id in concept.get("definition_item_ids", []):
            item = final_items.get(str(item_id))
            if not item:
                errors.append(f"Hard concept {concept_id} references missing definition item {item_id}.")
            elif concept_id not in {str(value) for value in item.get("explained_concept_ids", [])}:
                errors.append(f"Definition item {item_id} does not declare explained_concept_ids coverage for {concept_id}.")
            elif not visible_labels.issubset({str(value) for value in item.get("expected_labels", [])}):
                errors.append(f"Definition item {item_id} expected_labels do not expose every explanation layer for {concept_id}.")
        ordered_ids = list(final_items)
        first_use_id = str(concept.get("first_use_item_id", ""))
        definition_ids = [str(value) for value in concept.get("definition_item_ids", []) if str(value) in final_items]
        if first_use_id in final_items and definition_ids:
            if min(ordered_ids.index(value) for value in definition_ids) > ordered_ids.index(first_use_id):
                errors.append(f"Hard concept {concept_id} is first used before its definition/explanation item.")
    for experiment in inventory.get("experiments", []):
        for field in (
            "comparison_objects",
            "sample_size",
            "metric",
            "metric_definition",
            "evaluator",
            "baseline_status",
            "uncertainty_or_missing",
        ):
            if experiment.get(field) in (None, "", []):
                errors.append(f"Experiment {experiment.get('id', '[unknown]')} is missing {field}; use not_reported_by_paper when necessary.")
        setup_ids = experiment.get("setup_item_ids", [])
        result_ids = experiment.get("result_item_ids", [])
        limitation_ids = experiment.get("limitation_item_ids", [])
        image_requirement = (experiment.get("mode_requirement") or {}).get("image-series")
        if image_requirement not in {"must-cover", "optional", "not-applicable"}:
            errors.append(f"Experiment {experiment.get('id', '[unknown]')} has invalid image-series mode_requirement.")
        if image_requirement == "must-cover" and (not setup_ids or not result_ids):
            errors.append(f"Selected experiment {experiment.get('id', '[unknown]')} needs setup_item_ids and result_item_ids.")
        for item_id in [*setup_ids, *result_ids, *limitation_ids]:
            if str(item_id) not in final_items:
                errors.append(f"Experiment {experiment.get('id', '[unknown]')} references missing final item {item_id}.")
        experiment_id = str(experiment.get("id", ""))
        for item_id in limitation_ids:
            item = final_items.get(str(item_id), {})
            if experiment_id not in {str(value) for value in item.get("covered_experiment_limitations", [])}:
                errors.append(f"Experiment limitation item {item_id} does not visibly cover {experiment_id}.")
        ordered_ids = list(final_items)
        valid_setup = [ordered_ids.index(str(item_id)) for item_id in setup_ids if str(item_id) in final_items]
        valid_results = [ordered_ids.index(str(item_id)) for item_id in result_ids if str(item_id) in final_items]
        if valid_setup and valid_results and max(valid_setup) >= min(valid_results):
            errors.append(f"Experiment {experiment.get('id', '[unknown]')} setup pages must precede result pages.")
    for formula in [
        item
        for item in inventory.get("formula_or_algorithm_items", [])
        if (item.get("mode_requirement") or {}).get("image-series") == "must-cover"
    ]:
        for field in ("expression_or_name", "plain_explanation", "expected_tokens", "render_item_ids"):
            if not formula.get(field):
                errors.append(f"Formula/algorithm {formula.get('id', '[unknown]')} is missing {field}.")
        expected_tokens = {str(token) for token in formula.get("expected_tokens", [])}
        for item_id in formula.get("render_item_ids", []):
            item = final_items.get(str(item_id))
            if not item:
                errors.append(f"Formula/algorithm {formula.get('id', '[unknown]')} references missing item {item_id}.")
            elif not expected_tokens.issubset({str(token) for token in item.get("expected_labels", [])}):
                errors.append(f"Formula item {item_id} expected_labels do not cover the required formula tokens.")
    groups = {
        "hard_concepts": "hard_concept_coverage",
        "experiments": "experiment_coverage",
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
            mode_requirement = (entry.get("mode_requirement") or {}).get("image-series")
            if mode_requirement not in {"must-cover", "optional", "not-applicable"}:
                errors.append(f"Teaching inventory item has invalid image-series mode_requirement: {inventory_key}:{item_id}")
            selected = mode_requirement == "must-cover"
            omission_allowed = not selected or level == "secondary" or (level == "major" and size_mode == "concise")
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
        for field in ("bundle_id", "claim_id", "final_item_ids", "source_ids", "source_excerpt_sha256", "chinese_explanation", "evidence_meaning"):
            if not bundle.get(field):
                errors.append(f"Evidence bundle is missing {field}.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a paper explainer image series.")
    parser.add_argument("path", help="Image-series output directory")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--require-pdf", action="store_true", help="Require and validate the page-matched album PDF")
    parser.add_argument("--source", help="Original source PDF/article; verifies the final package belongs to the requested source")
    args = parser.parse_args()

    root = Path(args.path).expanduser().resolve()
    errors: list[str] = []
    warnings: list[str] = []
    if args.strict and not args.source:
        errors.append("Strict image-series audit requires --source so source identity cannot be self-reported.")
    manifest_path = root / "data" / "learning-series-manifest.json"
    storyboard_path = root / "data" / "storyboard.json"

    if not manifest_path.exists():
        errors.append("Missing data/learning-series-manifest.json")
        manifest = {}
    else:
        manifest = load_json(manifest_path)
        if not manifest:
            errors.append("Invalid learning-series-manifest.json")

    if not storyboard_path.exists():
        errors.append("Missing data/storyboard.json")
        storyboard = {}
    else:
        storyboard = load_json(storyboard_path)
        if not storyboard:
            errors.append("Invalid storyboard.json")

    if manifest:
        if str(manifest.get("manifest_schema_version")) != "0.5":
            errors.append("Manifest schema version must be 0.5.")
        if manifest.get("output_mode") != "image-series":
            errors.append("Manifest output_mode must be image-series.")
        reader_language = str(manifest.get("reader_language", ""))
        if not reader_language:
            errors.append("Manifest must record reader_language.")
        size_mode = manifest.get("size_mode")
        if size_mode not in {"concise", "medium", "detailed"}:
            errors.append("Manifest must record resolved size_mode.")
        if manifest.get("size_mode_requested") == "automatic":
            sizing = manifest.get("automatic_sizing", {})
            for field in ("complexity_score", "score_breakdown", "target_min", "target_max", "maximum_count", "resolved_count", "rationale"):
                if sizing.get(field) in (None, "", []):
                    errors.append(f"Automatic sizing is missing {field}.")
            breakdown = sizing.get("score_breakdown", {})
            if isinstance(breakdown, dict):
                recomputed_score = sum(value for value in breakdown.values() if isinstance(value, (int, float)))
                if sizing.get("complexity_score") != recomputed_score:
                    errors.append(f"Automatic sizing complexity_score does not equal score_breakdown sum: {sizing.get('complexity_score')}/{recomputed_score}.")
                expected_mode = "concise" if recomputed_score <= 7 else "medium" if recomputed_score <= 15 else "detailed"
                if size_mode != expected_mode:
                    errors.append(f"Automatic sizing resolves to {expected_mode} for score {recomputed_score}, not {size_mode}.")
                expected_range = {"concise": (6, 10), "medium": (11, 20), "detailed": (21, 36)}[expected_mode]
                if (sizing.get("target_min"), sizing.get("target_max")) != expected_range:
                    errors.append(f"Automatic sizing target range must be {expected_range[0]}-{expected_range[1]} for {expected_mode} mode.")
        items = manifest.get("items", [])
        expected = manifest.get("items_expected")
        rendered = manifest.get("items_rendered")
        if expected != len(items) or rendered != len(items):
            errors.append("Expected/rendered counts must match the item inventory.")
        if manifest.get("size_mode_requested") == "automatic":
            sizing = manifest.get("automatic_sizing", {})
            if sizing.get("resolved_count") != len(items) or not sizing.get("target_min", 0) <= len(items) <= sizing.get("target_max", 0):
                errors.append("Automatic image count is outside its recorded target range or resolved_count.")
        count = len(items)
        if size_mode == "concise" and (count > 10 or (count < 6 and not manifest.get("shorter_user_approved"))):
            errors.append("Concise image series must contain 6-10 images unless a shorter set was explicitly approved.")
        if size_mode == "medium" and not 11 <= count <= 20:
            errors.append("Medium image series must contain 11-20 images.")
        if size_mode == "detailed" and count < 21:
            errors.append("Detailed image series must contain at least 21 images.")
        if count > 36 and not manifest.get("over_36_user_approved"):
            errors.append("Image series exceeds 36 items without explicit approval.")
        audit_teaching_coverage(root, manifest, size_mode, errors)

        storyboard_meta = manifest.get("storyboard", {})
        if storyboard_meta.get("locked_before_final_generation") is not True:
            errors.append("Storyboard was not locked before final generation.")
        if clean_hash(storyboard_meta.get("sha256")) != (file_hash(storyboard_path) if storyboard_path.exists() else ""):
            errors.append("Storyboard hash is missing or incorrect.")
        story_items = storyboard.get("items", storyboard.get("slides", [])) if storyboard else []
        story_ids = [str(item.get("id")) for item in story_items if item.get("id")]
        item_ids = [str(item.get("id")) for item in items if item.get("id")]
        if story_ids != item_ids:
            errors.append("Storyboard and manifest image order do not match exactly.")
        for index, story_item in enumerate(story_items):
            if index > 0:
                previous_id = str(story_items[index - 1].get("id", ""))
                if not story_item.get("previous_bridge") or str(story_item.get("previous_item_id")) != previous_id:
                    errors.append(f"Storyboard item {story_item.get('id')} lacks a valid previous bridge/link.")
            if index < len(story_items) - 1:
                next_id = str(story_items[index + 1].get("id", ""))
                if not story_item.get("next_bridge") or str(story_item.get("next_item_id")) != next_id:
                    errors.append(f"Storyboard item {story_item.get('id')} lacks a valid next bridge/link.")

        acts = storyboard.get("acts", []) if storyboard else []
        roles = {str(act.get("learning_role")) for act in acts if act.get("learning_role")}
        if not {"problem", "method"}.issubset(roles):
            errors.append("Image series must at least establish the problem and the paper's method/argument.")

        argument_map = (storyboard.get("source_argument_map") or storyboard.get("paper_argument_map", {})) if storyboard else {}
        for field in ("main_question", "thesis", "argument_steps", "evidence_route", "conclusion"):
            if not argument_map.get(field):
                errors.append(f"Storyboard source_argument_map is missing {field}.")
        argument_steps = argument_map.get("argument_steps") or []
        evidence_route = argument_map.get("evidence_route") or []
        if not isinstance(argument_steps, list) or not isinstance(evidence_route, list):
            errors.append("Storyboard source_argument_map argument_steps/evidence_route must be lists.")
            argument_steps, evidence_route = [], []
        if len(argument_steps) < 3:
            errors.append("Storyboard source_argument_map needs at least three ordered argument/reading steps.")
        if len(evidence_route) < 2:
            errors.append("Storyboard source_argument_map needs an explicit support/evidence route.")

        opening_policies = [str(item.get("page_policy", "")) for item in items[:3]]
        if "fixed-context" not in opening_policies:
            errors.append("A fixed-context whole-source map must appear within the first three images.")
        if "fixed-core-contribution" not in opening_policies:
            errors.append("A fixed-core-contribution map must appear within the first three images.")
        all_sequence_roles = [str(item.get("sequence_role", "")) for item in items]
        if any(not role for role in all_sequence_roles):
            errors.append("Every image must record a source-specific sequence_role.")
        if "recap" in all_sequence_roles:
            recap_expected = storyboard.get("recap_expected_concepts", [])
            if len(recap_expected) < 4:
                errors.append("A planned recap needs recap_expected_concepts covering the paper's core logic.")
            recap_item = items[all_sequence_roles.index("recap")]
            if not set(map(str, recap_expected)).issubset({str(value) for value in recap_item.get("recap_concepts", [])}):
                errors.append("Final recap image does not cover all recap_expected_concepts.")
        detail_positions = [index for index, role in enumerate(all_sequence_roles) if role in {"method-detail", "argument-detail", "worked-example", "experiment-setup", "evidence"}]
        if "prerequisites_required" not in storyboard:
            errors.append("Storyboard must record prerequisites_required and its rationale.")
        if not storyboard.get("prerequisites_rationale"):
            errors.append("Storyboard is missing prerequisites_rationale.")
        if detail_positions and storyboard.get("prerequisites_required") is True:
            first_detail = min(detail_positions)
            if "prerequisite" not in all_sequence_roles[:first_detail]:
                errors.append("Prerequisite teaching must appear before detailed method or evidence pages.")
        if "method-detail" in all_sequence_roles:
            first_method_detail = all_sequence_roles.index("method-detail")
            if "framework-overview" not in all_sequence_roles[:first_method_detail]:
                errors.append("A framework overview must precede component-level detail.")
        if "worked_example_required" not in storyboard:
            errors.append("Storyboard must record worked_example_required and its rationale.")
        elif storyboard.get("worked_example_required") is True and "worked-example" not in all_sequence_roles:
            errors.append("Storyboard requires a worked example, but no worked-example item exists.")
        if not storyboard.get("worked_example_rationale"):
            errors.append("Storyboard is missing worked_example_rationale.")
        method_stage_count = storyboard.get("method_stage_count")
        if not isinstance(method_stage_count, int) or method_stage_count < 0:
            errors.append("Storyboard must record a non-negative method_stage_count.")
        source_has_experiments = storyboard.get("source_has_experiments", storyboard.get("paper_has_experiments"))
        if source_has_experiments is None:
            errors.append("Storyboard must record source_has_experiments.")
        elif source_has_experiments is True:
            if "experiment-setup" not in all_sequence_roles or "evidence" not in all_sequence_roles:
                errors.append("Experimental papers need experiment-setup and evidence pages.")
            elif all_sequence_roles.index("experiment-setup") > all_sequence_roles.index("evidence"):
                errors.append("Experiment setup must appear before result evidence.")

        source_meta = manifest.get("source_fidelity", {})
        source_hash = source_meta.get("source_sha256") or source_meta.get("source_pdf_sha256")
        source_format = str(source_meta.get("source_format") or "").lower()
        if not source_hash:
            errors.append("Source fidelity is missing source_sha256/source_pdf_sha256.")
        if source_format == "pdf" and not source_meta.get("page_count"):
            errors.append("PDF source fidelity is missing page_count.")
        if not manifest.get("source_title"):
            errors.append("Manifest is missing source_title.")
        if args.source:
            requested_source = Path(args.source).expanduser().resolve()
            if not requested_source.exists():
                errors.append(f"Requested source does not exist: {requested_source}")
            else:
                requested_hash = file_hash(requested_source)
                if clean_hash(source_hash) != requested_hash:
                    errors.append("P0 source identity mismatch: output manifest does not belong to the requested source file.")
                if requested_source.suffix.lower() == ".pdf":
                    pdfinfo = command_path("pdfinfo")
                    if pdfinfo:
                        result = subprocess.run([pdfinfo, str(requested_source)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
                        match = re.search(r"^Pages:\s+(\d+)", result.stdout, re.M) if result.returncode == 0 else None
                        if match and source_meta.get("page_count") != int(match.group(1)):
                            errors.append("P0 source identity mismatch: manifest page_count differs from the requested PDF.")
        source_rel = source_meta.get("inventory_path")
        source_ids: set[str] = set()
        if not source_rel or not (root / str(source_rel)).exists():
            errors.append("Source inventory path is missing or invalid.")
        else:
            source_path = root / str(source_rel)
            source_inventory = load_json(source_path)
            if clean_hash(source_inventory.get("source_sha256")) != clean_hash(source_hash):
                errors.append("Source inventory hash does not match manifest source hash.")
            if source_format == "pdf" and source_inventory.get("page_count") != source_meta.get("page_count"):
                errors.append("Source inventory page_count does not match manifest source fidelity.")
            if str(source_inventory.get("source_title", "")).strip() != str(manifest.get("source_title", "")).strip():
                errors.append("Source inventory title does not match manifest source_title.")
            blocks = source_inventory.get("all_main_text_blocks", [])
            source_ids = {str(block.get("source_id")) for block in blocks if block.get("source_id")}
            if clean_hash(source_meta.get("main_text_inventory_sha256")) != file_hash(source_path):
                errors.append("Source inventory hash is missing or incorrect.")

        argument_records = [*argument_steps, *evidence_route]
        argument_record_ids: set[str] = set()
        for record in argument_records:
            if not isinstance(record, dict):
                errors.append("paper_argument_map records must be objects.")
                continue
            for field in ("id", "text", "source_ids", "final_item_ids"):
                if not record.get(field):
                    errors.append(f"paper_argument_map record is missing {field}.")
            record_id = str(record.get("id", ""))
            if record_id:
                argument_record_ids.add(record_id)
            for source_id in record.get("source_ids", []):
                if source_ids and str(source_id) not in source_ids:
                    errors.append(f"paper_argument_map references missing source id: {source_id}")
            for final_item_id in record.get("final_item_ids", []):
                if str(final_item_id) not in set(item_ids):
                    errors.append(f"paper_argument_map references missing final item id: {final_item_id}")
        opening_item_records = [item for item in items[:3] if item.get("page_policy") in {"fixed-context", "fixed-core-contribution"}]
        covered_argument_ids = {str(value) for item in opening_item_records for value in item.get("covered_argument_step_ids", [])}
        if argument_record_ids - covered_argument_ids:
            errors.append(f"Opening overview/argument-map images do not visibly cover argument records: {sorted(argument_record_ids - covered_argument_ids)}")

        design = manifest.get("design_brief", {})
        for field in (
            "art_direction_thesis",
            "paper_motif",
            "motif_source_basis",
            "topic_specific_objects",
            "visual_direction",
            "typography_plan",
            "color_roles",
            "shared_style_block",
            "diagram_grammars",
            "forbidden_styles",
            "forbidden_slide_chrome",
        ):
            if not design.get(field):
                errors.append(f"Design brief is missing {field}.")
        aspect_ratio_policy = str(manifest.get("aspect_ratio_policy", ""))
        target_ratio = str(manifest.get("target_aspect_ratio", ""))
        if aspect_ratio_policy not in {"uniform", "adaptive"}:
            errors.append("Manifest must record aspect_ratio_policy as uniform or adaptive.")
        if aspect_ratio_policy == "uniform" and target_ratio not in {"3:4", "4:3", "16:9", "custom"}:
            errors.append("Uniform image series must record target_aspect_ratio.")
        if aspect_ratio_policy == "adaptive" and not manifest.get("adaptive_aspect_ratio_rationale"):
            errors.append("Adaptive image series requires adaptive_aspect_ratio_rationale.")
        if target_ratio == "custom" and not manifest.get("custom_aspect_ratio_rationale"):
            errors.append("Custom aspect ratio requires a rationale.")

        declared_paths: set[str] = set()
        hashes: dict[str, str] = {}
        generation_request_ids: set[str] = set()
        layout_counts: dict[str, int] = {}
        actual_ocr_records: dict[str, dict] = {}
        if args.strict:
            ocr_paths = [root / str(item.get("path", "")) for item in items if item.get("path")]
            actual_ocr, actual_ocr_error = run_actual_ocr([path for path in ocr_paths if path.exists()])
            if actual_ocr_error:
                errors.append(actual_ocr_error)
            elif actual_ocr is not None:
                actual_ocr_records = actual_ocr
        for index, item in enumerate(items, 1):
            for field in (
                "id",
                "learner_question",
                "one_sentence_answer",
                "source_ids",
                "layout_family",
                "path",
                "aspect_ratio",
                "diagram_grammar",
                "safe_area",
                "exactness_risk",
                "text_ownership",
                "production_method",
                "sequence_role",
                "page_policy",
                "visible_title",
                "standalone_explanation_labels",
                "information_groups",
                "reader_takeaway",
                "teaching_units",
            ):
                if not item.get(field):
                    errors.append(f"Item {index} is missing {field}.")
            role = str(item.get("sequence_role", ""))
            if item.get("page_policy") not in {"fixed-context", "fixed-core-contribution", "dynamic"}:
                errors.append(f"Item {index} has invalid page_policy.")
            if item.get("text_ownership") != "in-model":
                errors.append(f"Item {index} text_ownership must be in-model.")
            if item.get("forbidden_slide_chrome") is not True:
                errors.append(f"Item {index} must forbid slide chrome.")
            if item.get("deletion_test_passed") is not True:
                errors.append(f"Item {index} did not pass the visual deletion test.")
            groups = item.get("information_groups", [])
            required_groups = 3 if item.get("page_policy") in {"fixed-context", "fixed-core-contribution"} else (1 if index == 1 else 2)
            if len(groups) < required_groups:
                errors.append(f"Item {index} has too few information groups for {role or 'its teaching role'}: {len(groups)}/{required_groups}.")
            if len(groups) > 4 or len({json.dumps(group, sort_keys=True, ensure_ascii=False) for group in groups}) != len(groups):
                errors.append(f"Item {index} information_groups must contain 1-4 distinct groups.")
            if index > 1 and len(item.get("scan_order", [])) < 3:
                errors.append(f"Item {index} needs a scan_order with at least three steps.")
            if len(set(map(str, item.get("scan_order", [])))) != len(item.get("scan_order", [])):
                errors.append(f"Item {index} scan_order contains repeated steps.")
            teaching_units = item.get("teaching_units", [])
            if len(teaching_units) < required_groups:
                errors.append(f"Item {index} has too few teaching_units: {len(teaching_units)}/{required_groups}.")
            for unit in teaching_units:
                for field in ("claim_or_concept", "explanation", "visual_anchor", "source_ids"):
                    if not unit.get(field):
                        errors.append(f"Item {index} teaching unit is missing {field}.")
            teaching_unit_names = [str(unit.get("claim_or_concept", "")) for unit in teaching_units]
            if len(set(teaching_unit_names)) != len(teaching_unit_names):
                errors.append(f"Item {index} repeats the same teaching unit.")
            if role == "worked-example":
                example = item.get("worked_example", {})
                for field in ("input", "stages", "output", "source_ids"):
                    if not example.get(field):
                        errors.append(f"Worked-example item {index} is missing {field}.")
                if isinstance(method_stage_count, int) and len(example.get("stages", [])) < method_stage_count:
                    errors.append(f"Worked-example item {index} does not cover the full method pipeline.")
            layout = str(item.get("layout_family", ""))
            layout_counts[layout] = layout_counts.get(layout, 0) + 1
            for source_id in item.get("source_ids", []):
                if source_ids and str(source_id) not in source_ids:
                    errors.append(f"Item {index} references missing source id: {source_id}")
            rel = str(item.get("path", ""))
            if rel and not Path(rel).name.startswith(f"{index:03d}-"):
                errors.append(f"Image filename does not preserve sequence number {index:03d}: {rel}")
            declared_paths.add(rel)
            asset = root / rel
            if asset.suffix.lower() not in BITMAP_SUFFIXES or not asset.exists():
                errors.append(f"Missing or invalid bitmap: {rel}")
                continue
            actual_hash = file_hash(asset)
            if clean_hash(item.get("asset_sha256")) != actual_hash:
                errors.append(f"Image hash is missing or incorrect: {rel}")
            if actual_hash in hashes:
                errors.append(f"Duplicate final bitmap is not allowed in image-series mode: {hashes[actual_hash]} and {rel}")
            hashes[actual_hash] = rel
            request_id = str(item.get("generation_provenance", {}).get("request_id", ""))
            if request_id in generation_request_ids:
                errors.append(f"Duplicate image-generation request_id is not allowed: {request_id}")
            elif request_id:
                generation_request_ids.add(request_id)
            for issue in validate_native_generation_contract(item, asset, root):
                errors.append(f"Image {index} native-generation contract failed: {issue}.")
            if Image is not None:
                try:
                    with Image.open(asset) as image:
                        width, height = image.size
                    if max(width, height) < 1536 or min(width, height) < 864:
                        errors.append(f"Image resolution is too low: {rel} ({width}x{height})")
                    if item.get("width_px") != width or item.get("height_px") != height:
                        errors.append(f"Manifest dimensions are missing or incorrect: {rel}")
                    expected_ratios = {"3:4": 3 / 4, "4:3": 4 / 3, "16:9": 16 / 9}
                    item_ratio = str(item.get("aspect_ratio", ""))
                    ratio_to_check = target_ratio if aspect_ratio_policy == "uniform" else item_ratio
                    if ratio_to_check in expected_ratios and abs((width / height) - expected_ratios[ratio_to_check]) > 0.06:
                        errors.append(f"Image aspect ratio does not match declared ratio {ratio_to_check}: {rel} ({width}x{height})")
                except Exception:
                    errors.append(f"Unreadable image file: {rel}")
            if item.get("crop_checked") is not True or item.get("reviewer_status") != "passed":
                errors.append(f"Image has not passed visual review: {rel}")
            ocr_artifact_rel = str(item.get("ocr_artifact_path", ""))
            ocr_engine = str(item.get("ocr_engine", ""))
            if not ocr_artifact_rel or not ocr_engine:
                errors.append(f"Final image is missing OCR artifact provenance: {rel}")
                actual_ocr_text = ""
            else:
                ocr_artifact = root / ocr_artifact_rel
                if not ocr_artifact.exists():
                    errors.append(f"Final image OCR artifact does not exist: {ocr_artifact_rel}")
                    actual_ocr_text = ""
                else:
                    actual_ocr_text = ocr_artifact.read_text(encoding="utf-8", errors="replace")
                    if clean_hash(item.get("ocr_artifact_sha256")) != file_hash(ocr_artifact):
                        errors.append(f"Final image OCR artifact hash is missing or incorrect: {ocr_artifact_rel}")
            ocr_text = str(item.get("ocr_text", ""))
            if actual_ocr_text and ocr_text.strip() != actual_ocr_text.strip():
                errors.append(f"Manifest OCR text does not match the stored OCR artifact: {rel}")
            if not ocr_text:
                errors.append(f"Final image has no OCR text record: {rel}")
            if any(token in ocr_text for token in ("□", "�")):
                errors.append(f"Final image OCR contains missing/replacement glyphs: {rel}")
            actual_record = actual_ocr_records.get(str(asset.resolve()))
            actual_text = str(actual_record.get("text", "")) if actual_record else ""
            if args.strict and not actual_record:
                errors.append(f"Strict OCR did not return a record for final image: {rel}")
            if actual_record and actual_record.get("error"):
                errors.append(f"Strict OCR failed for final image {rel}: {actual_record.get('error')}")
            if actual_text and any(token in actual_text for token in ("□", "�")):
                errors.append(f"Strict OCR detected missing/replacement glyphs in final image: {rel}")
            actual_missing_labels = [str(label) for label in item.get("expected_labels", []) if str(label) and str(label) not in actual_text]
            if args.strict and actual_missing_labels:
                errors.append(f"Strict OCR could not find expected labels {actual_missing_labels[:5]} in final image: {rel}")
            if item.get("ocr_pass") is not True:
                errors.append(f"Final image has not passed full-page OCR review: {rel}")
            if not item.get("expected_labels"):
                errors.append(f"Final image has no expected_labels for OCR verification: {rel}")
            missing_anchors = [
                str(unit.get("visual_anchor"))
                for unit in teaching_units
                if unit.get("visual_anchor") and str(unit.get("visual_anchor")) not in ocr_text
            ]
            if missing_anchors:
                errors.append(f"Final image OCR does not contain teaching-unit visual anchors {missing_anchors[:5]}: {rel}")
            required_standalone_text = [str(item.get("visible_title", "")), *map(str, item.get("standalone_explanation_labels", []))]
            missing_standalone = [value for value in required_standalone_text if value and value not in ocr_text]
            if missing_standalone:
                errors.append(f"Final image is not standalone-readable; OCR misses title/explanation anchors {missing_standalone[:5]}: {rel}")
            if reader_language.lower().startswith("zh") and chinese_ratio(ocr_text) < 0.45:
                errors.append(f"Chinese-reader image is not Chinese-dominant enough: {rel}")
            copy_issues = public_copy_issues(ocr_text)
            if copy_issues:
                errors.append(f"Final image public copy has AI/process residue {copy_issues}: {rel}")
            generated = item.get("production_method") == "model-single-pass"
            if generated:
                labels = item.get("diagram_labels", [])
                semantic_map = item.get("visual_semantic_map", [])
                integration = item.get("text_integration", {})
                relation_type = str(item.get("visual_relation_type", ""))
                if len(labels) < 3:
                    errors.append(f"Generated teaching image needs at least three explanatory diagram_labels: {rel}")
                missing_labels = [str(label) for label in labels if str(label) and str(label) not in ocr_text]
                if missing_labels:
                    errors.append(f"Generated teaching image OCR is missing diagram labels {missing_labels[:5]}: {rel}")
                if len(semantic_map) < 2:
                    errors.append(f"Generated teaching image lacks a visual_semantic_map: {rel}")
                if relation_type not in {"causal", "spatial", "comparative", "sequential", "quantitative", "hierarchical"}:
                    errors.append(f"Generated teaching image does not declare a real teaching relationship: {rel}")
                relation_labels = [str(label) for label in item.get("visual_relation_labels", [])]
                if len(relation_labels) < 2 or any(label not in ocr_text for label in relation_labels):
                    errors.append(f"Generated teaching image visual relationship is not anchored by OCR-visible labels: {rel}")
                if integration.get("mode") != "in-model":
                    errors.append(f"Generated teaching image must use in-model text integration: {rel}")
                if integration.get("planned_before_generation") is not True:
                    errors.append(f"Generated teaching image labels were not planned before generation: {rel}")
                visual_language = str(item.get("in_image_text_language", "")).lower()
                if reader_language.lower().startswith("zh") and not any(token in visual_language for token in ("zh", "chinese", "中文")):
                    errors.append(f"Chinese-reader teaching image is not recorded as Chinese-dominant: {rel}")
            if item.get("production_method") == "model-single-pass" and not item.get("model_name"):
                errors.append(f"Generated image does not record the real model name: {rel}")

        if count and layout_counts:
            dominant_layout, dominant_count = max(layout_counts.items(), key=lambda entry: entry[1])
            if dominant_count / count > 0.60 and not manifest.get("layout_repetition_rationale"):
                errors.append(f"One image composition dominates the series without rationale: {dominant_layout} {dominant_count}/{count}")
            if count >= 11 and len(layout_counts) < 4:
                errors.append(f"Medium/detailed image series needs at least four composition families: {len(layout_counts)}.")
        layout_sequence = [str(item.get("layout_family", "")) for item in items]
        streak = 1
        for index in range(1, len(layout_sequence)):
            if layout_sequence[index] == layout_sequence[index - 1]:
                streak += 1
                if streak > 3:
                    errors.append(f"The same image composition repeats more than three times consecutively near item {index + 1}: {layout_sequence[index]}")
                    break
            else:
                streak = 1
        errors.extend(detect_repeated_slide_chrome([root / str(item.get("path", "")) for item in items if item.get("path")]))

        final_dir = root / "assets" / "images"
        packaged = {
            str(path.relative_to(root))
            for path in final_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in BITMAP_SUFFIXES
        } if final_dir.exists() else set()
        orphan = sorted(packaged - declared_paths)
        if orphan:
            errors.append(f"Orphan images found in final package: {orphan[:8]}")

        contact_sheet = root / str(manifest.get("contact_sheet_path", ""))
        if not manifest.get("contact_sheet_path") or not contact_sheet.exists():
            errors.append("Missing full-series contact sheet.")
        elif Image is not None:
            try:
                with Image.open(contact_sheet) as sheet:
                    sheet.verify()
            except Exception:
                errors.append("Full-series contact sheet is not a valid image.")
        exports = manifest.get("exports", {})
        album_rel = exports.get("album_pdf_path")
        if args.require_pdf or album_rel:
            if not album_rel:
                errors.append("Image series is missing exports.album_pdf_path.")
            else:
                album_path = root / str(album_rel)
                ordered_image_paths = [root / str(item.get("path", "")) for item in items]
                errors.extend(validate_album_pdf(album_path, count, target_ratio, ordered_image_paths, root / "qa" / "album-render-check"))
                if album_path.exists() and clean_hash(exports.get("album_pdf_sha256")) != file_hash(album_path):
                    errors.append("Album PDF hash is missing or incorrect.")
                if exports.get("album_pdf_page_count") != count:
                    errors.append("Manifest album_pdf_page_count does not match image count.")
        claims = manifest.get("claim_evidence_map", [])
        expected_claim_ids = {
            str(item.get("inventory_id"))
            for item in manifest.get("central_claim_coverage", [])
            if item.get("status") == "covered" and item.get("inventory_id")
        }
        mapped_claim_ids = {str(claim.get("claim_id")) for claim in claims if claim.get("claim_id")}
        if expected_claim_ids - mapped_claim_ids:
            errors.append(f"Covered central claims are missing from claim_evidence_map: {sorted(expected_claim_ids - mapped_claim_ids)}")
        visible_ocr = "\n".join(str(item.get("ocr_text", "")) for item in items)
        for claim in claims:
            for field in (
                "claim_id",
                "claim_role",
                "claim_wording",
                "source_ids",
                "comparison_baseline",
                "comparison_validity",
                "metric_or_dimension",
                "direction_or_value",
                "evidence_items",
                "evidence_strength",
                "boundary_handling",
            ):
                if not claim.get(field):
                    errors.append(f"Claim evidence entry is missing {field}.")
            wording = str(claim.get("claim_wording", ""))
            if wording and wording not in visible_ocr:
                errors.append(f"Claim wording is not visible in final image OCR: {wording[:120]}")
            if claim.get("comparison_validity") not in {"controlled", "descriptive", "cross-benchmark", "not-applicable"}:
                errors.append(f"Claim has invalid comparison_validity: {claim.get('comparison_validity')}")
            if re.search(r"(?:证明|证实|验证了|击败|打败|优于|超越|导致|带来|使得|归因于|显著提高|提升了|proves?|demonstrates?|validates?|beats?|outperforms?|causes?|leads?\s+to|improves?\s+by)", wording, re.I) and claim.get("comparison_validity") != "controlled":
                errors.append(f"Overstated claim without a controlled comparison: {wording[:120]}")
            if claim.get("claim_role") == "supported_conclusion":
                supporting = [item for item in claim.get("evidence_items", []) if item.get("supports_vs_illustrates") == "supports" and item.get("evidence_kind") != "generated_visual"]
                if not supporting:
                    errors.append("A supported conclusion has no non-generated supporting evidence.")
                for evidence in supporting:
                    for field in ("evidence_id", "evidence_kind", "source_id", "asset_or_excerpt_path", "asset_or_excerpt_sha256"):
                        if not evidence.get(field):
                            errors.append(f"Supporting evidence is missing {field} for claim {claim.get('claim_id')}.")
                    if evidence.get("evidence_kind") not in {"source_figure", "source_table", "source_paragraph", "source_experiment", "source_formula", "source_algorithm"}:
                        errors.append(f"Supporting evidence has an invalid evidence_kind: {evidence.get('evidence_kind')}")
                    source_id = str(evidence.get("source_id", ""))
                    if source_ids and source_id not in source_ids:
                        errors.append(f"Supporting evidence references a missing source id: {source_id}")
                    evidence_rel = str(evidence.get("asset_or_excerpt_path", ""))
                    evidence_path = (root / evidence_rel).resolve() if evidence_rel else None
                    if evidence_path:
                        try:
                            evidence_path.relative_to(root.resolve())
                        except ValueError:
                            errors.append(f"Supporting evidence path points outside package: {evidence_rel}")
                    if not evidence_path or not evidence_path.exists():
                        errors.append(f"Supporting evidence asset/excerpt is missing: {evidence_rel}")
                    elif clean_hash(evidence.get("asset_or_excerpt_sha256")) != file_hash(evidence_path):
                        errors.append(f"Supporting evidence hash is missing or incorrect: {evidence_rel}")
        qa = manifest.get("qa", {})
        for field in (
            "all_images_reviewed",
            "contact_sheet_checked",
            "public_copy_clean",
            "evidence_links_checked",
            "aesthetic_review_passed",
            "visual_variety_checked",
            "narrative_continuity_checked",
            "overview_sequence_checked",
            "in_image_explanation_checked",
            "information_density_checked",
            "album_pdf_checked",
            "glyph_integrity_checked",
            "template_residue_checked",
            "native_generation_provenance_checked",
            "standalone_readability_checked",
        ):
            if qa.get(field) is not True:
                errors.append(f"Image-series QA has not passed {field}.")
        adversarial_passes = qa.get("adversarial_passes", [])
        review_rounds = {str(item.get("round")) for item in adversarial_passes if isinstance(item, dict) and item.get("round") is not None}
        if len(review_rounds) < 2 or not has_full_review_lenses(adversarial_passes):
            errors.append("Image-series QA must record at least two rounds covering visual, information, teaching logic, novice comprehension, factual accuracy, public copy, and technical rendering.")
        qa_report_path = root / "qa" / "qa-report.json"
        qa_report = load_json(qa_report_path) if qa_report_path.exists() else {}
        if not qa_report:
            errors.append("Missing or invalid qa/qa-report.json.")
        else:
            if qa_report.get("final_status") not in {"passed", "clean"}:
                errors.append("QA report final_status is not passed/clean.")
            if qa_report.get("unresolved_blockers") or qa_report.get("remaining_errors"):
                errors.append("QA report still contains unresolved blockers or errors.")
            item_reviews = qa_report.get("item_reviews", [])
            if len(item_reviews) != count:
                errors.append(f"QA report needs one item_reviews entry per image: {len(item_reviews)}/{count}.")
            reviewed_ids = {str(review.get("item_id")) for review in item_reviews if isinstance(review, dict)}
            if reviewed_ids != set(item_ids):
                errors.append("QA item review ids do not match the final image ids.")
            finding_counts: dict[str, int] = {}
            item_by_id = {str(item.get("id")): item for item in items if item.get("id")}
            for review in item_reviews:
                for field in (
                    "item_id",
                    "visual_status",
                    "information_status",
                    "narrative_status",
                    "findings",
                    "fixes",
                    "review_evidence_path",
                    "reviewed_asset_sha256",
                    "final_status",
                ):
                    if review.get(field) in (None, "", []):
                        errors.append(f"QA item review is missing {field}: {review.get('item_id', '[unknown]')}")
                for status_field in ("visual_status", "information_status", "narrative_status", "final_status"):
                    if review.get(status_field) not in {"passed", "fixed"}:
                        errors.append(f"QA item review has invalid {status_field}: {review.get('item_id', '[unknown]')}")
                findings = re.sub(r"\s+", " ", str(review.get("findings", "")).strip().lower())
                if len(findings) < 20:
                    errors.append(f"QA item review findings are too generic: {review.get('item_id', '[unknown]')}")
                if findings:
                    finding_counts[findings] = finding_counts.get(findings, 0) + 1
                evidence_path = root / str(review.get("review_evidence_path", ""))
                if not evidence_path.exists():
                    errors.append(f"QA item review evidence path does not exist: {review.get('review_evidence_path')}")
                item = item_by_id.get(str(review.get("item_id")), {})
                reviewed_hash = clean_hash(review.get("reviewed_asset_sha256"))
                if reviewed_hash:
                    if reviewed_hash != clean_hash(item.get("asset_sha256")):
                        errors.append(f"QA item review asset hash does not match final image: {review.get('item_id')}")
            repeated_findings = [text for text, repetitions in finding_counts.items() if repetitions > 2]
            if repeated_findings:
                errors.append("QA item reviews reuse generic findings across more than two images.")

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
