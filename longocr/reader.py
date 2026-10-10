"""Reading order, layout analysis, and Markdown/Plaintext document reconstruction.

Features robust multi-row table alignment detection and configurable reading order modes.
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from .engines.base import OCRBox
from .config import OCRConfig


def cluster_into_lines(boxes: List[OCRBox], y_tolerance: float = 12.0) -> List[List[OCRBox]]:
    """Groups OCR boxes into horizontal lines, sorted left-to-right within each line."""
    if not boxes:
        return []
    sorted_by_y = sorted(boxes, key=lambda b: (b.y1, b.x1))
    lines: List[List[OCRBox]] = []
    current_line: List[OCRBox] = [sorted_by_y[0]]
    current_y = sorted_by_y[0].center_y
    for box in sorted_by_y[1:]:
        line_height = max([b.height for b in current_line] + [box.height, 10.0])
        dynamic_tol = max(y_tolerance, line_height * 0.45)
        if abs(box.center_y - current_y) <= dynamic_tol:
            current_line.append(box)
            current_y = sum(b.center_y for b in current_line) / len(current_line)
        else:
            current_line.sort(key=lambda b: b.x1)
            lines.append(current_line)
            current_line = [box]
            current_y = box.center_y
    if current_line:
        current_line.sort(key=lambda b: b.x1)
        lines.append(current_line)
    return lines


def are_columns_aligned(line_a: List[OCRBox], line_b: List[OCRBox], col_tol: float = 50.0) -> bool:
    """Verifies that line_a and line_b share matching column count and consistent horizontal X alignments."""
    if len(line_a) != len(line_b) or len(line_a) < 2:
        return False
    for box_a, box_b in zip(line_a, line_b):
        if abs(box_a.x1 - box_b.x1) > col_tol:
            return False
    return True


def detect_robust_tables(lines: List[List[OCRBox]]) -> List[int]:
    """Identifies consecutive rows forming genuine tables based on column stability and X alignment."""
    n = len(lines)
    table_ids = [0] * n
    current_table_id = 1
    i = 0
    while i < n - 1:
        if len(lines[i]) >= 2 and are_columns_aligned(lines[i], lines[i + 1]):
            table_len = 2
            j = i + 2
            while j < n and are_columns_aligned(lines[j - 1], lines[j]):
                table_len += 1
                j += 1
            if table_len >= 2:
                for idx in range(i, j):
                    table_ids[idx] = current_table_id
                current_table_id += 1
                i = j
                continue
        i += 1
    return table_ids


def is_timestamp_or_sender(text: str) -> bool:
    """Heuristic check for chat timestamps or metadata headers."""
    time_pattern = r'(\d{1,2}:\d{2}|\d{4}[-/.노년]\s*\d{1,2}[-/.월]\s*\d{1,2}|오전|오후|AM|PM)'
    return bool(re.search(time_pattern, text, re.IGNORECASE))


def build_markdown(boxes: List[OCRBox], config: Optional[OCRConfig] = None) -> str:
    """Reconstructs the document into clean, readable GitHub-flavored Markdown."""
    if not boxes:
        return ""
    cfg = config or OCRConfig()
    lines = cluster_into_lines(boxes, y_tolerance=cfg.line_y_tolerance)
    mode = cfg.reading_order_mode.lower()
    table_ids = detect_robust_tables(lines) if mode in ("auto", "table") else [0] * len(lines)
    md_lines: List[str] = []
    active_table_id = 0
    for idx, line in enumerate(lines):
        line_text_parts = [b.text for b in line]
        t_id = table_ids[idx]
        if t_id > 0:
            row_str = "| " + " | ".join(line_text_parts) + " |"
            if t_id != active_table_id:
                header_sep = "| " + " | ".join(["---"] * len(line)) + " |"
                md_lines.append(row_str)
                md_lines.append(header_sep)
                active_table_id = t_id
            else:
                md_lines.append(row_str)
        else:
            active_table_id = 0
            joined_text = "  ".join(line_text_parts)
            if mode in ("auto", "chat") and is_timestamp_or_sender(joined_text) and len(joined_text) < 40:
                md_lines.append(f"\n> **{joined_text}**")
            elif len(line) == 1 and line[0].height > 35 and len(joined_text) < 40:
                md_lines.append(f"\n## {joined_text}\n")
            else:
                md_lines.append(joined_text)
    return "\n".join(md_lines).strip() + "\n"


def build_plain_text(boxes: List[OCRBox], config: Optional[OCRConfig] = None) -> str:
    """Reconstructs plain text line by line."""
    if not boxes:
        return ""
    cfg = config or OCRConfig()
    lines = cluster_into_lines(boxes, y_tolerance=cfg.line_y_tolerance)
    return "\n".join(" ".join(b.text for b in line) for line in lines).strip() + "\n"


def format_markdown_document(boxes: List[OCRBox], width: int = 1080, height: int = 12000, config: Optional[OCRConfig] = None) -> str:
    return build_markdown(boxes, config)


def format_plain_text(boxes: List[OCRBox], config: Optional[OCRConfig] = None) -> str:
    return build_plain_text(boxes, config)
