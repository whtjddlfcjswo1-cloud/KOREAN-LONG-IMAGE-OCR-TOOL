---
name: long-image-ocr-lite
description: Use when reading, transcribing, extracting, or verifying long screenshots, dense document images, tables, transaction histories, receipts, chats, logs, or other OCR-sensitive visual content.
---

# LongImageOCR Lite

LongImageOCR Lite is an **instruction-only, evidence-only** native-vision protocol. Use Gemini's **native vision** to read OCR-sensitive images more systematically. Do not invoke or claim to invoke an external OCR engine, Python process, MCP server, API, Cloud Run service, local executable, or LongImageOCR Full.

## Non-negotiable evidence rules

Every character, number, date, product, transaction, row, field, and record in the output must be directly supported by visible source evidence.

- **Reconstruction is not completion.** Reorder and format only content already observed; never fill gaps to make a sequence look complete.
- **Recurring purchase patterns are not evidence.** Never invent a transaction, date, price, payment method, product, discount, quantity, or row because similar records appear elsewhere.
- **Missing evidence must remain missing.** Use `[uncertain: ...]`, `[uncertain: A | B]`, `[unreadable]`, or `[not verified]` instead of guessing.
- For structured data, **confirm that the row is visibly present** before extracting it, then confirm each value belongs to that row.
- **Never create a missing row.** Do not populate a field from contextual expectation or from a neighboring record.
- A partially verified result is preferable to a fabricated complete result.

## Phase 1 — Layout reconnaissance

Inspect the whole image before extracting details. Identify visible headings, sections, tables, columns, cards, repeated rows, transaction groups, chat/log blocks, timelines, and dense regions. For a long screenshot, establish the visible top-to-bottom order. Do not assume unreadable or unseen regions contain expected content.

## Phase 2 — Segmented reading

Read long or dense images in ordered logical regions from top to bottom, preferring semantic boundaries such as whitespace, section changes, table blocks, card groups, row groups, or paragraph boundaries.

Use crop, zoom, enhancement, or region reinspection only if Gemini actually exposes and performs that operation. **Do not claim** that a crop, zoom, enhancement, or reinspection occurred when it did not. If a material region cannot be reliably inspected, mark it `[not verified]` rather than reconstructing it.

## Phase 3 — Boundary reconciliation

At each region transition, check for split sentences, split rows, duplicated overlap text, skipped rows, repeated headers, missing transitions, truncated numbers, and values cut at region edges. Remove only duplicates introduced by repeated inspection or overlap. Preserve legitimate repeated source content.

## Phase 4 — Precision pass

Recheck values where one character can materially change meaning: dates, timestamps, currency amounts, prices, counts, quantities, percentages, tickers, identifiers, reference numbers, and table row/column associations.

Never choose between conflicting digits by intuition. If a value could be `1,234,500` or `1,234,800`, reinspect the visible evidence when possible; otherwise return `[uncertain: 1,234,500 | 1,234,800]`.

## Phase 5 — Low-confidence pass

Treat tiny text, blur, compression, low contrast, clipped rows, overlapping UI, unusual fonts, and look-alike characters such as `0/O`, `1/I/l`, `5/S`, `6/8`, and `8/B` as low-confidence signals. Revisit them using only image-inspection capabilities Gemini actually provides. **Do not guess** unreadable characters.

## Phase 6 — Reconstruction

Reassemble only information already observed from the source. Preserve visible source order, headings, chronology, table rows/columns, transaction groups, speakers, message order, log order, and record associations. Do not normalize or rewrite values unless the user requests it. Do not generate data to make the result appear more complete.

## Phase 7 — Audit

Before answering, perform a final evidence audit:

- Did every row actually exist in the source?
- Did every value come from visible evidence?
- Was any field inferred from a neighboring row?
- Was any transaction invented from a repeating pattern?
- Were missing dates or months filled automatically?
- Were duplicates introduced or rows lost at boundaries?
- Are numbers still attached to the correct record and column?
- Are uncertain or unverified areas marked explicitly?

Trace each structured record back to visible evidence. If a record cannot be traced to visible evidence, remove it from the output.

## Operating modes

### Auto mode
Use by default. For short, clearly readable images, answer normally. For long, dense, repetitive, tabular, financial, or precision-sensitive images, apply the complete protocol.

### Exact transcription mode
Use when the user asks to read everything, OCR, transcribe, copy visible text, or reproduce the source faithfully. Preserve visible wording and order, do not silently autocorrect, do not summarize unless asked, and mark uncertainty explicitly.

### Structured extraction mode
Use for tables, receipts, transaction histories, schedules, financial records, logs, lists, and repeated records. Verify every row independently; preserve row/column and record associations; never move values between rows; never create missing rows; preserve genuine duplicates; normalize only when requested.

## Response behavior

Apply this protocol silently unless the user asks how the image was analyzed. Return the requested result directly. Never claim `complete`, `all records`, `fully verified`, or `nothing missing` unless the visible source supports that claim. For financial, numerical, historical, transaction, or tabular data, correctness is more important than fluency: visible evidence beats plausibility, uncertainty beats guessing, and missing evidence beats invented data.
