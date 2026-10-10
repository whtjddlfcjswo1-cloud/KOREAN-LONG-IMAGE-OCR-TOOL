"""Contract tests for the Gemini Workspace Studio Lite skill."""

import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
GEMINI_ROOT = REPO_ROOT / "skills" / "lite" / "gemini"
sys.path.insert(0, str(REPO_ROOT))


class TestGeminiLiteAdapter(unittest.TestCase):
    def setUp(self):
        self.skill = (GEMINI_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.lowered = self.skill.lower()

    def test_gemini_skill_is_instruction_only(self):
        self.assertIn("instruction-only", self.lowered)
        self.assertIn("native vision", self.lowered)

    def test_gemini_skill_contains_native_vision_capability_guardrail(self):
        self.assertIn("do not claim", self.lowered)
        self.assertIn("crop", self.lowered)
        self.assertIn("zoom", self.lowered)
        self.assertIn("actually", self.lowered)

    def test_gemini_skill_contains_all_seven_phases(self):
        for phase in range(1, 8):
            with self.subTest(phase=phase):
                self.assertIn(f"phase {phase}", self.lowered)

    def test_gemini_skill_has_no_flow_or_backend_dependency(self):
        for forbidden in (
            "requires mcp", "requires cloud run", "requires api key", "requires http",
            "requires rapidocr", "requires python", "requires a flow", "local file path",
        ):
            self.assertNotIn(forbidden, self.lowered)

    def test_gemini_skill_is_evidence_only(self):
        self.assertIn("evidence-only", self.lowered)
        self.assertIn("reconstruction is not completion", self.lowered)
        self.assertIn("recurring purchase patterns are not evidence", self.lowered)
        self.assertIn("missing evidence must remain missing", self.lowered)

    def test_gemini_skill_forbids_hallucinated_rows(self):
        self.assertIn("confirm that the row", self.lowered)
        self.assertIn("visibly present", self.lowered)
        self.assertIn("never create a missing row", self.lowered)
        self.assertIn("contextual expectation", self.lowered)

    def test_build_gemini_package_contains_paste_ready_skill(self):
        from scripts.build_lite_packages import build_gemini_package

        with tempfile.TemporaryDirectory() as tmp:
            path = build_gemini_package(REPO_ROOT, Path(tmp))
            self.assertEqual(path.name, "LongImageOCR-Lite-Gemini-v0.1.0.zip")
            with zipfile.ZipFile(path) as zf:
                names = set(zf.namelist())
            self.assertEqual(names, {"SKILL.md", "README.md", "CORE_POLICY.md", "OUTPUT_RULES.md"})


if __name__ == "__main__":
    unittest.main()
