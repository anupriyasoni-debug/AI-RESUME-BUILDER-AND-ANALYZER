import os
import re
import docx
import io
from pypdf import PdfReader
from dotenv import load_dotenv

load_dotenv()

JOB_TAXONOMY = {
    "AI Engineer": {
        "skills": ["python", "pytorch", "tensorflow", "transformers", "hugging face", "llms", "deep learning", "machine learning", "docker", "mlops", "vector databases", "langchain"],
        "keywords": ["model training", "fine-tuning", "inference", "neural networks", "embeddings"]
    },
    "AI Prompt Engineer": {
        "skills": ["prompt engineering", "few-shot learning", "rag", "chain-of-thought", "langchain", "llamaindex", "python", "gpt-4", "claude", "system prompts", "token optimization"],
        "keywords": ["evaluation", "hallucination mitigation", "context window", "agentic workflows"]
    },
    "Data Scientist": {
        "skills": ["python", "r", "sql", "pandas", "numpy", "scikit-learn", "data visualization", "tableau", "power bi", "statistics", "feature engineering", "predictive modeling"],
        "keywords": ["eda", "hypothesis testing", "regression", "clustering", "a/b testing"]
    },
    "Information Security Analyst": {
        "skills": ["siem", "soc", "penetration testing", "firewalls", "incident response", "vulnerability assessment", "wireshark", "iso 27001", "nist", "network security", "linux"],
        "keywords": ["threat analysis", "risk mitigation", "compliance", "cryptography", "zero trust"]
    },
    "Cloud DevOps Engineer": {
        "skills": ["aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ci/cd", "jenkins", "github actions", "linux", "bash", "ansible", "prometheus"],
        "keywords": ["infrastructure as code", "containerization", "monitoring", "scalability", "pipeline"]
    },
    "ESG Sustainability Manager": {
        "skills": ["esg reporting", "carbon accounting", "sustainability reporting", "ghg protocol", "gri standards", "csrd", "tcfd", "environmental compliance", "lca", "auditing"],
        "keywords": ["decarbonization", "scope 1 2 3", "governance", "circular economy", "net-zero"]
    },
    "Digital Marketing Manager": {
        "skills": ["seo", "sem", "google analytics", "google ads", "social media marketing", "meta ads", "email marketing", "content strategy", "hubspot", "copywriting", "cro"],
        "keywords": ["campaign management", "cac", "roas", "funnel optimization", "retention"]
    },
    "Financial Manager": {
        "skills": ["financial modeling", "forecasting", "budgeting", "financial analysis", "excel", "gaap", "ifrs", "variance analysis", "cash flow management", "sap", "erp"],
        "keywords": ["p&l", "balance sheet", "working capital", "risk assessment", "financial reporting"]
    },
    "Semiconductor Design Engineer": {
        "skills": ["verilog", "systemverilog", "vlsi", "asic design", "fpga", "rtl design", "synopsys", "cadence", "static timing analysis", "sta", "physical design", "tcl"],
        "keywords": ["synthesis", "logic synthesis", "wafer", "silicon", "tapeout", "verification"]
    },
    "UX/UI Designer": {
        "skills": ["figma", "wireframing", "prototyping", "user research", "usability testing", "design systems", "information architecture", "ui design", "ux design", "responsive design"],
        "keywords": ["user journeys", "heuristics", "mockups", "interaction design", "accessibility"]
    }
}

EXPECTED_SECTIONS = {
    "contact": ["email", "phone", "linkedin", "github", "contact"],
    "summary": ["summary", "objective", "profile", "about me"],
    "education": ["education", "academic", "university", "degree", "b.tech", "b.e", "bachelor"],
    "experience": ["experience", "employment", "work history", "internship", "professional experience"],
    "skills": ["skills", "technical skills", "competencies", "technologies"],
    "projects": ["projects", "academic projects", "key projects"],
    "certifications": ["certifications", "licenses", "certificates"]
}

def extract_text_from_pdf(uploaded_file):
    """Safely extracts selectable text from a PDF stream."""
    try:
        uploaded_file.seek(0)
        pdf_bytes = io.BytesIO(uploaded_file.read())
        reader = PdfReader(pdf_bytes)
        extracted_chunks = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                extracted_chunks.append(text)
        return "\n".join(extracted_chunks).strip()
    except Exception as exc:
        print(f"PDF extraction error: {exc}")
        return ""

def extract_text_from_docx(uploaded_file):
    """Safely extracts text from a DOCX stream."""
    try:
        uploaded_file.seek(0)
        doc = docx.Document(uploaded_file)
        full_text = [paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()]
        return "\n".join(full_text).strip()
    except Exception as exc:
        print(f"DOCX extraction error: {exc}")
        return ""

def extract_text(uploaded_file):
    """Router for uploaded file extraction."""
    filename = uploaded_file.name.lower()
    if filename.endswith(".pdf"):
        return extract_text_from_pdf(uploaded_file)
    if filename.endswith(".docx"):
        return extract_text_from_docx(uploaded_file)
    return ""

def analyze_resume(text, target_role=None, pasted_jd=None):
    """
    Performs section auditing, keyword gap analysis, and weighted ATS scoring.
    """
    lower_text = text.lower()
    sections_found = {}
    missing_sections = []
    for sec, kws in EXPECTED_SECTIONS.items():
        found = any(re.search(rf"\b{re.escape(k)}\b", lower_text) for k in kws)
        sections_found[sec] = found
        if not found:
            missing_sections.append(sec)
    section_score = int(((len(EXPECTED_SECTIONS) - len(missing_sections)) / len(EXPECTED_SECTIONS)) * 30)

    matched_skills = []
    missing_skills = []
    if target_role and target_role in JOB_TAXONOMY:
        expected_skills = JOB_TAXONOMY[target_role]["skills"]
        for skill in expected_skills:
            if re.search(rf"\b{re.escape(skill)}\b", lower_text):
                matched_skills.append(skill)
            else:
                missing_skills.append(skill)
        match_rate = len(matched_skills) / len(expected_skills) if expected_skills else 0
        role_score = int(match_rate * 40)
    else:
        role_score = 25

    verbs = ["developed", "led", "managed", "designed", "engineered", "built", "spearheaded", "optimized", "increased", "reduced"]
    verbs_count = sum(1 for v in verbs if re.search(rf"\b{re.escape(v)}\b", lower_text))
    impact_score = min(15, verbs_count * 3)

    words = len(text.split())
    if 350 <= words <= 900:
        length_score = 15
    elif 200 <= words < 350 or 900 < words <= 1200:
        length_score = 8
    else:
        length_score = 4

    total_score = min(100, section_score + role_score + impact_score + length_score)

    return {
        "total_score": total_score,
        "section_score": section_score,
        "role_score": role_score,
        "impact_score": impact_score,
        "length_score": length_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "missing_sections": missing_sections,
        "word_count": words
    }

def generate_suggestions(results, target_role):
    """Produces structured improvement recommendations."""
    tips = []
    if results["missing_sections"]:
        tips.append(f"**Add Key Sections:** Missing `{', '.join(results['missing_sections'])}`.")
    if results["missing_skills"]:
        sample_missing = ", ".join(results["missing_skills"][:5])
        tips.append(f"**Add High-Demand Keywords for {target_role}:** Consider integrating `{sample_missing}`.")
    if results["impact_score"] < 12:
        tips.append("**Add Quantifiable Impact:** Use more strong action verbs (e.g., *Spearheaded*, *Optimized*) and include measurable numerical results (%, $, counts).")
    if results["length_score"] < 15:
        tips.append(f"**Adjust Length:** Your resume contains {results['word_count']} words. The recommended ATS range is 400–800 words.")
    return tips