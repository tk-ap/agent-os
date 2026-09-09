from __future__ import annotations

from dataclasses import dataclass

from runtime.task import Task


@dataclass(frozen=True)
class HarnessDecision:
    harness: str
    intelligence_tier: str
    reason: str
    fallback: list[str]

    def to_dict(self) -> dict:
        return {
            "harness": self.harness,
            "intelligence_tier": self.intelligence_tier,
            "reason": self.reason,
            "fallback": self.fallback,
        }


def route_harness(task: Task) -> dict:
    """Select an execution harness without changing durable task ownership/state.

    Agent identity routing and harness routing are deliberately separate concerns.
    Harnesses are replaceable execution resources; tasks and agent identities persist.
    """
    ctx = task.verification_context or {}

    if task.task_class == "verification":
        author_harnesses = set(ctx.get("author_harnesses", [])) | set(ctx.get("material_harnesses", []))
        candidates = ["claude", "codex", "hermes"]
        for candidate in candidates:
            if candidate not in author_harnesses:
                return HarnessDecision(
                    harness=candidate,
                    intelligence_tier="premium" if candidate in {"claude", "codex"} else "low",
                    reason="independent_verification",
                    fallback=[h for h in candidates if h != candidate and h not in author_harnesses],
                ).to_dict()
        raise RuntimeError("No independent execution harness is available; verification must remain BLOCKED")

    if task.task_class == "implementation":
        return HarnessDecision(
            harness="codex",
            intelligence_tier="premium",
            reason="repository_or_implementation_change",
            fallback=["claude"],
        ).to_dict()

    if task.task_class == "inspection":
        return HarnessDecision(
            harness="hermes",
            intelligence_tier="low",
            reason="routine_inspection_or_status",
            fallback=["claude"],
        ).to_dict()

    return HarnessDecision(
        harness="hermes",
        intelligence_tier="low",
        reason="coordination_default",
        fallback=["claude", "codex"],
    ).to_dict()
