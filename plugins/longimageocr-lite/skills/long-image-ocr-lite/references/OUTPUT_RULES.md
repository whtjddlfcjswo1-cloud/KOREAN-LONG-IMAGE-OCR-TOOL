# LongImageOCR Lite Output Rules

## Auto mode

Use this by default. For ordinary readable images, avoid unnecessary ceremony. For long, dense, repetitive, tabular, or precision-sensitive images, apply the full seven-phase LongImageOCR Lite policy before answering.

Return the format the user asked for. If they did not specify a format, preserve the most useful visible structure.

## Exact transcription mode

Use when the user asks to read, transcribe, OCR, copy, or reproduce visible text faithfully.

- Preserve source order and wording.
- Do not silently autocorrect names, numbers, dates, or identifiers.
- Represent material unresolved text as `[uncertain: ...]` or `[unreadable]`.
- If two readings remain plausible, use `[uncertain: A | B]`.
- Add a short `Uncertainty notes` section only when unresolved ambiguity materially affects the requested result.

## Structured extraction mode

Use for tables, transaction histories, receipts, schedules, logs, lists, and repeated records.

- Preserve row/column and record associations.
- Do not move a value to a neighboring row because it appears semantically likely.
- Preserve repeated source rows unless the policy establishes that they are overlap-created duplicates.
- Normalize field names, currencies, timestamps, or schemas only when the user requests normalization or when doing so is necessary to satisfy the requested output format.
- Mark uncertain cells or fields explicitly rather than guessing.

## Precision-sensitive output

Dates, currency, counts, percentages, tickers, identifiers, and row/column associations must reflect the precision pass from the core policy. If a value cannot be verified from the visible image, say so.

## Runtime boundary

No external OCR runtime is required. These rules assume native vision only and must not require Python, Docker, MCP, a remote OCR service, an API key, or LongImageOCR Full to complete the user's request.
