from dotenv import load_dotenv

load_dotenv()

import streamlit as st

from analyzer import (
    JOB_TAXONOMY,
    analyze_resume,
    extract_text,
    generate_suggestions,
)
from resume_builder import resume_builder_page
from resume_comparison import resume_comparison_page


st.set_page_config(page_title="Resumer | AI Resume Builder & Analyzer", layout="wide")

st.markdown(
    """
    <style>
    @keyframes meshShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    :root {
        --ink: #0f172a;
        --muted: #64748b;
        --line: #dbe3ee;
        --accent: #4f46e5;
        --panel: rgba(255, 255, 255, 0.88);
    }
    .stApp {
        background: linear-gradient(120deg, #f8fafc, #eef2ff, #ecfeff, #f8fafc);
        background-size: 300% 300%;
        animation: meshShift 18s ease infinite;
    }
    .block-container { max-width: 1240px; padding-top: 3rem; }
    .section-heading { display: block; line-height: 1.5; padding-top: .25rem; overflow: visible; }
    .hero {
        padding: 2.5rem 2.8rem;
        border: 1px solid rgba(255,255,255,.8);
        border-radius: 18px;
        background: linear-gradient(135deg, rgba(15,23,42,.96), rgba(30,41,59,.92));
        color: #f8fafc;
        box-shadow: 0 18px 55px rgba(15,23,42,.16);
    }
    .hero h1 { margin: .35rem 0 .7rem; font-size: clamp(2rem, 5vw, 4.4rem); line-height: 1; }
    .eyebrow { color: #67e8f9; font-size: .75rem; font-weight: 800; letter-spacing: .16em; text-transform: uppercase; }
    .hero p { max-width: 720px; color: #cbd5e1; font-size: 1.05rem; }
    .preview-card { min-height: 330px; padding: 1.2rem; border: 1px solid var(--line); border-radius: 12px; background: var(--panel); box-shadow: 0 8px 24px rgba(15,23,42,.06); }
    .preview-card.is-selected { border: 2px solid var(--accent); padding: calc(1.2rem - 1px); box-shadow: 0 12px 28px rgba(79,70,229,.16); background: linear-gradient(145deg, rgba(238,242,255,.96), rgba(255,255,255,.92)); }
    .preview-card h4 { margin: .2rem 0 .35rem; color: var(--ink); }
    .preview-name { margin: 0; color: var(--muted); font-size: .88rem; font-weight: 700; }
    .preview-card p { color: var(--muted); font-size: .88rem; }
    .preview-card strong { color: var(--ink); }
    .preview-card .selected-label { color: var(--accent); font-size: .72rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }
    .wireframe { margin: .9rem 0 .75rem; padding: .72rem; border: 1px solid #d9e1eb; border-radius: 8px; background: #fff; }
    .wireframe-header { display: flex; gap: .55rem; align-items: center; padding-bottom: .6rem; border-bottom: 1px solid #e5eaf0; }
    .wireframe-avatar { width: 25px; height: 25px; border-radius: 50%; background: #cbd5e1; }
    .wireframe-person-name { color: #334155; font-size: .68rem; font-weight: 800; line-height: 1.2; }
    .wireframe-contact { width: 28%; height: 5px; margin-left: auto; border-radius: 3px; background: #cbd5e1; }
    .wireframe-section { margin-top: .55rem; }
    .wireframe-label { display: block; margin-bottom: .3rem; color: #64748b; font-size: .56rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }
    .wireframe-title { width: 29%; height: 3px; margin-bottom: .35rem; border-radius: 3px; background: var(--accent); }
    .wireframe-detail { margin: 0; color: #475569; font-size: .62rem; line-height: 1.35; overflow-wrap: anywhere; }
    .wireframe-line { height: 4px; margin-top: .25rem; border-radius: 3px; background: #dbe3ee; }
    .wireframe-line.short { width: 68%; }
    .wireframe-line.medium { width: 84%; }
    .wireframe-line.long { width: 96%; }
    .wireframe.compact .wireframe-header { padding: .35rem; background: #f1f5f9; border-bottom-color: #cbd5e1; }
    .wireframe.compact .wireframe-section { margin-top: .4rem; }
    .wireframe.ivy .wireframe-header { display: block; text-align: center; }
    .wireframe.ivy .wireframe-avatar { display: none; }
    .wireframe.ivy .wireframe-person-name { margin-bottom: .45rem; color: #334155; font-size: .72rem; }
    .wireframe.ivy .wireframe-contact { width: 38%; height: 4px; margin: 0 auto; }
    .wireframe.ivy .wireframe-title { width: 23%; height: 4px; }
    .capability { min-height: 175px; padding: 1rem; border-top: 3px solid var(--accent); background: rgba(255,255,255,.72); }
    .capability h4 { color: var(--ink); margin: .3rem 0; }
    .swatch { display: flex; align-items: center; gap: .65rem; margin-top: .5rem; color: var(--ink); font-family: monospace; }
    .swatch span { width: 30px; height: 30px; border-radius: 7px; border: 1px solid rgba(15,23,42,.18); background: var(--swatch); }
    .font-preview { padding: .75rem 1rem; border: 1px solid var(--line); border-radius: 8px; color: var(--ink); background: rgba(255,255,255,.78); }
    </style>
    """,
    unsafe_allow_html=True,
)


st.sidebar.title("Resumer Studio")
page = st.sidebar.radio("Navigation", ["Home / Overview", "Upload & Dual Analyzer", "Resume Builder", "Resume Comparison"])


if page == "Home / Overview":
    st.markdown(
        """
        <section class="hero">
            <div class="eyebrow">AI Career Workspace</div>
            <h1>AI Resume Builder and Analyzer</h1>
            <p>Bridge your credentials with modern Applicant Tracking Systems through rule-based taxonomy scanning, AI bullet enrichment, and customizable ATS-friendly PDF exports.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Output Showcase & Template Preview")
    showcase = [
        (
            "Classic Single Column", "Professional Layout", "Alex Morgan", "94/100", "single",
            {
                "Summary": "Senior AI Engineer with 4+ years designing high-throughput NLP systems and scalable backend architectures.",
                "Experience": "Senior AI Developer at TechCorp (2024-Present) - Built custom LLM pipelines, reducing inference latency by 40%.",
                "Projects": "Enterprise RAG Knowledge Base using Pinecone and FastAPI.",
                "Education": "B.Tech in Computer Science, State University (2020-2024).",
                "Skills": "Python, PyTorch, LangChain, Docker, AWS.",
            },
        ),
        (
            "Executive Compact", "Modern Layout", "Jordan Lee", "91/100", "compact",
            {
                "Summary": "Spearheaded cloud migration, reducing pipeline compute costs by 31% while managing cross-functional engineering teams.",
                "Experience": "Engineering Lead at CloudScale Inc (2022-Present) - Directed microservices deployment across AWS clusters.",
                "Projects": "Automated CI/CD Deployment Orchestrator.",
                "Education": "M.S. in Software Engineering, Tech Institute.",
                "Skills": "Kubernetes, Terraform, AWS S3, System Architecture, Go.",
            },
        ),
        (
            "Minimalist Ivy League", "Clean Layout", "Taylor Reed", "89/100", "ivy",
            {
                "Summary": "Focused on machine learning research, vector databases, and high-performance CUDA optimization for deep learning models.",
                "Experience": "ML Researcher at DataCore Labs (2023-Present) - Optimized transformer models for edge devices.",
                "Projects": "Distributed Graph Neural Network Analyzer.",
                "Education": "B.S. in Artificial Intelligence, University of Technology.",
                "Skills": "PyTorch, Transformers, Vector DBs, MLOps, C++.",
            },
        ),
    ]
    wireframe_sections = ("Summary", "Experience", "Projects", "Education", "Skills")

    def render_wireframe(variant, name, details):
        section_markup = "".join(
            f'<div class="wireframe-section"><span class="wireframe-label">{section}</span>'
            f'<div class="wireframe-title"></div><p class="wireframe-detail">{details[section]}</p></div>'
            for section in wireframe_sections
        )
        return (
            f'<div class="wireframe {variant}">'
            '<div class="wireframe-header"><div class="wireframe-avatar"></div>'
            f'<div class="wireframe-person-name">{name}</div><div class="wireframe-contact"></div></div>'
            f'{section_markup}</div>'
        )

    chosen_template = st.session_state.get("resume_template", "Professional Layout")
    columns = st.columns(3)
    for column, (template, template_value, name, score, variant, details) in zip(columns, showcase):
        with column:
            selected_label = "<div class='selected-label'>Currently chosen template</div>" if chosen_template == template_value else ""
            card_class = "preview-card is-selected" if chosen_template == template_value else "preview-card"
            st.markdown(
                f'<div class="{card_class}"><h4>{template}</h4>{selected_label}{render_wireframe(variant, name, details)}<p>ATS Score: <strong>{score}</strong></p></div>',
                unsafe_allow_html=True,
            )

    st.subheader("Platform Capabilities")
    capabilities = [
        ("Smart Builder Presets", "Select ATS-ready templates, typography palettes, and custom accent tones."),
        ("Real-Time AI Assistant", "Transform flat task statements into action-oriented metrics using the Google XYZ formula."),
        ("ATS Match & Scoring", "Audit resumes against ten career taxonomy tracks with detailed keyword fit."),
        ("Dual Comparison View", "Compare raw input against the ATS-reconstructed optimized document."),
    ]
    columns = st.columns(4)
    for column, (title, description) in zip(columns, capabilities):
        with column:
            st.markdown(f'<div class="capability"><h4>{title}</h4><p>{description}</p></div>', unsafe_allow_html=True)

    st.subheader("What You Will Get")
    results = st.columns(3)
    results[0].info("Higher callback probability: keywords tailored to current industry criteria.")
    results[1].info("Instant gap detection: omitted sections, weak impact phrases, and length issues.")
    results[2].info("Single-click ATS export: standardized PDFs without unparseable multi-column tables.")


elif page == "Upload & Dual Analyzer":
    st.header("Resume Analyzer")
    st.caption("Upload your resume to review ATS alignment, matched skills, missing skills, and recommendations.")
    role_column, upload_column = st.columns(2)
    with role_column:
        target_role = st.selectbox("Select Target Job Domain", list(JOB_TAXONOMY.keys()))
    with upload_column:
        uploaded_file = st.file_uploader("Upload Resume (.pdf or .docx)", type=["pdf", "docx"])
    job_description = st.text_area(
        "Job Description (optional)",
        placeholder="Paste the target role's job description to compare resume keywords and skills.",
        height=140,
    )

    if uploaded_file:
        raw_text = extract_text(uploaded_file)
        if not raw_text:
            st.error("Could not parse selectable text. Please ensure the document is not an image-only scan.")
        else:
            results = analyze_resume(raw_text, target_role, job_description)
            score_columns = st.columns(4)
            score_columns[0].metric("Overall ATS Score", f"{results['total_score']} / 100")
            score_columns[1].metric("Role Keyword Fit", f"{results['role_score']} / 40")
            score_columns[2].metric("Completeness", f"{results['section_score']} / 30")
            score_columns[3].metric("Word Count", results["word_count"])
            st.progress(results["total_score"] / 100)

            st.divider()
            matched, missing = st.columns(2)
            with matched:
                st.markdown("**Matched Role Competencies**")
                st.write(", ".join(f"`{skill}`" for skill in results["matched_skills"]) or "None")
            with missing:
                st.markdown("**Missing High-Value Role Keywords**")
                st.write(", ".join(f"`{skill}`" for skill in results["missing_skills"][:10]) or "All core skills detected!")

            with st.expander("Job Description Match", expanded=bool(job_description.strip())):
                jd_results = results["jd_analysis"]
                if jd_results["available"]:
                    jd_columns = st.columns(3)
                    jd_columns[0].metric("JD Keyword Match", f"{jd_results['score']}%")
                    jd_columns[1].metric("Matched Terms", len(jd_results["matched_terms"]))
                    jd_columns[2].metric("Missing Terms", len(jd_results["missing_terms"]))
                    jd_matched, jd_missing = st.columns(2)
                    with jd_matched:
                        st.markdown("**Matched JD Terms**")
                        st.write(", ".join(jd_results["matched_terms"]) or "No extracted terms matched yet.")
                    with jd_missing:
                        st.markdown("**JD Terms to Address**")
                        st.write(", ".join(jd_results["missing_terms"]) or "All extracted terms were found.")
                    st.caption("Keyword matching is a local text comparison; it does not assess context or seniority.")
                else:
                    st.info("Paste a job description above to see its matched and missing terms.")

            with st.expander("Skills & Keyword Analysis"):
                skill_columns = st.columns(2)
                with skill_columns[0]:
                    st.markdown("**Role Skills Found**")
                    st.write(", ".join(results["matched_skills"]) or "No role skills detected.")
                with skill_columns[1]:
                    st.markdown("**Role Skills Missing**")
                    st.write(", ".join(results["missing_skills"]) or "All taxonomy skills matched.")
                keyword_columns = st.columns(2)
                with keyword_columns[0]:
                    st.markdown("**Role Keywords Found**")
                    st.write(", ".join(results["matched_keywords"]) or "No role keywords detected.")
                with keyword_columns[1]:
                    st.markdown("**Role Keywords Missing**")
                    st.write(", ".join(results["missing_keywords"]) or "All taxonomy keywords matched.")

            with st.expander("Content Optimization Checks"):
                bullet_results = results["bullet_analysis"]
                bullet_columns = st.columns(3)
                bullet_columns[0].metric("Bullets Reviewed", bullet_results["bullet_count"])
                bullet_columns[1].metric("Action-Led", bullet_results["action_oriented_count"])
                bullet_columns[2].metric("With Metrics", bullet_results["quantified_count"])
                st.caption("Bullet checks look for standard bullet markers, action verbs, and measurable outcomes.")

                st.markdown("**Grammar Check**")
                st.caption("Local pattern-based checks for common issues; this is not a full grammar proofreader.")
                grammar_findings = results["grammar_analysis"]["findings"]
                if grammar_findings:
                    for finding in grammar_findings:
                        st.warning(finding)
                else:
                    st.success("No common grammar patterns were flagged.")

                st.markdown("**Formatting Check**")
                formatting = results["formatting_analysis"]
                format_columns = st.columns(2)
                format_columns[0].write(f"Email found: {'Yes' if formatting['email_found'] else 'No'}")
                format_columns[1].write(f"Phone found: {'Yes' if formatting['phone_found'] else 'No'}")
                for issue in formatting["issues"]:
                    st.warning(issue)
                if not formatting["issues"]:
                    st.success("No common text-formatting issues were flagged.")

            st.subheader("Recommendations")
            for recommendation in generate_suggestions(results, target_role):
                st.markdown(recommendation)

elif page == "Resume Comparison":
    resume_comparison_page()

else:
    resume_builder_page()


st.markdown(
    """
    <div style="text-align:center; padding:2rem 0 1rem; color:#64748b;">
        © 2026 Resumer Studio. All rights reserved. • Built for modern recruiting systems.<br>
        <strong>Made by Anupriya Soni and Mahak Sahu</strong>
    </div>
    """,
    unsafe_allow_html=True,
)