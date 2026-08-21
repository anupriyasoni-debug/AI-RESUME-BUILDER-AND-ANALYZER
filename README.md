# AI Resume Analyzer & Builder — Week 1 Submission

## 📌 Overview
This project is a Streamlit-based web application that helps users **analyze an existing resume** for ATS (Applicant Tracking System) compatibility and **build a new resume from scratch**, exporting it as a downloadable PDF. It combines rule-based text analysis with an optional AI (OpenAI) layer for smarter improvement suggestions.

**Goal for Week 1:** Build and validate a working end-to-end MVP — upload → analyze → score → suggest, plus a functional resume builder → PDF export.

---

## ✅ Features Implemented This Week

| Feature | Status |
|---|---|
| Upload resume (PDF/DOCX) and extract text | ✅ Done |
| ATS score (0–100) based on sections, skills, length, formatting | ✅ Done |
| Skill detection from a keyword database | ✅ Done |
| Section detection (contact, summary, education, experience, skills, projects, certifications) | ✅ Done |
| Missing section warnings | ✅ Done |
| Rule-based improvement suggestions | ✅ Done |
| Optional OpenAI-powered suggestions (via `.env`) | ✅ Done |
| Resume Builder form (personal info, education, experience, projects, skills, certifications) | ✅ Done |
| Generate & download builder output as PDF | ✅ Done |
| Simple two-page Streamlit UI (Analyzer / Builder) | ✅ Done |

---

## 🧱 Tech Stack
- **Frontend/App framework:** Streamlit
- **PDF text extraction:** PyPDF2
- **DOCX text extraction:** python-docx
- **PDF generation:** fpdf2
- **AI suggestions (optional):** OpenAI API (`gpt-4o-mini`)
- **Config management:** python-dotenv

---

## 📂 Project Structure
```
resume_app/
├── app.py               # Main Streamlit app (navigation + UI)
├── analyzer.py           # Text extraction, skill/section detection, ATS scoring, suggestions
├── resume_builder.py     # Resume Builder form UI
├── pdf_generator.py      # Builds the downloadable resume PDF
├── requirements.txt      # Python dependencies
├── .env.example           # Template for OpenAI API key
└── README.md              # This file
```

---

## ⚙️ Setup & Run
```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Enable AI suggestions
cp .env.example .env
# edit .env → OPENAI_API_KEY=sk-...

# 4. Run the app
streamlit run app.py
```
App opens at `http://localhost:8501`.

---

## 🧠 How the ATS Score Works
The score (0–100) is a weighted sum of four checks, all computed in `analyzer.py`:

| Component | Weight | Logic |
|---|---|---|
| Section completeness | 40 pts | % of expected sections found (contact, summary, education, experience, skills, projects, certifications) |
| Skill keyword matches | 30 pts | Number of skills found against a curated skills database (capped at 15 skills) |
| Resume length | 15 pts | Ideal range: 300–900 words |
| Formatting signals | 15 pts | Presence of strong action verbs (developed, led, implemented, etc.) |

This is intentionally simple and transparent (no black-box scoring) so it's easy to explain in the submission and to extend later.

---

## 🖥️ App Flow
**Resume Analyzer**
1. Upload a `.pdf` or `.docx` resume
2. App extracts raw text
3. App detects skills, sections, and missing sections
4. ATS score is calculated and shown with a progress bar
5. Improvement suggestions are displayed (rule-based or AI-based)

**Resume Builder**
1. Fill in personal details, education, experience, projects, skills, certifications
2. Click "Generate Resume PDF"
3. Download the formatted resume

---

## ⚠️ Known Limitations (to address in later weeks)
- Skill detection relies on a fixed keyword list — no fuzzy matching or synonym handling yet
- Scanned/image-based PDFs (no embedded text layer) won't extract text — OCR not implemented
- No resume-vs-job-description matching yet (planned for a future week)
- PDF builder layout is single-template only — no style/theme options yet
- No persistence layer — builder data is not saved between sessions

---

## 🗺️ Planned for Next Week
- Add job description matching (compare resume keywords against a pasted JD)
- Add OCR fallback for scanned PDF resumes
- Add multiple resume templates/themes in the builder
- Improve skill detection with a larger, categorized skill taxonomy
- Add basic session persistence (save/load builder drafts)

---

## 📸 Screenshots
*(Add screenshots of the Analyzer and Builder pages here before submitting.)*

---

## 👤 Author
Anupriya — AI/ML student, Week 1 submission
