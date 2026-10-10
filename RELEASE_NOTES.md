# Release Notes

## LongImageOCR Lite v0.1

Initial serverless skill-only preview for ChatGPT and Gemini.

### Included
- Shared seven-phase native-vision OCR inspection policy.
- ChatGPT skills-only Agent Plugin package with no MCP manifest or external OCR runtime.
- Gemini Workspace Studio paste-ready skill package with no Flow/backend dependency.
- Explicit uncertainty handling for ambiguous text and precision-sensitive values.
- Native-vs-Lite benchmark harness covering CER/WER, line precision/recall/F1, duplicate lines, and numeric-token accuracy.

### Benchmark status

**No measured Lite-vs-native result** is claimed in this release note yet. The committed benchmark fixtures verify the scorer itself; real ChatGPT/Gemini comparisons must be run on the same host/model and source images before publishing improvement percentages.

---

## LongImageOCR Full v0.1.0-preview.1 (0.1.0a1)

Developer preview of **LongImageOCR Full**, a multi-AI shared OCR engine for ultra-long vertical screenshots, mobile scroll captures, financial tables, and technical documents.

### Modern RapidOCR backend
- Uses `rapidocr` + `onnxruntime` instead of deprecated `rapidocr_onnxruntime`.
- Targets PP-OCRv5 Korean recognition and mobile detection.
- Records fallback state, requested/actual models, and fallback reason in `manifest.json`.

### Official MCP integration
- Removes the old top-level `mcp/` namespace to avoid collision with the official SDK.
- Provides `longocr-mcp` / `python -m longocr.mcp_server`.
- Tools:
  - `long_image_ocr`: native-resolution long-image OCR with compact preview by default.
  - `read_ocr_output`: paginated retrieval of large OCR outputs.
  - `inspect_ocr_region`: regional OCR with original-image global Y coordinates.
  - `ocr_status(output_dir)`: manifest metadata and audit preview for a completed OCR job.
- `longocr-mcp --help` and `--version` exit normally rather than entering server mode.
- Includes real MCP Client stdio subprocess coverage.

### Strict low-confidence retry gating
- Prevents a higher-confidence adjacent line from replacing the target OCR box.
- Uses spatial overlap/distance, text compatibility, and numeric-token safety checks.
- Keeps the original OCR result if no valid retry candidate exists.

### Hardened evaluator
- Hungarian one-to-one assignment for repeated/ambiguous lines.
- CER/WER include insertion and deletion penalties.
- Repeated table cells use one-to-one multiset accounting.
- Benchmark runs are performed uncached.

### PaddleOCR compatibility
- Supports the PaddleOCR 3.x `predict()` result contract as well as the 2.x `ocr()` path.
- Handles attribute-style, mapping-style, and JSON-style result fields.
- Normalizes `[xmin, ymin, xmax, ymax]` boxes into four-point polygons.
- Mock fixtures verify protocol compatibility; this preview does not claim hardware/runtime validation of every PaddleOCR 3.x environment.

### Multi-AI adapters
- Gemini CLI / Antigravity: `adapters/gemini/settings.json`
- OpenAI Codex: `adapters/codex/config.toml` and `AGENTS.md`
- Claude Desktop / Claude Code: `adapters/claude/claude_desktop_config.json` and `CLAUDE.md`

### Installation

```bash
git clone https://github.com/whtjddlfcjswo1-cloud/KOREAN-LONG-IMAGE-OCR-TOOL.git
cd KOREAN-LONG-IMAGE-OCR-TOOL
pip install -e .

longocr --help
longocr-mcp --help
longocr input_long.png --mode hybrid --output ./output
```

The full preview release archive can also include synthetic benchmark images and detailed generated OCR artifacts without placing those large generated files in Git history.
