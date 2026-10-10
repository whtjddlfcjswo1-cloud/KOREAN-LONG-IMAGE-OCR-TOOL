# LongImageOCR Operating Guide for OpenAI Codex & LLM Agents

## Instructions for Agents

1. **Avoid Whole-Image Ingestion for Tall Images**:
   - Whenever an image's height exceeds 4000px or the aspect ratio (height / width) exceeds 3.0, do not pass the entire raw image directly to the vision context. Downscaling will destroy small text, numbers, and stock tickers.
   - Use the `long_image_ocr` tool discovered from the `longimageocr` MCP server.

2. **Managing Tool Responses**:
   - `long_image_ocr` returns a compact summary, preview, and output file paths (`output.md`, `output.txt`, `manifest.json`, `ocr.json`).
   - Leave `return_full_text=false` (the default) to prevent overflowing the conversational context window.
   - For reading large output documents in manageable chunks, call `read_ocr_output(output_dir=..., offset=..., limit=...)`.

3. **Inspecting Specific Sub-Regions**:
   - Call `inspect_ocr_region(image_path=..., y_start=..., y_end=...)` to perform high-resolution verification on a specific vertical band. Global Y coordinates are preserved relative to the original image.
