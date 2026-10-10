# LongImageOCR Lite Output Rules

## Auto mode

Use by default. For ordinary readable images, avoid unnecessary ceremony. For long, dense, repetitive, tabular, financial, or precision-sensitive sources, apply the full seven-phase policy before answering.

Return the format the user asked for. If no format was specified, preserve the most useful visible structure.

## Exact transcription mode

Use when the user asks to read, transcribe, OCR, copy, or reproduce visible text faithfully.

- Preserve source order and wording.
- Do not silently autocorrect names, numbers, dates, or identifiers.
- Use `[uncertain: ...]`, `[uncertain: A | B]`, `[unreadable]`, or `[not verified]` where needed.
- Do not claim a source was read if only metadata or indexed text was available.

## Structured extraction mode

Use for tables, transaction histories, receipts, schedules, logs, lists, and repeated records.

For every output row or record:

1. Confirm that the row is visibly present.
2. Confirm each value belongs to that row.
3. Do not move values from neighboring rows.
4. Do not populate a field from contextual expectation.
5. Never create a missing row to make a sequence complete.
6. Preserve legitimate repeated rows while removing only overlap-created duplicates.
7. Mark uncertain cells individually rather than guessing.

**Recurring purchase patterns are not evidence. Missing evidence must remain missing.**

## Source coverage output

For multi-source work, inspect **every provided image** or page before claiming completion. Do not stop after the readable subset. If a source could not be visually inspected, state that limitation rather than silently omitting it.

## Task completion

Do not substitute a methodology report, verification note, or source-status checklist for the output the user requested. **Verification is a gate, not the deliverable** unless the user asked only for verification. After checking the evidence, **continue to the requested deliverable**.

## Structured serialization safety

When producing CSV, TSV, spreadsheets, JSON, or other structured artifacts, preserve **field boundaries** exactly.

- Never build CSV by naively joining fields with a comma.
- In CSV, **quote** and escape fields containing a **comma**, quote, or newline according to normal CSV rules.
- In spreadsheets, place each field in its own native cell instead of serializing rows into comma-separated text first.
- Validate that delimiter characters inside product names, currency strings, notes, and filenames did not shift later columns.

## Summary and aggregation rule

Any summary, total, count, monthly rollup, yearly rollup, or derived statistic must be **recomputed from the final structured rows**, not independently invented or copied from an earlier draft.

Use an explicit **include/exclude** decision for rows such as duplicates, cancellations, funding/top-up transactions, free/zero-value records, and other non-counted evidence. Then recompute totals and counts from the included rows and cross-check them against the detailed table.

If a summary disagrees with the final detailed rows, the detailed evidence-backed rows take precedence until the aggregation is fixed.

## Precision-sensitive output

Dates, currency, counts, percentages, tickers, identifiers, and row/column associations must reflect the precision pass. If a value cannot be verified from the visible image, say so.

## Completeness rule

Do not claim `complete`, `all records`, `fully verified`, or `nothing missing` unless every material accessible source has been visually inspected and the evidence supports the claim. **Reconstruction is not completion.**

## Runtime boundary

No external OCR runtime is required. These rules assume native vision only and must not require Python, Docker, MCP, a remote OCR service, an API key, or LongImageOCR Full to complete the user's request.
