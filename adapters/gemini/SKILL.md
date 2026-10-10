---
name: long-image-ocr
description: Process ultra-long vertical screenshots, chats, and documents using native-resolution smart-tiling OCR without downscaling.
---

# LongImageOCR Skill for Gemini Agent / Antigravity

When a user presents a screenshot, document, or capture that is vertically long:
- Dimension rule: `height > 4000px` OR `aspect_ratio (height/width) > 3.0`
- Content rule: Mobile scroll captures, continuous chat logs, stock charts with tables, webpage screenshots

## Critical Rule
**NEVER pass the entire ultra-long image directly to vision models or attempt to downscale it.** Downscaling destroys small text, numbers, stock prices, and Korean characters.

## Recommended Action
Execute LongImageOCR via the CLI:

```bash
python -m longocr.cli "<image_path>" --mode hybrid --language ko
```

Or via MCP Server tool:
```json
{
  "name": "long_image_ocr",
  "arguments": {
    "image_path": "<image_path>",
    "mode": "hybrid",
    "language": "ko"
  }
}
```

## Reading Results
1. Primary reconstructed Markdown: `<output_dir>/output.md`
2. Audit report for low-confidence regions: `<output_dir>/audit.md`
3. If `<output_dir>/audit.md` lists low-confidence crops, inspect `<output_dir>/low_confidence/crop_*.png` to verify ambiguous numbers or words before answering.
