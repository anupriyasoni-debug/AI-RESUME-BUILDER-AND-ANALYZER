import difflib
import hashlib
import html
import json
import os
import re

from dotenv import load_dotenv

load_dotenv()

import streamlit as st

from analyzer import JOB_TAXONOMY, extract_text
from resume_builder import _list_resume_versions
from local_model import local_engine
from job_catalog import render_job_selector


SECTION_HEADINGS = {
    "contact": {"contact", "contact information", "personal details"},
    "summary": {"summary", "professional summary", "objective", "profile", "about me"},
    "education": {"education", "academic background", "academic qualifications"},
    "experience": {"experience", "work experience", "professional experience", "employment", "work history"},
    "skills": {"skills", "technical skills", "technical core skills", "core skills", "competencies"},
    "projects": {"projects", "project experience", "academic projects", "key projects"},
    "certifications": {"certifications", "certificates", "licenses"},
    "languages": {"languages"},
    "awards": {"awards", "awards and honors", "honors"},
    "achievements": {"achievements", "selected achievements", "key achievements"},
    "volunteer": {"volunteer experience", "volunteering"},
    "extracurricular": {"extracurricular activities", "extracurricular", "student activities"},
    "publications": {"publications", "talks", "patents"},
    "interests": {"interests", "professional interests"},
}

SECTION_LABELS = {
    "header": "Header / unsectioned text",
    "summary": "Summary",
    "experience": "Experience",
    "projects": "Projects",
    "education": "Education",
    "skills": "Skills",
    "certifications": "Certifications",
    "languages": "Languages",
    "awards": "Awards & Honors",
    "achievements": "Selected Achievements",
    "volunteer": "Volunteer Experience",
    "extracurricular": "Extracurricular Activities",
    "publications": "Publications",
    "interests": "Interests",
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


def _matched_skills_for_comparison(text, target_role, job_description=""):
    from analyzer import _extract_job_keywords, _skill_in_text, JOB_TAXONOMY, canonicalize_skill
    jd_skills = _extract_job_keywords(job_description) if job_description and job_description.strip() else []
    raw_targets = jd_skills if len(jd_skills) >= 3 else JOB_TAXONOMY.get(target_role, {}).get("skills", [])
    seen = set()
    target_skills = []
    for s in raw_targets:
        c = canonicalize_skill(s)
        if c not in seen:
            seen.add(c)
            target_skills.append(c)
    return {skill for skill in target_skills if _skill_in_text(skill, text)}


def _saved_resume_to_text(data):
    lines = []
    contact_items = [
        data.get("name", ""), data.get("headline", ""), data.get("email", ""), data.get("phone", ""),
        data.get("linkedin", ""), data.get("portfolio", ""), data.get("website", ""),
        data.get("github", ""), data.get("location", ""),
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
        ("Experience", data.get("experience", []), ("role", "company", "employment_type", "location", "duration", "description")),
        ("Projects", data.get("projects", []), ("title", "dates", "url", "tech", "description")),
        ("Education", data.get("education", []), ("degree", "field", "institute", "location", "year", "score", "description")),
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
    for section, heading in (
        ("languages", "Languages"), ("awards", "Awards & Honors"),
        ("achievements", "Selected Achievements"),
        ("volunteer", "Volunteer Experience"),
        ("extracurricular", "Extracurricular Activities"),
        ("publications", "Publications"), ("interests", "Interests"),
    ):
        values = data.get(section, [])
        if isinstance(values, str):
            values = [line.strip() for line in values.splitlines() if line.strip()]
        if values:
            lines.extend((heading, *(str(value) for value in values if value)))
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


def _compare_with_local(text_a, text_b, target_role, job_description="", target_source_name=""):
    return local_engine.compare_resumes(
        text_a, text_b, target_role, job_description, target_source_name=target_source_name
    )


# Backward compatibility alias
_compare_with_gemini = _compare_with_local


def _render_change_column(title, items, marker):
    st.markdown(f"**{title}**")
    if items:
        st.code("\n".join(f"{marker} {item}" for item in items))
    else:
        st.caption("No changes")


def _render_score_diagram(label_a, label_b, result_a, result_b):
    dimensions = (
        ("Overall ATS rubric", "ats_score", 100),
        ("Target-role fit", "role_score", 40),
        ("Resume structure", "section_score", 30),
        ("Achievement evidence", "impact_score", 15),
        ("Length", "length_score", 15),
    )
    rows = []
    safe_a, safe_b = html.escape(label_a), html.escape(label_b)
    for title, field, maximum in dimensions:
        score_a = max(0, min(100, round(100 * result_a[field] / maximum)))
        score_b = max(0, min(100, round(100 * result_b[field] / maximum)))
        rows.append(
            f"<div class='score-row'><div class='score-title'>{html.escape(title)}</div><div class='score-pair'>"
            f"<div class='score-entry'><div class='score-label'><span>{safe_a}</span><b>{result_a[field]}/{maximum}</b></div>"
            f"<div class='score-track'><span class='score-a' style='width:{score_a}%'></span></div></div>"
            f"<div class='score-entry'><div class='score-label'><span>{safe_b}</span><b>{result_b[field]}/{maximum}</b></div>"
            f"<div class='score-track'><span class='score-b' style='width:{score_b}%'></span></div></div></div></div>"
        )
    st.markdown(
        "<style>"
        ".compare-hero{padding:1.35rem 1.5rem;border-radius:18px;background:radial-gradient(circle at 90% 30%,rgba(139,124,255,.32),transparent 16rem),linear-gradient(120deg,#121521 0%,#1c1c38 55%,#302460 100%);color:#fff;margin:.6rem 0 1rem;border:1px solid rgba(139,124,255,.3);box-shadow:0 24px 70px rgba(55,42,140,.24)}"
        ".compare-hero .eyebrow{font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;color:#bfdbfe;font-weight:700}"
        ".compare-hero h3{margin:.4rem 0;color:#fff;line-height:1.2}.compare-hero p{margin:.35rem 0 0;color:#d9d9eb;line-height:1.55}"
        ".score-panel{padding:1.15rem 1.25rem;border:1px solid #292f40;border-radius:16px;background:rgba(20,23,32,.86);margin:.8rem 0 1.2rem;box-shadow:0 12px 30px rgba(0,0,0,.16)}"
        ".score-panel-title{display:flex;justify-content:space-between;align-items:baseline;gap:1rem;margin-bottom:1rem;color:#f3f5fa}"
        ".score-panel-title span{color:#9aa4b8;font-size:.8rem;font-weight:400}"
        ".score-row{padding:.7rem 0;border-top:1px solid #292f40}"
        ".score-title{font-size:.88rem;font-weight:700;color:#e8eaf2;margin-bottom:.55rem}"
        ".score-pair{display:grid;grid-template-columns:1fr 1fr;gap:1.1rem}"
        ".score-entry{min-width:0}.score-label{display:flex;justify-content:space-between;gap:.5rem;color:#aab3c4;font-size:.76rem;margin-bottom:.35rem}"
        ".score-label span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.score-label b{color:#f3f5fa;white-space:nowrap}"
        ".score-track{height:8px;background:#30374a;border-radius:20px;overflow:hidden}"
        ".score-track span{display:block;height:100%;border-radius:20px}.score-a{background:linear-gradient(90deg,#7568e8,#a78bfa)}.score-b{background:linear-gradient(90deg,#0f9f8b,#5eead4)}"
        ".quote-strip{padding:.9rem 1rem;border-left:3px solid #8b7cff;background:rgba(55,45,105,.36);color:#d6d0ff;border-radius:0 12px 12px 0;margin:.6rem 0;line-height:1.55}"
        "@media(max-width:650px){.score-pair{grid-template-columns:1fr;gap:.65rem}.score-panel-title{display:block}.score-panel-title span{display:block;margin-top:.3rem}}"
        "</style><div class='score-panel'><div class='score-panel-title'><b>Score comparison</b><span>Each bar is scaled to its category maximum.</span></div>"
        + "".join(rows)
        + "</div>",
        unsafe_allow_html=True,
    )


def resume_comparison_page():
    st.markdown(
        "<div class='compare-hero'><div class='eyebrow'>Evidence-based side-by-side review</div>"
        "<h3>Which resume fits this role better?</h3>"
        "<p>Compare target-skill coverage, structure, impact evidence, and length. You’ll see what drove the result and what each version still needs.</p></div>",
        unsafe_allow_html=True,
    )
    st.caption("Choose two resumes and a target role. The offline evaluator uses explicit keywords and a scoring rubric; it does not make hiring decisions or generate text.")

    target_role = st.selectbox("Target Job Domain Preset", list(JOB_TAXONOMY.keys()), key="comparison_target_role")
    job_description, jd_source_label = render_job_selector(key_prefix="comparison")
    saved_versions = _list_resume_versions()
    source_a, source_b = st.columns(2, gap="large")
    with source_a:
        with st.container(border=True):
            st.markdown("#### Resume A")
            st.caption("Choose the first version to review.")
            label_a, text_a = _render_resume_source("A", saved_versions)
    with source_b:
        with st.container(border=True):
            st.markdown("#### Resume B")
            st.caption("Choose the version you want to compare against A.")
            label_b, text_b = _render_resume_source("B", saved_versions)

    if not text_a or not text_b:
        st.info("Choose or upload both resume versions to compare them.")
        return

    fingerprint = hashlib.sha256(
        f"comparison-v2\0{target_role}\0{job_description}\0{jd_source_label}\0{text_a}\0{text_b}".encode("utf-8")
    ).hexdigest()
    state = st.session_state
    if st.button("Compare resumes", type="primary", use_container_width=True, key="run_local_comparison"):
        try:
            with st.spinner("Analyzing and comparing resumes locally..."):
                state["resume_comparison_result"] = _compare_with_local(
                    text_a, text_b, target_role, job_description, target_source_name=jd_source_label
                )
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
        st.info("Run the local comparison to score the currently selected resume versions.")

    if comparison:
        res_a = comparison["resume_a"]
        res_b = comparison["resume_b"]

        if comparison.get("jd_fallback_notice"):
            st.warning(comparison["jd_fallback_notice"])

        st.caption(
            f"**Evaluation Target:** {comparison.get('role_fit_source', target_role)} · "
            "Local heuristic keyword and text alignment (does not guarantee employer screening results or semantic understanding)."
        )

        winner = comparison.get("winner", "Close match")
        if winner == "Close match":
            verdict_title = "These resumes are tied on the measured signals"
            verdict_detail = "Review the skill evidence and job description directly; the available rubric does not give one a clear lead."
        else:
            winner_label = label_a if winner == "Resume A" else label_b
            verdict_title = f"Stronger measured match: {winner_label}"
            verdict_detail = "This is a rubric-based recommendation for the selected role, not a prediction of hiring outcome."
        st.markdown(
            f"<div class='compare-hero'><div class='eyebrow'>Role-fit recommendation</div>"
            f"<h3>{html.escape(verdict_title)}</h3><p>{html.escape(verdict_detail)}</p></div>",
            unsafe_allow_html=True,
        )
        reason_column, quote_column = st.columns([1.5, 1])
        with reason_column:
            st.markdown("**Why this version leads**" if winner != "Close match" else "**What the tie means**")
            for reason in comparison.get("recommendation_reasons", []):
                st.markdown(f"- {reason}")
        with quote_column:
            st.markdown(
                "<div class='quote-strip'>A stronger resume makes relevant evidence easy to find and verify.</div>",
                unsafe_allow_html=True,
            )

        _render_score_diagram(label_a, label_b, res_a, res_b)

        st.subheader("Comparative Metrics")
        metric_fields = (
            ("ATS Score", "ats_score"),
            ("Role Fit (40 pt scale)", "role_score"),
            ("Sections (30 pt scale)", "section_score"),
            ("Impact (15 pt scale)", "impact_score"),
            ("Length (15 pt scale)", "length_score"),
        )
        metrics_a, metrics_b = st.columns(2)
        for column, label, result, other in (
            (metrics_a, label_a, res_a, res_b),
            (metrics_b, label_b, res_b, res_a),
        ):
            with column:
                with st.container(border=True):
                    st.markdown(f"**{label}**")
                    st.metric("Overall ATS Score", f"{result['ats_score']} / 100", f"{result['ats_score'] - other['ats_score']:+} vs other")
                    for component_pair in (metric_fields[1:3], metric_fields[3:5]):
                        component_columns = st.columns(2)
                        for metric_column, (metric_label, field) in zip(component_columns, component_pair):
                            with metric_column:
                                maximum = 40 if field == "role_score" else 30 if field == "section_score" else 15
                                st.metric(metric_label, f"{result[field]} / {maximum}")

        st.caption(
            f"**Component Breakdown:**\n"
            f"- **{label_a}:** Role Fit: **{res_a['role_score']}/40** + Sections: **{res_a['section_score']}/30** + "
            f"Impact: **{res_a['impact_score']}/15** + Length: **{res_a['length_score']}/15** = **{res_a['ats_score']}/100**\n"
            f"- **{label_b}:** Role Fit: **{res_b['role_score']}/40** + Sections: **{res_b['section_score']}/30** + "
            f"Impact: **{res_b['impact_score']}/15** + Length: **{res_b['length_score']}/15** = **{res_b['ats_score']}/100**"
        )

        st.subheader("Target Skills Coverage")
        cov_a, cov_b = st.columns(2)
        with cov_a:
            st.markdown(f"**{label_a} Matched Skills ({len(res_a['matched_skills'])})**")
            st.write(", ".join(f"`{s}`" for s in res_a["matched_skills"]) or "None matched")
            st.markdown(f"**{label_a} Missing Skills ({len(res_a['missing_skills'])})**")
            st.write(", ".join(f"`{s}`" for s in res_a["missing_skills"]) or "All target skills detected!")
        with cov_b:
            st.markdown(f"**{label_b} Matched Skills ({len(res_b['matched_skills'])})**")
            st.write(", ".join(f"`{s}`" for s in res_b["matched_skills"]) or "None matched")
            st.markdown(f"**{label_b} Missing Skills ({len(res_b['missing_skills'])})**")
            st.write(", ".join(f"`{s}`" for s in res_b["missing_skills"]) or "All target skills detected!")

        st.subheader("How to read this comparison")
        st.caption(f"{label_a} vs {label_b} · Evaluator: {comparison['model']}")
        st.caption("A skill counts as matched when its wording is detected in the resume text. Similar meanings, evidence quality, seniority, and employer preferences may not be captured.")
        with st.expander("Show scoring details"):
            st.write(comparison["report"])
        if comparison["highlights"]:
            st.markdown("**Key Differences**")
            for highlight in comparison["highlights"]:
                st.markdown(f"- {highlight}")
        feedback_a, feedback_b = st.columns(2)
        with feedback_a:
            st.markdown(f"**Recommendations for {label_a}**")
            for suggestion in res_a["feedback"]:
                st.markdown(f"- {suggestion}")
        with feedback_b:
            st.markdown(f"**Recommendations for {label_b}**")
            for suggestion in res_b["feedback"]:
                st.markdown(f"- {suggestion}")

    st.subheader("Version Diff / Change Tracker")
    from analyzer import _extract_job_keywords
    if comparison:
        skills_a = set(comparison["resume_a"]["matched_skills"])
        skills_b = set(comparison["resume_b"]["matched_skills"])
    else:
        skills_a = _matched_skills_for_comparison(text_a, target_role, job_description)
        skills_b = _matched_skills_for_comparison(text_b, target_role, job_description)

    skill_added = sorted(skills_b - skills_a)
    skill_removed = sorted(skills_a - skills_b)
    added_column, removed_column = st.columns(2)
    is_jd = bool(job_description.strip() and len(_extract_job_keywords(job_description)) >= 3)
    target_desc = "JD skills" if is_jd else "preset skills"
    with added_column:
        _render_change_column(f"Added {target_desc} (in {label_b})", skill_added, "+")
    with removed_column:
        _render_change_column(f"Missing / removed {target_desc} (from {label_a})", skill_removed, "-")

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
        st.success("No text or target skill changes were detected.")
