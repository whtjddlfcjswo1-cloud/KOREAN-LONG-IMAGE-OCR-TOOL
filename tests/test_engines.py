"""Unit tests and mock fixtures for PaddleOCR 3.x and 2.x engine paths.

Note: Mock tests verify API protocol compatibility and result parsing contracts (attribute,
mapping, and JSON structures) without claiming physical hardware verification of PaddlePaddle.
"""

import unittest
from unittest.mock import MagicMock
from collections.abc import Mapping
import numpy as np

from longocr.config import OCRConfig
from longocr.engines.paddle import PaddleOCREngine
from longocr.engines.rapid import RapidOCREngine, RapidEngine


class MockPaddle3xAttributeResult:
    """Mock fixture for attribute-style PaddleOCR 3.x result."""
    def __init__(self, texts, scores, polys):
        self.rec_texts = texts
        self.rec_scores = scores
        self.rec_polys = polys


class MockPaddle3xMappingResult(Mapping):
    """Mock fixture for custom mapping-like (non-dict) PaddleOCR 3.x result."""
    def __init__(self, data):
        self._data = data

    def __getitem__(self, key):
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def get(self, key, default=None):
        return self._data.get(key, default)


class MockPaddle3xJsonResult:
    """Mock fixture for nested JSON-style result with [xmin, ymin, xmax, ymax] boxes."""
    def __init__(self, res_dict):
        self.json = {"res": res_dict}


class TestEngineCompatibility(unittest.TestCase):

    def test_paddleocr_3x_predict_attribute_api(self):
        """Verifies that PaddleOCR 3.x predict API with attribute access is correctly parsed."""
        engine = PaddleOCREngine(OCRConfig(mode="accurate"))

        mock_3x = MagicMock()
        mock_3x.predict.return_value = [
            MockPaddle3xAttributeResult(
                texts=["삼성전자", "NVDA"],
                scores=[0.985, 0.991],
                polys=[
                    [[10, 20], [100, 20], [100, 50], [10, 50]],
                    [[110, 20], [180, 20], [180, 50], [110, 50]]
                ]
            )
        ]
        engine._engine = mock_3x
        engine._is_paddle = True

        dummy_img = np.zeros((100, 200, 3), dtype=np.uint8)
        boxes = engine.recognize(dummy_img, tile_id=1)

        self.assertEqual(len(boxes), 2)
        self.assertEqual(boxes[0].text, "삼성전자")
        self.assertAlmostEqual(boxes[0].confidence, 0.985, places=3)
        self.assertEqual(boxes[0].bbox_local, [[10.0, 20.0], [100.0, 20.0], [100.0, 50.0], [10.0, 50.0]])

        self.assertEqual(boxes[1].text, "NVDA")
        self.assertAlmostEqual(boxes[1].confidence, 0.991, places=3)

    def test_paddleocr_3x_predict_mapping_api(self):
        """Verifies that PaddleOCR 3.x predict API with custom Mapping (non-dict) access is correctly parsed."""
        engine = PaddleOCREngine(OCRConfig(mode="accurate"))

        mapping_result = MockPaddle3xMappingResult({
            "rec_texts": ["SK하이닉스"],
            "rec_scores": [0.992],
            "rec_polys": [[[20, 30], [120, 30], [120, 60], [20, 60]]]
        })

        mock_3x = MagicMock()
        mock_3x.predict.return_value = [mapping_result]
        engine._engine = mock_3x
        engine._is_paddle = True

        dummy_img = np.zeros((100, 200, 3), dtype=np.uint8)
        boxes = engine.recognize(dummy_img, tile_id=1)

        self.assertEqual(len(boxes), 1)
        self.assertEqual(boxes[0].text, "SK하이닉스")
        self.assertAlmostEqual(boxes[0].confidence, 0.992, places=3)
        self.assertEqual(boxes[0].bbox_local, [[20.0, 30.0], [120.0, 30.0], [120.0, 60.0], [20.0, 60.0]])

    def test_paddleocr_3x_predict_json_and_xmin_ymin_xmax_ymax_box_conversion(self):
        """Verifies that PaddleOCR 3.x JSON access with [xmin, ymin, xmax, ymax] converts to 4-point polygon."""
        engine = PaddleOCREngine(OCRConfig(mode="accurate"))

        json_result = MockPaddle3xJsonResult({
            "rec_texts": ["현대차"],
            "rec_scores": [0.975],
            "rec_boxes": [[15, 25, 115, 65]]  # [xmin, ymin, xmax, ymax]
        })

        mock_3x = MagicMock()
        mock_3x.predict.return_value = [json_result]
        engine._engine = mock_3x
        engine._is_paddle = True

        dummy_img = np.zeros((100, 200, 3), dtype=np.uint8)
        boxes = engine.recognize(dummy_img, tile_id=1)

        self.assertEqual(len(boxes), 1)
        self.assertEqual(boxes[0].text, "현대차")
        self.assertAlmostEqual(boxes[0].confidence, 0.975, places=3)
        # Expected converted 4-point polygon: [[15, 25], [115, 25], [115, 65], [15, 65]]
        self.assertEqual(boxes[0].bbox_local, [[15.0, 25.0], [115.0, 25.0], [115.0, 65.0], [15.0, 65.0]])

    def test_paddleocr_2x_ocr_api(self):
        """Verifies that PaddleOCR 2.x legacy ocr API is correctly parsed."""
        engine = PaddleOCREngine(OCRConfig(mode="accurate"))

        mock_2x = MagicMock(spec=["ocr"])
        mock_2x.ocr.return_value = [
            [
                [[[15, 25], [105, 25], [105, 55], [15, 55]], ("SK하이닉스", 0.978)],
                [[[115, 25], [185, 25], [185, 55], [115, 55]], ("000660", 0.995)]
            ]
        ]

        engine._engine = mock_2x
        engine._is_paddle = True

        dummy_img = np.zeros((100, 200, 3), dtype=np.uint8)
        boxes = engine.recognize(dummy_img, tile_id=2)

        self.assertEqual(len(boxes), 2)
        self.assertEqual(boxes[0].text, "SK하이닉스")
        self.assertAlmostEqual(boxes[0].confidence, 0.978, places=3)
        self.assertEqual(boxes[1].text, "000660")
        self.assertAlmostEqual(boxes[1].confidence, 0.995, places=3)

    def test_rapidocr_korean_identity_and_fallback_tracking(self):
        """Verifies that RapidOCREngine tracks identity, requested model, and fallback flags."""
        config = OCRConfig(mode="fast", language="ko")
        engine = RapidOCREngine(config)

        self.assertEqual(engine.requested_model, "PP-OCRv5 (ko)")
        self.assertIn("PP-OCRv5", engine.model_family)
        self.assertFalse(engine.engine_fallback)
        self.assertIn("korean", engine.rec_model)

    def test_install_scripts_precache_command_regression(self):
        """P0 Regression: Ensure exact import and instantiation in install.ps1/install.sh runs without error."""
        # 1. New official class name
        eng = RapidOCREngine(OCRConfig())
        self.assertIsNotNone(eng)

        # 2. Backward compatibility alias
        eng_alias = RapidEngine(OCRConfig())
        self.assertIsNotNone(eng_alias)


if __name__ == "__main__":
    unittest.main()
