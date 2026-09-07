import unittest

from runtime.authorization import (
    AGENT_CONSENSUS,
    AUTONOMOUS,
    HUMAN_ESCALATION,
    authorize,
    classify,
)
from runtime.task import Task, normalize


class AuthorizationDecisionTests(unittest.TestCase):
    def test_read_only_inspection_is_autonomous_and_authorized(self):
        result = authorize(normalize("inspect ailhat"))
        self.assertEqual(result["decision_class"], AUTONOMOUS)
        self.assertEqual(result["status"], "AUTHORIZED")
        self.assertEqual(result["triggers"], [])

    def test_mutating_task_still_reaches_the_human_gate(self):
        # Behaviour relied on by tests/test_task_api.py and runtime/executor.py.
        task = normalize("fix the broken mobile navigation on ASHWOOD")
        result = authorize(task)
        self.assertEqual(result["status"], "HUMAN_GATE")
        self.assertEqual(task.authorization, "HUMAN_GATE")

    def test_unrecognised_task_class_fails_closed(self):
        result = authorize(Task(request="do the thing", task_class="speculative"))
        self.assertEqual(result["decision_class"], HUMAN_ESCALATION)
        self.assertEqual(result["status"], "HUMAN_GATE")
        self.assertIn("unrecognised task class", result["triggers"][0])

    def test_destructive_action_escalates_even_when_classed_read_only(self):
        # An inspection label must not launder a destructive declared action.
        task = Task(request="routine cleanup", task_class="inspection")
        result = authorize(task, {"actions": ["delete production bucket"]})
        self.assertEqual(result["decision_class"], HUMAN_ESCALATION)
        self.assertEqual(result["status"], "HUMAN_GATE")

    def test_sensitive_data_class_escalates(self):
        task = Task(request="read the table", task_class="inspection")
        result = authorize(task, {"data_classes": ["pii"]})
        self.assertEqual(result["decision_class"], HUMAN_ESCALATION)

    def test_external_reach_requires_named_control_agent(self):
        task = Task(request="collect a page", task_class="inspection")
        result = authorize(task, {"network_destinations": ["https://example.com"]})
        self.assertEqual(result["decision_class"], AGENT_CONSENSUS)
        self.assertEqual(result["status"], "HUMAN_GATE")
        self.assertIn("rook", result["control_agents"])

    def test_multiple_resources_require_systemic_control_agent(self):
        task = Task(request="look at both", task_class="inspection")
        result = authorize(task, {"resources": ["alvira", "ledgato"]})
        self.assertEqual(result["decision_class"], AGENT_CONSENSUS)
        self.assertIn("w-dog", result["control_agents"])

    def test_malformed_request_does_not_widen_authority(self):
        task = Task(request="inspect something", task_class="inspection")
        for bad in ("not-a-dict", 42, [], {"actions": None}, {"actions": {"op": "delete"}}):
            with self.subTest(bad=bad):
                result = authorize(task, bad if isinstance(bad, dict) else None)
                self.assertIn(result["status"], ("AUTHORIZED", "HUMAN_GATE"))
        # A dict-shaped action still has to be read, not ignored.
        self.assertEqual(
            classify(task, {"actions": {"op": "delete"}})["decision_class"], HUMAN_ESCALATION
        )

    def test_decision_records_policy_and_evaluated_fields(self):
        result = authorize(normalize("inspect ailhat"))
        self.assertEqual(result["policy"], "policies/AUTONOMY_POLICY.md")
        for field in ("actions", "data_classes", "constraints", "network_destinations", "resources"):
            self.assertIn(field, result["evaluated_fields"])


if __name__ == "__main__":
    unittest.main()
