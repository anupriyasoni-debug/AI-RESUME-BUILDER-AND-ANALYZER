import unittest

import local_model


class RewriteSafetyTests(unittest.TestCase):
    def setUp(self):
        self.engine = local_model.LocalResumeEngine()

    def test_vague_wording_is_not_expanded_into_a_specific_claim(self):
        original = "made things better"

        alternatives = self.engine.generate_bullet_alternatives(original)

        self.assertEqual(
            alternatives["professional"]["text"],
            "made things better.",
        )
        self.assertEqual(alternatives["concise"]["text"], original)
        self.assertEqual(alternatives["impact"]["text"], original)
        self.assertNotIn("application", str(alternatives).lower())
        self.assertNotIn("functionality", str(alternatives).lower())
        self.assertIn("edit", alternatives["professional"]["note"].lower())
        self.assertIn("real outcome", alternatives["impact"]["note"].lower())

    def test_tool_or_technology_cannot_be_added_removed_or_swapped(self):
        original = "Built reports using Python and SQL."

        for candidate in (
            "Built reports using Python and Java.",
            "Built reports using Python, SQL, and Tableau.",
            "Built reports using Python.",
        ):
            with self.subTest(candidate=candidate):
                valid, _ = local_model.check_rewrite_structure(original, candidate)
                self.assertFalse(valid)

    def test_equal_number_cannot_be_reassigned_to_a_different_group(self):
        valid, _ = local_model.check_rewrite_structure(
            "Managed 5 engineers.",
            "Managed 5 customers.",
        )

        self.assertFalse(valid)

    def test_leading_team_size_is_not_stripped_as_a_bullet_marker(self):
        original = "5 engineers used Python."

        alternatives = self.engine.generate_bullet_alternatives(original)

        self.assertEqual(alternatives["impact"]["text"], original)
        self.assertIn("5 engineers", alternatives["professional"]["text"])
        self.assertIn("Python", alternatives["concise"]["text"])

    def test_leadership_ownership_causation_and_outcomes_cannot_be_added(self):
        original = "Worked with the team on deployment."
        unsafe_candidates = (
            "Led the team on deployment.",
            "Owned deployment.",
            "Worked with the team on deployment, reducing costs.",
            "Worked with the team on deployment, improving reliability.",
        )

        for candidate in unsafe_candidates:
            with self.subTest(candidate=candidate):
                valid, _ = local_model.check_rewrite_structure(original, candidate)
                self.assertFalse(valid)

    def test_metric_relationship_cannot_be_changed(self):
        original = "Reduced latency by 20% using Python."
        candidate = "Used Python to reduce costs by 20%."

        valid, _ = local_model.check_rewrite_structure(original, candidate)
        alternatives = self.engine.generate_bullet_alternatives(original)

        self.assertFalse(valid)
        self.assertEqual(alternatives["impact"]["text"], original)
        self.assertIn("metric", alternatives["impact"]["note"].lower())

    def test_unsafe_candidate_falls_back_to_original_with_manual_guidance(self):
        original = "Worked with five engineers."
        unsafe_candidate = "Led five engineers."

        text, note = local_model._candidate_or_original(original, unsafe_candidate)

        self.assertEqual(text, original)
        self.assertIn("original", note.lower())
        self.assertIn("manually", note.lower())

    def test_concise_only_removes_the_unambiguous_filler_phrase(self):
        original = "In order to build various tools, tested Python scripts."
        alternatives = self.engine.generate_bullet_alternatives(original)

        self.assertEqual(
            alternatives["concise"]["text"],
            "To build various tools, tested Python scripts.",
        )
        self.assertIn("various", alternatives["concise"]["text"])
        self.assertIn("Python", alternatives["concise"]["text"])

    def test_structural_check_is_explicitly_not_semantic_verification(self):
        description = local_model.check_rewrite_structure.__doc__.lower()

        self.assertIn("limited", description)
        self.assertIn("does not establish semantic", description)


if __name__ == "__main__":
    unittest.main()
