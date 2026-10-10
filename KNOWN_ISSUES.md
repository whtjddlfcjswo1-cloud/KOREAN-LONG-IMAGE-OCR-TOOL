# LongImageOCR Known Issues & Preview Caveats (v0.1.0-preview.1)

This document tracks known limitations, platform caveats, and architectural trade-offs for the **v0.1.0-preview.1** release.

---

## 1. Runtime & Environment Caveats

### 1.1 Python 3.13 Ecosystem Compatibility
- **Status**: LongImageOCR is officially tested and supported on **Python 3.10, 3.11, and 3.12**.
- **Caveat**: Python 3.13 introduces major C-API and GIL changes. While `numpy` and `pillow` have wheel support for 3.13, certain optional deep learning runtimes (`paddlepaddle`, `onnxruntime` native wheels) may still be finalizing stable prebuilt wheels for Python 3.13 across all operating systems.
- **Recommendation**: For production deployments and stable CLI usage, use Python 3.10–3.12.

### 1.2 PaddleOCR 3.x vs 2.x API Differences
- **Status**: LongImageOCR provides adaptive initialization for both PaddleOCR 2.x and 3.x.
- **Caveat**: Native `paddlepaddle` packages are large (~500MB to 1.5GB with CUDA) and require specific Microsoft Visual C++ redistributables on Windows.
- **Fallback**: LongImageOCR defaults to `mode="hybrid"` using official `rapidocr` and `onnxruntime` with native-resolution retry, providing PP-OCRv5 Korean recognition out of the box with zero heavy framework overhead. If `paddleocr` is requested but unavailable, the pipeline logs an informative warning and flags `engine_fallback: True` in `manifest.json`.

---

## 2. Image Processing & Layout Limitations

### 2.1 Borderless Complex Multi-Column Tables
- **Observation**: Tables without visible vertical grid borders rely on multi-row column coordinate clustering (`are_columns_aligned`, `detect_robust_tables`).
- **Caveat**: If a table has narrow horizontal whitespace between columns (< 15px) or irregular indented text, OCR bounding boxes may occasionally bridge across adjacent columns.
- **Mitigation**: Users can call the `inspect_ocr_region` tool to zoom into problematic table bands with higher-resolution crops.

### 2.2 Memory Footprint on Ultra-Massive (>100,000px Height) Images
- **Observation**: Loading an uncompressed 1080×100,000px 24-bit RGB bitmap into memory requires ~300MB RAM. Processing multiple image variants concurrently can increase transient memory consumption.
- **Status**: Tested and verified up to 35,000px height on standard developer workstations (8GB–16GB RAM). For extreme >100,000px images, streaming disk-tiling without loading the whole canvas into PIL memory is planned for v0.2.0.

### 2.3 Non-Standard Vertical (Top-to-Bottom) East Asian Text
- **Observation**: Traditional East Asian vertical writing mode (top-to-bottom, right-to-left) is grouped by horizontal line heuristics by default.
- **Workaround**: Standard modern web screenshots, chat logs, stock charts, and mobile apps use horizontal text and are unaffected.

---

## 3. Preview Release Notes
- `v0.1.0-preview.1` is a release-candidate preview intended for developer testing, MCP client integration, and agent benchmarking.
- Backward compatibility of internal cache formats across future minor versions is not guaranteed.
