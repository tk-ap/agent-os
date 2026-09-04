import json
import sys
from runtime.authorization import authorize
from runtime.evidence import record
from runtime.executor import execute
from runtime.product import resolve_product
from runtime.router import route_task
from runtime.skills import resolve_skills
from runtime.task import normalize
from runtime.verifier import verify


def run(request: str, product: str | None = None):
    task = normalize(request)
    resolved = resolve_product(request, product)
    if resolved.get("status") == "RESOLVED":
        task.product = resolved["product_key"]
    routing = route_task(task)
    skills = resolve_skills(task)
    authorization = authorize(task)
    if skills["status"] == "BLOCKED":
        task.execution = {"status": "BLOCKED", "reason": "No admitted skills were available for this task."}
    elif authorization["status"] != "AUTHORIZED":
        task.execution = {"status": "BLOCKED", "reason": authorization["reason"]}
    elif resolved.get("status") != "RESOLVED":
        task.execution = {"status": "BLOCKED", "reason": resolved.get("reason", "Product resolution failed.")}
    else:
        execute(task, resolved)
    verify(task)
    evidence = record(task)
    return {"product_resolution": resolved, "routing": routing, "skills": skills, "authorization": authorization, "verification": task.verification, "evidence": evidence}


def main():
    if len(sys.argv) < 2:
        print('Usage: python -m runtime.cli "task description" [product-key]')
        raise SystemExit(1)
    request = " ".join(sys.argv[1:])
    print(json.dumps(run(request), indent=2))


if __name__ == "__main__":
    main()
