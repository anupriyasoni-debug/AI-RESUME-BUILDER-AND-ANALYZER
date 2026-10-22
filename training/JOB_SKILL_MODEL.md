# Local Multi-Label Job-Function Model

This pipeline is separate from `train_classifier.py`, which predicts one resume category from labeled resume examples. This trainer predicts **multiple broad job-function labels** from job titles and descriptions using the LinkedIn postings archive and its skill mappings.

## Inputs

Point `--data-dir` to the extracted archive containing:

- `postings.csv` (`job_id`, `title`, `description`, and optionally `company_id`)
- `jobs/job_skills.csv` (`job_id`, `skill_abr`)
- `mappings/skills.csv` (`skill_abr`, `skill_name`)

IDs are loaded as text, and postings are streamed in chunks. A capped pilot uses reservoir sampling across the entire CSV, rather than only its first rows. The source CSV files are never modified.

## Representative pilot

From the project root in PowerShell, run:

```powershell
..\.venv\Scripts\python.exe training\train_job_skill_model.py `
  --data-dir "C:\Users\HP\OneDrive\Desktop\archive" `
  --max-samples 5000 `
  --min-label-support 5 `
  --min-label-groups 2 `
  --output models\job_skill_classifier_representative_pilot
```

The pilot scans the full postings CSV to choose a representative labeled sample. It then separates train, validation, and test data by company when company IDs are present. Thresholds are selected on validation data and reported alongside the fixed 0.5 baseline. Review `metrics.json`, especially the per-label precision, recall, and F1, before training on all records.

## Train and evaluate on all labeled postings

After reviewing the pilot, run without `--max-samples` and use a new output directory:

```powershell
..\.venv\Scripts\python.exe training\train_job_skill_model.py `
  --data-dir "C:\Users\HP\OneDrive\Desktop\archive" `
  --output models\job_skill_classifier_full
```

Artifacts are saved separately from the existing resume classifier:

- `job_skill_pipeline.joblib`
- `metrics.json`
- `metadata.json`

If an output directory already contains those artifacts, the script stops rather than replacing them. Choose a new `--output` path or explicitly pass `--overwrite` to replace them.

## Scope and limitations

The mapped labels are broad functions such as Information Technology, Sales, Management, and Engineering. They are not detailed technologies such as Python, SQL, or React. The model predicts categories attached to job postings; it does not predict resume-job fit, ATS scores, candidate quality, or semantic similarity. It is not automatically loaded into the Streamlit app. Keep the ten existing role presets and technical skill matcher until detailed labels and a separate integration review are available.
