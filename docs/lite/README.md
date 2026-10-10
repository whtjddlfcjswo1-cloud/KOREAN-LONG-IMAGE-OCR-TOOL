# LongImageOCR Lite

LongImageOCR Lite is the **no server** version of LongImageOCR. It improves how ChatGPT and Gemini use their own native vision when reading long screenshots, dense documents, tables, payment histories, chats, logs, and other OCR-sensitive images.

Lite does not run RapidOCR, Python, MCP, Cloud Run, or any remote OCR backend. The seven-phase inspection protocol is carried entirely as skill instructions.

## Choose a package

- **ChatGPT:** `LongImageOCR-Lite-ChatGPT-v0.1.0.zip` is a skills-only Agent Plugin. The ZIP root contains `plugin.json` and `skills/`; there is no MCP manifest.
- **Gemini:** `LongImageOCR-Lite-Gemini-v0.1.0.zip` contains paste-ready instructions for **Workspace Studio** plus the canonical policy references.

## ChatGPT setup

Install/import the ChatGPT Lite plugin using the platform's supported Agent Plugin workflow, then invoke LongImageOCR Lite on an attached image. The skill uses only the model's available image understanding and inspection capabilities.

## Gemini setup

Open **Workspace Studio → Skills → Create**, create a skill named **LongImageOCR Lite**, paste `SKILL.md` as the instructions, review/test it, and turn it on. In supported Gemini surfaces, use `@LongImageOCR Lite` with the image or Drive context you want inspected.

## What the skill changes

Lite applies this sequence when needed:

1. layout reconnaissance;
2. segmented reading;
3. boundary reconciliation;
4. precision-sensitive recheck;
5. low-confidence recheck;
6. structural reconstruction;
7. final audit.

The protocol is especially strict about dates, money, quantities, percentages, tickers, identifiers, repeated boundary rows, and table alignment. If a value remains ambiguous, the skill reports uncertainty instead of silently guessing.

## Lite vs Full

| | LongImageOCR Lite | LongImageOCR Full |
|---|---|---|
| Runtime | Host model native vision | RapidOCR/ONNX + LongImageOCR pipeline |
| User-managed server | No | Optional for remote use |
| Python required to use | No | Yes for local/self-hosted engine |
| Deterministic pixel tiling | No | Yes |
| External OCR retry | No | Yes |
| Best first choice | General ChatGPT/Gemini users | Exhaustive/high-precision or reproducible OCR |

Start with Lite. Move to Full only when native vision remains materially uncertain or deterministic OCR is required.

## Building the ZIPs from the repository

Maintainers can build both Lite packages with:

```bash
python scripts/build_lite_packages.py
```

This build command is for packaging the distribution; end users do not need it to use Lite.
