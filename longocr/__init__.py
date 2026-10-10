"""LongImageOCR — Multi-AI Shared Ultra-Long Screenshot OCR Engine."""

from .config import OCRConfig
from .splitter import split_image, TileInfo, is_long_image
from .engines import BaseOCREngine, OCRBox, RapidOCREngine, PaddleOCREngine, create_engine
from .pipeline import LongImageOCRPipeline, PipelineResult

__version__ = "0.1.0a1"
__all__ = [
    "OCRConfig",
    "LongImageOCRPipeline",
    "PipelineResult",
    "split_image",
    "TileInfo",
    "is_long_image",
    "BaseOCREngine",
    "OCRBox",
    "RapidOCREngine",
    "PaddleOCREngine",
    "create_engine",
    "__version__",
]
