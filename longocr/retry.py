"""Low-confidence native resolution retry and crop inspector with strict spatial and semantic validation."""

import os
import logging
import difflib
from typing import List, Optional, Tuple
from PIL import Image

from .engines.base import OCRBox, BaseOCREngine
from .preprocess import crop_with_padding, get_preprocessing_variants
from .config import OCRConfig
from .merge import numbers_conflict, normalize_text_for_comparison

logger = logging.getLogger("longocr.retry")


def calculate_box_iou_2d(
    box_a: Tuple[float, float, float, float],
    box_b: Tuple[float, float, float, float]
) -> float:
    """Computes 2D Intersection-over-Union (IoU) between two bounding boxes [x1, y1, x2, y2]."""
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b
    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)
    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h
    if inter_area <= 0.0:
        return 0.0
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union_area = area_a + area_b - inter_area
    return inter_area / union_area if union_area > 0 else 0.0


def is_valid_retry_candidate(
    original_box: OCRBox,
    candidate_box: OCRBox,
    expected_crop_bbox: Tuple[float, float, float, float],
    scale_factor: float
) -> Tuple[bool, float]:
    """Validates whether candidate_box corresponds to original_box within the cropped region."""
    cx1 = candidate_box.x1 / scale_factor
    cy1 = candidate_box.y1 / scale_factor
    cx2 = candidate_box.x2 / scale_factor
    cy2 = candidate_box.y2 / scale_factor
    cand_crop_bbox = (cx1, cy1, cx2, cy2)
    ex1, ey1, ex2, ey2 = expected_crop_bbox
    expected_h = max(10.0, ey2 - ey1)
    expected_cy = (ey1 + ey2) / 2.0
    cand_cy = (cy1 + cy2) / 2.0
    y_dist = abs(cand_cy - expected_cy)
    if y_dist > max(expected_h * 0.75, 25.0):
        return False, 0.0
    iou_2d = calculate_box_iou_2d(expected_crop_bbox, cand_crop_bbox)
    inter_top = max(ey1, cy1)
    inter_bottom = min(ey2, cy2)
    inter_h = max(0.0, inter_bottom - inter_top)
    union_h = (ey2 - ey1) + (cy2 - cy1) - inter_h
    v_iou = inter_h / union_h if union_h > 0 else 0.0
    if iou_2d < 0.20 and v_iou < 0.35:
        return False, 0.0
    if numbers_conflict(original_box.text, candidate_box.text):
        return False, 0.0
    norm_orig = normalize_text_for_comparison(original_box.text)
    norm_cand = normalize_text_for_comparison(candidate_box.text)
    text_sim = difflib.SequenceMatcher(None, norm_orig, norm_cand).ratio()
    if text_sim < 0.25 and iou_2d < 0.40:
        return False, 0.0
    match_score = (iou_2d * 0.4) + (v_iou * 0.3) + (text_sim * 0.3)
    return True, match_score


class RetryManager:
    """Manages native-resolution retries on low-confidence detections and crop persistence."""

    def __init__(self, engine: BaseOCREngine, config: OCRConfig, output_crops_dir: Optional[str] = None):
        self.engine = engine
        self.config = config
        self.output_crops_dir = output_crops_dir
        if self.output_crops_dir:
            os.makedirs(self.output_crops_dir, exist_ok=True)

    def retry_low_confidence_boxes(self, boxes: List[OCRBox], tile_image: Image.Image, tile_id: int) -> List[OCRBox]:
        processed_boxes: List[OCRBox] = []
        for idx, box in enumerate(boxes):
            if box.confidence >= self.config.confidence_threshold:
                processed_boxes.append(box)
                continue
            processed_boxes.append(self._retry_single_box(box, tile_image, tile_id, idx + 1))
        return processed_boxes

    def process_tile_boxes(self, tile_image: Image.Image, boxes: List[OCRBox], tile_id: int) -> List[OCRBox]:
        return self.retry_low_confidence_boxes(boxes=boxes, tile_image=tile_image, tile_id=tile_id)

    def _retry_single_box(self, box: OCRBox, tile_image: Image.Image, tile_id: int, box_idx: int) -> OCRBox:
        try:
            crop_img, (offset_x, offset_y) = crop_with_padding(image=tile_image, bbox=box.bbox_local, padding=self.config.retry_padding)
        except Exception as e:
            logger.warning(f"Failed to crop bbox for tile {tile_id} box {box_idx}: {e}")
            return box

        bx1 = min(pt[0] for pt in box.bbox_local) - offset_x
        by1 = min(pt[1] for pt in box.bbox_local) - offset_y
        bx2 = max(pt[0] for pt in box.bbox_local) - offset_x
        by2 = max(pt[1] for pt in box.bbox_local) - offset_y
        expected_crop_bbox = (bx1, by1, bx2, by2)

        crop_filename = f"crop_tile{tile_id:03d}_{box_idx:03d}.png"
        if self.output_crops_dir:
            crop_save_path = os.path.join(self.output_crops_dir, crop_filename)
            try:
                crop_img.save(crop_save_path)
                box.crop_path = os.path.join("low_confidence", crop_filename)
            except Exception as e:
                logger.warning(f"Failed to save crop image: {e}")

        variants = get_preprocessing_variants(crop_img, upscale_factor=self.config.retry_upscale_factor)
        best_score = box.confidence
        best_text = box.text
        best_variant = None

        for var_name, var_img in variants:
            try:
                scale_factor = var_img.width / float(crop_img.width) if crop_img.width > 0 else 1.0
                retry_results = self.engine.recognize(var_img, tile_id=tile_id)
                if not retry_results:
                    continue
                for cand in retry_results:
                    is_valid, match_score = is_valid_retry_candidate(
                        original_box=box,
                        candidate_box=cand,
                        expected_crop_bbox=expected_crop_bbox,
                        scale_factor=scale_factor
                    )
                    if not is_valid:
                        continue
                    if cand.confidence > best_score and len(cand.text.strip()) > 0:
                        best_score = cand.confidence
                        best_text = cand.text
                        best_variant = var_name
            except Exception:
                continue

        if best_score > box.confidence and best_text != box.text:
            logger.info(
                f"Retry strictly verified & improved tile {tile_id} box {box_idx}: '{box.text}' ({box.confidence:.3f}) -> "
                f"'{best_text}' ({best_score:.3f}) using variant [{best_variant}]"
            )
            box.text = best_text
            box.confidence = best_score
            box.retry = True
            box.retry_variant = best_variant

        return box
