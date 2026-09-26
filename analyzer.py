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


def _extract_job_keywords(job_description):
    stopwords = {
        "about", "after", "and", "are", "as", "at", "be", "been", "being", "but", "by",
        "can", "candidate", "for", "from", "have", "in", "into", "is", "it", "its", "job",
        "must", "of", "on", "or", "our", "per", "role", "should", "the", "their", "this",
        "to", "with", "will", "you", "your", "years", "work", "working", "experience",
        "responsibilities", "requirements", "required", "preferred", "including", "strong",
    }
    lower_jd = job_description.lower()
    candidates = []
    for role_data in JOB_TAXONOMY.values():
        for term in role_data["skills"] + role_data["keywords"]:
            if re.search(rf"(?<!\w){re.escape(term)}(?!\w)", lower_jd) and term not in candidates:
                candidates.append(term)

    tokens = re.findall(r"[a-z][a-z0-9+#.-]*", lower_jd)
    discovered = []
    for size in (3, 2, 1):
        for start in range(len(tokens) - size + 1):
            phrase_tokens = tokens[start:start + size]
            if any(token in stopwords for token in phrase_tokens):
                continue
            if size == 1 and len(phrase_tokens[0]) < 3 and phrase_tokens[0] not in {"r", "go", "c++", "c#"}:
                continue
            phrase = " ".join(phrase_tokens)
            if phrase not in candidates and phrase not in discovered:
                discovered.append(phrase)
    return (candidates + discovered)[:25]


def analyze_job_description(resume_text, job_description):
    """Compare resume text with rule-extracted terms from a pasted job description."""
    if not job_description or not job_description.strip():
        return {"available": False, "score": None, "matched_terms": [], "missing_terms": []}

    terms = _extract_job_keywords(job_description)
    lower_resume = resume_text.lower()
    matched_terms = [
        term for term in terms
        if re.search(rf"(?<!\w){re.escape(term)}(?!\w)", lower_resume)
    ]
    missing_terms = [term for term in terms if term not in matched_terms]
    score = int(len(matched_terms) / len(terms) * 100) if terms else 0
    return {
        "available": True,
        "score": score,
        "matched_terms": matched_terms,
        "missing_terms": missing_terms,
        "terms_analyzed": len(terms),
    }


def analyze_bullets(text):
    """Review resume bullets for action verbs, measurable results, and weak openers."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    bullet_pattern = re.compile(r"^(?:[-*•▪◦]\s+|\d+[.)]\s+)")
    bullet_lines = [bullet_pattern.sub("", line) for line in lines if bullet_pattern.match(line)]
    if not bullet_lines:
        bullet_lines = [
            line for line in lines
            if len(line.split()) >= 5 and re.search(r"\b(?:developed|led|managed|designed|engineered|built|optimized|increased|reduced)\b", line, re.I)
        ]

    action_verbs = (
        "developed", "led", "managed", "designed", "engineered", "built", "spearheaded",
        "optimized", "increased", "reduced", "launched", "automated", "implemented", "delivered",
    )
    action_count = sum(
        any(re.search(rf"\b{re.escape(verb)}\b", line, re.I) for verb in action_verbs)
        for line in bullet_lines
    )
    quantified_count = sum(bool(re.search(r"(?:\$\s?\d|\b\d+(?:\.\d+)?\s?%|\b\d{2,}\b)", line)) for line in bullet_lines)
    weak_count = sum(
        bool(re.match(r"(?:responsible for|helped|assisted with|worked on|participated in)\b", line, re.I))
        for line in bullet_lines
    )
    suggestions = []
    if not bullet_lines:
        suggestions.append("Format experience and project achievements as concise bullet points.")
    if bullet_lines and action_count < len(bullet_lines):
        suggestions.append("Start each achievement with a specific action verb.")
    if bullet_lines and quantified_count < len(bullet_lines):
        suggestions.append("Add measurable outcomes, such as time saved, volume, revenue, or percentages.")
    if weak_count:
        suggestions.append("Replace passive openers like 'Responsible for' or 'Helped' with direct ownership and impact.")
    return {
        "bullet_count": len(bullet_lines),
        "action_oriented_count": action_count,
        "quantified_count": quantified_count,
        "weak_opener_count": weak_count,
        "suggestions": suggestions,
    }


def check_grammar(text):
    """Flag common grammar patterns locally; this is not a full proofreader."""
    findings = []
    repeated_words = re.finditer(r"\b([A-Za-z]{2,})\s+\1\b", text, re.I)
    findings.extend(
        f"Repeated word '{match.group(1)}': remove the duplicate."
        for match in repeated_words
    )
    patterns = (
        (r"\bresponsible of\b", "Use 'responsible for' instead of 'responsible of'."),
        (r"\b(?:I|we|they|you)\s+(?:has|was)\b", "Check subject-verb agreement (for example, 'we were' or 'they have')."),
        (r"\b(?:he|she|it)\s+(?:have|are|were)\b", "Check subject-verb agreement (for example, 'he has' or 'it is')."),
        (r"\bmore better\b|\bmost best\b", "Avoid double comparatives such as 'more better'."),
    )
    for pattern, message in patterns:
        if re.search(pattern, text, re.I):
            findings.append(message)
    return {"findings": findings, "check_type": "Local pattern-based checks"}


def check_formatting(text, missing_sections=None):
    """Run text-based ATS formatting checks on the extracted resume."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    long_lines = [line for line in lines if len(line) > 120]
    bullet_markers = set(re.findall(r"(?m)^\s*([-*•▪◦])\s+", text))
    email_found = bool(re.search(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", text, re.I))
    phone_found = bool(re.search(r"(?<!\w)\+?\d[\d().\s-]{6,}\d(?!\w)", text))
    issues = []
    if not email_found:
        issues.append("Add a clearly labeled email address to the contact section.")
    if not phone_found:
        issues.append("Add a phone number using a standard, readable format.")
    if long_lines:
        issues.append(f"Break up {len(long_lines)} unusually long line(s) to improve readability and text extraction.")
    if len(bullet_markers) > 1:
        issues.append("Use one consistent bullet marker throughout the resume.")
    if missing_sections:
        issues.append(f"Add clearly labeled sections for: {', '.join(missing_sections)}.")
    return {
        "email_found": email_found,
        "phone_found": phone_found,
        "long_line_count": len(long_lines),
        "bullet_styles": sorted(bullet_markers),
        "issues": issues,
    }


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

    expected_keywords = JOB_TAXONOMY.get(target_role, {}).get("keywords", [])
    matched_keywords = [keyword for keyword in expected_keywords if re.search(rf"\b{re.escape(keyword)}\b", lower_text)]
    missing_keywords = [keyword for keyword in expected_keywords if keyword not in matched_keywords]

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
    jd_analysis = analyze_job_description(text, pasted_jd)
    bullet_analysis = analyze_bullets(text)
    grammar_analysis = check_grammar(text)
    formatting_analysis = check_formatting(text, missing_sections)

    return {
        "total_score": total_score,
        "section_score": section_score,
        "role_score": role_score,
        "impact_score": impact_score,
        "length_score": length_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
        "missing_sections": missing_sections,
        "word_count": words,
        "jd_analysis": jd_analysis,
        "bullet_analysis": bullet_analysis,
        "grammar_analysis": grammar_analysis,
        "formatting_analysis": formatting_analysis,
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
    jd_analysis = results.get("jd_analysis", {})
    if jd_analysis.get("available") and jd_analysis.get("missing_terms"):
        terms = ", ".join(jd_analysis["missing_terms"][:5])
        tips.append(f"**Improve JD Match:** Add relevant evidence for `{terms}` where it accurately reflects your experience.")
    tips.extend(f"**Bullet Analysis:** {suggestion}" for suggestion in results.get("bullet_analysis", {}).get("suggestions", []))
    tips.extend(f"**Grammar Check:** {finding}" for finding in results.get("grammar_analysis", {}).get("findings", []))
    tips.extend(f"**Formatting Check:** {issue}" for issue in results.get("formatting_analysis", {}).get("issues", []))
    return tips