from runtime.task import Task


def verify(task: Task):
    execution = task.execution
    if execution.get("status") != "EXECUTED":
        result = {"status": "FAILED", "reason": "Execution did not complete successfully.", "execution_status": execution.get("status")}
    elif execution.get("repository") and execution.get("entries") is not None:
        result = {"status": "VERIFIED", "checks": ["GitHub adapter executed", "repository identified", "repository evidence present"], "limitations": ["repository evidence does not prove deployment, runtime health, or resolution"]}
    else:
        result = {"status": "FAILED", "reason": "Execution produced insufficient evidence."}
    task.verification = result
    return result
