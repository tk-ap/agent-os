import tempfile
import unittest
from pathlib import Path

from runtime.harness import codex_auto_review_enabled, inspection_prompt, prepare_readonly_task


class HarnessTests(unittest.TestCase):
    def test_general_request_is_narrowed_to_readonly_inspection(self):
        plan = prepare_readonly_task("Explain the Agent OS authorization boundary")
        self.assertEqual(plan["status"], "READY")
        self.assertEqual(plan["task"]["task_class"], "inspection")
        self.assertEqual(plan["task"]["authorization"], "AUTHORIZED")

    def test_implementation_language_cannot_bypass_human_gate(self):
        plan = prepare_readonly_task("fix the Agent OS authorization boundary")
        self.assertEqual(plan["status"], "BLOCKED")
        self.assertEqual(plan["task"]["task_class"], "implementation")
        self.assertEqual(plan["authorization"]["status"], "HUMAN_GATE")

    def test_prompt_preserves_readonly_and_privilege_boundaries(self):
        plan = prepare_readonly_task("inspect the Agent OS authorization boundary")
        prompt = inspection_prompt(plan)
        self.assertIn("Do not modify", prompt)
        self.assertIn("Do not use sudo", prompt)
        self.assertIn("stop and report the unresolved gate", prompt)

    def test_codex_auto_review_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "config.toml"
            config.write_text('model = "gpt-5"\napprovals_reviewer = "auto_review"\n')
            self.assertTrue(codex_auto_review_enabled(config))
            config.write_text('approval_policy = "on-request"\n')
            self.assertFalse(codex_auto_review_enabled(config))


if __name__ == "__main__":
    unittest.main()
