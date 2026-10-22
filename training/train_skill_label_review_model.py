"""Train a local binary reviewer for automatically extracted job-skill labels.

This pilot is separate from resume classification and does not change app behavior.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, balanced_accuracy_score,
                             classification_report, confusion_matrix,
                             precision_recall_fscore_support)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = PROJECT_ROOT / "data" / "processed" / "skill_labels_v6_v9_shadow5_training.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "models" / "skill_label_review_v6_v9_shadow5"
ARTIFACTS = ("skill_label_review_pipeline.joblib", "metrics.json", "metadata.json")
TEXT_COLUMNS = ("title", "skill", "requirement_type", "evidence_text")


def make_pipeline() -> Pipeline:
    return Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1,
                                  max_features=30000, sublinear_tf=True,
                                  strip_accents="unicode", lowercase=True)),
        ("classifier", LogisticRegression(class_weight="balanced",
                                           max_iter=2000, random_state=42)),
    ])


def read_dataset(path: Path) -> tuple[pd.DataFrame, list[str], list[int], list[str]]:
    if not path.is_file():
        raise FileNotFoundError(f"Training CSV not found: {path}")
    frame = pd.read_csv(path, dtype="string", keep_default_na=False, encoding="utf-8-sig")
    required = {"job_id", *TEXT_COLUMNS, "label"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Training CSV is missing required columns: {sorted(missing)}")
    frame = frame[list(required)].copy()
    for name in required:
        frame[name] = frame[name].str.strip()
    frame = frame[(frame.job_id != "") & frame.label.isin(["0", "1"])]
    frame = frame.drop_duplicates(subset=["job_id", *TEXT_COLUMNS, "label"])
    y = frame.label.astype(int).tolist()
    if set(y) != {0, 1}:
        raise ValueError("Training data must include label 0 (reject) and label 1 (keep).")
    if min(y.count(0), y.count(1)) < 5:
        raise ValueError("Need at least five reviewed rows in each class for this pilot trainer.")
    texts = [" ".join(f"{col}: {row[col]}" for col in TEXT_COLUMNS if row[col])
             for row in frame.to_dict(orient="records")]
    return frame, texts, y, frame.job_id.tolist()


def select_group_split(y: list[int], groups: list[str], test_size: float,
                       seed: int) -> tuple[list[int], list[int]]:
    """Choose a deterministic job-ID split with both labels represented in test."""
    desired_negatives = max(1, round(sum(value == 0 for value in y) * test_size))
    best: tuple[tuple[int, int, int], list[int], list[int]] | None = None
    indices = np.arange(len(y))
    for candidate_seed in range(seed, seed + 500):
        splitter = GroupShuffleSplit(n_splits=1, test_size=test_size,
                                     random_state=candidate_seed)
        train_idx, test_idx = next(splitter.split(indices, y, groups))
        if {y[i] for i in train_idx} != {0, 1} or {y[i] for i in test_idx} != {0, 1}:
            continue
        test_negatives = sum(y[i] == 0 for i in test_idx)
        score = (abs(test_negatives - desired_negatives),
                 abs(len(test_idx) - round(len(y) * test_size)), candidate_seed)
        if best is None or score < best[0]:
            best = (score, train_idx.tolist(), test_idx.tolist())
    if best is None:
        raise ValueError("Could not create a job-ID-grouped split containing both labels. Add more reviewed examples.")
    return best[1], best[2]


def train(args: argparse.Namespace) -> int:
    data_path = args.data.expanduser().resolve()
    output_dir = args.output.expanduser().resolve()
    existing = [name for name in ARTIFACTS if (output_dir / name).exists()]
    if existing and not args.overwrite:
        raise FileExistsError(f"Output artifacts already exist in {output_dir}: {', '.join(existing)}. Choose another --output or pass --overwrite.")

    frame, texts, y, groups = read_dataset(data_path)
    train_idx, test_idx = select_group_split(y, groups, args.test_size, args.seed)
    evaluation_model = make_pipeline()
    evaluation_model.fit([texts[i] for i in train_idx], [y[i] for i in train_idx])
    truth = [y[i] for i in test_idx]
    predicted = evaluation_model.predict([texts[i] for i in test_idx]).astype(int).tolist()
    precision, recall, f1, support = precision_recall_fscore_support(
        truth, predicted, labels=[0, 1], zero_division=0
    )
    metrics: dict[str, Any] = {
        "evaluation": "single holdout grouped by job_id; exploratory due to small pilot",
        "test_rows": len(test_idx),
        "test_job_groups": len({groups[i] for i in test_idx}),
        "accuracy": round(float(accuracy_score(truth, predicted)), 4),
        "balanced_accuracy": round(float(balanced_accuracy_score(truth, predicted)), 4),
        "confusion_matrix_labels_0_reject_1_keep": confusion_matrix(truth, predicted, labels=[0, 1]).tolist(),
        "classes": {
            "0_reject": {"support": int(support[0]), "precision": round(float(precision[0]), 4), "recall": round(float(recall[0]), 4), "f1": round(float(f1[0]), 4)},
            "1_keep": {"support": int(support[1]), "precision": round(float(precision[1]), 4), "recall": round(float(recall[1]), 4), "f1": round(float(f1[1]), 4)},
        },
        "classification_report": classification_report(
            truth, predicted, labels=[0, 1], target_names=["reject", "keep"],
            zero_division=0, output_dict=True),
    }

    # Fit the candidate for later experiments only after recording held-out metrics.
    final_model = make_pipeline()
    final_model.fit(texts, y)
    output_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(final_model, output_dir / ARTIFACTS[0])
    (output_dir / ARTIFACTS[1]).write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    metadata = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "model_type": "TF-IDF + class-balanced LogisticRegression",
        "task": "classify extracted job-skill label as keep (1) or reject (0)",
        "training_csv": str(data_path),
        "training_rows": len(frame),
        "training_job_ids": len(set(groups)),
        "class_counts": {"reject_0": y.count(0), "keep_1": y.count(1)},
        "feature_columns": list(TEXT_COLUMNS),
        "excluded_columns": ["job_id", "confidence", "review_note"],
        "limitations": [
            "Small pilot with only 18 rejected examples; experimental, not for automatic decisions.",
            "Holdout metrics use one job-ID-grouped split and may vary with the sample.",
            "The candidate is not wired into the app; current app behavior is unchanged.",
        ],
    }
    (output_dir / ARTIFACTS[2]).write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Training rows: {len(frame)} (keep=1: {y.count(1)}, reject=0: {y.count(0)})")
    print(f"Grouped holdout: {len(test_idx)} rows / {metrics['test_job_groups']} job IDs")
    print(f"Holdout accuracy: {metrics['accuracy']:.3f}; balanced accuracy: {metrics['balanced_accuracy']:.3f}")
    print(f"Saved model candidate and metrics in: {output_dir}")
    print("This pilot is not connected to the app and is not production-ready.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Train a pilot reviewer for extracted job-skill labels.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA,
                        help="Reviewed CSV with label 1=keep and 0=reject")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help="New directory for model and metrics")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--overwrite", action="store_true",
                        help="Replace this trainer's three artifacts in the selected output directory")
    args = parser.parse_args()
    if not 0.1 <= args.test_size <= 0.4:
        parser.error("--test-size must be between 0.1 and 0.4")
    try:
        return train(args)
    except (FileNotFoundError, FileExistsError, ValueError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
