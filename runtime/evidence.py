from datetime import datetime, timezone
from runtime.task import Task


def record(task: Task):
    evidence = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request": task.request,
        "product": task.product,
        "task_class": task.task_class,
        "agent": task.agent,
        "skills": task.skills,
        "authorization": task.authorization,
        "execution": task.execution,
        "verification": task.verification,
    }
    task.evidence = evidence
    return evidence
