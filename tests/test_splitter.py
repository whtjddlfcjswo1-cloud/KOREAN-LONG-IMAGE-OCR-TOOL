"""Unit tests for Smart Tiling and Long Image Splitting."""

import unittest
from PIL import Image, ImageDraw
import numpy as np

from longocr.config import OCRConfig
from longocr.splitter import is_long_image, split_image, find_safe_cut_y, compute_horizontal_content_density


class TestSplitter(unittest.TestCase):

    def setUp(self):
        self.config = OCRConfig(
            min_height=4000,
            min_aspect_ratio=3.0,
            tile_height=2000,
            tile_search_range=200,
            overlap=150
        )

    def test_is_long_image_detection(self):
        self.assertFalse(is_long_image(1000, 1000, self.config))
        self.assertFalse(is_long_image(1920, 1080, self.config))
        self.assertTrue(is_long_image(1080, 5000, self.config))
        self.assertTrue(is_long_image(800, 2800, self.config))

    def test_safe_cut_detection(self):
        width, height = 800, 6000
        img = Image.new("RGB", (width, height), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        for y in range(0, 1800, 40):
            draw.line([(50, y), (750, y)], fill=(0, 0, 0), width=4)
        for y in range(2200, 5800, 40):
            draw.line([(50, y), (750, y)], fill=(0, 0, 0), width=4)
        tiles = split_image(img, self.config)
        self.assertGreater(len(tiles), 1)
        tile1 = tiles[0]
        self.assertTrue(tile1.is_safe_cut)
        self.assertTrue(1800 <= tile1.source_y_end <= 2300)

    def test_single_tile_for_short_image(self):
        img = Image.new("RGB", (800, 1200), color=(240, 240, 240))
        tiles = split_image(img, self.config)
        self.assertEqual(len(tiles), 1)
        self.assertEqual(tiles[0].source_y_start, 0)
        self.assertEqual(tiles[0].source_y_end, 1200)


if __name__ == "__main__":
    unittest.main()
