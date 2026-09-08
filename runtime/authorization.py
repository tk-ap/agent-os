"""Authorization decision for a task.

Implements the four decision classes defined in policies/AUTONOMY_POLICY.md and
evaluates the fields defined in contracts/authorization-request.schema.json.
"""

from typing import Any

from runtime.task import Task

POLICY = "policies/AUTONOMY_POLICY.md"

AUTONOMOUS = "AUTONOMOUS"
AUTONOMOUS_AUDIT = "AUTONOMOUS_AUDIT"
AGENT_CONSENSUS = "AGENT_CONSENSUS"
HUMAN_ESCALATION = "HUMAN_ESCALATION"

_GATE = {
    AUTONOMOUS: "AUTHORIZED",
    AUTONOMOUS_AUDIT: "AUTHORIZED",
    AGENT_CONSENSUS: "HUMAN_GATE",
    HUMAN_ESCALATION: "HUMAN_GATE",
}

READ_ONLY_TASK_CLASSES = {"inspection"}

CONTROL_AGENTS = {
    "economics": "ledger",
    "security": "rook",
    "privacy": "rook",
    "irreversibility": "rook",
    "systemic-consistency": "w-dog",
    "initiative-priority": "steward",
}

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
    # Independent verification is an audited role, not release authority. The
    # verifier may inspect live/provider state, but any underlying mutation must
    # still be separately bounded by the target system's own authorization path.
    if task.task_class == "verification":
        return {
            "decision_class": AUTONOMOUS_AUDIT,
            "triggers": ["independent verification role; attestation does not grant release authority"],
            "control_agents": [],
        }

    triggers: list[str] = []
    for label, field, needles in _ESCALATION_RULES:
        declared = _values(request, field)
        hits = sorted({n for n in needles for value in declared if n in value})
        if field == "actions":
            hits += sorted({n for n in needles if n in task.request.lower()} - set(hits))
        if hits:
            triggers.append(f"{label} ({field}: {', '.join(hits)})")

    if triggers:
        return {"decision_class": HUMAN_ESCALATION, "triggers": triggers, "control_agents": []}

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

    if task.task_class == "implementation":
        return {
            "decision_class": HUMAN_ESCALATION,
            "triggers": ["mutating action without a declared authorization request"],
            "control_agents": [],
        }

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
        AUTONOMOUS_AUDIT: "Within delegated authority; rationale and evidence must be recorded.",
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
