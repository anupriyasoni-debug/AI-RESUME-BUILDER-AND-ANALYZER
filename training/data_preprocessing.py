"""
Data Preprocessing Pipeline for Local AI Models.
Handles dataset loading, text cleaning, feature extraction, and dataset splitting.
"""

import os
import re
import pandas as pd
from typing import Tuple, List, Optional


def clean_resume_text(text: str) -> str:
    """
    Cleans raw resume or job description text:
    - Removes URLs and email addresses
    - Removes non-alphanumeric symbols while preserving technical terms (C++, C#, etc.)
    - Collapses multiple whitespace
    """
    if not isinstance(text, str):
        return ""
    text = re.sub(r"http\S+\s*", " ", text)
    text = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", " ", text)
    text = re.sub(r"[^\w\s+#.-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def inspect_dataset(file_path: str) -> dict:
    """
    Inspects a dataset file and returns metadata regarding row count, columns, and sample labels.
    """
    if not os.path.exists(file_path):
        return {"exists": False, "error": f"File not found: {file_path}"}

    try:
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
        elif file_path.endswith(".json"):
            df = pd.read_json(file_path)
        else:
            return {"exists": True, "supported": False, "error": "Unsupported file format."}

        return {
            "exists": True,
            "supported": True,
            "rows": len(df),
            "columns": list(df.columns),
            "sample_head": df.head(3).to_dict(orient="records"),
        }
    except Exception as exc:
        return {"exists": True, "error": str(exc)}


def load_and_preprocess_dataset(
    file_path: str,
    text_column: str = "Resume",
    label_column: Optional[str] = "Category",
) -> Tuple[List[str], Optional[List[str]]]:
    """
    Loads dataset, cleans text, and extracts labels for supervised learning.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dataset not found at {file_path}. Please place a dataset in data/.")

    df = pd.read_csv(file_path) if file_path.endswith(".csv") else pd.read_json(file_path)

    if text_column not in df.columns:
        # Fallback to common text column names
        for alt in ["resume", "Resume_str", "text", "Job Description", "job_description"]:
            if alt in df.columns:
                text_column = alt
                break
        else:
            raise KeyError(f"Text column '{text_column}' not found. Available columns: {list(df.columns)}")

    texts = [clean_resume_text(t) for t in df[text_column].fillna("").astype(str)]

    labels = None
    if label_column and label_column in df.columns:
        labels = df[label_column].fillna("Unknown").astype(str).tolist()

    return texts, labels
