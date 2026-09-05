from pathlib import Path
import re
from runtime.task import Task

ROOT = Path(__file__).resolve().parents[1]
SKILLS_FILE = ROOT / "registry" / "skills.yaml"

TASK_SKILLS = {
    "inspection": ["end-to-end-verification", "audit-evidence-ledger"],
    "implementation": ["task-envelope", "end-to-end-verification"],
    "general": ["task-envelope"],
}


def _load_skill_states():
    text = SKILLS_FILE.read_text()
    states = {}
    current = None
    for line in text.splitlines():
        m = re.match(r"^  ([a-z0-9][a-z0-9-]*):\s*$", line)
        if m:
            current = m.group(1)
            continue
        if current:
            m = re.match(r"^\s{4}trust:\s*([a-z_]+)", line)
            if m:
                states[current] = m.group(1)
    return states


def resolve_skills(task: Task):
    states = _load_skill_states()
    requested = TASK_SKILLS.get(task.task_class, TASK_SKILLS["general"])
    admitted, rejected = [], []
    for skill in requested:
        state = states.get(skill)
        if state in {"owned", "approved"}:
            admitted.append(skill)
        else:
            rejected.append({"skill": skill, "reason": f"Skill trust state is '{state or 'unknown'}'; only owned or approved skills may execute."})
    task.skills = admitted
    return {"skills": admitted, "rejected": rejected, "status": "RESOLVED" if admitted else "BLOCKED"}
