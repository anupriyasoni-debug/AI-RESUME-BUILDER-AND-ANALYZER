"""Offline Job Catalog Preparation Script.

Reads the downloaded LinkedIn job postings dataset archive:
  - postings.csv
  - jobs/job_skills.csv
  - mappings/skills.csv

Processes postings in memory-efficient chunks, preserves job IDs strictly as text,
joins mapped job-function/skill labels, and outputs a high-performance, compact
SQLite database under data/processed/job_catalog.db.

Never modifies original archive files or resumes.db.
"""
from __future__ import annotations

import argparse
import csv
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_ARCHIVE_DIR = Path(r"C:\Users\HP\OneDrive\Desktop\archive")
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
DEFAULT_DB_NAME = "job_catalog.db"


def increase_csv_field_size_limit() -> None:
    """Increase CSV field size limit safely across operating systems."""
    limit = 10 * 1024 * 1024
    while True:
        try:
            csv.field_size_limit(limit)
            break
        except OverflowError:
            limit //= 2


def load_job_function_mappings(archive_dir: Path) -> Dict[str, str]:
    """Loads mappings/skills.csv into a dictionary: skill_abr -> skill_name."""
    skills_csv = archive_dir / "mappings" / "skills.csv"
    if not skills_csv.is_file():
        raise FileNotFoundError(f"Missing required mapping file: {skills_csv}")

    code_to_name: Dict[str, str] = {}
    with skills_csv.open("r", encoding="utf-8-sig", errors="replace", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = (row.get("skill_abr") or "").strip()
            name = (row.get("skill_name") or "").strip()
            if code and name:
                code_to_name[code] = name
    return code_to_name


def load_job_skills(archive_dir: Path, code_to_name: Dict[str, str]) -> Dict[str, List[str]]:
    """Loads jobs/job_skills.csv while preserving job_id as text string."""
    job_skills_csv = archive_dir / "jobs" / "job_skills.csv"
    if not job_skills_csv.is_file():
        raise FileNotFoundError(f"Missing required job skills file: {job_skills_csv}")

    skills_by_job: Dict[str, Set[str]] = {}
    with job_skills_csv.open("r", encoding="utf-8-sig", errors="replace", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            job_id = str(row.get("job_id") or "").strip()
            code = (row.get("skill_abr") or "").strip()
            if not job_id or not code:
                continue
            name = code_to_name.get(code, code)
            skills_by_job.setdefault(job_id, set()).add(name)

    return {jid: sorted(names) for jid, names in skills_by_job.items()}


def init_database(db_path: Path) -> sqlite3.Connection:
    """Initializes SQLite database with indexed jobs table."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db_path))
    con.execute("PRAGMA journal_mode = WAL;")
    con.execute("PRAGMA synchronous = NORMAL;")

    con.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            company_name TEXT,
            location TEXT,
            work_type TEXT,
            experience_level TEXT,
            job_functions TEXT,
            skills_desc TEXT,
            description TEXT NOT NULL
        );
        """
    )
    con.execute("CREATE INDEX IF NOT EXISTS idx_jobs_title ON jobs(title);")
    con.execute("CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs(location);")
    con.execute("CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company_name);")

    con.execute(
        """
        CREATE TABLE IF NOT EXISTS catalog_metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        """
    )
    con.commit()
    return con


def prepare_catalog(
    archive_dir: Path,
    output_dir: Path,
    batch_size: int = 5000,
    limit: Optional[int] = None,
) -> Path:
    """Reads archive CSVs, joins job functions, and writes to SQLite catalog."""
    start_time = time.time()
    increase_csv_field_size_limit()

    postings_csv = archive_dir / "postings.csv"
    if not postings_csv.is_file():
        raise FileNotFoundError(f"Missing postings.csv at: {postings_csv}")

    print(f"Loading skill mappings from {archive_dir}...")
    code_to_name = load_job_function_mappings(archive_dir)
    print(f"Loaded {len(code_to_name)} skill mapping codes.")

    print("Loading job-skill associations...")
    skills_by_job = load_job_skills(archive_dir, code_to_name)
    print(f"Loaded skills for {len(skills_by_job):,} distinct jobs.")

    db_path = output_dir / DEFAULT_DB_NAME
    con = init_database(db_path)

    insert_sql = """
        INSERT OR REPLACE INTO jobs (
            job_id, title, company_name, location, work_type,
            experience_level, job_functions, skills_desc, description
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """

    total_inserted = 0
    total_skipped = 0
    batch: List[tuple] = []

    print(f"Streaming postings from {postings_csv} (batch size: {batch_size:,})...")
    with postings_csv.open("r", encoding="utf-8-sig", errors="replace", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            job_id = str(row.get("job_id") or "").strip()
            title = str(row.get("title") or "").strip()
            description = str(row.get("description") or "").strip()

            if not job_id or not title or not description:
                total_skipped += 1
                continue

            company = str(row.get("company_name") or "").strip()
            location = str(row.get("location") or "").strip()
            work_type = str(row.get("formatted_work_type") or row.get("work_type") or "").strip()
            exp_level = str(row.get("formatted_experience_level") or "").strip()
            skills_desc = str(row.get("skills_desc") or "").strip()

            job_functions = ", ".join(skills_by_job.get(job_id, []))

            batch.append((
                job_id,
                title,
                company,
                location,
                work_type,
                exp_level,
                job_functions,
                skills_desc,
                description,
            ))

            if len(batch) >= batch_size:
                con.executemany(insert_sql, batch)
                con.commit()
                total_inserted += len(batch)
                print(f"  Inserted {total_inserted:,} postings...", end="\r")
                batch = []

            if limit is not None and total_inserted + len(batch) >= limit:
                break

        if batch:
            con.executemany(insert_sql, batch)
            con.commit()
            total_inserted += len(batch)

    # Write metadata
    now_iso = datetime.now(timezone.utc).isoformat()
    meta = [
        ("total_postings", str(total_inserted)),
        ("created_at", now_iso),
        ("source", "LinkedIn Job Postings Dataset Archive"),
        ("notes", "Archived dataset snapshot, not current/live vacancies"),
        ("archive_dir", str(archive_dir)),
    ]
    con.executemany("INSERT OR REPLACE INTO catalog_metadata (key, value) VALUES (?, ?);", meta)
    con.commit()
    con.close()

    elapsed = time.time() - start_time
    db_size_mb = db_path.stat().st_size / (1024 * 1024)
    print(f"\nCatalog preparation completed successfully in {elapsed:.1f}s!")
    print(f"Output database: {db_path} ({db_size_mb:.1f} MB)")
    print(f"Total postings saved: {total_inserted:,} (skipped invalid/empty: {total_skipped:,})")

    return db_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_ARCHIVE_DIR,
        help="Path to folder containing postings.csv, jobs/, mappings/",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Destination directory for processed job_catalog.db",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5000,
        help="Chunk size for batch database insertion (default: 5000)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional maximum number of postings to process (for quick testing)",
    )
    args = parser.parse_args()

    data_dir = args.data_dir.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()

    if not data_dir.is_dir():
        print(f"Error: Archive directory not found at: {data_dir}", file=sys.stderr)
        sys.exit(1)

    prepare_catalog(
        archive_dir=data_dir,
        output_dir=output_dir,
        batch_size=args.batch_size,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
