import os
import streamlit as st
import plotly.graph_objects as go
from dotenv import load_dotenv

from analyzer import extract_text, analyze_resume
from resume_builder import resume_builder_page
from pdf_generator import generate_resume_pdf
from style import CUSTOM_CSS
from icons import icon, icon_badge

load_dotenv()

st.set_page_config(page_title="AI Resume Analyzer & Builder", page_icon="📄", layout="wide")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def render_badges(items, css_class, empty_text="None detected"):
    if not items:
        return f"<p class='empty-hint'>{empty_text}</p>"
    spans = "".join(f"<span class='badge {css_class}'>{item}</span>" for item in items)
    return f"<div>{spans}</div>"


def section_heading(icon_name, text, bg="#eef2ff", color="#4f46e5"):
    return f"{icon_badge(icon_name, size=16, badge_size=32, bg=bg, color=color, extra_class='icon-badge-section')}{text}"


def render_card(heading_html, body_html):
    st.markdown(
        f"<div class='custom-card'><div class='section-heading'>{heading_html}</div>{body_html}</div>",
        unsafe_allow_html=True
    )


def score_color(score):
    if score >= 75:
        return "#10b981"
    if score >= 50:
        return "#f59e0b"
    return "#ef4444"


def score_gauge(score):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={"suffix": "/100", "font": {"size": 38}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#9ca3af"},
            "bar": {"color": score_color(score), "thickness": 0.28},
            "bgcolor": "white",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 50], "color": "#fee2e2"},
                {"range": [50, 75], "color": "#fef3c7"},
                {"range": [75, 100], "color": "#d1fae5"},
            ],
        },
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=25, b=10),
                       paper_bgcolor="rgba(0,0,0,0)", font={"family": "Inter, sans-serif"})
    st.plotly_chart(fig, use_container_width=True)


def hero(icon_name, title, subtitle):
    st.markdown(
        f"""<div class='hero-header'><div class='hero-header-inner'>
        <div class='hero-title-row'>{icon_badge(icon_name, size=24, badge_size=46, bg="rgba(255,255,255,0.2)", color="white", extra_class="icon-badge-hero")}
        <h1>{title}</h1></div>
        <p>{subtitle}</p></div></div>""",
        unsafe_allow_html=True
    )


def feature_grid():
    features = [
        ("target", "Keyword Alignment", "Matches your skills and terms against common ATS keyword checks."),
        ("phone", "Contact Info", "Confirms your email, phone, and LinkedIn are easy to find."),
        ("edit", "Formatting", "Reviews structure, section completeness, and action-verb usage."),
    ]
    items_html = "".join(
        f"""<div class='feature-item'>
            {icon_badge(name, size=20, badge_size=44, bg="#f5f3ff", color="#7c3aed", extra_class="icon-badge-feature")}
            <h4>{title}</h4><p>{desc}</p>
        </div>"""
        for name, title, desc in features
    )
    st.markdown(f"<div class='feature-grid'>{items_html}</div>", unsafe_allow_html=True)


def main():
    st.sidebar.markdown(
        f"<div class='sidebar-brand-row'>{icon_badge('file-text', size=18, badge_size=32, bg='rgba(255,255,255,0.1)', color='#c4b5fd', extra_class='icon-badge-sidebar')}"
        f"<span class='brand-text'>AI Resume Toolkit</span></div>",
        unsafe_allow_html=True
    )
    st.sidebar.caption("Analyze. Improve. Build. Land the interview.")
    page = st.sidebar.radio("Navigate", ["🔍 Resume Analyzer", "🛠️ Resume Builder"], label_visibility="collapsed")

    st.sidebar.divider()
    openai_key = os.getenv("OPENAI_API_KEY")
    use_openai = st.sidebar.checkbox(
        "✨ Use AI-powered suggestions",
        value=bool(openai_key),
        disabled=not bool(openai_key),
        help="Requires OPENAI_API_KEY set in your .env file."
    )
    if not openai_key:
        st.sidebar.info("No OpenAI key found — using smart rule-based suggestions.\nAdd `OPENAI_API_KEY` to `.env` to unlock AI mode.")

    if page == "🔍 Resume Analyzer":
        analyzer_page(use_openai)
    else:
        builder_page()


def analyzer_page(use_openai):
    hero("search", "AI Resume Analyzer", "Upload your resume and get an instant ATS score with tailored improvement tips.")

    st.markdown(
        f"<div class='upload-card-label'>{icon_badge('upload', size=16, badge_size=30, bg='#eef2ff', color='#4f46e5', extra_class='icon-badge-section')}Upload your resume</div>",
        unsafe_allow_html=True
    )
    uploaded_file = st.file_uploader("Upload your resume", type=["pdf", "docx"], label_visibility="collapsed")

    if uploaded_file is None:
        feature_grid()
        return

    with st.spinner("Reading your resume..."):
        text = extract_text(uploaded_file)

    if not text.strip():
        st.error("Couldn't extract text from this file. Try another file or a text-based (not scanned) resume.")
        return

    with st.spinner("Analyzing..."):
        result = analyze_resume(text, use_openai=use_openai)

    score = result["ats_score"]

    col_gauge, col_stats = st.columns([1, 1.4])
    with col_gauge:
        with st.container(border=True):
            st.markdown(f"<div class='section-heading'>{section_heading('bar-chart', 'Your ATS Score')}</div>", unsafe_allow_html=True)
            score_gauge(score)

    with col_stats:
        c1, c2 = st.columns(2)
        c1.metric("📄 Word Count", result["word_count"])
        c2.metric("🧩 Sections Found", f'{len(result["sections_found"])}/{len(result["sections_found"]) + len(result["missing_sections"])}')
        c3, c4 = st.columns(2)
        c3.metric("⚡ Skills Detected", len(result["skills_found"]))
        rating = "Excellent" if score >= 75 else "Needs Work" if score >= 50 else "Low"
        c4.metric("🏆 Rating", rating)

    col1, col2 = st.columns(2)
    with col1:
        render_card(section_heading("check-circle", "Detected Skills", "#ecfdf5", "#059669"),
                    render_badges(result["skills_found"], "badge-skill", "No standard skills detected."))
        render_card(section_heading("layers", "Sections Found", "#eef2ff", "#4f46e5"),
                    render_badges(result["sections_found"], "badge-found"))
    with col2:
        render_card(section_heading("alert-triangle", "Missing Sections", "#fef2f2", "#dc2626"),
                    render_badges(result["missing_sections"], "badge-missing", "All key sections present! 🎉"))

    suggestions_html = "".join(
        f"<div class='suggestion-item'>{icon_badge('lightbulb', size=14, badge_size=24, bg='#fef3c7', color='#b45309')}{s}</div>"
        for s in result["suggestions"]
    )
    render_card(section_heading("sparkles", "Improvement Suggestions", "#fdf4ff", "#a21caf"), suggestions_html)

    with st.expander("View Extracted Text"):
        st.text_area("Extracted Resume Text", text, height=280, label_visibility="collapsed")


def builder_page():
    hero("tool", "Resume Builder", "Fill in your details and generate a clean, ATS-friendly resume PDF in minutes.")

    data = resume_builder_page()

    st.divider()
    col_a, col_b = st.columns([1, 3])
    with col_a:
        generate = st.button("✨ Generate Resume PDF", type="primary", use_container_width=True)

    if generate:
        if not data.get("name"):
            st.error("Please enter at least your name before generating the resume.")
        else:
            with st.spinner("Building your PDF..."):
                pdf_bytes = generate_resume_pdf(data)
            st.success("Resume generated successfully! 🎉")
            st.download_button(
                label="📥 Download Resume PDF",
                data=pdf_bytes,
                file_name=f"{data['name'].replace(' ', '_')}_resume.pdf",
                mime="application/pdf"
            )


if __name__ == "__main__":
    main()