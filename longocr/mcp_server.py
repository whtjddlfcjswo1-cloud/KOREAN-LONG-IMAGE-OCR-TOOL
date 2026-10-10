"""Official Model Context Protocol (MCP) Server for LongImageOCR.

Provides stdio JSON-RPC 2.0 integration for Claude Desktop, Claude Code, Gemini CLI,
and OpenAI Codex, featuring paginated large-output delivery and global coordinate preservation.
"""

import sys
import os
import json
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from PIL import Image

from .config import OCRConfig
from .pipeline import LongImageOCRPipeline

logger = logging.getLogger("longocr.mcp_server")

try:
    from mcp.server import MCPServer
    mcp_app = MCPServer("longimageocr-mcp")
except (ImportError, Exception):
    try:
        from mcp.server.mcpserver import MCPServer
        mcp_app = MCPServer("longimageocr-mcp")
    except Exception as e:
        mcp_app = None
        logger.error(f"Failed to load official MCP SDK: {e}")


def register_tools(app):
    @app.tool()
    def long_image_ocr(
        image_path: str,
        mode: str = "hybrid",
        language: str = "ko",
        tile_height: int = 2200,
        output_dir: Optional[str] = None,
        return_full_text: bool = False
    ) -> str:
        """Performs native-resolution smart-tiling OCR on ultra-long screenshots."""
        config = OCRConfig(mode=mode, language=language, tile_height=tile_height)
        pipeline = LongImageOCRPipeline(config=config)
        resolved_img = os.path.abspath(image_path)
        if not os.path.exists(resolved_img):
            raise FileNotFoundError(f"Image not found at: {image_path}")

        result = pipeline.process(resolved_img, output_dir=output_dir)
        preview_text = result.markdown[:1200] if len(result.markdown) > 1200 else result.markdown
        if len(result.markdown) > 1200:
            preview_text += f"\n\n... [Truncated: {len(result.markdown) - 1200} characters omitted. Use read_ocr_output tool for full paginated content] ..."

        out_path = result.output_dir or os.path.splitext(resolved_img)[0] + "_ocr"
        response_payload = {
            "image": resolved_img,
            "total_tiles": result.total_tiles,
            "total_boxes": result.total_boxes,
            "elapsed_seconds": round(result.elapsed_seconds, 2),
            "output_directory": out_path,
            "markdown_file": os.path.join(out_path, "output.md"),
            "text_file": os.path.join(out_path, "output.txt"),
            "manifest_file": os.path.join(out_path, "manifest.json"),
            "audit_file": os.path.join(out_path, "audit.md") if result.audit_required else None,
            "audit_required": result.audit_required,
            "engine": result.manifest.get("engine", "unknown"),
            "engine_fallback": result.manifest.get("engine_fallback", False),
            "preview": preview_text,
            "total_chars": len(result.markdown)
        }
        if return_full_text:
            response_payload["markdown"] = result.markdown
        return json.dumps(response_payload, ensure_ascii=False, indent=2)

    @app.tool()
    def read_ocr_output(output_dir: str, format: str = "markdown", offset: int = 0, limit: int = 4000) -> str:
        """Reads paginated output content from a completed OCR directory."""
        filename_map = {"markdown": "output.md", "text": "output.txt", "json": "ocr.json"}
        target_name = filename_map.get(format.lower(), "output.md")
        target_file = os.path.join(output_dir, target_name)
        if not os.path.exists(target_file):
            raise FileNotFoundError(f"Requested output file not found: {target_file}")
        with open(target_file, "r", encoding="utf-8") as f:
            content = f.read()
        total_len = len(content)
        start = max(0, min(offset, total_len))
        end = min(start + limit, total_len)
        response = {
            "output_dir": output_dir,
            "file": target_file,
            "offset": start,
            "limit": limit,
            "total_chars": total_len,
            "has_more": end < total_len,
            "next_offset": end if end < total_len else None,
            "content": content[start:end]
        }
        return json.dumps(response, ensure_ascii=False, indent=2)

    @app.tool()
    def inspect_ocr_region(image_path: str, y_start: int, y_end: int, language: str = "ko") -> str:
        """Inspects a specific vertical coordinate slice with native-resolution global coordinate restoration."""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        img = Image.open(image_path)
        w, h = img.size
        y1 = max(0, min(y_start, h))
        y2 = max(0, min(y_end, h))
        if y2 <= y1:
            raise ValueError(f"Invalid region bounds: y_end ({y_end}) must be greater than y_start ({y_start}).")
        crop = img.crop((0, y1, w, y2))
        config = OCRConfig(mode="hybrid", language=language, enable_cache=False)
        pipeline = LongImageOCRPipeline(config=config)
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = pipeline.process(crop, output_dir=tmp_dir)
            for box in result.boxes:
                base_pts = box.bbox_global if box.bbox_global else box.bbox_local
                box.bbox_global = [[float(pt[0]), float(pt[1]) + y1] for pt in base_pts]
            res_data = {
                "region": {"y_start": y1, "y_end": y2, "width": w, "height": y2 - y1},
                "total_boxes": len(result.boxes),
                "total_tiles_in_region": result.total_tiles,
                "boxes": [b.to_dict() for b in result.boxes],
                "markdown": result.markdown
            }
            return json.dumps(res_data, ensure_ascii=False, indent=2)

    @app.tool()
    def ocr_status(output_dir: str) -> str:
        """Checks manifest metadata, tile boundaries, and audit preview for a processed job."""
        manifest_path = os.path.join(output_dir, "manifest.json")
        audit_path = os.path.join(output_dir, "audit.md")
        if not os.path.exists(manifest_path):
            raise FileNotFoundError(f"Manifest not found in: {output_dir}")
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        audit_preview = ""
        if os.path.exists(audit_path):
            with open(audit_path, "r", encoding="utf-8") as f:
                audit_preview = f.read(1500)
        return json.dumps({"manifest": manifest, "audit_preview": audit_preview}, ensure_ascii=False, indent=2)


if mcp_app is not None:
    register_tools(mcp_app)


def main():
    """Entry point for `python -m longocr.mcp_server` and `longocr-mcp` CLI script."""
    import argparse
    parser = argparse.ArgumentParser(
        prog="longocr-mcp",
        description="Official Model Context Protocol (MCP) stdio server for LongImageOCR."
    )
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0a1")
    parser.parse_known_args()

    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s [longocr.mcp]: %(message)s",
        stream=sys.stderr
    )
    if mcp_app is None:
        sys.stderr.write("[ERROR] MCP SDK is not installed. Run: pip install mcp\n")
        sys.exit(1)

    logger.info("Starting LongImageOCR official MCP server over stdio...")
    mcp_app.run()


if __name__ == "__main__":
    main()
