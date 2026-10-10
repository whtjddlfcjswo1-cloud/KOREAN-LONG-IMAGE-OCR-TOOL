"""Benchmark evaluator primitives used by LongImageOCR regression tests.

The full A-E benchmark dataset/artifacts are distributed with the preview release archive.
This module keeps the evaluation algorithms in source control so CI can independently verify
Hungarian 1-to-1 matching, CER/WER insertion/deletion penalties, and table metrics.
"""

import difflib
from collections import Counter
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
from scipy.optimize import linear_sum_assignment


def calculate_text_similarity(pred: str, gt: str) -> float:
    """Whitespace-insensitive normalized similarity."""
    p_clean = "".join(pred.split()).lower()
    g_clean = "".join(gt.split()).lower()
    if not p_clean and not g_clean:
        return 1.0
    if not p_clean or not g_clean:
        return 0.0
    return difflib.SequenceMatcher(None, p_clean, g_clean).ratio()


def compute_sequence_levenshtein(s1: Any, s2: Any) -> int:
    """Levenshtein-style distance over character strings or token lists."""
    matcher = difflib.SequenceMatcher(None, s1, s2)
    dist = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "replace":
            dist += max(i2 - i1, j2 - j1)
        elif tag == "insert":
            dist += j2 - j1
        elif tag == "delete":
            dist += i2 - i1
    return dist


def compute_standard_cer(pred_lines: List[str], gt_lines: List[str]) -> float:
    """Character Error Rate including insertions, deletions, and substitutions."""
    gt_chars = list("".join("".join(gt_lines).split()))
    pred_chars = list("".join("".join(pred_lines).split()))
    if not gt_chars:
        return 0.0 if not pred_chars else 1.0
    return round(compute_sequence_levenshtein(gt_chars, pred_chars) / len(gt_chars), 4)


def compute_standard_wer(pred_lines: List[str], gt_lines: List[str]) -> float:
    """Word Error Rate including insertions, deletions, and substitutions."""
    gt_words = " ".join(gt_lines).split()
    pred_words = " ".join(pred_lines).split()
    if not gt_words:
        return 0.0 if not pred_words else 1.0
    return round(compute_sequence_levenshtein(gt_words, pred_words) / len(gt_words), 4)


def hungarian_bipartite_match(
    recognized_lines: List[str],
    gt_lines: List[str],
    sim_threshold: float = 0.60,
) -> Tuple[List[Tuple[int, int, float]], List[int], List[int]]:
    """Maximum-cardinality, maximum-similarity 1-to-1 matching via Hungarian assignment."""
    clean_recs = [r.strip() for r in recognized_lines]
    n, m = len(clean_recs), len(gt_lines)
    if n == 0 or m == 0:
        return [], list(range(m)), list(range(n))

    sim_matrix = np.zeros((n, m), dtype=float)
    for i, rec in enumerate(clean_recs):
        if not rec:
            continue
        len_r = len(rec)
        for j, gt in enumerate(gt_lines):
            len_g = len(gt)
            if len_r + len_g == 0:
                sim_matrix[i, j] = 1.0
                continue
            if (2.0 * min(len_r, len_g)) / (len_r + len_g) < sim_threshold:
                continue
            sim_matrix[i, j] = calculate_text_similarity(rec, gt)

    large_c = 1000.0
    profit = np.zeros((n, m), dtype=float)
    valid_mask = sim_matrix >= sim_threshold
    profit[valid_mask] = large_c + sim_matrix[valid_mask]

    dim = max(n, m)
    cost_matrix = np.full((dim, dim), large_c * 2, dtype=float)
    cost_matrix[:n, :m] = (large_c * 2) - profit
    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    matches: List[Tuple[int, int, float]] = []
    matched_recs: Set[int] = set()
    matched_gts: Set[int] = set()
    for r, c in zip(row_ind, col_ind):
        if r < n and c < m and sim_matrix[r, c] >= sim_threshold:
            matches.append((int(r), int(c), round(float(sim_matrix[r, c]), 4)))
            matched_recs.add(int(r))
            matched_gts.add(int(c))

    unmatched_gts = [j for j in range(m) if j not in matched_gts]
    unmatched_recs = [i for i in range(n) if clean_recs[i] and i not in matched_recs]
    return matches, unmatched_gts, unmatched_recs


def compute_line_metrics(
    matches: List[Tuple[int, int, float]], total_recs: int, total_gts: int
) -> Tuple[float, float, float]:
    matched = len(matches)
    recall = matched / total_gts * 100 if total_gts else 0.0
    precision = matched / total_recs * 100 if total_recs else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return round(precision, 2), round(recall, 2), round(f1, 2)


def evaluate_table_domain(
    recognized_lines: List[str], gt_lines: List[str], output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """Compact table evaluator with one-to-one repeated-cell accounting."""
    gt_cells = [c.strip() for line in gt_lines for c in line.strip().strip("|").split("|") if c.strip()]
    rec_cells = [c.strip() for line in recognized_lines for c in line.strip().strip("|").split("|") if c.strip()]
    gt_counter, rec_counter = Counter(gt_cells), Counter(rec_cells)
    matched = sum(min(rec_counter[k], count) for k, count in gt_counter.items())
    recall = matched / len(gt_cells) * 100 if gt_cells else 0.0
    precision = matched / len(rec_cells) * 100 if rec_cells else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "domain": "Table",
        "cell_recall_pct": round(recall, 2),
        "cell_precision_pct": round(precision, 2),
        "cell_f1_pct": round(f1, 2),
        "cer": compute_standard_cer(recognized_lines, gt_lines),
    }
