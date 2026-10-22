"""
Model Training Script for Resume Classification and Matching.
Trains a local machine learning model, evaluates it, and saves artifacts into models/.
Usage:
    python training/train_classifier.py --data data/raw/UpdatedResumeDataSet.csv
"""

import os
import sys
import json
import argparse
from datetime import datetime

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from training.data_preprocessing import load_and_preprocess_dataset
from training.evaluate import evaluate_predictions, print_evaluation_report


def train_model(
    data_path: str,
    output_dir: str = "models",
    test_size: float = 0.2,
    random_state: int = 42,
):
    """
    Trains a local supervised text classifier on resume data.
    """
    print(f"[*] Starting local model training pipeline...")
    print(f"[*] Dataset: {data_path}")

    if not os.path.exists(data_path):
        print(f"\n[!] Dataset file not found at: {data_path}")
        print("[*] To train your model:")
        print("    1. Download a Kaggle dataset (e.g., UpdatedResumeDataSet.csv or Resume.csv).")
        print(f"    2. Place it in the 'data/raw/' directory.")
        print(f"    3. Re-run: python training/train_classifier.py --data {data_path}\n")
        return False

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.model_selection import train_test_split
        from sklearn.linear_model import LogisticRegression
        import joblib
    except ImportError:
        print("\n[!] scikit-learn is required for model training.")
        print("[*] Install it by running: pip install scikit-learn\n")
        return False

    # 1. Load and Preprocess Data
    print("[*] Step 1: Loading and preprocessing dataset...")
    texts, labels = load_and_preprocess_dataset(data_path)
    if not labels or len(set(labels)) < 2:
        print("[!] Dataset must contain at least 2 target class labels for classification.")
        return False

    print(f"    Loaded {len(texts)} samples across {len(set(labels))} classes.")

    # 2. Train/Test Split
    print("[*] Step 2: Splitting into train and test sets...")
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=test_size, random_state=random_state, stratify=labels
    )

    # 3. Vectorization
    print("[*] Step 3: Fitting TF-IDF Vectorizer...")
    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), sublinear_tf=True)
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    # 4. Model Training
    print("[*] Step 4: Training Classifier (Logistic Regression)...")
    clf = LogisticRegression(max_iter=1000, C=1.0)
    clf.fit(X_train_vec, y_train)

    # 5. Model Evaluation
    print("[*] Step 5: Evaluating model on held-out test set...")
    y_pred = clf.predict(X_test_vec)
    metrics = evaluate_predictions(y_test, list(y_pred))
    print_evaluation_report(metrics)

    # 6. Save Artifacts
    print(f"[*] Step 6: Saving trained model artifacts to {output_dir}/...")
    os.makedirs(output_dir, exist_ok=True)
    model_file = os.path.join(output_dir, "resume_classifier.joblib")
    vec_file = os.path.join(output_dir, "tfidf_vectorizer.joblib")
    meta_file = os.path.join(output_dir, "model_metadata.json")

    joblib.dump(clf, model_file)
    joblib.dump(vectorizer, vec_file)

    metadata = {
        "created_at": datetime.now().isoformat(),
        "model_type": "LogisticRegression",
        "num_classes": len(set(labels)),
        "classes": sorted(list(set(labels))),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "test_accuracy": metrics["accuracy"],
        "macro_f1": metrics["macro_f1"],
    }
    with open(meta_file, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"[✓] Model successfully saved to {model_file}")
    print(f"[✓] Vectorizer saved to {vec_file}")
    print(f"[✓] Metadata saved to {meta_file}")
    print("\nTo activate this trained model in your app, set USE_CUSTOM_MODEL=true in your .env file.\n")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train a local resume classification model.")
    parser.add_argument("--data", type=str, default="data/raw/UpdatedResumeDataSet.csv", help="Path to input CSV dataset")
    parser.add_argument("--output", type=str, default="models", help="Directory to save trained model artifacts")
    args = parser.parse_args()

    train_model(data_path=args.data, output_dir=args.output)
