"""
Model Evaluation Pipeline for Local Machine Learning Models.
Calculates classification metrics, confusion matrices, and generates evaluation summaries.
"""

from typing import Dict, Any, List


def evaluate_predictions(y_true: List[Any], y_pred: List[Any]) -> Dict[str, Any]:
    """
    Computes classification accuracy, per-class metrics, and summary stats
    using standard Python/NumPy, with optional scikit-learn metrics if installed.
    """
    if len(y_true) != len(y_pred) or len(y_true) == 0:
        return {"error": "Invalid or empty prediction sets."}

    total = len(y_true)
    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    accuracy = correct / total

    classes = sorted(list(set(y_true + y_pred)))
    per_class = {}

    for c in classes:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == c and p == c)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != c and p == c)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == c and p != c)

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        per_class[str(c)] = {
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "support": sum(1 for t in y_true if t == c),
        }

    macro_f1 = sum(v["f1_score"] for v in per_class.values()) / len(per_class) if per_class else 0.0

    return {
        "total_samples": total,
        "accuracy": round(accuracy, 4),
        "macro_f1": round(macro_f1, 4),
        "per_class": per_class,
    }


def print_evaluation_report(metrics: Dict[str, Any]):
    """Pretty prints evaluation metrics to console."""
    if "error" in metrics:
        print(f"Evaluation Error: {metrics['error']}")
        return

    print("=" * 60)
    print("LOCAL MODEL EVALUATION REPORT")
    print("=" * 60)
    print(f"Total Test Samples: {metrics['total_samples']}")
    print(f"Overall Accuracy:   {metrics['accuracy'] * 100:.2f}%")
    print(f"Macro F1-Score:     {metrics['macro_f1']:.4f}")
    print("-" * 60)
    print(f"{'Class':<25} {'Precision':<10} {'Recall':<10} {'F1-Score':<10} {'Support'}")
    print("-" * 60)
    for cls_name, vals in metrics["per_class"].items():
        print(f"{cls_name[:24]:<25} {vals['precision']:<10.3f} {vals['recall']:<10.3f} {vals['f1_score']:<10.3f} {vals['support']}")
    print("=" * 60)
