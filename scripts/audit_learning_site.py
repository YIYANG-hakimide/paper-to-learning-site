#!/usr/bin/env python3
"""Static audit for paper-to-learning-site outputs."""

from __future__ import annotations

import argparse
import hashlib
import html
import os
import struct
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
    VOID_TAGS = {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }
    TEXT_FLOW_CLASSES = {
        "source-text",
        "translation-text",
        "plain-text",
        "source-paragraph",
    }
    DETACHED_TERM_CLASSES = {
        "term-strip",
        "terms-strip",
        "term-list",
        "related-terms",
        "glossary-strip",
        "glossary",
    }
    TEXT_COLLECT_CLASSES = {
        "source-text",
        "translation-text",
        "plain-text",
        "figure-note",
        "figure-explanation",
        "figure-reader",
        "source-figure-note",
        "marginalia",
        "side-note",
    }

    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.images: list[tuple[str, str, int]] = []
        self.iframes: list[tuple[str, int]] = []
        self.links: list[tuple[str, str, int]] = []
        self.buttons: list[tuple[dict[str, str], int]] = []
        self.starttags: list[tuple[str, dict[str, str], int]] = []
        self.class_counts: dict[str, int] = {}
        self.visible_text_parts: list[str] = []
        self.attr_texts: list[tuple[str, str, int]] = []
        self.class_texts: dict[str, list[str]] = {}
        self.term_records: list[dict[str, object]] = []
        self.reading_blocks: list[dict[str, str | int]] = []
        self.aria_counts = {"expanded": 0, "controls": 0, "current": 0}
        self._current_button: dict[str, str] | None = None
        self._button_text: list[str] = []
        self._current_link: dict[str, str] | None = None
        self._link_text: list[str] = []
        self._class_stack: list[set[str]] = []
        self._text_collectors: list[dict[str, object]] = []
        self._reading_block_collectors: list[dict[str, object]] = []
        self._term_collectors: list[dict[str, object]] = []
        self._skip_depth = 0
        self._line = 1

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_name = tag.lower()
        is_void = tag_name in self.VOID_TAGS
        if not is_void:
            for collector in self._text_collectors:
                collector["depth"] = int(collector["depth"]) + 1
            for collector in self._reading_block_collectors:
                collector["depth"] = int(collector["depth"]) + 1
            for collector in self._term_collectors:
                collector["depth"] = int(collector["depth"]) + 1
        attr = {k: (v or "") for k, v in attrs}
        self._line = self.getpos()[0]
        self.starttags.append((tag, attr, self._line))
        classes = set(attr.get("class", "").split())
        ancestor_classes = set().union(*self._class_stack) if self._class_stack else set()
        all_context_classes = ancestor_classes | classes
        for class_name in attr.get("class", "").split():
            self.class_counts[class_name] = self.class_counts.get(class_name, 0) + 1
        for aria_name in ("aria-expanded", "aria-controls", "aria-current"):
            if aria_name in attr:
                self.aria_counts[aria_name.removeprefix("aria-")] += 1
        for attr_name in ("alt", "title", "aria-label", "data-note", "data-note-title"):
            if attr.get(attr_name, "").strip():
                self.attr_texts.append((attr_name, attr[attr_name].strip(), self._line))
        if "id" in attr:
            self.ids.append(attr["id"])
        if tag == "img":
            self.images.append((attr.get("src", ""), attr.get("alt", ""), self._line))
        if tag == "iframe":
            self.iframes.append((attr.get("src", ""), self._line))
        if tag == "a":
            self._current_link = attr
            self._link_text = []
        if "reading-block" in classes:
            self._reading_block_collectors.append(
                {
                    "depth": 1,
                    "line": self._line,
                    "id": attr.get("id", ""),
                    "data_source_id": attr.get("data-source-id", ""),
                    "data_block": attr.get("data-block", ""),
                    "data_note": attr.get("data-note", ""),
                    "all_parts": [],
                    "source_parts": [],
                    "translation_parts": [],
                    "plain_parts": [],
                }
            )
        is_term = (
            "term" in classes
            or "data-term" in attr
            or "data-term-id" in attr
            or attr.get("data-open-drawer", "").lower() == "term"
        )
        if is_term:
            current_source_id = ""
            current_block_id = ""
            if self._reading_block_collectors:
                current_block = self._reading_block_collectors[-1]
                current_source_id = str(current_block.get("data_source_id", "") or "")
                current_block_id = str(current_block.get("id", "") or "")
            record = {
                "line": self._line,
                "classes": sorted(classes),
                "term_id": attr.get("data-term") or attr.get("data-term-id") or attr.get("data-open-drawer", ""),
                "source_id": current_source_id,
                "rendered_block_id": current_block_id,
                "inline": bool(all_context_classes & self.TEXT_FLOW_CLASSES) and not bool(all_context_classes & self.DETACHED_TERM_CLASSES),
                "detached": bool(all_context_classes & self.DETACHED_TERM_CLASSES),
                "has_aria": any(name in attr for name in ("aria-expanded", "aria-controls", "aria-label")),
                "parts": [],
            }
            if is_void:
                record["trigger_text"] = attr.get("aria-label") or attr.get("title") or ""
                self.term_records.append(record)
            else:
                record["depth"] = 1
                self._term_collectors.append(record)
        for class_name in classes & self.TEXT_COLLECT_CLASSES:
            if is_void:
                continue
            self._text_collectors.append({"class": class_name, "depth": 1, "parts": []})
        if tag_name in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1
        if tag == "button":
            self._current_button = attr
            self._button_text = []
        if not is_void:
            self._class_stack.append(classes)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._current_link is not None:
            attrs = dict(self._current_link)
            href = attrs.get("href", "")
            label = " ".join("".join(self._link_text).split())
            self.links.append((href, label, self.getpos()[0]))
            self._current_link = None
            self._link_text = []
        if tag == "button" and self._current_button is not None:
            attrs = dict(self._current_button)
            attrs["_text"] = " ".join("".join(self._button_text).split())
            self.buttons.append((attrs, self.getpos()[0]))
            self._current_button = None
            self._button_text = []
        finished: list[dict[str, object]] = []
        for collector in self._text_collectors:
            collector["depth"] = int(collector["depth"]) - 1
            if int(collector["depth"]) <= 0:
                finished.append(collector)
        if finished:
            for collector in finished:
                class_name = str(collector["class"])
                value = " ".join("".join(collector["parts"]).split())
                if value:
                    self.class_texts.setdefault(class_name, []).append(value)
                self._text_collectors.remove(collector)
        finished_blocks: list[dict[str, object]] = []
        for collector in self._reading_block_collectors:
            collector["depth"] = int(collector["depth"]) - 1
            if int(collector["depth"]) <= 0:
                finished_blocks.append(collector)
        if finished_blocks:
            for collector in finished_blocks:
                block = {
                    "line": int(collector["line"]),
                    "id": str(collector["id"]),
                    "data_source_id": str(collector["data_source_id"]),
                    "data_block": str(collector["data_block"]),
                    "data_note": str(collector["data_note"]),
                    "text": " ".join("".join(collector["all_parts"]).split()),
                    "source_text": " ".join("".join(collector["source_parts"]).split()),
                    "translation_text": " ".join("".join(collector["translation_parts"]).split()),
                    "plain_text": " ".join("".join(collector["plain_parts"]).split()),
                }
                self.reading_blocks.append(block)
                self._reading_block_collectors.remove(collector)
        finished_terms: list[dict[str, object]] = []
        for collector in self._term_collectors:
            collector["depth"] = int(collector["depth"]) - 1
            if int(collector["depth"]) <= 0:
                finished_terms.append(collector)
        if finished_terms:
            for collector in finished_terms:
                parts = collector.get("parts")
                trigger_text = " ".join("".join(parts if isinstance(parts, list) else []).split())
                collector["trigger_text"] = trigger_text
                collector.pop("parts", None)
                collector.pop("depth", None)
                self.term_records.append(collector)
                self._term_collectors.remove(collector)
        if tag.lower() in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1
        if self._class_stack:
            self._class_stack.pop()

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            if data.strip():
                self.visible_text_parts.append(data)
            for collector in self._text_collectors:
                cast_parts = collector["parts"]
                if isinstance(cast_parts, list):
                    cast_parts.append(data)
            context_classes = set().union(*self._class_stack) if self._class_stack else set()
            for collector in self._reading_block_collectors:
                all_parts = collector["all_parts"]
                if isinstance(all_parts, list):
                    all_parts.append(data)
                if context_classes & {"source-text", "source-paragraph"} and "source-label" not in context_classes:
                    source_parts = collector["source_parts"]
                    if isinstance(source_parts, list):
                        source_parts.append(data)
                if context_classes & {"translation-text", "chinese-reading", "cn-reading"} and "translation-label" not in context_classes:
                    translation_parts = collector["translation_parts"]
                    if isinstance(translation_parts, list):
                        translation_parts.append(data)
                if context_classes & {"plain-text", "explanation-text", "plain-explanation"} and "plain-label" not in context_classes:
                    plain_parts = collector["plain_parts"]
                    if isinstance(plain_parts, list):
                        plain_parts.append(data)
            for collector in self._term_collectors:
                parts = collector.get("parts")
                if isinstance(parts, list):
                    parts.append(data)
        if self._current_button is not None:
            self._button_text.append(data)
        if self._current_link is not None:
            self._link_text.append(data)

    @property
    def visible_text(self) -> str:
        return " ".join(" ".join(self.visible_text_parts).split())


def is_external_or_embedded(src: str) -> bool:
    if not src:
        return False
    if src.startswith(("data:", "blob:", "#")):
        return True
    parsed = urlparse(src)
    return bool(parsed.scheme and parsed.scheme not in {"file"})


def image_dimensions(path: Path) -> tuple[int, int] | None:
    try:
        with path.open("rb") as fh:
            header = fh.read(32)
            if header.startswith(b"\x89PNG\r\n\x1a\n") and header[12:16] == b"IHDR":
                return struct.unpack(">II", header[16:24])
            if header.startswith(b"\xff\xd8"):
                fh.seek(2)
                while True:
                    marker_start = fh.read(1)
                    if not marker_start:
                        return None
                    if marker_start != b"\xff":
                        continue
                    marker = fh.read(1)
                    while marker == b"\xff":
                        marker = fh.read(1)
                    if marker in {b"\xc0", b"\xc1", b"\xc2", b"\xc3", b"\xc5", b"\xc6", b"\xc7", b"\xc9", b"\xca", b"\xcb", b"\xcd", b"\xce", b"\xcf"}:
                        length = int.from_bytes(fh.read(2), "big")
                        payload = fh.read(length - 2)
                        if len(payload) >= 5:
                            return int.from_bytes(payload[3:5], "big"), int.from_bytes(payload[1:3], "big")
                        return None
                    if marker in {b"\xd8", b"\xd9"}:
                        continue
                    length_bytes = fh.read(2)
                    if len(length_bytes) != 2:
                        return None
                    length = int.from_bytes(length_bytes, "big")
                    if length < 2:
                        return None
                    fh.seek(length - 2, 1)
    except Exception:
        return None
    return None


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


def dependency_root() -> Path:
    return Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies"


def bundled_node_path() -> str | None:
    bundled = dependency_root() / "node" / "bin" / "node"
    if bundled.exists():
        return str(bundled)
    system_node = shutil.which("node")
    if system_node and Path(system_node).exists():
        return system_node
    return None


def prepare_browser_probe_html(path: Path, root: Path, strip_scripts: bool) -> str:
    source = path.read_text(encoding="utf-8", errors="replace")
    if strip_scripts:
        source = re.sub(r"<script\b[^>]*>[\s\S]*?</script>", "", source, flags=re.I)
    base_href = root.resolve().as_uri().rstrip("/") + "/"
    if "<head" in source.lower():
        return re.sub(r"(<head[^>]*>)", lambda match: f'{match.group(1)}<base href="{base_href}">', source, count=1, flags=re.I)
    return f'<base href="{base_href}">' + source


def run_playwright_probe(
    path: Path,
    root: Path,
    viewport: dict[str, int],
    probe_function: str,
    *,
    strip_scripts: bool,
    wait_ms: int,
    timeout: int,
) -> tuple[dict[str, object] | None, str | None]:
    node = bundled_node_path()
    node_modules = dependency_root() / "node" / "node_modules"
    if not node or not node_modules.exists():
        return None, "bundled Node.js or node_modules not found"

    runner = r"""
const fs = require('fs');
const { chromium } = require('playwright');

(async () => {
  const pageUrl = process.argv[2];
  const viewport = JSON.parse(process.argv[3]);
  const probeSource = fs.readFileSync(process.argv[4], 'utf8');
  const executablePath = process.argv[5] || undefined;
  const waitMs = Number(process.argv[6] || 400);
  const probe = (new Function(`return (${probeSource});`))();
  const launchOptions = {
    headless: true,
    args: ['--disable-background-networking', '--no-default-browser-check', '--no-first-run']
  };
  if (executablePath) launchOptions.executablePath = executablePath;
  const browser = await chromium.launch(launchOptions);
  try {
    const page = await browser.newPage({ viewport });
    await page.goto(pageUrl, { waitUntil: 'domcontentloaded', timeout: Math.min(20000, Math.max(5000, waitMs * 10)) });
    await page.waitForTimeout(waitMs);
    const metrics = await page.evaluate(probe);
    process.stdout.write(JSON.stringify(metrics));
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error && error.stack ? error.stack : String(error));
  process.exit(1);
});
"""
    source = prepare_browser_probe_html(path, root, strip_scripts)
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        html_path = tmp_path / path.name
        probe_path = tmp_path / "probe.js"
        runner_path = tmp_path / "runner.js"
        html_path.write_text(source, encoding="utf-8")
        probe_path.write_text(probe_function, encoding="utf-8")
        runner_path.write_text(runner, encoding="utf-8")
        env = dict(os.environ)
        env["NODE_PATH"] = str(node_modules)
        try:
            result = subprocess.run(
                [
                    node,
                    str(runner_path),
                    html_path.as_uri(),
                    json.dumps(viewport),
                    str(probe_path),
                    chrome_path() or "",
                    str(wait_ms),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
                env=env,
            )
        except subprocess.TimeoutExpired:
            return None, "Playwright probe timed out"
    if result.returncode != 0:
        return None, result.stderr.strip()[:320] or "Playwright probe failed"
    try:
        return json.loads(result.stdout), None
    except Exception as exc:
        return None, f"Playwright probe returned invalid JSON: {exc}"


def run_playwright_injected_metrics(
    path: Path,
    root: Path,
    viewport: dict[str, int],
    probe_script_tag: str,
    marker_id: str,
    *,
    strip_scripts: bool,
    wait_ms: int,
    timeout: int,
) -> tuple[dict[str, object] | None, str | None]:
    node = bundled_node_path()
    node_modules = dependency_root() / "node" / "node_modules"
    if not node or not node_modules.exists():
        return None, "bundled Node.js or node_modules not found"

    runner = r"""
const { chromium } = require('playwright');

(async () => {
  const pageUrl = process.argv[2];
  const viewport = JSON.parse(process.argv[3]);
  const markerId = process.argv[4];
  const executablePath = process.argv[5] || undefined;
  const waitMs = Number(process.argv[6] || 800);
  const launchOptions = {
    headless: true,
    args: ['--disable-background-networking', '--no-default-browser-check', '--no-first-run']
  };
  if (executablePath) launchOptions.executablePath = executablePath;
  const browser = await chromium.launch(launchOptions);
  try {
    const page = await browser.newPage({ viewport });
    await page.goto(pageUrl, { waitUntil: 'domcontentloaded', timeout: Math.min(20000, Math.max(5000, waitMs * 10)) });
    await page.waitForSelector(`#${markerId}`, { state: 'attached', timeout: Math.max(5000, waitMs * 3) });
    const text = await page.textContent(`#${markerId}`);
    process.stdout.write(text || '');
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error && error.stack ? error.stack : String(error));
  process.exit(1);
});
"""
    source = prepare_browser_probe_html(path, root, strip_scripts)
    if "</body>" in source.lower():
        source = re.sub(r"</body>", lambda _match: probe_script_tag + "</body>", source, count=1, flags=re.I)
    else:
        source += probe_script_tag
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        html_path = tmp_path / path.name
        runner_path = tmp_path / "runner.js"
        html_path.write_text(source, encoding="utf-8")
        runner_path.write_text(runner, encoding="utf-8")
        env = dict(os.environ)
        env["NODE_PATH"] = str(node_modules)
        try:
            result = subprocess.run(
                [
                    node,
                    str(runner_path),
                    html_path.as_uri(),
                    json.dumps(viewport),
                    marker_id,
                    chrome_path() or "",
                    str(wait_ms),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
                env=env,
            )
        except subprocess.TimeoutExpired:
            return None, "Playwright injected probe timed out"
    if result.returncode != 0:
        return None, result.stderr.strip()[:320] or "Playwright injected probe failed"
    try:
        return json.loads(result.stdout), None
    except Exception as exc:
        return None, f"Playwright injected probe returned invalid JSON: {exc}"


def analyze_mobile_render_metrics(path: Path, metrics: dict[str, object]) -> tuple[list[str], list[str]]:
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
            if isinstance(item, dict)
        )
        errors.append(f"{path}: mobile elements extend outside viewport: {preview}")
    return errors, warnings


def analyze_desktop_first_viewport_metrics(path: Path, metrics: dict[str, object]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    inner_width = int(metrics.get("innerWidth") or 1440)
    scroll_width = max(int(metrics.get("documentScrollWidth") or 0), int(metrics.get("bodyScrollWidth") or 0))
    if scroll_width > inner_width + 2:
        errors.append(f"{path}: desktop layout has horizontal overflow ({scroll_width}px content in {inner_width}px viewport)")
    visible = metrics.get("visible") or {}
    required = {
        "title": "paper title",
        "chapterNav": "chapter navigation",
        "sourceText": "real source paragraph",
        "chineseReading": "Chinese translation/explanation",
        "visualLandmark": "paper-specific visual landmark or teaching image",
        "learningAffordance": "inline term, evidence, side note, or learning affordance",
    }
    for key, label in required.items():
        if not isinstance(visible, dict) or not visible.get(key):
            errors.append(f"{path}: desktop first viewport does not show {label}; avoid cover pages that hide the paper reader")
    if not isinstance(visible, dict) or not visible.get("languageMode"):
        warnings.append(f"{path}: desktop first viewport does not show a language mode control")
    offenders = metrics.get("offenders") or []
    if offenders:
        preview = "; ".join(
            f"{item.get('tag')}.{str(item.get('className', '')).split()[0] if item.get('className') else ''} right={item.get('right')}"
            for item in offenders[:4]
            if isinstance(item, dict)
        )
        errors.append(f"{path}: desktop elements extend outside viewport: {preview}")
    return errors, warnings


def analyze_interaction_metrics(path: Path, metrics: dict[str, object]) -> tuple[list[str], list[str]]:
    errors = [f"{path}: {message}" for message in metrics.get("errors", [])]
    warnings = [f"{path}: {message}" for message in metrics.get("warnings", [])]
    return errors, warnings


def run_mobile_render_check(path: Path, root: Path) -> tuple[list[str], list[str]]:
    playwright_probe = r"""
() => {
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
  return {
    innerWidth: window.innerWidth,
    documentScrollWidth: document.documentElement.scrollWidth,
    bodyScrollWidth: document.body.scrollWidth,
    offenders: offenders.slice(0, 12)
  };
}
"""
    playwright_metrics, _playwright_error = run_playwright_probe(
        path,
        root,
        {"width": 390, "height": 1200},
        playwright_probe,
        strip_scripts=True,
        wait_ms=500,
        timeout=45,
    )
    if playwright_metrics is not None:
        return analyze_mobile_render_metrics(path, playwright_metrics)

    chrome = chrome_path()
    if not chrome:
        return [], [f"{path}: Chrome/Chromium not found; mobile render overflow check skipped"]

    source = path.read_text(encoding="utf-8", errors="replace")
    source = re.sub(r"<script\b[^>]*>[\s\S]*?</script>", "", source, flags=re.I)
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
        try:
            result = subprocess.run(
                [
                    chrome,
                    "--headless=new",
                    "--disable-gpu",
                    "--blink-settings=imagesEnabled=false",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--window-size=390,1200",
                    "--virtual-time-budget=1500",
                    "--dump-dom",
                    probe_path.as_uri(),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=45,
            )
        except subprocess.TimeoutExpired:
            return [f"{path}: mobile render overflow check timed out; strict audits must not waive browser QA"], []
    if result.returncode != 0:
        return [], [f"{path}: mobile render overflow check failed to run: {result.stderr.strip()[:240]}"]

    match = re.search(r'<pre id="paper-site-audit-metrics">([\s\S]*?)</pre>', result.stdout)
    if not match:
        return [], [f"{path}: mobile render overflow metrics were not produced"]
    try:
        metrics = json.loads(html.unescape(match.group(1)))
    except Exception as exc:
        return [], [f"{path}: mobile render overflow metrics could not be parsed: {exc}"]

    return analyze_mobile_render_metrics(path, metrics)


def run_desktop_first_viewport_check(path: Path, root: Path) -> tuple[list[str], list[str]]:
    playwright_probe = r"""
() => {
  const groups = {
    title: 'h1,[data-paper-title],.paper-title',
    chapterNav: '.chapter-map,.chapter-tab,.map-item,.chapter-button,[role="tablist"]',
    languageMode: '.language-mode,.language-toggle,.lang-toggle,.mode-toggle,.segmented-language,[data-language-mode]',
    sourceText: '.source-text,.source-paragraph,[data-source-id]',
    chineseReading: '.translation-text,.plain-text,.chinese-reading,.cn-reading',
    visualLandmark: '.visual-landmark,.paper-visual-landmark,.diagram-card img,.source-figure img,.hero-visual img,[data-visual-landmark]',
    learningAffordance: '.term,[data-term],[data-term-id],.figure-note,.figure-explanation,.source-figure-note,.marginalia,.side-note,[data-open-drawer],.term-popover'
  };
  const visible = {};
  for (const [key, selector] of Object.entries(groups)) {
    visible[key] = Array.from(document.querySelectorAll(selector)).some((el) => {
      const rect = el.getBoundingClientRect();
      const inViewport = rect.width > 0 && rect.height > 0 && rect.top < window.innerHeight && rect.bottom > 0 && rect.left < window.innerWidth && rect.right > 0;
      if (key === 'visualLandmark') {
        return inViewport && rect.width >= 180 && rect.height >= 100;
      }
      return inViewport;
    });
  }
  const offenders = [];
  for (const el of document.querySelectorAll('body,header,.shell,.reader-card,.chapter-map,.reading-block,.source-text,.translation-text,.plain-text,p,button')) {
    const rect = el.getBoundingClientRect();
    const isRootBox = el === document.body || el === document.documentElement;
    if (rect.width > 0 && (rect.right > window.innerWidth + 2 || rect.left < -2 || (!isRootBox && el.scrollWidth > el.clientWidth + 2))) {
      offenders.push({
        tag: el.tagName.toLowerCase(),
        className: el.className || '',
        right: Math.round(rect.right),
        clientWidth: Math.round(el.clientWidth || 0),
        scrollWidth: Math.round(el.scrollWidth || 0),
        text: (el.innerText || '').replace(/\s+/g, ' ').slice(0, 80)
      });
    }
  }
  return {
    innerWidth: window.innerWidth,
    documentScrollWidth: document.documentElement.scrollWidth,
    bodyScrollWidth: document.body.scrollWidth,
    visible,
    offenders: offenders.slice(0, 12)
  };
}
"""
    playwright_metrics, _playwright_error = run_playwright_probe(
        path,
        root,
        {"width": 1440, "height": 950},
        playwright_probe,
        strip_scripts=True,
        wait_ms=500,
        timeout=45,
    )
    if playwright_metrics is not None:
        return analyze_desktop_first_viewport_metrics(path, playwright_metrics)

    chrome = chrome_path()
    if not chrome:
        return [], [f"{path}: Chrome/Chromium not found; desktop first-viewport reader check skipped"]

    source = path.read_text(encoding="utf-8", errors="replace")
    source = re.sub(r"<script\b[^>]*>[\s\S]*?</script>", "", source, flags=re.I)
    base_href = root.resolve().as_uri().rstrip("/") + "/"
    probe = r"""
<script>
setTimeout(() => {
  const groups = {
    title: 'h1,[data-paper-title],.paper-title',
    chapterNav: '.chapter-map,.chapter-tab,.map-item,.chapter-button,[role="tablist"]',
    languageMode: '.language-mode,.language-toggle,.lang-toggle,.mode-toggle,.segmented-language,[data-language-mode]',
    sourceText: '.source-text,.source-paragraph,[data-source-id]',
    chineseReading: '.translation-text,.plain-text,.chinese-reading,.cn-reading',
    visualLandmark: '.visual-landmark,.paper-visual-landmark,.diagram-card img,.source-figure img,.hero-visual img,[data-visual-landmark]',
    learningAffordance: '.term,[data-term],[data-term-id],.figure-note,.figure-explanation,.source-figure-note,.marginalia,.side-note,[data-open-drawer],.term-popover'
  };
  const visible = {};
  for (const [key, selector] of Object.entries(groups)) {
    visible[key] = Array.from(document.querySelectorAll(selector)).some((el) => {
      const rect = el.getBoundingClientRect();
      const inViewport = rect.width > 0 && rect.height > 0 && rect.top < window.innerHeight && rect.bottom > 0 && rect.left < window.innerWidth && rect.right > 0;
      if (key === 'visualLandmark') {
        return inViewport && rect.width >= 180 && rect.height >= 100;
      }
      return inViewport;
    });
  }
  const offenders = [];
  for (const el of document.querySelectorAll('body,header,.shell,.reader-card,.chapter-map,.reading-block,.source-text,.translation-text,.plain-text,p,button')) {
    const rect = el.getBoundingClientRect();
    const isRootBox = el === document.body || el === document.documentElement;
    if (rect.width > 0 && (rect.right > window.innerWidth + 2 || rect.left < -2 || (!isRootBox && el.scrollWidth > el.clientWidth + 2))) {
      offenders.push({
        tag: el.tagName.toLowerCase(),
        className: el.className || '',
        right: Math.round(rect.right),
        clientWidth: Math.round(el.clientWidth || 0),
        scrollWidth: Math.round(el.scrollWidth || 0),
        text: (el.innerText || '').replace(/\s+/g, ' ').slice(0, 80)
      });
    }
  }
  const metrics = {
    innerWidth: window.innerWidth,
    documentScrollWidth: document.documentElement.scrollWidth,
    bodyScrollWidth: document.body.scrollWidth,
    visible,
    offenders: offenders.slice(0, 12)
  };
  const pre = document.createElement('pre');
  pre.id = 'paper-site-audit-desktop-metrics';
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
        try:
            result = subprocess.run(
                [
                    chrome,
                    "--headless=new",
                    "--disable-gpu",
                    "--blink-settings=imagesEnabled=false",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--window-size=1440,950",
                    "--virtual-time-budget=1500",
                    "--dump-dom",
                    probe_path.as_uri(),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=45,
            )
        except subprocess.TimeoutExpired:
            return [f"{path}: desktop first-viewport check timed out; strict audits must not waive browser QA"], []
    if result.returncode != 0:
        return [], [f"{path}: desktop first-viewport check failed to run: {result.stderr.strip()[:240]}"]

    match = re.search(r'<pre id="paper-site-audit-desktop-metrics">([\s\S]*?)</pre>', result.stdout)
    if not match:
        return [], [f"{path}: desktop first-viewport metrics were not produced"]
    try:
        metrics = json.loads(html.unescape(match.group(1)))
    except Exception as exc:
        return [], [f"{path}: desktop first-viewport metrics could not be parsed: {exc}"]

    return analyze_desktop_first_viewport_metrics(path, metrics)


def run_interaction_quality_check(path: Path, root: Path) -> tuple[list[str], list[str]]:
    chrome = chrome_path()
    if not chrome:
        return [], [f"{path}: Chrome/Chromium not found; interaction quality check skipped"]

    source = path.read_text(encoding="utf-8", errors="replace")
    base_href = root.resolve().as_uri().rstrip("/") + "/"
    probe = r"""
<script>
setTimeout(async () => {
  const errors = [];
  const warnings = [];
  const wait = () => new Promise((resolve) => setTimeout(resolve, 40));
  const visible = (el) => {
    if (!el) return false;
    const style = getComputedStyle(el);
    const rect = el.getBoundingClientRect();
    return style.display !== 'none' && style.visibility !== 'hidden' && rect.width > 0 && rect.height > 0;
  };
  const textLength = (el) => (el && el.innerText ? el.innerText.replace(/\s+/g, '').length : 0);
  const cssEscape = (value) => window.CSS && CSS.escape ? CSS.escape(value) : String(value).replace(/["\\]/g, '\\$&');
  const closeOpenPanels = async () => {
    const close = document.querySelector('[data-close],.close-drawer,[aria-label*="关闭"],[aria-label*="Close"]');
    if (close) close.click();
    document.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape', bubbles: true}));
    await wait();
  };
  const activePanel = () => document.querySelector('.chapter-panel[data-active="true"],[data-chapter-panel][data-active="true"],.chapter-panel:not([hidden])');
  const visibleTextIn = (root, selector) => Array.from((root || document).querySelectorAll(selector)).some((el) => visible(el) && textLength(el) > 40);

  const chapterButtons = Array.from(document.querySelectorAll('button[data-chapter],a[data-chapter],[role="tab"][data-chapter]')).filter(visible);
  const modeButtons = Array.from(document.querySelectorAll('button[data-mode],a[data-mode],[role="tab"][data-mode]')).filter(visible);
  for (const chapterButton of chapterButtons) {
    const chapterId = chapterButton.dataset.chapter;
    chapterButton.click();
    await wait();
    const panel = document.querySelector(`[data-chapter-panel="${cssEscape(chapterId)}"], #${cssEscape(chapterId)}`);
    if (!visible(panel) || textLength(panel) < 220) {
      errors.push(`chapter '${chapterId}' opens an empty or too-thin panel`);
      continue;
    }
    if (chapterButton.getAttribute('aria-current') !== 'true') {
      errors.push(`chapter '${chapterId}' does not mark aria-current=true after click`);
    }
    for (const modeButton of modeButtons) {
      const mode = modeButton.dataset.mode || modeButton.textContent.trim();
      modeButton.click();
      await wait();
      const current = document.querySelector(`[data-chapter-panel="${cssEscape(chapterId)}"], #${cssEscape(chapterId)}`);
      if (!visible(current) || !current.querySelector('.reading-block,[data-source-id]')) {
        errors.push(`chapter '${chapterId}' + mode '${mode}' has no visible source reading block`);
        continue;
      }
      const hasSource = visibleTextIn(current, '.source-text,.source-paragraph,[data-source-layer="source"]');
      const hasChinese = visibleTextIn(current, '.translation-text,.plain-text,.chinese-reading,.cn-reading,[data-source-layer="translation"],[data-source-layer="plain"]');
      const normalized = String(mode).toLowerCase();
      if ((normalized.includes('bilingual') || mode.includes('中英')) && (!hasSource || !hasChinese)) {
        errors.push(`chapter '${chapterId}' bilingual mode does not show both source and Chinese reading`);
      }
      if ((normalized === 'zh' || mode.includes('中文')) && !hasChinese) {
        errors.push(`chapter '${chapterId}' Chinese mode has no Chinese reading/explanation`);
      }
      if ((normalized.includes('en') || mode.includes('EN')) && !hasSource) {
        errors.push(`chapter '${chapterId}' English mode has no source text`);
      }
    }
  }

  const termButtons = Array.from(document.querySelectorAll('.term[data-term],[data-term-id],[data-open-drawer="term"]')).filter(visible);
  for (const termButton of termButtons.slice(0, 40)) {
    await closeOpenPanels();
    const termId = termButton.dataset.term || termButton.dataset.termId || termButton.textContent.trim();
    const block = termButton.closest('.reading-block,[data-source-id]');
    const beforeScrollY = window.scrollY;
    termButton.scrollIntoView({block: 'center', inline: 'nearest'});
    await wait();
    const blockRect = block ? block.getBoundingClientRect() : null;
    termButton.click();
    await wait();
    const panel = document.querySelector('#term-panel[aria-hidden="false"],#term-popover[aria-hidden="false"],.term-popover[aria-hidden="false"],.term-drawer[aria-hidden="false"],[data-term-panel][aria-hidden="false"],dialog[open]');
    if (!panel || !visible(panel)) {
      errors.push(`term '${termId}' did not open a visible explanation panel`);
      continue;
    }
    if (textLength(panel) < 80) {
      errors.push(`term '${termId}' explanation is too thin`);
    }
    if (termButton.getAttribute('aria-expanded') !== 'true') {
      errors.push(`term '${termId}' trigger did not set aria-expanded=true`);
    }
    if (blockRect) {
      const panelRect = panel.getBoundingClientRect();
      const overlapX = Math.max(0, Math.min(blockRect.right, panelRect.right) - Math.max(blockRect.left, panelRect.left));
      const overlapY = Math.max(0, Math.min(blockRect.bottom, panelRect.bottom) - Math.max(blockRect.top, panelRect.top));
      const overlapArea = overlapX * overlapY;
      const blockArea = Math.max(1, blockRect.width * blockRect.height);
      if (overlapArea / blockArea > 0.3) {
        errors.push(`term '${termId}' panel overlaps the active reading block by ${Math.round((overlapArea / blockArea) * 100)}%`);
      }
    }
    const hasReturn = /回到原词|回到原文|show in context|return/i.test(panel.innerText || '');
    if (!hasReturn) {
      errors.push(`term '${termId}' explanation has no return-to-source affordance`);
    }
    await closeOpenPanels();
    if (termButton.getAttribute('aria-expanded') === 'true') {
      errors.push(`term '${termId}' remains aria-expanded=true after close`);
    }
    if (document.activeElement !== termButton && Math.abs(window.scrollY - beforeScrollY) > window.innerHeight) {
      errors.push(`term '${termId}' close did not clearly restore focus or reading position`);
    }
  }

  const visualImages = Array.from(document.querySelectorAll('.source-figure img,.diagram-card img,[data-figure-id] img')).filter(visible);
  for (const image of visualImages) {
    const rect = image.getBoundingClientRect();
    const naturalWidth = image.naturalWidth || 0;
    const label = image.alt || image.src || 'visual image';
    if (naturalWidth >= 800 && rect.width < 640) {
      errors.push(`visual '${label.slice(0, 80)}' renders too small on desktop (${Math.round(rect.width)}px wide)`);
    }
  }

  const figureButtons = Array.from(document.querySelectorAll('[data-figure]')).filter(visible);
  for (const figureButton of figureButtons.slice(0, 24)) {
    await closeOpenPanels();
    const figureId = figureButton.dataset.figure || figureButton.textContent.trim();
    const inlineImg = figureButton.closest('.source-figure,.diagram-card,[data-figure-id]')?.querySelector('img');
    const inlineRect = inlineImg ? inlineImg.getBoundingClientRect() : null;
    figureButton.click();
    await wait();
    const drawer = document.querySelector('#figure-panel[aria-hidden="false"],#figure-drawer[aria-hidden="false"],.figure-drawer[aria-hidden="false"],[data-figure-panel][aria-hidden="false"],dialog[open]');
    const drawerImg = drawer ? drawer.querySelector('img') : null;
    if (!drawer || !visible(drawer) || !drawerImg || !visible(drawerImg) || !(drawerImg.naturalWidth > 0)) {
      errors.push(`figure '${figureId}' did not open a visible loaded large view`);
      continue;
    }
    const drawerRect = drawerImg.getBoundingClientRect();
    if (inlineRect && drawerRect.width < inlineRect.width * 1.3) {
      errors.push(`figure '${figureId}' large view is not meaningfully larger than inline view`);
    }
    if ((drawerImg.naturalWidth || 0) >= 900 && drawerRect.width < 720) {
      errors.push(`figure '${figureId}' large view is still too small for close reading (${Math.round(drawerRect.width)}px wide)`);
    }
    if (textLength(drawer) < 120) {
      errors.push(`figure '${figureId}' large view has too little explanation text`);
    }
    await closeOpenPanels();
    if (figureButton.getAttribute('aria-expanded') === 'true') {
      errors.push(`figure '${figureId}' remains aria-expanded=true after close`);
    }
  }

  const reviewCards = Array.from(document.querySelectorAll('[data-review],.review-card,[data-quiz],.quiz-card'));
  const allReviewFeedback = [];
  for (const card of reviewCards) {
    const chapterPanel = card.closest('[data-chapter-panel]');
    if (chapterPanel && !visible(chapterPanel)) {
      const chapterId = chapterPanel.dataset.chapterPanel || chapterPanel.id;
      const chapterButton = document.querySelector(`button[data-chapter="${cssEscape(chapterId)}"],a[data-chapter="${cssEscape(chapterId)}"],[role="tab"][data-chapter="${cssEscape(chapterId)}"]`);
      if (chapterButton) {
        chapterButton.click();
        await wait();
      }
    }
    const choices = Array.from(card.querySelectorAll('[data-review-choice],[data-quiz-choice],button')).filter(visible);
    const feedback = card.querySelector('.review-feedback,[data-review-feedback],.quiz-feedback,[aria-live]');
    for (const choice of choices) {
      choice.click();
      await wait();
      const value = feedback ? (feedback.innerText || '').replace(/\s+/g, ' ').trim() : '';
      if (value.length < 16) {
        errors.push(`chapter review choice '${choice.innerText.trim().slice(0, 40)}' produced empty or weak feedback`);
      } else {
        allReviewFeedback.push(value);
      }
    }
  }
  if (reviewCards.length >= 3 && allReviewFeedback.length >= reviewCards.length && new Set(allReviewFeedback).size <= 2) {
    errors.push(`chapter review feedback is repeated across chapters; make feedback chapter/evidence-specific`);
  }

  const metrics = {errors, warnings};
const pre = document.createElement('pre');
pre.id = 'paper-site-audit-interaction-metrics';
pre.textContent = JSON.stringify(metrics);
document.body.appendChild(pre);
}, 250);
</script>
"""
    playwright_metrics, _playwright_error = run_playwright_injected_metrics(
        path,
        root,
        {"width": 1440, "height": 1100},
        probe,
        "paper-site-audit-interaction-metrics",
        strip_scripts=False,
        wait_ms=7000,
        timeout=75,
    )
    if playwright_metrics is not None:
        return analyze_interaction_metrics(path, playwright_metrics)

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
        try:
            result = subprocess.run(
                [
                    chrome,
                    "--headless=new",
                    "--disable-gpu",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--window-size=1440,1100",
                    "--virtual-time-budget=4500",
                    "--dump-dom",
                    probe_path.as_uri(),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=60,
            )
        except subprocess.TimeoutExpired:
            return [f"{path}: interaction quality check timed out; strict audits must not waive dynamic reader QA"], []
    if result.returncode != 0:
        return [], [f"{path}: interaction quality check failed to run: {result.stderr.strip()[:240]}"]

    match = re.search(r'<pre id="paper-site-audit-interaction-metrics">([\s\S]*?)</pre>', result.stdout)
    if not match:
        return [f"{path}: interaction quality metrics were not produced"], []
    try:
        metrics = json.loads(html.unescape(match.group(1)))
    except Exception as exc:
        return [f"{path}: interaction quality metrics could not be parsed: {exc}"], []

    errors = [f"{path}: {message}" for message in metrics.get("errors", [])]
    warnings = [f"{path}: {message}" for message in metrics.get("warnings", [])]
    return errors, warnings


def run_mobile_interaction_quality_check(path: Path, root: Path) -> tuple[list[str], list[str]]:
    probe = r"""
async () => {
  const errors = [];
  const warnings = [];
  const wait = () => new Promise((resolve) => setTimeout(resolve, 80));
  const visible = (el) => {
    if (!el) return false;
    const style = getComputedStyle(el);
    const rect = el.getBoundingClientRect();
    return style.display !== 'none' && style.visibility !== 'hidden' && rect.width > 0 && rect.height > 0;
  };
  const text = (el) => (el && el.innerText ? el.innerText.replace(/\s+/g, ' ').trim() : '');
  const closeOpenPanels = async () => {
    const close = document.querySelector('[data-close],.close-drawer,[aria-label*="关闭"],[aria-label*="Close"]');
    if (close) close.click();
    document.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape', bubbles: true}));
    await wait();
  };

  const panelSelector = '#term-panel[aria-hidden="false"],#term-popover[aria-hidden="false"],.term-popover[aria-hidden="false"],.term-drawer[aria-hidden="false"],[data-term-panel][aria-hidden="false"],dialog[open]';
  const termButtons = Array.from(document.querySelectorAll('.term[data-term],[data-term-id],[data-open-drawer="term"]')).filter(visible);
  for (const termButton of termButtons.slice(0, 12)) {
    await closeOpenPanels();
    const block = termButton.closest('.reading-block,[data-source-id]');
    termButton.scrollIntoView({block: 'center', inline: 'nearest'});
    await wait();
    termButton.click();
    await wait();
    const panel = document.querySelector(panelSelector);
    if (!panel || !visible(panel)) continue;
    const blockRect = block ? block.getBoundingClientRect() : null;
    if (blockRect) {
      const panelRect = panel.getBoundingClientRect();
      const overlapX = Math.max(0, Math.min(blockRect.right, panelRect.right) - Math.max(blockRect.left, panelRect.left));
      const overlapY = Math.max(0, Math.min(blockRect.bottom, panelRect.bottom) - Math.max(blockRect.top, panelRect.top));
      const ratio = (overlapX * overlapY) / Math.max(1, blockRect.width * blockRect.height);
      if (ratio > 0.55) {
        const termId = termButton.dataset.term || termButton.dataset.termId || termButton.textContent.trim();
        errors.push(`mobile term '${termId}' panel overlaps the active reading block by ${Math.round(ratio * 100)}%`);
      }
    }
  }
  await closeOpenPanels();

  const sideNote = document.querySelector('#side-note,[data-side-note]');
  const readingBlocks = Array.from(document.querySelectorAll('.reading-block,[data-source-id]')).filter(visible);
  if (sideNote && readingBlocks.length >= 2) {
    const before = text(sideNote);
    readingBlocks[1].scrollIntoView({block: 'center', inline: 'nearest'});
    readingBlocks[1].click();
    await wait();
    const after = text(sideNote);
    if (before && after && before === after) {
      errors.push('side note does not change after focusing a different reading block');
    }
  }

  const reviewChoice = Array.from(document.querySelectorAll('[data-review-choice],[data-quiz-choice]')).find(visible);
  if (reviewChoice) {
    reviewChoice.scrollIntoView({block: 'center', inline: 'nearest'});
    await wait();
    reviewChoice.click();
    await wait();
    const card = reviewChoice.closest('[data-review],.review-card,[data-quiz],.quiz-card');
    const feedback = card ? card.querySelector('.review-feedback,[data-review-feedback],.quiz-feedback,[aria-live]') : null;
    const link = feedback ? feedback.querySelector('a[href^="#"]') : null;
    if (!feedback || text(feedback).length < 16) {
      errors.push('chapter review feedback is empty or too weak on mobile');
    } else if (!link || !/回到原文|证据|source/i.test(text(link))) {
      errors.push('chapter review feedback needs a visible return-to-evidence link');
    }
  }

  return {errors, warnings};
}
"""
    metrics, error = run_playwright_probe(
        path,
        root,
        {"width": 390, "height": 844},
        probe,
        strip_scripts=False,
        wait_ms=900,
        timeout=75,
    )
    if metrics is not None:
        return analyze_interaction_metrics(path, metrics)
    return [f"{path}: mobile interaction quality check skipped or failed; strict audits must not waive dynamic mobile QA: {error}"], []


PRODUCTION_TEXT_PATTERNS = [
    (r"面向无专业背景大学生", "audience-targeting note"),
    (r"生成教学图资产", "generated asset label"),
    (r"生成教学图用于", "generated asset purpose note"),
    (r"这张生成", "generated-image production phrasing"),
    (r"Generated explainer", "generated explainer label"),
    (r"generated assets?", "generated asset label"),
    (r"\bprompt[_ -]?summary\b|生成\s*prompt|image\s*prompt|diagram\s*prompt|提示词\s*[:：]", "prompt/internal generation label"),
    (r"\bmanifest\b", "manifest/internal file label"),
    (r"\bpreflight\b", "preflight/internal workflow label"),
    (r"\bregression(?: slice)?\b", "regression/internal test label"),
    (r"\breader level\b", "reader-level internal label"),
    (r"阅读样例|页面样例|示例页面|测试页|demo|fixture", "sample/demo label in public UI"),
    (r"面向初学者", "audience-targeting note"),
    (r"\bprompt_summary\b", "prompt summary label"),
    (r"\bstacked-bilingual\b", "source rendering mode leaked to public UI"),
    (r"\bparallel-bilingual\b", "source rendering mode leaked to public UI"),
    (r"\bfigure-led\b", "source rendering mode leaked to public UI"),
    (r"\binterleaved-close-reading\b", "source rendering mode leaked to public UI"),
    (r"\bfacsimile-plus-html\b", "source rendering mode leaked to public UI"),
    (r"\bsource[_ -]?id\b", "source id implementation label"),
    (r"\bsource block\b", "source block implementation label"),
    (r"\b(?:abs|intro|bg|arch|enc|dec|emb|sdp|mh|why|train|res|var|parse|concl|code|app|sec|source)[-_][0-9]{1,3}\b", "raw source anchor id"),
    (r"\b[a-z]{2,12}0[0-9]{1,3}\b", "raw source anchor id"),
    (r"读后文时要一直追问", "internal reviewer prompt in side note"),
    (r"作者在哪里证明", "internal reviewer prompt in side note"),
    (r"哪些结论只是局部实验下成立", "internal reviewer prompt in side note"),
    (r"检查作者是否|需要验证|审稿时|作为审查|回归样本|测试样本|验收时", "internal reviewer or QA phrasing"),
    (r"本轮|这轮|上一版|当前版本|交付前|子 ?agent|subagent", "iteration/process phrasing"),
    (r"章节小测|小测|测一下这章", "quiz-like public label; use chapter core recap wording"),
    (r"待补|占位|coming soon|undefined|null", "placeholder text"),
]


def compact_text(value: str) -> str:
    return " ".join(value.split())


def normalized_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def normalized_sha256(value: str) -> str:
    return "sha256:" + hashlib.sha256(normalized_text(value).encode("utf-8")).hexdigest()


def extract_window_json(text: str, var_name: str) -> object | None:
    marker = f"window.{var_name}"
    marker_pos = text.find(marker)
    if marker_pos < 0:
        return None
    equals_pos = text.find("=", marker_pos)
    if equals_pos < 0:
        return None
    payload = text[equals_pos + 1 :].lstrip()
    try:
        value, _end = json.JSONDecoder().raw_decode(payload)
    except Exception:
        return None
    return value


def source_order_map(parser: SiteHTMLParser) -> dict[str, int]:
    order: dict[str, int] = {}
    for index, block in enumerate(parser.reading_blocks):
        source_id = str(block.get("data_source_id") or "")
        if source_id and source_id not in order:
            order[source_id] = index
    return order


def rendered_block_id_to_source_id(parser: SiteHTMLParser) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for block in parser.reading_blocks:
        rendered_id = str(block.get("id") or "")
        source_id = str(block.get("data_source_id") or "")
        if rendered_id and source_id:
            mapping[rendered_id] = source_id
    return mapping


def file_sha256(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                digest.update(chunk)
        return "sha256:" + digest.hexdigest()
    except Exception:
        return None


def explanation_length(value: str) -> int:
    return len(re.sub(r"\s+", "", value))


def source_word_count(value: str) -> int:
    return len(re.findall(r"[A-Za-z][A-Za-z0-9_-]*|[\u4e00-\u9fff]", value))


def cue_missing(text: str, cue_groups: dict[str, list[str]]) -> list[str]:
    missing: list[str] = []
    for cue_name, variants in cue_groups.items():
        if not any(variant.lower() in text.lower() for variant in variants):
            missing.append(cue_name)
    return missing


def audit_html(
    path: Path,
    root: Path,
    strict: bool,
    manifest: dict[str, object] | None,
    expected_source_blocks: int | None = None,
    skip_browser: bool = False,
) -> tuple[list[str], list[str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    parser = SiteHTMLParser()
    parser.feed(text)

    errors: list[str] = []
    warnings: list[str] = []

    if re.search(r'data-(?:term|term-id|figure|figure-id)=["\'][^"\']*[<>]', text, re.I):
        errors.append(f"{path}: interactive data attributes contain raw HTML; fix term/figure replacement before delivery")
    if re.search(r'<button\b(?:(?!</button>).)*<button\b', text, re.I | re.S):
        errors.append(f"{path}: nested <button> markup found; inline term replacement corrupted the HTML")
    if re.search(r'[A-Za-z]<button\b[^>]*\bterm\b|<button\b[^>]*\bterm\b[^>]*>[^<]*</button>[A-Za-z]', text, re.I):
        errors.append(f"{path}: inline term button splits a word; wrap the complete term or leave the word unmarked")
    if strict and re.search(r'\[data-active=["\']true["\']\]', text, re.I) and re.search(r'\.toggleAttribute\(\s*["\']data-active["\']', text, re.I):
        errors.append(f"{path}: chapter state uses toggleAttribute('data-active') with [data-active=\"true\"] CSS; set data-active=\"true\" explicitly or use reader-runtime.js")
    if strict and re.search(r'querySelectorAll\(\s*[`"\']\[data-chapter\][`"\']\s*\)', text) and re.search(r'<(?:article|section|div)[^>]*class=["\'][^"\']*reading-block[^"\']*["\'][^>]*data-chapter=', text, re.I | re.S):
        errors.append(f"{path}: chapter script binds all [data-chapter] elements, including reading blocks; bind only button/a/tab chapter controls")

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
    term_count = max(parser.class_counts.get("term", 0), len(parser.term_records))
    inline_term_count = sum(1 for item in parser.term_records if item.get("inline"))
    detached_term_count = sum(1 for item in parser.term_records if item.get("detached"))
    visible_text = parser.visible_text
    public_attr_text = " ".join(value for _name, value, _line in parser.attr_texts)
    public_text_for_scan = f"{visible_text} {public_attr_text}"
    source_texts = parser.class_texts.get("source-text", [])
    translation_texts = parser.class_texts.get("translation-text", [])
    plain_texts = parser.class_texts.get("plain-text", [])
    source_order = source_order_map(parser)
    block_id_to_source = rendered_block_id_to_source_id(parser)
    dom_blocks_by_source_global = {
        str(block.get("data_source_id")): block
        for block in parser.reading_blocks
        if block.get("data_source_id")
    }
    runtime_terms = extract_window_json(text, "LEARNING_SITE_TERMS")
    runtime_figures = extract_window_json(text, "LEARNING_SITE_FIGURES")
    source_count = max(source_count, len(source_texts))
    translation_count = max(translation_count, len(translation_texts))
    plain_count = max(plain_count, len(plain_texts))
    figure_note_texts = []
    for class_name in ("figure-note", "figure-explanation", "figure-reader", "source-figure-note"):
        figure_note_texts.extend(parser.class_texts.get(class_name, []))
    marginalia_text = " ".join(parser.class_texts.get("marginalia", []) + parser.class_texts.get("side-note", []))
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
    source_screenshot_refs = [
        src
        for src, _alt, _line in parser.images
        if re.search(r"assets/screenshots/|source-facsimile|paper-facsimile|facsimile-plus-html", src, re.I)
    ]
    has_facsimile_markup = bool(re.search(r"source-facsimile|paper-facsimile|facsimile-plus-html|排版截图", text, re.I))
    uses_reader_runtime = bool(re.search(r"LearningSiteReader|reader-runtime\.js|learning-site:chapter-change", text, re.I))

    if full_source_pre:
        errors.append(f"{path}: full source is buried in a collapsed pre block; render paragraph-level bilingual source in the main flow")
    elif any_large_pre:
        warnings.append(f"{path}: large <pre> block found; avoid using raw pre dumps as the source reading experience")

    if source_count and translation_count and source_count != translation_count:
        errors.append(f"{path}: source/translation block count mismatch ({source_count} source vs {translation_count} translation)")
    if expected_source_blocks is not None and source_count < expected_source_blocks:
        errors.append(f"{path}: expected at least {expected_source_blocks} source reading blocks, found {source_count}")
    if strict and source_count < 10:
        errors.append(f"{path}: too few source reading blocks for a paper learning site ({source_count}); use --expected-source-blocks for exact checks")
    source_language_hint = str(manifest.get("source_language", "")).lower() if isinstance(manifest, dict) else ""
    source_is_chinese = source_language_hint in {"zh", "zh-cn", "zh-hans", "chinese", "中文"}
    source_is_non_chinese = bool(source_language_hint) and not source_is_chinese
    if strict and source_is_non_chinese and not language_mode:
        errors.append(f"{path}: non-Chinese source needs a visible bilingual language mode such as 中英 / 中文 / EN only")
    if strict and language_mode and len(parser.buttons) >= 2 and not has_interaction_logic:
        errors.append(f"{path}: language controls look static; wire 中英/中文/EN buttons to actual reading-mode changes")
    if strict and plain_count < max(3, source_count // 3):
        errors.append(f"{path}: plain-language explanations look sparse ({plain_count} plain blocks for {source_count} source blocks)")
    if strict and term_count and not has_interaction_logic:
        errors.append(f"{path}: inline terms are marked but have no detected popover/drawer interaction logic")
    if strict and term_count and not has_popover_or_drawer:
        errors.append(f"{path}: inline terms need an attached popover, drawer, dialog, or side panel")
    if strict and term_count and inline_term_count == 0:
        errors.append(f"{path}: terms are not anchored inline in source/translation/explanation text ({detached_term_count} detached term chips found)")
    if strict and detached_term_count and inline_term_count < detached_term_count:
        warnings.append(f"{path}: detached term chips outnumber inline term anchors ({detached_term_count} detached vs {inline_term_count} inline)")
    if strict and (term_count or has_popover_or_drawer) and not has_close_affordance:
        errors.append(f"{path}: popovers/drawers/term panels need an obvious close state")
    if strict and (term_count or has_popover_or_drawer) and parser.aria_counts["expanded"] == 0:
        errors.append(f"{path}: interactive term/drawer controls should expose state with aria-expanded")
    if strict and (term_count or has_popover_or_drawer) and parser.aria_counts["controls"] == 0:
        errors.append(f"{path}: interactive term/drawer controls should connect triggers to panels with aria-controls")
    if strict and any(name in parser.class_counts for name in ("chapter-map", "chapter-tab", "map-item", "chapter-button")) and parser.aria_counts["current"] == 0:
        warnings.append(f"{path}: chapter navigation should mark the active chapter with aria-current")
    if strict and source_figures:
        figure_cues = {
            "what": ["它是什么", "是什么", "图里", "表里"],
            "how-to-read": ["怎么看", "读法", "先看", "如何读"],
            "comparison": ["相比", "对比", "baseline", "基线"],
            "conclusion": ["结论", "说明", "支持"],
            "why-it-matters": ["为什么重要", "重要", "作用"],
            "limitation": ["不能推出", "不能证明", "不代表", "限制"],
            "return-to-source": ["回到原文", "对应原文", "source", "source id"],
        }
        if not figure_note_texts:
            errors.append(f"{path}: source figures/tables need per-figure explanation blocks")
        elif len(figure_note_texts) < len(source_figures):
            errors.append(f"{path}: fewer figure/table explanations than source figure/table assets ({len(figure_note_texts)} notes for {len(source_figures)} assets)")
        for index, note_text in enumerate(figure_note_texts[: len(source_figures)], start=1):
            missing_cues = cue_missing(note_text, figure_cues)
            if missing_cues:
                preview = compact_text(note_text)[:80]
                errors.append(f"{path}: figure/table explanation #{index} misses cues {', '.join(missing_cues)}: {preview}")
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
        elif strict and re.search(r"assets/(figures|tables)/", src, re.I):
            dimensions = image_dimensions(asset)
            if dimensions:
                width, height = dimensions
                if width < 900:
                    errors.append(f"{path}:{line}: source figure/table asset is too low-resolution for close reading ({width}x{height}): {src}")
                elif width < 1000:
                    warnings.append(f"{path}:{line}: source figure/table asset is narrow; confirm labels remain readable ({width}x{height}): {src}")

    for src, line in parser.iframes:
        if re.search(r"\.pdf(\?|#|$)", src, re.I):
            errors.append(f"{path}:{line}: PDF iframe found; source text must be in-page")

    for attrs, line in parser.buttons:
        label = attrs.get("aria-label", "").strip() or attrs.get("title", "").strip() or attrs.get("_text", "").strip()
        if not label:
            warnings.append(f"{path}:{line}: button has no visible text, aria-label, or title")

    if strict:
        for pattern, label in PRODUCTION_TEXT_PATTERNS:
            if re.search(pattern, public_text_for_scan, re.I):
                errors.append(f"{path}: public UI exposes internal production text ({label}); rewrite as reader-facing learning copy")
        for attr_name, value, line in parser.attr_texts:
            for pattern, label in PRODUCTION_TEXT_PATTERNS:
                if re.search(pattern, value, re.I):
                    errors.append(f"{path}:{line}: public {attr_name} exposes internal production text ({label})")
        if marginalia_text and re.search(r"资产|生成教学图|manifest|preflight|regression|generated assets?", marginalia_text, re.I):
            errors.append(f"{path}: marginalia/side notes expose production or asset-management language")
        side_note_values = [
            compact_text(str(block.get("data_note") or ""))
            for block in parser.reading_blocks
            if str(block.get("data_note") or "").strip()
        ]
        generic_side_note_patterns = [
            r"这一段正在推进本章主线",
            r"先看原文提出的动作或结论",
            r"确认它和方法、证据或限制的关系",
            r"本段主要讲这一章的核心内容",
        ]
        for note in side_note_values:
            if any(re.search(pattern, note) for pattern in generic_side_note_patterns):
                errors.append(f"{path}: side note copy is templated instead of paragraph-specific teaching copy: {note[:80]}")
                break
        repeated_notes = {
            note: side_note_values.count(note)
            for note in set(side_note_values)
            if note and side_note_values.count(note) >= 3
        }
        if repeated_notes:
            note, count = sorted(repeated_notes.items(), key=lambda item: item[1], reverse=True)[0]
            errors.append(f"{path}: side note repeats the same copy {count} times; make notes specific to each paragraph: {note[:80]}")
        missing_source_ids = [
            str(item.get("data_block") or item.get("id") or item.get("line"))
            for item in parser.reading_blocks
            if not item.get("data_source_id")
        ]
        if parser.reading_blocks and missing_source_ids:
            errors.append(
                f"{path}: reading blocks need stable data-source-id values; missing on {len(missing_source_ids)}/{len(parser.reading_blocks)} blocks"
            )
        if parser.reading_blocks and (source_count < len(parser.reading_blocks) or plain_count < len(parser.reading_blocks)):
            errors.append(
                f"{path}: every reading-block should include source and plain-language layers ({len(parser.reading_blocks)} blocks, {source_count} source labels, {plain_count} plain labels)"
            )
        missing_block_layers: list[str] = []
        thin_block_explanations: list[str] = []
        for block in parser.reading_blocks:
            source_id = str(block.get("data_source_id") or block.get("id") or block.get("line"))
            source_value = str(block.get("source_text") or "")
            translation_value = str(block.get("translation_text") or "")
            plain_value = str(block.get("plain_text") or "")
            missing_layers = []
            if not source_value.strip():
                missing_layers.append("source")
            if source_is_non_chinese and not translation_value.strip():
                missing_layers.append("translation")
            if not plain_value.strip():
                missing_layers.append("plain")
            if missing_layers:
                missing_block_layers.append(f"{source_id}:{'/'.join(missing_layers)}")
            words = source_word_count(source_value)
            if words >= 50 and explanation_length(plain_value) < 100:
                thin_block_explanations.append(source_id)
            elif words >= 90 and explanation_length(plain_value) < 160:
                thin_block_explanations.append(source_id)
        if missing_block_layers:
            preview = ", ".join(missing_block_layers[:8])
            errors.append(f"{path}: reading blocks missing required in-block source/translation/plain layers: {preview}")
        if thin_block_explanations:
            preview = ", ".join(thin_block_explanations[:8])
            errors.append(f"{path}: dense reading blocks need proportional Chinese/plain explanation: {preview}")
        if source_count and translation_count and plain_count and not (source_count == translation_count == plain_count):
            errors.append(
                f"{path}: source/translation/plain block counts should match ({source_count}/{translation_count}/{plain_count})"
            )
        if term_count:
            required_ladder = ["术语本义", "说人话", "本文指代", "作者怎么用", "常见误解"]
            missing_ladder = [label for label in required_ladder if label not in text]
            if missing_ladder:
                errors.append(f"{path}: term explanations should include full explanation ladder; missing labels: {', '.join(missing_ladder)}")
        generic_action_counts: dict[str, int] = {}
        generic_exact_labels = {"打开图表抽屉", "继续阅读这一章", "查看详情", "展开详情", "了解更多", "阅读更多"}
        for attrs, _line in parser.buttons:
            label = attrs.get("aria-label", "").strip() or attrs.get("title", "").strip() or attrs.get("_text", "").strip()
            if label:
                generic_action_counts[label] = generic_action_counts.get(label, 0) + 1
                if re.fullmatch(r"(查看|查看详情|了解更多|展开|展开详情|继续|探索|打开|阅读|更多|详情)", label, re.I):
                    errors.append(f"{path}: vague button label '{label}' needs a concrete learning object or action")
        for label, count in sorted(generic_action_counts.items()):
            if label in generic_exact_labels:
                errors.append(f"{path}: generic button label '{label}' appears {count} times; name the figure, table, term, chapter, or learning action")
            if count > 3 and label in {"打开图表抽屉", "继续下一章", "查看详情", "展开详情", "了解更多", "展开", "打开"}:
                errors.append(f"{path}: repeated generic button label '{label}' appears {count} times; use figure/table/chapter-specific learning actions")
        long_source_failures = 0
        for index, source_value in enumerate(source_texts):
            words = source_word_count(source_value)
            explanation = plain_texts[index] if index < len(plain_texts) else ""
            if words >= 50 and explanation_length(explanation) < 100:
                long_source_failures += 1
                if long_source_failures <= 5:
                    preview = compact_text(source_value)[:90]
                    errors.append(f"{path}: dense source block #{index + 1} has too little Chinese/plain explanation ({words} source tokens): {preview}")
        if source_texts and translation_texts and len(translation_texts) < len(source_texts):
            errors.append(f"{path}: fewer translation blocks than source text blocks ({len(translation_texts)} translations for {len(source_texts)} source blocks)")

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
        source_language = str(manifest.get("source_language", "")).lower()
        framework_runtime = manifest.get("framework_runtime")
        source_blocks = manifest.get("source_blocks")
        chapter_coverage = manifest.get("chapter_coverage")
        term_anchors = manifest.get("term_anchors")
        generated_visuals = manifest.get("generated_visuals")
        paper_figures_manifest = manifest.get("paper_figures")
        generated_visual_language = str(manifest.get("generated_visual_language", "")).lower()
        design_brief = manifest.get("design_brief")
        layout_strategy = manifest.get("layout_strategy")
        visual_readability_checks = manifest.get("visual_readability_checks")
        side_note_public_copy_review = manifest.get("side_note_public_copy_review")
        source_rendering_modes = manifest.get("source_rendering_modes")
        source_screenshot_blocks = manifest.get("source_screenshot_blocks")
        interaction_inventory = manifest.get("interaction_inventory")
        term_explanations = manifest.get("term_explanations")
        source_fidelity = manifest.get("source_fidelity")
        claim_evidence_map = manifest.get("claim_evidence_map")
        formula_breakdowns = manifest.get("formula_breakdowns")
        first_viewport_landmarks = manifest.get("first_viewport_landmarks")
        section_map = manifest.get("section_map")
        chapter_landmarks = manifest.get("chapter_landmarks")
        if expected_source_blocks is not None and not isinstance(expected_source, int):
            expected_source = expected_source_blocks
        if isinstance(expected_source, int) and isinstance(rendered_source, int) and rendered_source < expected_source:
            errors.append(f"{path}: manifest says only {rendered_source}/{expected_source} source paragraphs rendered")
        if isinstance(expected_figures, int) and isinstance(rendered_figures, int) and rendered_figures < expected_figures:
            errors.append(f"{path}: manifest says only {rendered_figures}/{expected_figures} paper figures/tables rendered")
        if isinstance(expected_visuals, int) and isinstance(rendered_visuals, int) and rendered_visuals < expected_visuals:
            errors.append(f"{path}: manifest says only {rendered_visuals}/{expected_visuals} generated visuals rendered")
        image2_pattern = r"image\s*2|gpt[-\s]*image[-\s]*2|gpt\s*image\s*2"
        if strict and expected_visuals and not re.search(image2_pattern, image_model, re.I):
            errors.append(f"{path}: manifest does not clearly record Image 2/gpt-image-2 for generated visuals")
        if strict:
            for field_name, value in (
                ("source_language", source_language),
                ("source_paragraphs_expected", expected_source),
                ("source_paragraphs_rendered", rendered_source),
                ("paper_figures_expected", expected_figures),
                ("paper_figures_rendered", rendered_figures),
                ("generated_visuals_expected", expected_visuals),
                ("generated_visuals_rendered", rendered_visuals),
            ):
                if field_name == "source_language":
                    if not value:
                        errors.append(f"{path}: manifest needs source_language so bilingual requirements can be audited")
                elif not isinstance(value, int):
                    errors.append(f"{path}: manifest needs integer {field_name}")
            if isinstance(expected_source, int) and expected_source < max(10, source_count):
                errors.append(f"{path}: source_paragraphs_expected ({expected_source}) is suspiciously below rendered source blocks ({source_count}); use the extraction inventory count")
            if isinstance(rendered_source, int) and rendered_source != source_count:
                errors.append(f"{path}: source_paragraphs_rendered ({rendered_source}) must match main reader source block count ({source_count})")
            if (language_mode or term_count or source_figures or any(name in parser.class_counts for name in ("chapter-map", "chapter-tab", "map-item", "chapter-button"))):
                framework_equivalent = isinstance(framework_runtime, dict) and framework_runtime.get("equivalent_reader_runtime") is True
                if not uses_reader_runtime and not framework_equivalent:
                    errors.append(f"{path}: static reader should include assets/reader-runtime.js/LearningSiteReader or manifest.framework_runtime.equivalent_reader_runtime=true")
            if manifest.get("public_ui_clean") is False:
                errors.append(f"{path}: manifest says public_ui_clean=false")
            elif manifest.get("public_ui_clean") is not True:
                errors.append(f"{path}: manifest needs public_ui_clean=true after scanning public text")
            if not isinstance(design_brief, dict) or not design_brief:
                errors.append(f"{path}: manifest needs design_brief with paper-specific visual direction and typography/layout choices")
            else:
                required_design_keys = {
                    "visual_direction",
                    "topic_motif",
                    "typography_plan",
                    "first_viewport_visual_landmark",
                    "component_rhythm_plan",
                    "evidence_first_plan",
                    "why_not_generic",
                    "paper_artifact_cues",
                    "layout_rhythm_by_chapter",
                    "visual_motif_applied_to_header",
                    "what_must_not_reuse_from_default_template",
                }
                missing_design_keys = sorted(required_design_keys - set(str(key) for key in design_brief.keys()))
                if missing_design_keys:
                    errors.append(f"{path}: design_brief missing keys: {', '.join(missing_design_keys)}")
                design_text = " ".join(str(value) for value in design_brief.values()).lower()
                if re.search(r"\bdashboard\b|generic|ai gradient|模板|通用", design_text):
                    warnings.append(f"{path}: design_brief sounds generic; explain the paper-specific visual system")
                if re.search(r"same card|identical card|all cards|单一卡片|同一种卡片|一套卡片", design_text, re.I):
                    errors.append(f"{path}: design_brief admits one-template card rhythm; use different forms for prose, methods, figures, experiments, and review")
            if not isinstance(layout_strategy, dict) or not layout_strategy.get("summary"):
                errors.append(f"{path}: manifest needs layout_strategy.summary explaining why this reading layout fits the paper")
            else:
                if layout_strategy.get("desktop_first_viewport_checked") is not True:
                    errors.append(f"{path}: layout_strategy.desktop_first_viewport_checked must be true after browser review")
                if layout_strategy.get("mobile_layout_checked") is not True:
                    errors.append(f"{path}: layout_strategy.mobile_layout_checked must be true after responsive review")
                if layout_strategy.get("mobile_dynamic_interactions_checked") is not True:
                    errors.append(f"{path}: layout_strategy.mobile_dynamic_interactions_checked must be true after mobile term/review/side-note tests")
                if layout_strategy.get("term_panel_non_overlap_checked") is not True:
                    errors.append(f"{path}: layout_strategy.term_panel_non_overlap_checked must be true after testing term panels")
                if layout_strategy.get("side_note_sync_checked") is not True:
                    errors.append(f"{path}: layout_strategy.side_note_sync_checked must be true after testing active paragraph notes")
                if layout_strategy.get("review_return_to_evidence_checked") is not True:
                    errors.append(f"{path}: layout_strategy.review_return_to_evidence_checked must be true after testing chapter recap evidence links")
                if layout_strategy.get("empty_state_switching_checked") is not True:
                    errors.append(f"{path}: layout_strategy.empty_state_switching_checked must be true after chapter/question/language switching tests")
            if not isinstance(visual_readability_checks, dict) or not visual_readability_checks:
                errors.append(f"{path}: manifest needs visual_readability_checks for dense figures/tables/generated diagrams")
            else:
                if visual_readability_checks.get("large_view_tested") is not True:
                    errors.append(f"{path}: visual_readability_checks.large_view_tested must be true")
                if visual_readability_checks.get("dense_figures_default_readable") is not True and not visual_readability_checks.get("split_panels_used"):
                    errors.append(f"{path}: dense figures must be readable by default or split into focused panels")
            if not isinstance(side_note_public_copy_review, dict) or side_note_public_copy_review.get("checked") is not True:
                errors.append(f"{path}: manifest needs side_note_public_copy_review.checked=true after public-copy review")
            elif side_note_public_copy_review.get("forbidden_patterns_found"):
                errors.append(f"{path}: side_note_public_copy_review reports forbidden patterns: {side_note_public_copy_review.get('forbidden_patterns_found')}")
            if not isinstance(source_rendering_modes, list) or not source_rendering_modes:
                errors.append(f"{path}: manifest needs source_rendering_modes[] such as parallel-bilingual, stacked-bilingual, interleaved-close-reading, figure-led")
            elif isinstance(expected_source, int) and expected_source >= 20 and len(set(map(str, source_rendering_modes))) == 1:
                warnings.append(f"{path}: only one source rendering mode recorded for a long paper; confirm the layout is not a one-template reader")
            rendered_layout_modes = {
                attrs.get("data-layout") or attrs.get("data-rendering-mode")
                for _tag, attrs, _line in parser.starttags
                if attrs.get("data-layout") or attrs.get("data-rendering-mode")
            }
            if source_rendering_modes and not rendered_layout_modes:
                errors.append(f"{path}: source_rendering_modes are recorded but not reflected in DOM data-layout/data-rendering-mode attributes")
            elif isinstance(source_rendering_modes, list):
                missing_rendered_modes = sorted(set(map(str, source_rendering_modes)) - set(map(str, rendered_layout_modes)))
                if missing_rendered_modes:
                    errors.append(f"{path}: source_rendering_modes not represented in DOM data-layout/data-rendering-mode: {', '.join(missing_rendered_modes)}")
            if not isinstance(first_viewport_landmarks, list) or not first_viewport_landmarks:
                errors.append(f"{path}: manifest needs first_viewport_landmarks[] describing the visible paper-specific first-screen teaching object")
            else:
                for index, item in enumerate(first_viewport_landmarks, start=1):
                    if not isinstance(item, dict):
                        errors.append(f"{path}: first_viewport_landmarks[{index}] must be an object")
                        continue
                    missing = [key for key in ("selector", "source_ids", "why_this_is_paper_specific") if not item.get(key)]
                    if missing:
                        errors.append(f"{path}: first_viewport_landmarks[{index}] missing: {', '.join(missing)}")
                    landmark_path = str(item.get("path", "") or "")
                    if landmark_path and landmark_path not in text:
                        errors.append(f"{path}: first_viewport_landmarks[{index}] path is not referenced in HTML: {landmark_path}")
            if isinstance(expected_source, int) and expected_source >= 20:
                if not isinstance(section_map, list) or not section_map:
                    errors.append(f"{path}: long papers need section_map[] so the reader is not a flat chapter list")
                if not isinstance(chapter_landmarks, list) or not chapter_landmarks:
                    errors.append(f"{path}: long papers need chapter_landmarks[] with visual/evidence anchors for navigation")
            if source_screenshot_blocks is None:
                errors.append(f"{path}: manifest needs source_screenshot_blocks[]; use [] when no original-text facsimile screenshots are rendered")
            elif not isinstance(source_screenshot_blocks, list):
                errors.append(f"{path}: source_screenshot_blocks must be a list")
            if (source_screenshot_refs or has_facsimile_markup) and not source_screenshot_blocks:
                errors.append(f"{path}: source facsimile/screenshot markup is present but manifest has no source_screenshot_blocks[] entries")
            if isinstance(source_screenshot_blocks, list):
                for index, item in enumerate(source_screenshot_blocks, start=1):
                    if not isinstance(item, dict):
                        errors.append(f"{path}: source_screenshot_blocks[{index}] must be an object")
                        continue
                    required = {"source_id", "path", "reason", "selectable_text_fallback_id"}
                    missing = sorted(required - set(str(key) for key in item.keys()))
                    if missing:
                        errors.append(f"{path}: source_screenshot_blocks[{index}] missing keys: {', '.join(missing)}")
                    block_path = str(item.get("path", ""))
                    if block_path:
                        asset = (root / block_path.split("#", 1)[0].split("?", 1)[0]).resolve()
                        try:
                            asset.relative_to(root.resolve())
                        except ValueError:
                            errors.append(f"{path}: source_screenshot_blocks[{index}] path points outside site root: {block_path}")
                        if not asset.exists():
                            errors.append(f"{path}: source_screenshot_blocks[{index}] missing image asset: {block_path}")
                        if block_path not in text:
                            warnings.append(f"{path}: source_screenshot_blocks[{index}] path is not referenced in HTML: {block_path}")
                    fallback_id = str(item.get("selectable_text_fallback_id", ""))
                    if fallback_id and fallback_id not in text:
                        errors.append(f"{path}: source_screenshot_blocks[{index}] fallback id not found in HTML: {fallback_id}")
            if not isinstance(interaction_inventory, dict) or not interaction_inventory:
                errors.append(f"{path}: manifest needs interaction_inventory with real learning interactions and tested controls")
            else:
                learning_keys = {
                    "figure_hotspots",
                    "formula_breakdowns",
                    "comparison_tables",
                    "chapter_reviews",
                    "chapter_quizzes",
                    "knowledge_map",
                    "method_chats",
                    "visualizers",
                    "concept_maps",
                }
                has_learning_action = False
                for key in learning_keys:
                    value = interaction_inventory.get(key)
                    if value is True or (isinstance(value, (int, float)) and value > 0) or (isinstance(value, list) and value):
                        has_learning_action = True
                if not has_learning_action:
                    errors.append(f"{path}: interaction_inventory needs at least one non-decorative learning action beyond passive text/terms")
                feynman_value = interaction_inventory.get("feynman_recaps") or interaction_inventory.get("feynman_scaffolds")
                has_feynman_inventory = bool(
                    feynman_value is True
                    or (isinstance(feynman_value, (int, float)) and feynman_value > 0)
                    or (isinstance(feynman_value, list) and feynman_value)
                )
                has_visible_feynman = bool(re.search(r"用自己的话|复述|问题是什么|方法怎么做|证据是什么|不能推出什么", visible_text))
                has_review_cards = any(name in parser.class_counts for name in ("review-card", "quiz-card")) or "[data-review" in text
                if has_review_cards and not (has_feynman_inventory and has_visible_feynman):
                    errors.append(f"{path}: chapter recap needs a Feynman-style scaffold, not only choice buttons")
                tested_controls = interaction_inventory.get("tested_controls")
                if not isinstance(tested_controls, list) or not tested_controls:
                    errors.append(f"{path}: interaction_inventory needs tested_controls[] with trigger, state_change, close_method, and linked_source_ids")
                else:
                    for index, item in enumerate(tested_controls[:12], start=1):
                        if not isinstance(item, dict):
                            errors.append(f"{path}: tested_controls[{index}] must be an object")
                            continue
                        missing = [key for key in ("trigger", "state_change", "close_method", "linked_source_ids") if not item.get(key)]
                        if missing:
                            errors.append(f"{path}: tested_controls[{index}] missing: {', '.join(missing)}")
                        trigger_text = f"{item.get('control_id', '')} {item.get('trigger', '')}".lower()
                        if "term" in trigger_text and not item.get("return_path"):
                            errors.append(f"{path}: tested_controls[{index}] for term interaction needs return_path")
                        if "term" in trigger_text and item.get("non_overlap_checked") is not True:
                            errors.append(f"{path}: tested_controls[{index}] for term interaction needs non_overlap_checked=true")
            if not isinstance(source_fidelity, dict) or not source_fidelity:
                errors.append(f"{path}: manifest needs source_fidelity with extraction artifact and paragraph alignment evidence")
            else:
                inventory_path = str(source_fidelity.get("extraction_inventory_path") or source_fidelity.get("source_inventory_path") or "")
                inventory_hash = str(source_fidelity.get("extraction_inventory_sha256") or source_fidelity.get("source_inventory_sha256") or "")
                if not inventory_path:
                    errors.append(f"{path}: source_fidelity needs extraction_inventory_path/source_inventory_path")
                else:
                    inventory_asset = (root / inventory_path.split("#", 1)[0].split("?", 1)[0]).resolve()
                    try:
                        inventory_asset.relative_to(root.resolve())
                    except ValueError:
                        errors.append(f"{path}: source_fidelity inventory path points outside site root: {inventory_path}")
                    if not inventory_asset.exists():
                        errors.append(f"{path}: source_fidelity inventory asset is missing: {inventory_path}")
                    elif inventory_hash:
                        actual_hash = file_sha256(inventory_asset)
                        if actual_hash and actual_hash != inventory_hash:
                            errors.append(f"{path}: source_fidelity inventory hash mismatch for {inventory_path}")
                    elif strict:
                        errors.append(f"{path}: source_fidelity needs extraction_inventory_sha256/source_inventory_sha256")
                if str(source_fidelity.get("source_format", "")).lower() == "pdf" and not source_fidelity.get("source_pdf_sha256"):
                    errors.append(f"{path}: PDF source_fidelity needs source_pdf_sha256")
                if source_fidelity.get("paragraph_alignment_checked") is not True:
                    errors.append(f"{path}: source_fidelity.paragraph_alignment_checked must be true after matching rendered paragraphs to extracted source")
            if not isinstance(source_blocks, list) or not source_blocks:
                errors.append(f"{path}: manifest needs source_blocks[] with per-paragraph ids/hashes, not only total source paragraph counts")
            if not isinstance(chapter_coverage, list) or not chapter_coverage:
                errors.append(f"{path}: manifest needs chapter_coverage[] with expected/rendered/missing source ids per chapter")
            if isinstance(source_blocks, list) and isinstance(rendered_source, int) and len(source_blocks) < rendered_source:
                errors.append(f"{path}: manifest source_blocks length ({len(source_blocks)}) is smaller than rendered source count ({rendered_source})")
            if isinstance(chapter_coverage, list):
                for index, chapter in enumerate(chapter_coverage, start=1):
                    if not isinstance(chapter, dict):
                        continue
                    missing_ids = chapter.get("missing_source_ids")
                    if isinstance(missing_ids, list) and missing_ids:
                        errors.append(f"{path}: chapter_coverage[{index}] has missing_source_ids: {', '.join(map(str, missing_ids[:5]))}")
                    expected_ids = chapter.get("expected_source_ids")
                    rendered_ids = chapter.get("rendered_source_ids")
                    if isinstance(expected_ids, list) and isinstance(rendered_ids, list):
                        missing_rendered = sorted(set(map(str, expected_ids)) - set(map(str, rendered_ids)))
                        if missing_rendered:
                            errors.append(f"{path}: chapter_coverage[{index}] did not render expected source ids: {', '.join(missing_rendered[:5])}")
            if isinstance(source_blocks, list):
                dom_blocks_by_source = dict(dom_blocks_by_source_global)
                missing_render_refs = []
                missing_hash_or_snippet = []
                hash_mismatches = []
                missing_source_text = []
                for block in source_blocks:
                    if not isinstance(block, dict):
                        continue
                    source_id = str(block.get("source_id", ""))
                    rendered_block_id = str(block.get("rendered_block_id", ""))
                    if rendered_block_id and rendered_block_id not in text and source_id and source_id not in text:
                        missing_render_refs.append(rendered_block_id or source_id)
                    dom_block = dom_blocks_by_source.get(source_id)
                    if not dom_block:
                        missing_source_text.append(source_id or rendered_block_id)
                        continue
                    dom_source_text = str(dom_block.get("source_text") or "")
                    expected_hash = str(block.get("source_text_hash", "") or "")
                    normalized_snippet = str(block.get("normalized_snippet", "") or "")
                    if not expected_hash and not normalized_snippet:
                        missing_hash_or_snippet.append(source_id or rendered_block_id)
                    if expected_hash and expected_hash.startswith("sha256:") and normalized_sha256(dom_source_text) != expected_hash:
                        hash_mismatches.append(source_id or rendered_block_id)
                    if normalized_snippet and normalized_text(normalized_snippet) not in normalized_text(dom_source_text):
                        hash_mismatches.append(source_id or rendered_block_id)
                if missing_render_refs:
                    errors.append(f"{path}: manifest source_blocks do not map back to visible DOM ids/snippets: {', '.join(missing_render_refs[:5])}")
                if missing_source_text:
                    errors.append(f"{path}: manifest source_blocks missing matching .reading-block[data-source-id] in DOM: {', '.join(missing_source_text[:8])}")
                if missing_hash_or_snippet:
                    errors.append(f"{path}: source_blocks need source_text_hash or normalized_snippet for source fidelity checks: {', '.join(missing_hash_or_snippet[:8])}")
                if hash_mismatches:
                    errors.append(f"{path}: rendered source text does not match manifest hash/snippet: {', '.join(hash_mismatches[:8])}")
            if term_count:
                inline_manifest_terms = 0
                if isinstance(term_anchors, list):
                    inline_manifest_terms = sum(1 for item in term_anchors if isinstance(item, dict) and item.get("is_inline") is True)
                if not inline_manifest_terms:
                    errors.append(f"{path}: manifest needs term_anchors[] with inline source/translation/plain-text locations")
                elif isinstance(term_anchors, list):
                    required_term_keys = {"term_id", "trigger_text", "source_id", "rendered_block_id", "anchor_location", "is_inline"}
                    for index, item in enumerate(term_anchors, start=1):
                        if not isinstance(item, dict):
                            errors.append(f"{path}: term_anchors[{index}] must be an object")
                            continue
                        missing = sorted(required_term_keys - set(str(key) for key in item.keys()))
                        if missing:
                            errors.append(f"{path}: term_anchors[{index}] missing keys: {', '.join(missing)}")
                        if item.get("is_inline") is not True:
                            errors.append(f"{path}: term_anchors[{index}] must be inline; detached glossary chips are secondary only")
                        source_id = str(item.get("source_id", "") or "")
                        trigger_text = str(item.get("trigger_text", "") or "")
                        dom_block = dom_blocks_by_source.get(source_id) if "dom_blocks_by_source" in locals() else None
                        if source_id and not dom_block:
                            errors.append(f"{path}: term_anchors[{index}] source_id not found in reading blocks: {source_id}")
                        elif trigger_text and dom_block and trigger_text not in str(dom_block.get("text") or ""):
                            errors.append(f"{path}: term_anchors[{index}] trigger_text is not found inside its reading block: {trigger_text[:40]}")
                    anchors_by_term: dict[str, set[str]] = {}
                    for item in term_anchors:
                        if not isinstance(item, dict):
                            continue
                        anchors_by_term.setdefault(str(item.get("term_id", "")), set()).add(str(item.get("source_id", "")))
                    runtime_terms_dict = runtime_terms if isinstance(runtime_terms, dict) else {}
                    explanation_dict = term_explanations if isinstance(term_explanations, dict) else {}
                    for record in parser.term_records:
                        term_id = str(record.get("term_id") or "")
                        source_id = str(record.get("source_id") or "")
                        trigger_text = str(record.get("trigger_text") or term_id)
                        if not term_id or not source_id or record.get("detached"):
                            continue
                        if isinstance(term_anchors, list) and source_id not in anchors_by_term.get(term_id, set()):
                            errors.append(f"{path}: inline term '{term_id}' appears in {source_id} but manifest anchors point elsewhere")
                        runtime_record = runtime_terms_dict.get(term_id) if isinstance(runtime_terms_dict, dict) else None
                        if isinstance(runtime_record, dict):
                            runtime_sources = {
                                str(runtime_record.get("source_id") or ""),
                                *[str(item) for item in runtime_record.get("linked_source_ids", []) if item],
                            }
                            if source_id not in runtime_sources:
                                errors.append(f"{path}: inline term '{term_id}' runtime source_id does not match trigger paragraph {source_id}")
                        explanation_record = explanation_dict.get(term_id) if isinstance(explanation_dict, dict) else None
                        if isinstance(explanation_record, dict):
                            explanation_sources = {str(item) for item in explanation_record.get("linked_source_ids", [])}
                            if explanation_sources and source_id not in explanation_sources:
                                errors.append(f"{path}: inline term '{term_id}' explanation linked_source_ids do not include trigger paragraph {source_id}")
                if not isinstance(term_explanations, (list, dict)) or not term_explanations:
                    errors.append(f"{path}: manifest needs term_explanations with per-term definition/plain/paper-use/misread coverage")
                high_risk_terms = [
                    "gradient",
                    "objective function",
                    "parameter",
                    "learning rate",
                    "attention",
                    "transformer",
                    "projection",
                    "baseline",
                    "metric",
                    "epsilon",
                    "ablation",
                    "supervised fine-tuning",
                    "rejection sampling",
                ]
                anchored_text = " ".join(str(record.get("trigger_text") or "") for record in parser.term_records).lower()
                explained_text = json.dumps(term_explanations, ensure_ascii=False).lower() if isinstance(term_explanations, (dict, list)) else ""
                for term in high_risk_terms:
                    if re.search(rf"\b{re.escape(term)}\b", public_text_for_scan, re.I) and term.lower() not in anchored_text and term.lower() not in explained_text:
                        warnings.append(f"{path}: high-risk novice term appears without inline explanation coverage: {term}")
            term_strip_only_count = manifest.get("term_strip_only_count")
            if isinstance(term_strip_only_count, int) and term_strip_only_count > 0:
                errors.append(f"{path}: manifest reports {term_strip_only_count} terms that only exist in detached strips")
            strong_claim_pattern = (
                r"\b(improves?|improved|outperform(?:s|ed)?|competitive|match(?:es|ed)?|exceed(?:s|ed)?|"
                r"better|best|reduce(?:s|d)?|lower (?:cost|latency|memory|loss|error|requirement)|fewer|less|efficient|efficiency|faster|preserve(?:s|d)? performance|"
                r"cost|latency|memory requirement)\b|更好|提升|超过|优于|竞争力|更快|成本低|减少|降低|节省|更省|高效|效果|性能"
            )
            strong_claim_blocks = [
                block
                for block in parser.reading_blocks
                if block.get("data_source_id") and re.search(strong_claim_pattern, str(block.get("text") or ""), re.I)
            ]
            strong_claim_source_ids = [
                str(block.get("data_source_id") or "")
                for block in strong_claim_blocks
            ]
            if strong_claim_source_ids:
                if not isinstance(claim_evidence_map, list) or not claim_evidence_map:
                    errors.append(f"{path}: strong result/efficiency claims need claim_evidence_map with baseline, metric/dimension, evidence, and limitation")
                else:
                    source_evidence_kinds = {"source_figure", "source_table", "source_paragraph", "source_experiment", "source_formula", "source_algorithm"}
                    evidence_dom_ids = {
                        attrs.get("data-evidence-id") or attrs.get("data-figure-id") or attrs.get("id")
                        for _tag, attrs, _line in parser.starttags
                        if attrs.get("data-evidence-id") or attrs.get("data-figure-id") or attrs.get("data-formula-breakdown") or attrs.get("id")
                    }
                    evidence_dom_ids = {str(item) for item in evidence_dom_ids if item}
                    evidence_dom_ids.update(source_order.keys())
                    claim_dom_ids = {
                        value
                        for _tag, attrs, _line in parser.starttags
                        for value in (attrs.get("data-claim-id"), attrs.get("id"))
                        if value
                    }
                    claim_dom_ids = {str(item) for item in claim_dom_ids if item}
                    covered_claim_sources: set[str] = set()
                    for index, item in enumerate(claim_evidence_map, start=1):
                        if not isinstance(item, dict):
                            errors.append(f"{path}: claim_evidence_map[{index}] must be an object")
                            continue
                        source_ids = {str(value) for value in item.get("source_ids", [])}
                        source_ids.update(str(value) for value in item.get("linked_source_ids", []))
                        covered_claim_sources.update(source_ids)
                        required_claim_fields = {
                            "claim_id",
                            "claim_role",
                            "source_ids",
                            "comparison_baseline",
                            "metric_or_dimension",
                            "direction_or_value",
                            "limitation",
                            "evidence_items",
                        }
                        missing = sorted(field for field in required_claim_fields if not item.get(field))
                        if missing:
                            errors.append(f"{path}: claim_evidence_map[{index}] missing fields: {', '.join(missing)}")
                        claim_role = str(item.get("claim_role") or "")
                        if claim_role not in {"source_claim_to_verify", "supported_conclusion"}:
                            errors.append(f"{path}: claim_evidence_map[{index}] claim_role must be source_claim_to_verify or supported_conclusion")
                        claim_dom_id = str(item.get("claim_dom_id") or "")
                        if claim_dom_id and claim_dom_id not in claim_dom_ids:
                            errors.append(f"{path}: claim_evidence_map[{index}] claim_dom_id not found in HTML: {claim_dom_id}")
                        evidence_items = item.get("evidence_items")
                        if not isinstance(evidence_items, list) or not evidence_items:
                            errors.append(f"{path}: claim_evidence_map[{index}] needs evidence_items[] with evidence_id, evidence_kind, dom_id, and supports_vs_illustrates")
                            evidence_items = []
                        has_source_support = False
                        for evidence_index, evidence in enumerate(evidence_items, start=1):
                            if not isinstance(evidence, dict):
                                errors.append(f"{path}: claim_evidence_map[{index}].evidence_items[{evidence_index}] must be an object")
                                continue
                            missing_evidence = [
                                field
                                for field in ("evidence_id", "evidence_kind", "dom_id", "supports_vs_illustrates")
                                if not evidence.get(field)
                            ]
                            if missing_evidence:
                                errors.append(
                                    f"{path}: claim_evidence_map[{index}].evidence_items[{evidence_index}] missing fields: {', '.join(missing_evidence)}"
                                )
                            evidence_kind = str(evidence.get("evidence_kind") or "")
                            support_role = str(evidence.get("supports_vs_illustrates") or "")
                            dom_id = str(evidence.get("dom_id") or "")
                            if dom_id and dom_id not in evidence_dom_ids:
                                errors.append(f"{path}: claim_evidence_map[{index}].evidence_items[{evidence_index}] dom_id not found in HTML: {dom_id}")
                            if support_role == "supports" and evidence_kind in source_evidence_kinds:
                                has_source_support = True
                            if evidence_kind.startswith("generated") and support_role == "supports" and claim_role == "supported_conclusion":
                                errors.append(
                                    f"{path}: claim_evidence_map[{index}] uses a generated visual as proof; generated visuals may illustrate but not prove result claims"
                                )
                        if claim_role == "supported_conclusion" and not has_source_support:
                            errors.append(f"{path}: claim_evidence_map[{index}] supported conclusions need at least one source evidence item")
                        if claim_role == "source_claim_to_verify":
                            linked_text = " ".join(str(dom_blocks_by_source_global.get(source_id, {}).get("text", "")) for source_id in source_ids)
                            if not re.search(
                                r"不能单独证明|不能.*证明|还要看|还需要|需要.*(?:实验|表格|证据)|待验证|not prove|cannot.*prove|needs?.*(?:table|evidence|experiment)|requires.*evidence",
                                f"{linked_text} {item.get('limitation', '')}",
                                re.I,
                            ):
                                errors.append(f"{path}: claim_evidence_map[{index}] source_claim_to_verify needs visible caveat text that sends readers to later evidence")
                    missing_claim_sources = sorted(set(strong_claim_source_ids) - covered_claim_sources)
                    if missing_claim_sources:
                        errors.append(f"{path}: strong claim paragraphs missing claim_evidence_map coverage: {', '.join(missing_claim_sources[:8])}")
            is_chinese_bilingual = source_language not in {"", "zh", "zh-cn", "zh-hans"} and language_mode
            if is_chinese_bilingual and isinstance(rendered_visuals, int) and rendered_visuals > 0:
                if generated_visual_language and generated_visual_language not in {"zh-dominant", "chinese-dominant"}:
                    errors.append(f"{path}: generated diagrams should be Chinese-dominant for Chinese-bilingual sites, got '{generated_visual_language}'")
                if not generated_visual_language:
                    errors.append(f"{path}: manifest must record generated_visual_language for Chinese-bilingual generated diagrams")
            if isinstance(chapter_coverage, list):
                non_appendix_chapters = [
                    chapter
                    for chapter in chapter_coverage
                    if isinstance(chapter, dict)
                    and not re.search(
                        r"appendix|references|bibliography|supplement|附录|参考文献",
                        f"{chapter.get('chapter_id', '')} {chapter.get('title', '')}",
                        re.I,
                    )
                ]
                if isinstance(rendered_visuals, int) and non_appendix_chapters and rendered_visuals < len(non_appendix_chapters):
                    errors.append(
                        f"{path}: generated visuals are below the per-chapter teaching expectation ({rendered_visuals} visuals for {len(non_appendix_chapters)} non-appendix chapters)"
                    )
                for index, chapter in enumerate(non_appendix_chapters, start=1):
                    visual_ids = chapter.get("generated_visual_ids")
                    if visual_ids is not None and not visual_ids:
                        errors.append(f"{path}: chapter_coverage[{index}] has no generated_visual_ids; each major chapter needs a teaching visual or a justified omission")
            if isinstance(generated_visuals, list):
                if isinstance(rendered_visuals, int) and len(generated_visuals) < rendered_visuals:
                    errors.append(f"{path}: generated_visuals[] length ({len(generated_visuals)}) is smaller than generated_visuals_rendered ({rendered_visuals})")
                source_position_by_id = {
                    source_id: text.find(f'data-source-id="{source_id}"')
                    for source_id in source_order
                }
                for index, item in enumerate(generated_visuals, start=1):
                    if not isinstance(item, dict):
                        continue
                    item_model = str(item.get("model_name") or item.get("tool") or image_model or "")
                    if not item_model:
                        errors.append(f"{path}: generated visual #{index} must record model_name/tool")
                    elif strict and not re.search(image2_pattern, item_model, re.I):
                        errors.append(f"{path}: generated visual #{index} must record Image 2/gpt-image-2 provenance, not '{item_model}'")
                    visual_path = str(item.get("path", "") or "")
                    if not visual_path:
                        errors.append(f"{path}: generated visual #{index} must record a local bitmap path")
                    else:
                        if re.search(r"\.svg(\?|#|$)", visual_path, re.I):
                            errors.append(f"{path}: generated visual #{index} path is SVG; use a real Image 2 bitmap asset: {visual_path}")
                        asset = (root / visual_path.split("#", 1)[0].split("?", 1)[0]).resolve()
                        try:
                            asset.relative_to(root.resolve())
                        except ValueError:
                            errors.append(f"{path}: generated visual #{index} path points outside site root: {visual_path}")
                        if not asset.exists():
                            errors.append(f"{path}: generated visual #{index} missing image asset: {visual_path}")
                        if visual_path not in text:
                            errors.append(f"{path}: generated visual #{index} path is not referenced in HTML: {visual_path}")
                    for key in ("teaches_concept", "reader_question", "why_image_needed"):
                        if not item.get(key):
                            errors.append(f"{path}: generated visual #{index} must record {key}")
                    if not item.get("linked_source_ids") and not item.get("linked_claim_ids"):
                        errors.append(f"{path}: generated visual #{index} should link to source paragraphs or claims")
                    linked_sources = [str(value) for value in item.get("linked_source_ids", []) if value]
                    if linked_sources and visual_path:
                        visual_position = text.find(visual_path)
                        linked_indices = [source_order[value] for value in linked_sources if value in source_order]
                        linked_positions = [source_position_by_id[value] for value in linked_sources if source_position_by_id.get(value, -1) >= 0]
                        if linked_indices and visual_position >= 0:
                            preceding_blocks = len(re.findall(r'data-source-id=', text[:visual_position]))
                            preceding_linked_indices = [value for value in linked_indices if value <= preceding_blocks]
                            anchor_index = max(preceding_linked_indices) if preceding_linked_indices else min(linked_indices)
                            if preceding_blocks - anchor_index > 5:
                                errors.append(f"{path}: generated visual #{index} is too far from its first linked source paragraph")
                        if linked_positions and visual_position >= 0:
                            preceding_linked_positions = [value for value in linked_positions if value <= visual_position]
                            anchor_pos = max(preceding_linked_positions) if preceding_linked_positions else min(linked_positions)
                            next_review_pos = text.find("review-card", anchor_pos)
                            if next_review_pos >= 0 and next_review_pos < visual_position:
                                errors.append(f"{path}: generated visual #{index} appears after the chapter review instead of inside the reading path")
                    language = str(item.get("in_image_text_language", item.get("prompt_language", ""))).lower()
                    ratio = item.get("chinese_label_ratio")
                    if is_chinese_bilingual and not language:
                        errors.append(f"{path}: generated visual #{index} must record in_image_text_language or prompt_language")
                    if is_chinese_bilingual and language and language not in {"zh", "zh-dominant", "chinese", "chinese-dominant", "mixed"}:
                        errors.append(f"{path}: generated visual #{index} records non-Chinese-dominant in-image language: {language}")
                    if is_chinese_bilingual and isinstance(ratio, (int, float)) and ratio < 0.6:
                        errors.append(f"{path}: generated visual #{index} has low Chinese label ratio ({ratio}); use Chinese-dominant labels/callouts")
                    factual_values = item.get("factual_values_used")
                    source_refs = item.get("source_refs_for_values")
                    if factual_values and not source_refs:
                        errors.append(f"{path}: generated visual #{index} uses factual values without source_refs_for_values")
                    in_image_claims = item.get("in_image_claims")
                    if in_image_claims and not (item.get("linked_claim_ids") or item.get("source_refs_for_values")):
                        errors.append(f"{path}: generated visual #{index} contains in-image claims without linked claim/value sources")
            elif strict and isinstance(rendered_visuals, int) and rendered_visuals > 0:
                errors.append(f"{path}: manifest must include generated_visuals[] entries with language and source-link metadata")
            if interaction_inventory and isinstance(interaction_inventory, dict):
                formula_count = interaction_inventory.get("formula_breakdowns")
                formula_like_text = bool(re.search(r"ΔW|\\bW\\b.*\\bA\\b.*\\bB\\b|m_hat|v_hat|m\s*和\s*v|epsilon|β|beta|Algorithm\\s*\\d|伪代码|公式|更新式", visible_text, re.I))
                needs_formula_manifest = (
                    formula_count is True
                    or (isinstance(formula_count, (int, float)) and formula_count > 0)
                    or formula_like_text
                    or "data-formula-breakdown" in text
                )
                if needs_formula_manifest:
                    if not isinstance(formula_breakdowns, list) or not formula_breakdowns:
                        errors.append(f"{path}: manifest needs formula_breakdowns[] with formula/algorithm line-level explanation metadata")
                    else:
                        formula_dom_ids = {
                            attrs.get("data-formula-breakdown") or attrs.get("id")
                            for _tag, attrs, _line in parser.starttags
                            if attrs.get("data-formula-breakdown") or ("formula" in attrs.get("class", ""))
                        }
                        formula_dom_ids = {str(item) for item in formula_dom_ids if item}
                        for index, item in enumerate(formula_breakdowns, start=1):
                            if not isinstance(item, dict):
                                errors.append(f"{path}: formula_breakdowns[{index}] must be an object")
                                continue
                            required_formula_fields = {"formula_id", "formula_dom_id", "linked_source_ids", "symbols", "step_explanation", "plain_example"}
                            missing = sorted(field for field in required_formula_fields if not item.get(field))
                            if missing:
                                errors.append(f"{path}: formula_breakdowns[{index}] missing fields: {', '.join(missing)}")
                            formula_dom_id = str(item.get("formula_dom_id") or "")
                            if formula_dom_id and formula_dom_id not in formula_dom_ids and formula_dom_id not in text:
                                errors.append(f"{path}: formula_breakdowns[{index}] formula_dom_id not found in HTML: {formula_dom_id}")
                            if formula_dom_id:
                                dom_match = re.search(
                                    rf'<section\b[^>]+(?:id|data-formula-breakdown)=["\']{re.escape(formula_dom_id)}["\'][\s\S]*?</section>',
                                    text,
                                    re.I,
                                )
                                dom_text = dom_match.group(0) if dom_match else ""
                                if dom_text and not re.search(r"符号|变量|symbol", dom_text, re.I):
                                    errors.append(f"{path}: formula breakdown '{formula_dom_id}' needs a visible symbol/variable table")
                                if dom_text and not re.search(r"步骤|逐步|step|先.*再|1\\.|2\\.", dom_text, re.I):
                                    errors.append(f"{path}: formula breakdown '{formula_dom_id}' needs visible step-by-step explanation")
                                if dom_text and not re.search(r"例子|比如|example|假设", dom_text, re.I):
                                    errors.append(f"{path}: formula breakdown '{formula_dom_id}' needs a visible concrete example")
            if isinstance(paper_figures_manifest, list):
                if isinstance(rendered_figures, int) and len(paper_figures_manifest) < rendered_figures:
                    errors.append(f"{path}: paper_figures[] length ({len(paper_figures_manifest)}) is smaller than paper_figures_rendered ({rendered_figures})")
                paper_figures_by_id = {
                    str(item.get("figure_id") or item.get("id") or ""): item
                    for item in paper_figures_manifest
                    if isinstance(item, dict)
                }
                for index, item in enumerate(paper_figures_manifest, start=1):
                    if not isinstance(item, dict):
                        continue
                    if not (item.get("primary_rendered_block_id") or item.get("primary_source_id") or item.get("linked_source_ids")):
                        errors.append(f"{path}: paper figure/table #{index} needs a primary in-flow reading position linked to source ids")
                    primary_block = str(item.get("primary_rendered_block_id", "") or "")
                    primary_source = str(item.get("primary_source_id", "") or "")
                    figure_path = str(item.get("path", "") or "")
                    if primary_block and primary_block not in text:
                        errors.append(f"{path}: paper figure/table #{index} primary_rendered_block_id not found in HTML: {primary_block}")
                    if primary_source and primary_source not in text:
                        errors.append(f"{path}: paper figure/table #{index} primary_source_id not found in HTML: {primary_source}")
                    if figure_path and figure_path not in text:
                        warnings.append(f"{path}: paper figure/table #{index} path is not referenced in HTML: {figure_path}")
                    cues = item.get("explanation_cues_present")
                    if isinstance(cues, list):
                        required = {"它是什么", "怎么看", "相比谁", "结论是什么", "为什么重要", "不能推出什么", "回到原文"}
                        missing = sorted(required - {str(cue) for cue in cues})
                        if missing:
                            errors.append(f"{path}: paper figure/table #{index} manifest explanation cues missing: {', '.join(missing)}")
                    else:
                        errors.append(f"{path}: paper figure/table #{index} needs explanation_cues_present[]")
                runtime_figures_dict = runtime_figures if isinstance(runtime_figures, dict) else {}
                for figure_id, item in paper_figures_by_id.items():
                    allowed_sources = {
                        str(value)
                        for value in item.get("linked_source_ids", [])
                        if value
                    }
                    if item.get("primary_source_id"):
                        allowed_sources.add(str(item.get("primary_source_id")))
                    primary_block = str(item.get("primary_rendered_block_id") or "")
                    if primary_block and primary_block in block_id_to_source:
                        allowed_sources.add(block_id_to_source[primary_block])
                    section_match = re.search(
                        rf'<section\b(?=[^>]*data-figure-id=["\']{re.escape(figure_id)}["\'])(?=[^>]*class=["\'][^"\']*source-figure)[\s\S]*?</section>',
                        text,
                        re.I,
                    )
                    if section_match:
                        href_targets = re.findall(r'<a\b[^>]*href=["\']#([^"\']+)["\']', section_match.group(0), re.I)
                        for target in href_targets:
                            target_source = block_id_to_source.get(target, target)
                            if allowed_sources and target_source not in allowed_sources:
                                errors.append(
                                    f"{path}: paper figure/table '{figure_id}' visible return link points to {target_source}, not its manifest source cluster"
                                )
                    runtime_record = runtime_figures_dict.get(figure_id) if isinstance(runtime_figures_dict, dict) else None
                    if isinstance(runtime_record, dict):
                        runtime_source = str(runtime_record.get("source_id") or "")
                        if runtime_source and allowed_sources and runtime_source not in allowed_sources:
                            errors.append(
                                f"{path}: paper figure/table '{figure_id}' runtime source_id {runtime_source} disagrees with manifest linked sources"
                            )
            elif isinstance(expected_figures, int) and expected_figures > 0:
                errors.append(f"{path}: manifest needs paper_figures[] with primary placement and per-figure explanation metadata")
    elif strict:
        errors.append(f"{path}: no learning-site manifest found; add data/learning-site-manifest.json for exact coverage checks")

    if strict and not skip_browser:
        render_errors, render_warnings = run_desktop_first_viewport_check(path, root)
        errors.extend(render_errors)
        warnings.extend(render_warnings)
        render_errors, render_warnings = run_mobile_render_check(path, root)
        errors.extend(render_errors)
        warnings.extend(render_warnings)
        render_errors, render_warnings = run_interaction_quality_check(path, root)
        errors.extend(render_errors)
        warnings.extend(render_warnings)
        render_errors, render_warnings = run_mobile_interaction_quality_check(path, root)
        errors.extend(render_errors)
        warnings.extend(render_warnings)
    elif strict and skip_browser:
        warnings.append(f"{path}: browser probes skipped; run full --strict before final delivery")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a static paper learning site.")
    parser.add_argument("target", help="Path to site directory or HTML file")
    parser.add_argument("--strict", action="store_true", help="Treat core product-quality gaps as errors")
    parser.add_argument("--expected-source-blocks", type=int, help="Expected minimum number of source reading blocks in the main reader")
    parser.add_argument("--skip-browser", action="store_true", help="Skip Chrome-based probes for fast iteration; do not use for final delivery")
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
        errors, warnings = audit_html(html_file, root, args.strict, manifest, args.expected_source_blocks, args.skip_browser)
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
