import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from runtime.authorization import authorize
from runtime.product import resolve_product
from runtime.router import route_task
from runtime.skills import resolve_skills
from runtime.task import normalize

ROOT = Path(__file__).resolve().parents[1]


def codex_auto_review_enabled(config_path: Path | None = None) -> bool:
    path = config_path or (Path.home() / ".codex" / "config.toml")
    try:
        text = path.read_text()
    except OSError:
        return False
    return bool(re.search(r'^\s*approvals_reviewer\s*=\s*["\']auto_review["\']\s*$', text, re.M))


def prepare_readonly_task(request: str, product: str | None = None) -> dict[str, Any]:
    task = normalize(request)

    # The `inspect` command is an explicit read-only intent. General requests can
    # therefore be narrowed to inspection, but implementation language must not
    # be silently downgraded to bypass the human gate.
    if task.task_class == "implementation":
        authorization = authorize(task)
        return {
            "status": "BLOCKED",
            "reason": "Implementation intent cannot run through the read-only inspection harness.",
            "task": task.to_dict(),
            "authorization": authorization,
        }
    task.task_class = "inspection"

    resolved = resolve_product(request, product)
    if resolved.get("status") == "RESOLVED":
        task.product = resolved["product_key"]

    routing = route_task(task)
    skills = resolve_skills(task)
    authorization = authorize(task)

    if skills["status"] == "BLOCKED" or authorization["status"] != "AUTHORIZED":
        return {
            "status": "BLOCKED",
            "reason": "Task failed Agent OS capability or authorization resolution.",
            "task": task.to_dict(),
            "product_resolution": resolved,
            "routing": routing,
            "skills": skills,
            "authorization": authorization,
        }

    return {
        "status": "READY",
        "task": task.to_dict(),
        "product_resolution": resolved,
        "routing": routing,
        "skills": skills,
        "authorization": authorization,
    }


def inspection_prompt(plan: dict[str, Any]) -> str:
    task = plan["task"]
    resolved = plan.get("product_resolution", {})
    product_note = (
        f"{resolved.get('product_key')} ({resolved.get('repository')})"
        if resolved.get("status") == "RESOLVED"
        else "no external product resolved; inspect only the current Agent OS workspace"
    )
    skills = ", ".join(plan.get("skills", {}).get("skills", [])) or "none"

    return f"""You are operating through the Agent OS Omarchy Host v1 read-only inspection harness.

User request:
{task['request']}

Agent OS resolution:
- task class: inspection
- authorization: {task['authorization']}
- responsible agent: {task.get('agent')}
- admitted skills: {skills}
- product context: {product_note}
- active workspace: {ROOT}

Execution boundary:
- Inspect the current workspace only.
- Do not modify, create, delete, rename, commit, push, install, deploy, or change configuration.
- Do not use sudo or request privileged operating-system access.
- Do not treat a credential, reachable service, or provider connection as authorization to mutate anything.
- Do not broaden filesystem or network access merely because the task would be easier with it.
- If the request actually requires mutation, production access, deployment, additional authority, or a different workspace, stop and report the unresolved gate instead of proceeding.
- Distinguish repository evidence from inference and uncertainty.
- Cite the repository files you relied on when practical.

Complete the requested read-only inspection within those boundaries."""


def run_codex_inspection(request: str, product: str | None = None) -> int:
    if shutil.which("codex") is None:
        print("Codex harness is not available on this host.")
        return 127
    if codex_auto_review_enabled():
        print(
            "Codex approvals_reviewer=auto_review is enabled. "
            "Agent OS Host v1 requires human approval for sandbox escalation; disable auto_review before using this harness."
        )
        return 4

    plan = prepare_readonly_task(request, product)
    if plan["status"] != "READY":
        print(plan["reason"])
        if plan.get("authorization"):
            print(f"Authorization: {plan['authorization'].get('status')}")
        return 3

    prompt = inspection_prompt(plan)
    command = [
        "codex",
        "--sandbox",
        "read-only",
        "--ask-for-approval",
        "on-request",
        prompt,
    ]
    try:
        return subprocess.run(command, cwd=ROOT).returncode
    except OSError as exc:
        print(f"Failed to launch Codex: {exc}")
        return 126
