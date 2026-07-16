#!/usr/bin/env python3
"""Static quality checks for visual paper teaching decks."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import posixpath
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from generation_provenance import validate_generated_asset_provenance

try:
    from PIL import Image, ImageChops, ImageStat
except Exception:  # Pillow is recommended by preflight but keep the audit readable without it.
    Image = None
    ImageChops = None
    ImageStat = None


BITMAP_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
NON_BODY_SLIDE_TYPES = {"title", "divider", "evidence-appendix"}
NON_LAYOUT_SLIDE_TYPES = {"title", "divider", "evidence-appendix"}
PML_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
DML_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
FORBIDDEN_PUBLIC_TEXT = (
    "面向无专业背景",
    "reader level",
    "prompt summary",
    "generated asset",
    "生成教学图资产",
    "preflight",
    "manifest",
    "regression",
    "本页旨在",
    "这里需要让用户",
    "这里需要告诉读者",
    "测试页",
    "回归样本",
)
GENERIC_AI_COPY_PATTERNS = (
    (r"值得注意的是|不难发现|接下来(?:我们)?(?:将)?深入|由此可见", "generic transition"),
    (r"赋能|颠覆|全新范式|革命性|重塑", "inflated generic wording"),
)


def public_copy_issues(text: str) -> list[str]:
    issues = [label for pattern, label in GENERIC_AI_COPY_PATTERNS if re.search(pattern, text, re.I)]
    if any(token.lower() in text.lower() for token in FORBIDDEN_PUBLIC_TEXT):
        issues.append("internal production wording")
    if len(re.findall(r"不是[^。！？\n]{0,36}而是", text)) > 1:
        issues.append("repeated not-but contrast syntax")
    if len(re.findall(r"不仅[^。！？\n]{0,36}(?:更|还)", text)) > 1:
        issues.append("repeated not-only contrast syntax")
    if len(re.findall(r"从[^。！？\n]{1,24}到[^。！？\n]{1,24}", text)) > 3:
        issues.append("repeated from-to framing")
    return issues


def chinese_ratio(text: str) -> float:
    chinese = len(re.findall(r"[\u3400-\u9fff]", text))
    latin = len(re.findall(r"[A-Za-z]", text))
    return chinese / max(1, chinese + latin)


def html_visible_text(html: str) -> str:
    text = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", " ", html, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


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
        ("technical", "render", "pdf", "技术", "渲染"),
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


def command_path(name: str) -> str | None:
    dependency_root = Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies"
    for candidate in (
        dependency_root / "bin" / "override" / name,
        dependency_root / "bin" / name,
        dependency_root / "native" / "poppler" / "bin" / name,
        dependency_root / "native" / "poppler" / "poppler" / "bin" / name,
    ):
        if candidate.exists():
            return str(candidate)
    return shutil.which(name)


def _slide_number(path: str) -> int:
    match = re.search(r"slide(\d+)\.xml$", path)
    return int(match.group(1)) if match else 0


def _bytes_sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _grid_coverage(rects: list[dict], width: int, height: int, y_start: float = 0) -> float:
    columns = 48
    rows = 27
    occupied: set[tuple[int, int]] = set()
    first_available_row = int(y_start / height * rows)
    for rect in rects:
        left = max(0.0, float(rect.get("left", 0)))
        top = max(y_start, float(rect.get("top", 0)))
        right = min(float(width), float(rect.get("right", 0)))
        bottom = min(float(height), float(rect.get("bottom", 0)))
        if right <= left or bottom <= top:
            continue
        first_column = max(0, int(left / width * columns))
        last_column = min(columns - 1, int(max(left, right - 1) / width * columns))
        first_row = max(first_available_row, int(top / height * rows))
        last_row = min(rows - 1, int(max(top, bottom - 1) / height * rows))
        for row in range(first_row, last_row + 1):
            for column in range(first_column, last_column + 1):
                occupied.add((row, column))
    available_rows = rows - first_available_row
    return len(occupied) / max(1, columns * available_rows)


def _shape_geometry(element: ET.Element, kind: str, slide_width: int, slide_height: int) -> dict | None:
    if kind == "graphic":
        xfrm = element.find(f"./{{{PML_NS}}}xfrm")
    else:
        xfrm = element.find(f"./{{{PML_NS}}}spPr/{{{DML_NS}}}xfrm")
    offset = xfrm.find(f"{{{DML_NS}}}off") if xfrm is not None else None
    extent = xfrm.find(f"{{{DML_NS}}}ext") if xfrm is not None else None
    if offset is None or extent is None:
        return None
    left = int(offset.get("x", "0"))
    top = int(offset.get("y", "0"))
    width = int(extent.get("cx", "0"))
    height = int(extent.get("cy", "0"))
    if width <= 0 or height <= 0 or left >= slide_width or top >= slide_height:
        return None
    return {
        "left": left,
        "top": top,
        "right": min(slide_width, left + width),
        "bottom": min(slide_height, top + height),
        "width": min(width, slide_width - left),
        "height": min(height, slide_height - top),
        "raw_width": width,
        "raw_height": height,
    }


def _layout_tokens(objects: list[dict], slide_width: int, slide_height: int) -> list[str]:
    tokens: set[str] = set()
    for item in objects:
        rect = item["rect"]
        center_column = min(5, int(((rect["left"] + rect["right"]) / 2) / slide_width * 6))
        center_row = min(3, int(((rect["top"] + rect["bottom"]) / 2) / slide_height * 4))
        width_bucket = max(1, min(4, round(rect["width"] / slide_width * 4)))
        height_bucket = max(1, min(4, round(rect["height"] / slide_height * 4)))
        tokens.add(f"{item['kind']}:{center_column}:{center_row}:{width_bucket}:{height_bucket}")
    return sorted(tokens)


def inspect_pptx_geometry(
    pptx_path: Path,
    slide_items: list[dict] | None = None,
    generated_visuals: list[dict] | None = None,
) -> tuple[list[dict], list[str]]:
    issues: list[str] = []
    results: list[dict] = []
    generated_hashes = {
        normalized_hash(item.get("asset_sha256"))
        for item in (generated_visuals or [])
        if normalized_hash(item.get("asset_sha256"))
    }
    source_hashes = {
        normalized_hash(evidence.get("asset_sha256"))
        for slide in (slide_items or [])
        for evidence in slide.get("source_evidence_objects", [])
        if normalized_hash(evidence.get("asset_sha256"))
    }
    with zipfile.ZipFile(pptx_path) as archive:
        slide_width, slide_height = 12192000, 6858000
        if "ppt/presentation.xml" in archive.namelist():
            presentation = ET.fromstring(archive.read("ppt/presentation.xml"))
            size = presentation.find(f".//{{{PML_NS}}}sldSz")
            if size is not None:
                slide_width = int(size.get("cx", slide_width))
                slide_height = int(size.get("cy", slide_height))
        slide_names = sorted(
            (name for name in archive.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)),
            key=_slide_number,
        )
        for index, slide_name in enumerate(slide_names, 1):
            slide = ET.fromstring(archive.read(slide_name))
            relationship_path = posixpath.join(
                posixpath.dirname(slide_name),
                "_rels",
                f"{posixpath.basename(slide_name)}.rels",
            )
            relationships: dict[str, str] = {}
            if relationship_path in archive.namelist():
                relationship_root = ET.fromstring(archive.read(relationship_path))
                relationships = {
                    relation.get("Id", ""): posixpath.normpath(
                        posixpath.join(posixpath.dirname(slide_name), relation.get("Target", ""))
                    ).lstrip("/")
                    for relation in relationship_root
                }

            content_objects: list[dict] = []
            layout_objects: list[dict] = []
            visual_rects: list[dict] = []
            source_rects: list[dict] = []
            oversized_boxes = 0

            for shape in slide.findall(f".//{{{PML_NS}}}sp"):
                rect = _shape_geometry(shape, "shape", slide_width, slide_height)
                text = "".join(node.text or "" for node in shape.findall(f".//{{{DML_NS}}}t")).strip()
                if rect is None or not text:
                    continue
                paragraph_count = max(1, len([node for node in shape.findall(f".//{{{DML_NS}}}p") if "".join(part.text or "" for part in node.findall(f".//{{{DML_NS}}}t")).strip()]))
                sizes = [
                    int(node.get("sz", "0"))
                    for node in shape.findall(f".//*[@sz]")
                    if node.get("sz", "").isdigit()
                ]
                max_font_size = max(sizes, default=1800)
                estimated_text_height = max_font_size / 100 * 12700 * max(1.35, paragraph_count * 1.25)
                effective_rect = dict(rect)
                effective_rect["height"] = min(rect["height"], estimated_text_height)
                effective_rect["bottom"] = min(rect["bottom"], rect["top"] + effective_rect["height"])
                placeholder = shape.find(f"./{{{PML_NS}}}nvSpPr/{{{PML_NS}}}nvPr/{{{PML_NS}}}ph")
                placeholder_type = placeholder.get("type", "") if placeholder is not None else ""
                kind = "heading" if placeholder_type in {"title", "ctrTitle"} or max_font_size >= 2800 else "group"
                content_objects.append({"kind": kind, "rect": effective_rect})
                if (
                    placeholder_type not in {"title", "ctrTitle"}
                    and paragraph_count == 1
                    and len(text) <= 80
                    and (
                        (rect["width"] / slide_width > 0.70 and rect["height"] / slide_height > 0.22)
                        or (
                            rect["raw_width"] / slide_width > 0.88
                            and rect["raw_height"] / slide_height > 0.07
                        )
                    )
                ):
                    oversized_boxes += 1
                if rect["width"] * rect["height"] >= slide_width * slide_height * 0.012:
                    layout_objects.append({"kind": kind, "rect": effective_rect})

            for picture in slide.findall(f".//{{{PML_NS}}}pic"):
                rect = _shape_geometry(picture, "picture", slide_width, slide_height)
                if rect is None:
                    continue
                blip = picture.find(f".//{{{DML_NS}}}blip")
                embed = blip.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed", "") if blip is not None else ""
                target = relationships.get(embed, "")
                media_hash = ""
                natural_ratio = 0.0
                if target in archive.namelist():
                    payload = archive.read(target)
                    media_hash = _bytes_sha256(payload)
                    if Image is not None:
                        try:
                            with Image.open(io.BytesIO(payload)) as image:
                                natural_ratio = image.height / max(1, image.width)
                        except Exception:
                            natural_ratio = 0.0
                properties = picture.find(f"./{{{PML_NS}}}nvPicPr/{{{PML_NS}}}cNvPr")
                cue = " ".join(
                    [
                        target,
                        properties.get("name", "") if properties is not None else "",
                        properties.get("descr", "") if properties is not None else "",
                        properties.get("title", "") if properties is not None else "",
                    ]
                ).lower()
                area_ratio = rect["width"] * rect["height"] / (slide_width * slide_height)
                is_generated = media_hash in generated_hashes
                is_source = media_hash in source_hashes or bool(re.search(r"source|evidence|screenshot|crop|paper[-_ ]?page|原文|证据", cue))
                if not is_generated and natural_ratio > 1.15 and area_ratio >= 0.12:
                    is_source = True
                content_objects.append({"kind": "source" if is_source else "visual", "rect": rect})
                if area_ratio >= 0.035:
                    visual_rects.append(rect)
                    layout_objects.append({"kind": "visual", "rect": rect})
                if is_source:
                    source_rects.append(rect)

            for graphic in slide.findall(f".//{{{PML_NS}}}graphicFrame"):
                rect = _shape_geometry(graphic, "graphic", slide_width, slide_height)
                if rect is None:
                    continue
                area_ratio = rect["width"] * rect["height"] / (slide_width * slide_height)
                kind = "table" if graphic.find(f".//{{{DML_NS}}}tbl") is not None else "visual"
                content_objects.append({"kind": kind, "rect": rect})
                if area_ratio >= 0.035:
                    visual_rects.append(rect)
                    layout_objects.append({"kind": kind, "rect": rect})

            if oversized_boxes:
                issues.append(
                    f"PPTX OOXML slide {index} contains {oversized_boxes} oversized one-line text box(es) whose empty bounds inflate apparent canvas use."
                )
            content_rects = [item["rect"] for item in content_objects]
            results.append(
                {
                    "index": index,
                    "layoutTokens": _layout_tokens(layout_objects, slide_width, slide_height),
                    "layoutObjectCount": len(layout_objects),
                    "validVisualObjectCount": len(visual_rects),
                    "sourceScreenshotObjectCount": len(source_rects),
                    "validVisualAreaRatio": _grid_coverage(visual_rects, slide_width, slide_height),
                    "sourceScreenshotAreaRatio": _grid_coverage(source_rects, slide_width, slide_height),
                    "contentAreaRatio": _grid_coverage(content_rects, slide_width, slide_height),
                    "lowerHalfContentRatio": _grid_coverage(content_rects, slide_width, slide_height, slide_height / 2),
                    "pixelMetrics": None,
                }
            )
    return results, issues


def validate_pptx_editability(
    pptx_path: Path,
    expected_pages: int,
    slide_items: list[dict] | None = None,
    generated_visuals: list[dict] | None = None,
) -> list[str]:
    """Inspect OOXML directly so a full-slide screenshot cannot masquerade as editable PPTX."""
    issues: list[str] = []
    if not pptx_path.exists() or pptx_path.stat().st_size < 1024:
        return ["Editable PPTX export is missing or suspiciously small."]
    try:
        with zipfile.ZipFile(pptx_path) as archive:
            slide_names = sorted(
                (
                    name
                    for name in archive.namelist()
                    if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
                ),
                key=_slide_number,
            )
            if len(slide_names) != expected_pages:
                issues.append(
                    f"PPTX slide count does not match deck: pptx={len(slide_names)}, slides={expected_pages}."
                )
            if not slide_names:
                issues.append("PPTX contains no slide XML.")
                return issues

            slide_width, slide_height = 12192000, 6858000
            if "ppt/presentation.xml" in archive.namelist():
                presentation = ET.fromstring(archive.read("ppt/presentation.xml"))
                size = presentation.find(f".//{{{PML_NS}}}sldSz")
                if size is not None:
                    slide_width = int(size.get("cx", slide_width))
                    slide_height = int(size.get("cy", slide_height))

            first_slide = ET.fromstring(archive.read(slide_names[0]))
            editable_shapes: list[dict] = []
            for shape in first_slide.findall(f".//{{{PML_NS}}}sp"):
                text = "".join(node.text or "" for node in shape.findall(f".//{{{DML_NS}}}t")).strip()
                if not text:
                    continue
                xfrm = shape.find(f"./{{{PML_NS}}}spPr/{{{DML_NS}}}xfrm")
                offset = xfrm.find(f"{{{DML_NS}}}off") if xfrm is not None else None
                extent = xfrm.find(f"{{{DML_NS}}}ext") if xfrm is not None else None
                if offset is None or extent is None:
                    continue
                x = int(offset.get("x", "0"))
                y = int(offset.get("y", "0"))
                width = int(extent.get("cx", "0"))
                height = int(extent.get("cy", "0"))
                if width <= 0 or height <= 0 or x >= slide_width or y >= slide_height:
                    continue
                placeholder = shape.find(f"./{{{PML_NS}}}nvSpPr/{{{PML_NS}}}nvPr/{{{PML_NS}}}ph")
                placeholder_type = placeholder.get("type", "") if placeholder is not None else ""
                sizes = [
                    int(node.get("sz", "0"))
                    for node in shape.findall(f".//*[@sz]")
                    if node.get("sz", "").isdigit()
                ]
                editable_shapes.append(
                    {
                        "text": text,
                        "x": x,
                        "y": y,
                        "width": width,
                        "height": height,
                        "placeholder": placeholder_type,
                        "max_font_size": max(sizes, default=0),
                    }
                )

            title_shapes = [
                shape
                for shape in editable_shapes
                if shape["placeholder"] in {"title", "ctrTitle"}
                or (
                    shape["y"] < slide_height * 0.45
                    and shape["max_font_size"] >= 2400
                    and len(shape["text"]) >= 2
                )
            ]
            body_shapes = [
                shape
                for shape in editable_shapes
                if shape["placeholder"] in {"body", "subTitle", "obj"}
                or (
                    len(shape["text"]) >= 8
                    and shape["max_font_size"] >= 1200
                    and shape not in title_shapes
                )
            ]
            if not title_shapes:
                issues.append("PPTX first slide has no visible editable title text box; the title may be flattened into an image.")
            if not body_shapes:
                issues.append("PPTX first slide has no separate visible editable body/subtitle text box; body copy may be flattened into an image.")
            geometry_results, geometry_issues = inspect_pptx_geometry(pptx_path, slide_items, generated_visuals)
            issues.extend(geometry_issues)
            if slide_items:
                issues.extend(audit_rendered_design(geometry_results, slide_items, origin="PPTX OOXML"))
    except (OSError, zipfile.BadZipFile, ET.ParseError, KeyError, ValueError) as exc:
        issues.append(f"Editable PPTX OOXML could not be inspected: {exc}")
    return issues


def pixel_content_metrics(path: Path) -> dict[str, float] | None:
    if Image is None:
        return None
    try:
        with Image.open(path) as image:
            sample = image.convert("RGB").resize((320, 180))
            border_pixels = []
            for y in range(180):
                for x in (*range(0, 4), *range(316, 320)):
                    border_pixels.append(sample.getpixel((x, y)))
            for y in (*range(0, 4), *range(176, 180)):
                for x in range(4, 316):
                    border_pixels.append(sample.getpixel((x, y)))
            color_counts: dict[tuple[int, int, int], int] = {}
            for pixel in border_pixels:
                bucket = tuple(round(channel / 16) * 16 for channel in pixel)
                color_counts[bucket] = color_counts.get(bucket, 0) + 1
            background_palette = [
                color
                for color, _ in sorted(color_counts.items(), key=lambda item: item[1], reverse=True)[:6]
            ]
            pixels = list(sample.get_flattened_data()) if hasattr(sample, "get_flattened_data") else list(sample.getdata())
            foreground = [
                min(
                    sum(abs(pixel[channel] - background[channel]) for channel in range(3))
                    for background in background_palette
                )
                >= 36
                for pixel in pixels
            ]
            lower = foreground[320 * 90 :]
            return {
                "foreground_ratio": sum(foreground) / len(foreground),
                "lower_half_foreground_ratio": sum(lower) / len(lower),
            }
    except Exception:
        return None


def layouts_are_similar(left: dict, right: dict) -> bool:
    left_tokens = set(left.get("layoutTokens", []))
    right_tokens = set(right.get("layoutTokens", []))
    if not left_tokens or not right_tokens:
        return False
    overlap = len(left_tokens & right_tokens) / max(1, len(left_tokens | right_tokens))
    left_count = int(left.get("layoutObjectCount", 0))
    right_count = int(right.get("layoutObjectCount", 0))
    count_close = abs(left_count - right_count) <= max(1, round(max(left_count, right_count) * 0.25))
    return overlap >= 0.72 and count_close


def rendered_layout_family_count(results: list[dict]) -> int:
    representatives: list[dict] = []
    for result in results:
        if not any(layouts_are_similar(result, representative) for representative in representatives):
            representatives.append(result)
    return len(representatives)


def audit_rendered_design(results: list[dict], slide_items: list[dict], origin: str = "Rendered") -> list[str]:
    issues: list[str] = []
    body_results: list[dict] = []
    layout_results: list[dict] = []
    for result in results:
        index = result.get("index")
        slide = slide_items[index - 1] if isinstance(index, int) and 0 < index <= len(slide_items) else {}
        slide_type = str(slide.get("type", ""))
        if slide_type in NON_BODY_SLIDE_TYPES:
            continue
        body_results.append(result)
        if slide_type not in NON_LAYOUT_SLIDE_TYPES:
            layout_results.append(result)

        pixel_metrics = result.get("pixelMetrics") or {}
        lower_geometry = float(result.get("lowerHalfContentRatio", 0) or 0)
        lower_pixels = pixel_metrics.get("lower_half_foreground_ratio")
        if lower_geometry < 0.20 and (
            lower_pixels is None or float(lower_pixels) < 0.12
        ):
            issues.append(
                f"{origin} slide {index} leaves the lower half substantially blank: geometry={lower_geometry:.2f}, "
                f"pixels={float(lower_pixels or 0):.2f}."
            )

        content_area = float(result.get("contentAreaRatio", 0) or 0)
        foreground = pixel_metrics.get("foreground_ratio")
        if content_area < 0.38 and (foreground is None or float(foreground) < 0.24):
            issues.append(
                f"{origin} slide {index} underuses the canvas: meaningful content covers only {content_area:.2f} of the stage."
            )

        ordinary_page = str(slide.get("reasoning_role", "")) != "evidence" and str(slide.get("sequence_role", "")) not in {
            "evidence",
            "source-evidence",
            "evidence-close-reading",
        }
        source_ratio = float(result.get("sourceScreenshotAreaRatio", 0) or 0)
        if ordinary_page and source_ratio > 0.40:
            issues.append(
                f"{origin} slide {index} lets source screenshots occupy {source_ratio:.2f} of an ordinary teaching page; keep them at or below 0.40 or use a dedicated evidence page."
            )

    if body_results:
        visual_pages = [result for result in body_results if int(result.get("validVisualObjectCount", 0) or 0) > 0]
        visual_ratio = len(visual_pages) / len(body_results)
        if visual_ratio < 0.70:
            issues.append(
                f"{origin} effective visual-object coverage is below 70% of body slides: {len(visual_pages)}/{len(body_results)} ({visual_ratio:.0%})."
            )
        visual_objects = sum(int(result.get("validVisualObjectCount", 0) or 0) for result in body_results)
        source_objects = sum(int(result.get("sourceScreenshotObjectCount", 0) or 0) for result in body_results)
        if visual_objects >= 4 and source_objects / visual_objects > 0.60:
            issues.append(
                f"{origin} deck is source-screenshot dominated: {source_objects}/{visual_objects} effective visual objects are source screenshots."
            )

    if layout_results:
        family_count = rendered_layout_family_count(layout_results)
        required_families = 6 if len(slide_items) >= 20 else 4 if len(layout_results) >= 10 else 3 if len(layout_results) >= 6 else 1
        if family_count < required_families:
            issues.append(
                f"{origin} geometry provides only {family_count} materially different layouts; this deck requires at least {required_families}."
            )
        streak = 1
        for index in range(1, len(layout_results)):
            if layouts_are_similar(layout_results[index - 1], layout_results[index]):
                streak += 1
                if streak > 2:
                    issues.append(
                        f"The same or a similar {origin.lower()} structure repeats for more than two consecutive teaching slides near slide {layout_results[index].get('index')}."
                    )
                    break
            else:
                streak = 1
    return issues


def validate_pdf(
    pdf_path: Path,
    expected_pages: int,
    qa_dir: Path,
    slide_items: list[dict],
    html_screenshot_dir: Path,
) -> list[str]:
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
        sparse_pages: list[int] = []
        content_pages = 0
        for page_number in range(1, pages + 1):
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
                issues.append(f"Failed to render PDF page {page_number}.")
                continue
            slide_type = str(slide_items[page_number - 1].get("type", "")) if page_number <= len(slide_items) else ""
            if slide_type not in {"title", "divider", "evidence-appendix"}:
                content_pages += 1
                if Image is not None:
                    try:
                        with Image.open(rendered) as image:
                            sample = image.convert("RGB").resize((320, 180))
                            corners = [
                                sample.getpixel((2, 2)),
                                sample.getpixel((317, 2)),
                                sample.getpixel((2, 177)),
                                sample.getpixel((317, 177)),
                            ]
                            background = tuple(round(sum(point[channel] for point in corners) / 4) for channel in range(3))
                            pixels = list(sample.getdata())
                            foreground = sum(
                                1
                                for pixel in pixels
                                if sum(abs(pixel[channel] - background[channel]) for channel in range(3)) >= 36
                            ) / len(pixels)
                        if foreground < 0.10:
                            sparse_pages.append(page_number)
                        if foreground < 0.06:
                            issues.append(f"PDF page {page_number} is visually near-empty after export (foreground ratio {foreground:.3f}).")
                        html_screenshot = html_screenshot_dir / f"slide-{page_number:02d}.png"
                        if html_screenshot.exists() and ImageChops is not None and ImageStat is not None:
                            with Image.open(html_screenshot) as source_image, Image.open(rendered) as pdf_image:
                                source_thumb = source_image.convert("RGB").resize((320, 180))
                                pdf_thumb = pdf_image.convert("RGB").resize((320, 180))
                                delta = sum(ImageStat.Stat(ImageChops.difference(source_thumb, pdf_thumb)).mean) / 3
                            if delta > 20:
                                issues.append(f"PDF page {page_number} does not visually match the reviewed HTML slide (mean delta {delta:.1f}).")
                    except Exception:
                        issues.append(f"Could not inspect rendered PDF page {page_number}.")
        if content_pages and len(sparse_pages) / content_pages > 0.25:
            issues.append(f"Too many exported teaching pages are visually sparse: {sparse_pages} ({len(sparse_pages)}/{content_pages}).")
    return issues


def extract_pdf_text(pdf_path: Path) -> tuple[str, str | None]:
    pdftotext = command_path("pdftotext")
    if not pdftotext:
        return "", "pdftotext is unavailable; final PDF public copy cannot be extracted."
    result = subprocess.run(
        [pdftotext, "-layout", str(pdf_path), "-"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        return "", f"pdftotext could not extract final PDF: {(result.stderr or result.stdout).strip()[:240]}"
    return result.stdout, None


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
    source_has_experiments = inventory.get("source_has_experiments", inventory.get("paper_has_experiments"))
    if source_has_experiments is None:
        errors.append("Teaching inventory must record source_has_experiments.")
    elif source_has_experiments is True and not inventory.get("experiments"):
        errors.append("Teaching inventory says the source has experiments but experiments[] is empty.")
    final_items = {str(item.get("id")): item for item in manifest.get("slides", []) if item.get("id")}
    for concept in inventory.get("hard_concepts", []):
        for field in ("term", "plain_label", "field_definition", "plain_explanation", "author_usage", "common_misunderstanding", "definition_item_ids", "first_use_item_id", "visible_dom_ids"):
            if not concept.get(field):
                errors.append(f"Hard concept {concept.get('id', '[unknown]')} is missing {field}.")
        if not (concept.get("source_specific_meaning") or concept.get("paper_specific_meaning")):
            errors.append(f"Hard concept {concept.get('id', '[unknown]')} is missing source_specific_meaning.")
        concept_id = str(concept.get("id", ""))
        for dom_id in concept.get("visible_dom_ids", []) or []:
            if not re.search(rf'id=["\']{re.escape(str(dom_id))}["\']', html):
                errors.append(f"Hard concept {concept_id} explanation is not visible in HTML: {dom_id}")
        for item_id in concept.get("definition_item_ids", []):
            item = final_items.get(str(item_id))
            if not item:
                errors.append(f"Hard concept {concept_id} references missing definition slide {item_id}.")
            elif concept_id not in {str(value) for value in item.get("explained_concept_ids", [])}:
                errors.append(f"Definition slide {item_id} does not declare explained_concept_ids coverage for {concept_id}.")
        ordered_ids = list(final_items)
        first_use_id = str(concept.get("first_use_item_id", ""))
        definition_ids = [str(value) for value in concept.get("definition_item_ids", []) if str(value) in final_items]
        if first_use_id in final_items and definition_ids:
            if min(ordered_ids.index(value) for value in definition_ids) > ordered_ids.index(first_use_id):
                errors.append(f"Hard concept {concept_id} is first used before its definition/explanation slide.")
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
        if not setup_ids or not result_ids or not limitation_ids:
            errors.append(f"Experiment {experiment.get('id', '[unknown]')} needs setup_item_ids, result_item_ids, and limitation_item_ids.")
        for item_id in [*setup_ids, *result_ids, *limitation_ids]:
            if str(item_id) not in final_items:
                errors.append(f"Experiment {experiment.get('id', '[unknown]')} references missing final slide {item_id}.")
        experiment_id = str(experiment.get("id", ""))
        for item_id in limitation_ids:
            item = final_items.get(str(item_id), {})
            if experiment_id not in {str(value) for value in item.get("covered_experiment_limitations", [])}:
                errors.append(f"Experiment limitation slide {item_id} does not visibly cover {experiment_id}.")
        ordered_ids = list(final_items)
        valid_setup = [ordered_ids.index(str(item_id)) for item_id in setup_ids if str(item_id) in final_items]
        valid_results = [ordered_ids.index(str(item_id)) for item_id in result_ids if str(item_id) in final_items]
        if valid_setup and valid_results and max(valid_setup) >= min(valid_results):
            errors.append(f"Experiment {experiment.get('id', '[unknown]')} setup slides must precede result slides.")
    for formula in inventory.get("formula_or_algorithm_items", []):
        for field in ("expression_or_name", "plain_explanation", "expected_tokens", "render_item_ids"):
            if not formula.get(field):
                errors.append(f"Formula/algorithm {formula.get('id', '[unknown]')} is missing {field}.")
        expected_tokens = {str(token) for token in formula.get("expected_tokens", [])}
        for item_id in formula.get("render_item_ids", []):
            item = final_items.get(str(item_id))
            if not item:
                errors.append(f"Formula/algorithm {formula.get('id', '[unknown]')} references missing slide {item_id}.")
            elif not expected_tokens.issubset({str(token) for token in item.get("expected_labels", [])}):
                errors.append(f"Formula slide {item_id} expected_labels do not cover the required formula tokens.")
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
            mode_requirement = (entry.get("mode_requirement") or {}).get("presentation-pdf")
            if mode_requirement not in {"must-cover", "optional", "not-applicable"}:
                errors.append(f"Teaching inventory item has invalid presentation-pdf mode_requirement: {inventory_key}:{item_id}")
            omission_allowed = mode_requirement != "must-cover" or level == "secondary" or (level == "major" and size_mode == "concise")
            if status == "omitted":
                if not omission_allowed or not item.get("reason"):
                    errors.append(f"Required teaching item was omitted without an allowed reason: {inventory_key}:{item_id}")
            elif status != "covered" or not item.get("final_item_ids"):
                errors.append(f"Teaching coverage must be covered with final_item_ids: {inventory_key}:{item_id}")
    figure_explanations = manifest.get("major_figure_explanations", [])
    explanations_by_id = {
        str(item.get("figure_id")): item
        for item in figure_explanations
        if isinstance(item, dict) and item.get("figure_id")
    }
    covered_figure_ids = {
        str(item.get("inventory_id"))
        for item in manifest.get("major_figure_coverage", [])
        if item.get("status") == "covered" and item.get("inventory_id")
    }
    coverage_by_figure = {
        str(item.get("inventory_id")): {str(value) for value in item.get("final_item_ids", [])}
        for item in manifest.get("major_figure_coverage", [])
        if item.get("inventory_id")
    }
    valid_slide_ids = {str(item.get("id")) for item in manifest.get("slides", []) if item.get("id")}
    for figure_id in covered_figure_ids:
        explanation = explanations_by_id.get(figure_id)
        if not explanation:
            errors.append(f"Covered major figure lacks a reading explanation: {figure_id}")
            continue
        for field in (
            "final_slide_ids",
            "what_it_is",
            "how_to_read",
            "baseline_metric",
            "highlighted_region",
            "supported_conclusion",
            "limitation_or_not_applicable",
            "source_page",
            "visible_dom_ids",
        ):
            if explanation.get(field) in (None, "", []):
                errors.append(f"Major figure explanation {figure_id} is missing {field}.")
        for dom_id in explanation.get("visible_dom_ids", []):
            if not re.search(rf'id=["\']{re.escape(str(dom_id))}["\']', html):
                errors.append(f"Major figure explanation {figure_id} is not visible in HTML: {dom_id}")
        explanation_slide_ids = {str(value) for value in explanation.get("final_slide_ids", [])}
        if not explanation_slide_ids.issubset(valid_slide_ids):
            errors.append(f"Major figure explanation {figure_id} references missing slides.")
        if explanation_slide_ids != coverage_by_figure.get(figure_id, set()):
            errors.append(f"Major figure explanation {figure_id} slide ids disagree with major_figure_coverage.")
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


def browser_probe(html_path: Path, output_dir: Path, expected_ids_by_slide: dict[str, list[str]]) -> tuple[dict | None, str | None]:
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
  const expectedIdsBySlide = JSON.parse(process.argv[3] || '{}');
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
    const expectedVisibleIds = expectedIdsBySlide[String(index + 1)] || [];
	  const metrics = await page.locator('.slide, [data-slide]').nth(index).evaluate((slide, expectedVisibleIds) => {
	      const stageWidth = 1920;
	      const stageHeight = 1080;
	      const isVisible = el => {
	        const style = getComputedStyle(el);
	        const box = el.getBoundingClientRect();
	        return style.display !== 'none' && style.visibility !== 'hidden' && parseFloat(style.opacity || '1') > 0 && box.width > 2 && box.height > 2;
	      };
	      const clippedRect = el => {
	        const box = el.getBoundingClientRect();
	        const left = Math.max(0, box.left);
	        const top = Math.max(0, box.top);
	        const right = Math.min(stageWidth, box.right);
	        const bottom = Math.min(stageHeight, box.bottom);
	        return { left, top, right, bottom, width: Math.max(0, right - left), height: Math.max(0, bottom - top) };
	      };
	      const gridCoverage = (rects, yStart = 0) => {
	        const columns = 48;
	        const rows = 27;
	        const occupied = new Set();
	        rects.forEach(rect => {
	          const firstColumn = Math.max(0, Math.floor(rect.left / stageWidth * columns));
	          const lastColumn = Math.min(columns - 1, Math.floor(Math.max(rect.left, rect.right - 1) / stageWidth * columns));
	          const firstRow = Math.max(Math.floor(yStart / stageHeight * rows), Math.floor(rect.top / stageHeight * rows));
	          const lastRow = Math.min(rows - 1, Math.floor(Math.max(rect.top, rect.bottom - 1) / stageHeight * rows));
	          for (let row = firstRow; row <= lastRow; row += 1) {
	            for (let column = firstColumn; column <= lastColumn; column += 1) occupied.add(`${row}:${column}`);
	          }
	        });
	        const availableRows = rows - Math.floor(yStart / stageHeight * rows);
	        return occupied.size / Math.max(1, columns * availableRows);
	      };
	      const visualCandidates = [...slide.querySelectorAll('img,svg,canvas,table,[data-generated-visual-id],[data-source-evidence-id],[data-teaching-object]')]
	        .filter(isVisible)
	        .filter(el => {
	          const box = el.getBoundingClientRect();
	          const tagName = el.tagName.toUpperCase();
	          if (box.width < 220 || box.height < 120 || (box.width * box.height) / (stageWidth * stageHeight) < 0.035) return false;
	          if (tagName === 'IMG') return el.complete && el.naturalWidth > 0;
	          if (tagName === 'SVG') return el.querySelectorAll('path,line,polyline,polygon,rect,circle,ellipse,text').length >= 3;
	          if (tagName === 'TABLE') return el.querySelectorAll('td,th').length >= 4;
	          if (tagName === 'CANVAS') return true;
	          if (el.matches('[data-generated-visual-id],[data-source-evidence-id]')) return !!el.querySelector('img,svg,canvas,table');
	          const kind = (el.getAttribute('data-teaching-object') || el.getAttribute('data-visual-kind') || '').toLowerCase();
	          const structuredChildren = el.querySelectorAll('[data-diagram-label],.diagram-label,.callout,[data-step],[data-node],li,td,th').length;
	          return /diagram|chart|formula|example|comparison|timeline|map|system|process|mechanism/.test(kind) && structuredChildren >= 3;
	        });
	      const validVisualRects = visualCandidates.map(clippedRect).filter(rect => rect.width > 0 && rect.height > 0);
	      const sourceScreenshotElements = [...slide.querySelectorAll('[data-source-evidence-id] img,img[data-source-evidence-id],[data-source-screenshot],img')]
	        .filter(isVisible)
	        .filter(el => {
	          if (el.tagName.toUpperCase() !== 'IMG') return el.hasAttribute('data-source-screenshot');
	          const evidenceAncestor = el.closest('[data-source-evidence-id],[data-source-screenshot]');
	          const cue = `${el.id} ${el.className || ''} ${el.getAttribute('alt') || ''} ${el.getAttribute('src') || ''}`.toLowerCase();
	          return !!evidenceAncestor || /source|evidence|screenshot|crop|paper-page|原文|证据/.test(cue);
	        });
	      const sourceScreenshotRects = sourceScreenshotElements.map(clippedRect).filter(rect => rect.width > 0 && rect.height > 0);
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
      const textOverflow = bodyText.filter(el => {
        const container = el.closest('[data-bounds-check], [data-card], .card');
        if (!container || container === el) return false;
        const box = el.getBoundingClientRect();
        const parent = container.getBoundingClientRect();
        return box.left < parent.left - 2 || box.right > parent.right + 2 || box.top < parent.top - 2 || box.bottom > parent.bottom + 2;
      }).length;
      let textOverlap = 0;
      const textBoxes = bodyText.map(el => ({ el, box: el.getBoundingClientRect() })).filter(item => item.box.width > 2 && item.box.height > 2);
      for (let a = 0; a < textBoxes.length; a += 1) {
        for (let b = a + 1; b < textBoxes.length; b += 1) {
          if (textBoxes[a].el.contains(textBoxes[b].el) || textBoxes[b].el.contains(textBoxes[a].el)) continue;
          const left = Math.max(textBoxes[a].box.left, textBoxes[b].box.left);
          const right = Math.min(textBoxes[a].box.right, textBoxes[b].box.right);
          const top = Math.max(textBoxes[a].box.top, textBoxes[b].box.top);
          const bottom = Math.min(textBoxes[a].box.bottom, textBoxes[b].box.bottom);
          const intersection = Math.max(0, right - left) * Math.max(0, bottom - top);
          const smaller = Math.min(textBoxes[a].box.width * textBoxes[a].box.height, textBoxes[b].box.width * textBoxes[b].box.height);
          if (smaller > 0 && intersection / smaller > 0.12) textOverlap += 1;
        }
      }
      const clippedContainers = [...slide.querySelectorAll('[data-bounds-check], [data-card], .card')]
        .filter(el => el.scrollWidth > el.clientWidth + 2 || el.scrollHeight > el.clientHeight + 2).length;
	      const teachingObjects = validVisualRects.map(rect => ({ width: rect.width, height: rect.height, areaRatio: (rect.width * rect.height) / (stageWidth * stageHeight) }));
      const sourceEvidence = [...slide.querySelectorAll('[data-source-evidence-id]')].map(el => {
        const box = el.getBoundingClientRect();
        return { id: el.getAttribute('data-source-evidence-id'), width: Math.round(box.width), height: Math.round(box.height) };
      });
	      const contentElements = [...slide.querySelectorAll('h1,h2,h3,p,li,blockquote,td,th,[data-information-group],.information-group,img,svg,canvas,table,[data-teaching-object]')]
	        .filter(isVisible)
	        .filter(el => !el.closest('footer,.footnote,.citation'));
	      const contentRects = contentElements.map(clippedRect).filter(rect => rect.width >= 24 && rect.height >= 12 && rect.width * rect.height < stageWidth * stageHeight * 0.92);
	      const layoutElements = [...slide.querySelectorAll('h1,h2,h3,[data-information-group],.information-group,img,svg,canvas,table,[data-teaching-object]')]
	        .filter(isVisible)
	        .filter(el => !el.closest('footer,.footnote,.citation'))
	        .filter(el => {
	          const box = el.getBoundingClientRect();
	          return box.width * box.height >= stageWidth * stageHeight * 0.012 && box.width * box.height < stageWidth * stageHeight * 0.90;
	        });
	      const layoutTokens = new Set();
	      layoutElements.forEach(el => {
	        const box = clippedRect(el);
	        const kind = el.matches('img,svg,canvas,[data-teaching-object]') ? 'visual' : el.matches('table') ? 'table' : el.matches('h1,h2,h3') ? 'heading' : 'group';
	        const centerColumn = Math.min(5, Math.floor(((box.left + box.right) / 2) / stageWidth * 6));
	        const centerRow = Math.min(3, Math.floor(((box.top + box.bottom) / 2) / stageHeight * 4));
	        const widthBucket = Math.max(1, Math.min(4, Math.round(box.width / stageWidth * 4)));
	        const heightBucket = Math.max(1, Math.min(4, Math.round(box.height / stageHeight * 4)));
	        layoutTokens.add(`${kind}:${centerColumn}:${centerRow}:${widthBucket}:${heightBucket}`);
	      });
      const expectedVisibleFields = Object.fromEntries(expectedVisibleIds.map(id => {
        const el = document.getElementById(id);
        if (!el || !slide.contains(el)) return [id, { present: false, visible: false, text: '' }];
        const style = getComputedStyle(el);
        const box = el.getBoundingClientRect();
        return [id, {
          present: true,
          visible: style.display !== 'none' && style.visibility !== 'hidden' && box.width > 0 && box.height > 0,
          text: (el.innerText || el.textContent || '').trim()
        }];
      }));
      return {
        scrollWidth: slide.scrollWidth,
        scrollHeight: slide.scrollHeight,
        clientWidth: slide.clientWidth,
        clientHeight: slide.clientHeight,
        brokenImages,
        images,
        generatedVisuals,
        visibleText: slide.innerText || '',
        textChars: (slide.innerText || '').replace(/\s+/g, '').length,
        projectedMinBodyPx: projectedFonts.length ? Math.min(...projectedFonts) : null,
        nestedCards,
        textOverflow,
        textOverlap,
	        clippedContainers,
	        teachingObjectCount: teachingObjects.length,
	        validVisualObjectCount: visualCandidates.length,
	        sourceScreenshotObjectCount: sourceScreenshotElements.length,
	        teachingObjectAreaRatio: gridCoverage(validVisualRects),
	        validVisualAreaRatio: gridCoverage(validVisualRects),
	        sourceScreenshotAreaRatio: gridCoverage(sourceScreenshotRects),
	        contentAreaRatio: gridCoverage(contentRects),
	        lowerHalfContentRatio: gridCoverage(contentRects, stageHeight / 2),
	        contentBottomRatio: contentRects.length ? Math.max(...contentRects.map(rect => rect.bottom)) / stageHeight : 0,
	        informationGroupCount: slide.querySelectorAll('[data-information-group], .information-group').length,
        diagramLabelCount: slide.querySelectorAll('[data-diagram-label], .diagram-label, .callout').length,
        visibleClaimIds: [...slide.querySelectorAll('[data-claim-id]')]
          .filter(el => { const style = getComputedStyle(el); const box = el.getBoundingClientRect(); return style.display !== 'none' && style.visibility !== 'hidden' && box.width > 0 && box.height > 0; })
          .map(el => el.getAttribute('data-claim-id')),
        sourceEvidence,
	        layoutTokens: [...layoutTokens].sort(),
	        layoutObjectCount: layoutElements.length,
	        expectedVisibleFields
      };
    }, expectedVisibleIds);
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
            [str(node), "-e", code, str(html_path), str(output_dir), json.dumps(expected_ids_by_slide, ensure_ascii=False)],
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
    parser.add_argument("--source", help="Original source PDF/article; verifies the final deck belongs to the requested source")
    args = parser.parse_args()

    root, html_path = locate(Path(args.path).expanduser().resolve())
    errors: list[str] = []
    warnings: list[str] = []
    if args.strict and not args.source:
        errors.append("Strict deck audit requires --source so source identity cannot be self-reported.")

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
    visible_copy = html_visible_text(html)
    for issue in public_copy_issues(visible_copy):
        errors.append(f"Public deck copy has AI/template residue: {issue}")
    if any(token in html for token in ("□", "�")):
        errors.append("Public deck HTML contains missing/replacement glyphs.")

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
        if str(manifest.get("manifest_schema_version")) != "0.5":
            errors.append("Deck manifest schema version must be 0.5.")
        if manifest.get("output_mode") != "presentation-pdf":
            errors.append("Deck manifest output_mode must be presentation-pdf.")
        if manifest.get("presentation_intent") != "present-and-read":
            errors.append("Deck presentation_intent must be present-and-read.")
        reader_language = str(manifest.get("reader_language", ""))
        if not reader_language:
            errors.append("Deck manifest must record reader_language.")
        elif reader_language.lower().startswith("zh") and chinese_ratio(visible_copy) < 0.45:
            errors.append("Chinese-reader deck is not Chinese-dominant enough in visible copy.")
        size_mode = manifest.get("size_mode")
        if size_mode not in {"concise", "medium", "detailed"}:
            errors.append("Deck manifest must record resolved size_mode.")
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
        for index, story_item in enumerate(storyboard_slides):
            if index > 0:
                previous_id = str(storyboard_slides[index - 1].get("id", ""))
                if not story_item.get("previous_bridge") or str(story_item.get("previous_item_id")) != previous_id:
                    errors.append(f"Storyboard slide {story_item.get('id')} lacks a valid previous bridge/link.")
            if index < len(storyboard_slides) - 1:
                next_id = str(storyboard_slides[index + 1].get("id", ""))
                if not story_item.get("next_bridge") or str(story_item.get("next_item_id")) != next_id:
                    errors.append(f"Storyboard slide {story_item.get('id')} lacks a valid next bridge/link.")
        acts = storyboard.get("acts", []) if isinstance(storyboard, dict) else []
        if len(acts) < 3:
            errors.append("Storyboard has too few teaching acts to establish a coherent learning arc.")
        source_type = str(storyboard.get("source_type", "academic-paper"))
        if source_type in {"book", "book-chapter", "article", "essay"}:
            required_arc_roles = {"problem", "idea", "example", "synthesis", "limitation"}
        elif source_type in {"manual", "guide", "handbook"}:
            required_arc_roles = {"goal", "prerequisite", "procedure", "worked-example", "limitation"}
        else:
            required_arc_roles = {"problem", "prerequisite", "method", "evidence", "limitation"}
        arc_roles = {str(item.get("learning_role")) for item in acts if item.get("learning_role")}
        if not required_arc_roles.issubset(arc_roles):
            errors.append(f"Storyboard does not cover the required teaching arc for source_type={source_type}: {sorted(required_arc_roles)}.")

        argument_map = (storyboard.get("source_argument_map") or storyboard.get("paper_argument_map", {})) if isinstance(storyboard, dict) else {}
        for field in ("main_question", "thesis", "argument_steps", "evidence_route", "conclusion", "limitation"):
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

        opening_roles = [str(item.get("sequence_role", "")) for item in slide_items[:3]]
        if not any(role in {"source-overview", "paper-overview", "overview-and-argument-map"} for role in opening_roles):
            errors.append("A source overview must appear within the opening three slides.")
        if not any(role in {"argument-map", "overview-and-argument-map"} for role in opening_roles):
            errors.append("An argument map must appear by slide 3.")
        all_sequence_roles = [str(item.get("sequence_role", "")) for item in slide_items]
        valid_sequence_roles = {
            "cover-thesis",
            "paper-overview",
            "source-overview",
            "argument-map",
            "overview-and-argument-map",
            "prerequisite",
            "framework-overview",
            "method-detail",
            "argument-detail",
            "idea-detail",
            "chapter-progression",
            "example",
            "procedure",
            "failure-mode",
            "worked-example",
            "experiment-setup",
            "evidence",
            "conclusion",
            "limitation",
            "recap",
        }
        invalid_roles = sorted({role for role in all_sequence_roles if role not in valid_sequence_roles})
        if invalid_roles:
            errors.append(f"Deck contains invalid sequence_role values: {invalid_roles}")
        if "overview-and-argument-map" not in all_sequence_roles:
            overview_role = "source-overview" if "source-overview" in all_sequence_roles else "paper-overview"
            if overview_role in all_sequence_roles and "argument-map" in all_sequence_roles and all_sequence_roles.index(overview_role) > all_sequence_roles.index("argument-map"):
                errors.append("Source overview must precede the argument map.")
        for role in ("conclusion", "limitation", "recap"):
            if role not in all_sequence_roles:
                errors.append(f"Deck is missing required closing role: {role}")
        if "recap" in all_sequence_roles and all_sequence_roles[-1] != "recap":
            errors.append("The final slide must be the learner recap/reconstruction page.")
        recap_expected = storyboard.get("recap_expected_concepts", [])
        if len(recap_expected) < 5:
            errors.append("Storyboard recap_expected_concepts must cover at least problem, method, evidence, conclusion, and limitation.")
        if "recap" in all_sequence_roles:
            recap_slide = slide_items[all_sequence_roles.index("recap")]
            if not set(map(str, recap_expected)).issubset({str(value) for value in recap_slide.get("recap_concepts", [])}):
                errors.append("Final recap slide does not cover all recap_expected_concepts.")
        if all(role in all_sequence_roles for role in ("evidence", "conclusion", "limitation", "recap")):
            positions = [all_sequence_roles.index(role) for role in ("evidence", "conclusion", "limitation", "recap")]
            if positions != sorted(positions):
                errors.append("Closing teaching order must be evidence -> conclusion -> limitation -> recap.")
        detail_positions = [index for index, role in enumerate(all_sequence_roles) if role in {"method-detail", "argument-detail", "worked-example", "experiment-setup", "evidence"}]
        if "prerequisites_required" not in storyboard:
            errors.append("Storyboard must record prerequisites_required and its rationale.")
        if not storyboard.get("prerequisites_rationale"):
            errors.append("Storyboard is missing prerequisites_rationale.")
        if detail_positions and storyboard.get("prerequisites_required") is True and "prerequisite" not in all_sequence_roles[:min(detail_positions)]:
            errors.append("Prerequisite teaching must appear before detailed method or evidence pages.")
        if "method-detail" in all_sequence_roles:
            first_method_detail = all_sequence_roles.index("method-detail")
            if "framework-overview" not in all_sequence_roles[:first_method_detail]:
                errors.append("A framework overview must precede component-level detail.")
        if "worked_example_required" not in storyboard:
            errors.append("Storyboard must record worked_example_required and its rationale.")
        elif storyboard.get("worked_example_required") is True and "worked-example" not in all_sequence_roles:
            errors.append("Storyboard requires a worked example, but no worked-example slide exists.")
        if not storyboard.get("worked_example_rationale"):
            errors.append("Storyboard is missing worked_example_rationale.")
        method_stage_count = storyboard.get("method_stage_count")
        if not isinstance(method_stage_count, int) or method_stage_count < 0:
            errors.append("Storyboard must record a non-negative method_stage_count.")
        elif method_stage_count >= 3 and storyboard.get("worked_example_required") is not True:
            errors.append("A method with three or more stages must require a worked example.")
        source_has_experiments = storyboard.get("source_has_experiments", storyboard.get("paper_has_experiments"))
        if source_has_experiments is None:
            errors.append("Storyboard must record source_has_experiments.")
        elif source_has_experiments is True:
            if "experiment-setup" not in all_sequence_roles or "evidence" not in all_sequence_roles:
                errors.append("Experimental papers need experiment-setup and evidence pages.")
            elif all_sequence_roles.index("experiment-setup") > all_sequence_roles.index("evidence"):
                errors.append("Experiment setup must appear before result evidence.")

        layout_counts: dict[str, int] = {}
        content_slide_count = 0
        evidence_dense_streak = 0
        max_evidence_dense_streak = 0
        low_density_count = 0
        low_density_teaching_count = 0
        section_reset_count = 0
        for slide in slide_items:
            for field in ("id", "type", "learner_question", "one_sentence_answer", "layout_family", "sequence_role"):
                if not slide.get(field):
                    errors.append(f"Slide inventory entry is missing {field}.")
            if slide.get("type") not in {"title", "divider", "evidence-appendix"}:
                for field in ("sequence_role", "information_groups", "scan_order", "reader_takeaway", "teaching_units"):
                    if not slide.get(field):
                        errors.append(f"Presentation slide {slide.get('id')} is missing {field}.")
                role = str(slide.get("sequence_role", ""))
                groups = slide.get("information_groups", [])
                required_groups = 3
                if len(groups) < required_groups:
                    errors.append(f"Presentation slide {slide.get('id')} has too few information groups for {role}: {len(groups)}/{required_groups}.")
                if len(groups) > 7 or len({json.dumps(group, sort_keys=True, ensure_ascii=False) for group in groups}) != len(groups):
                    errors.append(f"Present-and-read slide {slide.get('id')} information_groups must contain 3-7 distinct groups.")
                if len(slide.get("scan_order", [])) < 3:
                    errors.append(f"Presentation slide {slide.get('id')} needs a scan_order with at least three steps.")
                if len(set(map(str, slide.get("scan_order", [])))) != len(slide.get("scan_order", [])):
                    errors.append(f"Presentation slide {slide.get('id')} scan_order contains repeated steps.")
                teaching_units = slide.get("teaching_units", [])
                if len(teaching_units) < required_groups:
                    errors.append(f"Presentation slide {slide.get('id')} has too few teaching_units: {len(teaching_units)}/{required_groups}.")
                for unit in teaching_units:
                    for field in ("claim_or_concept", "explanation", "visual_anchor", "source_ids"):
                        if not unit.get(field):
                            errors.append(f"Presentation slide {slide.get('id')} teaching unit is missing {field}.")
                    anchor_id = str(unit.get("visual_anchor", ""))
                    if anchor_id and not re.search(rf'id=["\']{re.escape(anchor_id)}["\']', html):
                        errors.append(f"Presentation slide {slide.get('id')} teaching unit visual anchor is not present in HTML: {anchor_id}")
                teaching_unit_names = [str(unit.get("claim_or_concept", "")) for unit in teaching_units]
                if len(set(teaching_unit_names)) != len(teaching_unit_names):
                    errors.append(f"Presentation slide {slide.get('id')} repeats the same teaching unit.")
                if role == "evidence":
                    evidence_objects = slide.get("source_evidence_objects", [])
                    if not evidence_objects:
                        errors.append(f"Evidence slide {slide.get('id')} has no source_evidence_objects.")
                    for evidence in evidence_objects:
                        for field in (
                            "evidence_id",
                            "source_id",
                            "source_page",
                            "object_type",
                            "reader_question",
                            "asset_path",
                            "asset_sha256",
                            "crop_bbox",
                            "display_width_px",
                            "display_height_px",
                            "annotated_regions",
                        ):
                            if evidence.get(field) in (None, "", []):
                                errors.append(f"Evidence slide {slide.get('id')} source object is missing {field}.")
                        if evidence.get("readable_at_final_size") is not True:
                            errors.append(f"Evidence slide {slide.get('id')} contains a source crop that is not readable at final size.")
                        evidence_asset = root / str(evidence.get("asset_path", ""))
                        if not evidence_asset.exists() or evidence_asset.suffix.lower() not in BITMAP_SUFFIXES:
                            errors.append(f"Evidence slide {slide.get('id')} source crop is missing or not a bitmap: {evidence.get('asset_path')}")
                        elif normalized_hash(evidence.get("asset_sha256")) != sha256(evidence_asset):
                            errors.append(f"Evidence slide {slide.get('id')} source crop hash is missing or incorrect.")
                        if evidence.get("display_width_px", 0) < 900 or evidence.get("display_height_px", 0) < 300:
                            errors.append(f"Evidence slide {slide.get('id')} source crop is displayed too small for teaching.")
                if role == "worked-example":
                    example = slide.get("worked_example", {})
                    for field in ("input", "stages", "output", "source_ids"):
                        if not example.get(field):
                            errors.append(f"Worked-example slide {slide.get('id')} is missing {field}.")
                    if isinstance(method_stage_count, int) and len(example.get("stages", [])) < method_stage_count:
                        errors.append(f"Worked-example slide {slide.get('id')} does not cover the full method pipeline.")
            for field in ("presentation_intent", "communication_job", "reasoning_role", "standalone_takeaway", "reader_context", "so_what", "density_class", "scan_order", "information_group_count", "visual_route"):
                if slide.get("type") not in {"title", "evidence-appendix"} and slide.get(field) in (None, "", []):
                    errors.append(f"Present-and-read slide {slide.get('id')} is missing {field}.")
            if slide.get("type") not in {"title", "evidence-appendix"} and slide.get("presentation_intent") != "present-and-read":
                errors.append(f"Slide {slide.get('id')} presentation_intent must be present-and-read.")
            if slide.get("type") not in {"title", "evidence-appendix"}:
                if slide.get("reasoning_role") not in {"question", "definition", "mechanism", "example", "evidence", "comparison", "conclusion", "boundary", "synthesis"}:
                    errors.append(f"Slide {slide.get('id')} has invalid reasoning_role.")
                if slide.get("density_class") not in {"low", "medium", "evidence-dense"}:
                    errors.append(f"Slide {slide.get('id')} has invalid density_class.")
                groups = slide.get("information_groups", [])
                if slide.get("information_group_count") != len(groups):
                    errors.append(f"Slide {slide.get('id')} information_group_count does not match information_groups.")
                if slide.get("visual_route") not in {"generated", "image-to-image", "deterministic", "source-crop", "mixed"}:
                    errors.append(f"Slide {slide.get('id')} has invalid visual_route.")
                visible_fields = (
                    ("communication_job", "communication_job_dom_id"),
                    ("standalone_takeaway", "standalone_takeaway_dom_id"),
                    ("reader_context", "reader_context_dom_id"),
                    ("so_what", "so_what_dom_id"),
                )
                for value_field, dom_field in visible_fields:
                    dom_id = str(slide.get(dom_field, ""))
                    if not dom_id:
                        errors.append(f"Slide {slide.get('id')} is missing {dom_field}.")
                    elif not re.search(rf'id=["\']{re.escape(dom_id)}["\']', html):
                        errors.append(f"Slide {slide.get('id')} {value_field} is not visible in HTML: {dom_id}")
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
                if slide.get("type") not in {"title", "divider"} and not slide.get("low_density_reason"):
                    errors.append(f"Low-density slide {slide.get('id')} lacks low_density_reason.")
                if slide.get("type") not in {"title", "divider", "evidence-appendix"}:
                    low_density_teaching_count += 1
            if slide.get("section_reset") is True:
                section_reset_count += 1
            if slide.get("type") not in {"title", "divider", "recap", "evidence-appendix"}:
                content_slide_count += 1
                family = str(slide.get("layout_family", ""))
                layout_counts[family] = layout_counts.get(family, 0) + 1
        if content_slide_count and layout_counts:
            dominant_family, dominant_count = max(layout_counts.items(), key=lambda item: item[1])
            if dominant_count / content_slide_count > 0.60 and not manifest.get("layout_repetition_rationale"):
                errors.append(f"One layout family dominates {dominant_count}/{content_slide_count} teaching slides without rationale: {dominant_family}")
            if content_slide_count >= 10 and len(layout_counts) < 4:
                warnings.append(f"Manifest declares fewer than four composition families ({len(layout_counts)}); rendered geometry is authoritative.")
        content_layout_sequence = [
            str(slide.get("layout_family", ""))
            for slide in slide_items
            if slide.get("type") not in {"title", "divider", "recap", "evidence-appendix"}
        ]
        streak = 1
        for index in range(1, len(content_layout_sequence)):
            if content_layout_sequence[index] == content_layout_sequence[index - 1]:
                streak += 1
                if streak > 2:
                    warnings.append(f"Manifest repeats the same slide composition more than twice near teaching slide {index + 1}: {content_layout_sequence[index]}; rendered geometry is authoritative.")
                    break
            else:
                streak = 1
        if max_evidence_dense_streak > 3:
            errors.append("Presentation contains more than three consecutive evidence-dense pages without a reset.")
        teaching_page_count = len([slide for slide in slide_items if slide.get("type") not in {"title", "divider", "evidence-appendix"}])
        if teaching_page_count and low_density_teaching_count / teaching_page_count > 0.15:
            errors.append(f"Low-density slides exceed the present-and-read allowance: {low_density_teaching_count}/{teaching_page_count}.")
        if size_mode in {"medium", "detailed"} and section_reset_count < 2:
            errors.append("Medium/detailed presentation needs at least two visible section resets.")

        visuals = manifest.get("generated_visuals", [])
        actual_ocr_records: dict[str, dict] = {}
        if args.strict:
            ocr_paths = [root / str(item.get("path", "")) for item in visuals if item.get("path")]
            actual_ocr, actual_ocr_error = run_actual_ocr([path for path in ocr_paths if path.exists()])
            if actual_ocr_error:
                errors.append(actual_ocr_error)
            elif actual_ocr is not None:
                actual_ocr_records = actual_ocr
        expected_visuals = manifest.get("generated_visuals_expected")
        hard_concepts = [item for item in manifest.get("hard_concepts", []) if item.get("visual_needed", True)]
        logic_units = manifest.get("logic_units", [])
        derived_visual_floor = max(len(hard_concepts), len(logic_units), derived_teaching_visual_floor)
        if isinstance(expected_visuals, int) and expected_visuals < derived_visual_floor:
            errors.append(f"generated_visuals_expected is below the derived concept/chapter floor: {expected_visuals}/{derived_visual_floor}")
        if isinstance(expected_visuals, int) and len(visuals) < expected_visuals:
            errors.append(f"Generated visual coverage is incomplete: {len(visuals)}/{expected_visuals}")
        if not isinstance(expected_visuals, int) or expected_visuals < 1:
            errors.append("generated_visuals_expected=0 bypasses the visual-first deck contract.")
        if not visuals:
            errors.append("Every non-trivial presentation must embed at least one real generated bitmap.")
        smoke_test = manifest.get("image_generation_smoke_test", {})
        for field in ("status", "tool", "model", "receipt", "local_asset_path"):
            if smoke_test.get(field) in (None, "", []):
                errors.append(f"Image-generation smoke test is missing {field}.")
        if smoke_test.get("status") != "passed":
            errors.append("Image-generation smoke test must record status=passed before deck completion.")
        smoke_asset = root / str(smoke_test.get("local_asset_path", ""))
        if not smoke_asset.exists() or smoke_asset.suffix.lower() not in BITMAP_SUFFIXES:
            errors.append("Image-generation smoke test local_asset_path is missing or not a real bitmap.")
        planned_generated_ids = {
            str(slide.get("id"))
            for slide in slide_items
            if slide.get("visual_route") in {"generated", "image-to-image"}
        }
        fulfilled_generated_ids = {str(item.get("slide_id")) for item in visuals if item.get("slide_id")}
        if planned_generated_ids - fulfilled_generated_ids:
            errors.append(f"Planned generated/image-to-image slides lack real generated assets: {sorted(planned_generated_ids - fulfilled_generated_ids)}")

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
                for issue in validate_generated_asset_provenance(item, asset, root):
                    errors.append(f"Generated visual provenance failed for {rel}: {issue}")
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
                "ocr_text",
                "ocr_engine",
                "ocr_artifact_path",
                "ocr_artifact_sha256",
            ):
                if not item.get(field):
                    errors.append(f"Generated visual {rel} is missing {field}.")
            if item.get("crop_checked") is not True:
                errors.append(f"Generated visual has not passed crop inspection: {rel}")
            expected_labels = item.get("expected_labels", [])
            ocr_text = str(item.get("ocr_text", ""))
            ocr_artifact_rel = str(item.get("ocr_artifact_path", ""))
            if ocr_artifact_rel:
                ocr_artifact = root / ocr_artifact_rel
                if not ocr_artifact.exists():
                    errors.append(f"Generated visual OCR artifact does not exist: {ocr_artifact_rel}")
                else:
                    actual_ocr_text = ocr_artifact.read_text(encoding="utf-8", errors="replace")
                    if normalized_hash(item.get("ocr_artifact_sha256")) != sha256(ocr_artifact):
                        errors.append(f"Generated visual OCR artifact hash is missing or incorrect: {ocr_artifact_rel}")
                    if actual_ocr_text.strip() != ocr_text.strip():
                        errors.append(f"Generated visual OCR text does not match the stored artifact: {rel}")
            if any(token in ocr_text for token in ("□", "�")):
                errors.append(f"Generated visual OCR contains missing/replacement glyphs: {rel}")
            actual_record = actual_ocr_records.get(str(asset.resolve())) if asset.exists() else None
            actual_text = str(actual_record.get("text", "")) if actual_record else ""
            if args.strict and not actual_record:
                errors.append(f"Strict OCR did not return a record for generated visual: {rel}")
            if actual_record and actual_record.get("error"):
                errors.append(f"Strict OCR failed for generated visual {rel}: {actual_record.get('error')}")
            if actual_text and any(token in actual_text for token in ("□", "�")):
                errors.append(f"Strict OCR detected missing/replacement glyphs in generated visual: {rel}")
            copy_text = actual_text or ocr_text
            if reader_language.lower().startswith("zh") and copy_text and chinese_ratio(copy_text) < 0.35:
                errors.append(f"Chinese-reader generated visual is not Chinese-dominant enough: {rel}")
            for issue in public_copy_issues(copy_text):
                errors.append(f"Generated visual public copy has AI/template residue ({issue}): {rel}")
            for token in FORBIDDEN_PUBLIC_TEXT:
                if token.lower() in copy_text.lower():
                    errors.append(f"Generated visual contains production wording '{token}': {rel}")
            actual_missing_labels = [str(label) for label in expected_labels if str(label) and str(label) not in actual_text]
            if args.strict and actual_missing_labels:
                errors.append(f"Strict OCR could not find expected labels {actual_missing_labels[:5]} in generated visual: {rel}")
            owner_slide = next((slide for slide in slide_items if str(slide.get("id")) == str(item.get("slide_id"))), {})
            owner_type = str(owner_slide.get("type", ""))
            if owner_type not in {"title", "divider"}:
                labels = item.get("diagram_labels", [])
                semantic_map = item.get("visual_semantic_map", [])
                integration = item.get("text_integration", {})
                relation_type = str(item.get("visual_relation_type", ""))
                if len(labels) < 3:
                    errors.append(f"Generated teaching visual needs at least three explanatory diagram_labels: {rel}")
                missing_labels = [str(label) for label in labels if str(label) and str(label) not in ocr_text]
                if missing_labels:
                    errors.append(f"Generated teaching visual OCR is missing diagram labels {missing_labels[:5]}: {rel}")
                if len(semantic_map) < 2:
                    errors.append(f"Generated teaching visual lacks a visual_semantic_map: {rel}")
                if relation_type not in {"causal", "spatial", "comparative", "sequential", "quantitative", "hierarchical"}:
                    errors.append(f"Generated teaching visual does not declare a real teaching relationship: {rel}")
                relation_labels = [str(label) for label in item.get("visual_relation_labels", [])]
                if len(relation_labels) < 2 or any(label not in ocr_text for label in relation_labels):
                    errors.append(f"Generated teaching visual relationship is not anchored by OCR-visible labels: {rel}")
                if integration.get("mode") not in {"in-model", "reserved-zone-overlay", "source-annotation"}:
                    errors.append(f"Generated teaching visual has no valid text-integration mode: {rel}")
                if integration.get("planned_before_generation") is not True:
                    errors.append(f"Generated teaching visual labels were not planned before generation: {rel}")
                if integration.get("native_resolution_composite") is not True:
                    errors.append(f"Generated teaching visual text was not composed at native output resolution: {rel}")
                if integration.get("mode") == "reserved-zone-overlay" and integration.get("label_zones_planned") is not True:
                    errors.append(f"Reserved-zone overlay lacks planned label zones: {rel}")
                if not expected_labels:
                    errors.append(f"Generated teaching visual has empty expected_labels, so OCR is meaningless: {rel}")
                visual_language = str(item.get("in_image_text_language", "")).lower()
                if reader_language.lower().startswith("zh") and not any(token in visual_language for token in ("zh", "chinese", "中文")):
                    errors.append(f"Chinese-reader teaching visual is not recorded as Chinese-dominant: {rel}")
            if expected_labels and not item.get("ocr_pass"):
                errors.append(f"Generated visual with text has not passed OCR label comparison: {rel}")
            if item.get("display_width_px", 0) < 700 or item.get("display_height_px", 0) < 390:
                errors.append(f"Generated visual is displayed too small to be a primary teaching object: {rel}")

        source = manifest.get("source_fidelity", {})
        source_hash = source.get("source_sha256") or source.get("source_pdf_sha256")
        source_format = str(source.get("source_format") or "").lower()
        if not source_hash:
            errors.append("Source fidelity is missing source_sha256/source_pdf_sha256.")
        if source_format == "pdf" and not source.get("page_count"):
            errors.append("PDF source fidelity is missing page_count.")
        if not manifest.get("source_title"):
            errors.append("Deck manifest is missing source_title.")
        if args.source:
            requested_source = Path(args.source).expanduser().resolve()
            if not requested_source.exists():
                errors.append(f"Requested source does not exist: {requested_source}")
            else:
                requested_hash = sha256(requested_source)
                if normalized_hash(source_hash) != requested_hash:
                    errors.append("P0 source identity mismatch: deck manifest does not belong to the requested source file.")
                if requested_source.suffix.lower() == ".pdf":
                    pdfinfo = command_path("pdfinfo")
                    if pdfinfo:
                        result = subprocess.run([pdfinfo, str(requested_source)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
                        match = re.search(r"^Pages:\s+(\d+)", result.stdout, re.M) if result.returncode == 0 else None
                        if match and source.get("page_count") != int(match.group(1)):
                            errors.append("P0 source identity mismatch: manifest page_count differs from the requested PDF.")
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
                    if normalized_hash(inventory.get("source_sha256")) != normalized_hash(source_hash):
                        errors.append("Source inventory hash does not match manifest source hash.")
                    if source_format == "pdf" and inventory.get("page_count") != source.get("page_count"):
                        errors.append("Source inventory page_count does not match manifest source fidelity.")
                    if str(inventory.get("source_title", "")).strip() != str(manifest.get("source_title", "")).strip():
                        errors.append("Source inventory title does not match manifest source_title.")
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
                if str(final_item_id) not in set(manifest_slide_ids):
                    errors.append(f"paper_argument_map references missing final slide id: {final_item_id}")
        opening_slide_records = [slide for slide in slide_items[:3] if slide.get("sequence_role") in {"paper-overview", "argument-map", "overview-and-argument-map"}]
        covered_argument_ids = {str(value) for slide in opening_slide_records for value in slide.get("covered_argument_step_ids", [])}
        if argument_record_ids - covered_argument_ids:
            errors.append(f"Opening overview/argument-map slides do not visibly cover argument records: {sorted(argument_record_ids - covered_argument_ids)}")

        for slide in slide_items:
            for source_id in slide.get("source_ids", []):
                if source_ids and str(source_id) not in source_ids:
                    errors.append(f"Slide references a missing source id: {source_id}")

        claims = manifest.get("claim_evidence_map", [])
        expected_claim_ids = {
            str(item.get("inventory_id"))
            for item in manifest.get("central_claim_coverage", [])
            if item.get("status") == "covered" and item.get("inventory_id")
        }
        mapped_claim_ids = {str(claim.get("claim_id")) for claim in claims if claim.get("claim_id")}
        if expected_claim_ids - mapped_claim_ids:
            errors.append(f"Covered central claims are missing from claim_evidence_map: {sorted(expected_claim_ids - mapped_claim_ids)}")
        for claim in claims:
            for field in (
                "claim_id",
                "claim_role",
                "claim_wording",
                "claim_dom_id",
                "source_ids",
                "comparison_baseline",
                "comparison_validity",
                "metric_or_dimension",
                "direction_or_value",
                "evidence_items",
                "evidence_strength",
                "limitation",
            ):
                if not claim.get(field):
                    errors.append(f"Claim evidence entry is missing {field}.")
            wording = str(claim.get("claim_wording", ""))
            if wording and wording not in html:
                errors.append(f"Claim wording is not visible in final deck HTML: {wording[:120]}")
            claim_dom_id = str(claim.get("claim_dom_id", ""))
            claim_id = str(claim.get("claim_id", ""))
            if claim_dom_id and not re.search(
                rf'<(?=[^>]*id=["\']{re.escape(claim_dom_id)}["\'])(?=[^>]*data-claim-id=["\']{re.escape(claim_id)}["\'])[^>]+>',
                html,
                re.I,
            ):
                errors.append(f"Claim DOM element is missing its visible data-claim-id binding: {claim_id}")
            if claim.get("comparison_validity") not in {"controlled", "descriptive", "cross-benchmark", "not-applicable"}:
                errors.append(f"Claim has invalid comparison_validity: {claim.get('comparison_validity')}")
            if re.search(r"(?:证明|证实|验证了|击败|打败|优于|超越|导致|带来|使得|归因于|显著提高|提升了|proves?|demonstrates?|validates?|beats?|outperforms?|causes?|leads?\s+to|improves?\s+by)", wording, re.I) and claim.get("comparison_validity") != "controlled":
                errors.append(f"Overstated claim without a controlled comparison: {wording[:120]}")
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
            "style_selection_basis",
            "color_roles",
            "typography_roles",
            "grid_system",
            "title_system",
            "forbidden_layouts",
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
            "independent_reading_checked",
            "reading_rhythm_checked",
            "laptop_pdf_legibility_checked",
            "overview_sequence_checked",
            "in_image_explanation_checked",
            "information_density_checked",
            "consulting_report_density_checked",
            "anti_ai_public_copy_checked",
            "key_figure_explanations_checked",
            "title_story_checked",
            "glyph_integrity_checked",
            "template_residue_checked",
            "source_crop_readability_checked",
        ):
            if qa.get(field) is not True:
                errors.append(f"Deck QA has not passed {field}.")
        if qa.get("orphan_generated_visuals") != 0:
            errors.append("Deck QA reports orphan generated visuals.")
        adversarial_passes = qa.get("adversarial_passes", [])
        review_rounds = {str(item.get("round")) for item in adversarial_passes if isinstance(item, dict) and item.get("round") is not None}
        if len(review_rounds) < 2 or not has_full_review_lenses(adversarial_passes):
            errors.append("Deck QA must record at least two rounds covering visual, information, teaching logic, novice comprehension, factual accuracy, public copy, and technical rendering.")
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
                slide_reviews = qa_report.get("slide_reviews", [])
                if len(slide_reviews) != len(slide_items):
                    errors.append(f"QA report needs one slide_reviews entry per slide: {len(slide_reviews)}/{len(slide_items)}.")
                reviewed_ids = {str(review.get("slide_id")) for review in slide_reviews if isinstance(review, dict)}
                if reviewed_ids != set(manifest_slide_ids):
                    errors.append("QA slide review ids do not match the final slide ids.")
                finding_counts: dict[str, int] = {}
                for review in slide_reviews:
                    for field in (
                        "slide_id",
                        "visual_status",
                        "information_status",
                        "narrative_status",
                        "findings",
                        "fixes",
                        "review_evidence_path",
                        "reviewed_screenshot_sha256",
                        "final_status",
                    ):
                        if review.get(field) in (None, "", []):
                            errors.append(f"QA slide review is missing {field}: {review.get('slide_id', '[unknown]')}")
                    for status_field in ("visual_status", "information_status", "narrative_status", "final_status"):
                        if review.get(status_field) not in {"passed", "fixed"}:
                            errors.append(f"QA slide review has invalid {status_field}: {review.get('slide_id', '[unknown]')}")
                    findings = re.sub(r"\s+", " ", str(review.get("findings", "")).strip().lower())
                    if len(findings) < 20:
                        errors.append(f"QA slide review findings are too generic: {review.get('slide_id', '[unknown]')}")
                    if findings:
                        finding_counts[findings] = finding_counts.get(findings, 0) + 1
                    evidence_path = root / str(review.get("review_evidence_path", ""))
                    if not evidence_path.exists():
                        errors.append(f"QA slide review evidence path does not exist: {review.get('review_evidence_path')}")
                    elif normalized_hash(review.get("reviewed_screenshot_sha256")) != sha256(evidence_path):
                        errors.append(f"QA slide review screenshot hash is missing or incorrect: {review.get('slide_id')}")
                if any(repetitions > 2 for repetitions in finding_counts.values()):
                    errors.append("QA slide reviews reuse generic findings across more than two slides.")
        if args.require_pdf:
            exports = manifest.get("exports", {})
            pptx_rel = exports.get("pptx_path")
            if not pptx_rel:
                errors.append("Editable PPTX export is missing.")
            else:
                pptx_path = root / str(pptx_rel)
                if not pptx_path.exists() or pptx_path.stat().st_size < 1024 or pptx_path.read_bytes()[:2] != b"PK":
                    errors.append("Editable PPTX export is missing, suspiciously small, or invalid.")
                else:
                    errors.extend(validate_pptx_editability(pptx_path, len(slide_items), slide_items, visuals))
                    if normalized_hash(exports.get("pptx_sha256")) != sha256(pptx_path):
                        errors.append("Final PPTX hash is missing or does not match the exported file.")
            pdf_rel = exports.get("pdf_path")
            if not pdf_rel:
                errors.append("Final presentation PDF export is missing.")
            else:
                pdf_path = root / str(pdf_rel)
                errors.extend(
                    validate_pdf(
                        pdf_path,
                        len(slide_items),
                        root / "qa" / "pdf-render-check",
                        slide_items,
                        root / "qa" / "screenshots",
                    )
                )
                declared_pdf_hash = normalized_hash(exports.get("pdf_sha256"))
                if pdf_path.exists() and (not declared_pdf_hash or declared_pdf_hash != sha256(pdf_path)):
                    errors.append("Final PDF hash is missing or does not match the exported file.")
                if pdf_path.exists():
                    pdf_text, pdf_text_error = extract_pdf_text(pdf_path)
                    if pdf_text_error:
                        errors.append(pdf_text_error)
                    else:
                        if reader_language.lower().startswith("zh") and chinese_ratio(pdf_text) < 0.35:
                            errors.append("Final PDF extracted text is not Chinese-dominant enough.")
                        for issue in public_copy_issues(pdf_text):
                            errors.append(f"Final PDF public copy has AI/template residue: {issue}")
                        for token in FORBIDDEN_PUBLIC_TEXT:
                            if token.lower() in pdf_text.lower():
                                errors.append(f"Final PDF contains production wording: {token}")

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
        expected_ids_by_slide = {
            str(index): [
                str(slide.get(field))
                for field in (
                    "communication_job_dom_id",
                    "standalone_takeaway_dom_id",
                    "reader_context_dom_id",
                    "so_what_dom_id",
                )
                if slide.get(field)
            ]
            for index, slide in enumerate(slide_items, 1)
        }
        probe, probe_error = browser_probe(html_path, root / "qa" / "screenshots", expected_ids_by_slide)
        if probe_error:
            errors.append(probe_error)
        elif probe:
            if probe.get("slideCount") != len(slides):
                errors.append("Browser-rendered slide count does not match static slide count.")
            visible_claim_ids: set[str] = set()
            rendered_source_evidence: dict[str, dict] = {}
            rendered_results: list[dict] = []
            for result in probe.get("results", []):
                index = result.get("index")
                slide_item = slide_items[index - 1] if isinstance(index, int) and 0 < index <= len(slide_items) else {}
                slide_type = str(slide_item.get("type", ""))
                density_class = str(slide_item.get("density_class", ""))
                visible_claim_ids.update(str(value) for value in result.get("visibleClaimIds", []) if value)
                for evidence in result.get("sourceEvidence", []):
                    if evidence.get("id"):
                        rendered_source_evidence[str(evidence.get("id"))] = evidence
                screenshot_path = Path(str(result.get("screenshot", "")))
                result["pixelMetrics"] = pixel_content_metrics(screenshot_path) if screenshot_path.exists() else None
                rendered_results.append(result)
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
                if result.get("textChars", 0) > 1600:
                    errors.append(f"Slide {index} is too text-dense even for reading-first mode: {result.get('textChars')} visible characters.")
                visible_slide_text = str(result.get("visibleText", ""))
                if reader_language.lower().startswith("zh") and visible_slide_text and chinese_ratio(visible_slide_text) < 0.35:
                    errors.append(f"Slide {index} browser-visible copy is not Chinese-dominant enough.")
                for issue in public_copy_issues(visible_slide_text):
                    errors.append(f"Slide {index} browser-visible copy has AI/template residue: {issue}")
                for dom_id, field_state in result.get("expectedVisibleFields", {}).items():
                    if not field_state.get("present") or not field_state.get("visible"):
                        errors.append(f"Slide {index} reading-first field is not browser-visible: {dom_id}")
                    elif len(str(field_state.get("text", "")).strip()) < 8:
                        errors.append(f"Slide {index} reading-first field is too empty to teach: {dom_id}")
                if result.get("projectedMinBodyPx") is not None and result.get("projectedMinBodyPx") < 12:
                    errors.append(f"Slide {index} body text becomes too small at 1366x768 projection: {result.get('projectedMinBodyPx'):.1f}px.")
                if result.get("nestedCards", 0) > 0:
                    errors.append(f"Slide {index} contains nested card-like components, which harms presentation hierarchy.")
                if result.get("textOverflow", 0) > 0:
                    errors.append(f"Slide {index} has {result.get('textOverflow')} text blocks outside their card/container bounds.")
                if result.get("textOverlap", 0) > 0:
                    errors.append(f"Slide {index} has {result.get('textOverlap')} overlapping text-block pairs.")
                if result.get("clippedContainers", 0) > 0:
                    errors.append(f"Slide {index} has {result.get('clippedContainers')} clipped semantic containers.")
                if slide_type not in {"title", "divider", "evidence-appendix"}:
                    if result.get("informationGroupCount", 0) < 3:
                        errors.append(f"Slide {index} does not expose at least three visible data-information-group teaching groups.")
                    if result.get("contentAreaRatio", 0) < 0.38 and result.get("informationGroupCount", 0) < 3:
                        errors.append(f"Slide {index} lacks both canvas utilization and a complete visible teaching structure.")
            expected_visible_claim_ids = {
                str(claim.get("claim_id"))
                for claim in manifest.get("claim_evidence_map", [])
                if claim.get("claim_id")
            } if manifest and not manifest.get("_invalid") else set()
            if expected_visible_claim_ids - visible_claim_ids:
                errors.append(f"Claim map entries are not visible in rendered slides: {sorted(expected_visible_claim_ids - visible_claim_ids)}")
            expected_source_evidence = {
                str(evidence.get("evidence_id")): evidence
                for slide in slide_items
                for evidence in slide.get("source_evidence_objects", [])
                if evidence.get("evidence_id")
            }
            missing_evidence = set(expected_source_evidence) - set(rendered_source_evidence)
            if missing_evidence:
                errors.append(f"Source evidence objects are not present in rendered slides: {sorted(missing_evidence)}")
            for evidence_id, rendered in rendered_source_evidence.items():
                if evidence_id in expected_source_evidence and (rendered.get("width", 0) < 900 or rendered.get("height", 0) < 300):
                    errors.append(f"Rendered source evidence {evidence_id} is too small: {rendered.get('width')}x{rendered.get('height')}.")
            errors.extend(audit_rendered_design(rendered_results, slide_items))

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
