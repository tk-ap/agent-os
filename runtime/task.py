from dataclasses import dataclass, field
from typing import Any


@dataclass
class Task:
    request: str
    product: str | None = None
    task_class: str = "general"
    agent: str | None = None
    skills: list[str] = field(default_factory=list)
    authorization: str = "UNRESOLVED"
    execution: dict[str, Any] = field(default_factory=dict)
    verification: dict[str, Any] = field(default_factory=dict)
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {
            "request": self.request,
            "product": self.product,
            "task_class": self.task_class,
            "agent": self.agent,
            "skills": self.skills,
            "authorization": self.authorization,
            "execution": self.execution,
            "verification": self.verification,
            "evidence": self.evidence,
        }


def normalize(request: str) -> Task:
    text = request.lower()

    # Action verbs take precedence over words describing the condition.
    # For example, "fix the broken mobile navigation" is an implementation
    # task, while "inspect the broken mobile navigation" is an inspection.
    if any(x in text for x in ["implement", "build", "fix", "change", "code", "deploy"]):
        task_class = "implementation"
    elif any(x in text for x in ["inspect", "check", "audit", "review", "broken", "status", "diagnose"]):
        task_class = "inspection"
    else:
        task_class = "general"

    return Task(request=request, task_class=task_class)
