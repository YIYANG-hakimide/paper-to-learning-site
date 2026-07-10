#!/usr/bin/env python3
"""Preflight checks for paper-to-learning-site runs."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def dependency_root() -> Path:
    return Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies"


def command_path(*names: str) -> str | None:
    dep_bin = dependency_root() / "bin"
    dep_node_bin = dependency_root() / "node" / "bin"
    for name in names:
        for folder in (dep_bin, dep_node_bin):
            candidate = folder / name
            if candidate.exists():
                return str(candidate)
        path = shutil.which(name)
        if path:
            return path
    return None


def bundled_python() -> Path:
    return dependency_root() / "python" / "bin" / "python3"


def python_module(name: str) -> tuple[bool, str | None]:
    if importlib.util.find_spec(name) is not None:
        return True, sys.executable
    candidate = bundled_python()
    if candidate.exists():
        code = f"import {name}"
        try:
            result = subprocess.run([str(candidate), "-c", code], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
        except Exception:
            return False, None
        if result.returncode == 0:
            return True, str(candidate)
    return False, None


def node_can_import(package: str) -> bool:
    node = command_path("node")
    if not node:
        return False
    code = f"try {{ require('{package}'); process.exit(0); }} catch (error) {{ process.exit(1); }}"
    env = dict(os.environ)
    node_modules = dependency_root() / "node" / "node_modules"
    if node_modules.exists():
        env["NODE_PATH"] = str(node_modules)
    try:
        result = subprocess.run([node, "-e", code], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10, env=env)
    except Exception:
        return False
    return result.returncode == 0


def playwright_browser_status() -> dict[str, object]:
    node = command_path("node")
    if not node:
        return status(False, "Node.js not found")
    node_modules = dependency_root() / "node" / "node_modules"
    env = dict(os.environ)
    if node_modules.exists():
        env["NODE_PATH"] = str(node_modules)
    system_chrome = chrome_path()
    if system_chrome:
        env["PLAYWRIGHT_CHROME_EXECUTABLE"] = system_chrome
    code = r"""
const { chromium } = require('playwright');
(async () => {
  const executablePath = process.env.PLAYWRIGHT_CHROME_EXECUTABLE || undefined;
  const launchOptions = {
    headless: true,
    args: ['--disable-background-networking', '--no-default-browser-check', '--no-first-run']
  };
  if (executablePath) launchOptions.executablePath = executablePath;
  const browser = await chromium.launch(launchOptions);
  const page = await browser.newPage({ viewport: { width: 390, height: 800 } });
  await page.setContent('<!doctype html><title>qa</title><p>browser qa ready</p>');
  await browser.close();
})().catch((error) => {
  console.error(error && error.message ? error.message : String(error));
  process.exit(1);
});
"""
    try:
        result = subprocess.run([node, "-e", code], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, timeout=20, env=env)
    except Exception as exc:
        return status(False, f"Playwright launch check failed: {exc}")
    if result.returncode == 0:
        detail = f"Playwright via system Chrome: {system_chrome}" if system_chrome else "Playwright managed Chromium"
        return status(True, detail)
    detail = (result.stderr or "").strip().splitlines()[0:2]
    return status(False, " ".join(detail)[:240])


def chrome_path() -> str | None:
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    return command_path("google-chrome", "google-chrome-stable", "chromium", "chromium-browser")


def status(ok: bool, detail: str | None = None) -> dict[str, object]:
    return {"ok": ok, "detail": detail or ""}


def validate_source(source: str | None) -> tuple[dict[str, object] | None, list[str]]:
    if not source:
        return None, []
    source_path = Path(source).expanduser()
    report: dict[str, object] = {
        "path": str(source_path),
        "exists": source_path.exists(),
        "size_bytes": source_path.stat().st_size if source_path.exists() else 0,
        "type": source_path.suffix.lower().lstrip("."),
        "pdfinfo_ok": None,
        "python_extract_ok": None,
        "page_count": None,
        "first_text_chars": 0,
        "errors": [],
    }
    errors: list[str] = []
    if not source_path.exists():
        return report, [f"Source file not found: {source_path}"]
    if source_path.stat().st_size < 1024:
        errors.append("Source file is suspiciously small.")
    if source_path.suffix.lower() != ".pdf":
        report["python_extract_ok"] = True
        report["errors"] = errors
        return report, errors

    pdfinfo = command_path("pdfinfo")
    if pdfinfo:
        try:
            result = subprocess.run([pdfinfo, str(source_path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=20)
        except Exception as exc:
            result = None
            errors.append(f"pdfinfo failed to run: {exc}")
        if result:
            report["pdfinfo_ok"] = result.returncode == 0
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if line.startswith("Pages:"):
                        try:
                            report["page_count"] = int(line.split(":", 1)[1].strip())
                        except ValueError:
                            pass
            else:
                errors.append(f"pdfinfo could not read source PDF: {(result.stderr or result.stdout).strip()[:240]}")

    python = str(bundled_python() if bundled_python().exists() else Path(sys.executable))
    code = r"""
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
payload = {"ok": False, "page_count": None, "first_text_chars": 0, "error": ""}
try:
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        payload["page_count"] = len(reader.pages)
        first_text = reader.pages[0].extract_text() if reader.pages else ""
        payload["first_text_chars"] = len((first_text or "").strip())
        payload["ok"] = bool(reader.pages)
    except Exception:
        import pdfplumber
        with pdfplumber.open(path) as doc:
            payload["page_count"] = len(doc.pages)
            first_text = doc.pages[0].extract_text() if doc.pages else ""
            payload["first_text_chars"] = len((first_text or "").strip())
            payload["ok"] = bool(doc.pages)
except Exception as exc:
    payload["error"] = str(exc)
print(json.dumps(payload, ensure_ascii=False))
"""
    try:
        result = subprocess.run([python, "-c", code, str(source_path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
    except Exception as exc:
        result = None
        errors.append(f"Python PDF extraction check failed to run: {exc}")
    if result:
        if result.returncode == 0:
            try:
                payload = json.loads(result.stdout)
            except Exception as exc:
                payload = {"ok": False, "error": f"invalid JSON from extraction check: {exc}"}
            report["python_extract_ok"] = bool(payload.get("ok"))
            report["page_count"] = report["page_count"] or payload.get("page_count")
            report["first_text_chars"] = payload.get("first_text_chars") or 0
            if not payload.get("ok"):
                errors.append(f"Python could not extract source PDF: {payload.get('error') or 'no readable pages'}")
        else:
            report["python_extract_ok"] = False
            errors.append(f"Python could not extract source PDF: {(result.stderr or result.stdout).strip()[:240]}")

    if report.get("python_extract_ok") is not True:
        errors.append("Source PDF is not readable enough to build an in-page learning reader. Re-download or repair the PDF before extraction.")
    report["errors"] = errors
    return report, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Preflight checks for paper-to-learning-site runs.")
    parser.add_argument("--source", help="Optional PDF/article path to validate before extraction")
    args = parser.parse_args()

    pdfplumber_ok, pdfplumber_python = python_module("pdfplumber")
    pypdf_ok, pypdf_python = python_module("pypdf")
    pillow_ok, pillow_python = python_module("PIL")
    recommended_python = pdfplumber_python or pypdf_python or pillow_python or sys.executable

    checks: dict[str, dict[str, object]] = {
        "python3": status(bool(command_path("python3")), command_path("python3")),
        "node": status(bool(command_path("node")), command_path("node")),
        "git": status(bool(command_path("git")), command_path("git")),
        "gh": status(bool(command_path("gh")), command_path("gh")),
        "vercel": status(bool(command_path("vercel")), command_path("vercel")),
        "pdfinfo": status(bool(command_path("pdfinfo")), command_path("pdfinfo")),
        "pdftotext": status(bool(command_path("pdftotext")), command_path("pdftotext")),
        "pdftoppm": status(bool(command_path("pdftoppm")), command_path("pdftoppm")),
        "sips": status(bool(command_path("sips")), command_path("sips")),
        "imagemagick": status(bool(command_path("magick", "convert")), command_path("magick", "convert")),
        "python_pdfplumber": status(pdfplumber_ok, pdfplumber_python),
        "python_pypdf": status(pypdf_ok, pypdf_python),
        "python_pillow": status(pillow_ok, pillow_python),
        "node_playwright": status(node_can_import("playwright")),
        "playwright_browser": playwright_browser_status(),
        "chrome_headless": status(bool(chrome_path()), chrome_path()),
    }

    routes = {
        "pdf_text": checks["pdftotext"]["ok"] or checks["python_pdfplumber"]["ok"] or checks["python_pypdf"]["ok"],
        "pdf_figures": checks["pdftoppm"]["ok"] or checks["python_pillow"]["ok"],
        "image_processing": checks["python_pillow"]["ok"] or checks["sips"]["ok"] or checks["imagemagick"]["ok"],
        "image_generation": "manual_check_required",
        "browser_qa": checks["playwright_browser"]["ok"] or checks["chrome_headless"]["ok"],
        "github_publish": checks["git"]["ok"] and checks["gh"]["ok"],
        "vercel_deploy": checks["vercel"]["ok"],
    }

    source_report, source_errors = validate_source(args.source)

    blockers = []
    if not routes["pdf_text"]:
        blockers.append("No PDF text extraction route found: install/use pdftotext, pdfplumber, or pypdf.")
    if not routes["pdf_figures"]:
        blockers.append("No PDF figure rendering route found: install/use pdftoppm or another reliable renderer.")
    if not routes["browser_qa"]:
        blockers.append("No browser QA route found: install Playwright or use system Chrome.")
    blockers.extend(source_errors)

    report = {
        "checks": checks,
        "routes": routes,
        "source": source_report,
        "recommended_commands": {
            "python": recommended_python,
            "node": command_path("node"),
            "chrome": chrome_path(),
            "browser_qa_driver": checks["playwright_browser"]["detail"] or checks["chrome_headless"]["detail"],
        },
        "manual_checks": {
            "image_generation": "Verify the current Codex tool list includes Image 2 or another image generation tool before promising generated teaching diagrams.",
            "image_asset_export": "After the first generated preview, verify that a PNG/JPG/WebP can be saved or copied into the site assets/diagrams directory. A chat-only preview is not a deliverable website asset."
        },
        "blockers": blockers,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
