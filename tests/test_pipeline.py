"""Integration test for end-to-end LongImageOCRPipeline."""

import os
import shutil
import tempfile
import unittest
from PIL import Image, ImageDraw, ImageFont

from longocr.config import OCRConfig
from longocr.pipeline import LongImageOCRPipeline


class TestPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.test_dir, "output")

        # Create a synthetic tall image (width=800, height=4800)
        self.image_path = os.path.join(self.test_dir, "sample_tall.png")
        img = Image.new("RGB", (800, 4800), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", 24)
        except Exception:
            font = ImageFont.load_default()

        # Draw content
        for y in range(100, 4700, 300):
            draw.text((50, y), f"섹션 요약 #{y // 300} — 삼성전자 NVDA +12.5%", fill=(0, 0, 0), font=font)
            draw.text((50, y + 40), f"평가금액 1,234,{y % 900:03d}원 | 2026-10-10", fill=(50, 50, 50), font=font)

        img.save(self.image_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_end_to_end_pipeline(self):
        config = OCRConfig(
            mode="fast",
            tile_height=1800,
            overlap=150,
            enable_cache=True
        )
        pipeline = LongImageOCRPipeline(config=config)
        result = pipeline.process(self.image_path, output_dir=self.output_dir)

        # Check results
        self.assertGreater(result.total_tiles, 1)
        self.assertGreater(result.total_boxes, 5)
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "output.md")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "output.txt")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "ocr.json")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "manifest.json")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "audit.md")))

        # Verify manifest
        manifest = result.manifest
        self.assertEqual(manifest["width"], 800)
        self.assertEqual(manifest["height"], 4800)
        self.assertTrue(manifest["is_long_image"])
        self.assertGreater(len(manifest["tiles"]), 1)

        # Verify second run hits cache
        result2 = pipeline.process(self.image_path, output_dir=self.output_dir)
        self.assertEqual(result2.total_boxes, result.total_boxes)


if __name__ == "__main__":
    unittest.main()
