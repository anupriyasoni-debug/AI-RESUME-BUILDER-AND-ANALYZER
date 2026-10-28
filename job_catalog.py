"""Offline Job Catalog Query Service.

Provides fast, indexed access to the prepared offline job catalog database
(data/processed/job_catalog.db) without loading the 517 MB raw CSV into memory.

Supports search and filtering by job title and location, single-posting retrieval
for resume analysis / comparison, and graceful fallback when the catalog has
not yet been generated.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_CATALOG_DB = PROJECT_ROOT / "data" / "processed" / "job_catalog.db"
SNAPSHOT_LABEL = "Archived Dataset Snapshot (Historical LinkedIn Postings — Not Current/Live Vacancies)"


def get_default_catalog_path() -> Path:
    """Returns default path to the prepared SQLite catalog."""
    return DEFAULT_CATALOG_DB


def is_catalog_available(db_path: Optional[Path] = None) -> bool:
    """Checks whether the offline catalog database exists and is populated."""
    path = db_path or get_default_catalog_path()
    if not path.is_file():
        return False
    try:
        con = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
        cur = con.cursor()
        count = cur.execute("SELECT count(*) FROM jobs;").fetchone()[0]
        con.close()
        return count > 0
    except Exception:
        return False


def get_catalog_metadata(db_path: Optional[Path] = None) -> Dict[str, str]:
    """Retrieves catalog metadata (postings count, snapshot date, source)."""
    path = db_path or get_default_catalog_path()
    meta = {
        "is_available": "false",
        "total_postings": "0",
        "snapshot_label": SNAPSHOT_LABEL,
        "db_path": str(path),
    }
    if not path.is_file():
        return meta

    try:
        con = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
        cur = con.cursor()
        for k, v in cur.execute("SELECT key, value FROM catalog_metadata;"):
            meta[k] = v
        total = cur.execute("SELECT count(*) FROM jobs;").fetchone()[0]
        meta["total_postings"] = str(total)
        meta["is_available"] = "true"
        con.close()
    except Exception:
        pass

    return meta


def search_jobs(
    title_query: str = "",
    location_query: str = "",
    function_query: str = "",
    limit: int = 50,
    offset: int = 0,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Searches jobs by title, location, and optional job-function substring.
    Uses parameterized SQL queries over indexed fields without loading full descriptions.
    """
    path = db_path or get_default_catalog_path()
    if not path.is_file():
        return []

    conditions = []
    params: List[Any] = []

    title_clean = title_query.strip()
    if title_clean:
        for word in title_clean.split():
            conditions.append("title LIKE ?")
            params.append(f"%{word}%")

    loc_clean = location_query.strip()
    if loc_clean:
        for word in loc_clean.split():
            conditions.append("location LIKE ?")
            params.append(f"%{word}%")

    func_clean = function_query.strip()
    if func_clean:
        conditions.append("job_functions LIKE ?")
        params.append(f"%{func_clean}%")

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"""
        SELECT
            job_id,
            title,
            company_name,
            location,
            work_type,
            experience_level,
            job_functions,
            substr(description, 1, 280) AS desc_snippet
        FROM jobs
        {where_clause}
        ORDER BY title ASC
        LIMIT ? OFFSET ?;
    """
    params.extend([max(1, min(limit, 200)), max(0, offset)])

    try:
        con = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        rows = cur.execute(sql, params).fetchall()
        results = [dict(row) for row in rows]
        con.close()
        return results
    except Exception:
        return []


def get_job_by_id(job_id: str, db_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """
    Fetches full record (including complete job description) by job_id.
    Preserves job_id as string.
    """
    if not job_id:
        return None
    path = db_path or get_default_catalog_path()
    if not path.is_file():
        return None

    sql = """
        SELECT
            job_id,
            title,
            company_name,
            location,
            work_type,
            experience_level,
            job_functions,
            skills_desc,
            description
        FROM jobs
        WHERE job_id = ?
        LIMIT 1;
    """
    try:
        con = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        row = cur.execute(sql, (str(job_id).strip(),)).fetchone()
        con.close()
        return dict(row) if row else None
    except Exception:
        return None


def format_job_display_label(job: Dict[str, Any]) -> str:
    """Creates a user-friendly label for selectbox options."""
    title = job.get("title") or "Untitled Position"
    company = job.get("company_name") or "Unknown Company"
    location = job.get("location") or "Location Unspecified"
    job_id = job.get("job_id") or ""
    return f"{title} · {company} ({location}) [ID: {job_id}]"


def get_setup_instructions() -> str:
    """Returns markdown instructions on how to generate the offline catalog."""
    return (
        "**Offline Job Catalog Not Found**\n\n"
        "The prepared catalog database was not found at `data/processed/job_catalog.db`.\n\n"
        "To generate the offline catalog from your downloaded dataset archive, run:\n"
        "```powershell\n"
        "python prepare_job_catalog.py --data-dir \"C:\\Users\\HP\\OneDrive\\Desktop\\archive\"\n"
        "```\n"
        "This processes `postings.csv`, `jobs/job_skills.csv`, and `mappings/skills.csv` in chunks "
        "and saves an indexed, compact database under `data/processed/`.\n\n"
        "*You can also paste any target job description manually.*"
    )


def render_job_selector(key_prefix: str = "main") -> Tuple[str, str]:
    """
    Renders Streamlit UI for selecting a Job Description:
    either manual paste or searching the offline catalog snapshot.

    Returns:
        (job_description_text, source_label)
    """
    import streamlit as st

    catalog_ready = is_catalog_available()

    options = ["Paste Description Manually"]
    if catalog_ready:
        options.append("Search Offline Job Catalog (Archived Snapshot)")

    mode = st.radio(
        "Job Description Source",
        options,
        horizontal=True,
        key=f"{key_prefix}_jd_mode",
    )

    if mode == "Paste Description Manually":
        pasted = st.text_area(
            "Target Job Description (optional - overrides preset when provided)",
            placeholder="Paste the target role's job description to compare resume keywords and skills.",
            height=130,
            key=f"{key_prefix}_pasted_jd",
        )
        label = "Pasted Job Description" if pasted.strip() else ""
        return pasted, label

    else:
        st.caption(
            "ℹ️ **Archived Dataset Snapshot:** Listings are from the historical LinkedIn job postings archive. "
            "These represent an offline research snapshot, not current or live vacancies."
        )

        col1, col2 = st.columns(2)
        with col1:
            title_q = st.text_input(
                "Filter by Job Title",
                placeholder="e.g. Data Scientist, DevOps, Marketing",
                key=f"{key_prefix}_title_filter",
            )
        with col2:
            loc_q = st.text_input(
                "Filter by Location",
                placeholder="e.g. Remote, New York, San Francisco",
                key=f"{key_prefix}_loc_filter",
            )

        results = search_jobs(title_query=title_q, location_query=loc_q, limit=50)

        if not results:
            st.warning("No catalog postings matched your filter criteria. Try broader keywords or paste manually.")
            pasted = st.text_area(
                "Or Paste Target Job Description Manually",
                placeholder="Paste your target job description here...",
                height=110,
                key=f"{key_prefix}_empty_cat_pasted_jd",
            )
            return pasted, "Pasted Job Description" if pasted.strip() else ""

        job_ids = [r["job_id"] for r in results]
        jobs_by_id = {r["job_id"]: r for r in results}

        selected_id = st.selectbox(
            f"Select Job Posting ({len(results)} matching listings shown)",
            job_ids,
            format_func=lambda jid: format_job_display_label(jobs_by_id[jid]),
            key=f"{key_prefix}_selected_job_id",
        )

        full_job = get_job_by_id(selected_id) or jobs_by_id[selected_id]
        job_title = full_job.get("title", "Untitled")
        company = full_job.get("company_name", "Company")
        location = full_job.get("location", "Location Unspecified")
        job_funcs = full_job.get("job_functions", "")

        meta_str = f"**Selected:** {job_title} · **{company}** ({location})"
        if job_funcs:
            meta_str += f" · *Job Functions: {job_funcs}*"
        st.markdown(meta_str)

        with st.expander("Preview Selected Catalog Job Description", expanded=False):
            st.write(full_job.get("description", ""))

        source_label = f"Catalog Listing: {job_title} @ {company} (Archived Snapshot ID: {selected_id})"
        return full_job.get("description", ""), source_label
