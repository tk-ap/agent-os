import json
import subprocess
from typing import Any
from runtime.task import Task


def _gh_api(path: str) -> Any:
    p = subprocess.run(["gh", "api", path], capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip() or f"gh api failed for {path}")
    return json.loads(p.stdout)


def execute(task: Task, product: dict[str, Any]):
    if task.authorization != "AUTHORIZED":
        result = {"status": "BLOCKED", "reason": "Task is not authorized for execution."}
        task.execution = result
        return result
    if product.get("status") != "RESOLVED":
        result = {"status": "BLOCKED", "reason": "Product was not resolved."}
        task.execution = result
        return result

    repo = product["repository"]
    try:
        root = _gh_api(f"repos/{repo}/contents?ref=main")
        entries = [{"name": x["name"], "type": x["type"], "path": x["path"]} for x in root]
        metadata = _gh_api(f"repos/{repo}")
        result = {
            "status": "EXECUTED",
            "adapter": "github",
            "repository": repo,
            "integration_level": product["integration_level"],
            "default_branch": metadata.get("default_branch"),
            "private": metadata.get("private"),
            "entries": entries[:200],
            "entry_count": len(entries),
            "evidence_scope": "repository structure and metadata; does not prove deployment or runtime health",
        }
    except (RuntimeError, json.JSONDecodeError, OSError) as exc:
        result = {"status": "FAILED", "adapter": "github", "repository": repo, "reason": str(exc)}
    task.execution = result
    return result
