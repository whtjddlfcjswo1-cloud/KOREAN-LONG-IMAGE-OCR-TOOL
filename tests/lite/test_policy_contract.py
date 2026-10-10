"""Contract tests for the serverless LongImageOCR Lite policy."""

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CORE_POLICY = REPO_ROOT / "skills" / "lite" / "common" / "CORE_POLICY.md"
OUTPUT_RULES = REPO_ROOT / "skills" / "lite" / "common" / "OUTPUT_RULES.md"


class TestLitePolicyContract(unittest.TestCase):
    def setUp(self):
        self.core = CORE_POLICY.read_text(encoding="utf-8")
        self.output = OUTPUT_RULES.read_text(encoding="utf-8")
        self.all_text = f"{self.core}\n{self.output}"

    def test_core_policy_contains_all_seven_phases(self):
        expected = [
            "Phase 1 — Layout reconnaissance",
            "Phase 2 — Segmented reading",
            "Phase 3 — Boundary reconciliation",
            "Phase 4 — Precision pass",
            "Phase 5 — Low-confidence pass",
            "Phase 6 — Reconstruction",
            "Phase 7 — Audit",
        ]
        for heading in expected:
            with self.subTest(heading=heading):
                self.assertIn(heading, self.core)

    def test_core_policy_contains_all_three_modes(self):
        for heading in ("Auto mode", "Exact transcription mode", "Structured extraction mode"):
            with self.subTest(heading=heading):
                self.assertIn(heading, self.output)

    def test_policy_requires_uncertainty_instead_of_guessing(self):
        lowered = self.all_text.lower()
        self.assertIn("do not guess", lowered)
        self.assertIn("uncertain", lowered)
        self.assertIn("1,234,500", self.core)
        self.assertIn("1,234,800", self.core)

    def test_policy_handles_boundary_duplicates_and_missing_rows(self):
        lowered = self.core.lower()
        self.assertIn("duplicate", lowered)
        self.assertIn("missing rows", lowered)
        self.assertIn("legitimate repeated", lowered)

    def test_policy_does_not_require_external_runtime(self):
        lowered = self.all_text.lower()
        self.assertIn("no external ocr runtime is required", lowered)
        self.assertIn("native vision", lowered)

    def test_policy_does_not_claim_crop_when_capability_is_absent(self):
        lowered = self.core.lower()
        self.assertIn("only when the host actually exposes", lowered)
        self.assertIn("do not claim", lowered)
        self.assertIn("crop", lowered)
        self.assertIn("zoom", lowered)

    def test_precision_pass_names_sensitive_value_classes(self):
        lowered = self.core.lower()
        for token in ("dates", "currency", "counts", "percentages", "tickers", "identifiers", "row/column"):
            with self.subTest(token=token):
                self.assertIn(token, lowered)

    def test_policy_is_evidence_only_and_forbids_pattern_completion(self):
        lowered = self.all_text.lower()
        self.assertIn("evidence-only", lowered)
        self.assertIn("reconstruction is not completion", lowered)
        self.assertIn("recurring purchase patterns are not evidence", lowered)
        self.assertIn("missing evidence must remain missing", lowered)

    def test_structured_rows_must_be_visually_verified(self):
        lowered = self.all_text.lower()
        self.assertIn("confirm that the row", lowered)
        self.assertIn("visibly present", lowered)
        self.assertIn("never create a missing row", lowered)
        self.assertIn("do not populate a field from contextual expectation", lowered)

    def test_final_audit_removes_untraceable_records(self):
        lowered = self.core.lower()
        self.assertIn("trace", lowered)
        self.assertIn("visible evidence", lowered)
        self.assertIn("remove", lowered)


if __name__ == "__main__":
    unittest.main()
