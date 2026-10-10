# LongImageOCR Lite Core Policy

LongImageOCR Lite improves OCR-sensitive image reading by changing **how the host model inspects an image**. It does not execute an external OCR engine. No external OCR runtime is required; use the host model's native vision and only the image-inspection capabilities the host actually provides.

## Phase 1 — Layout reconnaissance

Before transcribing, inspect the whole image for structure. Identify whether it is a normal image or a long/dense screenshot, then map major sections, tables, cards, chat/log blocks, repeated rows, columns, headers, timelines, and visually dense areas.

Do not treat a very long screenshot as one undifferentiated reading pass when doing so risks missed text.

## Phase 2 — Segmented reading

Read long or dense content in an explicit top-to-bottom sequence of logical visual regions. Prefer semantic boundaries such as section breaks, whitespace, table blocks, cards, or row groups rather than arbitrary cuts.

Use actual crop, zoom, or region reinspection **only when the host actually exposes** that capability. If it does not, keep segmentation conceptual and continue from the image available in context. Do not claim that you cropped, zoomed, enhanced, or reinspected a region unless that operation actually occurred.

## Phase 3 — Boundary reconciliation

Reconcile every adjacent region before continuing. Check for:

- split sentences or values crossing a boundary;
- duplicate lines or duplicate rows introduced by overlap;
- missing rows or skipped transitions;
- repeated headers that are layout artifacts;
- truncated numbers at region edges.

Remove overlap-created duplicates, but preserve **legitimate repeated content** that genuinely occurs more than once in the source. When uncertain whether repetition is real or overlap-induced, retain it with an uncertainty note rather than silently deleting information.

## Phase 4 — Precision pass

Perform a second, explicit verification pass for values where one character can materially change meaning:

- dates and timestamps;
- currency amounts and prices;
- counts and quantities;
- percentages;
- tickers and security symbols;
- identifiers and reference numbers when requested;
- table row/column associations.

Do not resolve conflicting numeric readings by intuition. For example, if a value could be `1,234,500` or `1,234,800`, reinspect the relevant visible region when possible. If the conflict remains unresolved, report both plausible readings and mark the value uncertain.

## Phase 5 — Low-confidence pass

Treat tiny text, blur, compression, low contrast, clipped rows, overlay interference, and look-alike characters such as `0/O`, `1/I/l`, `5/S`, and `8/B` as low-confidence signals.

Revisit low-confidence material using whatever native vision inspection the host actually supports. **Do not guess** unreadable characters. If uncertainty remains material to the user's task, mark it explicitly as **uncertain**.

## Phase 6 — Reconstruction

Reassemble the result in the source's logical order. Preserve useful structure instead of flattening everything into prose:

- headings and section order;
- chronological sequence;
- table rows and columns;
- transaction or record grouping;
- speaker/message grouping where visible.

Do not normalize, reorder, translate, or summarize source text unless the user's request calls for it.

## Phase 7 — Audit

Before answering, perform a final audit for:

- duplicated text introduced by segmented reading;
- missing transitions or missing rows;
- suspicious numeric transcription;
- row/column shifts;
- arithmetic inconsistencies visible in the source;
- unresolved uncertain regions.

Do not claim exhaustive completeness when material regions remain unreadable or unavailable. State the limitation and still return the best supported result.

## Native-vision capability rule

LongImageOCR Lite is instruction-only. It uses native vision and host-provided image operations. It must never imply that an external OCR engine, Python process, MCP server, API endpoint, Cloud Run service, or local executable was used.
