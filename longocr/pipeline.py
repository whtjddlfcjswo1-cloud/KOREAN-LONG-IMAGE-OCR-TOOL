"""Main LongImageOCR End-to-End Processing Pipeline."""

import os
import time
import json
import logging
from typing import List, Optional, Union, Dict, Any
from pathlib import Path
from PIL import Image

from .config import OCRConfig
from .engines import create_engine
from .engines.base import BaseOCREngine, OCRBox
from .splitter import split_image, is_long_image, TileInfo
from .retry import RetryManager
from .merge import map_to_global_coordinates, deduplicate_boxes
from .reader import format_markdown_document, format_plain_text
from .audit import generate_audit_report
from .cache import CacheManager
from .preprocess import compute_image_hash, compute_file_hash

logger = logging.getLogger("longocr.pipeline")


class PipelineResult:
    """Encapsulates the end-to-end processing results and artifacts."""

    def __init__(
        self,
        markdown: str,
        text: str,
        output_dir: str,
        total_tiles: int,
        total_boxes: int,
        low_confidence_count: int,
        audit_required: bool,
        elapsed_seconds: float,
        boxes: List[OCRBox],
        manifest: Dict[str, Any]
    ):
        self.markdown = markdown
        self.text = text
        self.output_dir = output_dir
        self.total_tiles = total_tiles
        self.total_boxes = total_boxes
        self.low_confidence_count = low_confidence_count
        self.audit_required = audit_required
        self.elapsed_seconds = elapsed_seconds
        self.boxes = boxes
        self.manifest = manifest


class LongImageOCRPipeline:
    """Decoupled, multi-AI shared pipeline for ultra-long screenshot OCR."""

    def __init__(self, config: Optional[OCRConfig] = None, engine: Optional[BaseOCREngine] = None):
        self.config = config or OCRConfig()
        self.engine = engine or create_engine(self.config)

    def process(self, image_input: Union[str, Path, Image.Image], output_dir: Optional[str] = None) -> PipelineResult:
        start_time = time.time()

        if isinstance(image_input, (str, Path)):
            image_path = str(Path(image_input).resolve())
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Input image not found: {image_path}")
            pil_image = Image.open(image_path)
            image_name = os.path.splitext(os.path.basename(image_path))[0]
            img_hash = compute_file_hash(image_path)
        else:
            pil_image = image_input
            image_name = f"image_{int(time.time())}"
            img_hash = compute_image_hash(pil_image.tobytes())

        if not output_dir:
            if self.config.output_dir:
                output_dir = os.path.abspath(self.config.output_dir)
            else:
                output_dir = os.path.abspath(os.path.join(".", "ocr_output", image_name))
        os.makedirs(output_dir, exist_ok=True)

        tiles_dir = os.path.join(output_dir, "tiles")
        crops_dir = os.path.join(output_dir, "low_confidence")
        cache_dir = os.path.join(output_dir, ".cache")

        if self.config.save_tiles:
            os.makedirs(tiles_dir, exist_ok=True)
        if self.config.save_low_confidence_crops:
            os.makedirs(crops_dir, exist_ok=True)

        model_identity = {
            "longocr_version": "0.1.0a1",
            "backend": self.engine.name,
            "backend_version": getattr(self.engine, "backend_version", "unknown"),
            "model_family": getattr(self.engine, "model_family", "unknown"),
            "rec_model": getattr(self.engine, "rec_model", "unknown"),
            "det_model": getattr(self.engine, "det_model", "unknown"),
            "actual_model": getattr(self.engine, "actual_model", self.engine.name),
            "language": self.config.language
        }

        cfg_hash = self.config.compute_hash()
        cache = CacheManager(cache_dir, img_hash, cfg_hash, model_identity) if self.config.enable_cache else None

        tiles: List[TileInfo] = split_image(pil_image, self.config)
        logger.info(f"Split image ({pil_image.width}x{pil_image.height}) into {len(tiles)} tiles.")

        retry_manager = RetryManager(
            engine=self.engine,
            config=self.config,
            output_crops_dir=crops_dir if self.config.save_low_confidence_crops else None
        )

        all_boxes: List[OCRBox] = []

        for tile in tiles:
            tile_img_path = os.path.join(tiles_dir, f"tile_{tile.tile_id:03d}.png")
            if self.config.save_tiles and not os.path.exists(tile_img_path):
                tile.image.save(tile_img_path)

            cached_boxes = cache.load_tile_cache(tile.tile_id) if cache else None
            if cached_boxes is not None:
                logger.debug(f"Loaded tile {tile.tile_id} from cache ({len(cached_boxes)} boxes).")
                mapped = map_to_global_coordinates(cached_boxes, tile)
                all_boxes.extend(mapped)
                continue

            raw_boxes = self.engine.recognize(tile.image, tile_id=tile.tile_id)

            if self.config.mode == "hybrid":
                processed_boxes = retry_manager.process_tile_boxes(tile.image, raw_boxes, tile.tile_id)
            else:
                processed_boxes = raw_boxes

            if cache:
                cache.save_tile_cache(tile.tile_id, processed_boxes)

            mapped_boxes = map_to_global_coordinates(processed_boxes, tile)
            all_boxes.extend(mapped_boxes)

        deduped_boxes, merges_audit = deduplicate_boxes(all_boxes, self.config)
        logger.info(f"Deduplicated {len(all_boxes)} detected boxes down to {len(deduped_boxes)} final boxes.")

        markdown_content = format_markdown_document(deduped_boxes, pil_image.width, pil_image.height)
        plaintext_content = format_plain_text(deduped_boxes)
        audit_content = generate_audit_report(
            boxes=deduped_boxes,
            tiles=tiles,
            merges_audit=merges_audit,
            config=self.config,
            image_name=image_name
        )

        low_conf_count = sum(1 for b in deduped_boxes if b.confidence < self.config.confidence_threshold)
        audit_required = low_conf_count > 0
        elapsed = time.time() - start_time

        is_fallback = getattr(self.engine, "engine_fallback", getattr(self.engine, "fallback_occurred", False))

        manifest = {
            "image_name": image_name,
            "width": pil_image.width,
            "height": pil_image.height,
            "is_long_image": is_long_image(pil_image.width, pil_image.height, self.config),
            "total_tiles": len(tiles),
            "tiles": [t.to_dict() for t in tiles],
            "total_boxes_detected": len(all_boxes),
            "total_boxes_deduplicated": len(deduped_boxes),
            "low_confidence_count": low_conf_count,
            "audit_required": audit_required,
            "elapsed_seconds": round(elapsed, 3),
            "engine": self.engine.name,
            "engine_fallback": is_fallback,
            "requested_model": getattr(self.engine, "requested_model", self.engine.name),
            "actual_model": getattr(self.engine, "actual_model", self.engine.name),
            "fallback_reason": getattr(self.engine, "fallback_reason", None),
            "config": self.config.to_dict()
        }

        with open(os.path.join(output_dir, "output.md"), "w", encoding="utf-8") as f:
            f.write(markdown_content)
        with open(os.path.join(output_dir, "output.txt"), "w", encoding="utf-8") as f:
            f.write(plaintext_content)
        with open(os.path.join(output_dir, "audit.md"), "w", encoding="utf-8") as f:
            f.write(audit_content)
        with open(os.path.join(output_dir, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        with open(os.path.join(output_dir, "ocr.json"), "w", encoding="utf-8") as f:
            json.dump([b.to_dict() for b in deduped_boxes], f, ensure_ascii=False, indent=2)

        return PipelineResult(
            markdown=markdown_content,
            text=plaintext_content,
            output_dir=output_dir,
            total_tiles=len(tiles),
            total_boxes=len(deduped_boxes),
            low_confidence_count=low_conf_count,
            audit_required=audit_required,
            elapsed_seconds=elapsed,
            boxes=deduped_boxes,
            manifest=manifest
        )
