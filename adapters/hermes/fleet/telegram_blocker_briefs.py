"""Translate governed blocker states into conversational operator briefs.

Milchik should not make TK infer why autonomous work stopped from raw lifecycle
logs. This adapter emits idempotent private-chat cards for meaningful blocker
states and says what stopped, why, what the system is trying next, what safe
alternatives exist, and whether TK needs to do anything.

It also translates Polly's durable release-recovery states. Persistence is useful
only if the operator can tell whether the right action is approval, reconciliation,
a narrower execution plan, or simply time.

This layer observes existing authority/state only; it grants nothing, resumes
nothing, and never widens a harness's capability envelope just to make work move.
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

    # A restricted capability makes a harness ineligible for work that did not
    # ask for it, however well its other capabilities match. Enforcement lives
    # in enqueue; this has to agree with it, or Milchik reports the routing
    # working correctly as "a fleet-selection problem" and sends TK looking for
    # a bug that is the safety rule doing its job.
    restricted = set(binding.get("restricted_capabilities") or ())

    eligible = []
    ineligible = []
    for harness in configured:
        if harness in selected:
            continue
        caps = set((harnesses.get(harness) or {}).get("capabilities") or [])
        withheld = sorted(restricted & caps - needed)
        if withheld:
            ineligible.append((harness, [f"holds {c}, which this work did not request"
                                         for c in withheld]))
        elif needed <= caps:
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


def approval_card_covers(conn, row) -> bool:
    """Whether an approval card already asks TK about this exact parked task.

    A task parked at a protected boundary produced two private cards: the
    approval card with the decision and its buttons, and a blocker brief whose
    entire payload was "review the approval card in this chat". Two
    notifications, one of which exists only to point at the other.
    """
    if row["phase"] != "waiting_approval":
        return False
    return bool(conn.execute(
        "SELECT 1 FROM telegram_cards WHERE task_id=? AND event_key LIKE 'approval:%' LIMIT 1",
        (row["task_id"],)).fetchone())


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
        if approval_card_covers(conn, row):
            continue
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


def _polly_message(record):
    """Human explanation of one durable release-recovery state."""
    state = record.get("state") or "unknown"
    blocker = record.get("blocker") or {}
    reason = blocker.get("reason") or record.get("terminal_reason") or "No additional reason was recorded."
    work = record.get("work_id") or record.get("recovery_id") or "release recovery"
    policy = record.get("retry_policy") or {}
    next_check = policy.get("next_check_at")

    if state == "waiting_availability":
        what = "Polly is preserving the approved release because the external system is not currently available."
        next_step = "Polly will re-check availability without repeating the protected mutation."
        if next_check:
            next_step += f" The next recorded check is {next_check}."
        solutions = "The safest fix is usually time. If a provider-specific retry window exists, wait for it. Do not create a second deployment attempt manually unless reconciliation proves the first attempt did not happen."
        ask = "Nothing right now. Waiting is the correct action unless Milchik later asks for a specific decision."
    elif state == "reconciling":
        what = "Polly cannot safely tell whether the previous external action happened, so it has stopped before retrying."
        next_step = "The persistence layer is reconciling provider/live evidence first to avoid a duplicate push or deployment."
        solutions = "Check provider state, deployment IDs, branch/live revision, or other durable evidence. Retry only after the ambiguity is resolved."
        ask = "Usually nothing unless the evidence is inaccessible or contradictory; then Milchik should ask you for the exact missing access or decision."
    elif state == "verifying":
        what = "The release action may have completed, but Polly is not calling it done until the actual live state is independently verified."
        next_step = "W Dog or the configured verifier should check the user-facing/live result."
        solutions = "Wait for independent verification. If verification fails, route remediation instead of relabeling the release successful."
        ask = "Nothing unless verification reaches a protected action or requires access only you can provide."
    elif state == "human_required":
        what = "Polly reached a condition it is not authorized to resolve autonomously."
        next_step = "The release remains preserved and stopped; it will not manufacture new authority."
        solutions = "The exact fix depends on the recorded reason: renew/re-scope authority, resolve exhausted retry budget, provide missing access, or cancel/supersede the release."
        ask = "A human decision is required. Milchik should surface the exact scoped choice rather than asking for blanket permission."
    elif state in {"ready", "checking", "executing"}:
        what = "Polly is actively carrying the already-approved release toward a terminal state."
        next_step = "The persistence layer should continue under the existing grant and retry policy."
        solutions = "No intervention unless the state stops advancing or a new blocker is recorded."
        ask = "Nothing right now."
    else:
        what = f"Polly recorded release state `{state}`."
        next_step = "The durable record remains the source of truth across restarts."
        solutions = "Inspect the recorded blocker/retry policy before taking any manual action."
        ask = "Only act if Milchik identifies a specific human-owned decision."

    return (
        "**Milchik — Polly persistence update**\n\n"
        f"**Work**\n{work}\n\n"
        f"**What is happening**\n{what}\n\n"
        f"**Why**\n{reason}\n\n"
        f"**What happens next**\n{next_step}\n\n"
        f"**What may fix it**\n{solutions}\n\n"
        f"**What I need from you**\n{ask}"
    )


def _fleet_state_root(conn):
    try:
        rows = conn.execute("PRAGMA database_list").fetchall()
        for row in rows:
            path = row[2]
            if path:
                return Path(path).resolve().parent
    except Exception:
        return None
    return None


def collect_polly_briefs(conn):
    """Surface non-terminal Polly records when the canonical fleet store exists."""
    from runtime import release_recovery

    state_root = _fleet_state_root(conn)
    if state_root is None:
        return 0
    recovery_root = state_root / "release-recovery"
    if not recovery_root.exists():
        return 0

    store = release_recovery.RecoveryStore(recovery_root)
    created = 0
    for record in store.all():
        if release_recovery.is_terminal(record) and record.get("state") != "human_required":
            continue
        key = "polly-state:{}:{}:{}".format(
            record.get("recovery_id", "unknown"),
            record.get("state", "unknown"),
            record.get("updated_at", "unknown"),
        )
        if conn.execute("SELECT 1 FROM telegram_cards WHERE event_key=?", (key,)).fetchone():
            continue
        conn.execute(
            """INSERT INTO telegram_cards
               (id,event_key,expires,message,channel)
               VALUES (?,?,?,?,'private')""",
            (secrets.token_urlsafe(12), key, time.time() + 604800, _polly_message(record)[:3900]),
        )
        created += 1
    return created


def _install_release_pending_renderer():
    """Upgrade the existing coarse release-pending notice into operator guidance."""
    from . import telegram_operational_continuity as continuity

    def release_pending_card(conn, item):
        if item.get("status") != "release_pending":
            return False
        work_id = item.get("work_id", "unknown")
        completed = item.get("completed") or {}
        evidence = str(completed.get("evidence") or "release artifact recorded")
        key = f"polly-release-pending:{work_id}:{evidence[:120]}"
        if conn.execute("SELECT 1 FROM telegram_cards WHERE event_key=?", (key,)).fetchone():
            return False
        note = str(completed.get("note") or item.get("notes") or "")
        text = (
            "**Milchik — Polly is holding this release open**\n\n"
            f"**Work**\n{item.get('title', work_id)}\n\n"
            f"**What I know**\n{evidence}\n\n"
            "**What is happening**\nThe implementation exists, but the intended live state is not independently verified, so Polly is preserving this as unfinished instead of calling it done.\n\n"
            "**What may fix it**\nIf the exact push/deploy is already covered by a still-valid scoped grant, Polly may resume it. If capacity or provider availability is the blocker, waiting may be the correct fix. If the prior external result is ambiguous, reconcile before retrying. If authority is missing or expired, Milchik should ask you for the exact scope required.\n\n"
            "**What I need from you**\nNothing unless I send a specific approval/access decision. Do not manually repeat the release just because it is taking time."
            + (f"\n\n**Recorded note**\n{note[:700]}" if note else "")
        )
        conn.execute(
            "INSERT OR IGNORE INTO telegram_cards(id,event_key,expires,message,channel) VALUES (?,?,?,?,?)",
            (secrets.token_urlsafe(12), key, time.time() + 604800, text[:3900], "monitor"),
        )
        return True

    continuity._release_pending_card = release_pending_card


def install(telegram) -> None:
    original_collect_fleet = telegram.collect_fleet
    _install_release_pending_renderer()

    def collect_fleet(conn):
        result = original_collect_fleet(conn)
        collect_blocker_briefs(conn)
        collect_polly_briefs(conn)
        return result

    telegram.collect_fleet = collect_fleet
