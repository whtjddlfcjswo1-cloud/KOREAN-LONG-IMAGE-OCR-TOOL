# LongImageOCR

> **Multi-AI Shared Ultra-Long Screenshot & Document OCR Engine**  
> *Native-Resolution Preservation • Smart Content-Density Tiling • Overlap Deduplication • Low-Confidence Audit • Official Multi-AI MCP Server*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.10 | 3.11 | 3.12](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-brightgreen.svg)](https://python.org)
[![Platform: Windows | Linux | macOS](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](README.md)
[![MCP Compliant](https://img.shields.io/badge/MCP-Official%20SDK-orange.svg)](longocr/mcp_server.py)
[![Release](https://img.shields.io/badge/Release-v0.1.0--preview.1-blueviolet.svg)](RELEASE_NOTES.md)

---

## 1. Why LongImageOCR?

When ultra-long vertical images (e.g., mobile screenshots `1080×24000`, chat threads, stock apps, developer logs) are fed directly into multimodal AI Vision models (ChatGPT, Gemini, Claude), the image is aggressively **downscaled to ~1000–2048px**.

This downscaling turns critical financial tickers, percentages, Korean syllables, and table cells into illegible pixel blur.

**LongImageOCR** solves this by enforcing a single immutable rule:

```text
NEVER resize the entire long screenshot for OCR.
```

Instead, LongImageOCR:
1. Detects long images automatically (`height > 4000px` or `aspect_ratio > 3.0`).
2. Analyzes **horizontal content density** to slice at safe whitespace boundaries.
3. Slices overlapping tiles while **preserving 100% native resolution**.
4. Performs OCR with PP-OCRv5 Korean & English models on CPU (via ONNXRuntime).
5. Executes **native-resolution retries** on low-confidence boxes with spatial candidate gating to prevent adjacent-line misreplacement.
6. Maps bounding boxes to global coordinates and **deduplicates overlaps** with strict numerical validation.
7. Synthesizes Markdown/plaintext plus an audit trail.
8. Exposes an **MCP Server (`longocr-mcp`)** so Gemini, Claude, Codex, and other MCP clients can call the same engine with paginated output.

---

## 2. Architecture

```text
LongImageOCR Core
       │
       ├── CLI (longocr / python -m longocr.cli)
       ├── MCP Server (longocr-mcp / python -m longocr.mcp_server)
       ├── Gemini Adapter / Skill (adapters/gemini)
       ├── Codex Adapter / Tool (adapters/codex)
       └── Claude Adapter / MCP (adapters/claude)
```

No AI adapter contains duplicate OCR logic. All adapters point to the core pipeline.

---

## 3. Quick Start

### Installation

```bash
git clone https://github.com/whtjddlfcjswo1-cloud/KOREAN-LONG-IMAGE-OCR-TOOL.git
cd KOREAN-LONG-IMAGE-OCR-TOOL
pip install -e .

# Or use the platform installer
# Windows:
powershell -ExecutionPolicy Bypass -File scripts/install.ps1
# Linux/macOS:
bash scripts/install.sh
```

### Basic CLI Usage

```bash
longocr screenshot.png --mode fast --output ./output
longocr screenshot.png --mode accurate --output ./output
longocr screenshot.png --mode hybrid --output ./output
longocr screenshot.png --tile-height 2200 --overlap 220
python -m longocr.cli screenshot.png --mode hybrid
```

The default mode is `hybrid`.

---

## 4. Output Artifacts

```text
ocr_output/screenshot/
├── output.md
├── output.txt
├── ocr.json
├── manifest.json
├── audit.md
├── tiles/
└── low_confidence/
```

---

## 5. Model Context Protocol (MCP) Server

```bash
longocr-mcp
# Or:
python -m longocr.mcp_server
```

### Provided Tools

| Tool Name | Parameters | Description |
| :--- | :--- | :--- |
| `long_image_ocr` | `image_path`, `mode="hybrid"`, `language="ko"`, `return_full_text=false` | Primary native-resolution smart-tiling OCR tool. Returns a compact preview and artifact paths by default. |
| `read_ocr_output` | `output_dir`, `format="markdown"`, `offset=0`, `limit=4000` | Paginated retrieval for large OCR output. |
| `inspect_ocr_region` | `image_path`, `y_start`, `y_end`, `language="ko"` | Re-OCRs a vertical band while preserving original-image global Y coordinates. |
| `ocr_status` | `output_dir` | Returns manifest metadata and audit preview for a completed OCR job. |

---

## 6. AI Agent Adapters

- **Gemini CLI / Antigravity**: [`adapters/gemini/settings.json`](adapters/gemini/settings.json)
- **OpenAI Codex**: [`adapters/codex/config.toml`](adapters/codex/config.toml), [`adapters/codex/AGENTS.md`](adapters/codex/AGENTS.md)
- **Claude Desktop / Claude Code**: [`adapters/claude/claude_desktop_config.json`](adapters/claude/claude_desktop_config.json), [`adapters/claude/CLAUDE.md`](adapters/claude/CLAUDE.md)

---

## 7. Key Algorithmic Features

### Smart Safe-Cut Slicing
LongImageOCR measures row content density and variance to prefer low-content cut points. When a safe boundary cannot be found, it falls back to overlap slicing.

### Strict Numeric Preservation
If overlapping OCR candidates contain conflicting numeric tokens (for example `1,234,500` vs `1,234,800`), they are not merged as duplicates.

### Safe Low-Confidence Retry
Low-confidence boxes are reprocessed from native-resolution crops. Spatial alignment and text/numeric compatibility are checked before a retry candidate can replace the original OCR result.

---

## 8. Benchmark Summary

Fresh uncached preview benchmark results reported by the release candidate:

| Scenario | Domain | Baseline Recall | LongImageOCR Recall | Precision / F1 | Key Metric Highlights |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Test A** | Document (12k px) | 0.52% | **66.67%** | 96.97% / 79.01% | CER **0.3151** vs 1.0077 |
| **Test B** | Finance (14k px) | 0.0% | **90.57%** | 97.82% / 94.06% | 100% ticker, 85.19% exact number |
| **Test C** | Chat UI (12k px) | 0.0% | **86.36%** | 93.44% / 89.76% | 100% sender, 80% timestamp |
| **Test D** | Table (12k px) | 1.06% cell | **77.52% cell** | 97.07% / 86.20% | 68.44% row exact, 79.79% row fuzzy |
| **Test E** | Console Log (12k px) | 0.0% | **95.35%** | 99.16% / 97.22% | 100% level token, 95.14% request ID |

Evaluator primitives are kept in [`tests/benchmark_comparison.py`](tests/benchmark_comparison.py). The full preview archive can carry the generated synthetic benchmark images and detailed OCR artifacts without bloating Git history.

---

## 9. Inspired by / References

1. **[Anionex/agent-vision-toolkit](https://github.com/Anionex/agent-vision-toolkit)** — long screenshot chunking, safe-cut and audit ideas.
2. **[Anionex/dsh-vision-toolkit](https://github.com/Anionex/dsh-vision-toolkit)** — agent tool and manifest patterns.
3. **[Yuff1010/Manga-Overlay-Translator](https://github.com/Yuff1010/Manga-Overlay-Translator)** — native-resolution retry and tiling ideas.
4. **Webtoon tiling/scanlation patterns** — coordinate restoration and overlap concepts.

See [`LICENSE_REVIEW.md`](LICENSE_REVIEW.md) for the project’s license review.

---

## 10. License

MIT License. See [LICENSE](LICENSE).
