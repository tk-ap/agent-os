"""Translate governed blocker states into conversational operator briefs.

Milchik should not make TK infer why autonomous work stopped from raw lifecycle
logs. This adapter emits idempotent private-chat cards for meaningful blocker
states and says what stopped, why, what the system is trying next, what safe
alternatives exist, and whether TK needs to do anything.

It observes existing authority/state only; it grants nothing, resumes nothing,
and never widens a harness's capability envelope just to make a task move.
"""
from __future__ import annotations

import json
from pathlib import Path
import secrets
import time

ROOT = Path(__file__).resolve().parents[3]


def _order_payload(row):
    try:
        value = json.loads(row["payload"] or "{}")
    except (ValueError, TypeError):
        return {}
    return value if isinstance(value, dict) else {}


def _work_label(row):
    payload = _order_payload(row)
    problem = payload.get("problem_or_opportunity") or {}
    if isinstance(problem, dict):
        directive = problem.get("directive") or problem.get("statement")
        if directive:
            return str(directive).strip().splitlines()[0]
    return payload.get("work_id") or row["work_id"] or row["task_id"]


def _harness_context(row):
    """Explain why another configured harness can or cannot take the same task."""
    payload = _order_payload(row)
    needed = set(payload.get("required_capabilities") or [])
    try:
        selected = list(json.loads(row["harnesses"] or "[]"))
    except (ValueError, TypeError):
        selected = []

    try:
        import yaml
        registry = yaml.safe_load((ROOT / "registry/harnesses.yaml").read_text()) or {}
        binding = ((registry.get("execution_bindings") or {}).get("hermes-fleet") or {})
        configured = list(binding.get("harnesses") or [])
        harnesses = registry.get("harnesses") or {}
    except (OSError, ImportError, ValueError, TypeError):
        return selected, needed, [], []

    eligible = []
    ineligible = []
    for harness in configured:
        if harness in selected:
            continue
        caps = set((harnesses.get(harness) or {}).get("capabilities") or [])
        if needed <= caps:
            eligible.append(harness)
        else:
            ineligible.append((harness, sorted(needed - caps)))
    return selected, needed, eligible, ineligible


def _capacity_message(row):
    payload = _order_payload(row)
    owner = (payload.get("owning_agent") or row["owning_agent"] or "The assigned agent").replace("-", " ").title()
    selected, needed, eligible, ineligible = _harness_context(row)
    harness_text = ", ".join(selected) if selected else "the required execution harness"

    if row["next_at"] and row["next_at"] > time.time():
        retry = "AgentOS has parked the same task and will retry it automatically when its capacity window reopens."
    else:
        retry = "AgentOS will retry the same task automatically when capacity returns."

    if eligible:
        alternate = (
            "A second configured harness appears to cover the same declared capabilities: "
            + ", ".join(eligible)
            + ". If AgentOS does not rotate to it, that is a fleet-selection problem Milchik should surface rather than leave silent."
        )
    elif ineligible:
        details = "; ".join(
            f"{name} is missing {', '.join(missing)}" for name, missing in ineligible
        )
        alternate = (
            "The other configured harnesses were considered but are not eligible for this exact task envelope. "
            + details
            + ". Safe options are: wait for the eligible harness; narrow the declared capabilities if they were over-stated; or split the work so a narrower subtask can move on another harness. Do not widen permissions just to bypass capacity."
        )
    else:
        alternate = (
            "No safe alternate harness is currently recorded for this exact task envelope. The safe default is to wait, unless the task can be narrowed or split without changing its approved outcome."
        )

    required_text = ", ".join(sorted(needed)) if needed else "no special capability beyond the task record"
    return (
        "**Milchik — the team is blocked, but the work is preserved**\n\n"
        f"{owner} cannot continue **{_work_label(row)}** because {harness_text} is currently unavailable or at capacity. "
        f"This task declares: {required_text}.\n\n"
        f"**What the system is doing**\n{retry}\n\n"
        f"**Other ways this could move**\n{alternate}\n\n"
        "**What I need from you**\nNothing right now. Waiting is a valid action here. I will ask only if the safe next step requires a specific approval, credential, product decision, or a deliberate change to the execution plan."
    )


def _approval_message(row):
    return (
        "**Milchik — the team hit a boundary only you can clear**\n\n"
        f"The work **{_work_label(row)}** reached a protected action that AgentOS is not allowed to cross on its own.\n\n"
        "**What the system is doing**\nThe same task is parked with its current evidence intact. It will not widen scope or continue past the protected action without a valid scoped grant.\n\n"
        "**Possible fix**\nApprove the exact requested scope if you want it to continue; otherwise deny it and the task stops cleanly.\n\n"
        "**What I need from you**\nReview the approval card in this chat."
    )


def _collision_message(row):
    return (
        "**Milchik — two pieces of work are in each other's way**\n\n"
        f"AgentOS paused **{_work_label(row)}** before touching files because another live context overlaps the same mutable surface.\n\n"
        "**What the system is doing**\nThe task stays parked so neither side silently overwrites the other.\n\n"
        "**Possible fixes**\nWait for the other context to finish, split the mutable surfaces, or reconcile the workspace and then resume the same task.\n\n"
        "**What I need from you**\nNothing if the other work is expected to finish soon. Otherwise use the collision card when you know the overlap is resolved."
    )


def _blocked_message(row):
    return (
        "**Milchik — execution stopped and needs a diagnosis**\n\n"
        f"The worker could not continue **{_work_label(row)}** under the current task envelope. This can mean permission, authentication, capability, or execution failure.\n\n"
        "**What the system is doing**\nAgentOS is keeping the task and evidence open instead of pretending it completed.\n\n"
        "**Possible fixes**\nThe next safe move depends on the recorded failure: retry automatically if transient; use another eligible harness if one exists; request the exact missing access if authority is the issue; or narrow/split the task if its capability envelope is too broad. Sometimes the correct answer is simply to wait.\n\n"
        "**What I need from you**\nCheck the accompanying problem card only if Milchik says human input is required. Otherwise the system should continue or come back with a more specific ask."
    )


def collect_blocker_briefs(conn):
    """Emit one private blocker card per meaningful state transition/attempt."""
    rows = conn.execute(
        """SELECT * FROM agent_os_orders
           WHERE phase IN ('waiting_capacity','waiting_approval','collision','blocked')
           ORDER BY rowid"""
    ).fetchall()
    created = 0
    for row in rows:
        phase = row["phase"]
        # attempts makes a later retry/failure eligible for a fresh brief while
        # keeping repeated minute ticks idempotent for the same stalled state.
        key = f"blocker:{row['task_id']}:{phase}:{row['attempts']}"
        if conn.execute("SELECT 1 FROM telegram_cards WHERE event_key=?", (key,)).fetchone():
            continue
        if phase == "waiting_capacity":
            message = _capacity_message(row)
        elif phase == "waiting_approval":
            message = _approval_message(row)
        elif phase == "collision":
            message = _collision_message(row)
        else:
            message = _blocked_message(row)
        conn.execute(
            """INSERT INTO telegram_cards
               (id,event_key,task_id,expires,message,channel)
               VALUES (?,?,?,?,?,'private')""",
            (secrets.token_urlsafe(12), key, row["task_id"], time.time() + 604800, message),
        )
        created += 1
    return created


def install(telegram) -> None:
    original_collect_fleet = telegram.collect_fleet

    def collect_fleet(conn):
        result = original_collect_fleet(conn)
        collect_blocker_briefs(conn)
        return result

    telegram.collect_fleet = collect_fleet
