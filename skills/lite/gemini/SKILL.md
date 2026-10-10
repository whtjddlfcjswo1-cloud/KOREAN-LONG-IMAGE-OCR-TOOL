# LongImageOCR Lite — Gemini Workspace Studio Skill

LongImageOCR Lite is an **instruction-only** OCR-improvement skill. Use Gemini's **native vision** to inspect long screenshots, dense documents, tables, transaction histories, chats, logs, and other OCR-sensitive images more systematically.

Do not invoke an external OCR engine. Do not assume access to a local path, remote service, or hidden image-processing operation.

## Phase 1 — Layout reconnaissance

Inspect the image as a whole first. Identify major sections, tables, cards, columns, repeated rows, timelines, and dense regions before attempting full transcription.

## Phase 2 — Segmented reading

Read long or dense images in ordered logical regions from top to bottom. Prefer semantic boundaries such as whitespace, section changes, table blocks, or card groups.

Only use crop, zoom, or region reinspection when Gemini actually provides and performs that operation. **Do not claim** that a crop, zoom, enhancement, or reinspection happened when it did not actually happen.

## Phase 3 — Boundary reconciliation

At every region transition, check for split sentences, duplicated overlap text, skipped rows, repeated headers, and truncated edge values. Remove only overlap-created duplicates; preserve legitimate repeated source content.

## Phase 4 — Precision pass

Recheck dates, times, currency amounts, prices, quantities, percentages, tickers, identifiers, and table row/column associations. Never choose between conflicting digits by intuition alone.

## Phase 5 — Low-confidence pass

Revisit tiny, blurred, compressed, low-contrast, clipped, or visually ambiguous text. If material ambiguity remains, mark it as uncertain instead of guessing.

## Phase 6 — Reconstruction

Reassemble the result in source order. Preserve headings, chronology, table structure, transaction groups, speakers, and record associations when visible.

## Phase 7 — Audit

Before answering, check for duplicated text, missing transitions, suspicious numbers, row/column shifts, arithmetic inconsistencies visible in the image, and unresolved uncertainty.

## Operating modes

- **Auto mode:** default; use the full protocol when image length, density, repetition, tables, or precision risk warrants it.
- **Exact transcription mode:** preserve visible wording/order and mark unreadable or uncertain material explicitly.
- **Structured extraction mode:** preserve record and row/column relationships; normalize only when the user requests it.

## Response rule

Apply the workflow silently unless the user asks for methodology. Return the requested result directly. Never imply that LongImageOCR Full or an external OCR backend was used.
