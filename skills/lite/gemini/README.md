# LongImageOCR Lite for Gemini

This package contains the serverless Gemini Skills version of LongImageOCR Lite.

## Setup

1. Open Gemini and create a **Skill**.
2. Prefer uploading the package ZIP whose root contains `SKILL.md`, or paste `SKILL.md` into the skill instructions when the UI offers a text editor.
3. Name it **LongImageOCR Lite**.
4. Save/enable it and invoke it from a supported Gemini surface when reading screenshots or image files.

The package also includes `CORE_POLICY.md` and `OUTPUT_RULES.md` as canonical reference policy for auditing the standalone skill instructions.

## Important Drive behavior

LongImageOCR Lite requires direct visual inspection when image pixels are accessible. Drive/workspace indexed text is supplementary evidence only and must not be treated as equivalent to inspecting the image itself.

## Runtime

**No server** is needed for Lite. It uses Gemini's native vision and whatever image-inspection capabilities the current Gemini surface actually exposes. LongImageOCR Full remains a separate option for deterministic tiling, external OCR, or reproducible OCR output.
