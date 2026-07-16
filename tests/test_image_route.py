from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import resolve_image_route as route


class ImageRouteTests(unittest.TestCase):
    def make_verified_route(
        self,
        root: Path,
        name: str,
        *,
        model: str,
        timestamp: datetime,
        route_kind: str = "external_api",
        provider: str = "example",
    ) -> tuple[Path, dict[str, object]]:
        asset = root / "assets" / f"{name}.png"
        receipt = root / "receipts" / f"{name}.json"
        asset.parent.mkdir(parents=True, exist_ok=True)
        receipt.parent.mkdir(parents=True, exist_ok=True)
        asset.write_bytes(f"real-raster-{name}".encode("utf-8"))
        output_hash = hashlib.sha256(asset.read_bytes()).hexdigest()
        request_id = f"req-{name}"
        receipt.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "provider": provider,
                    "tool": "image_gen" if route_kind == "system_imagegen" else "images-api",
                    "model": model,
                    "request_id": request_id,
                    "prompt_sha256": "1" * 64,
                    "output_sha256": output_hash,
                    "local_asset_path": str(asset),
                }
            ),
            encoding="utf-8",
        )
        event = {
            "event": "smoke_test_succeeded",
            "timestamp": timestamp.isoformat(),
            "provider": provider,
            "tool": "image_gen" if route_kind == "system_imagegen" else "images-api",
            "model": model,
            "request_id": request_id,
            "route_kind": route_kind,
            "transport": "built-in" if route_kind == "system_imagegen" else "https-api",
            "receipt_path": str(receipt),
            "output_sha256": output_hash,
        }
        return receipt, event

    def write_journal(self, path: Path, events: list[dict[str, object]]) -> None:
        path.write_text(json.dumps({"schema_version": 1, "events": events}), encoding="utf-8")

    def test_codex_discovers_system_imagegen_first_without_hardcoded_model(self) -> None:
        candidates = route.discover_route_candidates(
            "codex",
            environ={"CODEX_THREAD_ID": "thread"},
            which=lambda _name: None,
        )
        self.assertEqual(candidates[0]["route_kind"], "system_imagegen")
        self.assertEqual(candidates[0]["tool"], "image_gen")
        self.assertIsNone(candidates[0]["model"])

    def test_latest_verified_model_is_selected_dynamically(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            old_receipt, old_event = self.make_verified_route(
                root, "old", model="provider-model-2025", timestamp=datetime(2026, 7, 1, tzinfo=timezone.utc)
            )
            new_receipt, new_event = self.make_verified_route(
                root, "new", model="provider-model-2026", timestamp=datetime(2026, 7, 15, tzinfo=timezone.utc)
            )
            journal = root / "route-journal.json"
            self.write_journal(journal, [old_event, new_event])
            report = route.resolve_image_route(
                [old_receipt, new_receipt], journal, runtime="external", environ={}
            )
        self.assertEqual(report["status"], "ready")
        self.assertEqual(report["selected_route"]["model"], "provider-model-2026")

    def test_codex_prefers_latest_verified_system_route(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            system_receipt, system_event = self.make_verified_route(
                root,
                "system",
                model="runtime-selected-model",
                timestamp=datetime(2026, 7, 10, tzinfo=timezone.utc),
                route_kind="system_imagegen",
                provider="codex",
            )
            external_receipt, external_event = self.make_verified_route(
                root,
                "external",
                model="newer-external-model",
                timestamp=datetime(2026, 7, 15, tzinfo=timezone.utc),
            )
            journal = root / "route-journal.json"
            self.write_journal(journal, [system_event, external_event])
            report = route.resolve_image_route(
                [system_receipt, external_receipt],
                journal,
                runtime="codex",
                environ={"CODEX_THREAD_ID": "thread"},
            )
        self.assertEqual(report["selected_route"]["route_kind"], "system_imagegen")
        self.assertEqual(report["selected_route"]["model"], "runtime-selected-model")

    def test_codex_external_fallback_requires_explicit_user_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            verified_at = datetime(2026, 7, 15, tzinfo=timezone.utc)
            receipt, success = self.make_verified_route(
                root, "external-only", model="external-model", timestamp=verified_at
            )
            journal = root / "route-journal.json"
            self.write_journal(journal, [success])
            blocked = route.resolve_image_route(
                [receipt], journal, runtime="codex", environ={"CODEX_THREAD_ID": "thread"}
            )
            confirmation = {
                "event": "model_provider_fallback",
                "timestamp": (verified_at - timedelta(seconds=1)).isoformat(),
                "from_route_kind": "system_imagegen",
                "to_route_kind": "external_api",
                "to_provider": "example",
                "to_model": "external-model",
                "user_confirmed": True,
            }
            self.write_journal(journal, [confirmation, success])
            ready = route.resolve_image_route(
                [receipt], journal, runtime="codex", environ={"CODEX_THREAD_ID": "thread"}
            )
        self.assertEqual(blocked["status"], "blocked_waiting_user")
        self.assertEqual(blocked["block_reason"], "external_fallback_requires_user_confirmation")
        self.assertEqual(ready["status"], "ready")
        self.assertEqual(ready["selected_route"]["model"], "external-model")

    def test_codex_builtin_failure_waits_for_user_before_external_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            journal = Path(temp_dir) / "route-journal.json"
            self.write_journal(
                journal,
                [
                    {
                        "event": "failure",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "route_kind": "system_imagegen",
                        "provider": "codex",
                        "tool": "image_gen",
                        "error_code": "tool_unavailable",
                    }
                ],
            )
            report = route.resolve_image_route(
                [], journal, runtime="codex", environ={"CODEX_THREAD_ID": "thread"}
            )
        self.assertEqual(report["status"], "blocked_waiting_user")
        self.assertEqual(report["block_reason"], "external_fallback_requires_user_confirmation")

    def test_receipt_and_journal_must_bind_real_asset_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            receipt, event = self.make_verified_route(
                root, "tampered", model="model-a", timestamp=datetime.now(timezone.utc)
            )
            journal = root / "route-journal.json"
            self.write_journal(journal, [event])
            receipt_payload = json.loads(receipt.read_text(encoding="utf-8"))
            Path(receipt_payload["local_asset_path"]).write_bytes(b"tampered-after-receipt")
            report = route.resolve_image_route([receipt], journal, runtime="external", environ={})
        self.assertNotEqual(report["status"], "ready")
        self.assertTrue(any("output_sha256" in issue for issue in report["issues"]))

    def test_route_journal_never_records_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            journal = Path(temp_dir) / "route-journal.json"
            route.append_route_event(
                journal,
                {
                    "event": "failure",
                    "api_key": "sk-this-must-not-be-written",
                    "authorization": "Bearer top-secret-value",
                    "message": "request failed with sk-another-secret-value",
                },
            )
            text = journal.read_text(encoding="utf-8")
        self.assertNotIn("top-secret", text)
        self.assertNotIn("sk-this", text)
        self.assertNotIn("sk-another", text)
        self.assertIn("[REDACTED]", text)

    def test_existing_secret_material_invalidates_journal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            receipt, event = self.make_verified_route(
                root, "secret", model="model-a", timestamp=datetime.now(timezone.utc)
            )
            event["api_key"] = "sk-secret-material-123456"
            journal = root / "route-journal.json"
            self.write_journal(journal, [event])
            report = route.resolve_image_route([receipt], journal, runtime="external", environ={})
        self.assertNotEqual(report["status"], "ready")
        self.assertTrue(any("sensitive field" in issue for issue in report["issues"]))

    def test_transport_switch_is_not_model_provider_downgrade(self) -> None:
        transport = route.classify_failure({"status_code": 504, "message": "Gateway Timeout"})
        downgrade = route.classify_failure({"error_code": "unsupported_model"})
        self.assertEqual(transport["transition"], "transport_retry")
        self.assertFalse(transport["model_provider_downgrade"])
        self.assertEqual(downgrade["transition"], "model_provider_fallback")
        self.assertTrue(downgrade["model_provider_downgrade"])

    def test_three_consecutive_504s_block_after_about_eight_minutes(self) -> None:
        started = datetime(2026, 7, 16, 1, 0, tzinfo=timezone.utc)
        events = [
            {"event": "failure", "status_code": 504, "timestamp": started.isoformat()},
            {"event": "failure", "status_code": 504, "timestamp": (started + timedelta(seconds=20)).isoformat()},
            {"event": "failure", "status_code": 504, "timestamp": (started + timedelta(seconds=65)).isoformat()},
        ]
        cooldown = route.evaluate_504_policy(events, now=started + timedelta(seconds=300))
        blocked = route.evaluate_504_policy(events, now=started + timedelta(seconds=481))
        self.assertEqual(cooldown["status"], "transport_cooldown")
        self.assertFalse(cooldown["retry_allowed"])
        self.assertEqual(blocked["status"], "blocked_waiting_user")
        self.assertEqual(blocked["consecutive_504"], 3)

    def test_504_backoff_uses_twenty_forty_five_ninety_second_schedule(self) -> None:
        started = datetime(2026, 7, 16, 1, 0, tzinfo=timezone.utc)
        first = {"event": "failure", "status_code": 504, "timestamp": started.isoformat()}
        second_at = started + timedelta(seconds=20)
        second = {"event": "failure", "status_code": 504, "timestamp": second_at.isoformat()}
        third_at = second_at + timedelta(seconds=45)
        third = {"event": "failure", "status_code": 504, "timestamp": third_at.isoformat()}
        after_first = route.evaluate_504_policy([first], now=started)
        after_second = route.evaluate_504_policy([first, second], now=second_at)
        after_third = route.evaluate_504_policy([first, second, third], now=third_at)
        self.assertEqual(after_first["retry_after_seconds"], 20)
        self.assertEqual(after_second["retry_after_seconds"], 45)
        self.assertGreaterEqual(after_third["retry_after_seconds"], 90)
        self.assertFalse(after_third["retry_allowed"])

    def test_route_journal_refuses_a_fourth_automatic_504_attempt(self) -> None:
        started = datetime(2026, 7, 16, 1, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as temp_dir:
            journal = Path(temp_dir) / "route-journal.json"
            for offset in (0, 20, 65):
                route.append_route_event(
                    journal,
                    {
                        "event": "failure",
                        "status_code": 504,
                        "timestamp": (started + timedelta(seconds=offset)).isoformat(),
                    },
                )
            with self.assertRaisesRegex(RuntimeError, "fourth automatic attempt"):
                route.append_route_event(
                    journal,
                    {
                        "event": "failure",
                        "status_code": 504,
                        "timestamp": (started + timedelta(seconds=155)).isoformat(),
                    },
                )

    def test_transport_switch_keeps_504_count_but_model_fallback_resets_it(self) -> None:
        started = datetime(2026, 7, 16, 1, 0, tzinfo=timezone.utc)
        base = {"event": "failure", "status_code": 504, "timestamp": started.isoformat()}
        switched = route.evaluate_504_policy(
            [base, {"event": "transport_switch", "timestamp": (started + timedelta(seconds=30)).isoformat()}],
            now=started + timedelta(seconds=31),
        )
        downgraded = route.evaluate_504_policy(
            [base, {"event": "model_provider_fallback", "timestamp": (started + timedelta(seconds=30)).isoformat()}],
            now=started + timedelta(seconds=31),
        )
        self.assertEqual(switched["consecutive_504"], 1)
        self.assertEqual(downgraded["consecutive_504"], 0)

    def test_external_runtime_without_tool_or_api_requests_configuration(self) -> None:
        report = route.resolve_image_route([], None, runtime="external", environ={}, which=lambda _name: None)
        self.assertEqual(report["status"], "needs_user_configuration")

    def test_preflight_rejects_self_confirmation(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "preflight_learning_site.py"),
                "--mode",
                "image-series",
                "--confirm-image-direct-output",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
        )
        payload = json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(any("Self-confirmation" in blocker for blocker in payload["blockers"]))

    def test_preflight_accepts_only_real_receipt_and_journal_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            receipt, event = self.make_verified_route(
                root,
                "preflight",
                model="runtime-selected-model",
                timestamp=datetime.now(timezone.utc),
                route_kind="system_imagegen",
                provider="codex",
            )
            journal = root / "route-journal.json"
            self.write_journal(journal, [event])
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "preflight_learning_site.py"),
                    "--mode",
                    "image-series",
                    "--image-runtime",
                    "codex",
                    "--image-route-receipt",
                    str(receipt),
                    "--image-route-journal",
                    str(journal),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30,
            )
            payload = json.loads(result.stdout)
        self.assertEqual(payload["image_route"]["status"], "ready")
        self.assertEqual(payload["image_route"]["selected_route"]["model"], "runtime-selected-model")
        self.assertFalse(any("direct-output capability" in blocker for blocker in payload["blockers"]))


if __name__ == "__main__":
    unittest.main()
