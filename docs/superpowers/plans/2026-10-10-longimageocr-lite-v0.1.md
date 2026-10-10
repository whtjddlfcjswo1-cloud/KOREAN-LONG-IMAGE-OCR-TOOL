# LongImageOCR Lite v0.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a serverless LongImageOCR Lite skill that improves ChatGPT and Gemini long-image reading behavior using the host model's native vision only, while keeping the existing Full OCR engine unchanged.

**Architecture:** Keep one canonical Lite OCR policy under `skills/lite/common/`, then expose thin ChatGPT and Gemini adapters around that policy. ChatGPT ships as a portable skills-only Agent Plugin with no MCP manifest; Gemini ships as Workspace Studio-ready skill instructions that users can paste/create/share without a backend. A small deterministic validation/benchmark harness checks package integrity and scores exported model outputs against ground truth using the repository's existing evaluator primitives.

**Tech Stack:** Markdown skill instructions, JSON Agent Plugin manifest, Python 3.10-3.12 `unittest`, existing `tests/benchmark_comparison.py` evaluator primitives, ZIP packaging via Python standard library.

**Spec:** `docs/superpowers/specs/2026-10-10-longimageocr-lite-v0.1-design.md`

## Global Constraints

- Lite must require no Python runtime, Docker, MCP server, GCP project, Cloud Run, GCS, API key, RapidOCR, ONNX Runtime, or remote endpoint at use time.
- Lite uses only the host model's native vision and whatever image inspection operations the host already exposes.
- Never claim an image was cropped, zoomed, or region-reinspected unless the host platform actually performed that operation.
- Ambiguous text must be surfaced as uncertain rather than silently guessed.
- Dates, currency, counts, percentages, tickers, identifiers, and table row/column associations require an explicit precision pass.
- ChatGPT and Gemini adapters must share the same seven-phase behavioral contract and must not develop separate OCR strategies.
- ChatGPT packaging must be a portable skills-only Agent Plugin with root `plugin.json`, root `skills/`, and no `mcp.json`.
- Gemini v0.1 must be usable as a Workspace Studio skill created from instructions, with no Flow or Custom Step dependency.
- The existing Full engine and existing `adapters/gemini`, `adapters/codex`, and `adapters/claude` integrations remain unchanged except for documentation that distinguishes Full from Lite.

## Review Focus

- **Extremely long or dense screenshots:** Lite must switch from a single-pass reading mindset to ordered segmented inspection and report unresolved omissions instead of pretending completeness. Covered by Task 1 policy contract tests.
- **Precision-sensitive ambiguous digits:** competing readings such as `1,234,500` vs `1,234,800` must trigger reinspection/uncertainty rather than intuitive selection. Covered by Task 1 policy contract tests and Task 4 benchmark fixture.
- **Repeated rows near segment boundaries:** reconciliation must remove duplicates without dropping legitimate repeated content. Covered by Task 1 policy contract tests and Task 4 benchmark fixture.
- **Hosts without crop/zoom tools:** the skill must describe conceptual segmentation without falsely claiming a real crop or zoom occurred. Covered by Task 1 and Task 3 contract tests.
- **Skills-only distribution accidentally depending on Full:** generated ChatGPT/Gemini deliverables must contain no MCP/runtime/backend requirement. Covered by Task 2 and Task 3 package tests.

---

### Task 1: Canonical Lite OCR Policy

**Files:**
- Create: `skills/lite/common/CORE_POLICY.md`
- Create: `skills/lite/common/OUTPUT_RULES.md`
- Create: `tests/lite/__init__.py`
- Create: `tests/lite/test_policy_contract.py`

**Interfaces:**
- Consumes: the seven-phase behavior and three operating modes defined in the design spec.
- Produces: canonical Markdown policy documents referenced by both platform adapters. Stable headings are `Phase 1 — Layout reconnaissance` through `Phase 7 — Audit`, plus `Auto mode`, `Exact transcription mode`, and `Structured extraction mode`.

- [ ] **Step 1: Write the failing contract tests**

Create `tests/lite/test_policy_contract.py` with `unittest.TestCase` methods that load the two canonical Markdown files and assert:

```python
def test_core_policy_contains_all_seven_phases(): ...
def test_core_policy_contains_all_three_modes(): ...
def test_policy_requires_uncertainty_instead_of_guessing(): ...
def test_policy_handles_boundary_duplicates_and_missing_rows(): ...
def test_policy_does_not_require_external_runtime(): ...
def test_policy_does_not_claim_crop_when_capability_is_absent(): ...
```

Assertions must check for the exact phase/mode headings and semantic guardrail phrases, including explicit treatment of precision-sensitive values and repeated boundary content.

- [ ] **Step 2: Run the tests and verify they fail because the policy files do not exist**

Run:

```bash
python -m unittest tests.lite.test_policy_contract -v
```

Expected: FAIL/ERROR with missing `skills/lite/common/CORE_POLICY.md` or `OUTPUT_RULES.md`.

- [ ] **Step 3: Create `CORE_POLICY.md`**

Implement the seven phases from the spec as host-model instructions. Keep segmentation conceptual, instruct the model to use actual crop/zoom/reinspection only when available, and require a second precision pass for numeric/financial/table-sensitive content.

- [ ] **Step 4: Create `OUTPUT_RULES.md`**

Define the three modes and output behavior:

- Auto: choose light vs full seven-phase handling based on image complexity.
- Exact transcription: preserve order/text and mark uncertainty.
- Structured extraction: preserve rows/columns/records and normalize only when requested.

Define a compact uncertainty notation and require an audit note only when unresolved ambiguity materially affects the answer.

- [ ] **Step 5: Run Task 1 tests**

Run:

```bash
python -m unittest tests.lite.test_policy_contract -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add skills/lite/common tests/lite

git commit -m "feat: add LongImageOCR Lite core policy"
```

---

### Task 2: ChatGPT Skills-Only Agent Plugin

**Files:**
- Create: `plugins/longimageocr-lite/plugin.json`
- Create: `plugins/longimageocr-lite/skills/long-image-ocr-lite/SKILL.md`
- Create: `plugins/longimageocr-lite/skills/long-image-ocr-lite/references/CORE_POLICY.md`
- Create: `plugins/longimageocr-lite/skills/long-image-ocr-lite/references/OUTPUT_RULES.md`
- Create: `scripts/build_lite_packages.py`
- Create: `tests/lite/test_chatgpt_package.py`

**Interfaces:**
- Consumes: `skills/lite/common/CORE_POLICY.md` and `skills/lite/common/OUTPUT_RULES.md` from Task 1.
- Produces: a portable Agent Plugin rooted at `plugins/longimageocr-lite/` and a build function `build_chatgpt_package(repo_root: Path, dist_dir: Path) -> Path` that returns the generated ZIP path.

- [ ] **Step 1: Write failing package tests**

Create tests asserting:

```python
def test_plugin_manifest_is_portable_skills_only(): ...
def test_plugin_contains_one_valid_lite_skill(): ...
def test_plugin_has_no_mcp_manifest_or_runtime_dependency(): ...
def test_packaged_policy_matches_canonical_policy(): ...
def test_build_chatgpt_package_creates_single_plugin_root_zip(): ...
```

`plugin.json` must use:

```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
  "name": "longimageocr-lite",
  "version": "0.1.0",
  "description": "Improve long-image and OCR-sensitive reading using native model vision without an external OCR server."
}
```

The plugin root must not contain `mcp.json`.

- [ ] **Step 2: Run the tests and verify failure**

Run:

```bash
python -m unittest tests.lite.test_chatgpt_package -v
```

Expected: FAIL because the plugin/package builder does not exist.

- [ ] **Step 3: Implement the portable plugin files**

Create `SKILL.md` with frontmatter:

```yaml
---
name: long-image-ocr-lite
description: Improve reading of long screenshots, dense documents, tables, and OCR-sensitive images using a disciplined native-vision inspection workflow without an external OCR server.
---
```

The body must instruct the host to apply the canonical policy and must not mention calling LongImageOCR Full unless as an optional escalation recommendation after Lite has attempted the task.

- [ ] **Step 4: Implement `build_chatgpt_package(repo_root: Path, dist_dir: Path) -> Path`**

The builder must copy the current canonical policy files into the plugin's `references/` directory before creating `LongImageOCR-Lite-ChatGPT-v0.1.0.zip`. The ZIP root must directly contain `plugin.json` and `skills/`, with no extra wrapping directory and no MCP file.

- [ ] **Step 5: Run Task 2 tests and inspect the ZIP listing**

Run:

```bash
python -m unittest tests.lite.test_chatgpt_package -v
python scripts/build_lite_packages.py --chatgpt --dist dist
python -c "import zipfile; z=zipfile.ZipFile('dist/LongImageOCR-Lite-ChatGPT-v0.1.0.zip'); print('\n'.join(z.namelist()))"
```

Expected: tests PASS; archive starts with `plugin.json` and `skills/long-image-ocr-lite/...`; no `mcp.json`.

- [ ] **Step 6: Commit**

```bash
git add plugins/longimageocr-lite scripts/build_lite_packages.py tests/lite/test_chatgpt_package.py

git commit -m "feat: package LongImageOCR Lite for ChatGPT"
```

---

### Task 3: Gemini Workspace Studio Skill Adapter

**Files:**
- Create: `skills/lite/gemini/SKILL.md`
- Create: `skills/lite/gemini/README.md`
- Create: `tests/lite/test_gemini_adapter.py`
- Modify: `scripts/build_lite_packages.py`

**Interfaces:**
- Consumes: canonical policy files from Task 1.
- Produces: Workspace Studio-ready instructions plus `build_gemini_package(repo_root: Path, dist_dir: Path) -> Path`, returning `LongImageOCR-Lite-Gemini-v0.1.0.zip` containing the skill instructions and canonical references.

- [ ] **Step 1: Write failing Gemini adapter tests**

Create tests asserting:

```python
def test_gemini_skill_is_instruction_only(): ...
def test_gemini_skill_contains_native_vision_capability_guardrail(): ...
def test_gemini_skill_contains_all_seven_phases(): ...
def test_gemini_skill_has_no_flow_or_backend_dependency(): ...
def test_build_gemini_package_contains_paste_ready_skill(): ...
```

The no-backend test must reject instructions that require MCP, Cloud Run, API keys, HTTP endpoints, local file paths, RapidOCR, or Python execution.

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
python -m unittest tests.lite.test_gemini_adapter -v
```

Expected: FAIL because `skills/lite/gemini/` does not exist.

- [ ] **Step 3: Create the Workspace Studio-ready skill instructions**

`skills/lite/gemini/SKILL.md` must be directly pasteable into the Workspace Studio Skill Builder, tell Gemini to use the current/selected image or Drive source available in context, apply the seven-phase protocol, and avoid claiming unavailable crop/zoom actions.

`README.md` must document the browser-only setup path:

```text
Workspace Studio → Skills → Create → paste SKILL.md instructions → review/test → Turn on
```

Then document use from Drive as `@LongImageOCR Lite` followed by the user's extraction/transcription request. Do not require a Flow for v0.1.

- [ ] **Step 4: Extend `build_lite_packages.py` for Gemini**

Add `build_gemini_package(repo_root: Path, dist_dir: Path) -> Path` and CLI flag `--gemini`. The ZIP must contain `SKILL.md`, `README.md`, `CORE_POLICY.md`, and `OUTPUT_RULES.md` at a single clear package root.

- [ ] **Step 5: Run Task 3 tests and build the package**

Run:

```bash
python -m unittest tests.lite.test_gemini_adapter -v
python scripts/build_lite_packages.py --gemini --dist dist
```

Expected: PASS and `dist/LongImageOCR-Lite-Gemini-v0.1.0.zip` created.

- [ ] **Step 6: Commit**

```bash
git add skills/lite/gemini scripts/build_lite_packages.py tests/lite/test_gemini_adapter.py

git commit -m "feat: add Gemini Workspace Studio Lite skill"
```

---

### Task 4: Lite Benchmark and Scoring Harness

**Files:**
- Create: `tests/lite/benchmark/cases.json`
- Create: `tests/lite/benchmark/README.md`
- Create: `tests/lite/benchmark/score.py`
- Create: `tests/lite/fixtures/precision_conflict/ground_truth.txt`
- Create: `tests/lite/fixtures/precision_conflict/native.txt`
- Create: `tests/lite/fixtures/precision_conflict/lite.txt`
- Create: `tests/lite/fixtures/boundary_repeat/ground_truth.txt`
- Create: `tests/lite/fixtures/boundary_repeat/native.txt`
- Create: `tests/lite/fixtures/boundary_repeat/lite.txt`
- Create: `tests/lite/test_benchmark_score.py`

**Interfaces:**
- Consumes: `calculate_text_similarity`, `compute_standard_cer`, `compute_standard_wer`, `hungarian_bipartite_match`, and `compute_line_metrics` from `tests/benchmark_comparison.py`.
- Produces: `score_case(ground_truth: list[str], prediction: list[str]) -> dict[str, float]` and `compare_runs(case_dir: Path) -> dict[str, object]` for native-vs-Lite exported text comparison.

- [ ] **Step 1: Write failing scorer tests**

Tests must prove:

```python
def test_score_case_penalizes_wrong_precision_digit(): ...
def test_score_case_penalizes_duplicate_boundary_row(): ...
def test_compare_runs_reports_native_and_lite_metrics(): ...
def test_compare_runs_marks_improvement_when_lite_is_better(): ...
```

Use tiny text fixtures only; do not fake model benchmark claims in README or release notes.

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
python -m unittest tests.lite.test_benchmark_score -v
```

Expected: FAIL because the scoring harness does not exist.

- [ ] **Step 3: Implement `score.py`**

Expose exactly:

```python
def score_case(ground_truth: list[str], prediction: list[str]) -> dict[str, float]: ...
def compare_runs(case_dir: Path) -> dict[str, object]: ...
```

Return at minimum CER, WER, line precision, line recall, line F1, duplicate-line count, and exact numeric-token accuracy. `compare_runs` loads `ground_truth.txt`, `native.txt`, and `lite.txt` and returns both result dictionaries plus boolean `lite_improved_any_objective_metric` and boolean `lite_regressed_numeric_accuracy`.

- [ ] **Step 4: Define benchmark case metadata**

`cases.json` must list the six spec categories:

- long Korean screenshot
- transaction/payment history
- dense table
- mixed Korean/English/numeric text
- small-font UI screenshot
- repeated rows near segment boundaries

`README.md` must describe the manual capture protocol: run the same host/model once without Lite and once with Lite, export exact text outputs into the matching case directory, then run the scorer. Do not mix model versions between paired runs.

- [ ] **Step 5: Run Task 4 tests**

Run:

```bash
python -m unittest tests.lite.test_benchmark_score -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add tests/lite/benchmark tests/lite/fixtures tests/lite/test_benchmark_score.py

git commit -m "test: add LongImageOCR Lite benchmark harness"
```

---

### Task 5: Product Documentation, Full/Lite Separation, and Final Verification

**Files:**
- Create: `docs/lite/README.md`
- Modify: `README.md`
- Modify: `RELEASE_NOTES.md`
- Create: `tests/lite/test_docs_contract.py`

**Interfaces:**
- Consumes: package names and build commands from Tasks 2-4.
- Produces: user-facing documentation that presents Lite as the default low-friction option and Full as the optional high-accuracy/self-hosted engine.

- [ ] **Step 1: Write failing documentation contract tests**

Create tests asserting:

```python
def test_root_readme_explains_lite_vs_full(): ...
def test_lite_docs_do_not_require_server_setup(): ...
def test_lite_docs_link_chatgpt_and_gemini_install_paths(): ...
def test_release_notes_do_not_claim_unrun_benchmark_results(): ...
```

- [ ] **Step 2: Run documentation tests and verify failure**

Run:

```bash
python -m unittest tests.lite.test_docs_contract -v
```

Expected: FAIL until the documentation is updated.

- [ ] **Step 3: Write `docs/lite/README.md`**

Document:

- what Lite does and does not do
- ChatGPT skills-only plugin installation/package
- Gemini Workspace Studio skill creation/use
- Auto / Exact transcription / Structured extraction behavior
- when to escalate to Full
- how to run the Lite benchmark

- [ ] **Step 4: Update root README and release notes**

Change the project description from a single-engine presentation to a two-tier product:

```text
LongImageOCR Lite → native-vision skill, no server
LongImageOCR Full → deterministic OCR engine, CLI/MCP/self-host/hosted
```

Do not remove the existing Full architecture or benchmark claims. Clearly label existing v0.1 Full benchmark numbers as Full-engine results, not Lite results.

- [ ] **Step 5: Run the complete Lite test suite**

Run:

```bash
python -m unittest discover -s tests/lite -p "test_*.py" -v
```

Expected: all Lite tests PASS.

- [ ] **Step 6: Run the existing project regression suite**

Run the repository's existing test entry point:

```bash
python run_tests.py
```

Expected: existing Full-engine tests PASS with no Lite-induced regressions.

- [ ] **Step 7: Build both distributables and inspect them**

Run:

```bash
python scripts/build_lite_packages.py --all --dist dist
```

Expected outputs:

```text
dist/LongImageOCR-Lite-ChatGPT-v0.1.0.zip
dist/LongImageOCR-Lite-Gemini-v0.1.0.zip
```

Confirm neither package includes `mcp.json`, credentials, backend URLs, Python executables, or server configuration.

- [ ] **Step 8: Manual platform smoke tests**

Using the same representative long screenshot:

1. ChatGPT without Lite: record the extraction output.
2. ChatGPT with the skills-only plugin: record the extraction output.
3. Gemini without Lite: record the extraction output.
4. Gemini with `@LongImageOCR Lite`: record the extraction output.
5. Score paired outputs with `tests/lite/benchmark/score.py`.

Release candidate criteria:

- at least one objective OCR metric improves on at least one host/model pair;
- exact numeric accuracy does not regress on the evaluated pair;
- neither platform requires a server for Lite;
- uncertainty is surfaced on deliberately ambiguous test content.

- [ ] **Step 9: Commit**

```bash
git add docs/lite README.md RELEASE_NOTES.md tests/lite/test_docs_contract.py

git commit -m "docs: publish LongImageOCR Lite v0.1 workflow"
```

---

## Final Verification

- [ ] `python -m unittest discover -s tests/lite -p "test_*.py" -v` passes.
- [ ] `python run_tests.py` passes after dependencies are installed.
- [ ] `python scripts/build_lite_packages.py --all --dist dist` creates both v0.1.0 ZIPs.
- [ ] ChatGPT ZIP is a valid skills-only portable plugin with no MCP configuration.
- [ ] Gemini package is paste-ready for Workspace Studio and requires no Flow/backend.
- [ ] Manual native-vs-Lite smoke outputs are captured before any accuracy claim is added to documentation.
- [ ] Full engine behavior and existing adapters remain unchanged.
