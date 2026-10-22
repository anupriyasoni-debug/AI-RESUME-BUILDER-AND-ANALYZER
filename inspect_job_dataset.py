"""Read-only inspection of the LinkedIn jobs CSV archive used by the resume analyzer.

Reads CSVs as text, preserves job IDs, and prints join/data-quality statistics.
Does not write to the dataset or project data/model directories.
"""
from __future__ import annotations

import argparse
import csv
import os
import re
from collections import Counter, defaultdict
from pathlib import Path


def open_csv(path: Path):
    return path.open("r", encoding="utf-8-sig", errors="replace", newline="")


def require_columns(reader: csv.DictReader, path: Path, required: set[str]) -> None:
    columns = {str(name).strip() for name in (reader.fieldnames or [])}
    missing = sorted(required - columns)
    if missing:
        raise ValueError(f"{path} is missing required columns: {', '.join(missing)}")


def percent(part: int, whole: int) -> str:
    return f"{(100 * part / whole):.1f}%" if whole else "n/a"


def inspect(root: Path) -> None:
    postings_path = root / "postings.csv"
    job_skills_path = root / "jobs" / "job_skills.csv"
    skills_path = root / "mappings" / "skills.csv"
    for path in (postings_path, job_skills_path, skills_path):
        if not path.is_file():
            raise FileNotFoundError(f"Required CSV not found: {path}")

    csv.field_size_limit(10 * 1024 * 1024)

    skill_names: dict[str, str] = {}
    with open_csv(skills_path) as handle:
        reader = csv.DictReader(handle)
        require_columns(reader, skills_path, {"skill_abr", "skill_name"})
        for row in reader:
            code = (row.get("skill_abr") or "").strip()
            name = (row.get("skill_name") or "").strip()
            if code and name:
                skill_names[code] = name

    skills_by_job: dict[str, set[str]] = defaultdict(set)
    labels_per_job: Counter[str] = Counter()
    unmapped_codes: Counter[str] = Counter()
    association_rows = 0
    with open_csv(job_skills_path) as handle:
        reader = csv.DictReader(handle)
        require_columns(reader, job_skills_path, {"job_id", "skill_abr"})
        for row in reader:
            association_rows += 1
            job_id = (row.get("job_id") or "").strip()
            code = (row.get("skill_abr") or "").strip()
            if not job_id or not code:
                continue
            name = skill_names.get(code)
            if name:
                skills_by_job[job_id].add(name)
                labels_per_job[name] += 1
            else:
                unmapped_codes[code] += 1

    posting_rows = 0
    nonempty_ids = 0
    nonempty_titles = 0
    nonempty_descriptions = 0
    nonempty_skills_desc = 0
    scientific_id_rows = 0
    jobs_with_skill_links = 0
    mapped_label_links = 0
    seen_ids: set[str] = set()
    duplicate_id_rows = 0
    samples: list[tuple[str, str, list[str], int, bool]] = []

    with open_csv(postings_path) as handle:
        reader = csv.DictReader(handle)
        require_columns(reader, postings_path, {"job_id", "title", "description"})
        has_skills_desc = "skills_desc" in (reader.fieldnames or [])
        for row in reader:
            posting_rows += 1
            job_id = (row.get("job_id") or "").strip()
            title = (row.get("title") or "").strip()
            description = (row.get("description") or "").strip()
            skills_desc = (row.get("skills_desc") or "").strip() if has_skills_desc else ""
            nonempty_ids += bool(job_id)
            nonempty_titles += bool(title)
            nonempty_descriptions += bool(description)
            nonempty_skills_desc += bool(skills_desc)
            scientific_id_rows += bool(re.search(r"\d(?:\.\d+)?e[+-]?\d+", job_id, re.I))
            if job_id:
                if job_id in seen_ids:
                    duplicate_id_rows += 1
                else:
                    seen_ids.add(job_id)
            labels = sorted(skills_by_job.get(job_id, set())) if job_id else []
            if labels:
                jobs_with_skill_links += 1
                mapped_label_links += len(labels)
                if len(samples) < 5:
                    samples.append((job_id, title, labels, len(description), bool(skills_desc)))

    print(f"Dataset folder: {root}")
    print("Read-only inspection: no source CSVs or project files were changed by this script.")
    print(f"postings.csv size: {postings_path.stat().st_size:,} bytes")
    print(f"Postings rows: {posting_rows:,}")
    print(f"Rows with job_id/title/description: {nonempty_ids:,} / {nonempty_titles:,} / {nonempty_descriptions:,}")
    print(f"Rows with skills_desc: {nonempty_skills_desc:,} (column present: {has_skills_desc})")
    print(f"Duplicate posting-ID rows after first occurrence: {duplicate_id_rows:,}")
    print(f"IDs formatted like scientific notation in raw CSV: {scientific_id_rows:,}")
    print(f"Skill mapping entries: {len(skill_names):,}")
    print(f"Job-skill association rows: {association_rows:,}")
    print(f"Distinct jobs with at least one mapped skill: {len(skills_by_job):,}")
    print(f"Distinct mapped skill labels: {len(labels_per_job):,}")
    print(f"Posting rows with mapped skills: {jobs_with_skill_links:,} ({percent(jobs_with_skill_links, posting_rows)})")
    print(f"Mapped skill associations for matched posting rows: {mapped_label_links:,}")
    print(f"Unmapped skill codes (association rows): {sum(unmapped_codes.values()):,}")
    if unmapped_codes:
        print("Most common unmapped codes: " + ", ".join(f"{code} ({count:,})" for code, count in unmapped_codes.most_common(10)))
    print("Most common mapped skill labels: " + (", ".join(f"{name} ({count:,})" for name, count in labels_per_job.most_common(12)) or "none"))
    print("Sample joined jobs (ID | title | mapped labels | description chars | skills_desc present):")
    for job_id, title, labels, description_chars, has_skills_desc in samples:
        label_text = ", ".join(labels[:8]) + (", …" if len(labels) > 8 else "")
        print(f"  {job_id} | {title[:70]} | {label_text} | {description_chars} | {has_skills_desc}")
    if not samples:
        print("  No posting rows joined to mapped skills; verify IDs and source CSV integrity.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True, help="Extracted archive folder containing postings.csv, jobs/, mappings/")
    args = parser.parse_args()
    inspect(args.data_dir.expanduser().resolve())


if __name__ == "__main__":
    main()
