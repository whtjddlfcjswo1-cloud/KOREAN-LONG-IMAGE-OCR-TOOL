"""Global coordinate mapping and overlap deduplication module."""

import re
import difflib
from typing import List, Tuple
from .engines.base import OCRBox
from .splitter import TileInfo
from .config import OCRConfig


def map_to_global_coordinates(boxes: List[OCRBox], tile_info: TileInfo) -> List[OCRBox]:
    """Converts local tile bounding box coordinates into full-image global coordinates."""
    y_offset = tile_info.source_y_start

    for box in boxes:
        box.bbox_global = [
            [float(pt[0]), float(pt[1] + y_offset)]
            for pt in box.bbox_local
        ]
        box.tile = tile_info.tile_id

    return boxes


def normalize_text_for_comparison(text: str) -> str:
    """Normalizes text for fuzzy match while preserving semantic tokens."""
    return "".join(text.split()).lower()


def extract_numbers(text: str) -> List[str]:
    """Extracts all contiguous number sequences (e.g. '1,234,500' -> ['1234500'])."""
    cleaned = re.sub(r'[,_]', '', text)
    return re.findall(r'\d+', cleaned)


def numbers_conflict(text_a: str, text_b: str) -> bool:
    """Checks if numbers in text_a and text_b conflict."""
    nums_a = extract_numbers(text_a)
    nums_b = extract_numbers(text_b)
    if not nums_a or not nums_b:
        return False
    return nums_a != nums_b


def calculate_iou_y(box_a: OCRBox, box_b: OCRBox) -> float:
    """Computes 1D vertical Intersection-over-Union (IoU) between two global boxes."""
    ay1, ay2 = box_a.y1, box_a.y2
    by1, by2 = box_b.y1, box_b.y2
    inter_top = max(ay1, by1)
    inter_bottom = min(ay2, by2)
    inter_h = max(0.0, inter_bottom - inter_top)
    if inter_h == 0.0:
        return 0.0
    union_h = (ay2 - ay1) + (by2 - by1) - inter_h
    return inter_h / union_h if union_h > 0 else 0.0


def are_boxes_duplicates(box_a: OCRBox, box_b: OCRBox, config: OCRConfig) -> bool:
    """Determines whether two global OCR boxes represent the same text from overlapping tiles."""
    if box_a.tile == box_b.tile:
        return False
    if config.strict_number_matching and numbers_conflict(box_a.text, box_b.text):
        return False
    iou_y = calculate_iou_y(box_a, box_b)
    y_dist = abs(box_a.center_y - box_b.center_y)
    max_h = max(box_a.height, box_b.height, 10.0)
    if iou_y < config.iou_threshold and y_dist > max_h * 0.7:
        return False
    x_dist = abs(box_a.center_x - box_b.center_x)
    max_w = max(box_a.width, box_b.width, 20.0)
    if x_dist > max_w * 0.4:
        return False
    norm_a = normalize_text_for_comparison(box_a.text)
    norm_b = normalize_text_for_comparison(box_b.text)
    if norm_a == norm_b:
        return True
    return difflib.SequenceMatcher(None, norm_a, norm_b).ratio() >= config.text_similarity_threshold


def deduplicate_boxes(boxes: List[OCRBox], config: OCRConfig) -> Tuple[List[OCRBox], List[dict]]:
    """Removes duplicate OCR boxes generated across overlapping tile boundaries."""
    if not boxes:
        return [], []

    sorted_boxes = sorted(boxes, key=lambda b: (b.y1, b.x1))
    kept_boxes: List[OCRBox] = []
    suppressed_indices = set()
    merges_audit = []

    for i in range(len(sorted_boxes)):
        if i in suppressed_indices:
            continue
        box_i = sorted_boxes[i]
        best_box = box_i

        for j in range(i + 1, len(sorted_boxes)):
            if j in suppressed_indices:
                continue
            box_j = sorted_boxes[j]
            if box_j.y1 - box_i.y2 > 100.0:
                break
            if are_boxes_duplicates(box_i, box_j, config):
                if box_j.confidence > best_box.confidence:
                    winner = box_j
                    loser = best_box
                else:
                    winner = best_box
                    loser = box_j
                merges_audit.append({
                    "winner_tile": winner.tile,
                    "winner_text": winner.text,
                    "winner_conf": winner.confidence,
                    "loser_tile": loser.tile,
                    "loser_text": loser.text,
                    "loser_conf": loser.confidence,
                    "global_y": round(winner.y1, 1)
                })
                best_box = winner
                suppressed_indices.add(j)

        kept_boxes.append(best_box)

    return kept_boxes, merges_audit
