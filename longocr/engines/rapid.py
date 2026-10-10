"""RapidOCR Engine implementation using official RapidOCR 3.x and ONNXRuntime.

Configured with official PP-OCRv5 Detection, PP-OCRv5 Korean Recognition, and ONNXRuntime.
"""

import os
import logging
from typing import List, Optional, Union
import numpy as np
from PIL import Image

from .base import BaseOCREngine, OCRBox
from ..config import OCRConfig

logger = logging.getLogger("longocr.engine.rapid")


class RapidOCREngine(BaseOCREngine):
    """Fast ONNX-based OCR Engine using official RapidOCR 3.x with PP-OCRv5 models."""

    def __init__(self, config: Optional[OCRConfig] = None):
        import rapidocr
        from rapidocr import RapidOCR, OCRVersion, LangRec, EngineType, ModelType

        self.config = config or OCRConfig()
        self.backend_version = getattr(rapidocr, "__version__", "3.x")
        self.model_family = "PP-OCRv5"
        self.det_model = "ch_PP-OCRv5_det_mobile.onnx"
        self.rec_model = "korean_PP-OCRv5_rec_mobile.onnx" if self.config.language == "ko" else "en_PP-OCRv5_rec_mobile.onnx"
        
        self.engine_fallback = False
        self.requested_model = f"PP-OCRv5 ({self.config.language})"
        self.actual_model = f"PP-OCRv5 ({self.config.language})"
        self.fallback_reason: Optional[str] = None

        params = {
            "Det.engine_type": EngineType.ONNXRUNTIME,
            "Det.ocr_version": OCRVersion.PPOCRV5,
            "Det.model_type": ModelType.MOBILE,
            "Rec.engine_type": EngineType.ONNXRUNTIME,
            "Rec.ocr_version": OCRVersion.PPOCRV5,
            "Rec.model_type": ModelType.MOBILE,
            "Rec.lang_type": LangRec.KOREAN if self.config.language == "ko" else LangRec.EN,
        }

        if self.config.rec_model_path and os.path.exists(self.config.rec_model_path):
            params["Rec.model_path"] = self.config.rec_model_path
        if self.config.rec_keys_path and os.path.exists(self.config.rec_keys_path):
            params["Rec.rec_keys_path"] = self.config.rec_keys_path

        try:
            self._engine = RapidOCR(params=params)
            self._model_version = "PP-OCRv5"
        except Exception as e:
            self.engine_fallback = True
            self.fallback_reason = str(e)
            self.actual_model = "RapidOCR Default (Ch/En fallback)"
            self._model_version = "default_fallback"
            logger.warning(
                "========================================================================\n"
                f"[ENGINE NOTICE] RapidOCR PP-OCRv5 initialization failed for '{self.config.language}': {e}\n"
                "-> Flagging engine_fallback=True in manifest and cache metadata.\n"
                f"-> Actual model running: {self.actual_model}\n"
                "========================================================================"
            )
            self._engine = RapidOCR()

    @property
    def name(self) -> str:
        return f"rapidocr_{self._model_version.lower()}"

    def recognize(
        self,
        image: Union[Image.Image, np.ndarray],
        tile_id: int = 1
    ) -> List[OCRBox]:
        if isinstance(image, Image.Image):
            img_np = np.array(image.convert("RGB"))
        else:
            img_np = image

        try:
            res = self._engine(img_np)
        except Exception as e:
            logger.error(f"Error during RapidOCR inference: {e}")
            return []

        if res is None:
            return []

        boxes: List[OCRBox] = []

        if hasattr(res, "boxes") and hasattr(res, "txts") and hasattr(res, "scores"):
            if res.boxes is None or res.txts is None:
                return []
            for box_coords, text, score in zip(res.boxes, res.txts, res.scores):
                box_list = [[float(c[0]), float(c[1])] for c in box_coords]
                boxes.append(
                    OCRBox(
                        text=str(text).strip(),
                        confidence=float(score),
                        bbox_local=box_list,
                        bbox_global=[],
                        tile=tile_id,
                        engine=self.name,
                        retry=False
                    )
                )
        elif isinstance(res, (list, tuple)) and len(res) > 0 and isinstance(res[0], (list, tuple)):
            for item in res:
                if len(item) >= 3:
                    box_coords, text, score = item[0], item[1], item[2]
                    box_list = [[float(c[0]), float(c[1])] for c in box_coords]
                    boxes.append(
                        OCRBox(
                            text=str(text).strip(),
                            confidence=float(score),
                            bbox_local=box_list,
                            bbox_global=[],
                            tile=tile_id,
                            engine=self.name,
                            retry=False
                        )
                    )

        return boxes


# Backward compatibility alias
RapidEngine = RapidOCREngine
