"""Unit tests for cache and resume subsystem, verifying comprehensive hash invalidation."""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from longocr.config import OCRConfig
from longocr.cache import CacheManager
from longocr.engines.base import OCRBox


class TestCache(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.image_hash = "abc12345"
        self.config_hash = "cfg98765"

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_cache_save_and_load(self):
        mgr = CacheManager(self.test_dir, self.image_hash, self.config_hash)
        boxes = [OCRBox(text="삼성전자", confidence=0.99, bbox_local=[[10, 10], [100, 10], [100, 40], [10, 40]], tile=1)]
        self.assertFalse(mgr.is_tile_cached(1))
        mgr.save_tile_cache(1, boxes)
        self.assertTrue(mgr.is_tile_cached(1))
        loaded = mgr.load_tile_cache(1)
        self.assertIsNotNone(loaded)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].text, "삼성전자")
        self.assertEqual(loaded[0].confidence, 0.99)

    def test_cache_invalidation_on_config_change(self):
        mgr1 = CacheManager(self.test_dir, self.image_hash, self.config_hash)
        boxes = [OCRBox(text="Test", confidence=0.9, bbox_local=[[0, 0], [10, 0], [10, 10], [0, 10]], tile=1)]
        mgr1.save_tile_cache(1, boxes)
        self.assertTrue(mgr1.is_tile_cached(1))
        mgr2 = CacheManager(self.test_dir, self.image_hash, "new_config_hash")
        self.assertFalse(mgr2.is_tile_cached(1))

    def test_cache_hash_sensitivity_all_fields(self):
        base_cfg = OCRConfig()
        base_hash = base_cfg.compute_hash()
        self.assertNotEqual(base_hash, OCRConfig(retry_upscale_factor=2.0).compute_hash())
        self.assertNotEqual(base_hash, OCRConfig(engine_name="paddle").compute_hash())
        self.assertNotEqual(base_hash, OCRConfig(language="en").compute_hash())
        self.assertNotEqual(base_hash, OCRConfig(confidence_threshold=0.85).compute_hash())
        self.assertNotEqual(base_hash, OCRConfig(retry_padding=50).compute_hash())
        self.assertNotEqual(base_hash, OCRConfig(mode="fast").compute_hash())
        self.assertNotEqual(base_hash, OCRConfig(tile_height=1800).compute_hash())
        self.assertNotEqual(base_hash, OCRConfig(reading_order_mode="table").compute_hash())


if __name__ == "__main__":
    unittest.main()
