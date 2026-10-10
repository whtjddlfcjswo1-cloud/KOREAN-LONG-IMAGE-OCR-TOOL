"""OCR Engine registry and factory."""

from .base import BaseOCREngine, OCRBox
from .rapid import RapidOCREngine
from .paddle import PaddleOCREngine
from ..config import OCRConfig


def create_engine(config: OCRConfig) -> BaseOCREngine:
    """Factory to create appropriate OCR engine according to configuration mode."""
    if config.engine_name:
        name = config.engine_name.lower()
        if "paddle" in name:
            return PaddleOCREngine(config)
        elif "rapid" in name:
            return RapidOCREngine(config)

    if config.mode == "accurate":
        return PaddleOCREngine(config)
    elif config.mode in ("fast", "hybrid"):
        return RapidOCREngine(config)
    else:
        return RapidOCREngine(config)


__all__ = ["BaseOCREngine", "OCRBox", "RapidOCREngine", "PaddleOCREngine", "create_engine"]
