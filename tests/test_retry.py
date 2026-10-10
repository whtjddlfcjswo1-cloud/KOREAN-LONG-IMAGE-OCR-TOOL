"""Unit and regression tests for low-confidence retry and candidate validation."""

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from PIL import Image

from longocr.config import OCRConfig
from longocr.engines.base import OCRBox, BaseOCREngine
from longocr.retry import RetryManager, is_valid_retry_candidate
from longocr.preprocess import crop_with_padding, get_preprocessing_variants


class MockImprovingWithAdjacentLineEngine(BaseOCREngine):
    """Engine that returns both an improved target candidate and an unrelated high-confidence neighbor."""

    @property
    def name(self) -> str:
        return "mock_multi_candidate_engine"

    def recognize(self, image, tile_id=1):
        # Returns:
        # 1. Neighboring line (adjacent line with higher confidence 0.99, but vertically far)
        # 2. Genuinely improved target line (confidence 0.82, centered around expected padding)
        return [
            OCRBox(
                text="옆줄텍스트_광고",
                confidence=0.99,
                bbox_local=[[20, 120], [180, 120], [180, 150], [20, 150]],
                tile=tile_id
            ),
            OCRBox(
                text="원래텍스트_복원",
                confidence=0.82,
                bbox_local=[[20, 20], [180, 20], [180, 50], [20, 50]],
                tile=tile_id
            )
        ]


class MockNeighborOnlyEngine(BaseOCREngine):
    """Engine that only detects neighboring lines, but misses the target."""

    @property
    def name(self) -> str:
        return "mock_neighbor_only_engine"

    def recognize(self, image, tile_id=1):
        return [
            OCRBox(
                text="옆줄텍스트_광고",
                confidence=0.99,
                bbox_local=[[20, 120], [180, 120], [180, 150], [20, 150]],
                tile=tile_id
            )
        ]


class TestRetry(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config = OCRConfig(confidence_threshold=0.75, retry_padding=20)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_crop_with_padding(self):
        img = Image.new("RGB", (200, 200), color=(255, 255, 255))
        bbox = [50, 50, 100, 100]
        crop, (ox, oy) = crop_with_padding(img, bbox, padding=20)
        self.assertEqual(crop.size, (90, 90))
        self.assertEqual(ox, 30)
        self.assertEqual(oy, 30)

    def test_preprocessing_variants(self):
        img = Image.new("RGB", (100, 50), color=(200, 200, 200))
        variants = get_preprocessing_variants(img, upscale_factor=1.5)
        var_names = [name for name, _ in variants]
        self.assertIn("native", var_names)
        self.assertIn("upscaled", var_names)
        self.assertIn("contrast", var_names)
        self.assertIn("sharpened", var_names)

    def test_regression_adjacent_line_not_picked_despite_higher_confidence(self):
        """P0 Regression: Ensure adjacent lines (0.99 conf) are REJECTED in favor of target candidate (0.82 conf)."""
        engine = MockImprovingWithAdjacentLineEngine()
        manager = RetryManager(engine=engine, config=self.config, output_crops_dir=self.test_dir)

        dummy_tile = Image.new("RGB", (300, 300), color=(255, 255, 255))
        # Original target box at [50, 50] to [210, 80]
        low_box = OCRBox(
            text="원래텍스X",
            confidence=0.50,
            bbox_local=[[50, 50], [210, 50], [210, 80], [50, 80]],
            tile=1
        )

        results = manager.retry_low_confidence_boxes([low_box], dummy_tile, tile_id=1)
        self.assertEqual(len(results), 1)
        improved = results[0]

        # Must adopt the matching candidate '원래텍스트_복원', NOT '옆줄텍스트_광고'
        self.assertEqual(improved.text, "원래텍스트_복원")
        self.assertEqual(improved.confidence, 0.82)
        self.assertTrue(improved.retry)

    def test_regression_neighbor_only_keeps_original_text(self):
        """P0 Regression: If only adjacent text appears in crop, retain original rather than corrupting."""
        engine = MockNeighborOnlyEngine()
        manager = RetryManager(engine=engine, config=self.config, output_crops_dir=self.test_dir)

        dummy_tile = Image.new("RGB", (300, 300), color=(255, 255, 255))
        low_box = OCRBox(
            text="원래텍스X",
            confidence=0.50,
            bbox_local=[[50, 50], [210, 50], [210, 80], [50, 80]],
            tile=1
        )

        results = manager.retry_low_confidence_boxes([low_box], dummy_tile, tile_id=1)
        self.assertEqual(len(results), 1)
        unchanged = results[0]

        # Original text and confidence must be preserved
        self.assertEqual(unchanged.text, "원래텍스X")
        self.assertEqual(unchanged.confidence, 0.50)
        self.assertFalse(unchanged.retry)


if __name__ == "__main__":
    unittest.main()
