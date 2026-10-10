"""Resume and caching system for long image OCR with model/version identity."""

import os
import json
import hashlib
import logging
from typing import List, Optional, Dict, Any
from .engines.base import OCRBox

logger = logging.getLogger("longocr.cache")


class CacheManager:
    """Handles per-tile resume and cache invalidation based on image, config, and model identities."""

    def __init__(
        self,
        cache_dir: str,
        image_hash: str,
        config_hash: str,
        model_identity: Optional[Dict[str, Any]] = None
    ):
        self.cache_dir = cache_dir
        self.image_hash = image_hash
        self.config_hash = config_hash
        self.model_identity = model_identity or {}
        self.meta_path = os.path.join(self.cache_dir, "cache_meta.json")

        os.makedirs(self.cache_dir, exist_ok=True)
        self._validate_or_reset()

    def _validate_or_reset(self) -> None:
        """Invalidates cache if image, config, or model identity has changed."""
        if not os.path.exists(self.meta_path):
            self._write_meta([])
            return

        try:
            with open(self.meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            
            invalid = False
            if meta.get("image_hash") != self.image_hash:
                invalid = True
            elif meta.get("config_hash") != self.config_hash:
                invalid = True
            elif self.model_identity and meta.get("model_identity") != self.model_identity:
                invalid = True

            if invalid:
                logger.info("Cache invalidated: input image, configuration, or model identity modified.")
                self._clear_cache()
                self._write_meta([])
        except Exception as e:
            logger.warning(f"Failed to read cache meta ({e}), resetting cache.")
            self._clear_cache()
            self._write_meta([])

    def _clear_cache(self) -> None:
        if os.path.exists(self.cache_dir):
            for fname in os.listdir(self.cache_dir):
                if fname.endswith(".json"):
                    try:
                        os.remove(os.path.join(self.cache_dir, fname))
                    except Exception:
                        pass

    def _write_meta(self, completed_tiles: List[int]) -> None:
        meta = {
            "image_hash": self.image_hash,
            "config_hash": self.config_hash,
            "model_identity": self.model_identity,
            "completed_tiles": completed_tiles
        }
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

    def is_tile_cached(self, tile_id: int) -> bool:
        tile_file = os.path.join(self.cache_dir, f"tile_{tile_id:03d}.json")
        return os.path.exists(tile_file)

    def load_tile_cache(self, tile_id: int) -> Optional[List[OCRBox]]:
        tile_file = os.path.join(self.cache_dir, f"tile_{tile_id:03d}.json")
        if not os.path.exists(tile_file):
            return None

        try:
            with open(tile_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [OCRBox.from_dict(d) for d in data]
        except Exception as e:
            logger.warning(f"Failed to load tile cache {tile_file}: {e}")
            return None

    def save_tile_cache(self, tile_id: int, boxes: List[OCRBox]) -> None:
        tile_file = os.path.join(self.cache_dir, f"tile_{tile_id:03d}.json")
        try:
            data = [b.to_dict() for b in boxes]
            with open(tile_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            completed = []
            if os.path.exists(self.meta_path):
                try:
                    with open(self.meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                        completed = meta.get("completed_tiles", [])
                except Exception:
                    pass
            if tile_id not in completed:
                completed.append(tile_id)
                self._write_meta(completed)
        except Exception as e:
            logger.warning(f"Failed to save tile cache {tile_file}: {e}")
