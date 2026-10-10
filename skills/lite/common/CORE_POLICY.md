# LongImageOCR Lite Core Policy

LongImageOCR Lite changes **how the host model inspects OCR-sensitive images**. It is an **evidence-only, instruction-only native-vision protocol**. No external OCR runtime is required; use only native vision and image-inspection capabilities the host actually provides.

## Non-negotiable evidence rules

Every extracted character, number, date, product, transaction, row, field, and record must be supported by visible source evidence.

- **Reconstruction is not completion.** Order and format only content already observed; never fill gaps.
- **Recurring purchase patterns are not evidence.** Repetition does not justify creating a missing transaction, date, price, method, product, discount, quantity, or row.
- **Missing evidence must remain missing.** Use `[uncertain: ...]`, `[uncertain: A | B]`, `[unreadable]`, or `[not verified]` instead of guessing.
- For structured data, confirm that the row is **visibly present** and that each value belongs to that row.
- **Never create a missing row** or populate a field from contextual expectation or a neighboring record.
- A partially verified result is preferable to a fabricated complete result.

## Source modality gate

For image-reading tasks, distinguish the actual **image pixels** from file metadata, Drive/workspace **indexed text**, OCR snippets, or previously extracted text.

- If image pixels are accessible, direct visual inspection is the primary evidence path.
- Indexed text is **supplementary evidence** only. It must not replace direct visual inspection when image pixels are available.
- If only metadata/indexed text is available, mark the source `[image not visually verified]`. Do not claim that the image was processed or OCR was completed.
- **Empty indexed text does not mean the image is unreadable.** It means only that no usable indexed text was returned; inspect the pixels if they are available.
- Do not claim crop, zoom, enhancement, segmentation, or reinspection unless the host actually performed that operation.

## Source coverage gate

For multi-image or multi-page work, maintain an internal **source coverage** checklist. **Every provided image**, page, screenshot, or accessible source region must be inspected before claiming the task is complete.

- Do not stop after the first readable subset.
- Do not skip a source because it resembles a previous source.
- Do not skip files merely because indexed text already exists.
- Distinguish `VISUALLY_VERIFIED`, `TEXT_ONLY_NOT_VISUALLY_VERIFIED`, `NOT_ACCESSED`, and `UNREADABLE_AFTER_VISUAL_INSPECTION` internally.
- Completeness means complete source inspection, not inference of missing content.

## Phase 1 — Layout reconnaissance

Inspect the whole source for structure before transcribing. Map headings, sections, tables, columns, cards, chat/log blocks, repeated rows, timelines, and dense regions. Establish the visible top-to-bottom order for long screenshots. Do not assume unseen or unreadable areas contain expected content.

## Phase 2 — Segmented reading

Read long or dense content in an explicit top-to-bottom sequence of logical visual regions. Prefer semantic boundaries such as whitespace, section changes, table blocks, cards, or row groups.

Use crop, zoom, or region reinspection only when the host actually exposes that capability. If a material region cannot be reliably inspected, mark it `[not verified]` rather than reconstructing it.

## Phase 3 — Boundary reconciliation

At each adjacent region or screenshot boundary, check for split sentences, split rows, repeated headers, truncated numbers, **missing rows**, skipped transitions, and overlap duplicates.

Remove only duplicates introduced by overlap or repeated inspection. Preserve legitimate repeated source content. When several screenshots are consecutive scroll captures, do not count the same visible transaction twice merely because it appears in the overlap.

## Phase 4 — Precision pass

Recheck values where one character can materially change meaning:

- dates and timestamps;
- currency amounts and prices;
- counts and quantities;
- percentages;
- tickers and security symbols;
- identifiers and reference numbers;
- table row/column associations.

Do not resolve conflicting readings by intuition. If a value could be `1,234,500` or `1,234,800`, reinspect when possible; otherwise return `[uncertain: 1,234,500 | 1,234,800]`.

## Phase 5 — Low-confidence pass

Treat tiny text, blur, compression, low contrast, clipped rows, overlay interference, and look-alike characters such as `0/O`, `1/I/l`, `5/S`, `6/8`, and `8/B` as low-confidence signals. Revisit them using only actual host capabilities. **Do not guess** unreadable characters.

## Phase 6 — Reconstruction

Reassemble only information already observed from the source. Preserve source order, chronology, headings, table rows/columns, transaction grouping, speaker/message order, and record associations. Do not normalize, translate, reorder, or summarize unless the user's request calls for it.

## Phase 7 — Audit

Before answering, audit for:

- missing or uninspected sources;
- duplicated overlap rows;
- missing transitions or rows;
- suspicious numeric transcription;
- row/column shifts;
- unresolved uncertainty;
- records inferred rather than observed;
- disagreement between detailed rows and any derived summary.

Trace each structured record back to visible evidence. If it cannot be traced, remove it. If a source was not visually inspected, do not claim exhaustive completeness.

## Task-completion rule

Internal checking must not replace the user's requested output. **Verification is a gate, not the deliverable** unless the user explicitly asks only for verification. After validation, **continue to the requested deliverable**: transcription, structured table, extracted records, summary, file, or other requested artifact.

## Native-vision capability rule

LongImageOCR Lite must never imply that an external OCR engine, Python process, MCP server, API endpoint, Cloud Run service, or local executable was used when it was not.
