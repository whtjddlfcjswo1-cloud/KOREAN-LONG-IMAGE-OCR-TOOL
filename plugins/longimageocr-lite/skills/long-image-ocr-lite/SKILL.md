---
name: long-image-ocr-lite
description: Use when reading, transcribing, extracting, or verifying long screenshots, dense document images, tables, transaction histories, receipts, chats, logs, or other OCR-sensitive visual content.
---

# LongImageOCR Lite

LongImageOCR Lite is an **instruction-only, evidence-only native-vision workflow**. It does not invoke LongImageOCR Full or any external OCR runtime.

## Evidence gate

Before using the seven-phase workflow, enforce these rules:

- Every extracted row, field, number, date, product, transaction, or record must be supported by visible source evidence.
- **Reconstruction is not completion.** Never fill gaps to make a sequence look complete.
- **Recurring purchase patterns are not evidence.** Never create a missing transaction from repetition or contextual expectation.
- **Missing evidence must remain missing.** Mark uncertainty or unreadable/unverified regions instead of guessing.
- For structured data, confirm that the row is visibly present and that each value belongs to that row. **Never create a missing row.**

## Required workflow

Apply the canonical seven-phase protocol in `references/CORE_POLICY.md`:

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
