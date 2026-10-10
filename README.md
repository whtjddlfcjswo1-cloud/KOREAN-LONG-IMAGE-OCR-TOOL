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
4. Performs OCR with official PP-OCRv5 Korean & English models on CPU (via ONNXRuntime).
5. Executes **native-resolution retries** on low-confidence boxes with spatial IoU candidate gating to prevent adjacent line misreplacement.
6. Maps bounding boxes to global coordinates and **deduplicates overlaps** with strict numerical validation.
7. Synthesizes clean GitHub-Flavored Markdown tables and an audit trail.
8. Exposes an **official MCP Server (`longocr-mcp`)** so all AI agents (Gemini, Claude, Codex) call the exact same engine with built-in output pagination.

---

## 2. Architecture

```text
LongImageOCR Core
       │
       ├── CLI (longocr / python -m longocr.cli)
       ├── Official MCP Server (longocr-mcp / python -m longocr.mcp_server)
       ├── Gemini Adapter / Skill (adapters/gemini)
       ├── Codex Adapter / Tool (adapters/codex)
       └── Claude Adapter / MCP (adapters/claude)
```

No AI adapter contains duplicate OCR logic. All adapters point to the core pipeline.

---

## 3. Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/LongImageOCR.git
cd LongImageOCR

# Install package and dependencies in editable mode
pip install -e .

# Or run the platform installer
# Windows:
powershell -ExecutionPolicy Bypass -File scripts/install.ps1
# Linux/macOS:
bash scripts/install.sh
```

### Basic CLI Usage

```bash
# Fast mode (Official PP-OCRv5 Korean ONNX on CPU)
longocr screenshot.png --mode fast --out-dir ./output

# Accurate mode (Adaptive PaddleOCR 2.x/3.x with fallback)
longocr screenshot.png --mode accurate --out-dir ./output

# Hybrid mode (Fast Engine + Native-Resolution Retry)
longocr screenshot.png --mode hybrid --out-dir ./output

# Custom tile height and overlap
longocr screenshot.png --tile-height 2200 --overlap 220

# Invocation via Python module (default mode: hybrid)
python -m longocr.cli screenshot.png --mode hybrid
```

---

## 4. Output Artifacts

Each OCR operation generates a structured output directory:

```text
ocr_output/screenshot/
├── output.md          # Reconstructed GitHub-Flavored Markdown document
├── output.txt         # Clean plain text line-by-line
├── ocr.json           # Fine-grained bounding box coordinates & confidences
├── manifest.json      # Processing metadata, tile coordinates, time elapsed, fallback flag
├── audit.md           # Audit report of low-confidence detections & merges
├── tiles/             # Saved native-resolution slice tiles
│   ├── tile_001.png
│   ├── tile_002.png
│   └── ...
└── low_confidence/    # High-resolution crops of ambiguous regions
    ├── crop_tile001_002.png
    └── ...
```

---

## 5. Model Context Protocol (MCP) Server

LongImageOCR provides an official Model Context Protocol server (`longocr/mcp_server.py`) using the official `mcp` Python SDK:

### Launching the MCP Server

```bash
longocr-mcp
# Or:
python -m longocr.mcp_server
```

### Provided Tools

| Tool Name | Parameters | Description |
| :--- | :--- | :--- |
| `long_image_ocr` | `image_path`, `mode="hybrid"`, `language="ko"`, `return_full_text=false` | Primary native-resolution smart-tiling OCR tool (default mode: `hybrid`). Returns safe preview and output paths by default to avoid flooding agent context. |
| `read_ocr_output` | `output_dir`, `format="markdown"`, `offset=0`, `limit=4000` | Paginated retrieval tool supporting large document inspection without context overflow. |
| `inspect_ocr_region` | `image_path`, `y_start`, `y_end`, `language="ko"` | Crops and evaluates a specific vertical band, preserving full global Y coordinates. |
| `ocr_status` | `output_dir` | Returns manifest metadata and audit preview for a completed OCR job. |

---

## 6. AI Agent Adapters

- **Gemini CLI / Antigravity**: Configured via [`adapters/gemini/settings.json`](adapters/gemini/settings.json).
- **OpenAI Codex**: Configured via [`adapters/codex/config.toml`](adapters/codex/config.toml).
- **Claude Desktop & Claude Code**: Configured via [`adapters/claude/claude_desktop_config.json`](adapters/claude/claude_desktop_config.json) and agent operating rules in [`adapters/claude/CLAUDE.md`](adapters/claude/CLAUDE.md).

---

## 7. Key Algorithmic Features

### 7.1 Smart Safe-Cut Slicing
Instead of cutting at arbitrary pixel heights, LongImageOCR measures vertical gradient profiles and pixel variances to discover natural whitespace breaks between paragraphs or chat bubbles. If no empty space is found within $\pm 300\text{px}$, it falls back to overlap slicing.

### 7.2 Strict Numeric Preservation & Overlap Deduplication
When duplicate text appears in overlapping tiles, deduplication matches text and global coordinates.
If numerical sequences differ (e.g., `평가금액 1,234,500원` vs `평가금액 1,234,800원`), **merging is strictly prohibited**, preventing financial inaccuracies.

### 7.3 Safe Low-Confidence Retry Candidate Gating
Any detection with confidence $< 0.75$ triggers a localized crop from the original unscaled image. The candidate must pass 2D spatial IoU, center distance, and text compatibility checks (`is_valid_retry_candidate`). Adjacent lines (`옆줄텍스트`) are rejected, safely preserving the original detection if no valid enhancement match exists.

---

## 8. Benchmark Summary

Evaluated against the downscaled baseline across 5 domain test suites using true 1-to-1 Hungarian Maximum Bipartite Matching in strictly uncached mode (`enable_cache=False`):

| Scenario | Domain | Baseline Recall | LongImageOCR Recall | Precision / F1 | Key Metric Highlights |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Test A** | Document (12k px) | 0.52% | **66.67%** | 96.97% / 79.01% | CER: **0.3151** (vs 1.0077) |
| **Test B** | Finance (14k px) | 0.0% | **90.57%** | 97.82% / 94.06% | **100% Ticker**, **85.19% Exact Number**, **92.59% Field** |
| **Test C** | Chat UI (12k px) | 0.0% | **86.36%** | 93.44% / 89.76% | **100% Sender**, **80% Timestamp**, **72.73% Message** |
| **Test D** | Table (12k px) | 1.06% (Cell) | **77.52%** (Cell) | 97.07% / 86.20% | **68.44% Row Exact**, **79.79% Row Fuzzy**, **99.56% Col Align** |
| **Test E** | Console Log (12k px) | 0.0% | **95.35%** | 99.16% / 97.22% | **100% Level Token**, **95.14% Request ID Accuracy** |

*Full details and failure analysis: [`test_results/comparison_summary.md`](test_results/comparison_summary.md) and [`TEST_REPORT.md`](TEST_REPORT.md).*

---

## 9. Inspired by / References

We gratefully acknowledge the algorithmic patterns, research, and ideas from the following open-source projects:

1. **[Anionex/agent-vision-toolkit](https://github.com/Anionex/agent-vision-toolkit)** (MIT License):
   - Architectural inspiration for long screenshot chunking, content-density safe cuts, overlap management, Markdown merging, and audit trail generation.
2. **[Anionex/dsh-vision-toolkit](https://github.com/Anionex/dsh-vision-toolkit)** (MIT License):
   - Inspiration for AI agent tool interfaces, structured manifest designs, and OCR sidecar files.
3. **[Yuff1010/Manga-Overlay-Translator](https://github.com/Yuff1010/Manga-Overlay-Translator)** (MIT License):
   - Inspiration for native-resolution retry on low-confidence regions, coordinate restoration, and PaddleOCR tiling integration.
4. **Webtoon Scanlation & Tiling Methodologies (vasmks / toontra / Community Art)**:
   - Concepts of global coordinate mapping ($y_{global} = y_{local} + y_{start}$), tile ownership, and Non-Maximum Suppression (NMS) for overlapping slices.

*See [`LICENSE_REVIEW.md`](LICENSE_REVIEW.md) for detailed intellectual property review.*

---

## 10. License

This project is licensed under the [MIT License](LICENSE).
