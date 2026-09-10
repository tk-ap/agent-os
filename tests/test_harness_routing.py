"""Harness routing reads the registry rather than restating it in code.

These were written in pytest style -- bare functions and bare asserts -- while
the repository's runner is unittest, so `unittest discover` collected zero of
them and they never ran. They were also broken: Task takes `request`, not
`title`, so every one would have raised TypeError on the first line. Rewritten
here as unittest cases so a green CI run actually means something about harness
routing.
"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from runtime import harness_router
from runtime.harness_router import route_harness
from runtime.store import TaskStore
from runtime.task import Task


def _task(task_class, verification_context=None):
    return Task(request="test", task_class=task_class,
                verification_context=verification_context or {})


class HarnessRoutingTests(unittest.TestCase):
    def setUp(self):
        harness_router._registry.cache_clear()
        harness_router._defaults.cache_clear()

    tearDown = setUp

    def test_implementation_prefers_codex_at_premium_tier(self):
        decision = route_harness(_task("implementation"))
        self.assertEqual(decision["harness"], "codex")
        self.assertEqual(decision["intelligence_tier"], "premium")

    def test_inspection_prefers_hermes_at_low_tier(self):
        decision = route_harness(_task("inspection"))
        self.assertEqual(decision["harness"], "hermes")
        self.assertEqual(decision["intelligence_tier"], "low")

    def test_coordination_is_the_default_for_anything_else(self):
        decision = route_harness(_task("general"))
        self.assertEqual(decision["harness"], "hermes")
        self.assertEqual(decision["reason"], "coordination_default")

    def test_verification_picks_an_uninvolved_capable_harness(self):
        catalogue = dict(harness_router._registry())
        catalogue["second_reviewer"] = {"role": "reviewer", "cost_tier": "premium",
                                        "intelligence_tier": "premium",
                                        "capabilities": ["independent_verification"]}
        with patch.object(harness_router, "_registry", lambda: catalogue):
            decision = route_harness(_task("verification", {"author_harnesses": ["claude"]}))
        self.assertEqual(decision["harness"], "second_reviewer")
        self.assertEqual(decision["reason"], "independent_verification")
        self.assertNotIn("claude", decision["fallback"])

    def test_verification_blocks_rather_than_using_an_incapable_harness(self):
        """Only claude declares independent_verification, so claude-authored work
        has no eligible verifier. Blocking is the honest answer: substituting a
        harness that does not declare the capability produces a verdict the
        registry does not support. The gap is a workforce problem, not a routing
        problem, and the error names which half is missing."""
        with self.assertRaises(RuntimeError) as raised:
            route_harness(_task("verification", {"author_harnesses": ["claude"]}))
        self.assertIn("must remain BLOCKED", str(raised.exception))
        self.assertIn("capable", str(raised.exception))

    def test_a_material_participant_is_never_the_verifier(self):
        catalogue = dict(harness_router._registry())
        catalogue["second_reviewer"] = {"role": "reviewer", "cost_tier": "premium",
                                        "intelligence_tier": "premium",
                                        "capabilities": ["independent_verification"]}
        with patch.object(harness_router, "_registry", lambda: catalogue):
            decision = route_harness(
                _task("verification", {"material_harnesses": ["claude", "codex"]}))
        self.assertNotIn(decision["harness"], {"claude", "codex"})

    def test_verification_blocks_when_nothing_independent_remains(self):
        every = list(harness_router._registry())
        with self.assertRaises(RuntimeError):
            route_harness(_task("verification", {"material_harnesses": every}))

    def test_a_fallback_can_actually_do_the_work(self):
        """A fallback list is a claim of substitutability, not a list of names.
        Only codex declares implementation, so implementation honestly has no
        fallback -- which is better than naming harnesses that would refuse."""
        decision = route_harness(_task("implementation"))
        self.assertEqual(decision["fallback"], [])
        for fallback in route_harness(_task("inspection"))["fallback"]:
            self.assertIn("inspection",
                          harness_router._registry()[fallback]["capabilities"])


class RegistryIsReadTests(unittest.TestCase):
    """The point of a registry is that editing it changes behaviour.

    A router that names its candidates in code disagrees silently with the file
    that claims to describe them -- which is exactly what happened when Gemini
    became a third fleet executor and the routing registry still listed three.
    """

    def setUp(self):
        harness_router._registry.cache_clear()
        harness_router._defaults.cache_clear()

    tearDown = setUp

    def test_gemini_is_registered_and_routable(self):
        self.assertIn("gemini", harness_router._registry())
        self.assertIn("gemini", route_harness(_task("inspection"))["fallback"])

    def test_tiers_come_from_the_registry_not_from_code(self):
        self.assertEqual(harness_router._tier("codex"), "premium")
        self.assertEqual(harness_router._tier("hermes"), "low")
        self.assertEqual(harness_router._tier("gemini"), "standard")

    def test_a_harness_added_to_the_registry_becomes_a_candidate(self):
        catalogue = dict(harness_router._registry())
        catalogue["fictional"] = {"role": "executor", "cost_tier": "low",
                                  "intelligence_tier": "premium",
                                  "capabilities": ["independent_verification"]}
        with patch.object(harness_router, "_registry", lambda: catalogue):
            decision = route_harness(
                _task("verification", {"material_harnesses": ["claude", "codex", "hermes", "gemini"]}))
        self.assertEqual(decision["harness"], "fictional",
                         "a registry entry did not reach the router")

    def test_an_unregistered_harness_is_never_selected(self):
        decision = route_harness(_task("implementation"))
        self.assertIn(decision["harness"], harness_router._registry())
        for fallback in decision["fallback"]:
            self.assertIn(fallback, harness_router._registry())


class RoutingHistoryTests(unittest.TestCase):
    def test_store_persists_routing_and_execution_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = TaskStore(Path(tmp) / "tasks.db")
            task_id = store.create({"request": "persist me"}, "READY")
            store.record_routing_decision(task_id, {
                "agent": "eugene",
                "harness": route_harness(_task("implementation")),
            })
            store.record_execution_attempt(
                task_id, attempt=1, agent="eugene", harness="codex",
                intelligence_tier="premium", outcome="executed",
                payload={"evidence_ref": "commit:abc123"})
            task = store.get(task_id)
            self.assertEqual(task["status"], "READY")
            self.assertEqual(task["routing_history"][0]["harness"], "codex")
            self.assertEqual(task["execution_history"][0]["outcome"], "executed")
            self.assertEqual(task["execution_history"][0]["payload"]["evidence_ref"],
                             "commit:abc123")


class ExecutionOutcomeTests(unittest.TestCase):
    """Which failures justify trying another harness, and which do not."""

    def test_only_capacity_justifies_rotating(self):
        self.assertTrue(TaskStore.rotatable("capacity"))
        for outcome in ("executed", "permission", "authentication", "failed", "timeout"):
            self.assertFalse(TaskStore.rotatable(outcome),
                             f"{outcome} would rotate through every harness in turn")

    def test_an_unknown_outcome_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = TaskStore(Path(tmp) / "tasks.db")
            task_id = store.create({"request": "x"}, "READY")
            with self.assertRaises(ValueError):
                store.record_execution_attempt(
                    task_id, attempt=1, agent="eugene", harness="codex",
                    intelligence_tier="premium", outcome="completed")

    def test_rotatability_is_recorded_with_the_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = TaskStore(Path(tmp) / "tasks.db")
            task_id = store.create({"request": "x"}, "READY")
            for attempt, outcome in enumerate(("capacity", "authentication"), start=1):
                store.record_execution_attempt(
                    task_id, attempt=attempt, agent="eugene", harness="codex",
                    intelligence_tier="premium", outcome=outcome)
            history = store.get(task_id)["execution_history"]
            self.assertTrue(history[0]["payload"]["rotatable"])
            self.assertFalse(history[1]["payload"]["rotatable"])
