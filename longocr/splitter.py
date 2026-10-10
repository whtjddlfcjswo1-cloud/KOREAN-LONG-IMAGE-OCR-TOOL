"""Smart Tiling and Long Image Splitting Module.

Analyzes horizontal content density, edge gradient, and whitespace variance to determine
optimal safe-cut positions, with fallback to overlap slicing.
"""

from dataclasses import dataclass
from typing import List, Tuple, Union, Optional
import numpy as np
from PIL import Image

from .config import OCRConfig


@dataclass
class TileInfo:
    tile_id: int
    source_y_start: int
    source_y_end: int
    width: int
    height: int
    is_safe_cut: bool
    overlap_top: int
    overlap_bottom: int
    image: Image.Image

    def to_dict(self) -> dict:
        return {
            "tile_id": self.tile_id,
            "source_y_start": self.source_y_start,
            "source_y_end": self.source_y_end,
            "width": self.width,
            "height": self.height,
            "is_safe_cut": self.is_safe_cut,
            "overlap_top": self.overlap_top,
            "overlap_bottom": self.overlap_bottom,
        }


def is_long_image(width: int, height: int, config: OCRConfig) -> bool:
    """Determines whether an image requires long-image tiling."""
    if width <= 0 or height <= 0:
        return False
    aspect_ratio = height / float(width)
    return height > config.min_height or aspect_ratio > config.min_aspect_ratio


def compute_horizontal_content_density(gray_array: np.ndarray, whitespace_var_thresh: float = 5.0) -> np.ndarray:
    """Computes a per-row content density score based on edge magnitude and row variance."""
    step = max(1, gray_array.shape[1] // 400)
    sampled = gray_array[:, ::step].astype(np.float32)
    row_var = np.var(sampled, axis=1)
    grad_y = np.abs(np.diff(sampled, axis=0, prepend=sampled[:1, :]))
    row_grad = np.mean(grad_y, axis=1)
    is_whitespace = row_var <= whitespace_var_thresh
    row_var[is_whitespace] = 0.0
    row_grad[is_whitespace] = 0.0
    combined = (row_var / (row_var.max() + 1e-6)) * 0.5 + (row_grad / (row_grad.max() + 1e-6)) * 0.5
    kernel_size = 7
    kernel = np.ones(kernel_size) / kernel_size
    return np.convolve(combined, kernel, mode="same")


def find_safe_cut_y(density_profile: np.ndarray, target_y: int, search_range: int, min_score_threshold: float = 0.05) -> Tuple[int, bool]:
    """Finds the lowest content density position within [target_y - range, target_y + range]."""
    total_height = len(density_profile)
    start_y = max(0, target_y - search_range)
    end_y = min(total_height - 1, target_y + search_range)
    if start_y >= end_y:
        return min(target_y, total_height), False
    search_window = density_profile[start_y:end_y]
    min_idx_relative = int(np.argmin(search_window))
    min_density = float(search_window[min_idx_relative])
    best_y = start_y + min_idx_relative
    return best_y, min_density <= min_score_threshold


def split_image(image: Union[Image.Image, np.ndarray], config: Optional[OCRConfig] = None) -> List[TileInfo]:
    """Splits a long image into overlapping or safe-cut tiles preserving native resolution."""
    if config is None:
        config = OCRConfig()
    pil_img = Image.fromarray(image) if isinstance(image, np.ndarray) else image
    width, height = pil_img.size
    if not is_long_image(width, height, config):
        return [TileInfo(1, 0, height, width, height, True, 0, 0, pil_img.copy())]
    gray = np.array(pil_img.convert("L"))
    density_profile = compute_horizontal_content_density(gray, whitespace_var_thresh=config.whitespace_variance_threshold)
    tiles: List[TileInfo] = []
    current_y = 0
    tile_id = 1
    while current_y < height:
        target_end_y = current_y + config.tile_height
        if target_end_y >= height:
            y_start, y_end = current_y, height
            overlap_top = config.overlap if tile_id > 1 else 0
            tile_crop = pil_img.crop((0, y_start, width, y_end))
            tiles.append(TileInfo(tile_id, y_start, y_end, width, y_end-y_start, True, overlap_top, 0, tile_crop))
            break
        best_cut_y, is_safe = find_safe_cut_y(density_profile, target_end_y, config.tile_search_range, config.content_density_threshold)
        if is_safe:
            y_start = current_y
            y_end = min(best_cut_y + (config.overlap // 2), height)
            tile_crop = pil_img.crop((0, y_start, width, y_end))
            tiles.append(TileInfo(tile_id, y_start, y_end, width, y_end-y_start, True, config.overlap if tile_id > 1 else 0, config.overlap // 2, tile_crop))
            current_y = best_cut_y
        else:
            y_start = current_y
            y_end = min(target_end_y + config.overlap, height)
            tile_crop = pil_img.crop((0, y_start, width, y_end))
            tiles.append(TileInfo(tile_id, y_start, y_end, width, y_end-y_start, False, config.overlap if tile_id > 1 else 0, config.overlap, tile_crop))
            current_y = target_end_y
        tile_id += 1
    return tiles
