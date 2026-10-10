# LongImageOCR Lite Benchmark

This harness compares the **same host/model** in two runs: native vision without Lite, then native vision with LongImageOCR Lite enabled. LongImageOCR Full may be added as a third reference where practical.

## Procedure

1. Use the same source image and the same user request.
2. Keep the host product and model version identical between native and Lite runs.
3. Export the model result exactly as returned; do not manually correct it.
4. Store source-of-truth text separately from both model outputs.
5. Score exact numeric tokens, CER/WER, line precision/recall/F1, and excess duplicate lines.
6. Record uncertain values separately when a real-image benchmark is reviewed.

The committed `fixtures/` cases are deterministic scorer regression fixtures, not measured claims about ChatGPT or Gemini accuracy. Real model benchmark results must be collected separately before any accuracy improvement percentage is published.
