# LongImageOCR License Review and Open Source Attribution (Release Hardened)

## 1. Overview and Intellectual Property Policy

LongImageOCR was designed to solve ultra-long screenshot optical character recognition for multimodal AI agents.
To ensure broad commercial and research usability without intellectual property contamination or viral licensing issues:
- **Project License**: MIT License (`LICENSE`)
- **Implementation Strategy**: Clean-room independent implementation based on published algorithmic concepts and design patterns.
- **Copying Policy**: No copyrighted source code chunks were copied verbatim. All modules (`splitter.py`, `preprocess.py`, `merge.py`, `retry.py`, `reader.py`, `audit.py`, `cache.py`, `pipeline.py`, `mcp_server.py`) were written from first principles in idiomatic Python.

---

## 2. Surveyed Reference Projects & License Compliance

### 2.1 Anionex / agent-vision-toolkit
- **Repository**: [https://github.com/Anionex/agent-vision-toolkit](https://github.com/Anionex/agent-vision-toolkit)
- **License**: **MIT License**
- **Referenced Concepts**:
  - Image chunking and safe cut bands based on low-content horizontal density.
  - Overlap reconciliation without data loss.
  - Audit logging of ambiguous boundaries.
  - Multi-agent skill integration philosophy.
- **Compliance Status**: Algorithmic patterns were referenced and independently implemented. Credit is provided in `README.md` under *Inspired by / References*.

### 2.2 Anionex / dsh-vision-toolkit
- **Repository**: [https://github.com/Anionex/dsh-vision-toolkit](https://github.com/Anionex/dsh-vision-toolkit)
- **License**: **MIT License**
- **Referenced Concepts**:
  - Agent tool contract and structured JSON manifest patterns.
  - Tile storage organization and OCR sidecar files.
- **Compliance Status**: Tool schemas and manifest formats independently designed.

### 2.3 Yuff1010 / Manga-Overlay-Translator
- **Repository**: [https://github.com/Yuff1010/Manga-Overlay-Translator](https://github.com/Yuff1010/Manga-Overlay-Translator)
- **License**: **MIT License**
- **Referenced Concepts**:
  - Ultra-long vertical strip tiling and global coordinate mapping.
  - Native-resolution retry on low-confidence bounding boxes.
  - Image enhancement before OCR retry.
- **Compliance Status**: Concepts adopted and generalized for document/screenshot processing.

### 2.4 Webtoon OCR Tiling Patterns
- **Referenced Concepts**: tile overlap, global coordinate restoration, spatial overlap gating and deduplication.
- **Compliance Status**: general computer-vision principles implemented independently.

---

## 3. Dependency Licensing Analysis

| Package | License | Distribution Impact | Notes |
| :--- | :--- | :--- | :--- |
| `rapidocr` | Apache 2.0 | Permissive | Unified RapidOCR runtime. |
| `onnxruntime` | MIT | Permissive | Microsoft ONNX Runtime. |
| `mcp` | MIT | Permissive | Model Context Protocol Python SDK. |
| `opencv-python-headless` | Apache 2.0 | Permissive | Computer-vision primitives. |
| `Pillow` | HPND / MIT-style | Permissive | Image processing. |
| `numpy` | BSD 3-Clause | Permissive | Numerical arrays. |
| `scipy` | BSD 3-Clause | Permissive | Hungarian assignment implementation used by evaluator. |
| `paddleocr` *(optional)* | Apache 2.0 | Permissive | Optional accurate engine. |
| `paddlepaddle` *(optional)* | Apache 2.0 | Permissive | Optional framework. |

No GPL/AGPL runtime dependency is intentionally introduced by the base project.

---

## 4. Model Weights Attribution

LongImageOCR uses PP-OCR family ONNX model assets through RapidOCR, including Korean recognition and mobile detection models. Upstream model licensing and distribution terms should remain documented with each future model change; release maintainers should re-check upstream licensing whenever model sources or redistribution strategy changes.
