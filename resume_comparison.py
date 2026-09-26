import difflib
import hashlib
import json
import os
import re

from dotenv import load_dotenv

load_dotenv()

import streamlit as st
from groq import Groq

from analyzer import JOB_TAXONOMY, extract_text
from resume_builder import _list_resume_versions


SECTION_HEADINGS = {
    "contact": {"contact", "contact information", "personal details"},
    "summary": {"summary", "professional summary", "objective", "profile", "about me"},
    "education": {"education", "academic background", "academic qualifications"},
    "experience": {"experience", "work experience", "professional experience", "employment", "work history"},
    "skills": {"skills", "technical skills", "technical core skills", "core skills", "competencies"},
    "projects": {"projects", "project experience", "academic projects", "key projects"},
    "certifications": {"certifications", "certificates", "licenses"},
}

SECTION_LABELS = {
    "header": "Header / unsectioned text",
    "summary": "Summary",
    "experience": "Experience",
    "projects": "Projects",
    "education": "Education",
    "skills": "Skills",
    "certifications": "Certifications",
    "contact": "Contact",
}


def _normalise_heading(line):
    value = re.sub(r"^\s*\d+[.)-]?\s*", "", line.lower().strip().rstrip(":"))
    return re.sub(r"[^a-z0-9+#& ]", " ", value).replace("&", " ").strip()


def _split_sections(text):
    sections = {"header": []}
    current_section = "header"
    heading_lookup = {
        _normalise_heading(heading): section
        for section, headings in SECTION_HEADINGS.items()
        for heading in headings
    }
    for line in text.splitlines():
        normalized = _normalise_heading(line)
        section = heading_lookup.get(normalized)
        if section:
            current_section = section
            sections.setdefault(current_section, [])
        elif line.strip():
            sections.setdefault(current_section, []).append(line.rstrip())
    return {section: "\n".join(lines).strip() for section, lines in sections.items()}


def _section_diff(text_a, text_b):
    lines_a = [line.strip() for line in text_a.splitlines() if line.strip()]
    lines_b = [line.strip() for line in text_b.splitlines() if line.strip()]
    added = []
    removed = []
    matcher = difflib.SequenceMatcher(a=lines_a, b=lines_b, autojunk=False)
    for operation, start_a, end_a, start_b, end_b in matcher.get_opcodes():
        if operation in ("delete", "replace"):
            removed.extend(lines_a[start_a:end_a])
        if operation in ("insert", "replace"):
            added.extend(lines_b[start_b:end_b])
    return added, removed


def _matched_role_skills(text, target_role):
    lower_text = text.lower()
    return {
        skill for skill in JOB_TAXONOMY[target_role]["skills"]
        if re.search(rf"(?<!\w){re.escape(skill)}(?!\w)", lower_text)
    }


def _saved_resume_to_text(data):
    lines = []
    contact_items = [
        data.get("name", ""), data.get("email", ""), data.get("phone", ""),
        data.get("linkedin", ""), data.get("github", ""), data.get("location", ""),
    ]
    lines.extend(item for item in contact_items if item)

    section_values = (
        ("Professional Summary", data.get("summary", "")),
        ("Skills", ", ".join(data.get("skills", []))),
    )
    for title, text in section_values:
        if text:
            lines.extend((title, text))

    collection_sections = (
        ("Experience", data.get("experience", []), ("role", "company", "duration", "description")),
        ("Projects", data.get("projects", []), ("title", "tech", "description")),
        ("Education", data.get("education", []), ("degree", "institute", "year", "score")),
    )
    for title, entries, fields in collection_sections:
        populated = [entry for entry in entries if any(entry.values())]
        if populated:
            lines.append(title)
            for entry in populated:
                lines.extend(entry[field] for field in fields if entry.get(field))

    certifications = data.get("certifications", [])
    if certifications:
        lines.extend(("Certifications", *certifications))
    return "\n".join(lines)


def _render_resume_source(slot, saved_versions):
    source = st.radio(
        f"Resume {slot} source",
        ("Upload PDF/DOCX", "Select from Saved Versions"),
        horizontal=True,
        key=f"comparison_source_{slot.lower()}",
    )
    if source == "Upload PDF/DOCX":
        uploaded_file = st.file_uploader(
            f"Resume {slot}", type=["pdf", "docx"], key=f"comparison_resume_{slot.lower()}"
        )
        if not uploaded_file:
            return None, ""
        return uploaded_file.name, extract_text(uploaded_file)

    if not saved_versions:
        st.info("No saved versions yet. Save a version in Resume Builder first.")
        return None, ""

    version_ids = [version["id"] for version in saved_versions]
    versions_by_id = {version["id"]: version for version in saved_versions}
    version_id = st.selectbox(
        f"Saved Resume {slot}",
        version_ids,
        format_func=lambda item_id: versions_by_id[item_id]["name"],
        key=f"comparison_saved_version_{slot.lower()}",
    )
    version = versions_by_id[version_id]
    return version["name"], _saved_resume_to_text(version["data"])


def _compare_with_groq(text_a, text_b, target_role):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your_groq_api_key_here":
        raise ValueError("Groq is not configured. Add GROQ_API_KEY to your local .env file.")

    model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=model_name,
        temperature=0.2,
        max_tokens=1800,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert resume reviewer. Compare the two resume texts for the target role. "
                    "Score each resume independently from 0 to 100 for ATS, skills match, project quality, "
                    "and format/structure, using job-relevant evidence. Be consistent and factual; do not "
                    "invent details. Return only a JSON object with exactly these keys: "
                    "resume_a (object with ats_score, skills_match, projects_quality, format_structure), "
                    "resume_b (same fields), report (detailed natural-language comparison), and "
                    "highlights (array of concise, evidence-based differences)."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Target Job Domain: {target_role}\n\n"
                    f"Resume A:\n{text_a}\n\nResume B:\n{text_b}"
                ),
            },
        ],
    )
    content = response.choices[0].message.content
    if not content:
        raise ValueError("Groq returned an empty comparison response.")
    result = json.loads(content)

    metric_fields = ("ats_score", "skills_match", "projects_quality", "format_structure")
    for version in ("resume_a", "resume_b"):
        if not isinstance(result.get(version), dict):
            raise ValueError("Groq returned an invalid metrics response.")
        for field in metric_fields:
            score = result[version].get(field)
            if isinstance(score, bool) or not isinstance(score, (int, float)):
                raise ValueError("Groq returned a non-numeric metric score.")
            result[version][field] = max(0, min(100, round(score)))
    if not isinstance(result.get("report"), str) or not result["report"].strip():
        raise ValueError("Groq returned no comparison report.")
    result["highlights"] = [
        str(item) for item in result.get("highlights", []) if str(item).strip()
    ]
    result["model"] = model_name
    return result


def _render_change_column(title, items, marker):
    st.markdown(f"**{title}**")
    if items:
        st.code("\n".join(f"{marker} {item}" for item in items))
    else:
        st.caption("No changes")


def resume_comparison_page():
    st.header("Resume Comparison")
    st.caption("Choose two uploaded resumes or saved builder versions. Groq receives both texts to generate job-specific scores and a comparison report.")

    target_role = st.selectbox("Target Job Domain", list(JOB_TAXONOMY.keys()), key="comparison_target_role")
    saved_versions = _list_resume_versions()
    source_a, source_b = st.columns(2)
    with source_a:
        label_a, text_a = _render_resume_source("A", saved_versions)
    with source_b:
        label_b, text_b = _render_resume_source("B", saved_versions)

    if not text_a or not text_b:
        st.info("Choose or upload both resume versions to compare them.")
        return

    fingerprint = hashlib.sha256(f"{target_role}\0{text_a}\0{text_b}".encode("utf-8")).hexdigest()
    state = st.session_state
    if st.button("Compare with Groq AI", type="primary", key="run_groq_comparison"):
        try:
            with st.spinner("Comparing resumes with Groq AI..."):
                state["resume_comparison_result"] = _compare_with_groq(text_a, text_b, target_role)
                state["resume_comparison_fingerprint"] = fingerprint
                state["resume_comparison_error"] = None
        except Exception as exc:
            state["resume_comparison_result"] = None
            state["resume_comparison_fingerprint"] = None
            state["resume_comparison_error"] = str(exc)

    if state.get("resume_comparison_error"):
        st.error(state["resume_comparison_error"])

    comparison = state.get("resume_comparison_result")
    if state.get("resume_comparison_fingerprint") != fingerprint:
        comparison = None
        st.info("Run the Groq comparison to score the currently selected resume versions.")

    if comparison:
        st.subheader("Comparative Metrics")
        metric_fields = (
            ("ATS Score", "ats_score"),
            ("Skills Match", "skills_match"),
            ("Projects Quality", "projects_quality"),
            ("Format & Structure", "format_structure"),
        )
        metric_columns = st.columns(4)
        for column, (label, field) in zip(metric_columns, metric_fields):
            with column:
                st.markdown(f"**{label}**")
                version_columns = st.columns(2)
                with version_columns[0]:
                    st.metric("Resume A", f"{comparison['resume_a'][field]} / 100")
                with version_columns[1]:
                    delta = comparison["resume_b"][field] - comparison["resume_a"][field]
                    st.metric("Resume B", f"{comparison['resume_b'][field]} / 100", f"{delta:+}")

        st.subheader("Groq AI Comparison Report")
        st.caption(f"{label_a} vs {label_b} · Model: {comparison['model']}")
        st.write(comparison["report"])
        if comparison["highlights"]:
            st.markdown("**Key Differences**")
            for highlight in comparison["highlights"]:
                st.markdown(f"- {highlight}")

    st.subheader("Version Diff / Change Tracker")
    skills_a = _matched_role_skills(text_a, target_role)
    skills_b = _matched_role_skills(text_b, target_role)
    skill_added = sorted(skills_b - skills_a)
    skill_removed = sorted(skills_a - skills_b)
    added_column, removed_column = st.columns(2)
    with added_column:
        _render_change_column("Added role skills (in Resume B)", skill_added, "+")
    with removed_column:
        _render_change_column("Removed role skills (from Resume A)", skill_removed, "-")

    section_changes = []
    sections_a = _split_sections(text_a)
    sections_b = _split_sections(text_b)
    all_sections = list(dict.fromkeys((*sections_a.keys(), *sections_b.keys())))
    for section in all_sections:
        added, removed = _section_diff(
            sections_a.get(section, ""),
            sections_b.get(section, ""),
        )
        if added or removed:
            section_changes.append((section, added, removed))

    if section_changes:
        for section, added, removed in section_changes:
            st.markdown(f"#### {SECTION_LABELS.get(section, section.title())}")
            old_column, new_column = st.columns(2)
            with old_column:
                _render_change_column("Removed / previous text", removed, "-")
            with new_column:
                _render_change_column("Added / updated text", added, "+")
    elif not skill_added and not skill_removed:
        st.success("No text or role-skill changes were detected.")
