# Windows Installation Script for LongImageOCR (Release Hardened)
$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   LongImageOCR (v0.1.0-preview.1) Installation Script" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Check Python
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "[ERROR] Python is not installed or not in PATH." -ForegroundColor Red
    Exit 1
}

$pyVersion = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
Write-Host "[INFO] Detected Python: $pyVersion" -ForegroundColor Green

# 2. Upgrade pip and install package in editable mode
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir

Write-Host "[INFO] Installing LongImageOCR and dependencies from $projectRoot..." -ForegroundColor Yellow
& python -m pip install --upgrade pip
& python -m pip install -e "$projectRoot"

# 3. Pre-cache official RapidOCR PP-OCRv5 Korean models
Write-Host "[INFO] Verifying & caching official RapidOCR PP-OCRv5 Korean models..." -ForegroundColor Yellow
& python -c "from longocr.engines.rapid import RapidOCREngine; from longocr.config import OCRConfig; RapidOCREngine(OCRConfig()); print('Official RapidOCR PP-OCRv5 engine verified successfully.')"

# 4. Verify CLI Entry Points
Write-Host "[INFO] Verifying CLI entry points..." -ForegroundColor Yellow
& longocr --help | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  -> 'longocr' CLI command is verified and working." -ForegroundColor Green
} else {
    Write-Host "  -> [WARNING] 'longocr' command not found in PATH. Use 'python -m longocr.cli' instead." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Installation Succeeded!" -ForegroundColor Green
Write-Host " CLI Usage:    longocr <image_path> --mode hybrid" -ForegroundColor White
Write-Host " MCP Server:   longocr-mcp  (or: python -m longocr.mcp_server)" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan
