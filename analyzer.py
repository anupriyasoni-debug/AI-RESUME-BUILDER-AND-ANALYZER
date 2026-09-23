import os
import re
import io
import docx
from pypdf import PdfReader
from dotenv import load_dotenv

load_dotenv()

# Taxonomy for the 10 Trending Jobs
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
    except Exception as e:
        print(f"PDF extraction error: {e}")
        return ""


def extract_text_from_docx(uploaded_file):
    """Safely extracts text from a DOCX stream."""
    try:
        uploaded_file.seek(0)
        doc = docx.Document(uploaded_file)
        full_text = [paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()]
        return "\n".join(full_text).strip()
    except Exception as e:
        print(f"DOCX extraction error: {e}")
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
    Performs full extraction, section auditing, keyword gap analysis,
    and returns a weighted ATS score (0-100).
    """
    lower_text = text.lower()
    
    # 1. Section Completeness (30%)
    sections_found = {}
    missing_sections = []
    for sec, kws in EXPECTED_SECTIONS.items():
        found = any(re.search(rf"\b{re.escape(k)}\b", lower_text) for k in kws)
        sections_found[sec] = found
        if not found:
            missing_sections.append(sec)
    section_score = int(((len(EXPECTED_SECTIONS) - len(missing_sections)) / len(EXPECTED_SECTIONS)) * 30)

    # 2. Target Role & Keyword Alignment (40%)
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
        # Fallback generic score if no role picked
        role_score = 25

    # 3. Action Verbs & Quantified Metrics (15%)
    action_verbs = ["developed", "led", "managed", "designed", "engineered", "built", "spearheaded", "optimized", "increased", "reduced"]
    verbs_count = sum(1 for v in action_verbs if re.search(rf"\b{re.escape(v)}\b", lower_text))
    impact_score = min(15, verbs_count * 3)

    # 4. Resume Length & Density (15%)
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


def generate_optimized_resume(raw_text, target_role, missing_skills):
    """Generate an ATS-focused resume rewrite using OpenAI when configured."""
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
            prompt = f"""
You are an expert resume writer and ATS optimizer.
Rewrite and clean up the following resume for the target role: '{target_role}'.

Key objectives:
1. Integrate missing industry keywords organically: {', '.join(missing_skills[:8])}.
2. Polish bullet points using the Google XYZ formula (accomplished X, measured by Y, by doing Z).
3. Fix grammar and passive voice issues without inventing experience or metrics.
4. Keep standard section headings: Professional Summary, Core Skills, Experience, Projects, Education, Certifications.

Original Resume:
{raw_text[:3500]}
"""
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            return response.choices[0].message.content
        except Exception:
            pass

    # Keep the offline path usable when no API key is configured.
    cleaned_lines = []
    for line in raw_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        rewritten = re.sub(
            r"^(worked on|helped with|responsible for)",
            "Spearheaded and delivered",
            stripped,
            flags=re.IGNORECASE,
        )
        cleaned_lines.append(rewritten)

    suggested_skills = ", ".join(skill.title() for skill in missing_skills[:6])
    optimized_lines = [
        f"### PROFESSIONAL SUMMARY\nResults-driven {target_role} professional with proven competence across scalable systems, quantifiable problem-solving, and cross-functional execution.",
        f"### RECOMMENDED CORE SKILLS (ATS TARGETED)\n• Integrated Competencies: {suggested_skills}",
        "### OPTIMIZED CONTENT & EXPERIENCE",
    ]
    optimized_lines.extend(
        f"• {line}" if not line.startswith("•") and len(line) > 40 else line
        for line in cleaned_lines[:25]
    )
    return "\n".join(optimized_lines)


def refine_bullet_point(bullet_text, role="General"):
    """Rewrite one resume bullet with an optional OpenAI-powered polisher."""
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": (
                        "Rewrite this resume bullet into a high-impact, ATS-friendly action "
                        f"sentence with strong verbs and truthful metrics for a {role} role: "
                        f"'{bullet_text}'. Return ONLY the refined bullet point."
                    ),
                }],
                temperature=0.3,
                max_tokens=60,
            )
            return response.choices[0].message.content.strip()
        except Exception:
            pass

    return (
        f"Spearheaded {bullet_text.lstrip('• ')}, increasing operational efficiency "
        "by 22% through automated workflows."
    )