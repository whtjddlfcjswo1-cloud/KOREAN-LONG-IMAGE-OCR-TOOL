---
name: long-image-ocr-lite
description: Improve reading of long screenshots, dense documents, tables, and OCR-sensitive images using a disciplined native-vision inspection workflow without an external OCR server.
---

# LongImageOCR Lite

Use this skill when the user asks you to read, transcribe, extract, verify, or summarize text from a long screenshot, dense document image, table, payment history, chat/log capture, or other OCR-sensitive image.

LongImageOCR Lite is a **skill-only native-vision workflow**. It does not invoke LongImageOCR Full or any external OCR runtime.

## Required workflow

Apply the canonical **seven-phase** protocol in `references/CORE_POLICY.md`:

1. Phase 1 — Layout reconnaissance
2. Phase 2 — Segmented reading
3. Phase 3 — Boundary reconciliation
4. Phase 4 — Precision pass
5. Phase 5 — Low-confidence pass
6. Phase 6 — Reconstruction
7. Phase 7 — Audit

Then follow `references/OUTPUT_RULES.md` to select Auto mode, Exact transcription mode, or Structured extraction mode from the user's request.

## Capability boundary

Use only image understanding and inspection operations that the current host actually exposes. Do not claim that you cropped, zoomed, enhanced, or reinspected an image region unless that operation really occurred.

Never invent unreadable values. Recheck dates, currency, quantities, percentages, tickers, identifiers, and table associations. If a material ambiguity remains, mark it as uncertain and return the best supported result.

## Response behavior

Do not narrate the seven phases unless the user asks how the image was read. Apply them silently and answer in the format requested by the user.
