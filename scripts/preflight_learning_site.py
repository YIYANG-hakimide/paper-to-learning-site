#!/usr/bin/env python3
"""Preflight checks for paper learning deck/site runs."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import resolve_image_route


def dependency_root() -> Path:
    return Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies"


def command_path(*names: str) -> str | None:
    dep_bin = dependency_root() / "bin"
    dep_override_bin = dep_bin / "override"
    dep_node_bin = dependency_root() / "node" / "bin"
    dep_poppler_bin = dependency_root() / "native" / "poppler" / "bin"
    dep_nested_poppler_bin = dependency_root() / "native" / "poppler" / "poppler" / "bin"
    for name in names:
        for folder in (
            dep_override_bin,
            dep_bin,
            dep_node_bin,
            dep_poppler_bin,
            dep_nested_poppler_bin,
        ):
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


def skill_status(name: str) -> dict[str, object]:
    candidates = [
        Path.home() / ".codex" / "skills" / name / "SKILL.md",
        Path.home() / ".codex" / "skills" / ".system" / name / "SKILL.md",
        Path.home() / ".agents" / "skills" / name / "SKILL.md",
        Path.home() / ".claude" / "skills" / name / "SKILL.md",
    ]
    for candidate in candidates:
        if candidate.exists():
            return status(True, str(candidate.parent))
    return status(False, "not installed in common skill directories")


def presentations_status() -> dict[str, object]:
    roots = [
        Path.home() / ".codex" / "plugins" / "cache" / "openai-primary-runtime" / "presentations",
        Path.home() / ".codex" / "skills" / "presentations",
        Path.home() / ".agents" / "skills" / "presentations",
    ]
    candidates: list[Path] = []
    for root in roots:
        if root.is_file() and root.name == "SKILL.md":
            candidates.append(root)
        elif root.exists():
            candidates.extend(root.glob("*/skills/presentations/SKILL.md"))
            candidates.extend(root.glob("SKILL.md"))
    for candidate in sorted(candidates, reverse=True):
        artifact_tool = candidate.parent / "artifact_tool"
        if candidate.exists() and artifact_tool.exists():
            return status(True, str(candidate))
    return status(False, "official Presentations skill with artifact_tool not found")


def validate_source(source: str | None) -> tuple[dict[str, object] | None, list[str]]:
    if not source:
        return None, []
    source_path = Path(source).expanduser()
    report: dict[str, object] = {
        "path": str(source_path),
        "exists": source_path.exists(),
        "size_bytes": source_path.stat().st_size if source_path.exists() else 0,
        "file_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest() if source_path.exists() else None,
        "type": source_path.suffix.lower().lstrip("."),
        "pdfinfo_ok": None,
        "python_extract_ok": None,
        "page_count": None,
        "first_text_chars": 0,
        "total_text_chars": 0,
        "empty_or_near_empty_pages": [],
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
payload = {"ok": False, "page_count": None, "first_text_chars": 0, "total_text_chars": 0, "page_text_chars": [], "error": ""}
try:
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        payload["page_count"] = len(reader.pages)
        counts = [len(((page.extract_text() or "").strip())) for page in reader.pages]
        payload["page_text_chars"] = counts
        payload["first_text_chars"] = counts[0] if counts else 0
        payload["total_text_chars"] = sum(counts)
        payload["ok"] = bool(reader.pages)
    except Exception:
        import pdfplumber
        with pdfplumber.open(path) as doc:
            payload["page_count"] = len(doc.pages)
            counts = [len(((page.extract_text() or "").strip())) for page in doc.pages]
            payload["page_text_chars"] = counts
            payload["first_text_chars"] = counts[0] if counts else 0
            payload["total_text_chars"] = sum(counts)
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
            report["total_text_chars"] = payload.get("total_text_chars") or 0
            counts = payload.get("page_text_chars") or []
            report["empty_or_near_empty_pages"] = [index + 1 for index, count in enumerate(counts) if count < 40]
            if not payload.get("ok"):
                errors.append(f"Python could not extract source PDF: {payload.get('error') or 'no readable pages'}")
            elif counts:
                empty_ratio = len(report["empty_or_near_empty_pages"]) / len(counts)
                if empty_ratio > 0.15:
                    errors.append(f"Too many PDF pages have little or no extractable text: {len(report['empty_or_near_empty_pages'])}/{len(counts)} pages. OCR or repair the source before building.")
        else:
            report["python_extract_ok"] = False
            errors.append(f"Python could not extract source PDF: {(result.stderr or result.stdout).strip()[:240]}")

    if report.get("python_extract_ok") is not True:
        errors.append("Source PDF is not readable enough to build a trustworthy learning deck or reader. Re-download or repair the PDF before extraction.")
    report["errors"] = errors
    return report, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Preflight checks for Paper and Book to Visual Learning runs.")
    parser.add_argument("--source", help="Optional PDF/article path to validate before extraction")
    parser.add_argument("--mode", choices=("image-series", "presentation-pdf", "interactive-html"), default="interactive-html")
    parser.add_argument("--deploy", action="store_true", help="Check deployment tooling when HTML deployment is requested")
    parser.add_argument(
        "--image-route-receipt",
        "--image-receipt",
        dest="image_route_receipt",
        action="append",
        default=[],
        help="Receipt from a real image-generation smoke test; repeatable",
    )
    parser.add_argument("--image-route-journal", help="Route journal containing the matching real smoke-test event")
    parser.add_argument("--image-runtime", choices=("auto", "codex", "external"), default="auto")
    parser.add_argument("--confirm-image-direct-output", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()

    pdfplumber_ok, pdfplumber_python = python_module("pdfplumber")
    pypdf_ok, pypdf_python = python_module("pypdf")
    pillow_ok, pillow_python = python_module("PIL")
    reportlab_ok, reportlab_python = python_module("reportlab")
    recommended_python = pdfplumber_python or pypdf_python or pillow_python or reportlab_python or sys.executable

    browser_required = args.mode in {"presentation-pdf", "interactive-html"}
    browser_status = playwright_browser_status() if browser_required else status(True, "not required for image-series mode")

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
        "swift": status(bool(command_path("swift")), command_path("swift")),
        "tesseract": status(bool(command_path("tesseract")), command_path("tesseract")),
        "python_pdfplumber": status(pdfplumber_ok, pdfplumber_python),
        "python_pypdf": status(pypdf_ok, pypdf_python),
        "python_pillow": status(pillow_ok, pillow_python),
        "python_reportlab": status(reportlab_ok, reportlab_python),
        "node_playwright": status(node_can_import("playwright")),
        "playwright_browser": browser_status,
        "chrome_headless": status(bool(chrome_path()), chrome_path()),
        "frontend_slides_skill": skill_status("frontend-slides"),
        "guizang_material_skill": skill_status("guizang-material-illustration"),
        "imagegen_skill": skill_status("imagegen"),
        "presentations_skill": presentations_status(),
    }

    image_generation_required = args.mode in {"image-series", "presentation-pdf", "interactive-html"}
    image_route_report = (
        resolve_image_route.resolve_image_route(
            [Path(value) for value in args.image_route_receipt],
            Path(args.image_route_journal).expanduser() if args.image_route_journal else None,
            runtime=args.image_runtime,
        )
        if image_generation_required
        else {
            "status": "not-required",
            "runtime": resolve_image_route.detect_runtime(args.image_runtime),
            "selected_route": None,
            "verified_routes": [],
            "candidates": [],
            "issues": [],
            "retry_policy": {"status": "not-required"},
        }
    )

    routes = {
        "pdf_text": checks["pdftotext"]["ok"] or checks["python_pdfplumber"]["ok"] or checks["python_pypdf"]["ok"],
        "pdf_figures": checks["pdftoppm"]["ok"] or checks["python_pillow"]["ok"],
        "image_processing": checks["python_pillow"]["ok"] or checks["sips"]["ok"] or checks["imagemagick"]["ok"],
        "actual_ocr": checks["tesseract"]["ok"] or (sys.platform == "darwin" and checks["swift"]["ok"]),
        "album_pdf_export": (checks["python_reportlab"]["ok"] or checks["python_pillow"]["ok"]) if args.mode == "image-series" else "not-required",
        "image_generation": image_route_report["status"],
        "visual_deck_layout": checks["presentations_skill"]["ok"],
        "illustration_prompting": checks["guizang_material_skill"]["ok"] or "built-in paper-specific prompting",
        "deck_export": checks["playwright_browser"]["ok"] if args.mode == "presentation-pdf" else "not-required",
        "browser_qa": checks["playwright_browser"]["ok"] if browser_required else "not-required",
        "github_publish": checks["git"]["ok"] and checks["gh"]["ok"],
        "vercel_deploy": checks["vercel"]["ok"],
    }

    source_report, source_errors = validate_source(args.source)

    blockers = []
    source_is_pdf = bool(source_report and source_report.get("type") == "pdf")
    if source_is_pdf and not routes["pdf_text"]:
        blockers.append("No PDF text extraction route found: install/use pdftotext, pdfplumber, or pypdf.")
    if source_is_pdf and not routes["pdf_figures"]:
        blockers.append("No PDF figure rendering route found: install/use pdftoppm or another reliable renderer.")
    if browser_required and not routes["browser_qa"]:
        blockers.append("No browser QA route found: install Playwright or use system Chrome.")
    if image_generation_required and not routes["actual_ocr"]:
        blockers.append("No executable OCR route found for final visual verification: install Tesseract or use macOS Swift/Vision.")
    if args.mode == "image-series" and not routes["album_pdf_export"]:
        blockers.append("No album PDF export route found: install reportlab or Pillow.")
    if image_generation_required and args.confirm_image_direct_output:
        blockers.append("Self-confirmation via --confirm-image-direct-output is prohibited and cannot verify an image route. Provide a real --image-route-receipt and --image-route-journal instead.")
    if image_generation_required and image_route_report["status"] != "ready":
        route_status = image_route_report["status"]
        runtime = image_route_report["runtime"]
        if route_status == "blocked_waiting_user":
            if image_route_report.get("block_reason") == "external_fallback_requires_user_confirmation":
                blockers.append("blocked_waiting_user: Codex built-in imagegen failed or only an external route is verified. Ask the user to explicitly confirm the CLI/API fallback before using it.")
            else:
                blockers.append("blocked_waiting_user: image generation had three consecutive HTTP 504 transport failures and about eight minutes without success. Stop retrying and ask the user before changing provider/model or configuration.")
        elif route_status == "transport_cooldown":
            wait_seconds = image_route_report.get("retry_policy", {}).get("retry_after_seconds", 0)
            blockers.append(f"Image transport reached the three-attempt HTTP 504 cap. Do not retry or downgrade the model/provider; remain in transport cooldown for about {wait_seconds} more seconds.")
        elif route_status == "transport_retry_scheduled":
            wait_seconds = image_route_report.get("retry_policy", {}).get("retry_after_seconds", 0)
            blockers.append(f"Image transport retry is backing off for {wait_seconds} more seconds. Keep the same model/provider; a transport switch is not a model downgrade.")
        elif route_status == "needs_user_configuration":
            blockers.append("No usable external image-generation tool/API configuration was detected. Ask the user to configure a supported CLI or API credential, then run a real smoke test and record its receipt and route journal.")
        elif runtime == "codex":
            blockers.append("Image-generation direct-output capability is unverified. Use the preferred built-in imagegen route for a real smoke test, then provide its local raster receipt and route journal; self-confirmation is not accepted.")
        else:
            blockers.append("Image generation is not verified. Run a real smoke test with the detected external tool/API and provide its local raster receipt plus route journal.")
    if args.mode == "presentation-pdf" and not routes["deck_export"]:
        blockers.append("No browser route found for presentation PDF export.")
    if args.mode == "presentation-pdf" and not routes["visual_deck_layout"]:
        blockers.append("The official Presentations skill and editable artifact-tool engine are unavailable. Configure an equivalent editable PPT engine or choose the learning-album mode.")
    if args.mode == "presentation-pdf" and not checks["pdftotext"]["ok"]:
        blockers.append("pdftotext is required to scan final PDF copy and language quality.")
    if args.deploy and args.mode == "interactive-html" and not routes["vercel_deploy"]:
        blockers.append("Vercel CLI is unavailable for the requested deployment.")
    blockers.extend(source_errors)

    report = {
        "checks": checks,
        "mode": args.mode,
        "routes": routes,
        "image_route": image_route_report,
        "source": source_report,
        "recommended_commands": {
            "python": recommended_python,
            "node": command_path("node"),
            "chrome": chrome_path(),
            "browser_qa_driver": checks["playwright_browser"]["detail"] or checks["chrome_headless"]["detail"],
        },
        "manual_checks": {
            "image_generation": "In Codex, call the built-in imagegen route first. Outside Codex, detect a configured tool/API and ask the user to configure one when none is available. Availability is proven only by a real receipt plus route journal.",
            "image_asset_export": "The receipt must bind a PNG/JPG/WebP local asset to its SHA-256. A chat-only preview or a --confirm flag is not evidence.",
            "image_series_direct_output": "For image-series mode, the verified model must generate the complete Chinese infographic as one untouched raster file. Preserve the real receipt and route journal; post-composed pages are not allowed."
        },
        "blockers": blockers,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
