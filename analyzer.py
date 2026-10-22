import json
import os
import re
import docx
import io
from pypdf import PdfReader
from dotenv import load_dotenv
from local_model import local_engine

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
    """Safely extracts selectable text from a PDF stream using PyMuPDF with pypdf fallback."""
    try:
        uploaded_file.seek(0)
        file_bytes = uploaded_file.read()
        # 1. Try PyMuPDF (fitz) for fast and robust text extraction
        try:
            import pymupdf
            doc = pymupdf.open(stream=file_bytes, filetype="pdf")
            extracted_chunks = [page.get_text() for page in doc if page.get_text()]
            if extracted_chunks:
                return "\n".join(extracted_chunks).strip()
        except Exception:
            pass

        # 2. Fallback to pypdf.PdfReader
        pdf_bytes = io.BytesIO(file_bytes)
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


ADDITIONAL_TECH_TERMS = [
    # Core Data Science & AI/ML
    "machine learning", "deep learning", "artificial intelligence", "nlp",
    "natural language processing", "computer vision", "neural networks",
    "data science", "data analysis", "data analytics", "data modeling",
    "data pipelines", "data engineering", "etl", "big data", "data warehouse",
    "spark", "pyspark", "hadoop", "kafka", "flink", "hive", "dbt",
    "nosql", "mongodb", "postgresql", "mysql", "oracle", "sqlite", "redis",
    "snowflake", "bigquery", "redshift", "databricks",
    "scipy", "matplotlib", "seaborn", "plotly", "keras", "xgboost", "lightgbm", "catboost",
    "llm", "llms", "rag", "langchain", "llamaindex", "hugging face", "transformers",
    # Core Languages & Frameworks
    "python", "r", "c", "c++", "c#", "golang", "go", "rust", "scala",
    "javascript", "typescript", "react", "angular", "vue", "node.js", "nodejs",
    "django", "flask", "fastapi", "spring boot", "ruby", "php",
    # Cloud, DevOps & Tools
    "aws", "azure", "gcp", "google cloud", "cloud computing",
    "docker", "kubernetes", "k8s", "terraform", "ansible", "helm",
    "linux", "unix", "bash", "shell scripting", "powershell",
    "git", "github", "gitlab", "bitbucket", "jira", "confluence",
    "ci/cd", "continuous integration", "continuous deployment", "jenkins", "github actions",
    "rest api", "restful api", "graphql", "grpc", "microservices",
    "unit testing", "integration testing", "test automation", "pytest",
    # Agile / Methodologies / Analytics
    "agile", "scrum", "kanban", "sprint planning",
    "excel", "vba", "tableau", "power bi", "looker", "metabase",
    "statistics", "feature engineering", "predictive modeling", "a/b testing", "hypothesis testing",
]

TERM_CANONICAL_MAP = {
    # Kubernetes
    "k8s": "kubernetes",
    "k8": "kubernetes",
    # Scikit-learn
    "sklearn": "scikit-learn",
    # Go / Golang
    "golang": "go",
    # JavaScript & TypeScript
    "js": "javascript",
    "ts": "typescript",
    # Python
    "py": "python",
    # Databases
    "postgres": "postgresql",
    "mongo": "mongodb",
    # Web Frameworks
    "reactjs": "react",
    "react.js": "react",
    "vuejs": "vue",
    "vue.js": "vue",
    "angularjs": "angular",
    "angular.js": "angular",
    "nodejs": "node.js",
    "node": "node.js",
    # AI / ML
    "tf": "tensorflow",
    "torch": "pytorch",
    "huggingface": "hugging face",
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "dl": "deep learning",
    "nlp": "natural language processing",
    "llm": "llms",
    "large language model": "llms",
    "large language models": "llms",
    "retrieval augmented generation": "rag",
    "retrieval-augmented generation": "rag",
    # Cloud & DevOps
    "amazon web services": "aws",
    "google cloud": "gcp",
    "google cloud platform": "gcp",
    "microsoft azure": "azure",
    "continuous integration": "ci/cd",
    "continuous deployment": "ci/cd",
    "ci / cd": "ci/cd",
    # APIs & Other
    "restful api": "rest api",
    "restful apis": "rest api",
    "rest apis": "rest api",
    "powerbi": "power bi",
    "power-bi": "power bi",
    "eda": "exploratory data analysis",
}

KNOWN_TECH_ACRONYMS = {
    "api", "sql", "aws", "gcp", "etl", "nlp", "rag", "sdk", "cli",
    "siem", "soc", "erp", "sap", "crm", "kpi", "roi", "ci/cd",
}


def canonicalize_skill(skill: str) -> str:
    """
    Returns the normalized canonical name for a given skill or alias.
    e.g. 'k8s' -> 'kubernetes', 'sklearn' -> 'scikit-learn', 'golang' -> 'go'
    """
    if not skill:
        return ""
    clean = skill.strip().lower()
    return TERM_CANONICAL_MAP.get(clean, clean)


def _build_boundary_pattern(term: str) -> str:
    """
    Constructs a boundary-safe regular expression pattern for a technical term or skill.
    Ensures that short or ambiguous terms such as 'r', 'go', and 'c' are not matched
    inside unrelated words or false-positive contexts (e.g. 'c++' matching 'c', 'r&d'
    matching 'r', or 'go to' / 'django' matching 'go').
    """
    clean_term = term.strip().lower()
    escaped = re.escape(clean_term)
    prefix = r"(?<![a-zA-Z0-9])"
    suffix = r"(?![a-zA-Z0-9])"

    if clean_term == "c":
        # Disallow C++, C#, C-level, C-suite, and c/o (care of)
        suffix = r"(?![+#a-zA-Z0-9])(?!(?:-level|-suite|/o\b))"
    elif clean_term == "r":
        # Disallow R&D, R & D, and r-squared
        suffix = r"(?![a-zA-Z0-9])(?!(?:\s*&\s*d\b|-squared\b))"
    elif clean_term == "go":
        # Disallow English colloquialisms: go-to, go to, go live, go-live, go market, go through
        suffix = r"(?![a-zA-Z0-9])(?!(?:-to\b| to\b| live\b|-live\b| market\b| through\b))"
    elif clean_term.endswith("+"):
        suffix = r"(?![+a-zA-Z0-9])"
    elif clean_term.endswith("#"):
        suffix = r"(?![#a-zA-Z0-9])"

    return f"{prefix}{escaped}{suffix}"


def _build_alias_lookup():
    """
    Builds a bidirectional map of canonical skills to all equivalent forms/aliases.
    e.g. 'kubernetes' -> {'kubernetes', 'k8s', 'k8'}
         'scikit-learn' -> {'scikit-learn', 'sklearn'}
         'aws' -> {'aws', 'amazon web services'}
         'go' -> {'go', 'golang'}
    """
    lookup = {}
    for alias, canonical in TERM_CANONICAL_MAP.items():
        canonical_clean = canonical.strip().lower()
        alias_clean = alias.strip().lower()
        lookup.setdefault(canonical_clean, set()).add(canonical_clean)
        lookup[canonical_clean].add(alias_clean)
        lookup.setdefault(alias_clean, set()).add(canonical_clean)
        lookup[alias_clean].add(alias_clean)
    return lookup


SKILL_ALIASES = _build_alias_lookup()


def _skill_in_text(skill: str, text: str) -> bool:
    """
    Checks if a skill or any of its canonical aliases is present in text
    using boundary-safe matching.
    """
    if not skill or not text:
        return False
    lower_text = text.lower()
    canonical = canonicalize_skill(skill)
    variants = SKILL_ALIASES.get(canonical, {canonical, skill.strip().lower()})
    for variant in variants:
        pattern = _build_boundary_pattern(variant)
        if re.search(pattern, lower_text):
            return True
    return False


def _extract_job_keywords(job_description):
    """
    Extracts distinct technical skills and keywords from a job description
    using curated role taxonomy and conservative term matching.
    Returns each canonical skill only once, even if multiple aliases occur.
    Does NOT construct arbitrary, noisy multiword n-grams.
    """
    if not job_description or not job_description.strip():
        return []

    lower_jd = job_description.lower()

    # 1. Build prioritized search vocabulary from taxonomy and tech terms
    curated_vocab = set()
    for role_data in JOB_TAXONOMY.values():
        for term in role_data["skills"] + role_data["keywords"]:
            curated_vocab.add(term.strip().lower())
    for term in ADDITIONAL_TECH_TERMS:
        curated_vocab.add(term.strip().lower())
    for alias in TERM_CANONICAL_MAP:
        curated_vocab.add(alias.strip().lower())

    # Sort multiword phrases first so more specific terms are matched
    sorted_terms = sorted(curated_vocab, key=lambda t: (-len(t.split()), -len(t)))

    extracted = []
    seen_canonical = set()

    for term in sorted_terms:
        pattern = _build_boundary_pattern(term)
        if re.search(pattern, lower_jd):
            canonical = canonicalize_skill(term)
            if canonical not in seen_canonical:
                seen_canonical.add(canonical)
                extracted.append(canonical)

    # 2. Check for capitalized technical acronyms (e.g. 'API', 'ETL', 'SQL')
    acronyms = re.findall(r"\b[A-Z]{2,6}\b", job_description)
    for ac in acronyms:
        ac_lower = ac.lower()
        if ac_lower in KNOWN_TECH_ACRONYMS:
            canonical = canonicalize_skill(ac_lower)
            if canonical not in seen_canonical:
                seen_canonical.add(canonical)
                extracted.append(canonical)

    return extracted[:25]


def analyze_job_description(resume_text, job_description):
    """Compare resume text with rule-extracted terms from a pasted job description."""
    if not job_description or not job_description.strip():
        return {
            "available": False,
            "score": None,
            "matched_terms": [],
            "missing_terms": [],
            "terms_analyzed": 0,
            "terms_analyzed_list": [],
            "notice": "No job description was provided.",
        }

    terms = _extract_job_keywords(job_description)
    matched_terms = [
        term for term in terms
        if _skill_in_text(term, resume_text)
    ]
    missing_terms = [term for term in terms if term not in matched_terms]

    if len(terms) < 3:
        return {
            "available": True,
            "score": None,
            "matched_terms": matched_terms,
            "missing_terms": missing_terms,
            "terms_analyzed": len(terms),
            "terms_analyzed_list": terms,
            "notice": (
                "Fewer than 3 distinct technical skills or requirements were identified in the job description. "
                "Paste a more detailed job description containing specific technical qualifications for an accurate match percentage."
            ),
        }

    score = int(round((len(matched_terms) / len(terms)) * 100))
    return {
        "available": True,
        "score": score,
        "matched_terms": matched_terms,
        "missing_terms": missing_terms,
        "terms_analyzed": len(terms),
        "terms_analyzed_list": terms,
        "notice": None,
    }


def analyze_job_description_local(resume_text, job_description, target_role=""):
    """Score resume evidence against a job description using local TF-IDF and NLP analysis."""
    return local_engine.analyze_job_fit(resume_text, job_description, target_role=target_role)


# Backward compatibility alias
analyze_job_description_with_gemini = analyze_job_description_local


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
        suggestions.append("Bullet formatting check: Format experience and project achievements as concise bullet points.")
    if bullet_lines and action_count == 0:
        suggestions.append("Action verb check: No strong action verbs were detected starting your bullet points. If applicable, begin achievements with active verbs (e.g., 'Developed', 'Managed').")
    if bullet_lines and quantified_count == 0:
        suggestions.append("Measurable outcomes check: No quantitative metrics were detected in your bullet points. If your projects yielded measurable results (%, $, counts), consider adding them.")
    if weak_count:
        suggestions.append("Weak opener check: Detected passive phrasing like 'Responsible for' or 'Helped'. Replacing these with direct action verbs clarifies ownership.")
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
    # Only flag adjacent duplicates on the same line separated by horizontal whitespace (e.g. 'the the').
    # Do NOT flag words that naturally reoccur across different lines, bullets, or paragraphs.
    repeated_words = re.finditer(r"\b([A-Za-z]{2,})[ \t]+\1\b", text, re.I)
    seen_duplicates = set()
    for match in repeated_words:
        word_lower = match.group(1).lower()
        if word_lower not in seen_duplicates:
            seen_duplicates.add(word_lower)
            findings.append(f"Adjacent duplicate word '{match.group(1)}': check for accidental duplication.")

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
        issues.append("Contact details check: No email address was detected during text extraction. If already present in a header/footer or graphic, ensure it appears in selectable body text.")
    if not phone_found:
        issues.append("Contact details check: No phone number was detected during text extraction. If present, verify readable standard numeric formatting.")
    if long_lines:
        issues.append(f"Line length check: Detected {len(long_lines)} unusually long line(s) (>120 chars); breaking them into standard lines helps text extraction.")
    if len(bullet_markers) > 1:
        issues.append("Bullet consistency check: Multiple bullet styles detected. Using one consistent marker improves parsing reliability.")
    if missing_sections:
        issues.append(f"Section heading check: Standard headings for {', '.join(missing_sections)} were not detected during text extraction. If already present, standardizing heading titles ensures ATS parsers recognize them.")
    return {
        "email_found": email_found,
        "phone_found": phone_found,
        "long_line_count": len(long_lines),
        "bullet_styles": sorted(bullet_markers),
        "issues": issues,
    }


def analyze_resume(text, target_role=None, pasted_jd=None, target_source_name=None):
    """
    Performs section auditing, keyword gap analysis, and weighted ATS scoring.
    Prioritizes a pasted job description's recognized skills for the 40-point
    role-fit component when available (with >= 3 recognized skills).
    Otherwise falls back to the selected target_role preset.
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

    # 1. Determine target skills for the 40-point role fit
    jd_skills = _extract_job_keywords(pasted_jd) if pasted_jd and pasted_jd.strip() else []
    using_jd_target = False
    jd_fallback_notice = None

    if pasted_jd and pasted_jd.strip():
        if len(jd_skills) >= 3:
            using_jd_target = True
            target_skills = jd_skills
            role_fit_source = target_source_name or "Job Description"
            role_fit_target_name = target_source_name or f"Job Description ({len(jd_skills)} recognized skills)"
        else:
            using_jd_target = False
            jd_fallback_notice = (
                "JD-based role fit is unavailable because fewer than 3 recognized skills were found "
                "in the job description. The 40-point role fit score has fallen back to the selected preset taxonomy."
            )
            role_fit_source = f"Preset: {target_role} (Fallback: JD contained fewer than 3 recognized skills)"
            target_skills = JOB_TAXONOMY.get(target_role, {}).get("skills", [])
            role_fit_target_name = f"Preset: {target_role}" if target_role else "Preset"
    else:
        role_fit_source = f"Preset: {target_role}" if target_role else "Default Taxonomy"
        target_skills = JOB_TAXONOMY.get(target_role, {}).get("skills", [])
        role_fit_target_name = f"Preset: {target_role}" if target_role else "Default"

    # Normalize target skills to unique canonical forms
    canonical_target_skills = []
    seen_targets = set()
    for s in target_skills:
        c = canonicalize_skill(s)
        if c not in seen_targets:
            seen_targets.add(c)
            canonical_target_skills.append(c)

    matched_skills = []
    missing_skills = []
    if canonical_target_skills:
        for skill in canonical_target_skills:
            if _skill_in_text(skill, lower_text):
                matched_skills.append(skill)
            else:
                missing_skills.append(skill)
        match_rate = len(matched_skills) / len(canonical_target_skills)
        role_score = int(round(match_rate * 40))
    else:
        role_score = 25

    # Role keywords for preset (if preset is in use)
    expected_keywords = JOB_TAXONOMY.get(target_role, {}).get("keywords", []) if not using_jd_target else []
    matched_keywords = [keyword for keyword in expected_keywords if _skill_in_text(keyword, lower_text)]
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

    score_breakdown = {
        "role_score": role_score,
        "role_max": 40,
        "section_score": section_score,
        "section_max": 30,
        "impact_score": impact_score,
        "impact_max": 15,
        "length_score": length_score,
        "length_max": 15,
        "total_score": total_score,
        "word_count": words,
        "role_fit_source": role_fit_source,
        "evaluation_type": "Deterministic Keyword/Text Alignment (Heuristic)",
        "disclaimer": "Scores represent local heuristic keyword/text alignment, not a guaranteed ATS score or semantic understanding.",
        "formula": f"{role_score}/40 (Role Fit) + {section_score}/30 (Sections) + {impact_score}/15 (Impact) + {length_score}/15 (Length) = {total_score}/100",
    }

    return {
        "total_score": total_score,
        "section_score": section_score,
        "role_score": role_score,
        "impact_score": impact_score,
        "length_score": length_score,
        "score_breakdown": score_breakdown,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "analyzed_skills": canonical_target_skills,
        "role_fit_source": role_fit_source,
        "role_fit_target_name": role_fit_target_name,
        "using_jd_target": using_jd_target,
        "jd_fallback_notice": jd_fallback_notice,
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
    """Produces structured, evidence-based improvement recommendations."""
    tips = []
    if results.get("missing_sections"):
        missing_sec_str = ", ".join(results["missing_sections"])
        tips.append(
            f"**Section Heading Check:** Standard headings for `{missing_sec_str}` were not detected during text extraction. "
            f"If these sections already exist under custom titles or multi-column layouts, standardizing their headings ensures parser recognition."
        )
    if results.get("missing_skills"):
        sample_missing = ", ".join(results["missing_skills"][:5])
        source_label = results.get("role_fit_source", target_role)
        tips.append(
            f"**Skill Gap Analysis ({source_label}):** If you have hands-on experience with `{sample_missing}`, consider highlighting it. "
            f"(Only include skills you actually possess; do not claim unfamiliar tools.)"
        )
    if results.get("impact_score", 0) < 12 and results.get("bullet_analysis", {}).get("quantified_count", 0) == 0:
        tips.append(
            "**Quantifiable Outcomes Check:** No numerical metrics were detected in your bullet points. "
            "If your projects produced measurable results (percentages, dollar amounts, volume, scale), consider including them."
        )
    if results.get("length_score", 0) < 15:
        tips.append(
            f"**Length Check:** Your resume contains {results['word_count']} words. The recommended ATS range is 400–800 words."
        )
    jd_analysis = results.get("jd_analysis", {})
    if jd_analysis.get("available") and jd_analysis.get("missing_terms") and not results.get("using_jd_target"):
        terms = ", ".join(jd_analysis["missing_terms"][:5])
        tips.append(
            f"**Job Description Keyword Review:** If your background includes authentic experience with `{terms}`, "
            f"consider highlighting it in your bullets where it accurately reflects your work. (Do not add requirements you do not have.)"
        )
    tips.extend(f"**Bullet Analysis:** {suggestion}" for suggestion in results.get("bullet_analysis", {}).get("suggestions", []))
    tips.extend(f"**Grammar Check:** {finding}" for finding in results.get("grammar_analysis", {}).get("findings", []))
    tips.extend(f"**Formatting Check:** {issue}" for issue in results.get("formatting_analysis", {}).get("issues", []))
    return tips