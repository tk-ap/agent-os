from runtime.task import Task

SAFE_TASK_CLASSES = {"inspection"}


def authorize(task: Task):
    if task.task_class in SAFE_TASK_CLASSES:
        task.authorization = "AUTHORIZED"
        return {"status": "AUTHORIZED", "reason": "Inspection is within the initial read-only execution envelope."}
    task.authorization = "HUMAN_GATE"
    return {"status": "HUMAN_GATE", "reason": "Mutating actions require explicit execution authorization."}
