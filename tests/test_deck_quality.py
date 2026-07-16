from __future__ import annotations

import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    Image = None
    ImageDraw = None


ROOT = Path(__file__).resolve().parents[1]


def load_audit():
    path = ROOT / "scripts" / "audit_learning_deck.py"
    spec = importlib.util.spec_from_file_location("audit_learning_deck_quality", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


AUDIT = load_audit()


def rendered_result(index: int, family: int, visual: bool = True, source_ratio: float = 0.10) -> dict:
    return {
        "index": index,
        "layoutTokens": [
            f"heading:{family}:0:2:1",
            f"group:{family}:1:2:2",
            f"visual:{family}:2:2:2",
        ],
        "layoutObjectCount": 4,
        "validVisualObjectCount": 1 if visual else 0,
        "sourceScreenshotObjectCount": 1 if source_ratio > 0.15 else 0,
        "validVisualAreaRatio": 0.28 if visual else 0.0,
        "sourceScreenshotAreaRatio": source_ratio,
        "contentAreaRatio": 0.58,
        "lowerHalfContentRatio": 0.30,
        "pixelMetrics": {"foreground_ratio": 0.42, "lower_half_foreground_ratio": 0.28},
    }


def slide_items(count: int, reasoning_role: str = "mechanism") -> list[dict]:
    return [
        {"id": f"slide-{index}", "type": "content", "reasoning_role": reasoning_role, "sequence_role": "mechanism"}
        for index in range(1, count + 1)
    ]


def write_minimal_pptx(path: Path, editable_text: bool) -> None:
    presentation = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:sldSz cx="12192000" cy="6858000"/>
</p:presentation>"""
    if editable_text:
        shapes = """
      <p:sp>
        <p:nvSpPr><p:cNvPr id="2" name="Title"/><p:cNvSpPr/><p:nvPr><p:ph type="ctrTitle"/></p:nvPr></p:nvSpPr>
        <p:spPr><a:xfrm><a:off x="900000" y="700000"/><a:ext cx="10300000" cy="1100000"/></a:xfrm></p:spPr>
        <p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:rPr sz="3600"/><a:t>Editable title</a:t></a:r></a:p></p:txBody>
      </p:sp>
      <p:sp>
        <p:nvSpPr><p:cNvPr id="3" name="Subtitle"/><p:cNvSpPr/><p:nvPr><p:ph type="subTitle"/></p:nvPr></p:nvSpPr>
        <p:spPr><a:xfrm><a:off x="1200000" y="2500000"/><a:ext cx="9500000" cy="1200000"/></a:xfrm></p:spPr>
        <p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:rPr sz="2000"/><a:t>Editable body copy</a:t></a:r></a:p></p:txBody>
      </p:sp>"""
    else:
        shapes = """
      <p:pic>
        <p:nvPicPr><p:cNvPr id="2" name="Flattened slide"/><p:cNvPicPr/><p:nvPr/></p:nvPicPr>
        <p:blipFill><a:blip r:embed="rId1"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>
        <p:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="12192000" cy="6858000"/></a:xfrm></p:spPr>
      </p:pic>"""
    slide = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <p:cSld><p:spTree>
    <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
    <p:grpSpPr/>{shapes}
  </p:spTree></p:cSld>
</p:sld>"""
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr("ppt/presentation.xml", presentation)
        archive.writestr("ppt/slides/slide1.xml", slide)
        archive.writestr("ppt/media/filler.bin", b"x" * 2048)


def write_geometry_pptx(
    path: Path,
    families: list[int],
    source_dominant: bool = False,
    oversized: bool = False,
    blank_lower: bool = False,
) -> None:
    presentation = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:sldSz cx="12192000" cy="6858000"/>
</p:presentation>"""
    positions = (
        (600000, 3600000, 4800000, 2300000),
        (6600000, 3600000, 4800000, 2300000),
        (1800000, 3000000, 8500000, 2800000),
        (600000, 2100000, 4700000, 3600000),
        (6600000, 2100000, 4700000, 3600000),
        (2600000, 3900000, 7000000, 2100000),
    )
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr("ppt/presentation.xml", presentation)
        archive.writestr("ppt/media/source-crop.png", b"source-screenshot-bytes" * 64)
        archive.writestr("ppt/media/filler.bin", b"x" * 2048)
        for index, family in enumerate(families, 1):
            x, y, width, height = positions[family % len(positions)]
            if blank_lower:
                x, y, width, height = 1800000, 2200000, 8500000, 800000
            large_box = """
      <p:sp>
        <p:nvSpPr><p:cNvPr id="4" name="Oversized"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
        <p:spPr><a:xfrm><a:off x="500000" y="1900000"/><a:ext cx="11100000" cy="3000000"/></a:xfrm></p:spPr>
        <p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:rPr sz="1800"/><a:t>One short line</a:t></a:r></a:p></p:txBody>
      </p:sp>""" if oversized and index == 1 else ""
            if source_dominant and index == 1:
                visual = """
      <p:pic>
        <p:nvPicPr><p:cNvPr id="5" name="Source evidence screenshot" descr="source crop"/><p:cNvPicPr/><p:nvPr/></p:nvPicPr>
        <p:blipFill><a:blip r:embed="rId1"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>
        <p:spPr><a:xfrm><a:off x="1200000" y="1800000"/><a:ext cx="9800000" cy="3800000"/></a:xfrm></p:spPr>
      </p:pic>"""
            else:
                visual = f"""
      <p:graphicFrame>
        <p:nvGraphicFramePr><p:cNvPr id="5" name="Diagram"/><p:cNvGraphicFramePr/><p:nvPr/></p:nvGraphicFramePr>
        <p:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{width}" cy="{height}"/></p:xfrm>
        <a:graphic><a:graphicData uri="urn:test"/></a:graphic>
      </p:graphicFrame>"""
            slide = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <p:cSld><p:spTree>
    <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/>
    <p:sp>
      <p:nvSpPr><p:cNvPr id="2" name="Title"/><p:cNvSpPr/><p:nvPr><p:ph type="ctrTitle"/></p:nvPr></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="700000" y="500000"/><a:ext cx="10800000" cy="900000"/></a:xfrm></p:spPr>
      <p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:rPr sz="3400"/><a:t>Editable title {index}</a:t></a:r></a:p></p:txBody>
    </p:sp>
    <p:sp>
      <p:nvSpPr><p:cNvPr id="3" name="Body"/><p:cNvSpPr/><p:nvPr><p:ph type="body"/></p:nvPr></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="800000" y="1450000"/><a:ext cx="10500000" cy="700000"/></a:xfrm></p:spPr>
      <p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:rPr sz="1800"/><a:t>Editable body explanation</a:t></a:r></a:p></p:txBody>
    </p:sp>{large_box}{visual}
  </p:spTree></p:cSld>
</p:sld>"""
            archive.writestr(f"ppt/slides/slide{index}.xml", slide)
            if source_dominant and index == 1:
                archive.writestr(
                    f"ppt/slides/_rels/slide{index}.xml.rels",
                    """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/source-crop.png"/>
</Relationships>""",
                )


class DeckQualityTests(unittest.TestCase):
    def test_browser_probe_reports_real_geometry(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            html = root / "index.html"
            html.write_text(
                """<!doctype html><html><body style="margin:0">
<section class="slide" data-slide style="position:relative;width:1920px;height:1080px;background:#fff">
  <h2 style="position:absolute;left:120px;top:70px;width:1500px;height:90px;font-size:48px">Question and conclusion</h2>
  <div data-information-group style="position:absolute;left:120px;top:220px;width:520px;height:280px"><p style="font-size:28px">Reasoning block</p></div>
  <div data-information-group style="position:absolute;left:700px;top:220px;width:520px;height:280px"><p style="font-size:28px">Evidence block</p></div>
  <div data-information-group style="position:absolute;left:1280px;top:220px;width:520px;height:280px"><p style="font-size:28px">Implication block</p></div>
  <svg data-teaching-object="diagram" style="position:absolute;left:240px;top:590px;width:1440px;height:360px" viewBox="0 0 100 30">
    <rect x="2" y="4" width="25" height="20"/><line x1="27" y1="14" x2="70" y2="14"/><circle cx="82" cy="14" r="10"/>
  </svg>
</section></body></html>""",
                encoding="utf-8",
            )
            probe, error = AUDIT.browser_probe(html, root / "shots", {})
        if error and "unavailable" in error.lower():
            self.skipTest(error)
        self.assertIsNone(error)
        self.assertEqual(probe["slideCount"], 1)
        result = probe["results"][0]
        self.assertGreaterEqual(result["validVisualObjectCount"], 1)
        self.assertGreater(result["contentAreaRatio"], 0.38)
        self.assertGreater(result["lowerHalfContentRatio"], 0.10)
        self.assertTrue(result["layoutTokens"])

    def test_twenty_page_deck_requires_six_rendered_layouts(self) -> None:
        bad = [rendered_result(index, (index - 1) % 5) for index in range(1, 21)]
        issues = AUDIT.audit_rendered_design(bad, slide_items(20))
        self.assertTrue(any("requires at least 6" in issue for issue in issues))

        good = [rendered_result(index, (index - 1) % 6) for index in range(1, 21)]
        self.assertEqual(AUDIT.audit_rendered_design(good, slide_items(20)), [])

    def test_similar_structure_cannot_repeat_three_times(self) -> None:
        results = [rendered_result(index, family) for index, family in enumerate((0, 0, 0, 1, 2, 3), 1)]
        issues = AUDIT.audit_rendered_design(results, slide_items(6))
        self.assertTrue(any("more than two consecutive" in issue for issue in issues))

    def test_effective_visual_coverage_must_reach_seventy_percent(self) -> None:
        bad = [rendered_result(index, (index - 1) % 6, visual=index <= 13) for index in range(1, 21)]
        issues = AUDIT.audit_rendered_design(bad, slide_items(20))
        self.assertTrue(any("below 70%" in issue for issue in issues))

        good = [rendered_result(index, (index - 1) % 6, visual=index <= 14) for index in range(1, 21)]
        self.assertEqual(AUDIT.audit_rendered_design(good, slide_items(20)), [])

    def test_ordinary_page_rejects_source_screenshot_over_forty_percent(self) -> None:
        result = rendered_result(1, 0, source_ratio=0.41)
        issues = AUDIT.audit_rendered_design([result], slide_items(1))
        self.assertTrue(any("at or below 0.40" in issue for issue in issues))

        evidence_slide = slide_items(1, reasoning_role="evidence")
        self.assertEqual(AUDIT.audit_rendered_design([result], evidence_slide), [])

    def test_deck_rejects_source_screenshot_dominance(self) -> None:
        results = [rendered_result(index, index - 1, source_ratio=0.20 if index <= 4 else 0.0) for index in range(1, 6)]
        issues = AUDIT.audit_rendered_design(results, slide_items(5))
        self.assertTrue(any("source-screenshot dominated" in issue for issue in issues))

    def test_lower_half_blank_is_a_failure(self) -> None:
        result = rendered_result(1, 0)
        result["lowerHalfContentRatio"] = 0.04
        result["pixelMetrics"]["lower_half_foreground_ratio"] = 0.03
        issues = AUDIT.audit_rendered_design([result], slide_items(1))
        self.assertTrue(any("lower half substantially blank" in issue for issue in issues))

    @unittest.skipUnless(Image is not None and ImageDraw is not None, "Pillow is required for pixel occupancy regression")
    def test_pixel_probe_detects_blank_lower_half(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "slide.png"
            image = Image.new("RGB", (320, 180), "white")
            ImageDraw.Draw(image).rectangle((40, 20, 280, 72), fill="black")
            image.save(path)
            metrics = AUDIT.pixel_content_metrics(path)
        self.assertIsNotNone(metrics)
        self.assertLess(metrics["lower_half_foreground_ratio"], 0.01)
        self.assertGreater(metrics["foreground_ratio"], 0.10)

    @unittest.skipUnless(Image is not None and ImageDraw is not None, "Pillow is required for border-palette regression")
    def test_pixel_probe_ignores_a_colored_side_rail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "slide.png"
            image = Image.new("RGB", (320, 180), "white")
            draw = ImageDraw.Draw(image)
            draw.rectangle((0, 0, 42, 179), fill=(20, 80, 180))
            draw.rectangle((70, 20, 280, 70), fill="black")
            image.save(path)
            metrics = AUDIT.pixel_content_metrics(path)
        self.assertIsNotNone(metrics)
        self.assertLess(metrics["lower_half_foreground_ratio"], 0.01)

    def test_pptx_ooxml_geometry_enforces_six_real_layouts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            five = root / "five-layouts.pptx"
            six = root / "six-layouts.pptx"
            write_geometry_pptx(five, [(index - 1) % 5 for index in range(1, 21)])
            write_geometry_pptx(six, [(index - 1) % 6 for index in range(1, 21)])
            five_results, five_geometry_issues = AUDIT.inspect_pptx_geometry(five)
            six_results, six_geometry_issues = AUDIT.inspect_pptx_geometry(six)
        self.assertEqual(five_geometry_issues, [])
        self.assertEqual(six_geometry_issues, [])
        five_issues = AUDIT.audit_rendered_design(five_results, slide_items(20), origin="PPTX OOXML")
        six_issues = AUDIT.audit_rendered_design(six_results, slide_items(20), origin="PPTX OOXML")
        self.assertTrue(any("requires at least 6" in issue for issue in five_issues))
        self.assertFalse(any("requires at least 6" in issue for issue in six_issues))

    def test_pptx_ooxml_catches_oversized_box_and_source_dominance(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad-geometry.pptx"
            write_geometry_pptx(path, [0], source_dominant=True, oversized=True)
            results, geometry_issues = AUDIT.inspect_pptx_geometry(path)
        self.assertTrue(any("oversized one-line" in issue for issue in geometry_issues))
        rendered_issues = AUDIT.audit_rendered_design(results, slide_items(1), origin="PPTX OOXML")
        self.assertTrue(any("source screenshots occupy" in issue for issue in rendered_issues))

    def test_pptx_ooxml_catches_blank_lower_half(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "blank-lower.pptx"
            write_geometry_pptx(path, [0], blank_lower=True)
            results, geometry_issues = AUDIT.inspect_pptx_geometry(path)
        self.assertEqual(geometry_issues, [])
        rendered_issues = AUDIT.audit_rendered_design(results, slide_items(1), origin="PPTX OOXML")
        self.assertTrue(any("lower half substantially blank" in issue for issue in rendered_issues))

    def test_pptx_first_slide_requires_editable_title_and_body(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            flattened = root / "flattened.pptx"
            editable = root / "editable.pptx"
            write_minimal_pptx(flattened, editable_text=False)
            write_minimal_pptx(editable, editable_text=True)

            flattened_issues = AUDIT.validate_pptx_editability(flattened, 1)
            self.assertTrue(any("editable title" in issue for issue in flattened_issues))
            self.assertTrue(any("editable body" in issue for issue in flattened_issues))
            self.assertEqual(AUDIT.validate_pptx_editability(editable, 1), [])

    def test_character_count_is_not_a_completeness_gate(self) -> None:
        source = (ROOT / "scripts" / "audit_learning_deck.py").read_text(encoding="utf-8")
        self.assertNotIn("minimum_chars", source)
        self.assertNotIn("expected about {minimum_chars}", source)


if __name__ == "__main__":
    unittest.main()
