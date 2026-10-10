"""Audit report generation for low confidence detections and overlap merges."""

import os
from typing import List, Dict, Any, Optional
from .engines.base import OCRBox
from .splitter import TileInfo
from .config import OCRConfig


def generate_audit_report(
    boxes: List[OCRBox],
    tiles: Optional[List[TileInfo]] = None,
    merges_audit: Optional[List[dict]] = None,
    config: Optional[OCRConfig] = None,
    image_name: str = "image",
    **kwargs
) -> str:
    """Generates a structured audit.md markdown report detailing low confidence boxes and merges."""
    tiles = tiles or []
    merges_audit = merges_audit or []
    if config is None:
        threshold = kwargs.get("confidence_threshold", 0.75)
        config = OCRConfig(confidence_threshold=threshold)

    low_conf_boxes = [b for b in boxes if b.confidence < config.confidence_threshold]
    retried_boxes = [b for b in boxes if b.retry]
    avg_conf = sum(b.confidence for b in boxes) / len(boxes) if boxes else 0.0

    lines: List[str] = [
        f"# LongImageOCR Audit Report — {image_name}\n",
        "## Summary",
        f"- **Total Tiles**: {len(tiles)}",
        f"- **Total Recognized Text Elements**: {len(boxes)}",
        f"- **Average Confidence**: {avg_conf:.3f}",
        f"- **Confidence Threshold**: {config.confidence_threshold}",
        f"- **Low Confidence Elements**: {len(low_conf_boxes)}",
        f"- **Retried Elements**: {len(retried_boxes)}",
        f"- **Overlap Merges**: {len(merges_audit)}\n",
    ]

    lines.append("## Low Confidence Elements (< 0.75)")
    if not low_conf_boxes:
        lines.append("No elements below confidence threshold. All recognitions passed quality check.\n")
    else:
        lines.append("| Tile | Global Y | Text | Confidence | Crop Path |")
        lines.append("| :--- | :--- | :--- | :--- | :--- |")
        for b in low_conf_boxes:
            crop_link = f"`{b.crop_path}`" if b.crop_path else "N/A"
            lines.append(f"| Tile {b.tile} | y={round(b.y1)} | `{b.text}` | **{b.confidence:.3f}** | {crop_link} |")
        lines.append("")

    lines.append("## Native-Resolution Retries")
    if not retried_boxes:
        lines.append("No retries triggered.\n")
    else:
        lines.append("| Tile | Global Y | Final Text | Final Confidence | Variant Used |")
        lines.append("| :--- | :--- | :--- | :--- | :--- |")
        for b in retried_boxes:
            lines.append(f"| Tile {b.tile} | y={round(b.y1)} | `{b.text}` | {b.confidence:.3f} | `{b.retry_variant}` |")
        lines.append("")

    lines.append("## Overlap Deduplication Merges")
    if not merges_audit:
        lines.append("No overlapping duplicate elements encountered.\n")
    else:
        lines.append("| Global Y | Kept Text (Tile / Conf) | Suppressed Text (Tile / Conf) |")
        lines.append("| :--- | :--- | :--- |")
        for m in merges_audit:
            lines.append(
                f"| y={m['global_y']} | `{m['winner_text']}` (T{m['winner_tile']} / {m['winner_conf']:.3f}) | "
                f"`{m['loser_text']}` (T{m['loser_tile']} / {m['loser_conf']:.3f}) |"
            )
        lines.append("")

    return "\n".join(lines)
