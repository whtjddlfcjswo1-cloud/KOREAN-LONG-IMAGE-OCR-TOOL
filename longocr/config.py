"""Configuration dataclasses, defaults, and deterministic hashing for LongImageOCR."""

from dataclasses import dataclass
from typing import Optional, Dict, Any
import hashlib
import json


@dataclass
class OCRConfig:
    # Long Image Detection thresholds
    min_height: int = 4000
    min_aspect_ratio: float = 3.0

    # Smart Tiling parameters
    tile_height: int = 2200
    tile_search_range: int = 300
    overlap: int = 220
    content_density_threshold: float = 0.05  # Content density score below this qualifies as safe cut
    whitespace_variance_threshold: float = 5.0  # Pixel variance below this qualifies as pure background whitespace

    # Engine and Execution Mode
    mode: str = "hybrid"  # "fast", "accurate", "hybrid"
    language: str = "ko"  # "ko", "en", etc.
    engine_name: Optional[str] = None  # Explicit engine override ("rapid", "paddle")
    rec_model_path: Optional[str] = None
    rec_keys_path: Optional[str] = None

    # Low Confidence Retry
    confidence_threshold: float = 0.75
    retry_padding: int = 30
    retry_upscale_factor: float = 1.5
    save_low_confidence_crops: bool = True

    # Deduplication and Reconciliation
    iou_threshold: float = 0.35  # Minimum vertical 1D IoU required to consider overlap duplicate
    text_similarity_threshold: float = 0.85
    strict_number_matching: bool = True  # Prohibit merging items when numeric tokens differ

    # Layout & Reading Order
    reading_order_mode: str = "auto"  # "auto", "chat", "table", "document"
    line_y_tolerance: int = 15

    # Cache & Output
    enable_cache: bool = True
    output_dir: Optional[str] = None
    save_tiles: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Returns full dictionary of all configuration parameters affecting OCR output."""
        return {
            "min_height": self.min_height,
            "min_aspect_ratio": self.min_aspect_ratio,
            "tile_height": self.tile_height,
            "tile_search_range": self.tile_search_range,
            "overlap": self.overlap,
            "content_density_threshold": self.content_density_threshold,
            "whitespace_variance_threshold": self.whitespace_variance_threshold,
            "mode": self.mode,
            "language": self.language,
            "engine_name": self.engine_name,
            "rec_model_path": self.rec_model_path,
            "rec_keys_path": self.rec_keys_path,
            "confidence_threshold": self.confidence_threshold,
            "retry_padding": self.retry_padding,
            "retry_upscale_factor": self.retry_upscale_factor,
            "save_low_confidence_crops": self.save_low_confidence_crops,
            "iou_threshold": self.iou_threshold,
            "text_similarity_threshold": self.text_similarity_threshold,
            "strict_number_matching": self.strict_number_matching,
            "reading_order_mode": self.reading_order_mode,
            "line_y_tolerance": self.line_y_tolerance,
            "output_dir": self.output_dir,
        }

    def compute_hash(self) -> str:
        """Computes a deterministic hash of all configuration parameters for cache invalidation."""
        payload = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
