from pathlib import Path

from runtime.harness_router import route_harness
from runtime.store import TaskStore
from runtime.task import Task


def _task(task_class: str, verification_context=None):
    return Task(
        title="test",
        task_class=task_class,
        verification_context=verification_context or {},
    )


def test_implementation_prefers_codex():
    decision = route_harness(_task("implementation"))
    assert decision["harness"] == "codex"
    assert decision["intelligence_tier"] == "premium"


def test_inspection_prefers_hermes_low_tier():
    decision = route_harness(_task("inspection"))
    assert decision["harness"] == "hermes"
    assert decision["intelligence_tier"] == "low"


def test_verification_avoids_author_harness():
    decision = route_harness(
        _task("verification", {"author_harnesses": ["claude"]})
    )
    assert decision["harness"] != "claude"
    assert decision["reason"] == "independent_verification"


def test_store_persists_routing_and_execution_history(tmp_path: Path):
    store = TaskStore(tmp_path / "tasks.db")
    task_id = store.create({"title": "persist me"}, "READY")

    store.record_routing_decision(
        task_id,
        {
            "agent": "eugene",
            "harness": {
                "harness": "codex",
                "intelligence_tier": "premium",
                "reason": "repository_or_implementation_change",
                "fallback": ["claude"],
            },
        },
    )
    store.record_execution_attempt(
        task_id,
        attempt=1,
        agent="eugene",
        harness="codex",
        intelligence_tier="premium",
        outcome="completed",
        payload={"evidence_ref": "commit:abc123"},
    )

    task = store.get(task_id)
    assert task["status"] == "READY"
    assert task["routing_history"][0]["harness"] == "codex"
    assert task["execution_history"][0]["outcome"] == "completed"
    assert task["execution_history"][0]["payload"]["evidence_ref"] == "commit:abc123"
