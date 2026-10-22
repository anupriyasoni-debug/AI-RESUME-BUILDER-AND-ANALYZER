# Trained Models Directory (`models/`)

This directory stores serialized weights, vectorizers, and metadata for locally trained machine learning models.

## Expected Files

When training completes via `training/train_classifier.py`, the following artifacts will be saved here:

1. `resume_classifier.pkl` / `resume_classifier.joblib`: Serialized trained classifier model.
2. `tfidf_vectorizer.pkl` / `tfidf_vectorizer.joblib`: Fitted TF-IDF vectorizer containing n-gram vocabulary and IDF weights.
3. `label_encoder.pkl`: Mapping between integer classes and target role names.
4. `model_metadata.json`: Details on training date, hyperparameters, training accuracy, and test F1-scores.

## Loading in the Application

`local_model.py` automatically checks for `models/resume_classifier.joblib` or `models/resume_classifier.pkl`.
When present and enabled via `USE_CUSTOM_MODEL=true` in `.env`, the application seamlessly switches from heuristic scoring to the local ML model without requiring any changes to the Streamlit UI.
