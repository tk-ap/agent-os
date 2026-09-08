from pathlib import Path
import re

from runtime.task import Task

ROOT = Path(__file__).resolve().parents[1]
AGENTS_FILE = ROOT / "registry" / "agents.yaml"


def _load_agents():
    text = AGENTS_FILE.read_text()
    agents = {}
    current = None
    for line in text.splitlines():
        m = re.match(r"^  ([a-z0-9-]+):\s*$", line)
        if m:
            current = m.group(1)
            agents[current] = {}
            continue
        if current:
            m = re.match(r"^    role:\s*(.+)$", line)
            if m:
                agents[current]["role"] = m.group(1).strip()
            m = re.match(r"^    owns:\s*\[(.*)\]$", line)
            if m:
                agents[current]["owns"] = [x.strip().strip("'\"") for x in m.group(1).split(",") if x.strip()]
    return agents


def _independent_verifier_for(task: Task, agents: dict):
    ctx = task.verification_context or {}
    ineligible = set(ctx.get("authors", [])) | set(ctx.get("remediators", [])) | set(ctx.get("material_participants", []))
    candidates = ctx.get("candidate_verifiers") or ["w-dog", "rook"]
    for candidate in candidates:
        if candidate in agents and candidate not in ineligible:
            return candidate
    raise RuntimeError("No eligible Independent Verifier is available; verification must remain BLOCKED")


def _owner_for(task: Task, agents: dict):
    if task.task_class == "verification":
        return _independent_verifier_for(task, agents)
    if task.task_class == "implementation":
        return "eugene"
    if task.task_class == "inspection":
        return "w-dog"
    return "router"


def route_task(task: Task):
    agents = _load_agents()
    agent = _owner_for(task, agents)
    if agent not in agents:
        raise RuntimeError(f"Agent '{agent}' is not present in registry/agents.yaml")
    task.agent = agent
    if task.task_class == "verification":
        return {
            "task": task.to_dict(),
            "agent": agent,
            "role": "Independent Verifier",
            "ownership": ["independent-verification", "provider-readback", "attestation"],
            "mode": "INDEPENDENT VERIFICATION",
        }
    return {
        "task": task.to_dict(),
        "agent": agent,
        "role": agents[agent].get("role"),
        "ownership": agents[agent].get("owns", []),
        "mode": "AUTONOMOUS + AUDIT",
    }
