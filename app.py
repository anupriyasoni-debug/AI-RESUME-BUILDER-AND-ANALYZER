from dotenv import load_dotenv

load_dotenv()

import streamlit as st
import hashlib
import html

from analyzer import (
    JOB_TAXONOMY,
    analyze_resume,
    analyze_job_description_local,
    extract_text,
    generate_suggestions,
)
from resume_builder import resume_builder_page
from resume_comparison import resume_comparison_page
from job_catalog import render_job_selector
from style import DARK_THEME_CSS, GRADIENT_CSS


st.set_page_config(page_title="Resumer | AI Resume Builder & Analyzer", layout="wide")

st.markdown(GRADIENT_CSS, unsafe_allow_html=True)

st.markdown(
    """
    <style>
    :root {
        --ink: #10132a;
        --muted: #6f7185;
        --line: #e8e7f2;
        --accent: #7657ff;
        --blue: #3987ff;
        --mint: #43d9ad;
        --amber: #f5ad3d;
        --surface: #ffffff;
        --canvas: #fafaff;
        --radius-card: 16px;
        --shadow-card: 0 8px 24px rgba(29, 34, 74, .07);
    }
    .stApp { background: var(--canvas); color: var(--ink); }
    .block-container { max-width: 1240px; padding-top: 3rem; }
    :focus-visible { outline: 3px solid #a78bfa !important; outline-offset: 2px !important; }
    .section-heading { display: block; line-height: 1.5; padding-top: .25rem; overflow: visible; }
    .hero {
        position: relative;
        overflow: hidden;
        padding: 2.2rem 2.5rem;
        border: 1px solid #243858;
        border-radius: 22px;
        background: linear-gradient(118deg, #10132a 0%, #26205e 57%, #5141a8 100%);
        color: #f8fafc;
        box-shadow: 0 10px 28px rgba(24, 42, 70, .12);
    }
    .hero h1 { margin: .35rem 0 .7rem; font-size: clamp(2rem, 5vw, 4.4rem); line-height: 1; }
    .eyebrow { color: #67e8f9; font-size: .75rem; font-weight: 800; letter-spacing: .16em; text-transform: uppercase; }
    .hero p { max-width: 720px; color: #cbd5e1; font-size: 1.05rem; }
    .hero-copy { position: relative; z-index: 1; max-width: 760px; }
    .hero-illustration { position: absolute; right: 3%; top: 50%; width: 220px; transform: translateY(-50%); opacity: .94; }
    .quote-card { margin: 1rem 0; padding: .9rem 1.1rem; border-left: 4px solid #8b5cf6; border-radius: 0 12px 12px 0; background: linear-gradient(90deg,#f5f3ff,#eef2ff); color: #3730a3; font-style: italic; }
    .preview-card { min-height: 330px; padding: 1.2rem; border: 1px solid var(--line); border-radius: 12px; background: #fff; box-shadow: 0 3px 12px rgba(15,23,42,.04); }
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
    .capability { min-height: 175px; padding: 1rem; border: 1px solid var(--line); border-top: 3px solid var(--accent); border-radius: var(--radius-card); background: #fff; box-shadow: var(--shadow-card); transition: transform .18s ease, box-shadow .18s ease; }
    .capability:hover { transform: translateY(-3px); box-shadow: 0 13px 28px rgba(29,34,74,.12); }
    .capability h4 { color: var(--ink); margin: .3rem 0; }
    .swatch { display: flex; align-items: center; gap: .65rem; margin-top: .5rem; color: var(--ink); font-family: monospace; }
    .swatch span { width: 30px; height: 30px; border-radius: 7px; border: 1px solid rgba(15,23,42,.18); background: var(--swatch); }
    .font-preview { padding: .75rem 1rem; border: 1px solid var(--line); border-radius: 8px; color: var(--ink); background: rgba(255,255,255,.78); }
    .how-step { min-height: 132px; padding: 1rem 1.1rem; border: 1px solid var(--line); border-radius: var(--radius-card); background: #fff; box-shadow: var(--shadow-card); }
    .how-number { display: inline-grid; place-items: center; width: 30px; height: 30px; border-radius: 10px; background: #f1edff; color: #6042e8; font-weight: 800; }
    @media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration: .01ms !important; animation-iteration-count: 1 !important; scroll-behavior: auto !important; transition-duration: .01ms !important; } }
    @media (max-width: 980px) { .hero-illustration { display: none; } .hero-copy { max-width: 100%; } }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)

def _navigate_to_page(page_name):
    st.session_state["main_navigation"] = page_name


def _score_ring_markup(score):
    score = max(0, min(100, int(score)))
    circumference = 2 * 3.14159 * 42
    offset = circumference * (1 - score / 100)
    return (
        f"<div style='display:flex;align-items:center;gap:14px;padding:.8rem 0' role='img' aria-label='Overall ATS rubric score {score} out of 100'>"
        f"<svg width='106' height='106' viewBox='0 0 100 100' aria-hidden='true'>"
        f"<circle cx='50' cy='50' r='42' fill='none' stroke='#293044' stroke-width='9'/>"
        f"<circle cx='50' cy='50' r='42' fill='none' stroke='#8b7cff' stroke-width='9' stroke-linecap='round' stroke-dasharray='{circumference:.1f}' stroke-dashoffset='{offset:.1f}' transform='rotate(-90 50 50)'/>"
        f"<text x='50' y='48' text-anchor='middle' font-size='24' font-weight='750' fill='#f8fafc'>{score}</text>"
        "<text x='50' y='65' text-anchor='middle' font-size='10' fill='#9aa4b8'>out of 100</text></svg>"
        "<span style='font-size:.85rem;color:#9aa4b8'>Overall<br><strong style='color:#f8fafc'>Resume score</strong></span></div>"
    )


def _render_skill_chips(values, variant):
    values = list(values or [])
    if not values:
        return "<span style='color:#6f7185'>None detected</span>"
    return "".join(
        f"<span style='display:inline-block;margin:.15rem .25rem .15rem 0;padding:.28rem .65rem;border-radius:999px;border:1px solid {'#b7efd9' if variant == 'matched' else '#f6d39e' if variant == 'missing' else '#d9d2ff'};background:{'#edfff7' if variant == 'matched' else '#fff8eb' if variant == 'missing' else '#f4f1ff'};color:{'#176b52' if variant == 'matched' else '#8a5700' if variant == 'missing' else '#51419a'};font-size:.82rem'>{html.escape(str(value))}</span>"
        for value in values
    )


st.sidebar.markdown("<div style='font-size:1.25rem;font-weight:800;letter-spacing:-.02em'>Resumer <span style='color:#a78bfa'>Studio</span></div><div style='color:#aab3c4;font-size:.78rem;margin:.25rem 0 1rem'>Your resume workspace</div>", unsafe_allow_html=True)
page = st.sidebar.radio("Workspace", ["Home / Overview", "Upload & Dual Analyzer", "Resume Builder", "Resume Comparison"], key="main_navigation")


if page == "Home / Overview":
    st.markdown(
        """
        <section class="hero">
            <div class="hero-copy">
                <div class="eyebrow">Resume and role-fit workspace</div>
                <h1>Build a clearer case for your next role</h1>
                <p>Shape your experience, compare role-specific evidence, and export a polished resume. Scoring and writing guidance run locally with transparent rules.</p>
            </div>
            <div class="hero-illustration" aria-hidden="true">
                <svg viewBox="0 0 240 190" role="img" xmlns="http://www.w3.org/2000/svg">
                    <rect x="45" y="15" width="135" height="160" rx="13" fill="#ffffff" opacity=".98"/>
                    <circle cx="75" cy="48" r="13" fill="#c4b5fd"/>
                    <rect x="98" y="39" width="60" height="7" rx="3.5" fill="#3730a3"/>
                    <rect x="98" y="53" width="44" height="5" rx="2.5" fill="#94a3b8"/>
                    <rect x="62" y="78" width="95" height="6" rx="3" fill="#4f46e5"/>
                    <rect x="62" y="91" width="103" height="5" rx="2.5" fill="#cbd5e1"/>
                    <rect x="62" y="102" width="83" height="5" rx="2.5" fill="#cbd5e1"/>
                    <rect x="62" y="120" width="57" height="6" rx="3" fill="#0f766e"/>
                    <rect x="62" y="133" width="97" height="5" rx="2.5" fill="#cbd5e1"/>
                    <rect x="62" y="144" width="78" height="5" rx="2.5" fill="#cbd5e1"/>
                    <circle cx="195" cy="47" r="18" fill="#2dd4bf"/>
                    <path d="m187 47 6 6 11-13" fill="none" stroke="#134e4a" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
                    <circle cx="35" cy="132" r="11" fill="#fbbf24"/>
                    <path d="M30 132h10M35 127v10" stroke="#78350f" stroke-width="2.5" stroke-linecap="round"/>
                </svg>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    cta_build, cta_analyze, cta_hint = st.columns([1.15, 1.25, 2.2], vertical_alignment="center")
    with cta_build:
        st.button("Build my resume", type="primary", use_container_width=True, key="home_build_resume", on_click=_navigate_to_page, args=("Resume Builder",))
    with cta_analyze:
        st.button("Analyze a resume", use_container_width=True, key="home_analyze_resume", on_click=_navigate_to_page, args=("Upload & Dual Analyzer",))
    with cta_hint:
        st.caption("Your files are evaluated locally by this app’s current rule-based tools.")

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
                f'<div class="{card_class}"><h4>{template}</h4>{selected_label}{render_wireframe(variant, name, details)}<p>Sample layout preview · scoring depends on your resume and target role.</p></div>',
                unsafe_allow_html=True,
            )

    st.subheader("Platform Capabilities")
    capabilities = [
        ("Resume Analyzer", "Review role-fit scoring, detected skills, and the checks available in the analyzer.", "Upload & Dual Analyzer"),
        ("Resume Builder", "Add your experience, choose a layout and font, then download the generated PDF.", "Resume Builder"),
        ("Resume Comparison", "Compare two resumes against the same role and see the measured differences.", "Resume Comparison"),
        ("Improvement Insights", "Get draft-specific rule checks and evidence prompts; no achievements are invented.", "Upload & Dual Analyzer"),
    ]
    columns = st.columns(4)
    for index, (column, (title, description, target_page)) in enumerate(zip(columns, capabilities), start=1):
        with column:
            st.markdown(f'<div class="capability"><span style="display:inline-grid;place-items:center;width:30px;height:30px;border-radius:10px;background:{["#f1edff","#eaf2ff","#e9fbf5","#fff4e4"][index-1]};color:{["#7657ff","#3987ff","#158061","#996200"][index-1]};font-weight:800">0{index}</span><h4>{title}</h4><p>{description}</p></div>', unsafe_allow_html=True)
            st.button("Open", key=f"home_feature_{index}", use_container_width=True, on_click=_navigate_to_page, args=(target_page,))

    st.subheader("What you can do here")
    results = st.columns(3)
    results[0].info("Review the selected role’s matched and missing keywords in your resume text.")
    results[1].info("See the analyzer’s section, impact, and length checks with the score breakdown.")
    results[2].info("Build a resume and export a PDF using the available layouts and fonts.")
    st.subheader("How it works")
    step_columns = st.columns(3)
    step_copy = (
        ("Choose a starting point", "Upload a PDF or DOCX, or enter your experience in the builder."),
        ("Review role-specific signals", "Check the rubric score, detected skills, and gaps for your chosen target."),
        ("Refine and export", "Edit your content, select a layout, and download a PDF."),
    )
    for index, (column, (title, description)) in enumerate(zip(step_columns, step_copy), start=1):
        with column:
            st.markdown(f"<div class='how-step'><span class='how-number'>{index}</span><h4>{title}</h4><p style='color:#6f7185;margin-bottom:0'>{description}</p></div>", unsafe_allow_html=True)
    st.markdown("<div class='quote-card'>“Make the evidence easy to find. Let your real work make the case.”</div>", unsafe_allow_html=True)
    with st.expander("What is actually trained, and what does the writing coach use?"):
        st.write(
            "The writing coach and resume comparison currently use local rules, keyword matching, and the scoring rubric; they do not call a generative AI model. "
            "The trained job-skill and skill-review pipelines in the models folder are separate experiments and are not connected to these features. "
            "The optional resume-category classifier is also not active unless its own model artifacts are installed and explicitly enabled."
        )


elif page == "Upload & Dual Analyzer":
    st.header("Resume Analyzer")
    st.caption("Upload your resume to review ATS alignment, matched skills, missing skills, and recommendations.")
    role_column, upload_column = st.columns(2)
    with role_column:
        target_role = st.selectbox("Select Target Job Domain", list(JOB_TAXONOMY.keys()))
    with upload_column:
        uploaded_file = st.file_uploader("Upload Resume (.pdf or .docx)", type=["pdf", "docx"])
        if uploaded_file:
            st.caption(f"Selected file: {uploaded_file.name} · {uploaded_file.size / 1024:.0f} KB")
    job_description, jd_source_label = render_job_selector(key_prefix="analyzer")

    if uploaded_file:
        raw_text = extract_text(uploaded_file)
        if not raw_text:
            st.error("Could not parse selectable text. Please ensure the document is not an image-only scan.")
        else:
            results = analyze_resume(
                raw_text,
                target_role=target_role,
                pasted_jd=job_description,
                target_source_name=jd_source_label,
            )

            if results.get("jd_fallback_notice"):
                st.warning(results["jd_fallback_notice"])

            score_columns = st.columns(4)
            with score_columns[0]:
                st.markdown(_score_ring_markup(results["total_score"]), unsafe_allow_html=True)
                st.metric("Overall ATS Rubric", f"{results['total_score']} / 100")
            score_columns[1].metric("Role Fit", f"{results['role_score']} / 40")
            score_columns[2].metric("Completeness", f"{results['section_score']} / 30")
            score_columns[3].metric("Impact & Length", f"{results['impact_score'] + results['length_score']} / 30")
            st.progress(results["total_score"] / 100)
            st.caption(
                f"**Score Calculation Breakdown:** "
                f"Role Fit: **{results['role_score']}/40** + "
                f"Sections: **{results['section_score']}/30** + "
                f"Action Verbs: **{results['impact_score']}/15** + "
                f"Length ({results['word_count']} words): **{results['length_score']}/15** = "
                f"**Total Score: {results['total_score']}/100**"
            )
            st.caption(
                f"**Role-Fit Source:** {results.get('role_fit_source', target_role)} · "
                "Local heuristic keyword and text alignment assessment (not a guaranteed ATS score or semantic understanding)."
            )

            st.divider()
            target_source_title = "JD Skills" if results.get("using_jd_target") else "Preset Skills"
            analyzed_col, matched_col, missing_col = st.columns(3)
            with analyzed_col:
                st.markdown(f"**Analyzed {target_source_title} ({len(results.get('analyzed_skills', []))})**")
                st.markdown(_render_skill_chips(results.get("analyzed_skills", []), "target"), unsafe_allow_html=True)
            with matched_col:
                st.markdown(f"**Matched Skills ({len(results['matched_skills'])})**")
                st.markdown(_render_skill_chips(results["matched_skills"], "matched"), unsafe_allow_html=True)
            with missing_col:
                st.markdown(f"**Missing Skills ({len(results['missing_skills'])})**")
                st.markdown(_render_skill_chips(results["missing_skills"], "missing"), unsafe_allow_html=True)

            with st.expander("Job Description Match", expanded=bool(job_description.strip())):
                jd_results = results["jd_analysis"]
                if jd_results["available"]:
                    jd_columns = st.columns(3)
                    score_display = f"{jd_results['score']}%" if jd_results["score"] is not None else "N/A"
                    jd_columns[0].metric("JD Keyword Overlap", score_display)
                    jd_columns[1].metric("Matched Terms", len(jd_results["matched_terms"]))
                    jd_columns[2].metric("Terms Analyzed", jd_results.get("terms_analyzed", len(jd_results["matched_terms"]) + len(jd_results["missing_terms"])))

                    if jd_results.get("notice"):
                        st.info(jd_results["notice"])

                    st.markdown("**Analyzed Job Description Skills & Keywords**")
                    analyzed_terms = jd_results.get("terms_analyzed_list", [])
                    st.write(", ".join(f"`{t}`" for t in analyzed_terms) if analyzed_terms else "None detected")

                    jd_matched, jd_missing = st.columns(2)
                    with jd_matched:
                        st.markdown("**Matched JD Terms**")
                        st.write(", ".join(f"`{t}`" for t in jd_results["matched_terms"]) or "No extracted terms matched yet.")
                    with jd_missing:
                        st.markdown("**JD Terms to Address**")
                        st.write(", ".join(f"`{t}`" for t in jd_results["missing_terms"]) or "All extracted terms were found.")

                    st.caption(
                        "**Method Distinction:** **JD Keyword Overlap** measures exact keyword matching of extracted requirements. "
                        "**Local text similarity (TF-IDF)** computes length-normalized cosine similarity across all vocabulary. "
                        "Neither percentage is a guaranteed ATS score or an employer's actual screening result."
                    )

                    jd_fingerprint = hashlib.sha256(
                        f"{raw_text}\0{job_description}".encode("utf-8")
                    ).hexdigest()
                    if st.button("Compute Local Text Similarity (TF-IDF)", key="analyze_jd_local"):
                        try:
                            with st.spinner("Reviewing resume evidence against the job description locally..."):
                                ai_jd_results = analyze_job_description_local(raw_text, job_description, target_role=target_role)
                            st.session_state["local_jd_analysis"] = (jd_fingerprint, ai_jd_results)
                            st.session_state.pop("local_jd_analysis_error", None)
                        except Exception as exc:
                            st.session_state["local_jd_analysis_error"] = (jd_fingerprint, str(exc))

                    stored_ai_jd = st.session_state.get("local_jd_analysis")
                    if stored_ai_jd and stored_ai_jd[0] == jd_fingerprint:
                        ai_jd_results = stored_ai_jd[1]
                        st.metric("Local text similarity (TF-IDF)", f"{ai_jd_results['score']}%")
                        st.caption(f"Evaluated with: {ai_jd_results['model']}")
                        st.caption(
                            "This metric measures lexical text similarity based on term-frequency overlap. "
                            "It does not measure semantic understanding, candidate seniority, or work quality."
                        )
                        ai_matched, ai_missing = st.columns(2)
                        with ai_matched:
                            st.markdown("**Matched Evidence Terms**")
                            st.write(", ".join(f"`{t}`" for t in ai_jd_results["matched_terms"]) or "No direct evidence identified.")
                        with ai_missing:
                            st.markdown("**Identified Term Gaps**")
                            st.write(", ".join(f"`{t}`" for t in ai_jd_results["missing_terms"]) or "No major gaps identified.")
                        st.markdown("**Local Analysis Feedback**")
                        for suggestion in ai_jd_results["feedback"]:
                            st.markdown(f"- {suggestion}")

                    ai_jd_error = st.session_state.get("local_jd_analysis_error")
                    if ai_jd_error and ai_jd_error[0] == jd_fingerprint:
                        st.warning(f"Job-fit analysis notice: {ai_jd_error[1]}")
                else:
                    st.info("Paste a job description above to see its matched and missing terms.")

            with st.expander("Skills & Keyword Analysis"):
                if results.get("using_jd_target"):
                    st.caption(f"Target evaluated: **{results.get('role_fit_source')}** (Job Description requirements supersede preset keywords for the 40-pt role fit).")
                else:
                    st.caption(f"Target evaluated: **{results.get('role_fit_source')}**")
                skill_columns = st.columns(2)
                with skill_columns[0]:
                    st.markdown("**Target Skills Found**")
                    st.write(", ".join(f"`{s}`" for s in results["matched_skills"]) or "No target skills detected.")
                with skill_columns[1]:
                    st.markdown("**Target Skills Missing**")
                    st.write(", ".join(f"`{s}`" for s in results["missing_skills"]) or "All target skills matched.")
                if not results.get("using_jd_target") and (results["matched_keywords"] or results["missing_keywords"]):
                    keyword_columns = st.columns(2)
                    with keyword_columns[0]:
                        st.markdown("**Preset Keywords Found**")
                        st.write(", ".join(f"`{k}`" for k in results["matched_keywords"]) or "No preset keywords detected.")
                    with keyword_columns[1]:
                        st.markdown("**Preset Keywords Missing**")
                        st.write(", ".join(f"`{k}`" for k in results["missing_keywords"]) or "All taxonomy keywords matched.")

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
    else:
        st.info("Upload a selectable-text PDF or a DOCX resume to see the role-fit score, skill evidence, and practical improvement checks.")

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
