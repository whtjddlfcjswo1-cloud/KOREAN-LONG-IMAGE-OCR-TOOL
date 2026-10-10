"""Documentation contract tests for Lite/Full product separation."""

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class TestLiteDocsContract(unittest.TestCase):
    def test_root_readme_explains_lite_vs_full(self):
        text = (REPO_ROOT / "README.md").read_text(encoding="utf-8").lower()
        self.assertIn("longimageocr lite", text)
        self.assertIn("longimageocr full", text)
        self.assertIn("server", text)
        self.assertIn("native vision", text)

    def test_lite_docs_do_not_require_server_setup(self):
        text = (REPO_ROOT / "docs" / "lite" / "README.md").read_text(encoding="utf-8").lower()
        self.assertIn("no server", text)
        self.assertIn("chatgpt", text)
        self.assertIn("gemini", text)
        for forbidden in ("create a gcp project", "deploy cloud run", "configure an api key", "start the mcp server"):
            self.assertNotIn(forbidden, text)

    def test_lite_docs_link_chatgpt_and_gemini_install_paths(self):
        text = (REPO_ROOT / "docs" / "lite" / "README.md").read_text(encoding="utf-8")
        self.assertIn("LongImageOCR-Lite-ChatGPT-v0.1.0.zip", text)
        self.assertIn("LongImageOCR-Lite-Gemini-v0.1.0.zip", text)
        self.assertIn("Workspace Studio", text)

    def test_release_notes_do_not_claim_unrun_benchmark_results(self):
        text = (REPO_ROOT / "RELEASE_NOTES.md").read_text(encoding="utf-8").lower()
        self.assertIn("lite v0.1", text)
        self.assertIn("benchmark", text)
        self.assertIn("no measured lite-vs-native result", text)


if __name__ == "__main__":
    unittest.main()
