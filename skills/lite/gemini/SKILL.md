---
name: long-image-ocr-lite
description: Use when reading, transcribing, extracting, or verifying long screenshots, dense document images, tables, transaction histories, receipts, chats, logs, or other OCR-sensitive visual content.
---

# LongImageOCR Lite

LongImageOCR Lite is an **instruction-only, evidence-only** native-vision protocol for Gemini. Use Gemini's native vision. Do not invoke or claim to invoke an external OCR engine, Python process, MCP server, API, Cloud Run service, local executable, or LongImageOCR Full.

## 0. Evidence gate

Every character, number, date, transaction, product, row, field, and record must be supported by visible source evidence.

- **Reconstruction is not completion.** Never fill gaps to make a sequence look complete.
- **Recurring purchase patterns are not evidence.** Never invent missing rows, dates, amounts, payment methods, discounts, quantities, or products from repetition.
- **Missing evidence must remain missing.** Use `[uncertain: ...]`, `[uncertain: A | B]`, `[unreadable]`, or `[not verified]` instead of guessing.
- Confirm that each structured row is visibly present and that each value belongs to that row.
- Never create a missing row or populate a field from contextual expectation.

## 0A. Source modality gate — critical for Drive/Workspace

Before reading an image file, determine whether Gemini actually has access to the **image pixels** or only file metadata, Drive/workspace **indexed text**, OCR snippets, or extracted text.

- When image pixels are available, inspect the image itself using native vision.
- Indexed text is **supplementary evidence** only. It must not replace direct visual inspection.
- If only indexed text/metadata is available, mark the source `[image not visually verified]`; do not claim that OCR or visual inspection was completed.
- **Empty indexed text does not mean the image is unreadable.** If image pixels are available, inspect them directly.
- Do not call a file processed merely because Gemini found its metadata or extracted snippet.
- Do not claim crop, zoom, enhancement, or reinspection unless Gemini actually performed that operation.

## 0B. Source coverage gate

For multi-image or multi-page tasks, maintain an internal **source coverage** checklist. **Every provided image**, page, screenshot, or accessible source region must be inspected before claiming completion.

- Do not stop after the first readable subset.
- Do not skip files because they resemble previous files.
- Do not skip visual inspection because Drive already exposes text.
- Do not silently omit files with empty indexed text.
- Complete source inspection is required; inferred completion is forbidden.

## Phase 1 — Layout reconnaissance

Inspect the whole source for headings, sections, tables, columns, cards, repeated rows, transaction groups, chat/log blocks, timelines, and dense regions. Establish visible top-to-bottom order for long screenshots.

## Phase 2 — Segmented reading

Read long or dense sources in ordered logical regions from top to bottom. Prefer semantic boundaries such as whitespace, section changes, table blocks, cards, or row groups. If a material region cannot be reliably inspected, mark it `[not verified]` instead of reconstructing it.

## Phase 3 — Boundary reconciliation

At every region or consecutive-screenshot boundary, check for split rows, repeated headers, truncated values, skipped transitions, and overlap duplicates. Remove only duplicates caused by overlap. Preserve genuine repeated transactions that are visibly distinct.

## Phase 4 — Precision pass

Recheck dates, timestamps, currency amounts, prices, counts, quantities, percentages, tickers, identifiers, and row/column associations. Never choose between conflicting digits by intuition. If unresolved, report the alternatives as uncertain.

## Phase 5 — Low-confidence pass

Treat tiny text, blur, compression, low contrast, clipped rows, overlays, and look-alike characters as low-confidence signals. Revisit them using only Gemini capabilities that actually exist. Do not guess unreadable characters.

## Phase 6 — Reconstruction

Reassemble only information already observed from the source. Preserve source order, chronology, table relationships, record grouping, and legitimate repetition. Do not generate data to make the result look complete.

## Phase 7 — Audit

Before answering, check source coverage, overlap duplicates, missing rows, numeric transcription, row/column shifts, uncertainty, and whether every record can be traced to visible evidence. Remove any record that cannot be traced.

## Task completion rule

Do not stop at a verification report when the user requested extraction, a table, a ledger, a spreadsheet, or another artifact. **Verification is a gate, not the deliverable** unless the user explicitly asked only for verification. After checking the evidence, **continue to the requested deliverable**.

## Structured output safety

For tables, ledgers, CSV, and spreadsheets:

- preserve **field boundaries**;
- never serialize rows by blindly joining fields with a comma;
- in **CSV**, **quote** and escape any field containing a **comma**, quote, or newline;
- in a spreadsheet, write each value to its own native cell;
- verify that commas inside product names, currency text, notes, or filenames did not shift later columns.

## Summary and aggregation rule

Any summary, total, count, monthly rollup, or yearly rollup must be **recomputed from the final structured rows**. Use an explicit **include/exclude** decision for duplicates, cancellations, top-ups/funding rows, free/zero-value records, or other non-counted evidence. Cross-check the summary against the detailed rows before returning it.

## Operating modes

### Auto mode
Use by default. For long, dense, repetitive, tabular, financial, or precision-sensitive sources, apply the full protocol.

### Exact transcription mode
Preserve visible wording and order. Do not silently autocorrect or summarize unless asked. Mark uncertainty explicitly.

### Structured extraction mode
Verify every row independently, preserve row/column associations, never move values between rows, never create missing rows, preserve genuine duplicates, and normalize only when requested.

## Response behavior

Apply the protocol silently unless the user asks about methodology. Return the requested result directly. Never claim `complete`, `all records`, `fully verified`, or `nothing missing` unless every material accessible source was visually inspected and the evidence supports that claim. Visible evidence beats plausibility; uncertainty beats guessing; missing evidence beats invented data.
