from datetime import datetime
import json
import os
import re
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import streamlit as st
from pdf_generator import generate_resume_pdf, get_pdf_palette
from gemini_client import create_gemini_model


TEMPLATE_OPTIONS = [
    "Professional Layout", "Modern Layout", "Clean Layout", "Executive Layout",
    "Tech / Developer Layout", "Minimalist Layout", "Two-Column Sidebar Layout",
    "Creative / Bold Header Layout", "Compact / Single-Page Layout", "Elegant / Corporate Layout",
]
TEMPLATE_PREVIEWS = [
    {
        "name": "Professional Layout",
        "style": "Centered name with balanced spacing and clear section dividers.",
        "structure": "Summary, experience, projects, education, skills, certifications.",
        "best_for": "Corporate, consulting, finance, and other traditional roles.",
    },
    {
        "name": "Modern Layout",
        "style": "Bold color banner, left-aligned identity, and highlighted section headers.",
        "structure": "Summary and skills lead, followed by experience, projects, and education.",
        "best_for": "Technology, startups, and contemporary creative teams.",
    },
    {
        "name": "Clean Layout",
        "style": "Minimal header, compact section accents, and uncluttered spacing.",
        "structure": "Skills and education first, followed by summary and experience.",
        "best_for": "Academic, early-career, and ATS-focused applications.",
    },
    {
        "name": "Executive Layout",
        "style": "Classic serif-inspired hierarchy with formal border accents and generous authority.",
        "structure": "Summary, experience, projects, education, skills, certifications.",
        "best_for": "Senior leaders, consulting, law, finance, and board-ready profiles.",
    },
    {
        "name": "Tech / Developer Layout",
        "style": "Compact, skills-first presentation with technical monospace-inspired accents.",
        "structure": "Skills, summary, experience, projects, education, certifications.",
        "best_for": "Software engineering, data, infrastructure, and product development roles.",
    },
    {
        "name": "Minimalist Layout",
        "style": "Ultra-clean whitespace, thin rules, and restrained typography for effortless scanning.",
        "structure": "Summary, experience, projects, education, skills, certifications.",
        "best_for": "Design-conscious professionals and modern ATS submissions.",
    },
    {
        "name": "Two-Column Sidebar Layout",
        "style": "Distinct contact and skills sidebar paired with a focused main experience column.",
        "structure": "Sidebar: contact and skills. Main: summary, experience, projects, education, certifications.",
        "best_for": "Candidates with strong technical breadth and a concise work history.",
    },
    {
        "name": "Creative / Bold Header Layout",
        "style": "High-contrast colored top banner with inverted identity text and crisp sections.",
        "structure": "Summary, skills, experience, projects, education, certifications.",
        "best_for": "Creative technology, marketing, design, and portfolio-led applications.",
    },
    {
        "name": "Compact / Single-Page Layout",
        "style": "Tight leading and compact section rhythm designed to keep a complete resume on one page.",
        "structure": "Summary, experience, projects, education, skills, certifications.",
        "best_for": "Early-career candidates and application portals with strict page limits.",
    },
    {
        "name": "Elegant / Corporate Layout",
        "style": "Refined alignment, subtle divider lines, and understated corporate polish.",
        "structure": "Summary, experience, education, projects, skills, certifications.",
        "best_for": "Corporate, operations, HR, healthcare, and client-facing professionals.",
    },
]
COLOR_OPTIONS = [
    "Navy and White",
    "Charcoal and Slate",
    "Dark Green and White",
    "Burgundy and Cream",
    "Classic Black and White",
]
TEMPLATE_SECTIONS = {
    "Professional Layout": ("SUMMARY", "EXPERIENCE", "PROJECTS", "EDUCATION", "SKILLS", "CERTIFICATIONS"),
    "Modern Layout": ("SUMMARY", "SKILLS", "EXPERIENCE", "PROJECTS", "EDUCATION", "CERTIFICATIONS"),
    "Clean Layout": ("SKILLS", "SUMMARY", "EDUCATION", "EXPERIENCE", "PROJECTS", "CERTIFICATIONS"),
    "Executive Layout": ("SUMMARY", "EXPERIENCE", "PROJECTS", "EDUCATION", "SKILLS", "CERTIFICATIONS"),
    "Tech / Developer Layout": ("SKILLS", "SUMMARY", "EXPERIENCE", "PROJECTS", "EDUCATION", "CERTIFICATIONS"),
    "Minimalist Layout": ("SUMMARY", "EXPERIENCE", "PROJECTS", "EDUCATION", "SKILLS", "CERTIFICATIONS"),
    "Two-Column Sidebar Layout": ("SUMMARY", "EXPERIENCE", "PROJECTS", "EDUCATION", "CERTIFICATIONS"),
    "Creative / Bold Header Layout": ("SUMMARY", "SKILLS", "EXPERIENCE", "PROJECTS", "EDUCATION", "CERTIFICATIONS"),
    "Compact / Single-Page Layout": ("SUMMARY", "EXPERIENCE", "PROJECTS", "EDUCATION", "SKILLS", "CERTIFICATIONS"),
    "Elegant / Corporate Layout": ("SUMMARY", "EXPERIENCE", "EDUCATION", "PROJECTS", "SKILLS", "CERTIFICATIONS"),
}
AI_REWRITE_MODES = [
    "Improve",
    "Make concise",
    "Make professional",
    "Add impact",
    "Fix grammar",
    "ATS optimize",
]
DATABASE_PATH = Path(__file__).with_name("resumes.db")


def _initialise_resume_database():
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS resume_versions (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                saved_at TEXT NOT NULL,
                template TEXT NOT NULL,
                color_scheme TEXT NOT NULL,
                data_json TEXT NOT NULL
            )
            """
        )


def _list_resume_versions():
    _initialise_resume_database()
    with sqlite3.connect(DATABASE_PATH) as connection:
        rows = connection.execute(
            """
            SELECT id, name, saved_at, template, color_scheme, data_json
            FROM resume_versions
            ORDER BY rowid
            """
        ).fetchall()
    return [
        {
            "id": row[0],
            "name": row[1],
            "saved_at": row[2],
            "template": row[3],
            "color_scheme": row[4],
            "data": json.loads(row[5]),
        }
        for row in rows
    ]


def _save_resume_version(version):
    _initialise_resume_database()
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            INSERT INTO resume_versions (id, name, saved_at, template, color_scheme, data_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                version["id"],
                version["name"],
                version["saved_at"],
                version["template"],
                version["color_scheme"],
                json.dumps(version["data"]),
            ),
        )


def _get_resume_version(version_id):
    _initialise_resume_database()
    with sqlite3.connect(DATABASE_PATH) as connection:
        row = connection.execute(
            """
            SELECT id, name, saved_at, template, color_scheme, data_json
            FROM resume_versions
            WHERE id = ?
            """,
            (version_id,),
        ).fetchone()
    if row is None:
        return None
    return {
        "id": row[0],
        "name": row[1],
        "saved_at": row[2],
        "template": row[3],
        "color_scheme": row[4],
        "data": json.loads(row[5]),
    }


def _preview_section_markup(section_names, variant):
    return "".join(
        f"<section class='html-resume-section {variant}-section'><h5>{section}</h5>"
        "<span class='html-resume-rule'></span><i></i><i></i><i class='short'></i></section>"
        for section in section_names
    )


def _professional_html_preview(palette):
    return (
        "<div class='html-resume professional-html'><header><h3>OLIVER SMITH</h3><p>oliver.smith@example.com | +1 (555) 234-5678</p>"
        "<p>linkedin.com/in/oliversmith | github.com/oliversmith</p></header>"
        f"{_preview_section_markup(TEMPLATE_SECTIONS['Professional Layout'], 'professional')}</div>"
    )


def _modern_html_preview(palette):
    return (
        "<div class='html-resume modern-html'><header><div><small>PRODUCT ENGINEER</small>"
        "<h3>JORDAN LEE</h3><p>jordan.lee@example.com | Austin, TX</p></div><b>94<br><small>ATS</small></b></header>"
        f"<main>{_preview_section_markup(TEMPLATE_SECTIONS['Modern Layout'], 'modern')}</main></div>"
    )


def _clean_html_preview(palette):
    return (
        "<div class='html-resume clean-html'><header><h3>TAYLOR REED</h3>"
        "<p>taylor.reed@example.com / University of Technology</p></header>"
        f"{_preview_section_markup(TEMPLATE_SECTIONS['Clean Layout'], 'clean')}</div>"
    )


def _executive_html_preview(palette):
    return (
        "<div class='html-resume executive-html'><header><span>EXECUTIVE PROFILE</span><h3>OLIVER SMITH</h3>"
        "<p>Strategy | Operations | Transformation</p></header><div class='executive-border'>"
        f"{_preview_section_markup(TEMPLATE_SECTIONS['Executive Layout'], 'executive')}</div></div>"
    )


def _tech_html_preview(palette):
    return (
        "<div class='html-resume tech-html'><header><code>./resume --candidate oliver</code><h3>OLIVER_SMITH</h3>"
        "<p>oliver@devmail.io // github.com/oliversmith</p></header><div class='tech-grid'>"
        "<aside><h5>STACK</h5><code>Python<br>Docker<br>AWS<br>PostgreSQL<br>PyTorch</code></aside>"
        f"<main>{_preview_section_markup(('SUMMARY', 'EXPERIENCE', 'PROJECTS', 'EDUCATION', 'CERTIFICATIONS'), 'tech')}</main>"
        "</div></div>"
    )


def _minimalist_html_preview(palette):
    return (
        "<div class='html-resume minimalist-html'><header><h3>oliver smith</h3>"
        "<p>ENGINEERING LEADER<br>oliver.smith@example.com / London</p></header>"
        f"<div class='minimalist-body'>{_preview_section_markup(TEMPLATE_SECTIONS['Minimalist Layout'], 'minimalist')}</div></div>"
    )


def _sidebar_html_preview(palette):
    return (
        "<div class='html-resume sidebar-html'><aside><h3>OLIVER<br>SMITH</h3><h5>CONTACT</h5>"
        "<p>oliver@example.com<br>London, UK<br>linkedin.com/in/oliver</p><h5>SKILLS</h5>"
        "<p>Python<br>Leadership<br>Cloud Systems<br>Strategy</p></aside><main>"
        f"{_preview_section_markup(('SUMMARY', 'EXPERIENCE', 'PROJECTS', 'EDUCATION', 'CERTIFICATIONS'), 'sidebar')}</main></div>"
    )


def _creative_html_preview(palette):
    return (
        "<div class='html-resume creative-html'><header><small>CREATIVE TECHNOLOGY</small>"
        "<h3>OLIVER<br>SMITH</h3><p>Designing useful systems with character.</p></header>"
        f"<div class='creative-body'>{_preview_section_markup(TEMPLATE_SECTIONS['Creative / Bold Header Layout'], 'creative')}</div></div>"
    )


def _compact_html_preview(palette):
    return (
        "<div class='html-resume compact-html'><header><h3>OLIVER SMITH</h3>"
        "<p>oliver@example.com | London | github.com/oliver</p></header>"
        f"<div class='compact-columns'><main>{_preview_section_markup(('SUMMARY', 'EXPERIENCE', 'PROJECTS'), 'compact')}</main>"
        f"<aside>{_preview_section_markup(('EDUCATION', 'SKILLS', 'CERTIFICATIONS'), 'compact')}</aside></div></div>"
    )


def _corporate_html_preview(palette):
    return (
        "<div class='html-resume corporate-html'><header><div><small>PROFESSIONAL RESUME</small>"
        "<h3>OLIVER SMITH</h3></div><p>oliver@example.com<br>London, UK<br>+1 555 234 5678</p></header>"
        f"<div class='corporate-body'>{_preview_section_markup(TEMPLATE_SECTIONS['Elegant / Corporate Layout'], 'corporate')}</div></div>"
    )


TEMPLATE_HTML_RENDERERS = {
    "Professional Layout": _professional_html_preview,
    "Modern Layout": _modern_html_preview,
    "Clean Layout": _clean_html_preview,
    "Executive Layout": _executive_html_preview,
    "Tech / Developer Layout": _tech_html_preview,
    "Minimalist Layout": _minimalist_html_preview,
    "Two-Column Sidebar Layout": _sidebar_html_preview,
    "Creative / Bold Header Layout": _creative_html_preview,
    "Compact / Single-Page Layout": _compact_html_preview,
    "Elegant / Corporate Layout": _corporate_html_preview,
}


def _build_template_html_preview(template, color_scheme):
    return TEMPLATE_HTML_RENDERERS[template](get_pdf_palette(color_scheme))


def _gemini_error_message(exc, feature):
    error_text = str(exc).lower()
    status_code = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    error_type = type(exc).__name__.lower()
    if (
        status_code == 429
        or "429" in error_text
        or "quota" in error_text
        or "rate limit" in error_text
        or "resourceexhausted" in error_type
    ):
        return (
            f"Gemini {feature} is temporarily unavailable because the API rate limit or quota "
            "was reached. Please wait a moment and try again, or check your Gemini usage and billing settings."
        )
    return f"Gemini {feature} failed ({type(exc).__name__}). Check your API configuration and try again."


def _rewrite_selected_bullet(text_key, selection_key, mode_key, status_key, context_keys):
    state = st.session_state
    text = state.get(text_key, "")
    lines = text.splitlines()
    nonempty_line_indexes = [index for index, line in enumerate(lines) if line.strip()]
    selected_position = state.get(selection_key, 0)
    if not nonempty_line_indexes or not isinstance(selected_position, int) or selected_position >= len(nonempty_line_indexes):
        state[status_key] = ("error", "Add a text line and select it before requesting an improvement.")
        return

    selected_line_index = nonempty_line_indexes[selected_position]
    selected_line = lines[selected_line_index]
    prefix_match = re.match(r"^(\s*(?:[-*•▪◦]|\d+[.)])\s+)(.*)$", selected_line)
    bullet_prefix = prefix_match.group(1) if prefix_match else ""
    original_bullet = prefix_match.group(2) if prefix_match else selected_line.strip()
    mode = state.get(mode_key, AI_REWRITE_MODES[0])
    instructions = {
        "Improve": "Improve clarity, specificity, and flow while preserving the original meaning.",
        "Make concise": "Make the bullet more concise while preserving its most important facts and outcomes.",
        "Make professional": "Rewrite the bullet in polished, professional resume language.",
        "Add impact": "Emphasize ownership, scale, and measurable outcomes when the source provides evidence. Never invent metrics or accomplishments; if no metric is supplied, strengthen the stated impact without adding numbers.",
        "Fix grammar": "Correct grammar, spelling, and punctuation while preserving the original meaning.",
        "ATS optimize": "Use relevant role and technology terms naturally without keyword stuffing or unsupported claims.",
    }
    context = [
        state.get(key, "").strip()
        for key in context_keys
        if state.get(key, "").strip()
    ]

    try:
        _, model = create_gemini_model()
        response = model.generate_content(
            "You are a resume bullet editor. Return only one complete rewritten bullet, without commentary. "
            "Preserve the user's facts, tools, scope, and meaning. Never invent employers, skills, "
            "responsibilities, outcomes, or numbers. Finish all sentences cleanly and never stop "
            "mid-sentence or return a fragment.\n\n"
            f"Mode: {mode}. {instructions[mode]}\n"
            f"Context: {'; '.join(context) if context else 'Resume bullet'}\n"
            f"Bullet to rewrite:\n{original_bullet}",
            generation_config={"temperature": 0.2, "max_output_tokens": 500},
        )
        improved_bullet = (response.text or "").strip()
        if not improved_bullet:
            state[status_key] = ("error", "Gemini returned no rewritten bullet. Try again.")
            return
        generated_prefix = re.match(r"^\s*(?:[-*•▪◦]|\d+[.)])\s+(.*)$", improved_bullet)
        if generated_prefix:
            improved_bullet = generated_prefix.group(1)
        lines[selected_line_index] = f"{bullet_prefix}{improved_bullet}"
        state[text_key] = "\n".join(lines)
        state[status_key] = ("success", f"Selected bullet updated with mode: {mode}.")
    except Exception as exc:
        state[status_key] = (
            "error",
            _gemini_error_message(exc, "bullet enhancement"),
        )


def _render_bullet_ai_controls(text_key, key_prefix, context_keys=()):
    state = st.session_state
    selection_key = f"{key_prefix}_ai_bullet_index"
    mode_key = f"{key_prefix}_ai_mode"
    status_key = f"{key_prefix}_ai_status"
    bullets = [line.strip() for line in state.get(text_key, "").splitlines() if line.strip()]
    selected_position = state.get(selection_key)
    if not isinstance(selected_position, int) or not 0 <= selected_position < len(bullets):
        state[selection_key] = 0

    st.markdown("**AI Assistant**")
    selection_column, mode_column, action_column = st.columns([3, 2, 1])
    with selection_column:
        st.selectbox(
            "Select bullet to improve",
            options=range(len(bullets)),
            format_func=lambda index: bullets[index][:90],
            key=selection_key,
            disabled=not bullets,
        )
    with mode_column:
        st.selectbox("Enhancement mode", AI_REWRITE_MODES, key=mode_key)
    with action_column:
        st.button(
            "Improve with AI",
            key=f"{key_prefix}_improve_ai",
            disabled=not bullets,
            on_click=_rewrite_selected_bullet,
            args=(text_key, selection_key, mode_key, status_key, context_keys),
        )

    status = state.pop(status_key, None)
    if status:
        level, message = status
        if level == "success":
            st.success(message)
        else:
            st.warning(message)


def _live_writing_tip(text, section):
    words = text.split()
    if not words:
        if section == "professional summary":
            return "Start with your target role, strongest skills, and one evidence-backed achievement."
        return "Describe the action, scope, and result; start each achievement with a clear verb."

    if section == "professional summary":
        if len(words) < 30:
            return "Add a specific strength or outcome to make this summary more distinctive."
        if len(words) > 90:
            return "Consider trimming this to a focused 2-4 sentences."
        if not re.search(r"\b\d+(?:\.\d+)?%?\b", text):
            return "Add a scale or result only if you can support it with a real example."
        return "Keep the focus on role, expertise, and evidence-backed impact."

    if not re.search(r"\b(?:built|created|delivered|designed|developed|improved|implemented|increased|led|managed|optimized|reduced|launched|automated)\b", text, re.I):
        return "Lead each achievement with a direct action verb."
    if not re.search(r"\b\d+(?:\.\d+)?%?\b", text):
        return "Add a real metric, scale, or outcome if available; don't estimate one."
    return "Good structure: make sure the outcome is clear and supported by your experience."


def _request_writing_suggestions(text, section, context):
    _, model = create_gemini_model()
    response = model.generate_content(
        "You are an intelligent, adaptive resume coach. First analyze the specific draft, section, "
        "and context provided, then identify the highest-value improvements for this candidate. "
        "Give three concise, specific, and varied suggestions that are clearly grounded in the "
        "draft. Adapt your advice to the section: for example, focus on positioning and evidence "
        "in a summary, ownership and measurable outcomes in experience, and clarity or technical "
        "relevance in projects. Prioritize the issues that actually appear instead of repeating "
        "generic advice or a fixed phrase. Do not rewrite the draft, invent facts, or suggest "
        "unsupported metrics. Explain briefly what to improve and why. Return exactly three numbered "
        "items, with each item written as one or two complete, grammatically correct sentences. "
        "Finish every sentence before moving to the next item, and do not end with a fragment, "
        "ellipsis, or unfinished suggestion.\n\n"
        f"Section: {section}\nContext: {context or 'Not provided'}\nDraft:\n{text}",
        generation_config={"temperature": 0.3, "max_output_tokens": 600},
    )
    suggestions = (response.text or "").strip()
    if not suggestions:
        raise ValueError("Gemini returned no writing suggestions. Try again.")
    return suggestions


def _render_writing_assistant(text_key, key_prefix, section, context_keys=()):
    state = st.session_state
    text = state.get(text_key, "")
    context = "; ".join(
        state.get(key, "").strip()
        for key in context_keys
        if state.get(key, "").strip()
    )
    st.caption(f"Live writing tip: {_live_writing_tip(text, section)}")

    result_key = f"{key_prefix}_writing_suggestions"
    if st.button("Get AI suggestions", key=f"{key_prefix}_get_suggestions", disabled=not text.strip()):
        try:
            with st.spinner("Reviewing your draft..."):
                state[result_key] = {
                    "draft": text,
                    "context": context,
                    "suggestions": _request_writing_suggestions(text, section, context),
                    "error": None,
                }
        except Exception as exc:
            state[result_key] = {
                "draft": text,
                "context": context,
                "error": _gemini_error_message(exc, "writing suggestions"),
            }

    result = state.get(result_key)
    if result and result.get("draft") == text and result.get("context") == context:
        if result.get("error"):
            st.warning(result["error"])
        elif result.get("suggestions"):
            st.info(result["suggestions"])


def resume_builder_page():
    state = st.session_state
    state.setdefault("step", 1)
    state.setdefault("resume_data", {})
    state.setdefault("resume_template", TEMPLATE_OPTIONS[0])
    state.setdefault("resume_color_scheme", COLOR_OPTIONS[-1])
    state.setdefault("resume_pdf", None)

    if state.step == 1:
        _set_form_widget_state(state.resume_data)
        st.markdown("<div class='section-heading'>📝 Build Your Resume</div>", unsafe_allow_html=True)

        data = {}
        container = st.container(border=True)
        tabs = container.tabs(["👤 Personal", "🎓 Education", "💼 Experience", "🚀 Projects", "🛠️ Skills", "📜 Certifications"])

        with tabs[0]:
            col1, col2 = st.columns(2)
            with col1:
                data["name"] = st.text_input("Full Name", placeholder="Mahak Sahu", key="builder_name")
                data["email"] = st.text_input("Email", placeholder="mahak@example.com", key="builder_email")
                data["phone"] = st.text_input("Phone Number", placeholder="+91 9876543210", key="builder_phone")
                data["location"] = st.text_input("Location (City, Country)", key="builder_location")
            with col2:
                data["linkedin"] = st.text_input("LinkedIn / Portfolio URL", placeholder="linkedin.com/in/mahaksahu", key="builder_linkedin")
                data["github"] = st.text_input("GitHub Profile URL", placeholder="github.com/mahaksahu", key="builder_github")
                data["summary"] = st.text_area(
                    "Professional Summary", height=100,
                    placeholder="Results-driven engineering student specializing in Artificial Intelligence and scalable backend services.",
                    key="builder_summary",
                )
                _render_writing_assistant("builder_summary", "summary", "professional summary")

        with tabs[1]:
            num_edu = st.number_input("Number of education entries", min_value=0, max_value=5, key="num_edu")
            education = []
            for i in range(int(num_edu)):
                st.markdown(f"**Education #{i + 1}**")
                c1, c2 = st.columns(2)
                with c1:
                    degree = st.text_input("Degree / Course", key=f"edu_degree_{i}")
                    year = st.text_input("Year", key=f"edu_year_{i}")
                with c2:
                    institute = st.text_input("Institute / University", key=f"edu_institute_{i}")
                    score = st.text_input("Score / CGPA (optional)", key=f"edu_score_{i}")
                education.append({"degree": degree, "institute": institute, "year": year, "score": score})
                if i < int(num_edu) - 1:
                    st.divider()
            data["education"] = education

        with tabs[2]:
            num_exp = st.number_input("Number of experience entries", min_value=0, max_value=5, key="num_exp")
            experience = []
            for i in range(int(num_exp)):
                st.markdown(f"**Experience #{i + 1}**")
                c1, c2 = st.columns(2)
                with c1:
                    role = st.text_input("Job Title", key=f"exp_role_{i}")
                with c2:
                    company = st.text_input("Company", key=f"exp_company_{i}")
                duration = st.text_input("Duration (e.g. Jan 2023 - Present)", key=f"exp_duration_{i}")
                description = st.text_area("Description", key=f"exp_desc_{i}", height=80)
                _render_writing_assistant(
                    f"exp_desc_{i}",
                    f"exp_{i}",
                    "experience description",
                    context_keys=(f"exp_role_{i}", f"exp_company_{i}", f"exp_duration_{i}"),
                )
                _render_bullet_ai_controls(
                    f"exp_desc_{i}",
                    f"exp_{i}",
                    context_keys=(f"exp_role_{i}", f"exp_company_{i}", f"exp_duration_{i}"),
                )
                experience.append({"role": role, "company": company, "duration": duration, "description": description})
                if i < int(num_exp) - 1:
                    st.divider()
            data["experience"] = experience

        with tabs[3]:
            num_proj = st.number_input("Number of projects", min_value=0, max_value=5, key="num_proj")
            projects = []
            for i in range(int(num_proj)):
                st.markdown(f"**Project #{i + 1}**")
                title = st.text_input("Project Title", key=f"proj_title_{i}")
                tech = st.text_input("Tech Stack Used", key=f"proj_tech_{i}")
                description = st.text_area("Description", key=f"proj_desc_{i}", height=80)
                _render_bullet_ai_controls(
                    f"proj_desc_{i}",
                    f"proj_{i}",
                    context_keys=(f"proj_title_{i}", f"proj_tech_{i}"),
                )
                projects.append({"title": title, "tech": tech, "description": description})
                if i < int(num_proj) - 1:
                    st.divider()
            data["projects"] = projects

        with tabs[4]:
            skills_text = st.text_area(
                "Technical & Core Skills", height=100,
                placeholder="Python, PyTorch, C++, SQL, Machine Learning, Docker, Git",
                key="builder_skills_text",
            )
            data["skills"] = [s.strip() for s in skills_text.split(",") if s.strip()]
            if data["skills"]:
                badges = "".join(f"<span class='badge badge-skill'>{s}</span>" for s in data["skills"])
                st.markdown(f"<div style='margin-top:0.5rem;'>{badges}</div>", unsafe_allow_html=True)

        with tabs[5]:
            cert_text = st.text_area("Certifications", height=100, key="builder_certifications")
            data["certifications"] = [c.strip() for c in cert_text.split("\n") if c.strip()]

        _render_progress(data)
        if st.button("Next: Choose Template & Style", type="primary"):
            state.resume_data = data
            state.resume_pdf = None
            state.step = 2
            st.rerun()
        return data

    if state.step == 2:
        state.setdefault("_resume_template_widget", state.resume_template)
        st.subheader("Choose Template & Style")
        if st.button("Back to Form"):
            state.resume_template = state.get("_resume_template_widget", state.resume_template)
            state.resume_color_scheme = state.get("_resume_color_widget", state.resume_color_scheme)
            _set_form_widget_state(state.resume_data, overwrite=True)
            state.step = 1
            st.rerun()

        color_index = COLOR_OPTIONS.index(state.resume_color_scheme)
        st.markdown(
            """
            <style>
            .template-preview {
                min-height: 210px;
                padding: 1rem;
                border: 1px solid #dbe3ee;
                border-top: 4px solid #9aa8b8;
                border-radius: 6px;
                background: rgba(255, 255, 255, 0.88);
                color: #263342;
            }
            .template-preview.is-selected {
                border-color: #315c75;
                border-top-color: #315c75;
                background: #f1f7fa;
            }
            .template-preview h4 {
                margin: 0 0 .65rem;
                color: #172b3a;
                font-size: 1rem;
            }
            .template-preview p {
                margin: .35rem 0;
                font-size: .82rem;
                line-height: 1.45;
            }
            .template-preview strong { color: #172b3a; }
            .html-resume-preview { min-height: 360px; padding: .7rem; border: 1px solid #d4dae0; background: #eef1f4; }
            .html-resume { min-height: 330px; padding: .8rem; overflow: hidden; background: #fff; color: #273444; }
            .html-resume h3, .html-resume h5, .html-resume p { margin: 0; }
            .html-resume h3 { font-size: .82rem; letter-spacing: .05em; }
            .html-resume p, .html-resume code { font-size: .48rem; line-height: 1.5; }
            .html-resume-section { margin-top: .7rem; }
            .html-resume-section h5 { font-size: .48rem; letter-spacing: .1em; }
            .html-resume-section i { display: block; width: 92%; height: 3px; margin-top: .25rem; background: #dce3ea; }
            .html-resume-section i:nth-of-type(2) { width: 78%; }.html-resume-section i.short { width: 56%; }
            .html-resume-rule { display: block; height: 2px; margin: .2rem 0 .25rem; background: #55758b; }
            .professional-html { padding: 1.1rem; text-align: center; }.professional-html header { padding-bottom: .6rem; border-bottom: 2px solid #55758b; }
            .professional-html .html-resume-section { text-align: left; }
            .modern-html { padding: 0; }.modern-html header { display: flex; justify-content: space-between; padding: 1rem; color: #fff; background: #183b56; }.modern-html header b { padding: .3rem .45rem; background: #2f718e; text-align: center; }.modern-html main { padding: .2rem .9rem; }.modern-html .html-resume-rule { height: 6px; background: #e2edf2; border-left: 3px solid #2f718e; }
            .clean-html { padding: 1.2rem; }.clean-html header { padding-bottom: .75rem; border-bottom: 1px solid #cbd5df; }.clean-html .html-resume-rule { width: 24%; height: 1px; background: #55758b; }.clean-html .html-resume-section { margin-top: .8rem; }
            .executive-html { font-family: Georgia, serif; padding: .7rem; border: 5px double #8b6f47; }.executive-html header { padding: .6rem; border-bottom: 1px solid #8b6f47; text-align: center; }.executive-html header span { font-size: .42rem; letter-spacing: .18em; }.executive-html .executive-border { padding: .15rem .45rem; border-left: 1px solid #8b6f47; border-right: 1px solid #8b6f47; }.executive-html .html-resume-rule { background: #8b6f47; }
            .tech-html { font-family: Consolas, monospace; padding: .65rem; background: #17212b; color: #d8f3dc; }.tech-html header { padding-bottom: .6rem; border-bottom: 1px dashed #63c174; }.tech-html h3 { color: #8be28b; }.tech-html .tech-grid { display: grid; grid-template-columns: 31% 1fr; gap: .7rem; }.tech-html aside { padding-top: .75rem; border-right: 1px solid #385446; }.tech-html aside h5 { color: #63c174; }.tech-html main { padding-top: .05rem; }.tech-html .html-resume-section h5 { color: #8be28b; }.tech-html .html-resume-rule { background: #63c174; }.tech-html .html-resume-section i { background: #385446; }
            .minimalist-html { padding: 1.3rem; font-family: Georgia, serif; }.minimalist-html header { padding-bottom: 1.1rem; border-bottom: 1px solid #d9dde1; }.minimalist-html header h3 { font-size: 1rem; font-weight: 400; letter-spacing: .01em; }.minimalist-html .minimalist-body { padding-top: .3rem; }.minimalist-html .html-resume-section { margin-top: 1.05rem; }.minimalist-html .html-resume-rule { height: 1px; background: #b8c0c7; }
            .sidebar-html { display: grid; grid-template-columns: 34% 1fr; padding: 0; }.sidebar-html aside { padding: 1rem .6rem; color: #fff; background: #274c5e; }.sidebar-html aside h3 { font-size: .8rem; line-height: 1.3; }.sidebar-html aside h5 { margin-top: 1.1rem; color: #b9d6d9; font-size: .45rem; letter-spacing: .13em; }.sidebar-html aside p { margin-top: .3rem; color: #edf7f5; }.sidebar-html main { padding: .8rem; }.sidebar-html .html-resume-rule { width: 28%; height: 2px; background: #4d8b8c; }
            .creative-html { padding: 0; }.creative-html header { padding: 1rem; color: #fff; background: #bb3e03; }.creative-html header h3 { margin-top: .35rem; font-size: 1.15rem; line-height: 1.05; }.creative-html header p { margin-top: .6rem; color: #ffe8d6; }.creative-html .creative-body { padding: .2rem 1rem; }.creative-html .html-resume-rule { height: 4px; background: #ee9b00; }
            .compact-html { padding: .65rem; }.compact-html header { padding-bottom: .45rem; border-bottom: 2px solid #334e68; }.compact-html .compact-columns { display: grid; grid-template-columns: 1.5fr 1fr; gap: .75rem; }.compact-html .html-resume-section { margin-top: .5rem; }.compact-html .html-resume-rule { height: 1px; background: #334e68; }.compact-html .html-resume-section i { height: 2px; }
            .corporate-html { padding: .8rem 1rem; }.corporate-html header { display: flex; justify-content: space-between; padding-bottom: .65rem; border-bottom: 1px solid #9aa8b8; }.corporate-html header p { text-align: right; }.corporate-html .corporate-body { padding-top: .15rem; }.corporate-html .html-resume-section { display: grid; grid-template-columns: 28% 1fr; column-gap: .5rem; }.corporate-html .html-resume-section h5 { padding-top: .15rem; color: #315c75; }.corporate-html .html-resume-rule { grid-column: 2; margin-top: 0; background: #9aa8b8; }.corporate-html .html-resume-section i { grid-column: 2; }
            </style>
            """,
            unsafe_allow_html=True,
        )
        for row_start in range(0, len(TEMPLATE_PREVIEWS), 3):
            template_columns = st.columns(3)
            for column, preview in zip(template_columns, TEMPLATE_PREVIEWS[row_start:row_start + 3]):
                with column:
                    selected = state._resume_template_widget == preview["name"]
                    card_class = "template-preview is-selected" if selected else "template-preview"
                    st.markdown(
                        f"<div class='html-resume-preview'>{_build_template_html_preview(preview['name'], state.resume_color_scheme)}</div>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"""
                        <article class="{card_class}">
                            <h4>{preview['name']}</h4>
                            <p>{preview['style']}</p>
                            <p><strong>Structure:</strong> {preview['structure']}</p>
                            <p><strong>Best for:</strong> {preview['best_for']}</p>
                        </article>
                        """,
                        unsafe_allow_html=True,
                    )
                    if st.button(
                        "Selected" if selected else "Select layout",
                        key=f"select_template_{row_start}_{preview['name'].split()[0].lower()}",
                        type="primary" if selected else "secondary",
                        use_container_width=True,
                    ):
                        state._resume_template_widget = preview["name"]
                        state.resume_template = preview["name"]
                        st.rerun()

        st.selectbox("Color Options", COLOR_OPTIONS, index=color_index, key="_resume_color_widget")

        if st.button("Create Resume PDF", type="primary"):
            state.resume_template = state._resume_template_widget
            state.resume_color_scheme = state._resume_color_widget
            state.resume_pdf = None
            state.step = 3
            st.rerun()
        return state.resume_data

    if state.step == 3:
        st.success("Your resume PDF is ready.")
        if state.resume_pdf is None:
            state.resume_pdf = generate_resume_pdf(
                state.resume_data,
                template=state.resume_template,
                color_scheme=state.resume_color_scheme,
            )
        download_name = st.text_input(
            "Resume version / PDF file name",
            placeholder="AI Engineer Resume",
            key="resume_download_name",
        ).strip()
        filename = f"{_safe_pdf_filename(download_name or state.resume_data.get('name') or 'Resume')}.pdf"
        st.download_button(
            "Download PDF",
            data=state.resume_pdf,
            file_name=filename,
            mime="application/pdf",
            on_click=_save_current_resume_version,
        )
        notice = state.pop("resume_version_notice", None)
        if notice:
            st.success(notice)
        if st.button("Start Over"):
            state.resume_data = {}
            state.resume_template = TEMPLATE_OPTIONS[0]
            state.resume_color_scheme = COLOR_OPTIONS[-1]
            state.resume_pdf = None
            state.step = 1
            state.pop("resume_download_name", None)
            state.pop("_resume_template_widget", None)
            state.pop("_resume_color_widget", None)
            _set_form_widget_state({}, overwrite=True)
            st.rerun()
        return state.resume_data

    state.step = 1
    st.rerun()


def _set_form_widget_state(data, overwrite=False):
    education = data.get("education", [])
    experience = data.get("experience", [])
    projects = data.get("projects", [])
    has_saved_data = bool(data)
    defaults = {
        "builder_name": data.get("name", ""),
        "builder_email": data.get("email", ""),
        "builder_phone": data.get("phone", ""),
        "builder_linkedin": data.get("linkedin", ""),
        "builder_github": data.get("github", ""),
        "builder_location": data.get("location", ""),
        "builder_summary": data.get("summary", ""),
        "builder_skills_text": ", ".join(data.get("skills", [])),
        "builder_certifications": "\n".join(data.get("certifications", [])),
        "num_edu": len(education) if has_saved_data else 1,
        "num_exp": len(experience) if has_saved_data else 1,
        "num_proj": len(projects) if has_saved_data else 1,
    }
    for key, value in defaults.items():
        if overwrite or key not in st.session_state:
            st.session_state[key] = value

    active_repeat_keys = set()
    for index in range(len(education)):
        active_repeat_keys.update(f"edu_{field}_{index}" for field in ("degree", "year", "institute", "score"))
    for index in range(len(experience)):
        active_repeat_keys.update(f"exp_{field}_{index}" for field in ("role", "company", "duration", "desc"))
    for index in range(len(projects)):
        active_repeat_keys.update(f"proj_{field}_{index}" for field in ("title", "tech", "desc"))
    repeat_prefixes = ("edu_degree_", "edu_year_", "edu_institute_", "edu_score_", "exp_role_", "exp_company_", "exp_duration_", "exp_desc_", "proj_title_", "proj_tech_", "proj_desc_")
    if overwrite:
        for key in list(st.session_state):
            if key.startswith(repeat_prefixes) and key not in active_repeat_keys:
                del st.session_state[key]

    for index, item in enumerate(education):
        for field in ("degree", "year", "institute", "score"):
            key = f"edu_{field}_{index}"
            if overwrite or key not in st.session_state:
                st.session_state[key] = item.get(field, "")
    for index, item in enumerate(experience):
        for field, widget_field in (("role", "role"), ("company", "company"), ("duration", "duration"), ("description", "desc")):
            key = f"exp_{widget_field}_{index}"
            if overwrite or key not in st.session_state:
                st.session_state[key] = item.get(field, "")
    for index, item in enumerate(projects):
        for field, widget_field in (("title", "title"), ("tech", "tech"), ("description", "desc")):
            key = f"proj_{widget_field}_{index}"
            if overwrite or key not in st.session_state:
                st.session_state[key] = item.get(field, "")


def _collect_active_resume_data():
    state = st.session_state
    education = []
    for index in range(int(state.get("num_edu", 1))):
        education.append({
            "degree": state.get(f"edu_degree_{index}", ""),
            "institute": state.get(f"edu_institute_{index}", ""),
            "year": state.get(f"edu_year_{index}", ""),
            "score": state.get(f"edu_score_{index}", ""),
        })
    experience = []
    for index in range(int(state.get("num_exp", 1))):
        experience.append({
            "role": state.get(f"exp_role_{index}", ""),
            "company": state.get(f"exp_company_{index}", ""),
            "duration": state.get(f"exp_duration_{index}", ""),
            "description": state.get(f"exp_desc_{index}", ""),
        })
    projects = []
    for index in range(int(state.get("num_proj", 1))):
        projects.append({
            "title": state.get(f"proj_title_{index}", ""),
            "tech": state.get(f"proj_tech_{index}", ""),
            "description": state.get(f"proj_desc_{index}", ""),
        })
    skills_text = state.get("builder_skills_text", "")
    return {
        "name": state.get("builder_name", ""),
        "email": state.get("builder_email", ""),
        "phone": state.get("builder_phone", ""),
        "linkedin": state.get("builder_linkedin", ""),
        "github": state.get("builder_github", ""),
        "location": state.get("builder_location", ""),
        "summary": state.get("builder_summary", ""),
        "skills": [skill.strip() for skill in skills_text.split(",") if skill.strip()],
        "experience": experience,
        "projects": projects,
        "education": education,
        "certifications": [item.strip() for item in state.get("builder_certifications", "").splitlines() if item.strip()],
    }


def _save_current_resume_version():
    state = st.session_state
    resume_data = state.get("resume_data") or _collect_active_resume_data()
    existing_versions = _list_resume_versions()
    name = state.get("resume_download_name", "").strip() or f"Resume Version {len(existing_versions) + 1}"
    saved_at = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    version_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
    version = {
        "id": version_id,
        "name": name,
        "saved_at": saved_at,
        "template": state.resume_template,
        "color_scheme": state.resume_color_scheme,
        "data": resume_data,
    }
    try:
        _save_resume_version(version)
    except (OSError, sqlite3.Error, TypeError, ValueError) as exc:
        state.resume_version_notice = f"Could not save downloaded version: {exc}"
        return
    state.resume_data = resume_data
    state.resume_pdf = None
    state.selected_resume_version_id = version_id
    state.resume_version_notice = f"Downloaded and saved '{name}'."


def _safe_pdf_filename(name):
    filename = re.sub(r'[<>:"/\\|?*]+', "", name).strip()
    filename = re.sub(r"\s+", "_", filename)
    return filename or "Resume"


def _render_progress(data):
    checks = [
        bool(data.get("name")),
        bool(data.get("email")),
        bool(data.get("summary")),
        any(any(e.values()) for e in data.get("education", [])),
        any(any(e.values()) for e in data.get("experience", [])),
        any(any(p.values()) for p in data.get("projects", [])),
        bool(data.get("skills")),
    ]
    completion = int(sum(checks) / len(checks) * 100)
    with st.container(border=True):
        st.markdown(f"<div class='section-heading'>Profile Completeness: {completion}%</div>", unsafe_allow_html=True)
        st.progress(completion / 100)