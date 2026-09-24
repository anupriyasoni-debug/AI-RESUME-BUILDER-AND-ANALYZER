import streamlit as st

from analyzer import (
    JOB_TAXONOMY,
    analyze_resume,
    extract_text,
    generate_suggestions,
)
from pdf_generator import build_pdf


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
    .block-container { max-width: 1240px; padding-top: 2rem; }
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
    .preview-card { min-height: 190px; padding: 1.2rem; border: 1px solid var(--line); border-radius: 12px; background: var(--panel); box-shadow: 0 8px 24px rgba(15,23,42,.06); }
    .preview-card h4 { margin: .25rem 0 .8rem; color: var(--ink); }
    .preview-card p { color: var(--muted); font-size: .88rem; }
    .preview-card strong { color: var(--ink); }
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
page = st.sidebar.radio("Navigation", ["Home / Overview", "Upload & Dual Analyzer", "Resume Builder"])


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
        ("Classic Single Column", "ALEX MORGAN", "Senior AI Engineer with 4+ years designing high-throughput NLP systems...", "94/100"),
        ("Executive Compact", "JORDAN LEE", "Spearheaded cloud migration, reducing pipeline compute costs by 31%...", "91/100"),
        ("Minimalist Ivy League", "TAYLOR REED", "PyTorch, Python, Transformers, Vector DBs, Kubernetes, MLOps...", "89/100"),
    ]
    columns = st.columns(3)
    for column, (template, name, body, score) in zip(columns, showcase):
        with column:
            st.markdown(
                f'<div class="preview-card"><div class="eyebrow">{template}</div><h4>{name}</h4><p><strong>{body}</strong></p><p>ATS Score: <strong>{score}</strong></p></div>',
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

    if uploaded_file:
        raw_text = extract_text(uploaded_file)
        if not raw_text:
            st.error("Could not parse selectable text. Please ensure the document is not an image-only scan.")
        else:
            results = analyze_resume(raw_text, target_role)
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

            st.subheader("Recommendations")
            for recommendation in generate_suggestions(results, target_role):
                st.markdown(recommendation)


else:
    st.header("Professional Resume Builder")
    st.caption("Fill in the essentials and export a clean ATS-friendly PDF.")

    with st.form("builder_form"):
        identity, contact = st.columns(2)
        with identity:
            name = st.text_input("Full Name", "Mahak Sahu")
            email = st.text_input("Email", "mahak@example.com")
        with contact:
            phone = st.text_input("Phone Number", "+91 9876543210")
            linkedin = st.text_input("LinkedIn / Portfolio URL", "linkedin.com/in/mahaksahu")
        summary = st.text_area("Professional Summary", "Results-driven engineering student specializing in Artificial Intelligence and scalable backend services.")
        skills = st.text_area("Technical & Core Skills", "Python, PyTorch, C++, SQL, Machine Learning, Docker, Git")
        experience = st.text_area("Work Experience", "Software Intern - Tech Corp (2025)\nBuilt internal reporting dashboard using Python and SQL, cutting generation time by 30%.")
        projects = st.text_area("Key Projects", "AI Resume Analyzer & Builder\nArchitected a Streamlit prototype with NLP parsing and automated PDF generation.")
        education = st.text_area("Education", "B.Tech in Artificial Intelligence & Machine Learning\nMadhav Institute of Technology and Science (2025 - Present)")
        certifications = st.text_area("Certifications", "NPTEL Mobile VR & AI Certification\nInfosys Springboard Technical Certification")
        submit = st.form_submit_button("Generate Resume PDF", type="primary")

    if submit:
        resume_data = {"name": name, "email": email, "phone": phone, "linkedin": linkedin, "summary": summary, "skills": skills, "experience": experience, "projects": projects, "education": education, "certifications": certifications}
        pdf_buffer = build_pdf(resume_data)
        st.success("Resume PDF generated successfully!")
        st.download_button("Download Resume PDF", data=pdf_buffer.getvalue(), file_name=f"{name.replace(' ', '_')}_Resume.pdf", mime="application/pdf")


st.markdown(
    """
    <div style="text-align:center; padding:2rem 0 1rem; color:#64748b;">
        © 2026 Resumer Studio. All rights reserved. • Built for modern recruiting systems.<br>
        <strong>Made by Anupriya Soni and Mahak Sahu</strong>
    </div>
    """,
    unsafe_allow_html=True,
)