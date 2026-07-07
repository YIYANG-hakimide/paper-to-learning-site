#!/usr/bin/env python3
"""Static audit for paper-to-learning-site outputs."""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


class SiteHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.images: list[tuple[str, str, int]] = []
        self.iframes: list[tuple[str, int]] = []
        self.buttons: list[tuple[dict[str, str], int]] = []
        self.starttags: list[tuple[str, dict[str, str], int]] = []
        self.class_counts: dict[str, int] = {}
        self._current_button: dict[str, str] | None = None
        self._button_text: list[str] = []
        self._line = 1

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {k: (v or "") for k, v in attrs}
        self._line = self.getpos()[0]
        self.starttags.append((tag, attr, self._line))
        for class_name in attr.get("class", "").split():
            self.class_counts[class_name] = self.class_counts.get(class_name, 0) + 1
        if "id" in attr:
            self.ids.append(attr["id"])
        if tag == "img":
            self.images.append((attr.get("src", ""), attr.get("alt", ""), self._line))
        if tag == "iframe":
            self.iframes.append((attr.get("src", ""), self._line))
        if tag == "button":
            self._current_button = attr
            self._button_text = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "button" and self._current_button is not None:
            attrs = dict(self._current_button)
            attrs["_text"] = " ".join("".join(self._button_text).split())
            self.buttons.append((attrs, self.getpos()[0]))
            self._current_button = None
            self._button_text = []

    def handle_data(self, data: str) -> None:
        if self._current_button is not None:
            self._button_text.append(data)


def is_external_or_embedded(src: str) -> bool:
    if not src:
        return False
    if src.startswith(("data:", "blob:", "#")):
        return True
    parsed = urlparse(src)
    return bool(parsed.scheme and parsed.scheme not in {"file"})


def find_html_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    return sorted(target.rglob("*.html"))


def load_manifest(root: Path) -> dict[str, object] | None:
    candidates = [
        root / "data" / "learning-site-manifest.json",
        root / "learning-site-manifest.json",
        root / "data" / "manifest.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            try:
                data = json.loads(candidate.read_text(encoding="utf-8"))
            except Exception as exc:
                return {"_manifest_error": f"{candidate}: {exc}"}
            data["_manifest_path"] = str(candidate)
            return data
    return None


def chrome_path() -> str | None:
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    return shutil.which("google-chrome") or shutil.which("google-chrome-stable") or shutil.which("chromium") or shutil.which("chromium-browser")


def run_mobile_render_check(path: Path, root: Path) -> tuple[list[str], list[str]]:
    chrome = chrome_path()
    if not chrome:
        return [], [f"{path}: Chrome/Chromium not found; mobile render overflow check skipped"]

    source = path.read_text(encoding="utf-8", errors="replace")
    base_href = root.resolve().as_uri().rstrip("/") + "/"
    probe = r"""
<script>
setTimeout(() => {
  const selectors = [
    'body',
    'header',
    '.shell',
    '.reader-card',
    '.chapter-map',
    '.marginalia',
    '.figure-row',
    '.figure-row img',
    '.figure-note',
    '.figure-note p',
    '.figure-note h3',
    '.reading-block',
    '.source-text',
    '.translation-text',
    '.plain-text',
    '.map-item',
    '.hero p',
    '.marginalia p',
    'p',
    'button'
  ];
  const offenders = [];
  for (const el of document.querySelectorAll(selectors.join(','))) {
    const rect = el.getBoundingClientRect();
    const isRootBox = el === document.body || el === document.documentElement;
    if (
      rect.width > 0 &&
      (
        rect.right > window.innerWidth + 2 ||
        rect.left < -2 ||
        (!isRootBox && el.scrollWidth > el.clientWidth + 2)
      )
    ) {
      offenders.push({
        tag: el.tagName.toLowerCase(),
        className: el.className || '',
        left: Math.round(rect.left),
        right: Math.round(rect.right),
        width: Math.round(rect.width),
        clientWidth: Math.round(el.clientWidth || 0),
        scrollWidth: Math.round(el.scrollWidth || 0),
        text: (el.innerText || el.alt || '').replace(/\s+/g, ' ').slice(0, 80)
      });
    }
  }
  const metrics = {
    innerWidth: window.innerWidth,
    documentScrollWidth: document.documentElement.scrollWidth,
    bodyScrollWidth: document.body.scrollWidth,
    offenders: offenders.slice(0, 12)
  };
  const pre = document.createElement('pre');
  pre.id = 'paper-site-audit-metrics';
  pre.textContent = JSON.stringify(metrics);
  document.body.appendChild(pre);
}, 150);
</script>
"""
    if "<head" in source.lower():
        source = re.sub(r"(<head[^>]*>)", lambda match: f'{match.group(1)}<base href="{base_href}">', source, count=1, flags=re.I)
    else:
        source = f'<base href="{base_href}">' + source
    if "</body>" in source.lower():
        source = re.sub(r"</body>", lambda _match: probe + "</body>", source, count=1, flags=re.I)
    else:
        source += probe

    with tempfile.TemporaryDirectory() as tmp:
        probe_path = Path(tmp) / path.name
        probe_path.write_text(source, encoding="utf-8")
        result = subprocess.run(
            [
                chrome,
                "--headless=new",
                "--disable-gpu",
                "--no-first-run",
                "--no-default-browser-check",
                "--window-size=390,1200",
                "--virtual-time-budget=1000",
                "--dump-dom",
                probe_path.as_uri(),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=20,
        )
    if result.returncode != 0:
        return [], [f"{path}: mobile render overflow check failed to run: {result.stderr.strip()[:240]}"]

    match = re.search(r'<pre id="paper-site-audit-metrics">([\s\S]*?)</pre>', result.stdout)
    if not match:
        return [], [f"{path}: mobile render overflow metrics were not produced"]
    try:
        metrics = json.loads(html.unescape(match.group(1)))
    except Exception as exc:
        return [], [f"{path}: mobile render overflow metrics could not be parsed: {exc}"]

    errors: list[str] = []
    warnings: list[str] = []
    inner_width = int(metrics.get("innerWidth") or 390)
    scroll_width = max(int(metrics.get("documentScrollWidth") or 0), int(metrics.get("bodyScrollWidth") or 0))
    if scroll_width > inner_width + 2:
        errors.append(f"{path}: mobile layout has horizontal overflow ({scroll_width}px content in {inner_width}px viewport)")
    offenders = metrics.get("offenders") or []
    if offenders:
        preview = "; ".join(
            f"{item.get('tag')}.{str(item.get('className', '')).split()[0] if item.get('className') else ''} right={item.get('right')}"
            for item in offenders[:4]
        )
        errors.append(f"{path}: mobile elements extend outside viewport: {preview}")
    return errors, warnings


def audit_html(path: Path, root: Path, strict: bool, manifest: dict[str, object] | None) -> tuple[list[str], list[str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    parser = SiteHTMLParser()
    parser.feed(text)

    errors: list[str] = []
    warnings: list[str] = []

    seen: set[str] = set()
    duplicates: set[str] = set()
    for item in parser.ids:
        if item in seen:
            duplicates.add(item)
        seen.add(item)
    for item in sorted(duplicates):
        errors.append(f"{path}: duplicate id '{item}'")

    source_count = parser.class_counts.get("source-label", 0)
    translation_count = parser.class_counts.get("translation-label", 0)
    plain_count = parser.class_counts.get("plain-label", 0)
    term_count = parser.class_counts.get("term", 0)
    script_count = len(re.findall(r"<script\b", text, re.I))
    language_mode = bool(
        re.search(r"中英|EN only|English only|仅英文|只英文|中文模式", text, re.I)
        or any(name in parser.class_counts for name in ("language-mode", "language-toggle", "lang-toggle", "mode-toggle", "segmented-language"))
    )
    has_interaction_logic = bool(
        script_count
        and re.search(r"addEventListener|onclick|classList|aria-expanded|aria-pressed|data-mode|data-term|showModal|popover|dialog|drawer", text, re.I)
    )
    has_close_affordance = bool(
        re.search(r"aria-label=[\"'][^\"']*(关闭|close)|data-close|drawer-close|modal-close|popover-close|class=[\"'][^\"']*close|>×<|>关闭<|>Close<", text, re.I)
    )
    has_popover_or_drawer = bool(
        re.search(r"popover|drawer|dialog|modal|bottom-sheet|side-panel|术语弹窗|图表抽屉", text, re.I)
        or any(name in parser.class_counts for name in ("popover", "drawer", "dialog", "modal", "bottom-sheet", "side-panel", "term-popover", "figure-drawer"))
    )
    full_source_pre = bool(re.search(r"""<details[^>]+class=["'][^"']*full-source[^"']*["'][\s\S]*?<pre""", text, re.I))
    any_large_pre = bool(re.search(r"<pre[\s\S]{2000,}</pre>", text, re.I))
    diagram_svgs = [src for src, _alt, _line in parser.images if re.search(r"assets/diagrams/.*\.svg(\?|#|$)", src, re.I)]
    source_figures = [src for src, _alt, _line in parser.images if re.search(r"assets/(figures|tables)/", src, re.I)]

    if full_source_pre:
        errors.append(f"{path}: full source is buried in a collapsed pre block; render paragraph-level bilingual source in the main flow")
    elif any_large_pre:
        warnings.append(f"{path}: large <pre> block found; avoid using raw pre dumps as the source reading experience")

    if source_count and translation_count and source_count != translation_count:
        errors.append(f"{path}: source/translation block count mismatch ({source_count} source vs {translation_count} translation)")
    if strict and source_count < 10:
        errors.append(f"{path}: too few source reading blocks for a paper learning site ({source_count}); use --expected-source-blocks for exact checks")
    if strict and not language_mode:
        errors.append(f"{path}: no visible bilingual language mode such as 中英 / 中文 / EN only")
    if strict and language_mode and len(parser.buttons) >= 2 and not has_interaction_logic:
        errors.append(f"{path}: language controls look static; wire 中英/中文/EN buttons to actual reading-mode changes")
    if strict and plain_count < max(3, source_count // 3):
        errors.append(f"{path}: plain-language explanations look sparse ({plain_count} plain blocks for {source_count} source blocks)")
    if strict and term_count and not has_interaction_logic:
        errors.append(f"{path}: inline terms are marked but have no detected popover/drawer interaction logic")
    if strict and term_count and not has_popover_or_drawer:
        errors.append(f"{path}: inline terms need an attached popover, drawer, dialog, or side panel")
    if strict and (term_count or has_popover_or_drawer) and not has_close_affordance:
        errors.append(f"{path}: popovers/drawers/term panels need an obvious close state")
    if strict and source_figures:
        required_figure_words = ["它是什么", "怎么看", "相比", "结论", "不能推出"]
        missing_words = [word for word in required_figure_words if word not in text]
        if missing_words:
            errors.append(f"{path}: source figure/table explanations are incomplete; missing cues: {', '.join(missing_words)}")
    if diagram_svgs:
        message = f"{path}: generated diagram assets include SVG files under assets/diagrams; use Image 2/bitmap visuals when available: {len(diagram_svgs)} found"
        if strict and not (manifest and manifest.get("allow_svg_fallback") is True):
            errors.append(message)
        else:
            warnings.append(message)

    base = path.parent
    for src, alt, line in parser.images:
        if not src:
            errors.append(f"{path}:{line}: img missing src")
            continue
        if not alt.strip():
            warnings.append(f"{path}:{line}: img missing useful alt text")
        if is_external_or_embedded(src):
            continue
        asset = (base / src.split("#", 1)[0].split("?", 1)[0]).resolve()
        try:
            asset.relative_to(root.resolve())
        except ValueError:
            warnings.append(f"{path}:{line}: img points outside site root: {src}")
        if not asset.exists():
            errors.append(f"{path}:{line}: missing image asset: {src}")

    for src, line in parser.iframes:
        if re.search(r"\.pdf(\?|#|$)", src, re.I):
            errors.append(f"{path}:{line}: PDF iframe found; source text must be in-page")

    for attrs, line in parser.buttons:
        label = attrs.get("aria-label", "").strip() or attrs.get("title", "").strip() or attrs.get("_text", "").strip()
        if not label:
            warnings.append(f"{path}:{line}: button has no visible text, aria-label, or title")

    if re.search(r"<iframe[^>]+pdf", text, re.I):
        errors.append(f"{path}: possible PDF iframe pattern found")
    if "原文" not in text and "Original" not in text:
        warnings.append(f"{path}: no obvious source-text label such as '原文' or 'Original'")
    if "说人话" not in text and "Plain language" not in text:
        warnings.append(f"{path}: no obvious plain-language explanation label")

    if manifest:
        if "_manifest_error" in manifest:
            errors.append(str(manifest["_manifest_error"]))
        expected_source = manifest.get("source_paragraphs_expected")
        rendered_source = manifest.get("source_paragraphs_rendered", source_count)
        expected_figures = manifest.get("paper_figures_expected")
        rendered_figures = manifest.get("paper_figures_rendered")
        expected_visuals = manifest.get("generated_visuals_expected")
        rendered_visuals = manifest.get("generated_visuals_rendered")
        image_model = str(manifest.get("image_generation_model", "")).lower()
        if isinstance(expected_source, int) and rendered_source < expected_source:
            errors.append(f"{path}: manifest says only {rendered_source}/{expected_source} source paragraphs rendered")
        if isinstance(expected_figures, int) and isinstance(rendered_figures, int) and rendered_figures < expected_figures:
            errors.append(f"{path}: manifest says only {rendered_figures}/{expected_figures} paper figures/tables rendered")
        if isinstance(expected_visuals, int) and isinstance(rendered_visuals, int) and rendered_visuals < expected_visuals:
            errors.append(f"{path}: manifest says only {rendered_visuals}/{expected_visuals} generated visuals rendered")
        if strict and expected_visuals and "image" not in image_model and "gpt-image" not in image_model:
            errors.append(f"{path}: manifest does not record an Image 2/image-generation model for generated visuals")
    elif strict:
        warnings.append(f"{path}: no learning-site manifest found; add data/learning-site-manifest.json for exact coverage checks")

    if strict:
        render_errors, render_warnings = run_mobile_render_check(path, root)
        errors.extend(render_errors)
        warnings.extend(render_warnings)

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a static paper learning site.")
    parser.add_argument("target", help="Path to site directory or HTML file")
    parser.add_argument("--strict", action="store_true", help="Treat core product-quality gaps as errors")
    args = parser.parse_args()

    target = Path(args.target).expanduser().resolve()
    if not target.exists():
        print(f"ERROR: target does not exist: {target}", file=sys.stderr)
        return 2

    root = target.parent if target.is_file() else target
    manifest = load_manifest(root)
    html_files = find_html_files(target)
    if not html_files:
        print(f"ERROR: no HTML files found under {target}", file=sys.stderr)
        return 2

    all_errors: list[str] = []
    all_warnings: list[str] = []
    for html_file in html_files:
        errors, warnings = audit_html(html_file, root, args.strict, manifest)
        all_errors.extend(errors)
        all_warnings.extend(warnings)

    for warning in all_warnings:
        print(f"WARN: {warning}")
    for error in all_errors:
        print(f"ERROR: {error}")

    print(f"Audited {len(html_files)} HTML file(s). Errors: {len(all_errors)}. Warnings: {len(all_warnings)}.")
    return 1 if all_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
