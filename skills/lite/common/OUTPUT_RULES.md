# LongImageOCR Lite Output Rules

## Auto mode

Use this by default. For ordinary readable images, avoid unnecessary ceremony. For long, dense, repetitive, tabular, financial, or precision-sensitive images, apply the full seven-phase LongImageOCR Lite policy before answering.

Return the format the user asked for. If they did not specify a format, preserve the most useful visible structure.

## Exact transcription mode

Use when the user asks to read, transcribe, OCR, copy, or reproduce visible text faithfully.

- Preserve source order and wording.
- Do not silently autocorrect names, numbers, dates, or identifiers.
- Represent material unresolved text as `[uncertain: ...]` or `[unreadable]`.
- If two readings remain plausible, use `[uncertain: A | B]`.
- Use `[not verified]` when a material region could not actually be inspected.
- Add a short `Uncertainty notes` section only when unresolved ambiguity materially affects the requested result.

## Structured extraction mode

Use for tables, transaction histories, receipts, schedules, logs, lists, and repeated records.

For every output row or record:

1. Confirm that the row is visibly present in the source.
2. Confirm each value belongs to that row.
3. Do not move a value from a neighboring row because it appears semantically likely.
4. Do not populate a field from contextual expectation.
5. Never create a missing row to make a sequence complete.
6. Preserve legitimate repeated source rows unless the policy establishes that they are overlap-created duplicates.
7. Mark uncertain cells or fields explicitly rather than guessing.

**Recurring purchase patterns are not evidence.** A transaction must not appear in the output unless visible source evidence supports that transaction. **Missing evidence must remain missing.**

Normalize field names, currencies, timestamps, or schemas only when the user requests normalization or when doing so is necessary to satisfy the requested output format.

## Precision-sensitive output

Dates, currency, counts, percentages, tickers, identifiers, and row/column associations must reflect the precision pass from the core policy. If a value cannot be verified from the visible image, say so.

## Completeness rule

Do not claim `complete`, `all records`, `fully verified`, or `nothing missing` unless the visible source actually supports that claim. **Reconstruction is not completion.** A partially verified result is better than invented data.

## Runtime boundary

No external OCR runtime is required. These rules assume native vision only and must not require Python, Docker, MCP, a remote OCR service, an API key, or LongImageOCR Full to complete the user's request.
