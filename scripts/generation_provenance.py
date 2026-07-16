#!/usr/bin/env python3
"""Shared receipt binding for generated bitmap assets."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clean_hash(value: object) -> str:
    return str(value or "").replace("sha256:", "").strip().lower()


def _inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def validate_generated_asset_provenance(item: dict, asset: Path, root: Path) -> list[str]:
    """Bind a final PPT/HTML bitmap to a real receipt, response, and raw model output."""
    issues: list[str] = []
    provenance = item.get("generation_provenance")
    if not isinstance(provenance, dict):
        return ["generation_provenance must be an object"]
    for field in (
        "provider",
        "tool",
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
    if not asset.exists():
        issues.append("final generated bitmap is missing")
        return issues

    raw_path = (root / str(provenance.get("raw_output_path", ""))).resolve()
    receipt_path = (root / str(provenance.get("run_receipt_path", ""))).resolve()
    response_path = (root / str(provenance.get("provider_response_path", ""))).resolve()
    for label, path, expected_parent in (
        ("raw_output_path", raw_path, root / "raw" / "model-outputs"),
        ("run_receipt_path", receipt_path, root / "raw" / "receipts"),
        ("provider_response_path", response_path, root / "raw" / "provider-responses"),
    ):
        if not _inside(path, expected_parent):
            issues.append(f"{label} must be under {expected_parent.relative_to(root)}")
        if not path.exists():
            issues.append(f"{label} does not exist")

    if raw_path.exists():
        raw_hash = file_sha256(raw_path)
        if clean_hash(provenance.get("raw_output_sha256")) != raw_hash:
            issues.append("raw_output_sha256 is missing or incorrect")
        if file_sha256(asset) != raw_hash:
            issues.append("final bitmap does not byte-match the recorded raw model output")

    if receipt_path.exists():
        if clean_hash(provenance.get("run_receipt_sha256")) != file_sha256(receipt_path):
            issues.append("run_receipt_sha256 is missing or incorrect")
        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        except Exception:
            receipt = {}
            issues.append("generation receipt is invalid JSON")
        expected = {
            "provider": provenance.get("provider"),
            "tool": provenance.get("tool"),
            "model": provenance.get("model"),
            "request_id": provenance.get("request_id"),
            "prompt_sha256": clean_hash(provenance.get("prompt_sha256")),
            "output_sha256": clean_hash(provenance.get("raw_output_sha256")),
        }
        for field, value in expected.items():
            actual = clean_hash(receipt.get(field)) if field.endswith("sha256") else receipt.get(field)
            if not value or actual != value:
                issues.append(f"generation receipt does not match {field}")

    if response_path.exists():
        if clean_hash(provenance.get("provider_response_sha256")) != file_sha256(response_path):
            issues.append("provider_response_sha256 is missing or incorrect")
        response_text = response_path.read_text(encoding="utf-8", errors="replace")
        for value in (
            str(provenance.get("request_id", "")),
            str(provenance.get("model", "")),
            clean_hash(provenance.get("raw_output_sha256")),
        ):
            if value and value not in response_text:
                issues.append("provider response is not bound to request/model/output")

    item_model = str(item.get("model_name") or "")
    if item_model and item_model != str(provenance.get("model") or ""):
        issues.append("model_name does not match generation_provenance.model")
    return issues
