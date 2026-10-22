"""Train/evaluate a local multi-label model for broad job-function labels.

Separate from train_classifier.py (single-label resume classification). Reads
source CSVs only and writes model artifacts to a dedicated output directory.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "models" / "job_skill_classifier"
ARTIFACT_NAMES = ("job_skill_pipeline.joblib", "metrics.json", "metadata.json")


def load_job_skill_labels(data_dir: Path) -> dict[str, list[str]]:
    """Load skill mappings while preserving job IDs as text."""
    skills_path = data_dir / "mappings" / "skills.csv"
    associations_path = data_dir / "jobs" / "job_skills.csv"
    for path in (skills_path, associations_path):
        if not path.is_file():
            raise FileNotFoundError(f"Required CSV not found: {path}")

    skills = pd.read_csv(skills_path, dtype="string", keep_default_na=False)
    associations = pd.read_csv(associations_path, dtype="string", keep_default_na=False)
    if not {"skill_abr", "skill_name"}.issubset(skills.columns):
        raise ValueError(f"{skills_path} must contain skill_abr and skill_name")
    if not {"job_id", "skill_abr"}.issubset(associations.columns):
        raise ValueError(f"{associations_path} must contain job_id and skill_abr")

    skills = skills[["skill_abr", "skill_name"]].copy()
    skills["skill_abr"] = skills["skill_abr"].str.strip()
    skills["skill_name"] = skills["skill_name"].str.strip()
    skills = skills[(skills.skill_abr != "") & (skills.skill_name != "")].drop_duplicates()
    code_to_name = dict(zip(skills.skill_abr, skills.skill_name))

    associations = associations[["job_id", "skill_abr"]].copy()
    associations["job_id"] = associations["job_id"].str.strip()
    associations["skill_abr"] = associations["skill_abr"].str.strip()
    associations = associations[(associations.job_id != "") & (associations.skill_abr != "")]
    associations["skill_name"] = associations["skill_abr"].map(code_to_name)
    associations = associations.dropna(subset=["skill_name"]).drop_duplicates(["job_id", "skill_name"])
    grouped = associations.groupby("job_id", sort=False)["skill_name"].agg(lambda values: sorted(set(values)))
    return grouped.to_dict()


def load_examples(data_dir: Path, labels_by_job: dict[str, list[str]], chunksize: int,
                  max_samples: int | None, seed: int) -> tuple[list[str], list[list[str]], list[str], dict[str, int]]:
    """Stream postings; pilot caps use reservoir sampling across the whole CSV."""
    postings_path = data_dir / "postings.csv"
    if not postings_path.is_file():
        raise FileNotFoundError(f"Required CSV not found: {postings_path}")

    header = pd.read_csv(postings_path, nrows=0, encoding="utf-8")
    required = {"job_id", "title", "description"}
    if not required.issubset(header.columns):
        raise ValueError(f"{postings_path} must contain {sorted(required)}")
    columns = ["job_id", "title", "description"]
    has_company_id = "company_id" in header.columns
    if has_company_id:
        columns.append("company_id")
    dtypes = {name: "string" for name in columns}

    rng = random.Random(seed)
    records: list[tuple[str, list[str], str]] = []
    stats = Counter()
    for chunk in pd.read_csv(
        postings_path,
        usecols=columns,
        dtype=dtypes,
        keep_default_na=False,
        chunksize=chunksize,
        encoding="utf-8",
        on_bad_lines="error",
    ):
        stats["posting_rows_scanned"] += len(chunk)
        for row in chunk.itertuples(index=False, name=None):
            job_id, title, description = (str(value).strip() for value in row[:3])
            company_id = str(row[3]).strip() if has_company_id and len(row) > 3 else ""
            job_labels = labels_by_job.get(job_id, [])
            if not job_labels:
                continue
            text = " ".join(part for part in (title, description) if part).strip()
            if not text:
                stats["empty_text_rows"] += 1
                continue
            # Missing company IDs become per-job groups, so unrelated unknowns do not collapse together.
            group = f"company:{company_id}" if company_id else f"job:{job_id}"
            record = (text, job_labels, group)
            stats["labeled_examples_seen"] += 1
            if max_samples is None:
                records.append(record)
            elif len(records) < max_samples:
                records.append(record)
            else:
                replacement = rng.randrange(stats["labeled_examples_seen"])
                if replacement < max_samples:
                    records[replacement] = record

    stats["examples_used"] = len(records)
    return ([r[0] for r in records], [r[1] for r in records],
            [r[2] for r in records], dict(stats))


def split_by_company(targets: np.ndarray, groups: list[str], test_size: float,
                     validation_size: float, seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Create train/validation/test partitions with no company overlap."""
    from sklearn.model_selection import GroupShuffleSplit

    indices = np.arange(len(groups))
    outer = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=seed)
    train_validation, test = next(outer.split(indices, targets, groups))
    validation_fraction_of_remainder = validation_size / (1.0 - test_size)
    inner = GroupShuffleSplit(n_splits=1, test_size=validation_fraction_of_remainder,
                              random_state=seed + 1)
    train_relative, validation_relative = next(
        inner.split(train_validation, targets[train_validation], [groups[i] for i in train_validation])
    )
    train = train_validation[train_relative]
    validation = train_validation[validation_relative]

    train_groups = {groups[i] for i in train}
    validation_groups = {groups[i] for i in validation}
    test_groups = {groups[i] for i in test}
    if train_groups & validation_groups or train_groups & test_groups or validation_groups & test_groups:
        raise RuntimeError("Company groups leaked across the train/validation/test split.")
    return train, validation, test


def calibrate_thresholds(y_true: np.ndarray, probabilities: np.ndarray, class_names: list[str],
                         minimum_validation_support: int) -> tuple[dict[str, float], dict[str, int]]:
    """Select per-label F1 thresholds on validation only; low-support labels use 0.5."""
    from sklearn.metrics import f1_score

    thresholds: dict[str, float] = {}
    supports: dict[str, int] = {}
    candidates = np.round(np.arange(0.10, 0.91, 0.05), 2)
    for index, name in enumerate(class_names):
        truth = y_true[:, index]
        support = int(truth.sum())
        supports[name] = support
        if support < minimum_validation_support:
            thresholds[name] = 0.5
            continue
        scores = [float(f1_score(truth, probabilities[:, index] >= threshold, zero_division=0))
                  for threshold in candidates]
        best = max(range(len(candidates)),
                   key=lambda i: (scores[i], -abs(float(candidates[i]) - 0.5), float(candidates[i])))
        thresholds[name] = float(candidates[best])
    return thresholds, supports


def build_metrics(y_true: np.ndarray, y_pred: np.ndarray, class_names: list[str]) -> dict[str, Any]:
    from sklearn.metrics import (accuracy_score, f1_score, hamming_loss,
                                 precision_score, recall_score)

    per_label: dict[str, dict[str, Any]] = {}
    for idx, name in enumerate(class_names):
        per_label[name] = {
            "support": int(y_true[:, idx].sum()),
            "predicted": int(y_pred[:, idx].sum()),
            "precision": round(float(precision_score(y_true[:, idx], y_pred[:, idx], zero_division=0)), 4),
            "recall": round(float(recall_score(y_true[:, idx], y_pred[:, idx], zero_division=0)), 4),
            "f1": round(float(f1_score(y_true[:, idx], y_pred[:, idx], zero_division=0)), 4),
        }
    return {
        "test_examples": int(y_true.shape[0]),
        "micro_precision": round(float(precision_score(y_true, y_pred, average="micro", zero_division=0)), 4),
        "micro_recall": round(float(recall_score(y_true, y_pred, average="micro", zero_division=0)), 4),
        "micro_f1": round(float(f1_score(y_true, y_pred, average="micro", zero_division=0)), 4),
        "macro_precision": round(float(precision_score(y_true, y_pred, average="macro", zero_division=0)), 4),
        "macro_recall": round(float(recall_score(y_true, y_pred, average="macro", zero_division=0)), 4),
        "macro_f1": round(float(f1_score(y_true, y_pred, average="macro", zero_division=0)), 4),
        "samples_f1": round(float(f1_score(y_true, y_pred, average="samples", zero_division=0)), 4),
        "hamming_loss": round(float(hamming_loss(y_true, y_pred)), 4),
        "exact_set_accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "per_label": per_label,
    }


def check_output_is_available(output_dir: Path, overwrite: bool) -> None:
    existing = [name for name in ARTIFACT_NAMES if (output_dir / name).exists()]
    if existing and not overwrite:
        raise FileExistsError(
            f"Output artifacts already exist in {output_dir}: {', '.join(existing)}. "
            "Choose another --output directory or pass --overwrite to replace them."
        )


def train(args: argparse.Namespace) -> int:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.multiclass import OneVsRestClassifier
    from sklearn.preprocessing import MultiLabelBinarizer
    import joblib

    data_dir: Path = args.data_dir.expanduser().resolve()
    output_dir: Path = args.output.expanduser().resolve()
    check_output_is_available(output_dir, args.overwrite)
    print(f"Reading source CSVs from: {data_dir}")
    labels_by_job = load_job_skill_labels(data_dir)
    texts, labels, groups, read_stats = load_examples(
        data_dir, labels_by_job, args.chunksize, args.max_samples, args.seed
    )
    if not texts:
        raise ValueError("No postings with both text and mapped skill labels were found.")

    example_support = Counter(label for row in labels for label in set(row))
    groups_by_label: dict[str, set[str]] = defaultdict(set)
    for group, row in zip(groups, labels):
        for label in set(row):
            groups_by_label[label].add(group)
    class_names = sorted(
        name for name, support in example_support.items()
        if support >= args.min_label_support and len(groups_by_label[name]) >= args.min_label_groups
    )
    discarded = {
        name: {"examples": support, "groups": len(groups_by_label[name])}
        for name, support in example_support.items()
        if name not in class_names
    }
    allowed = set(class_names)
    filtered = [[label for label in row if label in allowed] for row in labels]
    keep = [idx for idx, row in enumerate(filtered) if row]
    texts = [texts[idx] for idx in keep]
    filtered = [filtered[idx] for idx in keep]
    groups = [groups[idx] for idx in keep]

    if len(class_names) < 2:
        raise ValueError("At least two labels must meet the minimum example and company support.")
    if len(texts) < 50:
        raise ValueError(f"Only {len(texts)} usable examples remain; need at least 50 for three-way evaluation.")

    binarizer = MultiLabelBinarizer(classes=class_names)
    targets = binarizer.fit_transform(filtered)
    train_idx, validation_idx, test_idx = split_by_company(
        targets, groups, args.test_size, args.validation_size, args.seed
    )
    y_train, y_validation, y_test = targets[train_idx], targets[validation_idx], targets[test_idx]
    train_texts = [texts[i] for i in train_idx]
    validation_texts = [texts[i] for i in validation_idx]
    test_texts = [texts[i] for i in test_idx]

    missing_train_labels = [class_names[i] for i, count in enumerate(y_train.sum(axis=0)) if count == 0]
    if missing_train_labels:
        raise ValueError(
            "Company split left these labels absent from training: " + ", ".join(missing_train_labels)
            + ". Increase sample size, lower support thresholds, or try another --seed."
        )

    vectorizer = TfidfVectorizer(
        max_features=args.max_features,
        min_df=args.min_df,
        ngram_range=(1, 2),
        sublinear_tf=True,
        dtype=np.float32,
        stop_words="english",
    )
    x_train = vectorizer.fit_transform(train_texts)
    x_validation = vectorizer.transform(validation_texts)
    x_test = vectorizer.transform(test_texts)
    classifier = OneVsRestClassifier(
        LogisticRegression(solver="liblinear", max_iter=args.max_iter),
        n_jobs=args.jobs,
    )
    print(f"Training {len(class_names)} one-vs-rest classifiers on {len(train_texts):,} postings...")
    classifier.fit(x_train, y_train)

    validation_probabilities = classifier.predict_proba(x_validation)
    thresholds, validation_support = calibrate_thresholds(
        y_validation, validation_probabilities, class_names, args.min_calibration_support
    )
    test_probabilities = classifier.predict_proba(x_test)
    fixed_predictions = (test_probabilities >= args.threshold).astype("int8")
    tuned_cutoffs = np.array([thresholds[name] for name in class_names], dtype=np.float32)
    tuned_predictions = (test_probabilities >= tuned_cutoffs).astype("int8")
    fixed_metrics = build_metrics(y_test, fixed_predictions, class_names)
    tuned_metrics = build_metrics(y_test, tuned_predictions, class_names)
    metrics = {
        "split_strategy": "company-grouped train/validation/test; validation used for threshold selection",
        "threshold_calibration": {
            "candidate_range": [0.10, 0.90],
            "step": 0.05,
            "minimum_validation_support": args.min_calibration_support,
            "validation_support_by_label": validation_support,
            "threshold_by_label": thresholds,
        },
        "fixed_threshold": {"threshold": args.threshold, **fixed_metrics},
        "validation_tuned_thresholds": tuned_metrics,
        "warning": "Metrics describe prediction of dataset-defined broad job functions, not resume-job fit or ATS accuracy.",
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump({
        "vectorizer": vectorizer,
        "classifier": classifier,
        "classes": class_names,
        "threshold_by_label": thresholds,
        "default_threshold": args.threshold,
    }, output_dir / "job_skill_pipeline.joblib", compress=3)
    metadata = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "model_type": "TF-IDF + OneVsRest LogisticRegression",
        "task": "multi-label prediction of broad job-function categories from job title and description",
        "source_files": {
            "postings.csv": str(data_dir / "postings.csv"),
            "jobs/job_skills.csv": str(data_dir / "jobs" / "job_skills.csv"),
            "mappings/skills.csv": str(data_dir / "mappings" / "skills.csv"),
        },
        "read_stats": read_stats,
        "examples_used_after_label_filter": len(texts),
        "company_groups_used": len(set(groups)),
        "split_examples": {
            "train": len(train_idx), "validation": len(validation_idx), "test": len(test_idx)
        },
        "split_groups": {
            "train": len({groups[i] for i in train_idx}),
            "validation": len({groups[i] for i in validation_idx}),
            "test": len({groups[i] for i in test_idx}),
        },
        "label_support_before_filter": {
            name: {"examples": example_support[name], "groups": len(groups_by_label[name])}
            for name in sorted(example_support)
        },
        "discarded_low_support_labels": discarded,
        "classes": class_names,
        "parameters": {
            "validation_size": args.validation_size,
            "test_size": args.test_size,
            "seed": args.seed,
            "max_features": args.max_features,
            "min_df": args.min_df,
            "max_iter": args.max_iter,
            "fixed_threshold": args.threshold,
            "min_label_support": args.min_label_support,
            "min_label_groups": args.min_label_groups,
            "min_calibration_support": args.min_calibration_support,
        },
    }
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print("\nHeld-out test evaluation")
    print(f"  examples: {len(train_idx):,} train / {len(validation_idx):,} validation / {len(test_idx):,} test")
    print(f"  company groups: {metadata['split_groups']}")
    print(f"  labels: {len(class_names)}; ignored low-support labels: {len(discarded)}")
    print(f"  fixed {args.threshold:.2f}: micro F1 {fixed_metrics['micro_f1']:.4f}; macro F1 {fixed_metrics['macro_f1']:.4f}")
    print(f"  validation-tuned: micro F1 {tuned_metrics['micro_f1']:.4f}; macro F1 {tuned_metrics['macro_f1']:.4f}")
    print(f"  Model and reports saved in: {output_dir}")
    print("  These metrics are job-function classification metrics, not resume-match or ATS scores.")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True,
                        help="Extracted archive folder with postings.csv, jobs/, and mappings/")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help=f"Dedicated output folder (default: {DEFAULT_OUTPUT})")
    parser.add_argument("--chunksize", type=int, default=5000)
    parser.add_argument("--max-samples", type=int, default=None,
                        help="Optional representative reservoir sample across the entire postings CSV")
    parser.add_argument("--min-label-support", type=int, default=20)
    parser.add_argument("--min-label-groups", type=int, default=5,
                        help="Require each retained label to occur across this many companies/groups")
    parser.add_argument("--min-calibration-support", type=int, default=10,
                        help="Use the fixed threshold for labels with fewer validation examples")
    parser.add_argument("--max-features", type=int, default=30000)
    parser.add_argument("--min-df", type=int, default=2)
    parser.add_argument("--max-iter", type=int, default=200)
    parser.add_argument("--test-size", type=float, default=0.15)
    parser.add_argument("--validation-size", type=float, default=0.15)
    parser.add_argument("--threshold", type=float, default=0.5,
                        help="Baseline probability threshold; tuned thresholds are reported separately")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--jobs", type=int, default=1,
                        help="Parallel label models; default 1 limits laptop resource use")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if args.chunksize < 1 or (args.max_samples is not None and args.max_samples < 1):
        parser.error("--chunksize and --max-samples must be positive")
    if not 0 < args.test_size < 1 or not 0 < args.validation_size < 1:
        parser.error("test and validation sizes must be between 0 and 1")
    if args.test_size + args.validation_size >= 1:
        parser.error("test and validation sizes must sum to less than 1")
    if not 0 < args.threshold < 1:
        parser.error("--threshold must be between 0 and 1")
    if min(args.min_label_support, args.min_label_groups, args.min_calibration_support,
           args.max_features, args.min_df, args.max_iter) < 1:
        parser.error("support/features/min_df/max_iter values must be positive")
    return args


if __name__ == "__main__":
    try:
        raise SystemExit(train(parse_args()))
    except (FileNotFoundError, ValueError, FileExistsError, pd.errors.ParserError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
