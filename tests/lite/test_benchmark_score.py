"""Tests for LongImageOCR Lite native-vs-Lite benchmark scoring."""

import unittest
from pathlib import Path

from lite.benchmark.score import compare_runs, score_case


REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "tests" / "lite" / "fixtures"


class TestLiteBenchmarkScore(unittest.TestCase):
    def test_score_case_penalizes_wrong_precision_digit(self):
        gt = ["합계 1,234,500원"]
        wrong = ["합계 1,234,800원"]
        exact = ["합계 1,234,500원"]
        wrong_score = score_case(gt, wrong)
        exact_score = score_case(gt, exact)
        self.assertLess(wrong_score["numeric_token_accuracy"], exact_score["numeric_token_accuracy"])
        self.assertGreater(wrong_score["cer"], exact_score["cer"])

    def test_score_case_penalizes_duplicate_boundary_row(self):
        gt = ["A 100", "B 200", "C 300"]
        pred = ["A 100", "B 200", "B 200", "C 300"]
        score = score_case(gt, pred)
        self.assertEqual(score["duplicate_line_count"], 1.0)
        self.assertLess(score["line_precision"], 100.0)

    def test_compare_runs_reports_native_and_lite_metrics(self):
        result = compare_runs(FIXTURES / "precision_conflict")
        self.assertIn("native", result)
        self.assertIn("lite", result)
        self.assertIn("lite_improved_any_objective_metric", result)
        self.assertIn("lite_regressed_numeric_accuracy", result)

    def test_compare_runs_marks_improvement_when_lite_is_better(self):
        result = compare_runs(FIXTURES / "boundary_repeat")
        self.assertTrue(result["lite_improved_any_objective_metric"])
        self.assertFalse(result["lite_regressed_numeric_accuracy"])
        self.assertGreaterEqual(result["lite"]["line_f1"], result["native"]["line_f1"])


if __name__ == "__main__":
    unittest.main()
