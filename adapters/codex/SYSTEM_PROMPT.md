# OpenAI Codex / ChatGPT Integration Guide for LongImageOCR

## Directive
When receiving an image file where:
- The image is tall/vertical (e.g. mobile screenshots, long chat threads, GitHub Action logs, financial tables)
- Height exceeds 4000px or aspect ratio (H/W) exceeds 3.0:

DO NOT attempt to read the entire image directly through multimodal vision prompts, as token limits and downscaling will hallucinate or skip small text and numbers.

Always invoke the `long_image_ocr` tool:
```json
{
  "image_path": "path/to/screenshot.png",
  "mode": "hybrid",
  "language": "ko"
}
```

Then read the returned `markdown` field to reason about the user's inquiry.
If `audit_required` is true, check ambiguous items noted in `audit.md` before finalizing financial or code outputs.
