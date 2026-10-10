"""Base OCR Engine and OCRBox data structure."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Union, Dict, Any
import numpy as np
from PIL import Image


@dataclass
class OCRBox:
    text: str
    confidence: float
    bbox_local: List[List[float]]  # [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
    bbox_global: List[List[float]] = field(default_factory=list)
    tile: int = 1
    engine: str = "generic"
    retry: bool = False
    retry_variant: Optional[str] = None
    crop_path: Optional[str] = None

    @property
    def x1(self) -> float:
        return min(pt[0] for pt in self.bbox_global) if self.bbox_global else min(pt[0] for pt in self.bbox_local)

    @property
    def y1(self) -> float:
        return min(pt[1] for pt in self.bbox_global) if self.bbox_global else min(pt[1] for pt in self.bbox_local)

    @property
    def x2(self) -> float:
        return max(pt[0] for pt in self.bbox_global) if self.bbox_global else max(pt[0] for pt in self.bbox_local)

    @property
    def y2(self) -> float:
        return max(pt[1] for pt in self.bbox_global) if self.bbox_global else max(pt[1] for pt in self.bbox_local)

    @property
    def width(self) -> float:
        return max(0.0, self.x2 - self.x1)

    @property
    def height(self) -> float:
        return max(0.0, self.y2 - self.y1)

    @property
    def center_x(self) -> float:
        return (self.x1 + self.x2) / 2.0

    @property
    def center_y(self) -> float:
        return (self.y1 + self.y2) / 2.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "confidence": round(float(self.confidence), 4),
            "bbox_local": [[round(float(c), 1) for c in pt] for pt in self.bbox_local],
            "bbox_global": [[round(float(c), 1) for c in pt] for pt in self.bbox_global],
            "tile": self.tile,
            "engine": self.engine,
            "retry": self.retry,
            "retry_variant": self.retry_variant,
            "crop_path": self.crop_path,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "OCRBox":
        return cls(
            text=d.get("text", ""),
            confidence=float(d.get("confidence", 0.0)),
            bbox_local=d.get("bbox_local", []),
            bbox_global=d.get("bbox_global", []),
            tile=int(d.get("tile", 1)),
            engine=d.get("engine", "generic"),
            retry=bool(d.get("retry", False)),
            retry_variant=d.get("retry_variant"),
            crop_path=d.get("crop_path"),
        )


class BaseOCREngine(ABC):
    """Abstract base class for OCR Engines."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def recognize(
        self,
        image: Union[Image.Image, np.ndarray],
        tile_id: int = 1
    ) -> List[OCRBox]:
        """Recognizes text and bounding boxes in a single tile image."""
        pass
