# AI Resume Analyzer & Builder

## 📌 Overview
This project is a Streamlit-based web application that helps users **analyze an existing resume** for ATS (Applicant Tracking System) compatibility and **build a new resume from scratch**, exporting it as a downloadable, beautifully styled PDF.

The application runs **100% locally and offline** without any external AI API keys, cloud inference services, or subscription dependencies. It features a modular architecture that combines transparent rule-based NLP, local TF-IDF semantic matching, and a dedicated training pipeline for integrating your own custom-trained machine learning models.

---

## ✅ Features Implemented

| Feature | Status | Engine / Algorithm |
|---|---|---|
| Upload resume (PDF/DOCX) & text extraction | ✅ Done | PyMuPDF (`pymupdf`) + `python-docx` (with `pypdf` fallback) |
| ATS score (0–100) multi-factor breakdown | ✅ Done | Section, skill, length, and impact heuristic weighting |
| Skill & keyword detection | ✅ Done | Domain taxonomy dictionary across 10 career tracks |
| Section detection & gap detection | ✅ Done | Header normalization & expected section auditing |
| Resume-to-Job-Description match | ✅ Done | Local TF-IDF Vectorization & Cosine Similarity |
| Bullet impact & action-verb checks | ✅ Done | Action-verb scanning + metric/quantification checks |
| Grammar & text-formatting checks | ✅ Done | Local pattern matching (double words, agreement, line lengths) |
| Local AI Bullet Refiner (6 modes) | ✅ Done | Local rule-based NLP rewriter (`local_model.py`) |
| Live writing tips & contextual suggestions | ✅ Done | Rule-based section analyzer (`local_model.py`) |
| Resume Version Comparison | ✅ Done | Multi-factor comparative scoring & diff report |
| Modular Machine Learning Pipeline | ✅ Done | `training/` pipeline for custom model training & evaluation |
| Resume Builder with interactive PDF export | ✅ Done | `fpdf2` with multiple color palettes and typography |

---

## 🧱 Tech Stack
- **Frontend / UI:** Streamlit
- **PDF Text Extraction:** PyMuPDF (`pymupdf`), `PyPDF2`
- **DOCX Text Extraction:** `python-docx`
- **PDF Generation:** `fpdf2`
- **Local AI & NLP Engine:** Pure Python + NumPy TF-IDF and rule-based heuristics (`local_model.py`)
- **Model Training Pipeline:** `scikit-learn` (for training custom classifiers)
- **Local Storage:** SQLite (`resumes.db`) for saving builder versions

---

## 📂 Project Structure
```
AI-RESUME-BUILDER-AND-ANALYZER/
├── app.py                      # Main Streamlit app (navigation + UI)
├── analyzer.py                 # Text extraction, taxonomy detection, ATS scoring
├── local_model.py              # Local NLP, TF-IDF cosine similarity, rewriter & base model
├── resume_builder.py           # Resume Builder form UI & PDF generator integration
├── resume_comparison.py        # Version comparison, local scoring, and diff report
├── pdf_generator.py            # Builds the downloadable resume PDF
├── icons.py                    # SVG iconography for UI
├── style.py                    # Custom CSS typography & themes
├── requirements.txt            # Python dependencies (local-only, zero API SDKs)
├── env.example                 # Configuration template for local directories
├── resumes.db                  # Local SQLite database for saved resumes
├── data/                       # Directory for training datasets (Kaggle CSVs)
│   ├── raw/                    # Raw downloaded datasets
│   └── README.md               # Guide on supported dataset formats & schemas
├── models/                     # Saved local model artifacts (.joblib, metadata)
│   └── README.md               # Model loading documentation
├── training/                   # Modular ML training pipeline
│   ├── __init__.py
│   ├── data_preprocessing.py   # Dataset loading, cleaning, and tokenization
│   ├── train_classifier.py     # Script to train and save a local model
│   └── evaluate.py             # Accuracy, precision, recall, and F1 evaluation
└── README.md                   # This documentation
```

---

## ⚙️ How to Run Locally

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch the Application
```bash
python -m streamlit run app.py
```
The app will automatically launch in your browser at `http://localhost:8501`. No API keys or `.env` file configuration are required. The interface uses local system fonts and does not make external network requests.

---

## 🧠 Optional: Training a Local Machine Learning Classifier

The training pipeline in `training/` allows you to train a **supervised text classifier** to predict a candidate's broad resume role or domain category (e.g. *Data Science*, *DevOps*, *Java Developer*).

> **Important Scope Note:** The trained classifier specifically predicts the resume's role/domain label. Skill extraction (rule-based taxonomy), resume scoring (transparent weighted formula), job-description matching (TF-IDF cosine similarity), and bullet rewriting (rule-based NLP) remain local algorithms and are not modified by this classifier.

To train and integrate your own local classifier:

1. **Install Training Dependencies:**
   ```bash
   pip install -r requirements-training.txt
   ```
2. **Obtain and Place a Dataset:**
   Download a labeled resume dataset (e.g. Kaggle's `UpdatedResumeDataSet.csv` or `Resume.csv`) and place it in `data/raw/` (e.g., `data/raw/UpdatedResumeDataSet.csv`).
3. **Run Training Script:**
   ```bash
   python training/train_classifier.py --data data/raw/UpdatedResumeDataSet.csv
   ```
4. **Inspect Metrics:** The script evaluates test-set precision, recall, and F1-score, and automatically saves:
   - `models/resume_classifier.joblib`
   - `models/tfidf_vectorizer.joblib`
   - `models/model_metadata.json`
5. **Activate Trained Classifier in App:**
   Create a `.env` file from `env.example` and set:
   ```env
   USE_CUSTOM_MODEL=true
   ```
   When active, the app displays the classifier's predicted candidate role category during resume analysis.
