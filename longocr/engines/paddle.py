"""PaddleOCR Engine implementation supporting PaddleOCR 3.x (predict API) and 2.x (ocr API)."""

import logging
from typing import List, Optional, Union, Dict, Any
import numpy as np
from PIL import Image

from .base import BaseOCREngine, OCRBox
from ..config import OCRConfig

logger = logging.getLogger("longocr.engine.paddle")


def _extract_paddle_field(item: Any, candidate_keys: List[str]) -> Optional[Any]:
    """Safely extracts field from PaddleOCR 3.x result across attribute, mapping, and json interfaces."""
    for key in candidate_keys:
        val = getattr(item, key, None)
        if val is not None:
            return val
        if hasattr(item, "get") and callable(getattr(item, "get")):
            try:
                val = item.get(key)
                if val is not None:
                    return val
            except Exception:
                pass
        try:
            val = item[key]
            if val is not None:
                return val
        except Exception:
            pass
        if hasattr(item, "json"):
            try:
                raw_json = getattr(item, "json")
                json_data = raw_json() if callable(raw_json) else raw_json
                if isinstance(json_data, str):
                    import json
                    json_data = json.loads(json_data)
                if isinstance(json_data, dict):
                    if key in json_data and json_data[key] is not None:
                        return json_data[key]
                    res = json_data.get("res")
                    if isinstance(res, dict) and key in res and res[key] is not None:
                        return res[key]
            except Exception:
                pass
    return None


def _normalize_box_or_poly(box_or_poly: Any) -> List[List[float]]:
    """Converts 4-point polygons or [xmin, ymin, xmax, ymax] boxes into a standard polygon."""
    if isinstance(box_or_poly, (list, tuple, np.ndarray)) and len(box_or_poly) == 4:
        first = box_or_poly[0]
        if isinstance(first, (int, float, np.number)):
            xmin, ymin, xmax, ymax = (float(c) for c in box_or_poly)
            return [[xmin, ymin], [xmax, ymin], [xmax, ymax], [xmin, ymax]]
    return [[float(pt[0]), float(pt[1])] for pt in box_or_poly]


class PaddleOCREngine(BaseOCREngine):
    """PaddleOCR Engine (Accurate Mode) supporting PaddleOCR 3.x and 2.x APIs."""

    def __init__(self, config: Optional[OCRConfig] = None):
        self.config = config or OCRConfig()
        self._fallback_engine: Optional[BaseOCREngine] = None
        self._engine = None
        self.fallback_occurred = False
        self._is_paddle = False
        self.backend_version = "unknown"
        self.model_family = "PaddleOCR"
        self.rec_model = f"paddle_{self.config.language}"
        self.det_model = "paddle_det"
        self.requested_model = f"PaddleOCR ({self.config.language})"
        self.actual_model = f"PaddleOCR ({self.config.language})"
        self.fallback_reason: Optional[str] = None

        try:
            import paddleocr
            from paddleocr import PaddleOCR
            self.backend_version = getattr(paddleocr, "__version__", "3.x")
            lang = "korean" if self.config.language == "ko" else self.config.language
            init_attempts = [
                {"lang": lang},
                {"lang": lang, "use_angle_cls": True},
                {"lang": lang, "use_direction_classify": True},
            ]
            engine_instance = None
            last_err = None
            for kw in init_attempts:
                try:
                    engine_instance = PaddleOCR(**kw)
                    break
                except TypeError as te:
                    last_err = te
                    continue
            if engine_instance is None:
                raise ImportError(f"Could not initialize PaddleOCR with supported parameter sets: {last_err}")
            self._engine = engine_instance
            self._is_paddle = True
            logger.info(f"PaddleOCR {self.backend_version} engine initialized successfully.")
        except (ImportError, Exception) as e:
            self.fallback_occurred = True
            self.fallback_reason = str(e)
            self.actual_model = "RapidOCR (PP-OCRv5 Korean Fallback)"
            logger.warning(
                "========================================================================\n"
                "[ENGINE NOTICE] PaddleOCR (Accurate Mode) requested, but PaddlePaddle/PaddleOCR is not available.\n"
                f"Reason: {e}\n"
                "-> Explicitly falling back to RapidOCR (PP-OCRv5 Korean ONNXRuntime).\n"
                "-> To use native PaddleOCR, run: pip install paddlepaddle paddleocr\n"
                "========================================================================"
            )
            from .rapid import RapidOCREngine
            self._fallback_engine = RapidOCREngine(self.config)
            self._is_paddle = False

    @property
    def name(self) -> str:
        return "paddleocr" if self._is_paddle else "rapidocr_ppocr (paddle_fallback)"

    def recognize(self, image: Union[Image.Image, np.ndarray], tile_id: int = 1) -> List[OCRBox]:
        if not self._is_paddle and self._fallback_engine:
            return self._fallback_engine.recognize(image, tile_id)
        if isinstance(image, Image.Image):
            img_np = np.array(image.convert("RGB"))
        else:
            img_np = image
        try:
            boxes: List[OCRBox] = []
            if hasattr(self._engine, "predict") and callable(getattr(self._engine, "predict")):
                res = self._engine.predict(img_np)
                items = res if isinstance(res, list) else [res]
                for item in items:
                    rec_texts = _extract_paddle_field(item, ["rec_texts", "texts"])
                    rec_scores = _extract_paddle_field(item, ["rec_scores", "scores"])
                    rec_polys = _extract_paddle_field(item, ["rec_polys", "rec_boxes", "polys", "boxes"])
                    if rec_texts is not None and rec_scores is not None and rec_polys is not None:
                        for text, score, poly in zip(rec_texts, rec_scores, rec_polys):
                            boxes.append(OCRBox(text=str(text).strip(), confidence=float(score), bbox_local=_normalize_box_or_poly(poly), bbox_global=[], tile=tile_id, engine=self.name, retry=False))
                if boxes:
                    return boxes
            if hasattr(self._engine, "ocr") and callable(getattr(self._engine, "ocr")):
                result = self._engine.ocr(img_np)
                if not result:
                    return []
                lines_data = result[0] if (isinstance(result, list) and len(result) > 0 and isinstance(result[0], list)) else result
                for item in lines_data:
                    if isinstance(item, (list, tuple)) and len(item) == 2 and isinstance(item[1], (list, tuple)):
                        box_coords, (text, score) = item
                        box_list = [[float(c[0]), float(c[1])] for c in box_coords]
                        boxes.append(OCRBox(text=str(text).strip(), confidence=float(score), bbox_local=box_list, bbox_global=[], tile=tile_id, engine=self.name, retry=False))
                    elif isinstance(item, dict):
                        box_coords = item.get("dt_polys", item.get("box", []))
                        text = item.get("rec_text", item.get("text", ""))
                        score = item.get("rec_score", item.get("score", 0.0))
                        box_list = [[float(c[0]), float(c[1])] for c in box_coords]
                        boxes.append(OCRBox(text=str(text).strip(), confidence=float(score), bbox_local=box_list, bbox_global=[], tile=tile_id, engine=self.name, retry=False))
            return boxes
        except Exception as e:
            logger.error(f"Error in PaddleOCR inference: {e}")
            if self._fallback_engine:
                return self._fallback_engine.recognize(image, tile_id)
            return []
