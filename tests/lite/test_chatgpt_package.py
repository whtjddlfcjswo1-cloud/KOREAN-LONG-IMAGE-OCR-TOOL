"""Contract tests for the ChatGPT skills-only Lite plugin."""

import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "longimageocr-lite"
CANONICAL = REPO_ROOT / "skills" / "lite" / "common"
sys.path.insert(0, str(REPO_ROOT))


class TestChatGPTLitePackage(unittest.TestCase):
    def test_plugin_manifest_is_portable_skills_only(self):
        data = json.loads((PLUGIN_ROOT / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(data["$schema"], "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json")
        self.assertEqual(data["name"], "longimageocr-lite")
        self.assertEqual(data["version"], "0.1.0")
        self.assertIn("native model vision", data["description"])

    def test_plugin_contains_one_valid_lite_skill(self):
        skill = PLUGIN_ROOT / "skills" / "long-image-ocr-lite" / "SKILL.md"
        text = skill.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        self.assertIn("name: long-image-ocr-lite", text)
        self.assertIn("description:", text)
        self.assertIn("seven-phase", text.lower())

    def test_plugin_has_no_mcp_manifest_or_runtime_dependency(self):
        self.assertFalse((PLUGIN_ROOT / "mcp.json").exists())
        text = "\n".join(p.read_text(encoding="utf-8") for p in PLUGIN_ROOT.rglob("*.md")).lower()
        for forbidden in ("requires cloud run", "requires an api key", "requires rapidocr", "requires python"):
            self.assertNotIn(forbidden, text)

    def test_packaged_policy_matches_canonical_policy(self):
        refs = PLUGIN_ROOT / "skills" / "long-image-ocr-lite" / "references"
        self.assertEqual(
            (refs / "CORE_POLICY.md").read_text(encoding="utf-8"),
            (CANONICAL / "CORE_POLICY.md").read_text(encoding="utf-8"),
        )
        self.assertEqual(
            (refs / "OUTPUT_RULES.md").read_text(encoding="utf-8"),
            (CANONICAL / "OUTPUT_RULES.md").read_text(encoding="utf-8"),
        )

    def test_build_chatgpt_package_creates_single_plugin_root_zip(self):
        from scripts.build_lite_packages import build_chatgpt_package

        with tempfile.TemporaryDirectory() as tmp:
            path = build_chatgpt_package(REPO_ROOT, Path(tmp))
            self.assertEqual(path.name, "LongImageOCR-Lite-ChatGPT-v0.1.0.zip")
            with zipfile.ZipFile(path) as zf:
                names = zf.namelist()
            self.assertIn("plugin.json", names)
            self.assertIn("skills/long-image-ocr-lite/SKILL.md", names)
            self.assertNotIn("mcp.json", names)
            self.assertFalse(any(name.startswith("longimageocr-lite/") for name in names))


if __name__ == "__main__":
    unittest.main()
