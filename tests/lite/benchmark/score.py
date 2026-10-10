"""Score exported native-vision and LongImageOCR Lite OCR outputs."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Any

from benchmark_comparison import (
    compute_line_metrics,
    compute_standard_cer,
    compute_standard_wer,
    hungarian_bipartite_match,
)


_NUMERIC_TOKEN = re.compile(r"[+-]?\d[\d,]*(?:\.\d+)?%?")


def _numeric_tokens(lines: list[str]) -> list[str]:
    return _NUMERIC_TOKEN.findall("\n".join(lines))


def _numeric_token_accuracy(ground_truth: list[str], prediction: list[str]) -> float:
    gt_tokens = _numeric_tokens(ground_truth)
    if not gt_tokens:
        return 100.0
    pred_counter = Counter(_numeric_tokens(prediction))
    gt_counter = Counter(gt_tokens)
    matched = sum(min(count, pred_counter[token]) for token, count in gt_counter.items())
    return round(matched / len(gt_tokens) * 100.0, 2)


def _duplicate_line_count(ground_truth: list[str], prediction: list[str]) -> float:
    gt = Counter(line.strip() for line in ground_truth if line.strip())
    pred = Counter(line.strip() for line in prediction if line.strip())
    excess = sum(max(0, count - gt.get(line, 0)) for line, count in pred.items())
    return float(excess)


def score_case(ground_truth: list[str], prediction: list[str]) -> dict[str, float]:
    """Score one exported text result against line-oriented ground truth."""
    clean_gt = [line.rstrip("\n") for line in ground_truth if line.rstrip("\n")]
    clean_pred = [line.rstrip("\n") for line in prediction if line.rstrip("\n")]
    matches, _, _ = hungarian_bipartite_match(clean_pred, clean_gt)
    precision, recall, f1 = compute_line_metrics(matches, len(clean_pred), len(clean_gt))
    return {
        "cer": compute_standard_cer(clean_pred, clean_gt),
        "wer": compute_standard_wer(clean_pred, clean_gt),
        "line_precision": precision,
        "line_recall": recall,
        "line_f1": f1,
        "duplicate_line_count": _duplicate_line_count(clean_gt, clean_pred),
        "numeric_token_accuracy": _numeric_token_accuracy(clean_gt, clean_pred),
    }


def _read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def compare_runs(case_dir: Path) -> dict[str, Any]:
    """Compare native and Lite exported OCR text for one benchmark case directory."""
    case_dir = Path(case_dir)
    gt = _read_lines(case_dir / "ground_truth.txt")
    native = score_case(gt, _read_lines(case_dir / "native.txt"))
    lite = score_case(gt, _read_lines(case_dir / "lite.txt"))

    improved = any(
        (
            lite[metric] > native[metric]
            if metric in {"line_precision", "line_recall", "line_f1", "numeric_token_accuracy"}
            else lite[metric] < native[metric]
        )
        for metric in (
            "cer",
            "wer",
            "line_precision",
            "line_recall",
            "line_f1",
            "duplicate_line_count",
            "numeric_token_accuracy",
        )
    )
    return {
        "native": native,
        "lite": lite,
        "lite_improved_any_objective_metric": improved,
        "lite_regressed_numeric_accuracy": (
            lite["numeric_token_accuracy"] < native["numeric_token_accuracy"]
        ),
    }
