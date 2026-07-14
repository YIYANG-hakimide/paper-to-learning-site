from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    Image = None
    ImageDraw = None


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class AuditContractTests(unittest.TestCase):
    def test_image_series_rejects_post_composed_pages(self) -> None:
        audit = load_module("audit_visual_series_native", ROOT / "scripts" / "audit_visual_series.py")
        item = {
            "production_method": "generated-composite",
            "text_integration": {"mode": "reserved-zone-overlay", "planned_before_generation": True},
            "generation_provenance": {
                "provider": "example",
                "model": "example-image-model",
                "request_id": "req-bad",
                "prompt_sha256": "abc",
                "run_receipt_path": "qa/run.json",
                "run_receipt_sha256": "def",
                "provider_response_path": "raw/provider-responses/bad.json",
                "provider_response_sha256": "bad",
                "raw_output_path": "raw/page.png",
                "raw_output_sha256": "ghi",
                "final_asset_is_direct_output": False,
                "pixel_postprocess_operations": ["text-overlay"],
            },
        }
        issues = audit.validate_native_generation_contract(item)
        self.assertTrue(any("model-single-pass" in issue for issue in issues))
        self.assertTrue(any("in-model" in issue for issue in issues))
        self.assertTrue(any("pixel_postprocess_operations" in issue for issue in issues))

    def test_image_series_accepts_declared_native_generation_contract(self) -> None:
        audit = load_module("audit_visual_series_valid_native", ROOT / "scripts" / "audit_visual_series.py")
        item = {
            "production_method": "model-single-pass",
            "text_integration": {"mode": "in-model", "planned_before_generation": True},
            "generation_provenance": {
                "provider": "example",
                "model": "example-image-model",
                "request_id": "req-good",
                "prompt_sha256": "abc",
                "run_receipt_path": "qa/run.json",
                "run_receipt_sha256": "def",
                "provider_response_path": "raw/provider-responses/good.json",
                "provider_response_sha256": "good",
                "raw_output_path": "raw/page.png",
                "raw_output_sha256": "ghi",
                "final_asset_is_direct_output": True,
                "pixel_postprocess_operations": [],
            },
        }
        self.assertEqual(audit.validate_native_generation_contract(item), [])

    def test_image_series_receipt_binds_raw_output_to_final_asset(self) -> None:
        audit = load_module("audit_visual_series_receipt", ROOT / "scripts" / "audit_visual_series.py")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            raw = root / "raw" / "model-outputs" / "001.png"
            receipt = root / "raw" / "receipts" / "001.json"
            response = root / "raw" / "provider-responses" / "001.json"
            final = root / "assets" / "images" / "001-page.png"
            raw.parent.mkdir(parents=True)
            receipt.parent.mkdir(parents=True)
            response.parent.mkdir(parents=True)
            final.parent.mkdir(parents=True)
            raw.write_bytes(b"real-model-output")
            final.write_bytes(raw.read_bytes())
            output_hash = audit.file_hash(raw)
            prompt_hash = "1" * 64
            receipt.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "provider": "example",
                        "model": "example-image-model",
                        "request_id": "req-001",
                        "prompt_sha256": prompt_hash,
                        "output_sha256": output_hash,
                    }
                ),
                encoding="utf-8",
            )
            response.write_text(
                json.dumps(
                    {
                        "provider": "example",
                        "model": "example-image-model",
                        "request_id": "req-001",
                        "output_sha256": output_hash,
                    }
                ),
                encoding="utf-8",
            )
            item = {
                "model_name": "example-image-model",
                "production_method": "model-single-pass",
                "text_integration": {"mode": "in-model", "planned_before_generation": True},
                "generation_provenance": {
                    "provider": "example",
                    "model": "example-image-model",
                    "request_id": "req-001",
                    "prompt_sha256": prompt_hash,
                    "run_receipt_path": "raw/receipts/001.json",
                    "run_receipt_sha256": audit.file_hash(receipt),
                    "provider_response_path": "raw/provider-responses/001.json",
                    "provider_response_sha256": audit.file_hash(response),
                    "raw_output_path": "raw/model-outputs/001.png",
                    "raw_output_sha256": output_hash,
                    "final_asset_is_direct_output": True,
                    "pixel_postprocess_operations": [],
                },
            }
            self.assertEqual(audit.validate_native_generation_contract(item, final, root), [])
            final.write_bytes(b"post-composed-page")
            issues = audit.validate_native_generation_contract(item, final, root)
            self.assertTrue(any("byte-match" in issue for issue in issues))

    def test_public_copy_checks_ai_template_residue(self) -> None:
        visual_audit = load_module("audit_visual_series_copy", ROOT / "scripts" / "audit_visual_series.py")
        deck_audit = load_module("audit_learning_deck_copy", ROOT / "scripts" / "audit_learning_deck.py")
        cases = (
            "这里需要让用户理解拒绝采样。",
            "它不是分类器，而是规划器。它不是搜索，而是生成。",
            "值得注意的是，这将改变结果。",
            "这项技术将赋能研究。",
        )
        for text in cases:
            with self.subTest(text=text):
                self.assertTrue(visual_audit.public_copy_issues(text))
                self.assertTrue(deck_audit.public_copy_issues(text))
        natural = "这里比较的不是参数数量，而是同一预算下的准确率。"
        self.assertEqual(visual_audit.public_copy_issues(natural), [])
        self.assertEqual(deck_audit.public_copy_issues(natural), [])

    def test_chinese_ratio_allows_short_english_term_aliases(self) -> None:
        audit = load_module("audit_visual_series_language", ROOT / "scripts" / "audit_visual_series.py")
        text = "监督微调：模型先看示范，再学习怎样回答。Supervised Fine-Tuning (SFT) 是这个术语的英文名称。"
        self.assertGreater(audit.chinese_ratio(text), 0.45)

    def test_strict_html_audit_cannot_skip_browser_probes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            (temp / "index.html").write_text("<!doctype html><html><body><main>原文 说人话</main></body></html>", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "audit_learning_site.py"),
                    str(temp),
                    "--strict",
                    "--skip-browser",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--strict cannot skip browser probes", result.stdout)

    def test_image_preflight_requires_direct_output_confirmation(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "preflight_learning_site.py"), "--mode", "image-series"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
        )
        payload = json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(any("direct-output capability" in blocker for blocker in payload["blockers"]))

    def test_visual_audit_reports_null_argument_lists_without_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "data").mkdir()
            (root / "data" / "learning-series-manifest.json").write_text(
                json.dumps(
                    {
                        "manifest_schema_version": "0.5",
                        "output_mode": "image-series",
                        "reader_language": "zh",
                        "size_mode": "concise",
                        "items_expected": 0,
                        "items_rendered": 0,
                        "items": [],
                        "storyboard": {"locked_before_final_generation": True},
                    }
                ),
                encoding="utf-8",
            )
            (root / "data" / "storyboard.json").write_text(
                json.dumps(
                    {
                        "items": [],
                        "acts": [],
                        "paper_argument_map": {
                            "main_question": "q",
                            "thesis": "t",
                            "argument_steps": None,
                            "evidence_route": None,
                            "conclusion": "c",
                        },
                    }
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "audit_visual_series.py"), str(root)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30,
            )
        self.assertNotIn("Traceback", result.stderr)
        payload = json.loads(result.stdout)
        self.assertGreater(payload["summary"]["warnings"], 0)

    def test_strict_visual_audit_requires_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "audit_visual_series.py"), temp_dir, "--strict"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30,
            )
        payload = json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(any("requires --source" in issue for issue in payload["errors"]))

    @unittest.skipUnless(Image is not None and ImageDraw is not None, "Pillow is required for PDF image-order verification")
    def test_album_pdf_order_is_verified_against_numbered_images(self) -> None:
        audit = load_module("audit_visual_series", ROOT / "scripts" / "audit_visual_series.py")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            image_dir = temp / "images"
            image_dir.mkdir()
            paths = []
            for index, color in enumerate(((190, 40, 40), (30, 100, 190)), 1):
                path = image_dir / f"{index:03d}-page.png"
                image = Image.new("RGB", (900, 1200), color)
                ImageDraw.Draw(image).text((80, 80), f"PAGE {index}", fill="white")
                image.save(path)
                paths.append(path)
            pdf_path = temp / "album.pdf"
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "build_image_album_pdf.py"),
                    str(image_dir),
                    str(pdf_path),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=60,
            )
            self.assertEqual(audit.validate_album_pdf(pdf_path, 2, "3:4", paths, temp / "correct"), [])
            reversed_issues = audit.validate_album_pdf(pdf_path, 2, "3:4", list(reversed(paths)), temp / "reversed")
            self.assertTrue(any("does not visually match" in issue for issue in reversed_issues))


if __name__ == "__main__":
    unittest.main()
