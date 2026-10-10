#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "   LongImageOCR (v0.1.0-preview.1) Linux/macOS Install"
echo "=========================================================="

# 1. Check python3
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 could not be found."
    exit 1
fi

PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "[INFO] Detected Python: $PY_VERSION"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "[INFO] Installing LongImageOCR and dependencies from $PROJECT_ROOT..."
python3 -m pip install --upgrade pip
python3 -m pip install -e "$PROJECT_ROOT"

echo "[INFO] Verifying & caching official RapidOCR PP-OCRv5 Korean models..."
python3 -c "from longocr.engines.rapid import RapidOCREngine; from longocr.config import OCRConfig; RapidOCREngine(OCRConfig()); print('Official RapidOCR PP-OCRv5 engine verified successfully.')"

echo "[INFO] Verifying CLI entry points..."
if command -v longocr &> /dev/null; then
    echo "  -> 'longocr' CLI command is verified and working."
else
    echo "  -> [WARNING] 'longocr' command not found in PATH. You can invoke via 'python3 -m longocr.cli'."
fi

echo ""
echo "=========================================================="
echo " Installation Succeeded!"
echo " CLI:   longocr <image_path> --mode hybrid"
echo " MCP:   longocr-mcp  (or: python3 -m longocr.mcp_server)"
echo "=========================================================="
