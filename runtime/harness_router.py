from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from runtime.task import Task

ROOT = Path(__file__).resolve().parents[1]
HARNESS_REGISTRY = ROOT / "registry" / "harnesses-v1.yaml"
ROUTING_POLICY = ROOT / "policies" / "harness-routing.yaml"

# Preference order when several harnesses could take the same work. Only used to
# break ties; it never overrides the policy default or the independence rule.
_TIER_RANK = {"premium": 0, "standard": 1, "low": 2}


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


@lru_cache(maxsize=1)
def _registry() -> dict:
    """The harness catalogue: role, cost and intelligence tier, capabilities.

    Read rather than restated in code. A harness the fleet gained -- Gemini, for
    instance -- is a registry edit, not a code change, and a router that hardcodes
    its candidates silently disagrees with the file that claims to describe them.
    """
    data = yaml.safe_load(HARNESS_REGISTRY.read_text()) or {}
    return data.get("harnesses") or {}


@lru_cache(maxsize=1)
def _defaults() -> dict:
    """Which harness each task class prefers. Policy, not catalogue."""
    data = yaml.safe_load(ROUTING_POLICY.read_text()) or {}
    return data.get("defaults") or {}


def _tier(harness: str) -> str:
    return str(_registry().get(harness, {}).get("intelligence_tier") or "low")


def _ordered(preferred: str | None = None) -> list[str]:
    """Registered harnesses, the policy's preference first, then by tier."""
    names = sorted(_registry(), key=lambda h: (_TIER_RANK.get(_tier(h), 99), h))
    if preferred in names:
        names.remove(preferred)
        names.insert(0, preferred)
    return names


def route_harness(task: Task) -> dict:
    """Select an execution harness without changing durable task ownership/state.

    Agent identity routing and harness routing are deliberately separate concerns.
    Harnesses are replaceable execution resources; tasks and agent identities persist.
    """
    ctx = task.verification_context or {}
    defaults = _defaults()

    if task.task_class == "verification":
        material = set(ctx.get("author_harnesses", [])) | set(ctx.get("material_harnesses", []))
        candidates = [h for h in _ordered(defaults.get("verification")) if h not in material]
        if not candidates:
            raise RuntimeError(
                "No independent execution harness is available; verification must remain BLOCKED")
        chosen = candidates[0]
        return HarnessDecision(
            harness=chosen,
            intelligence_tier=_tier(chosen),
            reason="independent_verification",
            fallback=candidates[1:],
        ).to_dict()

    if task.task_class == "implementation":
        chosen = defaults.get("implementation") or _ordered()[0]
        return HarnessDecision(
            harness=chosen,
            intelligence_tier=_tier(chosen),
            reason="repository_or_implementation_change",
            fallback=[h for h in _ordered() if h != chosen],
        ).to_dict()

    if task.task_class == "inspection":
        chosen = defaults.get("inspection") or _ordered()[-1]
        return HarnessDecision(
            harness=chosen,
            intelligence_tier=_tier(chosen),
            reason="routine_inspection_or_status",
            fallback=[h for h in _ordered() if h != chosen],
        ).to_dict()

    chosen = defaults.get("coordination") or _ordered()[-1]
    return HarnessDecision(
        harness=chosen,
        intelligence_tier=_tier(chosen),
        reason="coordination_default",
        fallback=[h for h in _ordered() if h != chosen],
    ).to_dict()
