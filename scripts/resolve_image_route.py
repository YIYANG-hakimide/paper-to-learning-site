#!/usr/bin/env python3
"""Resolve and verify image-generation routes without trusting self-attestation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


RECEIPT_SCHEMA_VERSION = 1
ROUTE_JOURNAL_SCHEMA_VERSION = 1
MAX_CONSECUTIVE_504 = 3
BLOCK_AFTER_SECONDS = 8 * 60
RETRY_BACKOFF_SECONDS = (20, 45, 90)
RASTER_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
SUCCESS_EVENTS = {"success", "smoke_test_succeeded", "generation_succeeded"}
FAILURE_EVENTS = {"failure", "smoke_test_failed", "generation_failed"}
TRANSPORT_SWITCH_EVENTS = {"transport_switch", "transport_switched"}
MODEL_PROVIDER_FALLBACK_EVENTS = {"model_provider_fallback", "provider_fallback", "model_fallback"}
CODEX_MARKERS = (
    "CODEX_THREAD_ID",
    "CODEX_CI",
    "CODEX_SHELL",
    "CODEX_INTERNAL_ORIGINATOR_OVERRIDE",
)
SENSITIVE_KEY_PARTS = (
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "cookie",
    "credential",
    "password",
    "private_key",
    "secret",
    "session_key",
    "token",
)
SAFE_METADATA_KEYS = {"credential_env_names"}
SECRET_VALUE_PATTERNS = (
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]+", re.I),
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{20,}"),
)


@dataclass(frozen=True)
class VerifiedRoute:
    receipt_path: Path
    journal_path: Path
    provider: str
    tool: str
    model: str
    request_id: str
    route_kind: str
    transport: str
    local_asset_path: Path
    output_sha256: str
    verified_at: datetime

    def as_dict(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "tool": self.tool,
            "model": self.model,
            "request_id": self.request_id,
            "route_kind": self.route_kind,
            "transport": self.transport,
            "local_asset_path": str(self.local_asset_path),
            "output_sha256": self.output_sha256,
            "receipt_path": str(self.receipt_path),
            "route_journal_path": str(self.journal_path),
            "verified_at": self.verified_at.isoformat(),
        }


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def load_route_journal(path: Path) -> list[dict[str, object]]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        events = []
        for line_number, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            event = json.loads(line)
            if not isinstance(event, dict):
                raise ValueError(f"Route journal line {line_number} must be a JSON object")
            events.append(event)
        return events
    if isinstance(payload, list):
        events = payload
    elif isinstance(payload, dict):
        schema_version = payload.get("schema_version")
        if schema_version not in (None, ROUTE_JOURNAL_SCHEMA_VERSION):
            raise ValueError(f"Unsupported route journal schema_version: {schema_version}")
        events = payload.get("events", [])
    else:
        raise ValueError("Route journal must be a JSON object, array, or JSONL file")
    if not isinstance(events, list) or not all(isinstance(event, dict) for event in events):
        raise ValueError("Route journal events must be JSON objects")
    return list(events)


def _sensitive_key(key: object) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", "_", str(key).lower()).strip("_")
    if normalized in SAFE_METADATA_KEYS:
        return False
    return any(part in normalized for part in SENSITIVE_KEY_PARTS)


def secret_issues(value: object, path: str = "$") -> list[str]:
    issues: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            item_path = f"{path}.{key}"
            if _sensitive_key(key) and item not in (None, "", "[REDACTED]"):
                issues.append(f"sensitive field must not be recorded: {item_path}")
            issues.extend(secret_issues(item, item_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            issues.extend(secret_issues(item, f"{path}[{index}]"))
    elif isinstance(value, str) and value != "[REDACTED]":
        if any(pattern.search(value) for pattern in SECRET_VALUE_PATTERNS):
            issues.append(f"secret-like value must not be recorded: {path}")
    return issues


def sanitize_for_journal(value: object) -> object:
    if isinstance(value, Mapping):
        clean: dict[str, object] = {}
        for key, item in value.items():
            clean[str(key)] = "[REDACTED]" if _sensitive_key(key) else sanitize_for_journal(item)
        return clean
    if isinstance(value, list):
        return [sanitize_for_journal(item) for item in value]
    if isinstance(value, str) and any(pattern.search(value) for pattern in SECRET_VALUE_PATTERNS):
        return "[REDACTED]"
    return value


def append_route_event(path: Path, event: Mapping[str, object]) -> dict[str, object]:
    clean = sanitize_for_journal(dict(event))
    assert isinstance(clean, dict)
    clean.setdefault("timestamp", utc_now().isoformat())
    existing = load_route_journal(path) if path.exists() else []
    if _is_504(clean):
        current_policy = evaluate_504_policy(existing, parse_timestamp(clean.get("timestamp")) or utc_now())
        if int(current_policy.get("consecutive_504", 0)) >= MAX_CONSECUTIVE_504:
            raise RuntimeError("HTTP 504 retry cap reached; do not record a fourth automatic attempt")
    existing.append(clean)
    payload = {"schema_version": ROUTE_JOURNAL_SCHEMA_VERSION, "events": existing}
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)
    return clean


def detect_runtime(explicit: str = "auto", environ: Mapping[str, str] | None = None) -> str:
    if explicit in {"codex", "external"}:
        return explicit
    env = environ if environ is not None else os.environ
    return "codex" if any(env.get(marker) for marker in CODEX_MARKERS) else "external"


def discover_route_candidates(
    runtime: str = "auto",
    environ: Mapping[str, str] | None = None,
    which: Any = shutil.which,
) -> list[dict[str, object]]:
    env = environ if environ is not None else os.environ
    resolved_runtime = detect_runtime(runtime, env)
    candidates: list[dict[str, object]] = []
    if resolved_runtime == "codex":
        candidates.append(
            {
                "route_kind": "system_imagegen",
                "provider": "codex",
                "tool": "image_gen",
                "model": None,
                "configured": True,
                "verified": False,
                "priority": 0,
                "detail": "Preferred Codex built-in image generation route; model is learned from a real receipt.",
            }
        )

    external_specs = (
        ("openai_cli", "openai", "openai", ("OPENAI_API_KEY", "AZURE_OPENAI_API_KEY")),
        ("replicate_cli", "replicate", "replicate", ("REPLICATE_API_TOKEN",)),
        ("fal_cli", "fal", "fal", ("FAL_KEY",)),
        ("gemini_cli", "gemini", "google", ("GEMINI_API_KEY", "GOOGLE_API_KEY")),
    )
    for route_kind, executable, provider, env_names in external_specs:
        command = which(executable)
        configured_names = [name for name in env_names if env.get(name)]
        if command or configured_names:
            candidates.append(
                {
                    "route_kind": route_kind,
                    "provider": provider,
                    "tool": executable,
                    "model": None,
                    "configured": True,
                    "verified": False,
                    "priority": 10 + len(candidates),
                    "command_path": command,
                    "credential_env_names": configured_names,
                    "detail": "Candidate only; a real smoke-test receipt and route journal are still required.",
                }
            )
    return candidates


def classify_failure(event: Mapping[str, object]) -> dict[str, object]:
    status_code = event.get("status_code") or event.get("http_status")
    try:
        status_code = int(status_code) if status_code is not None else None
    except (TypeError, ValueError):
        status_code = None
    error_code = str(event.get("error_code") or "").lower()
    message = str(event.get("error") or event.get("message") or "").lower()
    if status_code == 504 or "gateway timeout" in message or error_code in {"gateway_timeout", "http_504"}:
        return {
            "failure_class": "transport",
            "transition": "transport_retry",
            "model_provider_downgrade": False,
        }
    model_markers = ("model_not_found", "unsupported_model", "model_disabled", "capability_mismatch")
    provider_markers = ("provider_unavailable", "account_disabled", "billing_required", "quota_exhausted")
    if (
        error_code in model_markers
        or error_code in provider_markers
        or any(marker in message for marker in model_markers + provider_markers)
    ):
        return {
            "failure_class": "model_or_provider",
            "transition": "model_provider_fallback",
            "model_provider_downgrade": True,
        }
    return {
        "failure_class": "unknown",
        "transition": "stop_and_inspect",
        "model_provider_downgrade": False,
    }


def _is_504(event: Mapping[str, object]) -> bool:
    return classify_failure(event)["failure_class"] == "transport" and (
        str(event.get("status_code") or event.get("http_status") or "") == "504"
        or str(event.get("error_code") or "").lower() in {"gateway_timeout", "http_504"}
        or "gateway timeout" in str(event.get("error") or event.get("message") or "").lower()
    )


def evaluate_504_policy(events: Sequence[Mapping[str, object]], now: datetime | None = None) -> dict[str, object]:
    current = (now or utc_now()).astimezone(timezone.utc)
    consecutive: list[Mapping[str, object]] = []
    for event in reversed(events):
        event_name = str(event.get("event") or event.get("status") or "").lower()
        if event_name in SUCCESS_EVENTS:
            break
        if event_name in MODEL_PROVIDER_FALLBACK_EVENTS:
            break
        if event_name in TRANSPORT_SWITCH_EVENTS:
            continue
        if event_name in FAILURE_EVENTS or event.get("status_code") or event.get("http_status"):
            if not _is_504(event):
                break
            consecutive.append(event)
    consecutive.reverse()
    count = len(consecutive)
    if count == 0:
        return {
            "status": "ready_for_attempt",
            "consecutive_504": 0,
            "retry_allowed": True,
            "retry_after_seconds": 0,
        }

    first_at = parse_timestamp(consecutive[0].get("timestamp")) or current
    last_at = parse_timestamp(consecutive[-1].get("timestamp")) or first_at
    elapsed = max(0, int((current - first_at).total_seconds()))
    if count >= MAX_CONSECUTIVE_504:
        if elapsed >= BLOCK_AFTER_SECONDS:
            return {
                "status": "blocked_waiting_user",
                "consecutive_504": count,
                "retry_allowed": False,
                "retry_after_seconds": 0,
                "elapsed_seconds": elapsed,
                "reason": "Three consecutive HTTP 504 transport failures and about eight minutes without success.",
            }
        cooldown_until = last_at.timestamp() + RETRY_BACKOFF_SECONDS[-1]
        cooldown_remaining = max(0, int(cooldown_until - current.timestamp()))
        return {
            "status": "transport_cooldown",
            "consecutive_504": count,
            "retry_allowed": False,
            "retry_after_seconds": max(BLOCK_AFTER_SECONDS - elapsed, cooldown_remaining),
            "elapsed_seconds": elapsed,
            "reason": "Retry cap reached; do not downgrade the model/provider while waiting for the transport window.",
        }

    delay = RETRY_BACKOFF_SECONDS[count - 1]
    ready_at = last_at.timestamp() + delay
    retry_after = max(0, int(ready_at - current.timestamp()))
    return {
        "status": "transport_retry_scheduled" if retry_after else "ready_for_transport_retry",
        "consecutive_504": count,
        "retry_allowed": retry_after == 0,
        "retry_after_seconds": retry_after,
        "elapsed_seconds": elapsed,
        "reason": "HTTP 504 is a transport failure; retry or switch transport without changing model/provider.",
    }


def _resolve_recorded_path(value: object, base: Path) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (base / path).resolve()


def _receipt_asset_path(
    receipt: Mapping[str, object],
    receipt_path: Path,
    event: Mapping[str, object],
    journal_path: Path,
) -> Path | None:
    for key in ("local_asset_path", "raw_output_path", "output_path"):
        path = _resolve_recorded_path(receipt.get(key), receipt_path.parent)
        if path:
            return path
    for key in ("local_asset_path", "raw_output_path", "output_path"):
        path = _resolve_recorded_path(event.get(key), journal_path.parent)
        if path:
            return path
    return None


def validate_verified_routes(
    receipt_paths: Iterable[Path],
    journal_path: Path,
) -> tuple[list[VerifiedRoute], list[str], list[dict[str, object]]]:
    issues: list[str] = []
    if not journal_path.exists():
        return [], [f"Route journal not found: {journal_path}"], []
    try:
        events = load_route_journal(journal_path)
    except Exception as exc:
        return [], [f"Route journal is unreadable: {exc}"], []
    journal_secret_issues = secret_issues(events, "$.events")
    if journal_secret_issues:
        return [], journal_secret_issues, events
    success_events = [
        event for event in events
        if str(event.get("event") or event.get("status") or "").lower() in SUCCESS_EVENTS
    ]
    verified: list[VerifiedRoute] = []
    for receipt_path in receipt_paths:
        path = receipt_path.expanduser().resolve()
        if not path.exists():
            issues.append(f"Receipt not found: {path}")
            continue
        try:
            receipt = load_json(path)
        except Exception as exc:
            issues.append(f"Receipt is unreadable ({path}): {exc}")
            continue
        if not isinstance(receipt, dict):
            issues.append(f"Receipt must be a JSON object: {path}")
            continue
        receipt_secret_issues = secret_issues(receipt, "$.receipt")
        if receipt_secret_issues:
            issues.extend(receipt_secret_issues)
            continue
        required = ("provider", "model", "request_id", "prompt_sha256", "output_sha256")
        missing = [field for field in required if not receipt.get(field)]
        if receipt.get("schema_version") != RECEIPT_SCHEMA_VERSION:
            issues.append(f"Receipt schema_version must be {RECEIPT_SCHEMA_VERSION}: {path}")
            continue
        if missing:
            issues.append(f"Receipt is missing required fields {missing}: {path}")
            continue
        matches = []
        for event in success_events:
            event_receipt = _resolve_recorded_path(event.get("receipt_path"), journal_path.parent)
            same_receipt = event_receipt == path if event_receipt else False
            same_request = str(event.get("request_id") or "") == str(receipt.get("request_id"))
            same_provider = str(event.get("provider") or "") == str(receipt.get("provider"))
            same_model = str(event.get("model") or "") == str(receipt.get("model"))
            if same_receipt and same_request and same_provider and same_model:
                event_required = ("timestamp", "tool", "route_kind", "transport", "output_sha256")
                event_missing = [field for field in event_required if not event.get(field)]
                if event_missing:
                    issues.append(f"Matching route-journal success event is missing {event_missing}: {path}")
                    continue
                matches.append(event)
        if not matches:
            issues.append(f"No matching successful route-journal event for receipt: {path}")
            continue
        event = max(matches, key=lambda item: parse_timestamp(item.get("timestamp")) or datetime.min.replace(tzinfo=timezone.utc))
        asset_path = _receipt_asset_path(receipt, path, event, journal_path)
        if not asset_path or not asset_path.exists() or not asset_path.is_file():
            issues.append(f"Receipt does not bind to an existing local raster asset: {path}")
            continue
        if asset_path.suffix.lower() not in RASTER_SUFFIXES:
            issues.append(f"Verified image asset must be PNG/JPEG/WebP: {asset_path}")
            continue
        expected_hash = str(receipt.get("output_sha256") or "").lower()
        actual_hash = file_sha256(asset_path)
        if not re.fullmatch(r"[0-9a-f]{64}", expected_hash) or actual_hash != expected_hash:
            issues.append(f"Receipt output_sha256 does not match local asset: {asset_path}")
            continue
        event_hash = str(event.get("output_sha256") or "").lower()
        if event_hash != expected_hash:
            issues.append(f"Route journal output_sha256 does not match receipt: {path}")
            continue
        verified_at = parse_timestamp(event.get("timestamp"))
        if not verified_at:
            issues.append(f"Successful route-journal event has no valid timestamp: {path}")
            continue
        verified.append(
            VerifiedRoute(
                receipt_path=path,
                journal_path=journal_path.resolve(),
                provider=str(receipt["provider"]),
                tool=str(event.get("tool") or receipt.get("tool") or receipt["provider"]),
                model=str(receipt["model"]),
                request_id=str(receipt["request_id"]),
                route_kind=str(event.get("route_kind") or receipt.get("route_kind") or "external_api"),
                transport=str(event.get("transport") or receipt.get("transport") or "unknown"),
                local_asset_path=asset_path.resolve(),
                output_sha256=expected_hash,
                verified_at=verified_at,
            )
        )
    return verified, issues, events


def fallback_confirmation_time(route: VerifiedRoute, events: Sequence[Mapping[str, object]]) -> datetime | None:
    matches: list[datetime] = []
    for event in events:
        event_name = str(event.get("event") or event.get("status") or "").lower()
        if event_name not in MODEL_PROVIDER_FALLBACK_EVENTS or event.get("user_confirmed") is not True:
            continue
        from_kind = str(event.get("from_route_kind") or "")
        from_tool = str(event.get("from_tool") or "")
        if from_kind != "system_imagegen" and from_tool not in {"image_gen", "imagegen"}:
            continue
        to_kind = str(event.get("to_route_kind") or "")
        to_provider = str(event.get("to_provider") or "")
        to_model = str(event.get("to_model") or "")
        if to_kind and to_kind != route.route_kind:
            continue
        if to_provider and to_provider != route.provider:
            continue
        if to_model and to_model != route.model:
            continue
        timestamp = parse_timestamp(event.get("timestamp"))
        if timestamp and timestamp <= route.verified_at:
            matches.append(timestamp)
    return max(matches) if matches else None


def codex_builtin_failed(events: Sequence[Mapping[str, object]]) -> bool:
    relevant: list[tuple[datetime, Mapping[str, object]]] = []
    for event in events:
        route_kind = str(event.get("route_kind") or "")
        tool = str(event.get("tool") or "")
        provider = str(event.get("provider") or "")
        if route_kind != "system_imagegen" and tool not in {"image_gen", "imagegen"} and provider != "codex":
            continue
        timestamp = parse_timestamp(event.get("timestamp"))
        if timestamp:
            relevant.append((timestamp, event))
    if not relevant:
        return False
    _, latest = max(relevant, key=lambda item: item[0])
    event_name = str(latest.get("event") or latest.get("status") or "").lower()
    return event_name in FAILURE_EVENTS and not _is_504(latest)


def select_verified_route(
    routes: Sequence[VerifiedRoute],
    runtime: str,
    events: Sequence[Mapping[str, object]] = (),
) -> VerifiedRoute | None:
    if not routes:
        return None
    if runtime == "codex":
        built_in = [route for route in routes if route.route_kind == "system_imagegen"]
        confirmed_external = [
            route for route in routes
            if route.route_kind != "system_imagegen" and fallback_confirmation_time(route, events)
        ]
        if confirmed_external:
            latest_external = max(confirmed_external, key=lambda route: route.verified_at)
            latest_system = max(built_in, key=lambda route: route.verified_at) if built_in else None
            if latest_system is None or latest_external.verified_at > latest_system.verified_at:
                return latest_external
        if built_in:
            return max(built_in, key=lambda route: route.verified_at)
        return None
    return max(routes, key=lambda route: route.verified_at)


def resolve_image_route(
    receipt_paths: Iterable[Path],
    journal_path: Path | None,
    runtime: str = "auto",
    environ: Mapping[str, str] | None = None,
    now: datetime | None = None,
    which: Any = shutil.which,
) -> dict[str, object]:
    resolved_runtime = detect_runtime(runtime, environ)
    candidates = discover_route_candidates(resolved_runtime, environ, which)
    if journal_path is None:
        return {
            "status": "needs_real_smoke_test" if candidates else "needs_user_configuration",
            "block_reason": None,
            "runtime": resolved_runtime,
            "selected_route": None,
            "verified_routes": [],
            "candidates": candidates,
            "issues": ["A real route journal is required; self-confirmation is not accepted."],
            "retry_policy": evaluate_504_policy([], now),
        }
    verified, issues, events = validate_verified_routes(receipt_paths, journal_path)
    retry_policy = evaluate_504_policy(events, now)
    selected = select_verified_route(verified, resolved_runtime, events)
    builtin_failed = resolved_runtime == "codex" and codex_builtin_failed(events)
    if builtin_failed and selected and selected.route_kind == "system_imagegen":
        selected = None
    unconfirmed_external = (
        resolved_runtime == "codex"
        and any(route.route_kind != "system_imagegen" for route in verified)
        and not any(
            route.route_kind != "system_imagegen" and fallback_confirmation_time(route, events)
            for route in verified
        )
    )
    fallback_confirmation_required = resolved_runtime == "codex" and (
        unconfirmed_external or builtin_failed
    )
    retry_status = str(retry_policy["status"])
    if retry_status == "blocked_waiting_user":
        status_name = "blocked_waiting_user"
        block_reason = "transport_504_timeout"
    elif retry_status in {"transport_cooldown", "transport_retry_scheduled"}:
        status_name = retry_status
        block_reason = None
    elif fallback_confirmation_required and selected is None:
        status_name = "blocked_waiting_user"
        block_reason = "external_fallback_requires_user_confirmation"
    elif selected:
        status_name = "ready"
        block_reason = None
    elif candidates:
        status_name = "needs_real_smoke_test"
        block_reason = None
    else:
        status_name = "needs_user_configuration"
        block_reason = None
    return {
        "status": status_name,
        "block_reason": block_reason,
        "runtime": resolved_runtime,
        "selected_route": selected.as_dict() if selected else None,
        "verified_routes": [route.as_dict() for route in sorted(verified, key=lambda item: item.verified_at, reverse=True)],
        "candidates": candidates,
        "issues": issues,
        "retry_policy": retry_policy,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve a verified image-generation route from real receipts and a route journal.")
    parser.add_argument("--receipt", action="append", default=[], help="JSON receipt from a real image-generation call; repeatable")
    parser.add_argument("--route-journal", help="JSON or JSONL route journal containing the matching successful call")
    parser.add_argument("--runtime", choices=("auto", "codex", "external"), default="auto")
    args = parser.parse_args()

    report = resolve_image_route(
        [Path(value) for value in args.receipt],
        Path(args.route_journal).expanduser() if args.route_journal else None,
        runtime=args.runtime,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["status"] == "ready":
        return 0
    if report["status"] == "blocked_waiting_user":
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
