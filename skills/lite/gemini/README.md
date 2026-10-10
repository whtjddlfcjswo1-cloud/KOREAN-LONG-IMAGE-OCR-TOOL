# LongImageOCR Lite for Gemini

This package contains the serverless Gemini Workspace Studio version of LongImageOCR Lite.

## Setup

1. Open **Workspace Studio → Skills → Create**.
2. Create a skill named **LongImageOCR Lite**.
3. Paste the contents of `SKILL.md` into the skill instructions.
4. Review/test the skill, then turn it on.
5. In supported Gemini surfaces such as the Drive side panel, invoke it with `@LongImageOCR Lite` and attach or reference the image you want inspected.

The package also includes `CORE_POLICY.md` and `OUTPUT_RULES.md` as the canonical reference policy used to author and audit the skill instructions.

## Runtime

**No server** is needed for Lite. It uses Gemini's native vision and the image-inspection capabilities available in the current Gemini surface. LongImageOCR Full remains a separate option for users who need an external OCR engine, deterministic tiling, or reproducible OCR output.
