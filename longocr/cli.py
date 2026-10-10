"""Command-line interface for LongImageOCR."""

import os
import sys
import glob
import logging
import argparse
from typing import List

from .config import OCRConfig
from .pipeline import LongImageOCRPipeline


def setup_logger(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] %(levelname)s [%(name)s]: %(message)s",
        datefmt="%H:%M:%S"
    )


def collect_image_files(target_path: str) -> List[str]:
    """Collects target image file or all image files in a directory."""
    target_path = os.path.abspath(target_path)
    if os.path.isfile(target_path):
        return [target_path]

    if os.path.isdir(target_path):
        extensions = ("*.png", "*.jpg", "*.jpeg", "*.webp", "*.bmp")
        files = []
        for ext in extensions:
            files.extend(glob.glob(os.path.join(target_path, ext)))
            files.extend(glob.glob(os.path.join(target_path, ext.upper())))
        return sorted(list(set(files)))

    matched = glob.glob(target_path)
    if matched:
        return sorted(matched)

    return []


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="longocr",
        description="LongImageOCR — Multi-AI Shared Ultra-Long Screenshot OCR Tool."
    )
    parser.add_argument("target", help="Path to an image file or directory containing images.")
    parser.add_argument("--output", "-o", default=None, help="Directory to save OCR outputs (default: ./ocr_output/<image_name>.)")
    parser.add_argument("--mode", "-m", choices=["fast", "accurate", "hybrid"], default="hybrid", help="OCR execution mode (default: hybrid).")
    parser.add_argument("--language", "-l", default="ko", help="Target language code: 'ko', 'en', etc. (default: ko).")
    parser.add_argument("--tile-height", type=int, default=2200, help="Target height of each tile in pixels (default: 2200).")
    parser.add_argument("--overlap", type=int, default=220, help="Overlap buffer between adjacent tiles in pixels (default: 220).")
    parser.add_argument("--confidence", type=float, default=0.75, help="Confidence threshold for low-confidence audit and retry (default: 0.75).")
    parser.add_argument("--no-cache", action="store_true", help="Disable resume cache and re-process all tiles.")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable detailed debug logs.")

    args = parser.parse_args()
    setup_logger(args.verbose)
    logger = logging.getLogger("longocr.cli")

    image_files = collect_image_files(args.target)
    if not image_files:
        logger.error(f"No valid image files found at: {args.target}")
        return 1

    config = OCRConfig(
        mode=args.mode,
        language=args.language,
        tile_height=args.tile_height,
        overlap=args.overlap,
        confidence_threshold=args.confidence,
        enable_cache=not args.no_cache
    )

    logger.info(f"Initializing LongImageOCR Pipeline (mode: {config.mode}, lang: {config.language})...")
    pipeline = LongImageOCRPipeline(config=config)
    logger.info(f"Processing {len(image_files)} image(s)...")

    for idx, img_path in enumerate(image_files, start=1):
        logger.info(f"[{idx}/{len(image_files)}] Processing: {img_path}")
        if len(image_files) > 1 and args.output:
            subname = os.path.splitext(os.path.basename(img_path))[0]
            out_dir = os.path.join(args.output, subname)
        else:
            out_dir = args.output

        try:
            result = pipeline.process(img_path, output_dir=out_dir)
            logger.info(
                f"Successfully completed '{os.path.basename(img_path)}' in {result.elapsed_seconds:.2f}s | "
                f"Tiles: {result.total_tiles} | Lines: {result.total_boxes} | "
                f"Audit required: {result.audit_required}"
            )
            logger.info(f"Output saved to: {result.output_dir}")
        except Exception as e:
            logger.error(f"Failed to process '{img_path}': {e}", exc_info=args.verbose)

    return 0


if __name__ == "__main__":
    sys.exit(main())
