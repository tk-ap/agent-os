"""Translate governed blocker states into plain-language operator briefs.

Milchik should not make TK infer why autonomous work stopped from raw lifecycle
logs. This adapter emits idempotent private-chat cards for meaningful blocker
states and says whether AgentOS will retry automatically or needs a human action.
It observes existing authority/state only; it grants nothing and resumes nothing.
"""
from __future__ import annotations

import json
import secrets
import time


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


def _capacity_message(row):
    payload = _order_payload(row)
    owner = (payload.get("owning_agent") or row["owning_agent"] or "The assigned agent").replace("-", " ").title()
    harnesses = []
    try:
        harnesses = json.loads(row["harnesses"] or "[]")
    except (ValueError, TypeError):
        pass
    harness_text = ", ".join(harnesses) if harnesses else "the required execution harness"
    retry = "AgentOS will retry automatically when capacity returns."
    if row["next_at"] and row["next_at"] > time.time():
        retry = "AgentOS has parked the same task and will retry it automatically when its capacity window reopens."
    return (
        "**BLOCKED — execution capacity**\n\n"
        f"**Work**\n{_work_label(row)}\n\n"
        f"**What is stopping it**\n{owner} cannot continue because {harness_text} is currently unavailable or at capacity.\n\n"
        f"**What happens next**\n{retry}\n\n"
        "**What you need to do**\nNothing right now. You only need to step in if Milchik later asks for a specific approval, credential, or product decision."
    )


def _approval_message(row):
    return (
        "**BLOCKED — your approval is required**\n\n"
        f"**Work**\n{_work_label(row)}\n\n"
        "**What is stopping it**\nThe task reached a protected action boundary that AgentOS is not allowed to cross on its own.\n\n"
        "**What happens next**\nThe same task stays parked. It will not widen scope or continue past the protected action without a valid scoped grant.\n\n"
        "**What you need to do**\nReview the approval card in this chat and approve or deny the specific requested action."
    )


def _collision_message(row):
    return (
        "**BLOCKED — workspace collision**\n\n"
        f"**Work**\n{_work_label(row)}\n\n"
        "**What is stopping it**\nAgentOS detected overlapping live work on the same mutable surface and stopped rather than risk overwriting someone else's changes.\n\n"
        "**What happens next**\nThe task remains parked until the overlap is reconciled.\n\n"
        "**What you need to do**\nUse the collision card to resume after the workspace is reconciled, or deny/cancel the task."
    )


def _blocked_message(row):
    return (
        "**BLOCKED — execution stopped**\n\n"
        f"**Work**\n{_work_label(row)}\n\n"
        "**What is stopping it**\nThe worker could not continue under the current task envelope. This can mean a permission, authentication, capability, or execution failure.\n\n"
        "**What happens next**\nAgentOS will not pretend the work completed.\n\n"
        "**What you need to do**\nCheck the accompanying fleet/problem card for the recorded reason. If the system can safely retry on its own, Milchik will say so; otherwise it should ask for the exact missing input."
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
