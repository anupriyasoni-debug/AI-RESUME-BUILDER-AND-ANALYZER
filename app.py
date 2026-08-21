import os
import streamlit as st
import plotly.graph_objects as go
from dotenv import load_dotenv

from analyzer import extract_text, analyze_resume
from resume_builder import resume_builder_page
from pdf_generator import generate_resume_pdf
from style import CUSTOM_CSS

load_dotenv()

st.set_page_config(page_title="AI Resume Analyzer & Builder", page_icon="📄", layout="wide")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def render_badges(items, css_class, empty_text="None detected"):
    if not items:
        return f"<p class='empty-hint'>{empty_text}</p>"
    spans = "".join(f"<span class='badge {css_class}'>{item}</span>" for item in items)
    return f"<div>{spans}</div>"


def render_card(heading, body_html):
    st.markdown(
        f"<div class='custom-card'><div class='section-heading'>{heading}</div>{body_html}</div>",
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


def hero(title, subtitle):
    st.markdown(
        f"<div class='hero-header'><h1>{title}</h1><p>{subtitle}</p></div>",
        unsafe_allow_html=True
    )


def main():
    st.sidebar.markdown("## 📄 AI Resume Toolkit")
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
    hero("🔍 AI Resume Analyzer", "Upload your resume and get an instant ATS score with tailored improvement tips.")

    uploaded_file = st.file_uploader("Upload your resume (PDF or DOCX)", type=["pdf", "docx"])

    if uploaded_file is None:
        st.markdown(
            "<div class='custom-card'><span class='empty-hint'>👆 Drop a PDF or DOCX resume above to get started.</span></div>",
            unsafe_allow_html=True
        )
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
            st.markdown("<div class='section-heading'>Your ATS Score</div>", unsafe_allow_html=True)
            score_gauge(score)

    with col_stats:
        c1, c2 = st.columns(2)
        c1.metric("📊 Word Count", result["word_count"])
        c2.metric("🧩 Sections Found", f'{len(result["sections_found"])}/{len(result["sections_found"]) + len(result["missing_sections"])}')
        c3, c4 = st.columns(2)
        c3.metric("🛠️ Skills Detected", len(result["skills_found"]))
        rating = "Excellent" if score >= 75 else "Needs Work" if score >= 50 else "Low"
        c4.metric("🏷️ Rating", rating)

    col1, col2 = st.columns(2)
    with col1:
        render_card("✅ Detected Skills", render_badges(result["skills_found"], "badge-skill", "No standard skills detected."))
        render_card("📑 Sections Found", render_badges(result["sections_found"], "badge-found"))
    with col2:
        render_card("⚠️ Missing Sections", render_badges(result["missing_sections"], "badge-missing", "All key sections present! 🎉"))

    suggestions_html = "".join(
        f"<div class='suggestion-item'>💡 {s}</div>" for s in result["suggestions"]
    )
    render_card("Improvement Suggestions", suggestions_html)

    with st.expander("View Extracted Text"):
        st.text_area("Extracted Resume Text", text, height=280, label_visibility="collapsed")


def builder_page():
    hero("🛠️ Resume Builder", "Fill in your details and generate a clean, ATS-friendly resume PDF in minutes.")

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