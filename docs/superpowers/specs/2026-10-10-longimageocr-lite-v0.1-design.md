# LongImageOCR Lite v0.1 — Design

Date: 2026-10-10
Status: Draft for user review

## 1. Purpose

LongImageOCR Lite is a serverless, skill-only companion to the existing LongImageOCR Full engine.

Its purpose is to improve how multimodal AI models such as ChatGPT and Gemini read long screenshots, dense documents, tables, financial records, and OCR-sensitive images by giving the model a disciplined inspection protocol.

Lite does **not** run RapidOCR, ONNX Runtime, FastAPI, MCP, Cloud Run, GCS, or any other external OCR backend. It uses only the host model's native vision capabilities and the host platform's available image inspection functions.

The existing Full engine remains the higher-accuracy option for users who need deterministic tiling, external OCR, low-confidence retries, or self-hosted/hosted processing.

## 2. Product split

The repository will expose two related products:

- **LongImageOCR Lite** — installable/shareable AI skill, no server required.
- **LongImageOCR Full** — existing OCR engine, local or hosted, with real OCR runtime and optional MCP/API integration.

Lite is the default entry point for general users. Full remains available for harder documents or users who need stronger guarantees.

## 3. Design principles

1. **No external execution dependency.** Lite must remain useful without Python, Docker, MCP, GCP, or a remote endpoint.
2. **Use model-native vision deliberately.** The skill should improve inspection behavior rather than pretend to provide an OCR engine it cannot execute.
3. **Do not invent unreadable text.** Ambiguous characters, cropped regions, and uncertain numeric values must be marked as uncertain rather than silently guessed.
4. **Prioritize precision-sensitive content.** Dates, money, quantities, IDs, tickers, percentages, and table alignment receive a second-pass verification.
5. **Preserve document structure.** Tables, chronological logs, grouped records, and section boundaries should be reconstructed rather than flattened into unstructured prose.
6. **Remain platform-neutral at the core.** ChatGPT and Gemini adapters should share the same OCR policy, with only the platform packaging and capability notes differing.

## 4. Lite OCR protocol

The common skill policy will implement a seven-phase inspection procedure.

### Phase 1 — Layout reconnaissance

Before transcribing, identify the image type and visual structure:

- long vertical screenshot vs normal image
- number and position of major sections
- tables, cards, receipts, chat logs, timelines, columns, or repeated rows
- likely dense or low-resolution areas
- regions containing precision-sensitive values

The model should avoid treating a very long image as a single undifferentiated OCR pass.

### Phase 2 — Segmented reading

Read the document in logical visual segments from top to bottom.

Segmentation is conceptual, not based on a fixed pixel count. When the platform supports zooming, cropping, or region reinspection, use those capabilities. When it does not, still maintain an explicit ordered sequence of regions.

The skill must not claim that an actual crop occurred unless the platform exposes such an operation.

### Phase 3 — Boundary reconciliation

Adjacent regions must be checked for:

- split sentences
- duplicate lines
- skipped rows
- repeated headers
- truncated numbers
- content that crosses region boundaries

This is the Lite analogue of the Full engine's overlap and merge behavior.

### Phase 4 — Precision pass

Perform an explicit second pass over values where a one-character error materially changes meaning:

- currency amounts
- dates and timestamps
- counts and quantities
- percentages
- securities/ticker symbols
- account/order/reference numbers when the user asks for them
- table row/column associations

Conflicting readings should not be resolved by intuition alone. The model should reinspect the relevant region when possible or report the alternatives.

### Phase 5 — Low-confidence pass

Flag uncertain regions and revisit them.

Examples of uncertainty signals:

- tiny text
- blur or compression artifacts
- low contrast
- overlapping UI elements
- visually similar characters such as `0/O`, `1/I/l`, `5/S`, `8/B`
- Korean characters with ambiguous strokes
- partially cropped rows

If confidence remains inadequate, output an explicit uncertainty marker rather than fabricating a value.

### Phase 6 — Reconstruction

Reassemble the document while preserving the original logical order.

Preferred output should retain useful structure such as:

- headings
- bullet groups
- table rows and columns
- chronological order
- transaction grouping
- page/section boundaries when visible

### Phase 7 — Audit

Before finalizing, check for:

- duplicated text introduced by segmented reading
- missing transitions between sections
- arithmetic inconsistencies visible in the document
- suspicious numeric transcription
- obvious row/column shifts
- unresolved uncertain regions

The final answer should separate confident transcription from uncertainty notes when appropriate.

## 5. Operating modes

Lite v0.1 will define three user-facing modes inside one skill rather than separate skills.

### Auto mode

Default behavior. The model decides whether the image needs the full seven-phase protocol or a lighter pass.

### Exact transcription mode

Used when the user asks to extract text faithfully. Prioritizes transcription fidelity and uncertainty reporting over summarization.

### Structured extraction mode

Used for tables, transaction histories, receipts, schedules, or records where the user wants structured fields or a normalized table.

The user does not need to memorize mode names. The skill infers the mode from the request unless the user explicitly specifies one.

## 6. Escalation to Full

Lite should not falsely imply that it can match an external OCR engine in every case.

The skill may recommend LongImageOCR Full when one or more of the following applies:

- the image is extremely long or text-dense
- the text is too small for reliable native vision reading
- the task is financially or operationally sensitive and exact digits matter
- repeated reinspection still leaves material uncertainty
- the user requests exhaustive character-level transcription
- the same document needs reproducible OCR output across models

Escalation is advisory. Lite must still return the best result it can rather than refusing simply because Full would be stronger.

## 7. Repository structure

Target layout:

```text
skills/
  lite/
    common/
      CORE_POLICY.md
      OUTPUT_RULES.md
    chatgpt/
      SKILL.md
      README.md
    gemini/
      SKILL.md
      README.md

tests/
  lite/
    cases/
    expected/
    prompts/
    benchmark.md
```

The platform adapters must remain thin. They should import or mirror the same behavioral contract rather than diverge into separate OCR strategies.

Exact packaging formats for ChatGPT and Gemini must be verified against the current platform requirements during implementation; the design must not hard-code an obsolete manifest format.

## 8. Benchmark design

Lite must be evaluated against native model behavior, not only inspected for prompt quality.

For each supported host model, compare:

1. model native vision with no Lite skill
2. model native vision with LongImageOCR Lite
3. LongImageOCR Full where practical

Initial benchmark categories:

- long Korean screenshot
- transaction/payment history
- dense table
- mixed Korean/English/numeric text
- small-font UI screenshot
- repeated rows near segment boundaries

Metrics should emphasize:

- exact numeric accuracy
- omitted-line rate
- duplicated-line rate
- structural/table accuracy
- uncertainty calibration
- total extraction completeness

The benchmark should preserve source-of-truth answers separately from model outputs.

## 9. v0.1 success criteria

Lite v0.1 is considered successful when:

- it requires no external server or user-managed infrastructure
- the same common policy can be used by both ChatGPT and Gemini adapters
- it materially improves at least one objective OCR quality metric over the same model without the skill on the benchmark set
- it does not increase hallucinated numeric values in the benchmark set
- uncertain values are surfaced explicitly rather than silently guessed
- the skill can be distributed independently from the Full engine
- Full remains available without being required for Lite operation

A specific percentage accuracy target is intentionally not fixed before the first benchmark because native model capability differs by platform and model version.

## 10. Non-goals for v0.1

The first Lite version will not include:

- remote OCR calls
- local OCR subprocesses
- Cloud Run deployment
- GCS job storage
- account systems or billing
- background processing
- automatic image preprocessing outside host model capabilities
- deterministic pixel-based tiling
- an attempt to replace the Full engine

## 11. Distribution strategy

The intended distribution order is:

1. Lite as the simplest install/share path for general ChatGPT and Gemini users.
2. Full self-hosted for users who need stronger OCR and privacy/control.
3. Hosted Full only if Lite proves insufficient for enough real-world cases to justify operating a shared backend.

This keeps infrastructure cost and setup complexity out of the default user experience.

## 12. Compatibility with the existing Full engine

The Full engine is not discarded or rewritten for Lite.

Lite reuses Full's design lessons conceptually:

- segmentation
- overlap-aware reconciliation
- confidence-based retry
- precision-sensitive verification
- structured merge
- audit

The Full implementation remains the reference for high-accuracy OCR behavior, while Lite translates those ideas into model-executable instructions.

## 13. Implementation boundary

Implementation of Lite v0.1 should be limited to:

- common policy documents
- ChatGPT adapter
- Gemini adapter
- benchmark harness/data structure
- documentation explaining Lite vs Full

No Cloud Run or backend work is part of Lite v0.1.
