---
name: long-image-ocr-lite
description: Use when reading, transcribing, extracting, or verifying long screenshots, dense document images, tables, transaction histories, receipts, chats, logs, or other OCR-sensitive visual content.
---

# LongImageOCR Lite

LongImageOCR Lite is an **instruction-only, evidence-only native-vision workflow**. It does not invoke LongImageOCR Full or any external OCR runtime.

## Critical gates

Before the seven-phase workflow:

- Every extracted row, field, number, date, product, transaction, or record must be supported by visible source evidence.
- **Reconstruction is not completion.** Never fill gaps to make a sequence look complete.
- **Recurring purchase patterns are not evidence.** Never create missing records from repetition or contextual expectation.
- **Missing evidence must remain missing.** Mark uncertainty rather than guessing.
- Distinguish actual **image pixels** from metadata, connector/workspace **indexed text**, OCR snippets, or extracted text. Indexed text is **supplementary evidence** only when pixels are available.
- **Empty indexed text does not mean the image is unreadable.** If only text/metadata is available, mark `[image not visually verified]` and do not claim visual OCR was completed.
- For multi-source work, maintain **source coverage**: inspect **every provided image** or accessible page before claiming completion. Do not stop after a readable subset.

## Required workflow

Apply the canonical policy in `references/CORE_POLICY.md`:

1. Phase 1 — Layout reconnaissance
2. Phase 2 — Segmented reading
3. Phase 3 — Boundary reconciliation
4. Phase 4 — Precision pass
5. Phase 5 — Low-confidence pass
6. Phase 6 — Reconstruction
7. Phase 7 — Audit

Then follow `references/OUTPUT_RULES.md` for Auto, Exact transcription, or Structured extraction mode.

## Deliverable rule

Do not replace the user's requested output with a verification/methodology report. **Verification is a gate, not the deliverable** unless the user explicitly asks only for verification. After checking evidence, **continue to the requested deliverable**.

For structured artifacts, preserve **field boundaries**. Never create CSV by blindly joining fields with a comma; **quote** fields containing a **comma**, quote, or newline, and use native spreadsheet cells when creating a workbook.

Any total or **summary** must be **recomputed from the final structured rows** using an explicit **include/exclude** decision for duplicates, cancellations, funding/top-up records, and free/zero-value rows.

## Capability boundary

Use only image understanding and inspection operations the current host actually exposes. Do not claim crop, zoom, enhancement, or reinspection unless it really occurred. Never invent unreadable values.

## Response behavior

Apply the workflow silently unless the user asks how the image was read. Answer in the requested format and state material source limitations when present.
