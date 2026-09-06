"""Authorization decision for a task.

Implements the four decision classes defined in policies/AUTONOMY_POLICY.md and
evaluates the fields defined in contracts/authorization-request.schema.json.

Two things are deliberate.

The decision is a pure function of declared inputs. No model judgement is
involved, because this is the enforcement boundary; interpretation belongs
above it, not inside it.

It fails closed. Anything not positively recognised as within the read-only
envelope escalates. An unrecognised action, an unreadable request, or a field
the policy has no rule for produces HUMAN_ESCALATION rather than a default
allow.
"""

from typing import Any

from runtime.task import Task

POLICY = "policies/AUTONOMY_POLICY.md"

# policies/AUTONOMY_POLICY.md, "Decision Classes"
AUTONOMOUS = "AUTONOMOUS"
AUTONOMOUS_AUDIT = "AUTONOMOUS_AUDIT"
AGENT_CONSENSUS = "AGENT_CONSENSUS"
HUMAN_ESCALATION = "HUMAN_ESCALATION"

# Only these two proceed. executor.py gates on the AUTHORIZED literal, so the
# mapping from decision class to gate is the single place that meaning lives.
_GATE = {
    AUTONOMOUS: "AUTHORIZED",
    AUTONOMOUS_AUDIT: "AUTHORIZED",
    AGENT_CONSENSUS: "HUMAN_GATE",
    HUMAN_ESCALATION: "HUMAN_GATE",
}

# Task classes inside the read-only execution envelope.
READ_ONLY_TASK_CLASSES = {"inspection"}

# The policy's AGENT CONSENSUS tier names its control agents by domain.
CONTROL_AGENTS = {
    "economics": "ledger",
    "security": "rook",
    "privacy": "rook",
    "irreversibility": "rook",
    "systemic-consistency": "w-dog",
    "initiative-priority": "steward",
}

# Each entry maps a HUMAN ESCALATION bullet in the policy to the declared
# request fields that evidence it. Kept as data so the mapping is auditable.
_ESCALATION_RULES = (
    ("irreversible or destructive material action", "actions",
     ("delete", "destroy", "drop", "purge", "truncate", "wipe", "erase", "force-push", "reset --hard", "revoke")),
    ("identity, credential, ownership, or permission change", "actions",
     ("credential", "secret", "token", "password", "rotate", "permission", "grant", "owner", "transfer")),
    ("external publication or contractual promise", "actions",
     ("publish", "post", "send", "email", "tweet", "announce", "release", "deploy")),
    ("legal or regulatory commitment", "actions",
     ("contract", "legal", "regulator", "license", "sign")),
    ("high-impact privacy or security exposure", "data_classes",
     ("pii", "personal", "credential", "secret", "financial", "health", "confidential")),
    ("spending or commitment above delegated threshold", "constraints",
     ("budget", "spend", "cost", "payment", "invoice", "purchase")),
)


def _values(request: dict[str, Any] | None, field: str) -> list[str]:
    """Declared values for a field, lowercased. Unreadable shapes yield nothing."""
    if not isinstance(request, dict):
        return []
    raw = request.get(field)
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw.lower()]
    if isinstance(raw, dict):
        return [f"{k} {v}".lower() for k, v in raw.items()]
    if isinstance(raw, (list, tuple)):
        out = []
        for item in raw:
            if isinstance(item, str):
                out.append(item.lower())
            elif isinstance(item, dict):
                out.extend(f"{k} {v}".lower() for k, v in item.items())
        return out
    return [str(raw).lower()]


def classify(task: Task, request: dict[str, Any] | None = None) -> dict[str, Any]:
    """Decide the policy class for a task and its optional authorization request."""
    triggers: list[str] = []
    for label, field, needles in _ESCALATION_RULES:
        declared = _values(request, field)
        hits = sorted({n for n in needles for value in declared if n in value})
        # The request text itself is evidence for action-shaped rules.
        if field == "actions":
            hits += sorted({n for n in needles if n in task.request.lower()} - set(hits))
        if hits:
            triggers.append(f"{label} ({field}: {', '.join(hits)})")

    if triggers:
        return {"decision_class": HUMAN_ESCALATION, "triggers": triggers, "control_agents": []}

    # Reaching outside the boundary is not automatically escalation, but it is
    # not a decision one agent should take alone either.
    consensus: list[str] = []
    if _values(request, "network_destinations"):
        consensus.append(CONTROL_AGENTS["security"])
    if len({r for r in _values(request, "resources")}) > 1:
        consensus.append(CONTROL_AGENTS["systemic-consistency"])
    if consensus:
        return {
            "decision_class": AGENT_CONSENSUS,
            "triggers": ["decision crosses material domains"],
            "control_agents": sorted(set(consensus)),
        }

    if task.task_class in READ_ONLY_TASK_CLASSES:
        return {"decision_class": AUTONOMOUS, "triggers": [], "control_agents": []}

    # Recognised, within authority, but consequential enough to record.
    if task.task_class == "implementation":
        return {
            "decision_class": HUMAN_ESCALATION,
            "triggers": ["mutating action without a declared authorization request"],
            "control_agents": [],
        }

    # Fail closed: an unrecognised task class is not evidence of safety.
    return {
        "decision_class": HUMAN_ESCALATION,
        "triggers": [f"unrecognised task class '{task.task_class}'"],
        "control_agents": [],
    }


def authorize(task: Task, request: dict[str, Any] | None = None):
    decision = classify(task, request)
    status = _GATE[decision["decision_class"]]
    task.authorization = status

    reasons = {
        AUTONOMOUS: "Read-only inspection is within the initial execution envelope.",
        AUTONOMOUS_AUDIT: "Within delegated authority; rationale and rollback path must be recorded.",
        AGENT_CONSENSUS: "Decision crosses material domains and requires the named control agents.",
        HUMAN_ESCALATION: "Policy requires human authorization before this action.",
    }
    return {
        "status": status,
        "decision_class": decision["decision_class"],
        "reason": reasons[decision["decision_class"]],
        "triggers": decision["triggers"],
        "control_agents": decision["control_agents"],
        "audit_required": decision["decision_class"] in (AUTONOMOUS_AUDIT, AGENT_CONSENSUS, HUMAN_ESCALATION),
        "policy": POLICY,
        "evaluated_fields": sorted({field for _, field, _ in _ESCALATION_RULES} | {"network_destinations", "resources"}),
    }
