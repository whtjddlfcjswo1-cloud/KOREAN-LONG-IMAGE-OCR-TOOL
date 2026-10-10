"""Regression contracts from live Gemini/long-ledger failures."""

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CORE = (REPO_ROOT / "skills" / "lite" / "common" / "CORE_POLICY.md").read_text(encoding="utf-8")
OUTPUT = (REPO_ROOT / "skills" / "lite" / "common" / "OUTPUT_RULES.md").read_text(encoding="utf-8")
GEMINI = (REPO_ROOT / "skills" / "lite" / "gemini" / "SKILL.md").read_text(encoding="utf-8")
CHATGPT = (REPO_ROOT / "plugins" / "longimageocr-lite" / "skills" / "long-image-ocr-lite" / "SKILL.md").read_text(encoding="utf-8")
ALL = "\n".join((CORE, OUTPUT, GEMINI, CHATGPT)).lower()


class TestLiveFailureContract(unittest.TestCase):
    def test_image_pixels_are_distinguished_from_indexed_text(self):
        self.assertIn("image pixels", ALL)
        self.assertIn("indexed text", ALL)
        self.assertIn("supplementary evidence", ALL)
        self.assertIn("not visually verified", ALL)

    def test_empty_indexed_text_does_not_mean_image_unreadable(self):
        self.assertIn("empty indexed text", ALL)
        self.assertIn("does not mean the image is unreadable", ALL)

    def test_multi_source_tasks_require_source_coverage(self):
        self.assertIn("source coverage", ALL)
        self.assertIn("every provided image", ALL)
        self.assertIn("do not stop", ALL)

    def test_verification_does_not_replace_requested_deliverable(self):
        self.assertIn("verification is a gate, not the deliverable", ALL)
        self.assertIn("continue to the requested deliverable", ALL)

    def test_structured_export_preserves_field_boundaries(self):
        self.assertIn("field boundaries", ALL)
        self.assertIn("csv", ALL)
        self.assertIn("quote", ALL)
        self.assertIn("comma", ALL)

    def test_summaries_are_recomputed_from_final_rows(self):
        self.assertIn("summary", ALL)
        self.assertIn("recompute", ALL)
        self.assertIn("final structured rows", ALL)
        self.assertIn("include/exclude", ALL)


if __name__ == "__main__":
    unittest.main()
