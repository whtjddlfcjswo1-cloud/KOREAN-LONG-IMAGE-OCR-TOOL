"""Unit tests for merge and overlap deduplication."""

import unittest
from longocr.config import OCRConfig
from longocr.engines.base import OCRBox
from longocr.splitter import TileInfo
from longocr.merge import (
    map_to_global_coordinates,
    deduplicate_boxes,
    numbers_conflict,
    extract_numbers
)
from PIL import Image


class TestMerge(unittest.TestCase):

    def setUp(self):
        self.config = OCRConfig()

    def test_coordinate_mapping(self):
        dummy_img = Image.new("RGB", (100, 100))
        tile = TileInfo(
            tile_id=3,
            source_y_start=4000,
            source_y_end=6200,
            width=1080,
            height=2200,
            is_safe_cut=True,
            overlap_top=200,
            overlap_bottom=200,
            image=dummy_img
        )
        box = OCRBox(
            text="삼성전자",
            confidence=0.98,
            bbox_local=[[10, 20], [100, 20], [100, 50], [10, 50]],
            tile=3
        )
        mapped = map_to_global_coordinates([box], tile)
        self.assertEqual(mapped[0].bbox_global[0], [10.0, 4020.0])
        self.assertEqual(mapped[0].bbox_global[2], [100.0, 4050.0])
        self.assertEqual(mapped[0].y1, 4020.0)

    def test_strict_number_conflict(self):
        # Different numbers must trigger conflict
        self.assertTrue(numbers_conflict("평가금액 1,234,500", "평가금액 1,234,800"))
        self.assertTrue(numbers_conflict("+12.83%", "+12.84%"))
        # Same numbers must not conflict
        self.assertFalse(numbers_conflict("평가금액 1,234,500원", "평가금액 1,234,500"))
        self.assertFalse(numbers_conflict("삼성전자 78,200원", "삼성전자 78,200원"))

    def test_deduplication_keeps_winner_and_preserves_distinct_numbers(self):
        # Two identical text boxes in the overlap zone from Tile 1 and Tile 2
        box_t1 = OCRBox(
            text="SK하이닉스 192,500원",
            confidence=0.91,
            bbox_local=[[50, 1980], [300, 1980], [300, 2010], [50, 2010]],
            bbox_global=[[50, 1980], [300, 1980], [300, 2010], [50, 2010]],
            tile=1
        )
        box_t2 = OCRBox(
            text="SK하이닉스 192,500원",
            confidence=0.98,  # Higher confidence winner
            bbox_local=[[50, 30], [300, 30], [300, 60], [50, 60]],
            bbox_global=[[50, 1980], [300, 1980], [300, 2010], [50, 2010]],
            tile=2
        )

        # A third box with DIFFERENT number located at adjacent line
        box_t2_diff = OCRBox(
            text="평가금액 1,234,800원",
            confidence=0.95,
            bbox_local=[[50, 80], [300, 80], [300, 110], [50, 110]],
            bbox_global=[[50, 2030], [300, 2030], [300, 2060], [50, 2060]],
            tile=2
        )

        all_boxes = [box_t1, box_t2, box_t2_diff]
        deduped, audit = deduplicate_boxes(all_boxes, self.config)

        # Duplicate SK하이닉스 should be merged to 1 box
        self.assertEqual(len(deduped), 2)
        # Winner must have confidence 0.98
        sk_box = next(b for b in deduped if "SK하이닉스" in b.text)
        self.assertEqual(sk_box.confidence, 0.98)
        self.assertEqual(sk_box.tile, 2)
        # Distinct number line must still be present
        self.assertTrue(any("1,234,800" in b.text for b in deduped))


if __name__ == "__main__":
    unittest.main()
