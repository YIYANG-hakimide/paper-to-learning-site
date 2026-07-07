#!/usr/bin/env python3
"""Preflight checks for paper-to-learning-site runs."""

from __future__ import annotations

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
    code = f"import('{package}').then(()=>process.exit(0)).catch(()=>process.exit(1))"
    env = dict(os.environ)
    node_modules = dependency_root() / "node" / "node_modules"
    if node_modules.exists():
        env["NODE_PATH"] = str(node_modules)
    try:
        result = subprocess.run([node, "-e", code], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10, env=env)
    except Exception:
        return False
    return result.returncode == 0


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


def main() -> int:
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
        "chrome_headless": status(bool(chrome_path()), chrome_path()),
    }

    routes = {
        "pdf_text": checks["pdftotext"]["ok"] or checks["python_pdfplumber"]["ok"] or checks["python_pypdf"]["ok"],
        "pdf_figures": checks["pdftoppm"]["ok"] or checks["python_pillow"]["ok"],
        "image_processing": checks["python_pillow"]["ok"] or checks["sips"]["ok"] or checks["imagemagick"]["ok"],
        "image_generation": "manual_check_required",
        "browser_qa": checks["node_playwright"]["ok"] or checks["chrome_headless"]["ok"],
        "github_publish": checks["git"]["ok"] and checks["gh"]["ok"],
        "vercel_deploy": checks["vercel"]["ok"],
    }

    blockers = []
    if not routes["pdf_text"]:
        blockers.append("No PDF text extraction route found: install/use pdftotext, pdfplumber, or pypdf.")
    if not routes["pdf_figures"]:
        blockers.append("No PDF figure rendering route found: install/use pdftoppm or another reliable renderer.")
    if not routes["browser_qa"]:
        blockers.append("No browser QA route found: install Playwright or use system Chrome.")

    report = {
        "checks": checks,
        "routes": routes,
        "recommended_commands": {
            "python": recommended_python,
            "node": command_path("node"),
            "chrome": chrome_path(),
        },
        "manual_checks": {
            "image_generation": "Verify the current Codex tool list includes Image 2 or another image generation tool before promising generated teaching diagrams."
        },
        "blockers": blockers,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
