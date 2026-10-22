# Reviewed Job-Skill Label Model (Pilot)

This separate experiment predicts whether an extracted job-skill row should be kept (1) or rejected (0), using title, skill, requirement type, and evidence text. It is separate from resume-category classification and the O*NET broad job-function model.

The combined V6, V9, and five newly reviewed shadow rows has 558 rows: 483 keep and 75 reject. The latest grouped holdout reached 0.866 accuracy and 0.333 recall for the reject class (5 of 15 rejected examples detected). These results are weak and unstable; the candidate is not production-ready. The script writes an isolated model and does not change or load into the app.

Run from the project root in PowerShell:

```powershell
..\.venv\Scripts\python.exe training\train_skill_label_review_model.py
```

Default input: `data/processed/skill_labels_v6_v9_shadow5_training.csv`. Default output: `models/skill_label_review_v6_v9_shadow5/`.

To use the earlier 553-row set instead, specify it explicitly:

```powershell
..\.venv\Scripts\python.exe training\train_skill_label_review_model.py `
  --data "data\processed\skill_labels_v6_v9_training.csv" `
  --output "models\skill_label_review_v6_v9"
```

The script refuses to overwrite existing model artifacts unless `--overwrite` is supplied.

Artifacts: `skill_label_review_pipeline.joblib`, `metrics.json`, and `metadata.json`.

The latest holdout contains only 15 rejects, so its metrics remain exploratory. The model is not connected to the app because it misses most held-out rejects. Review more false-positive examples and evaluate on a new sample before considering app integration.
