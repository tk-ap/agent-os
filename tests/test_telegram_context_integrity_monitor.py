import json
import unittest

from adapters.hermes.fleet import telegram_human_monitor as monitor


class TelegramContextIntegrityMonitorTests(unittest.TestCase):
    def sample_order(self):
        return {
            "problem_or_opportunity": {
                "directive": (
                    "ALVIRA lives at alviratech.vercel.app and the old cto.new domain is retired. "
                    "public/sitemap.xml and public/robots.txt still reference the retired domain. "
                    "Update both files, verify the production URLs, deploy the reviewed change, "
                    "and confirm the live files are correct."
                )
            },
            "desired_outcome": {
                "summary": "Both production metadata files reference the canonical ALVIRA domain and are verified live."
            },
            "acceptance_criteria": ["sitemap correct", "robots correct", "live verification"],
            "context_references": ["ALVIRA repo", "production domain"],
            "evidence": [{"kind": "live"}],
        }

    def test_summary_is_display_only_and_full_context_is_counted(self):
        order = self.sample_order()
        problem, shortened = monitor._display_problem(order, "directive-1-routing", limit=120)
        self.assertTrue(shortened)
        self.assertTrue(problem.endswith("…"))
        integrity = monitor._context_integrity(order, shortened)
        self.assertIn("Full work order attached: **Yes**", integrity)
        self.assertIn("Acceptance criteria attached: **3**", integrity)
        self.assertIn("Context references attached: **2**", integrity)
        self.assertIn("Telegram summary shortened for display: **Yes**", integrity)
        self.assertIn("worker receives the stored full work order", integrity.lower())

    def test_full_directive_is_not_replaced_by_display_summary(self):
        order = self.sample_order()
        full = monitor._full_directive(order)
        problem, _ = monitor._display_problem(order, "directive-1-routing", limit=120)
        self.assertGreater(len(full), len(problem))
        self.assertIn("confirm the live files are correct", full)

    def test_assignment_message_names_problem_outcome_and_context_check(self):
        order = self.sample_order()
        problem, shortened = monitor._display_problem(order, "directive-1-routing", limit=180)
        text = monitor._assignment_message(order, problem, shortened)
        self.assertIn("**Problem**", text)
        self.assertIn("**Expected outcome**", text)
        self.assertIn("**Context check**", text)
        self.assertIn("Acceptance criteria attached: **3**", text)


if __name__ == "__main__":
    unittest.main()
