"""
Regression and verification test suite for resume analyzer job description matching,
noise reduction, repeated-word detection, and evidence-based feedback.
"""

import unittest
import analyzer


class JobDescriptionMatchingTests(unittest.TestCase):
    def setUp(self):
        # Synthetic Data Scientist job description containing skills, responsibilities,
        # qualifications, and repeated generic prose phrases.
        self.synthetic_ds_jd = (
            "We are seeking a talented Senior Data Scientist to join our growing team. "
            "In this role, a Data Scientist applies advanced techniques to solve complex "
            "business problems. Core responsibilities include: analyzing large enterprise "
            "datasets build machine learning models, and collaborating across engineering. "
            "Qualifications: 3+ years of experience with Python, SQL, pandas, numpy, and "
            "scikit-learn. Demonstrated experience with data visualization tools such as Tableau "
            "or Power BI. Strong background in statistics, feature engineering, and predictive modeling."
        )

    def test_noise_reduction_does_not_extract_arbitrary_fragments(self):
        """Assert the extractor does NOT return arbitrary noisy fragments."""
        extracted = analyzer._extract_job_keywords(self.synthetic_ds_jd)

        noisy_fragments = [
            "datasets build machine",
            "a data scientist applies",
            "data scientist applies",
            "business problems core",
            "business problems. core",
            "solve complex",
            "complex business",
            "responsibilities include",
            "qualifications strong",
            "growing team",
            "enterprise datasets build",
        ]
        for noisy in noisy_fragments:
            self.assertNotIn(
                noisy,
                extracted,
                f"Extractor incorrectly extracted noisy fragment: '{noisy}'"
            )

    def test_curated_skill_extraction_prefers_meaningful_technical_terms(self):
        """Assert the extractor successfully discovers authentic technical skills and multiword phrases."""
        extracted = analyzer._extract_job_keywords(self.synthetic_ds_jd)

        expected_skills = [
            "python",
            "sql",
            "pandas",
            "numpy",
            "scikit-learn",
            "machine learning",
            "data visualization",
            "tableau",
            "power bi",
            "statistics",
            "predictive modeling",
            "feature engineering",
        ]
        for skill in expected_skills:
            self.assertIn(
                skill,
                extracted,
                f"Expected skill '{skill}' was not extracted from synthetic JD"
            )

    def test_insufficient_terms_returns_none_score_with_notice(self):
        """Assert that if too few meaningful terms are detected, score is None with explanation."""
        vague_jd = "Great company looking for someone to work hard and have fun with our team."
        analysis = analyzer.analyze_job_description(
            "Experienced professional with strong communication.",
            vague_jd
        )
        self.assertTrue(analysis["available"])
        self.assertIsNone(analysis["score"])
        self.assertIsNotNone(analysis["notice"])
        self.assertIn("fewer than 3", analysis["notice"].lower())

    def test_shows_terms_analyzed_list(self):
        """Assert that terms_analyzed_list is returned so the user can see what was evaluated."""
        analysis = analyzer.analyze_job_description(
            "Experienced in Python and SQL.",
            self.synthetic_ds_jd
        )
        self.assertIn("terms_analyzed_list", analysis)
        self.assertGreaterEqual(len(analysis["terms_analyzed_list"]), 5)
        self.assertIn("python", analysis["terms_analyzed_list"])


class RepeatedWordCheckTests(unittest.TestCase):
    def test_adjacent_duplicate_words_on_same_line_are_flagged(self):
        """Assert that 'the the' or other adjacent duplicates on the same line are flagged."""
        resume_with_stutter = "Responsible for reviewing the the deployment pipelines."
        res = analyzer.check_grammar(resume_with_stutter)
        findings = [f.lower() for f in res["findings"]]
        self.assertTrue(
            any("the" in f and "adjacent" in f for f in findings),
            f"Expected adjacent duplicate warning for 'the', got: {res['findings']}"
        )

    def test_word_occurring_in_separate_parts_of_resume_is_not_flagged(self):
        """
        Assert that 'hackathon' appearing across different lines, bullets, or paragraphs
        does NOT trigger a repeated-word warning.
        """
        resume_with_separate_occurrences = (
            "Experience\n"
            "- Organized annual university Hackathon with 300 participants.\n"
            "- Built real-time analytics dashboard using Python and SQL.\n\n"
            "Projects\n"
            "Hackathon Winner (2024)\n"
            "- Developed AI assistive tool during 48-hour Hackathon."
        )
        res = analyzer.check_grammar(resume_with_separate_occurrences)
        findings = [f.lower() for f in res["findings"]]
        for finding in findings:
            self.assertNotIn(
                "hackathon",
                finding,
                f"Spuriously flagged 'hackathon' repeated across separate parts: {finding}"
            )

    def test_adjacent_duplicate_hackathon_on_same_line_is_flagged(self):
        """Assert that adjacent repetition on the exact same line ('hackathon hackathon') IS flagged."""
        text = "Attended the hackathon hackathon event."
        res = analyzer.check_grammar(text)
        findings = [f.lower() for f in res["findings"]]
        self.assertTrue(
            any("hackathon" in f for f in findings),
            "Expected adjacent duplicate warning for 'hackathon'"
        )


class EvidenceBasedRecommendationsAndScoringTests(unittest.TestCase):
    def test_missing_skills_suggestions_are_conditional(self):
        """Assert missing skill suggestions advise including skills only if the user actually has them."""
        results = {
            "missing_sections": [],
            "missing_skills": ["PyTorch", "Transformers"],
            "impact_score": 15,
            "length_score": 15,
            "word_count": 500,
            "bullet_analysis": {"quantified_count": 2, "suggestions": []},
            "grammar_analysis": {"findings": []},
            "formatting_analysis": {"issues": []},
        }
        suggestions = analyzer.generate_suggestions(results, target_role="AI Engineer")
        suggestions_str = " ".join(suggestions).lower()
        self.assertIn("only include skills you actually possess", suggestions_str)

    def test_missing_sections_phrased_as_checks(self):
        """Assert missing sections are phrased as heading checks rather than absolute demands."""
        results = {
            "missing_sections": ["certifications"],
            "missing_skills": [],
            "impact_score": 15,
            "length_score": 15,
            "word_count": 500,
            "bullet_analysis": {"quantified_count": 2, "suggestions": []},
            "grammar_analysis": {"findings": []},
            "formatting_analysis": {"issues": []},
        }
        suggestions = analyzer.generate_suggestions(results, target_role="Data Scientist")
        suggestions_str = " ".join(suggestions).lower()
        self.assertIn("heading check", suggestions_str)

    def test_score_breakdown_formula_matches_total(self):
        """Assert component scores sum to total_score according to the documented formula."""
        sample_resume = (
            "Jane Doe\njane@example.com | +1 555 987 6543\n\n"
            "Summary\nData Scientist with experience in predictive modeling.\n\n"
            "Education\nB.S. in Computer Science.\n\n"
            "Experience\n"
            "- Developed predictive machine learning models in Python and SQL.\n"
            "- Increased ETL processing speed by 35% across 5M records.\n\n"
            "Skills\nPython, SQL, pandas, numpy, scikit-learn, Tableau.\n\n"
            "Projects\n- Built customer churn model achieving 88% accuracy.\n\n"
            "Certifications\nAWS Certified Cloud Practitioner.\n"
        )
        res = analyzer.analyze_resume(sample_resume, target_role="Data Scientist")
        breakdown = res["score_breakdown"]

        expected_sum = (
            breakdown["role_score"] +
            breakdown["section_score"] +
            breakdown["impact_score"] +
            breakdown["length_score"]
        )
        self.assertEqual(
            res["total_score"],
            expected_sum,
            f"Total score {res['total_score']} does not match component sum {expected_sum}"
        )
        self.assertIn("formula", breakdown)


class JobDescriptionPrioritizationAndComparisonTests(unittest.TestCase):
    def setUp(self):
        self.devops_jd = (
            "Seeking a Senior DevOps Engineer. Must have hands-on experience with "
            "docker, kubernetes, terraform, aws, and ci/cd pipelines. Experience with "
            "linux and monitoring tools is a plus."
        )

        self.resume_with_aliases = (
            "Alex Smith\nalex@example.com | 555-0199\n\n"
            "Summary\nInfrastructure engineer with extensive cloud and container experience.\n\n"
            "Experience\n"
            "- Managed containerized workloads using k8s and docker across multiple clusters.\n"
            "- Provisioned infrastructure using terraform on aws with automated ci/cd workflows.\n"
            "- Reduced deployment failure rate by 40% through automated canary releases.\n\n"
            "Skills\nk8s, docker, terraform, aws, ci/cd, linux, sklearn.\n\n"
            "Education\nB.S. in Computer Engineering, State University, 2021.\n\n"
            "Projects\n- Built automated deployment pipeline for microservices.\n"
        )

        self.resume_bare = (
            "Jordan Lee\njordan@example.com | 555-0188\n\n"
            "Summary\nMarketing coordinator with general project management experience.\n\n"
            "Experience\n"
            "- Coordinated cross-functional marketing campaigns and vendor communication.\n"
            "- Analyzed monthly campaign engagement across web channels.\n\n"
            "Skills\nseo, content marketing, communication, google analytics.\n\n"
            "Education\nB.A. in Communications, City College, 2020.\n\n"
            "Projects\n- Launched social media awareness drive.\n"
        )

    def test_pasted_jd_overrides_conflicting_preset_for_role_fit(self):
        """Verify that a pasted JD overrides a conflicting selected preset for role-fit scoring."""
        # Preset is Digital Marketing Manager, but pasted JD is Cloud DevOps Engineer
        res = analyzer.analyze_resume(
            self.resume_with_aliases,
            target_role="Digital Marketing Manager",
            pasted_jd=self.devops_jd
        )
        self.assertTrue(res["using_jd_target"])
        self.assertEqual(res["role_fit_source"], "Job Description")
        self.assertIn("docker", res["analyzed_skills"])
        self.assertIn("kubernetes", res["analyzed_skills"])
        # Should NOT be evaluated against Digital Marketing skills (seo, sem, etc.)
        self.assertNotIn("seo", res["analyzed_skills"])
        # Match rate should be high because resume has k8s (alias for kubernetes), docker, terraform, aws, ci/cd
        self.assertGreaterEqual(res["role_score"], 30)

    def test_canonical_aliases_match_consistently(self):
        """Verify aliases like k8s/kubernetes and sklearn/scikit-learn match reliably."""
        # 1. 'k8s' in resume should match 'kubernetes' in analyzed JD skills
        res = analyzer.analyze_resume(
            self.resume_with_aliases,
            target_role="Cloud DevOps Engineer",
            pasted_jd=self.devops_jd
        )
        self.assertIn("kubernetes", res["matched_skills"])

        # 2. 'sklearn' in resume should match 'scikit-learn' in Data Scientist preset
        ds_resume = "Skills: sklearn, python, pandas\nExperience: developed machine learning models"
        res_ds = analyzer.analyze_resume(ds_resume, target_role="Data Scientist")
        self.assertIn("scikit-learn", res_ds["matched_skills"])

        # 3. Direct boundary check on alias mapping
        self.assertTrue(analyzer._skill_in_text("kubernetes", "deployed containers on k8s clusters"))
        self.assertTrue(analyzer._skill_in_text("k8s", "managed large kubernetes infrastructure"))
        self.assertTrue(analyzer._skill_in_text("scikit-learn", "trained classifiers using sklearn."))
        self.assertTrue(analyzer._skill_in_text("aws", "cloud deployments on amazon web services"))
        self.assertTrue(analyzer._skill_in_text("amazon web services", "cloud infrastructure on aws."))

    def test_short_jd_triggers_documented_fallback_behavior(self):
        """Verify a JD with fewer than 3 recognized skills triggers preset fallback with notice."""
        short_jd = "Looking for an energetic team player to join our exciting company!"
        res = analyzer.analyze_resume(
            self.resume_with_aliases,
            target_role="Cloud DevOps Engineer",
            pasted_jd=short_jd
        )
        self.assertFalse(res["using_jd_target"])
        self.assertIsNotNone(res["jd_fallback_notice"])
        self.assertIn("fewer than 3 recognized skills", res["jd_fallback_notice"])
        self.assertIn("Fallback", res["role_fit_source"])
        # Preset skills for Cloud DevOps Engineer should be used
        expected_devops = analyzer.JOB_TAXONOMY["Cloud DevOps Engineer"]["skills"]
        self.assertEqual(res["analyzed_skills"], expected_devops)

    def test_comparison_uses_same_jd_and_rubric_with_distinct_results(self):
        """Verify both resumes use the exact same JD and rubric while returning distinct scores."""
        from local_model import local_engine

        comp = local_engine.compare_resumes(
            self.resume_with_aliases,
            self.resume_bare,
            target_role="Financial Manager",
            job_description=self.devops_jd
        )
        self.assertEqual(comp["role_fit_source"], "Job Description")
        self.assertIsNone(comp["jd_fallback_notice"])

        res_a = comp["resume_a"]
        res_b = comp["resume_b"]

        # Both evaluated against same JD skills
        self.assertEqual(res_a["analyzed_skills"], res_b["analyzed_skills"])
        self.assertIn("docker", res_a["analyzed_skills"])

        # Resume A has docker, k8s, terraform, aws, ci/cd
        # Resume B has marketing skills
        self.assertGreater(res_a["role_score"], res_b["role_score"])
        self.assertGreater(res_a["ats_score"], res_b["ats_score"])
        self.assertIn("kubernetes", res_a["matched_skills"])
        self.assertNotIn("kubernetes", res_b["matched_skills"])

    def test_comparison_without_jd_uses_preset_consistently(self):
        """Verify comparison without JD uses the selected preset consistently for both resumes."""
        from local_model import local_engine

        comp = local_engine.compare_resumes(
            self.resume_with_aliases,
            self.resume_bare,
            target_role="Cloud DevOps Engineer",
            job_description=""
        )
        self.assertEqual(comp["role_fit_source"], "Preset: Cloud DevOps Engineer")
        self.assertEqual(comp["target_skills"], analyzer.JOB_TAXONOMY["Cloud DevOps Engineer"]["skills"])
        self.assertEqual(comp["resume_a"]["analyzed_skills"], comp["resume_b"]["analyzed_skills"])


class SkillAliasAndBoundaryRegressionTests(unittest.TestCase):
    """
    Focused tests for boundary-aware matching (R, Go, C), canonical alias mapping,
    duplicate alias prevention, and consistent two-resume comparison.
    """

    def test_boundary_aware_matching_for_r(self):
        """Verify R does NOT match inside unrelated words or R&D, but matches authentic R usage."""
        # Unrelated words containing 'r'
        self.assertFalse(analyzer._skill_in_text("r", "Developed applications in Rust, React, and Ruby."))
        self.assertFalse(analyzer._skill_in_text("r", "Order processing and clear communication."))
        self.assertFalse(analyzer._skill_in_text("r", "Prior experience with word processors."))

        # False-positive contexts: R&D, R & D, R-squared
        self.assertFalse(analyzer._skill_in_text("r", "Led the R&D team on novel product development."))
        self.assertFalse(analyzer._skill_in_text("r", "Senior researcher in R & D department."))
        self.assertFalse(analyzer._skill_in_text("r", "Regression model achieved R-squared of 0.94."))

        # Authentic R usage
        self.assertTrue(analyzer._skill_in_text("r", "Data analysis using Python, R, and SQL."))
        self.assertTrue(analyzer._skill_in_text("r", "Proficient in R programming and tidyverse."))
        self.assertTrue(analyzer._skill_in_text("r", "Statistical modeling in Python/R/Julia."))

    def test_boundary_aware_matching_for_go(self):
        """Verify Go does NOT match inside unrelated words or colloquial phrases, but matches authentic Go/Golang."""
        # Unrelated words containing 'go'
        self.assertFalse(analyzer._skill_in_text("go", "Built APIs using Django framework and cargo tracking."))
        self.assertFalse(analyzer._skill_in_text("go", "Good ongoing negotiation and leadership skills."))
        self.assertFalse(analyzer._skill_in_text("go", "Optimized algorithmic sorting routines."))

        # Colloquial English phrases
        self.assertFalse(analyzer._skill_in_text("go", "Known as the go-to person on the engineering team."))
        self.assertFalse(analyzer._skill_in_text("go", "Helped the team go live with the production release."))
        self.assertFalse(analyzer._skill_in_text("go", "Coordinated smooth go-live rollout across clusters."))
        self.assertFalse(analyzer._skill_in_text("go", "Formulated go to market strategy for new SaaS offering."))

        # Authentic Go and Golang usage
        self.assertTrue(analyzer._skill_in_text("go", "Engineered microservices in Go, Python, and C++."))
        self.assertTrue(analyzer._skill_in_text("go", "Backend development using Golang and gRPC."))
        self.assertTrue(analyzer._skill_in_text("go", "Proficient in Go programming language."))

    def test_boundary_aware_matching_for_c(self):
        """Verify C does NOT match inside unrelated words, C++, C#, or C-suite, but matches authentic C usage."""
        # Unrelated words containing 'c'
        self.assertFalse(analyzer._skill_in_text("c", "Category management and basic project coordination."))
        self.assertFalse(analyzer._skill_in_text("c", "Clear code structure and best practices."))

        # Other languages and false-positives: C++, C#, C-level, c/o
        self.assertFalse(analyzer._skill_in_text("c", "Object-oriented software development in C++."))
        self.assertFalse(analyzer._skill_in_text("c", "Full-stack enterprise applications in C# and .NET."))
        self.assertFalse(analyzer._skill_in_text("c", "Reported quarterly metrics directly to C-level executives."))
        self.assertFalse(analyzer._skill_in_text("c", "Executive presentation to C-suite leadership."))
        self.assertFalse(analyzer._skill_in_text("c", "Please mail letters c/o Human Resources."))

        # Authentic C usage
        self.assertTrue(analyzer._skill_in_text("c", "Low-level system programming in C, C++, and Assembly."))
        self.assertTrue(analyzer._skill_in_text("c", "Firmware development in Embedded C."))
        self.assertTrue(analyzer._skill_in_text("c", "High-performance kernels written in C/C++."))
        self.assertTrue(analyzer._skill_in_text("c", "Languages: C, Python, and Java."))

    def test_duplicate_aliases_return_canonical_skill_only_once(self):
        """Verify each canonical skill is returned only once even when multiple aliases occur in resume or JD."""
        # Resume contains both canonical term and its alias
        resume_with_duplicates = (
            "Alex Smith\nalex@example.com | 555-0100\n\n"
            "Summary\nCloud and Machine Learning Engineer.\n\n"
            "Experience\n"
            "- Orchestrated microservices with Kubernetes and k8s clusters.\n"
            "- Trained classification pipelines using Scikit-Learn and sklearn.\n"
            "- Developed backend services in Go and Golang.\n\n"
            "Skills\nKubernetes, k8s, Scikit-Learn, sklearn, Go, Golang, Python.\n\n"
            "Education\nB.S. in Computer Science.\n"
        )

        res = analyzer.analyze_resume(
            resume_with_duplicates,
            target_role="Data Scientist"
        )
        # Verify scikit-learn is present exactly once in matched_skills
        scikit_matches = [s for s in res["matched_skills"] if s == "scikit-learn"]
        self.assertEqual(len(scikit_matches), 1, "scikit-learn should appear exactly once in matched_skills")

        # In JD extraction, verify both aliases produce a single canonical entry
        jd_with_duplicate_aliases = (
            "Seeking an engineer skilled in Kubernetes, k8s, k8, Scikit-Learn, sklearn, "
            "Golang, Go, and Python for distributed system development."
        )
        extracted = analyzer._extract_job_keywords(jd_with_duplicate_aliases)
        self.assertEqual(extracted.count("kubernetes"), 1)
        self.assertEqual(extracted.count("scikit-learn"), 1)
        self.assertEqual(extracted.count("go"), 1)
        self.assertNotIn("k8s", extracted)
        self.assertNotIn("sklearn", extracted)
        self.assertNotIn("golang", extracted)

    def test_consistent_comparison_across_alias_variants(self):
        """Verify two resumes listing different aliases of the same skills evaluate identically."""
        from local_model import local_engine

        jd = (
            "Requirements: Experience with kubernetes container orchestration, "
            "scikit-learn machine learning, python, and go backend services."
        )

        # Resume A uses abbreviated aliases
        resume_a = (
            "Resume A\na@example.com | 555-0001\n\n"
            "Summary\nCloud and ML engineer.\n\n"
            "Experience\n"
            "- Managed container deployments with k8s and docker.\n"
            "- Trained predictive models using sklearn and python.\n"
            "- Built microservices with golang.\n\n"
            "Skills\nk8s, sklearn, golang, python.\n\n"
            "Education\nB.S. Computer Science.\n"
        )

        # Resume B uses canonical names
        resume_b = (
            "Resume B\nb@example.com | 555-0002\n\n"
            "Summary\nCloud and ML engineer.\n\n"
            "Experience\n"
            "- Managed container deployments with kubernetes and docker.\n"
            "- Trained predictive models using scikit-learn and python.\n"
            "- Built microservices with go.\n\n"
            "Skills\nkubernetes, scikit-learn, go, python.\n\n"
            "Education\nB.S. Computer Science.\n"
        )

        comp = local_engine.compare_resumes(
            resume_a,
            resume_b,
            target_role="AI Engineer",
            job_description=jd
        )

        matched_a = set(comp["resume_a"]["matched_skills"])
        matched_b = set(comp["resume_b"]["matched_skills"])

        # Both resumes must match identical canonical skills
        self.assertEqual(matched_a, matched_b)
        self.assertIn("kubernetes", matched_a)
        self.assertIn("scikit-learn", matched_a)
        self.assertIn("go", matched_a)

        # Both must receive identical 40-point role fit scores
        self.assertEqual(comp["resume_a"]["role_score"], comp["resume_b"]["role_score"])


if __name__ == "__main__":
    unittest.main()


