import streamlit as st

from analyzer import (
    JOB_TAXONOMY,
    analyze_resume,
    extract_text,
    generate_optimized_resume,
    generate_suggestions,
    refine_bullet_point,
)
from pdf_generator import generate_custom_pdf
from style import CUSTOM_CSS


st.set_page_config(page_title="Resumer | AI Resume Builder & Analyzer", layout="wide")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def render_badges(items, badge_class):
    if not items:
        st.caption("None detected yet.")
        return
    badges = "".join(f'<span class="badge {badge_class}">{item}</span>' for item in items)
    st.markdown(badges, unsafe_allow_html=True)


def render_analysis(text, target_role):
    results = analyze_resume(text, target_role=target_role)
    suggestions = generate_suggestions(results, target_role)

    metric_columns = st.columns(4)
    metric_columns[0].metric("ATS score", f"{results['total_score']} / 100")
    metric_columns[1].metric("Role fit", f"{results['role_score']} / 40")
    metric_columns[2].metric("Completeness", f"{results['section_score']} / 30")
    metric_columns[3].metric("Word count", results["word_count"])
    st.progress(results["total_score"] / 100)

    left, right = st.columns(2)
    with left:
        st.markdown('<div class="section-heading">Matched skills</div>', unsafe_allow_html=True)
        render_badges(results["matched_skills"], "badge-found")
    with right:
        st.markdown('<div class="section-heading">Missing target skills</div>', unsafe_allow_html=True)
        render_badges(results["missing_skills"], "badge-missing")

    if suggestions:
        st.markdown('<div class="section-heading">Tailored recommendations</div>', unsafe_allow_html=True)
        for suggestion in suggestions:
            st.markdown(f'<div class="suggestion-item">{suggestion}</div>', unsafe_allow_html=True)
    return results


def render_home():
    st.markdown(
        """
        <div class="hero-header">
            <div class="hero-header-inner">
                <div class="eyebrow">AI resume workspace</div>
                <h1>Make your next application easier to find.</h1>
                <p>Measure ATS alignment, sharpen your strongest evidence, and export a clean resume from one focused workspace.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="section-heading">A clear path from draft to shortlist</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="feature-grid">
            <div class="feature-item"><div class="icon-badge icon-badge-feature">01</div><h4>Diagnose</h4><p>See role-specific skills, missing sections, impact language, and a weighted ATS score.</p></div>
            <div class="feature-item"><div class="icon-badge icon-badge-feature">02</div><h4>Improve</h4><p>Rewrite the full resume or polish individual bullets while keeping the original beside it.</p></div>
            <div class="feature-item"><div class="icon-badge icon-badge-feature">03</div><h4>Export</h4><p>Build a compact PDF with the typography, accent color, and spacing that suit your style.</p></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.info("Choose Upload & Dual Analyzer in the sidebar to start with an existing resume, or open Resume Builder to create one from scratch.")


def render_analyzer():
    st.markdown('<div class="eyebrow">Resume intelligence</div>', unsafe_allow_html=True)
    st.title("Upload & Dual Analyzer")
    st.caption("Compare your source resume with an ATS-focused rewrite and keep both versions visible while you edit.")

    role_column, upload_column = st.columns([0.9, 1.1])
    with role_column:
        target_role = st.selectbox("Target job profile", list(JOB_TAXONOMY.keys()))
    with upload_column:
        uploaded_file = st.file_uploader("Upload PDF or DOCX", type=["pdf", "docx"])

    if not uploaded_file:
        st.markdown('<div class="empty-hint">Your analysis will appear here after you upload a resume.</div>', unsafe_allow_html=True)
        return

    with st.spinner("Reading your resume and checking ATS alignment..."):
        text = extract_text(uploaded_file)
    if not text:
        st.error("Could not extract readable text. The document may be scanned or empty.")
        return

    st.divider()
    results = render_analysis(text, target_role)

    st.divider()
    st.markdown('<div class="section-heading">Side-by-side optimizer</div>', unsafe_allow_html=True)
    st.caption("The rewrite uses your detected keyword gaps. Review every suggested claim before using it.")
    if st.button("Generate optimized version", type="primary"):
        with st.spinner("Drafting an ATS-focused version..."):
            optimized_text = generate_optimized_resume(text, target_role, results["missing_skills"])
        original_column, optimized_column = st.columns(2)
        with original_column:
            st.markdown("**Original resume**")
            st.text_area("Original resume text", text, height=520, label_visibility="collapsed")
        with optimized_column:
            st.markdown("**Optimized draft**")
            st.text_area("Optimized resume text", optimized_text, height=520, label_visibility="collapsed")

    st.divider()
    st.markdown('<div class="section-heading">Bullet polisher</div>', unsafe_allow_html=True)
    bullet = st.text_area("Paste one bullet point", placeholder="Worked on an internal dashboard", key="bullet_input")
    if st.button("Polish bullet", disabled=not bullet.strip()):
        st.success(refine_bullet_point(bullet, target_role))


def render_builder():
    st.markdown('<div class="eyebrow">Document studio</div>', unsafe_allow_html=True)
    st.title("Resume Builder")
    st.caption("Fill in the essentials, tune the visual system, and download an ATS-friendly PDF.")

    with st.form("resume_builder_form"):
        identity_column, contact_column = st.columns(2)
        with identity_column:
            name = st.text_input("Full name", placeholder="e.g. Mahak Sahu")
            email = st.text_input("Email", placeholder="name@example.com")
        with contact_column:
            phone = st.text_input("Phone number", placeholder="+91 9876543210")
            linkedin = st.text_input("LinkedIn profile", placeholder="linkedin.com/in/username")

        summary = st.text_area("Professional summary", placeholder="Brief 2-3 sentence career summary...")
        skills = st.text_area("Core skills", placeholder="Python, SQL, Git, PyTorch, Docker")
        experience = st.text_area("Work experience", placeholder="Job Title - Company (Year)\nBuilt...\nImproved...")
        projects = st.text_area("Key projects", placeholder="Project Name | Tech Stack\nDeveloped...")
        education = st.text_area("Education", placeholder="B.Tech in Artificial Intelligence & Machine Learning\nUniversity (2025 - Present)")
        certifications = st.text_area("Certifications", placeholder="AWS Certified Cloud Practitioner")

        st.markdown("**Customize your PDF**")
        style_column, color_column, spacing_column = st.columns(3)
        with style_column:
            font_choice = st.selectbox("Font", ["Helvetica", "Times", "Courier"])
            template = st.selectbox("Template", ["Classic Single Column"])
        with color_column:
            color_name = st.selectbox("Accent color", ["Blue", "Emerald", "Slate", "Rose"])
        with spacing_column:
            spacing = st.slider("Section spacing", 2.0, 8.0, 4.0, 0.5)

        submitted = st.form_submit_button("Generate resume PDF", type="primary")

    if submitted:
        color_map = {"Blue": "#2563EB", "Emerald": "#059669", "Slate": "#475569", "Rose": "#E11D48"}
        resume_data = {
            "name": name,
            "email": email,
            "phone": phone,
            "linkedin": linkedin,
            "summary": summary,
            "skills": skills,
            "experience": experience,
            "projects": projects,
            "education": education,
            "certifications": certifications,
        }
        pdf_file = generate_custom_pdf(
            resume_data,
            font_choice=font_choice,
            color_hex=color_map[color_name],
            template=template,
            spacing=spacing,
        )
        st.success("Resume generated successfully.")
        st.download_button(
            "Download resume PDF",
            data=pdf_file.getvalue(),
            file_name="ATS_Resume.pdf",
            mime="application/pdf",
        )


st.sidebar.title("Resumer Studio")
page = st.sidebar.radio("Navigation", ["Home / Overview", "Upload & Dual Analyzer", "Resume Builder"])

if page == "Home / Overview":
    render_home()
elif page == "Upload & Dual Analyzer":
    render_analyzer()
else:
    render_builder()
