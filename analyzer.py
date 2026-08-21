import re
from PyPDF2 import PdfReader
import docx

SKILLS_DB = [
    "python", "java", "c++", "c", "c#", "javascript", "typescript", "html", "css", "sql", "r",
    "react", "angular", "vue", "node.js", "express", "django", "flask", "fastapi", "spring",
    "streamlit", "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy",
    "matplotlib", "seaborn", "opencv", "nlp", "machine learning", "deep learning",
    "data analysis", "data science", "data visualization", "power bi", "tableau",
    "excel", "mongodb", "mysql", "postgresql", "sqlite", "firebase", "aws", "azure", "gcp",
    "docker", "kubernetes", "git", "github", "gitlab", "ci/cd", "linux", "bash", "rest api",
    "graphql", "agile", "scrum", "project management", "communication", "teamwork",
    "leadership", "problem solving", "time management", "critical thinking"
]

SECTION_KEYWORDS = {
    "contact": ["email", "phone", "linkedin", "contact"],
    "summary": ["summary", "objective", "profile"],
    "education": ["education", "academic", "degree", "university", "college", "school"],
    "experience": ["experience", "work history", "employment", "internship"],
    "skills": ["skills", "technical skills", "competencies"],
    "projects": ["projects", "project"],
    "certifications": ["certification", "certificate", "certifications"],
}


def extract_text_from_pdf(file) -> str:
    text = ""
    try:
        reader = PdfReader(file)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    except Exception:
        text = ""
    return text


def extract_text_from_docx(file) -> str:
    text = ""
    try:
        document = docx.Document(file)
        for para in document.paragraphs:
            text += para.text + "\n"
        for table in document.tables:
            for row in table.rows:
                for cell in row.cells:
                    text += cell.text + " "
    except Exception:
        text = ""
    return text


def extract_text(uploaded_file) -> str:
    filename = uploaded_file.name.lower()
    if filename.endswith(".pdf"):
        return extract_text_from_pdf(uploaded_file)
    elif filename.endswith(".docx"):
        return extract_text_from_docx(uploaded_file)
    return ""


def detect_skills(text: str):
    text_lower = text.lower()
    found = []
    for skill in SKILLS_DB:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            found.append(skill)
    return sorted(set(found))


def detect_sections(text: str):
    text_lower = text.lower()
    found_sections, missing_sections = [], []
    for section, keywords in SECTION_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            found_sections.append(section)
        else:
            missing_sections.append(section)
    return found_sections, missing_sections


def calculate_ats_score(text: str, skills_found: list, sections_found: list, missing_sections: list) -> int:
    score = 0

    total_sections = len(sections_found) + len(missing_sections)
    section_score = (len(sections_found) / total_sections) * 40 if total_sections else 0
    score += section_score

    skill_score = min(len(skills_found), 15) / 15 * 30
    score += skill_score

    word_count = len(text.split())
    if 300 <= word_count <= 900:
        length_score = 15
    elif word_count < 300:
        length_score = max(0, (word_count / 300) * 15)
    else:
        length_score = max(0, 15 - ((word_count - 900) / 100))
    score += length_score

    action_verbs = ["managed", "developed", "led", "created", "built", "designed",
                     "implemented", "improved", "achieved", "analyzed", "organized"]
    verb_hits = sum(1 for v in action_verbs if v in text.lower())
    formatting_score = min(verb_hits, 10) / 10 * 15
    score += formatting_score

    return round(min(score, 100))


def generate_suggestions_rule_based(skills_found, missing_sections, word_count):
    suggestions = []
    if missing_sections:
        suggestions.append(f"Add missing sections: {', '.join(missing_sections)}.")
    if len(skills_found) < 5:
        suggestions.append("Add more relevant technical skills to strengthen keyword matching.")
    if word_count < 300:
        suggestions.append("Your resume looks too short. Add more detail about your experience and projects.")
    if word_count > 900:
        suggestions.append("Your resume is quite long. Try to make it more concise (ideally 1-2 pages).")
    suggestions.append("Use strong action verbs like 'developed', 'led', 'implemented' to describe achievements.")
    suggestions.append("Quantify achievements with numbers wherever possible (e.g., 'improved performance by 20%').")
    suggestions.append("Make sure contact info (email, phone, LinkedIn) is clearly visible at the top.")
    return suggestions


def get_ai_suggestions(text: str, skills_found, missing_sections, word_count, use_openai=False):
    if use_openai:
        try:
            from openai import OpenAI
            import os
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            prompt = (
                "You are a professional resume reviewer. Analyze this resume text and provide "
                "5 concise, actionable improvement suggestions as a bullet list. Be specific and practical.\n\n"
                f"Resume text:\n{text[:3000]}"
            )
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
            )
            content = response.choices[0].message.content
            suggestions = [line.strip("-• ").strip() for line in content.split("\n") if line.strip()]
            return suggestions
        except Exception as e:
            fallback = generate_suggestions_rule_based(skills_found, missing_sections, word_count)
            fallback.insert(0, f"(AI suggestions unavailable, showing rule-based tips. Reason: {e})")
            return fallback
    return generate_suggestions_rule_based(skills_found, missing_sections, word_count)


def analyze_resume(text: str, use_openai: bool = False) -> dict:
    skills_found = detect_skills(text)
    sections_found, missing_sections = detect_sections(text)
    word_count = len(text.split())
    ats_score = calculate_ats_score(text, skills_found, sections_found, missing_sections)
    suggestions = get_ai_suggestions(text, skills_found, missing_sections, word_count, use_openai=use_openai)

    return {
        "skills_found": skills_found,
        "sections_found": sections_found,
        "missing_sections": missing_sections,
        "word_count": word_count,
        "ats_score": ats_score,
        "suggestions": suggestions,
    }