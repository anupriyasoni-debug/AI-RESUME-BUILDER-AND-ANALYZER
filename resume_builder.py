from datetime import datetime
import json
import os
import re
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import streamlit as st
from pdf_generator import (
    COLOR_PALETTES,
    generate_resume_pdf,
    get_pdf_palette,
    render_pdf_to_thumbnail,
    PDF_PALETTES_HEX,
)
from gemini_client import create_gemini_model


TEMPLATE_OPTIONS = [
    "Two-Column Sidebar Layout",
    "Compact / Single-Page Layout",
    "Creative / Bold Header Layout",
    "Elegant / Corporate Layout",
    "Professional Layout",
    "Modern Layout",
    "Clean Layout",
    "Executive Layout",
    "Tech / Developer Layout",
    "Minimalist Layout",
]
TEMPLATE_PREVIEWS = [
    {
        "name": "Two-Column Sidebar Layout",
        "style": "Distinct contact and skills sidebar paired with a focused main experience column.",
        "structure": "Sidebar: contact and skills. Main: summary, experience, projects, education, certifications.",
        "best_for": "Candidates with strong technical breadth and a concise work history.",
    },
    {
        "name": "Compact / Single-Page Layout",
        "style": "Tight leading and compact section rhythm designed to keep a complete resume on one page.",
        "structure": "Summary, experience, projects, education, skills, certifications.",
        "best_for": "Early-career candidates and application portals with strict page limits.",
    },
    {
        "name": "Creative / Bold Header Layout",
        "style": "High-contrast colored top banner with inverted identity text and crisp sections.",
        "structure": "Summary, skills, experience, projects, education, certifications.",
        "best_for": "Creative technology, marketing, design, and portfolio-led applications.",
    },
    {
        "name": "Elegant / Corporate Layout",
        "style": "Refined alignment, subtle divider lines, and understated corporate polish.",
        "structure": "Summary, experience, education, projects, skills, certifications.",
        "best_for": "Corporate, operations, HR, healthcare, and client-facing professionals.",
    },
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
]
COLOR_OPTIONS = list(COLOR_PALETTES)
COLOR_PALETTE_SWATCHES = {
    "Mauve & Plum Velvet": ("#4A355E", "#6D5284", "#B39CCB", "#F7EEF2"),
    "Classic Black & White": ("#111827", "#4B5563", "#9CA3AF", "#FFFFFF"),
    "Navy & Cool Gray": ("#0F172A", "#334155", "#64748B", "#F8FAFC"),
    "Charcoal & Slate": ("#2B2D42", "#8D99AE", "#CBD5E1", "#EDF2F4"),
    "Emerald & Mint": ("#064E3B", "#0D9488", "#34D399", "#ECFDF5"),
    "Burgundy & Cream": ("#581845", "#900C3F", "#C70039", "#FAF3E0"),
    "Midnight & Royal Blue": ("#0A192F", "#1E3A8A", "#60A5FA", "#F0F9FF"),
    "Deep Forest Green": ("#1B4332", "#2D6A4F", "#52B788", "#D8F3DC"),
    "Teal & Seafoam": ("#134E4A", "#14B8A6", "#5EEAD4", "#F0FDFA"),
    "Espresso & Sand": ("#3E2723", "#795548", "#A1887F", "#F5F2EB"),
    "Sapphire & Amber": ("#1E3A8A", "#D97706", "#FBBF24", "#FFFBEB"),
    "Steel & Ice Gray": ("#374151", "#6B7280", "#9CA3AF", "#F3F4F6"),
    "Crimson & Rose": ("#881337", "#E11D48", "#FB7185", "#FFF1F2"),
    "Modern Olive & Khaki": ("#3F4E4F", "#A27B5C", "#A3B899", "#DCD7C9"),
    "Amethyst & Lilac": ("#3B185F", "#9333EA", "#C084FC", "#FAF5FF"),
    "Cobalt & Silver": ("#1D4ED8", "#64748B", "#94A3B8", "#F8FAFC"),
}

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


def _prepare_preview_data(data: dict) -> dict:
    if not isinstance(data, dict):
        data = {}
    sample_name = data.get("name") or "Alex Morgan"
    sample_email = data.get("email") or "alex.morgan@example.com"
    sample_phone = data.get("phone") or "+1 (555) 234-5678"
    sample_linkedin = data.get("linkedin") or "linkedin.com/in/alexmorgan"
    sample_github = data.get("github") or "github.com/alexmorgan"
    sample_location = data.get("location") or "San Francisco, CA"
    sample_summary = (
        data.get("summary")
        or "Accomplished software engineer with 5+ years of experience architecting distributed cloud systems, high-performance web applications, and resilient data pipelines."
    )
    sample_skills = data.get("skills") if data.get("skills") else [
        "Python", "FastAPI", "React", "Docker", "AWS", "PostgreSQL", "System Architecture"
    ]
    sample_certifications = data.get("certifications") if data.get("certifications") else [
        "AWS Certified Solutions Architect", "Certified Kubernetes Administrator (CKA)"
    ]
    sample_experience = data.get("experience") if (data.get("experience") and any(any(item.values()) for item in data.get("experience"))) else [
        {
            "role": "Senior Software Engineer",
            "company": "Tech Innovators Inc.",
            "duration": "2021 - Present",
            "description": "Led team of 7 engineers developing microservices platform. Reduced latency by 35% and scaled system to 5M daily transactions.",
        },
        {
            "role": "Software Developer",
            "company": "Apex Cloud Systems",
            "duration": "2019 - 2021",
            "description": "Engineered CI/CD automated deployment pipelines and built REST APIs with 99.98% uptime SLA.",
        },
    ]
    sample_education = data.get("education") if (data.get("education") and any(any(item.values()) for item in data.get("education"))) else [
        {
            "degree": "B.S. in Computer Science",
            "institute": "University of California, Berkeley",
            "year": "2015 - 2019",
            "score": "3.85 GPA",
        }
    ]
    sample_projects = data.get("projects") if (data.get("projects") and any(any(item.values()) for item in data.get("projects"))) else [
        {
            "title": "Distributed In-Memory Cache",
            "tech": "Python, Redis, gRPC",
            "description": "Designed a fault-tolerant caching tier with dynamic partition rebalancing and sub-millisecond lookups.",
        }
    ]
    return {
        "name": sample_name,
        "email": sample_email,
        "phone": sample_phone,
        "linkedin": sample_linkedin,
        "github": sample_github,
        "location": sample_location,
        "summary": sample_summary,
        "skills": sample_skills,
        "experience": sample_experience,
        "education": sample_education,
        "projects": sample_projects,
        "certifications": sample_certifications,
    }


@st.cache_data(show_spinner=False)
def get_cached_thumbnail(resume_data_json: str, template: str, color_scheme: str) -> bytes:
    try:
        data = json.loads(resume_data_json) if isinstance(resume_data_json, str) else (resume_data_json or {})
    except Exception:
        data = {}
    display_data = _prepare_preview_data(data)
    pdf_bytes = generate_resume_pdf(display_data, template=template, color_scheme=color_scheme)
    return render_pdf_to_thumbnail(pdf_bytes, dpi=115)


generate_cached_thumbnail = get_cached_thumbnail



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
    state.setdefault("selected_template", TEMPLATE_OPTIONS[0])
    state.setdefault("resume_color_scheme", COLOR_OPTIONS[0])
    state.setdefault("selected_color_scheme", COLOR_OPTIONS[0])
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
        top_c1, top_c2 = st.columns([1, 4])
        with top_c1:
            if st.button("← Back to Form"):
                _set_form_widget_state(state.resume_data, overwrite=True)
                state.step = 1
                st.rerun()

        st.subheader("Choose Template & Style")
        st.markdown(
            "Compare all template options dynamically populated with your actual resume content. "
            "Changing the color scheme below instantly re-renders all live previews."
        )

        active_color = state.get("selected_color_scheme") or state.get("resume_color_scheme") or COLOR_OPTIONS[0]
        if active_color not in COLOR_OPTIONS:
            active_color = COLOR_OPTIONS[0]
        color_index = COLOR_OPTIONS.index(active_color)

        st.markdown("#### 🎨 Color Scheme Palette")
        selected_color = st.selectbox(
            "Select Palette (instantly applies to all templates below):",
            COLOR_OPTIONS,
            index=color_index,
            key="_resume_color_picker",
        )
        if selected_color != active_color:
            state.resume_color_scheme = selected_color
            state.selected_color_scheme = selected_color
            active_color = selected_color
            st.rerun()

        # Visual swatch bar
        palette = COLOR_PALETTES[active_color]
        swatches = (
            palette["primary"],
            palette["secondary"],
            palette["border"],
            palette["tint"],
        )
        st.markdown(
            f"""
            <div style="display:flex; flex-wrap:wrap; align-items:center; gap:14px; margin-bottom:1.5rem; padding:10px 16px; background:#ffffff; border-radius:8px; border:1px solid #dbe3ee;">
                <span style="font-weight:600; font-size:0.88rem; color:#1e293b;">Active Theme: <strong>{active_color}</strong></span>
                <span style="display:inline-flex; align-items:center; gap:6px;">
                    <span style="display:inline-block; width:18px; height:18px; border-radius:50%; background:{swatches[0]}; border:1px solid rgba(0,0,0,0.15);"></span>
                    <small style="color:#64748b; font-family:monospace;">Primary {swatches[0]}</small>
                </span>
                <span style="display:inline-flex; align-items:center; gap:6px;">
                    <span style="display:inline-block; width:18px; height:18px; border-radius:50%; background:{swatches[1]}; border:1px solid rgba(0,0,0,0.15);"></span>
                    <small style="color:#64748b; font-family:monospace;">Accent {swatches[1]}</small>
                </span>
                <span style="display:inline-flex; align-items:center; gap:6px;">
                    <span style="display:inline-block; width:18px; height:18px; border-radius:50%; background:{swatches[2]}; border:1px solid rgba(0,0,0,0.15);"></span>
                    <small style="color:#64748b; font-family:monospace;">Border {swatches[2]}</small>
                </span>
                <span style="display:inline-flex; align-items:center; gap:6px;">
                    <span style="display:inline-block; width:18px; height:18px; border-radius:50%; background:{swatches[3]}; border:1px solid #cbd5e1;"></span>
                    <small style="color:#64748b; font-family:monospace;">Paper/Tint {swatches[3]}</small>
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        current_template = state.get("selected_template") or state.get("resume_template") or TEMPLATE_OPTIONS[0]
        if current_template not in TEMPLATE_OPTIONS:
            current_template = TEMPLATE_OPTIONS[0]

        resume_payload_json = json.dumps(state.resume_data or {}, sort_keys=True)

        st.markdown(
            """
            <style>
            .resume-thumbnail-card {
                border: 1px solid #d1d5db;
                border-radius: 8px;
                box-shadow: 0 10px 25px rgba(15, 23, 42, 0.10), 0 2px 6px rgba(15, 23, 42, 0.05);
                background: #ffffff;
                overflow: hidden;
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }
            .resume-thumbnail-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 14px 32px rgba(15, 23, 42, 0.14), 0 3px 8px rgba(15, 23, 42, 0.08);
            }
            .template-metadata-box {
                padding: 0.5rem 0.25rem;
            }
            .active-badge-pill {
                display: inline-block;
                padding: 4px 12px;
                background: #4A355E;
                color: #ffffff;
                border-radius: 9999px;
                font-size: 0.78rem;
                font-weight: 700;
                letter-spacing: 0.04em;
                margin-bottom: 0.5rem;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### 📋 Template Layouts (Linear Comparison)")
        st.caption("Each row below dynamically renders your actual resume content in the active colorway. Click **'Select This Template'** to choose a layout.")

        for index, preview in enumerate(TEMPLATE_PREVIEWS):
            t_name = preview["name"]
            is_active = (t_name == current_template)
            slug = t_name.lower().replace(" ", "_").replace("/", "").replace("-", "_")

            with st.container(border=True):
                col_preview, col_details = st.columns([1, 1.2], gap="large")

                with col_preview:
                    with st.spinner(f"Rendering {t_name}..."):
                        try:
                            thumbnail_bytes = get_cached_thumbnail(
                                resume_payload_json,
                                t_name,
                                active_color,
                            )
                            st.markdown("<div class='resume-thumbnail-card'>", unsafe_allow_html=True)
                            st.image(thumbnail_bytes, width="stretch")
                            st.markdown("</div>", unsafe_allow_html=True)
                        except Exception as err:
                            st.error(f"Error generating thumbnail: {err}")

                with col_details:
                    st.markdown("<div class='template-metadata-box'>", unsafe_allow_html=True)
                    if is_active:
                        st.markdown(
                            f"<div class='active-badge-pill' style='background:{swatches[0]};'>✓ ACTIVE SELECTION</div>",
                            unsafe_allow_html=True,
                        )
                    st.markdown(f"### {t_name}")
                    st.markdown(f"*{preview['style']}*")
                    st.markdown(f"**Structure:** {preview['structure']}")
                    st.markdown(f"**Best for:** {preview['best_for']}")

                    st.write("")
                    if is_active:
                        st.button(
                            "✓ Active Selection",
                            key=f"active_choice_{index}_{slug}",
                            disabled=True,
                            type="primary",
                            width="stretch",
                        )
                    else:
                        if st.button(
                            "Select This Template",
                            key=f"select_choice_{index}_{slug}",
                            type="primary",
                            width="stretch",
                        ):
                            state["selected_template"] = t_name
                            state.resume_template = t_name
                            st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

        st.divider()
        if st.button("Create Resume PDF with Selected Template →", type="primary", width="stretch"):
            state.resume_template = state.get("selected_template", current_template)
            state.resume_color_scheme = active_color
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

        col_nav1, col_nav2 = st.columns([1, 1])
        with col_nav1:
            if st.button("← Change Template or Colors"):
                state.step = 2
                st.rerun()
        with col_nav2:
            if st.button("Start Over"):
                state.resume_data = {}
                state.resume_template = TEMPLATE_OPTIONS[0]
                state.selected_template = TEMPLATE_OPTIONS[0]
                state.resume_color_scheme = COLOR_OPTIONS[0]
                state.selected_color_scheme = COLOR_OPTIONS[0]
                state.resume_pdf = None
                state.step = 1
                state.pop("resume_download_name", None)
                state.pop("_resume_color_picker", None)
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