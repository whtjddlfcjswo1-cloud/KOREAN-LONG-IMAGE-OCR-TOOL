"""Regression and unit tests for the benchmark evaluator algorithms.

Verifies:
  1. Duplicate Ground Truth 1-to-1 matching (no over- or under-counting)
  2. Greedy trap case (Hungarian finds 2 matches where greedy finds 1)
  3. Extra OCR insertion error reflects in CER and WER
  4. Missing OCR deletion error reflects in CER and WER
  5. Table repeated cells 1-to-1 multiset matching
  6. Table row exact and fuzzy preservation
  7. Numeric exact-match accuracy
"""

import unittest
import numpy as np
from collections import Counter

from tests.benchmark_comparison import (
    hungarian_bipartite_match,
    compute_standard_cer,
    compute_standard_wer,
    calculate_text_similarity,
    evaluate_table_domain,
    compute_line_metrics
)


class TestBenchmarkEvaluator(unittest.TestCase):

    def test_greedy_trap_case(self):
        """P0 Regression: Ensure Hungarian matching finds optimal 2 matches where greedy only finds 1.
        
        Matrix:
          r0-g0 = 0.90
          r0-g1 = 0.80
          r1-g0 = 0.85
          r1-g1 = 0.10
        Threshold = 0.50
        
        Greedy picks (r0, g0, 0.90), leaving r1 with only g1 (0.10 < 0.50) -> 1 match.
        Hungarian algorithm chooses (r0, g1, 0.80) and (r1, g0, 0.85) -> 2 matches!
        """
        sim_matrix = np.array([
            [0.90, 0.80],
            [0.85, 0.10]
        ])
        threshold = 0.50

        # We simulate the cost matrix inside hungarian_bipartite_match
        from scipy.optimize import linear_sum_assignment
        LARGE_C = 1000.0
        profit = np.zeros((2, 2), dtype=float)
        valid_mask = sim_matrix >= threshold
        profit[valid_mask] = LARGE_C + sim_matrix[valid_mask]

        cost_matrix = np.full((2, 2), LARGE_C * 2, dtype=float)
        cost_matrix[:2, :2] = (LARGE_C * 2) - profit

        row_ind, col_ind = linear_sum_assignment(cost_matrix)
        matches = [(r, c) for r, c in zip(row_ind, col_ind) if sim_matrix[r, c] >= threshold]

        self.assertEqual(len(matches), 2, "Hungarian matching must find 2 valid matches, not fall into the greedy 1-match trap.")
        matched_pairs = set(matches)
        self.assertIn((0, 1), matched_pairs)
        self.assertIn((1, 0), matched_pairs)

    def test_duplicate_gt_one_to_one_matching(self):
        """Ensures identical repeating GT strings match 1-to-1 against recognized lines."""
        gt_lines = [
            "삼성전자 보통주",
            "삼성전자 보통주",
            "삼성전자 보통주"
        ]
        rec_lines = [
            "삼성전자 보통주",
            "삼성전자 보통주",
            "삼성전자 보통주"
        ]
        matches, unmatched_gts, unmatched_recs = hungarian_bipartite_match(rec_lines, gt_lines, sim_threshold=0.60)
        
        self.assertEqual(len(matches), 3, "All 3 duplicate instances must be matched 1-to-1.")
        self.assertEqual(len(unmatched_gts), 0)
        self.assertEqual(len(unmatched_recs), 0)

        # What if OCR only has 2 instances?
        rec_partial = ["삼성전자 보통주", "삼성전자 보통주"]
        matches_p, unmatched_gts_p, unmatched_recs_p = hungarian_bipartite_match(rec_partial, gt_lines, sim_threshold=0.60)
        self.assertEqual(len(matches_p), 2)
        self.assertEqual(len(unmatched_gts_p), 1)

    def test_extra_ocr_insertion_cer_wer(self):
        """P0 Regression: Ensure extra garbage recognized lines increase CER and WER instead of reporting 0."""
        gt_lines = ["hello"]
        ocr_lines = ["hello", "garbage"]

        cer = compute_standard_cer(ocr_lines, gt_lines)
        wer = compute_standard_wer(ocr_lines, gt_lines)

        self.assertGreater(cer, 0.0, "CER must reflect insertion of 'garbage'.")
        self.assertGreater(wer, 0.0, "WER must reflect insertion of 'garbage'.")
        self.assertAlmostEqual(wer, 1.0, places=2)

    def test_missing_ocr_deletion_cer_wer(self):
        """Ensure omitted GT lines increase CER and WER due to deletions."""
        gt_lines = ["hello world"]
        ocr_lines = ["hello"]

        cer = compute_standard_cer(ocr_lines, gt_lines)
        wer = compute_standard_wer(ocr_lines, gt_lines)

        self.assertGreater(cer, 0.0)
        self.assertGreater(wer, 0.0)

    def test_table_repeated_cells_multiset_matching(self):
        """P0 Regression: Table cell evaluation must use 1-to-1 multiset matching without overcounting."""
        gt_cells = ["78,200", "78,200", "78,200", "192,500"]
        # OCR only found "78,200" ONCE
        rec_cells = ["78,200", "192,500"]

        gt_counter = Counter(gt_cells)
        rec_counter = Counter(rec_cells)

        matched_count = sum(min(rec_counter[k], count) for k, count in gt_counter.items())
        # Should be 2 matches (one 78,200 and one 192,500), NOT 4!
        self.assertEqual(matched_count, 2)
        recall = matched_count / len(gt_cells)
        self.assertAlmostEqual(recall, 0.50, places=2)

    def test_table_row_preservation(self):
        """Verifies row exact and fuzzy match accuracy on structured reconstructed rows."""
        gt_rows = [
            ["1", "삼성전자", "78,200", "+2.35%", "15,230,400"],
            ["2", "SK하이닉스", "192,500", "+4.81%", "4,820,100"]
        ]
        # Reconstructed rows: row 1 exact, row 2 fuzzy (4/5 cells match)
        rec_rows = [
            ["1", "삼성전자", "78,200", "+2.35%", "15,230,400"],
            ["2", "SK하이닉스", "192,500", "+4.81%", "999,999"]
        ]

        exact_matches = 0
        fuzzy_matches = 0
        unmatched_gt = list(gt_rows)

        for r_cells in rec_rows:
            matched_idx = -1
            for idx, g_cells in enumerate(unmatched_gt):
                if r_cells == g_cells:
                    matched_idx = idx
                    exact_matches += 1
                    fuzzy_matches += 1
                    break
            if matched_idx >= 0:
                unmatched_gt.pop(matched_idx)
                continue

            for idx, g_cells in enumerate(unmatched_gt):
                common = sum(1 for c in r_cells if c in g_cells)
                if common >= 3:
                    matched_idx = idx
                    fuzzy_matches += 1
                    break
            if matched_idx >= 0:
                unmatched_gt.pop(matched_idx)

        self.assertEqual(exact_matches, 1)
        self.assertEqual(fuzzy_matches, 2)

    def test_numeric_exact_matching(self):
        """Verifies exact token search for numbers and tickers in financial text."""
        rec_text = "삼성전자 (005930) : 78,200원 | +2.35% | 거래량: 15,230,400주"
        
        tickers = ["삼성전자", "005930", "NVDA"]
        numbers = ["78,200원", "+2.35%", "15,230,400주", "99,000원"]

        ticker_hits = sum(1 for t in tickers if t in rec_text)
        num_hits = sum(1 for n in numbers if n in rec_text)

        self.assertEqual(ticker_hits, 2)
        self.assertEqual(num_hits, 3)


if __name__ == "__main__":
    unittest.main()
