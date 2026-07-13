#!/usr/bin/env python3
"""Strict static checks for ordered paper explainer image series."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

try:
    from PIL import Image
except Exception:
    Image = None


BITMAP_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


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
        for field in ("bundle_id", "claim_id", "final_item_ids", "source_ids", "source_excerpt_or_asset", "visible_source_cue", "chinese_explanation", "evidence_meaning", "limitation"):
            if not bundle.get(field):
                errors.append(f"Evidence bundle is missing {field}.")
        if bundle.get("source_cue_ocr_pass") is not True:
            errors.append(f"Image-series evidence bundle source cue has not passed OCR: {bundle.get('bundle_id')}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a paper explainer image series.")
    parser.add_argument("path", help="Image-series output directory")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    root = Path(args.path).expanduser().resolve()
    errors: list[str] = []
    warnings: list[str] = []
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
        if str(manifest.get("manifest_schema_version")) != "0.3":
            errors.append("Manifest schema version must be 0.3.")
        if manifest.get("output_mode") != "image-series":
            errors.append("Manifest output_mode must be image-series.")
        size_mode = manifest.get("size_mode")
        if size_mode not in {"concise", "medium", "detailed"}:
            errors.append("Manifest must record resolved size_mode.")
        if manifest.get("size_mode_requested") == "automatic":
            sizing = manifest.get("automatic_sizing", {})
            for field in ("complexity_score", "score_breakdown", "target_min", "target_max", "maximum_count", "resolved_count", "rationale"):
                if sizing.get(field) in (None, "", []):
                    errors.append(f"Automatic sizing is missing {field}.")
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

        acts = storyboard.get("acts", []) if storyboard else []
        roles = {str(act.get("learning_role")) for act in acts if act.get("learning_role")}
        if not {"problem", "prerequisite", "method", "evidence", "limitation"}.issubset(roles):
            errors.append("Image series lacks the complete teaching arc.")

        source_meta = manifest.get("source_fidelity", {})
        source_rel = source_meta.get("inventory_path")
        source_ids: set[str] = set()
        if not source_rel or not (root / str(source_rel)).exists():
            errors.append("Source inventory path is missing or invalid.")
        else:
            source_path = root / str(source_rel)
            source_inventory = load_json(source_path)
            blocks = source_inventory.get("all_main_text_blocks", [])
            source_ids = {str(block.get("source_id")) for block in blocks if block.get("source_id")}
            if clean_hash(source_meta.get("main_text_inventory_sha256")) != file_hash(source_path):
                errors.append("Source inventory hash is missing or incorrect.")

        design = manifest.get("design_brief", {})
        for field in ("art_direction_thesis", "paper_motif", "motif_source_basis", "topic_specific_objects", "visual_direction", "typography_plan", "evidence_style", "forbidden_styles"):
            if not design.get(field):
                errors.append(f"Design brief is missing {field}.")
        target_ratio = str(manifest.get("target_aspect_ratio", ""))
        if target_ratio not in {"3:4", "4:3", "16:9", "custom"}:
            errors.append("Manifest must record target_aspect_ratio.")
        if target_ratio == "custom" and not manifest.get("custom_aspect_ratio_rationale"):
            errors.append("Custom aspect ratio requires a rationale.")

        declared_paths: set[str] = set()
        hashes: dict[str, str] = {}
        layout_counts: dict[str, int] = {}
        for index, item in enumerate(items, 1):
            for field in ("id", "learner_question", "one_sentence_answer", "source_ids", "layout_family", "path", "production_method"):
                if not item.get(field):
                    errors.append(f"Item {index} is missing {field}.")
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
            if actual_hash in hashes and not item.get("reuse_reason"):
                errors.append(f"Duplicate bitmap without reuse reason: {hashes[actual_hash]} and {rel}")
            hashes[actual_hash] = rel
            if Image is not None:
                try:
                    with Image.open(asset) as image:
                        width, height = image.size
                    if max(width, height) < 1536 or min(width, height) < 864:
                        errors.append(f"Image resolution is too low: {rel} ({width}x{height})")
                    if item.get("width_px") != width or item.get("height_px") != height:
                        errors.append(f"Manifest dimensions are missing or incorrect: {rel}")
                    expected_ratios = {"3:4": 3 / 4, "4:3": 4 / 3, "16:9": 16 / 9}
                    if target_ratio in expected_ratios and abs((width / height) - expected_ratios[target_ratio]) > 0.06:
                        errors.append(f"Image aspect ratio does not match series target {target_ratio}: {rel} ({width}x{height})")
                except Exception:
                    errors.append(f"Unreadable image file: {rel}")
            if item.get("crop_checked") is not True or item.get("reviewer_status") != "passed":
                errors.append(f"Image has not passed visual review: {rel}")
            if item.get("expected_labels") and item.get("ocr_pass") is not True:
                errors.append(f"Text-bearing image has not passed OCR label comparison: {rel}")
            if item.get("production_method") in {"generated", "generated-composite"} and not item.get("model_name"):
                errors.append(f"Generated image does not record the real model name: {rel}")
            if item.get("claim_role") in {"source_claim_to_verify", "supported_conclusion"}:
                source_cue = str(item.get("visible_source_cue", "")).strip()
                ocr_text = str(item.get("ocr_text", ""))
                if not source_cue or item.get("source_cue_ocr_pass") is not True or source_cue not in ocr_text:
                    errors.append(f"Factual image lacks a reader-visible, OCR-verified source cue: {rel}")

        if count and layout_counts:
            dominant_layout, dominant_count = max(layout_counts.items(), key=lambda entry: entry[1])
            if dominant_count / count > 0.60 and not manifest.get("layout_repetition_rationale"):
                errors.append(f"One image composition dominates the series without rationale: {dominant_layout} {dominant_count}/{count}")

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
        claims = manifest.get("claim_evidence_map", [])
        for claim in claims:
            for field in ("claim_role", "source_ids", "comparison_baseline", "metric_or_dimension", "direction_or_value", "evidence_items", "limitation"):
                if not claim.get(field):
                    errors.append(f"Claim evidence entry is missing {field}.")
            if claim.get("claim_role") == "supported_conclusion":
                supporting = [item for item in claim.get("evidence_items", []) if item.get("supports_vs_illustrates") == "supports" and item.get("evidence_kind") != "generated_visual"]
                if not supporting:
                    errors.append("A supported conclusion has no non-generated supporting evidence.")
        qa = manifest.get("qa", {})
        for field in ("all_images_reviewed", "contact_sheet_checked", "public_copy_clean", "evidence_links_checked", "aesthetic_review_passed", "visual_variety_checked", "narrative_continuity_checked"):
            if qa.get(field) is not True:
                errors.append(f"Image-series QA has not passed {field}.")
        if len(qa.get("adversarial_passes", [])) < 3:
            errors.append("Image-series QA does not record three adversarial reviews.")
        qa_report_path = root / "qa" / "qa-report.json"
        qa_report = load_json(qa_report_path) if qa_report_path.exists() else {}
        if not qa_report:
            errors.append("Missing or invalid qa/qa-report.json.")
        else:
            if qa_report.get("final_status") not in {"passed", "clean"}:
                errors.append("QA report final_status is not passed/clean.")
            if qa_report.get("unresolved_blockers") or qa_report.get("remaining_errors"):
                errors.append("QA report still contains unresolved blockers or errors.")

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
