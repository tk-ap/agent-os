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

    def test_verification_avoids_the_authoring_harness(self):
        decision = route_harness(_task("verification", {"author_harnesses": ["claude"]}))
        self.assertNotEqual(decision["harness"], "claude")
        self.assertEqual(decision["reason"], "independent_verification")
        self.assertNotIn("claude", decision["fallback"])

    def test_a_material_participant_is_never_the_verifier(self):
        decision = route_harness(_task("verification", {"material_harnesses": ["claude", "codex"]}))
        self.assertNotIn(decision["harness"], {"claude", "codex"})

    def test_verification_blocks_when_nothing_independent_remains(self):
        every = list(harness_router._registry())
        with self.assertRaises(RuntimeError):
            route_harness(_task("verification", {"material_harnesses": every}))


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
        decision = route_harness(_task("verification", {"author_harnesses": ["claude", "codex"]}))
        self.assertIn(decision["harness"], {"gemini", "hermes"})

    def test_tiers_come_from_the_registry_not_from_code(self):
        self.assertEqual(harness_router._tier("codex"), "premium")
        self.assertEqual(harness_router._tier("hermes"), "low")
        self.assertEqual(harness_router._tier("gemini"), "standard")

    def test_a_harness_added_to_the_registry_becomes_a_candidate(self):
        catalogue = dict(harness_router._registry())
        catalogue["fictional"] = {"role": "executor", "cost_tier": "low",
                                  "intelligence_tier": "premium",
                                  "capabilities": ["implementation"]}
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
                intelligence_tier="premium", outcome="completed",
                payload={"evidence_ref": "commit:abc123"})
            task = store.get(task_id)
            self.assertEqual(task["status"], "READY")
            self.assertEqual(task["routing_history"][0]["harness"], "codex")
            self.assertEqual(task["execution_history"][0]["outcome"], "completed")
            self.assertEqual(task["execution_history"][0]["payload"]["evidence_ref"],
                             "commit:abc123")
