# LongImageOCR Guide for Claude Code & Claude Desktop

This guide instructs Claude Code and Claude Desktop on how to handle ultra-long vertical screenshots and tall documents efficiently using the LongImageOCR MCP tools.

---

## 1. Operating Rules for Long Screenshots

1. **Never Feed Raw Long Screenshots to Vision**:
   - Ultra-tall screenshots (height > 4000px or aspect ratio > 3.0) will be heavily downscaled by AI vision frontends, resulting in severe character blur and loss of numbers/tickers.
   - Always route tall images through the `long_image_ocr` MCP tool.

2. **Preventing Context Window Flooding**:
   - By default, `long_image_ocr` returns a compact preview (`preview`) alongside saved artifact paths (`output.md`, `output.txt`, `ocr.json`, `manifest.json`, `audit.md`).
   - Leave `return_full_text=false` when calling `long_image_ocr`.
   - Read specific sections using `read_ocr_output(output_dir=..., offset=..., limit=...)`.

3. **Global Coordinates & Region Inspection**:
   - Every detected box preserves full global Y coordinates relative to the original image canvas.
   - If a specific chart, header, or table region requires targeted verification, call `inspect_ocr_region(image_path=..., y_start=..., y_end=...)`.

---

## 2. Available MCP Tools

| Tool Name | Parameters | Description |
| :--- | :--- | :--- |
| `long_image_ocr` | `image_path`, `mode="hybrid"`, `language="ko"`, `return_full_text=false` | Processes long image via smart low-density tiling, overlap deduplication, and document reconstruction (default mode: `hybrid`). |
| `read_ocr_output` | `output_dir`, `format="markdown"`, `offset=0`, `limit=4000` | Paginated retrieval of large OCR output documents. |
| `inspect_ocr_region` | `image_path`, `y_start`, `y_end`, `language="ko"` | Crops a vertical slice and performs OCR with global Y offsets preserved. |
| `ocr_status` | `output_dir` | Returns manifest metadata and audit preview for a completed OCR job. |

---

## 3. CLI Fallback Instructions

If MCP is not configured in the host environment, execute directly via shell:

```bash
# Standard hybrid execution
longocr path/to/image.png --mode hybrid --out-dir ./ocr_output

# Fast execution (pure ONNX without retry)
longocr path/to/image.png --mode fast --out-dir ./ocr_output

# Accurate execution with PaddleOCR
longocr path/to/image.png --mode accurate --out-dir ./ocr_output

# Python module invocation (default mode: hybrid)
python -m longocr.cli path/to/image.png --mode hybrid
```

---

## 4. MCP Server Registration

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "longimageocr": {
      "command": "longocr-mcp",
      "args": [],
      "env": {
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1"
      }
    }
  }
}
```
