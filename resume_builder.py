from datetime import datetime
from io import BytesIO
import json
import os
import re
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import streamlit as st
from groq import Groq
from PIL import Image, ImageDraw, ImageFont

from pdf_generator import generate_resume_pdf, get_pdf_palette


TEMPLATE_OPTIONS = ["Professional Layout", "Modern Layout", "Clean Layout"]
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


def _build_template_preview(template, color_scheme):
    palette = get_pdf_palette(color_scheme)
    image = Image.new("RGB", (360, 460), "#EEF1F4")
    draw = ImageDraw.Draw(image)
    title_font = ImageFont.load_default(size=15)
    section_font = ImageFont.load_default(size=9)
    page = (14, 10, 346, 450)
    draw.rectangle(page, fill="#FFFFFF", outline="#D4DAE0", width=1)
    left, top, right, _ = page
    content_left = left + 22
    content_right = right - 22
    name = "OLIVER SMITH"
    contact = "oliver.smith@example.com | +1 (555) 234-5678"
    profile_links = "linkedin.com/in/oliversmith | github.com/oliversmith"

    if template == "Modern Layout":
        draw.rectangle((content_left, top + 20, content_right, top + 100), fill=palette["primary"])
        draw.text((content_left + 14, top + 34), name, fill="#FFFFFF", font=title_font)
        draw.text((content_left + 14, top + 58), contact, fill="#FFFFFF", font=section_font)
        draw.text((content_left + 14, top + 73), profile_links, fill="#FFFFFF", font=section_font)
        section_y = top + 116
    elif template == "Professional Layout":
        name_width = draw.textbbox((0, 0), name, font=title_font)[2]
        draw.text(((360 - name_width) / 2, top + 22), name, fill=palette["primary"], font=title_font)
        contact_width = draw.textbbox((0, 0), contact, font=section_font)[2]
        draw.text(((360 - contact_width) / 2, top + 46), contact, fill=palette["muted"], font=section_font)
        links_width = draw.textbbox((0, 0), profile_links, font=section_font)[2]
        draw.text(((360 - links_width) / 2, top + 59), profile_links, fill=palette["muted"], font=section_font)
        draw.line((content_left, top + 78, content_right, top + 78), fill=palette["accent"], width=2)
        section_y = top + 92
    else:
        draw.text((content_left, top + 23), name, fill=palette["primary"], font=title_font)
        draw.text((content_left, top + 47), contact, fill=palette["muted"], font=section_font)
        draw.text((content_left, top + 60), profile_links, fill=palette["muted"], font=section_font)
        draw.line((content_left, top + 79, content_left + 30, top + 79), fill=palette["accent"], width=3)
        section_y = top + 94

    for section in TEMPLATE_SECTIONS[template]:
        if template == "Modern Layout":
            draw.rectangle((content_left, section_y, content_right, section_y + 15), fill=palette["soft"])
            draw.rectangle((content_left, section_y, content_left + 3, section_y + 15), fill=palette["accent"])
            draw.text((content_left + 8, section_y + 3), section, fill=palette["primary"], font=section_font)
        else:
            draw.text((content_left, section_y), section, fill=palette["primary"], font=section_font)
            rule_end = content_right if template == "Professional Layout" else content_left + 25
            draw.line((content_left, section_y + 14, rule_end, section_y + 14), fill=palette["accent"], width=1)
        section_y += 22
        for line_width in (125, 178, 146):
            draw.line(
                (content_left, section_y, min(content_left + line_width, content_right), section_y),
                fill="#DDE2E7",
                width=2,
            )
            section_y += 9
        section_y += 8

    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


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
        "Add impact": "Emphasize ownership, action, and outcome. Never invent metrics or accomplishments.",
        "Fix grammar": "Correct grammar, spelling, and punctuation while preserving the original meaning.",
        "ATS optimize": "Use relevant role and technology terms naturally without keyword stuffing or unsupported claims.",
    }
    context = [
        state.get(key, "").strip()
        for key in context_keys
        if state.get(key, "").strip()
    ]

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your_groq_api_key_here":
        state[status_key] = ("error", "AI enhancement is not configured. Add GROQ_API_KEY to your local .env file.")
        return

    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            temperature=0.2,
            max_tokens=350,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a resume bullet editor. Return only one rewritten bullet, without commentary. "
                        "Preserve the user's facts, tools, scope, and meaning. Never invent employers, skills, "
                        "responsibilities, outcomes, or numbers."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Mode: {mode}. {instructions[mode]}\n"
                        f"Context: {'; '.join(context) if context else 'Resume bullet'}\n"
                        f"Bullet to rewrite:\n{original_bullet}"
                    ),
                },
            ],
        )
        improved_bullet = (response.choices[0].message.content or "").strip()
        if not improved_bullet:
            state[status_key] = ("error", "Groq returned no rewritten bullet. Try again.")
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
            f"Groq AI enhancement failed ({type(exc).__name__}). Check your API configuration and try again.",
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
            </style>
            """,
            unsafe_allow_html=True,
        )
        template_columns = st.columns(3)
        for column, preview in zip(template_columns, TEMPLATE_PREVIEWS):
            with column:
                selected = state._resume_template_widget == preview["name"]
                card_class = "template-preview is-selected" if selected else "template-preview"
                st.image(
                    _build_template_preview(preview["name"], state.resume_color_scheme),
                    width=300,
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
                    key=f"select_template_{preview['name'].split()[0].lower()}",
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