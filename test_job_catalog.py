"""Unit and regression tests for offline job catalog preparation, search, and integration.

Verifies:
1. CSV joins and strict text job_id preservation.
2. Fast indexed search by title and location.
3. Graceful handling of missing catalog with setup instructions.
4. Manual description entry preservation and clear source labeling.
5. Consistent comparison scoring when evaluating against a catalog posting.
"""
from __future__ import annotations

import csv
import sqlite3
import tempfile
import unittest
from pathlib import Path

import analyzer
import job_catalog
from local_model import local_engine
from prepare_job_catalog import (
    init_database,
    load_job_function_mappings,
    load_job_skills,
    prepare_catalog,
)


class JobCatalogPreparationAndJoinTests(unittest.TestCase):
    """Tests for CSV parsing, join logic, and text ID integrity."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.archive_dir = Path(self.temp_dir.name) / "archive"
        self.output_dir = Path(self.temp_dir.name) / "processed"
        self.archive_dir.mkdir(parents=True)
        (self.archive_dir / "jobs").mkdir(parents=True)
        (self.archive_dir / "mappings").mkdir(parents=True)

        # 1. Create synthetic mappings/skills.csv
        skills_csv = self.archive_dir / "mappings" / "skills.csv"
        with skills_csv.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["skill_abr", "skill_name"])
            writer.writerow(["IT", "Information Technology"])
            writer.writerow(["ENG", "Engineering"])
            writer.writerow(["MRKT", "Marketing"])

        # 2. Create synthetic jobs/job_skills.csv with leading-zero and large text IDs
        job_skills_csv = self.archive_dir / "jobs" / "job_skills.csv"
        with job_skills_csv.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["job_id", "skill_abr"])
            writer.writerow(["0010099", "IT"])
            writer.writerow(["0010099", "ENG"])
            writer.writerow(["3905213935", "MRKT"])

        # 3. Create synthetic postings.csv
        postings_csv = self.archive_dir / "postings.csv"
        with postings_csv.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "job_id", "title", "company_name", "location", "description",
                "formatted_work_type", "formatted_experience_level", "skills_desc"
            ])
            writer.writerow([
                "0010099", "Cloud DevOps Specialist", "Apex Cloud Labs", "Remote",
                "Seeking an engineer with kubernetes, docker, terraform, aws, and ci/cd experience.",
                "Full-time", "Mid-Senior level", "Kubernetes, Docker, Cloud"
            ])
            writer.writerow([
                "3905213935", "Digital Marketing Coordinator", "Bright Media", "New York, NY",
                "Lead social media marketing, content marketing, and email campaigns using seo.",
                "Contract", "Entry level", "SEO, Social Media"
            ])

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_text_job_id_and_join_integrity(self):
        """Verify job_id is strictly preserved as text and skills are joined correctly."""
        db_path = prepare_catalog(
            archive_dir=self.archive_dir,
            output_dir=self.output_dir,
            batch_size=10,
        )
        self.assertTrue(db_path.is_file())

        con = sqlite3.connect(str(db_path))
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        # Verify job with leading zeros is preserved as '0010099', not 10099
        row1 = cur.execute("SELECT * FROM jobs WHERE job_id = ?", ("0010099",)).fetchone()
        self.assertIsNotNone(row1)
        self.assertEqual(row1["job_id"], "0010099")
        self.assertIsInstance(row1["job_id"], str)
        self.assertEqual(row1["title"], "Cloud DevOps Specialist")
        self.assertEqual(row1["company_name"], "Apex Cloud Labs")
        # Joined labels should be "Engineering, Information Technology" (alphabetical)
        self.assertEqual(row1["job_functions"], "Engineering, Information Technology")

        # Verify large 10-digit ID is preserved as text
        row2 = cur.execute("SELECT * FROM jobs WHERE job_id = ?", ("3905213935",)).fetchone()
        self.assertIsNotNone(row2)
        self.assertEqual(row2["job_id"], "3905213935")
        self.assertIsInstance(row2["job_id"], str)
        self.assertEqual(row2["job_functions"], "Marketing")

        con.close()


class JobCatalogSearchAndRetrievalTests(unittest.TestCase):
    """Tests searching, filtering, and retrieval against the active prepared catalog."""

    def test_catalog_is_available_and_returns_metadata(self):
        """Verify the prepared database exists, is valid, and provides metadata."""
        self.assertTrue(job_catalog.is_catalog_available())
        meta = job_catalog.get_catalog_metadata()
        self.assertEqual(meta["is_available"], "true")
        self.assertGreaterEqual(int(meta["total_postings"]), 1000)
        self.assertIn("Historical LinkedIn", meta["snapshot_label"])

    def test_search_by_title_and_location(self):
        """Verify searching jobs by title keywords and location returns structured matches."""
        results = job_catalog.search_jobs(title_query="Data Scientist", limit=10)
        self.assertGreater(len(results), 0)
        first = results[0]
        self.assertIn("job_id", first)
        self.assertIn("title", first)
        self.assertIn("company_name", first)
        self.assertIn("location", first)
        self.assertIn("desc_snippet", first)
        self.assertIn("data", first["title"].lower())
        self.assertIn("scientist", first["title"].lower())

        # Test location filter
        results_loc = job_catalog.search_jobs(title_query="Engineer", location_query="CA", limit=10)
        for r in results_loc:
            self.assertIn("engineer", r["title"].lower())

    def test_get_job_by_id_returns_full_description(self):
        """Verify single posting lookup returns complete job description."""
        results = job_catalog.search_jobs(title_query="Engineer", limit=1)
        self.assertGreater(len(results), 0)
        jid = results[0]["job_id"]
        job = job_catalog.get_job_by_id(jid)
        self.assertIsNotNone(job)
        self.assertEqual(job["job_id"], jid)
        self.assertGreater(len(job["description"]), 50)

    def test_missing_catalog_graceful_fallback(self):
        """Verify searching a non-existent database returns empty list and clean instructions without error."""
        fake_path = Path("non_existent_dir") / "missing_catalog.db"
        self.assertFalse(job_catalog.is_catalog_available(fake_path))
        self.assertEqual(job_catalog.search_jobs("Python", db_path=fake_path), [])
        self.assertIsNone(job_catalog.get_job_by_id("123", db_path=fake_path))
        instructions = job_catalog.get_setup_instructions()
        self.assertIn("prepare_job_catalog.py", instructions)


class CatalogResumeEvaluationIntegrationTests(unittest.TestCase):
    """Tests evaluating resumes against catalog postings and comparing them consistently."""

    def setUp(self):
        self.resume_devops = (
            "Taylor Vance\ntaylor@example.com | 555-0155\n\n"
            "Summary\nDevOps engineer specialized in container orchestration and infrastructure as code.\n\n"
            "Experience\n"
            "- Orchestrated multi-region container deployments using kubernetes and docker.\n"
            "- Managed AWS infrastructure with terraform and automated ci/cd pipelines.\n"
            "- Reduced deployment lead time by 30% through automated canary releases.\n\n"
            "Skills\nkubernetes, docker, terraform, aws, ci/cd, linux, python.\n\n"
            "Education\nB.S. in Computer Science.\n\n"
            "Projects\n- Built GitOps delivery pipeline on AWS EKS.\n"
        )

        self.resume_marketing = (
            "Jordan Casey\njordan@example.com | 555-0144\n\n"
            "Summary\nMarketing coordinator with experience in content strategy and analytics.\n\n"
            "Experience\n"
            "- Planned social media marketing and brand engagement campaigns.\n"
            "- Tracked website organic traffic using google analytics and seo.\n\n"
            "Skills\nseo, social media marketing, content marketing, copywriting.\n\n"
            "Education\nB.A. in Communications.\n\n"
            "Projects\n- Directed multi-channel campaign driving 20% engagement lift.\n"
        )

    def test_catalog_posting_evaluates_resume_and_sets_source_label(self):
        """Verify resume analysis against a catalog posting accurately sets role_fit_source."""
        catalog_desc = (
            "Senior Cloud Engineer. Must have strong hands-on experience with "
            "kubernetes, docker, terraform, aws, and ci/cd automation."
        )
        catalog_source = "Catalog Listing: Senior Cloud Engineer @ TechCorp (Archived Snapshot ID: 1001)"

        res = analyzer.analyze_resume(
            self.resume_devops,
            target_role="Digital Marketing Manager",
            pasted_jd=catalog_desc,
            target_source_name=catalog_source,
        )
        self.assertTrue(res["using_jd_target"])
        self.assertEqual(res["role_fit_source"], catalog_source)
        self.assertIn("kubernetes", res["matched_skills"])
        self.assertIn("docker", res["matched_skills"])
        self.assertGreaterEqual(res["role_score"], 30)

    def test_two_resume_comparison_uses_identical_catalog_posting(self):
        """Verify two resumes in comparison evaluate against the exact same catalog job description."""
        catalog_desc = (
            "Senior Cloud Engineer. Must have strong hands-on experience with "
            "kubernetes, docker, terraform, aws, and ci/cd automation."
        )
        catalog_source = "Catalog Listing: Senior Cloud Engineer @ TechCorp (Archived Snapshot ID: 1001)"

        comp = local_engine.compare_resumes(
            self.resume_devops,
            self.resume_marketing,
            target_role="Financial Manager",
            job_description=catalog_desc,
            target_source_name=catalog_source,
        )

        self.assertEqual(comp["role_fit_source"], catalog_source)
        res_a = comp["resume_a"]
        res_b = comp["resume_b"]

        # Both evaluate against identical target skills from the catalog posting
        self.assertEqual(res_a["analyzed_skills"], res_b["analyzed_skills"])
        self.assertIn("kubernetes", res_a["analyzed_skills"])
        self.assertIn("docker", res_a["analyzed_skills"])

        # Resume A matches the catalog skills; Resume B does not
        self.assertGreater(res_a["role_score"], res_b["role_score"])
        self.assertIn("kubernetes", res_a["matched_skills"])
        self.assertNotIn("kubernetes", res_b["matched_skills"])


if __name__ == "__main__":
    unittest.main()
