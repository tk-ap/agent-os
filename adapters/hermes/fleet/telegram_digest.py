"""Milchik's periodic fleet digest.

The fleet reports itself one event at a time: a card when work parks, a card
when it finishes, a card when a decision is needed. That is the right shape for
something the operator must answer, and the wrong shape for knowing how the
workforce is doing. Read one at a time, a day of autonomous work arrives as a
stream of fragments that has to be reassembled by hand -- which is the babysitting
the fleet exists to remove.

This adapter emits one private card per period summarising what the workforce did,
what it handled on its own, what stopped, and what genuinely needs the operator.
It observes state and the lifecycle event feed; it decides nothing, resumes
nothing, and never widens a task's authority.

A digest is sent even when the period was quiet. Silence is ambiguous -- a healthy
idle fleet and a dead one look identical from the outside -- and the whole point is
that the operator can stop checking.
"""
from __future__ import annotations

import json
from collections import Counter
import secrets
import time

from .telegram_blocker_briefs import _work_label

DEFAULT_PERIOD = 86400
WATERMARK = "digest_last_at"
# Enough lines to be worth reading, few enough to stay a summary. Anything
# longer is the event stream again, wearing a digest's clothes.
MAX_ITEMS = 5
# Delivery truncates a card at 3900 characters and "Needs you" is deliberately
# last, so an unbounded directive could cut off the one section the operator
# must not miss. Bounding each label keeps the whole digest comfortably inside.
MAX_LABEL = 90


def _detail(row):
    try:
        value = json.loads(row["detail"] or "{}")
    except (ValueError, TypeError):
        return {}
    return value if isinstance(value, dict) else {}


def _label(conn, task_id):
    row = conn.execute("SELECT * FROM agent_os_orders WHERE task_id=?", (task_id,)).fetchone()
    text = str(_work_label(row) if row else task_id).strip()
    return text if len(text) <= MAX_LABEL else text[:MAX_LABEL - 1].rstrip() + "…"


def _bullets(items):
    shown = [f"  - {item}" for item in items[:MAX_ITEMS]]
    if len(items) > MAX_ITEMS:
        shown.append(f"  - ...and {len(items) - MAX_ITEMS} more")
    return "\n".join(shown)


def _plural(count, singular, plural=None):
    return f"{count} {singular if count == 1 else (plural or singular + 's')}"


def build_digest(conn, since, now):
    """Render the digest for the window, in the operator-communication order:
    what happened, what it cost the operator, what still needs them."""
    events = conn.execute(
        "SELECT * FROM agent_os_events WHERE ts>=? AND ts<? ORDER BY id", (since, now)
    ).fetchall()

    started = Counter()
    rotated, finished, stopped = [], [], []
    for event in events:
        detail = _detail(event)
        if event["kind"] == "start":
            started[detail.get("harness") or "unknown"] += 1
        elif event["kind"] == "result":
            result = detail.get("result") or "unknown"
            if result == "capacity":
                rotated.append(event["task_id"])
            elif result in {"permission", "authentication", "failed"}:
                stopped.append((event["task_id"], result))
        elif event["kind"] == "phase" and detail.get("phase") == "review":
            finished.append(event["task_id"])

    superseded = [e["task_id"] for e in events if e["kind"] == "superseded"]
    credited = [_detail(e).get("seconds", 0) for e in events if e["kind"] == "capacity_credit"]

    # Current state, not windowed: these are the things still true right now.
    needs_you = conn.execute(
        """SELECT o.task_id FROM agent_os_orders o WHERE o.phase='waiting_approval'"""
    ).fetchall()
    undecided = conn.execute(
        """SELECT task_id FROM telegram_cards
           WHERE decision IS NULL AND channel='private' AND task_id IS NOT NULL
             AND expires>?""", (now,)).fetchall()
    escalated = conn.execute(
        "SELECT task_id FROM agent_os_inspections WHERE verdict='escalated'").fetchall()
    blocked = conn.execute(
        "SELECT task_id FROM agent_os_orders WHERE phase='blocked'").fetchall()
    cooldowns = conn.execute(
        "SELECT harness, available_at FROM agent_os_capacity WHERE available_at>?",
        (now,)).fetchall()

    hours = max(1, int(round((now - since) / 3600)))
    lines = [f"**Milchik — fleet digest, last {_plural(hours, 'hour')}**", ""]

    # 1. What happened.
    if started:
        ran = ", ".join(f"{_plural(n, 'run')} on {harness}" for harness, n in started.most_common())
        lines.append(f"**What the workforce did**\n  {ran}.")
        if finished:
            lines.append(f"  {_plural(len(finished), 'piece')} of work reached review:")
            lines.append(_bullets([_label(conn, t) for t in dict.fromkeys(finished)]))
        lines.append("")
    else:
        lines.append("**What the workforce did**\n  Nothing ran. The queue was empty.\n")

    # 2. What it handled without the operator -- the reason a digest is enough.
    handled = []
    if rotated:
        handled.append(f"moved {_plural(len(rotated), 'task')} to another harness "
                       "when a provider hit its limit")
    if credited:
        banked = int(sum(credited) / 60)
        handled.append(f"protected {_plural(len(credited), 'mandate')} from expiring "
                       f"while parked, crediting about {_plural(banked, 'minute')}")
    if superseded:
        handled.append(f"closed {_plural(len(superseded), 'superseded attempt')} "
                       "that a revision had replaced")
    if handled:
        lines.append("**Handled without you**")
        lines.append("\n".join(f"  - {item.capitalize()}" for item in handled))
        lines.append("")

    # 3. What stopped, and whether it is waiting on time or on a person.
    if cooldowns:
        waits = [f"{row['harness']} until "
                 f"{time.strftime('%H:%M', time.localtime(row['available_at']))}"
                 for row in cooldowns]
        lines.append("**Waiting on provider capacity**\n  " + "; ".join(waits) +
                     ".\n  These resume on their own. Nothing to do.\n")
    if stopped or blocked:
        lines.append("**Stopped and not retrying**")
        detail_lines = [f"{_label(conn, task)} — {reason}" for task, reason in stopped]
        detail_lines += [f"{_label(conn, row['task_id'])} — blocked"
                         for row in blocked
                         if row["task_id"] not in {t for t, _ in stopped}]
        lines.append(_bullets(detail_lines))
        lines.append("  Permission and authentication failures never rotate to another\n"
                     "  harness on purpose: retrying them would just fail again.\n")

    # 4. What genuinely needs the operator, last and unmissable.
    pending = {row["task_id"] for row in needs_you} | {row["task_id"] for row in undecided} \
        | {row["task_id"] for row in escalated}
    if pending:
        lines.append(f"**Needs you — {_plural(len(pending), 'item')}**")
        lines.append(_bullets([_label(conn, task) for task in sorted(pending)]))
        lines.append("  Each has its own card in this chat with the decision and what\n"
                     "  changes either way.")
    else:
        lines.append("**Needs you**\n  Nothing. Everything either finished or is waiting on time.")

    return "\n".join(lines)


def collect_digest(conn, now=None, period=DEFAULT_PERIOD):
    """Emit at most one digest card per period. Returns the number created."""
    now = time.time() if now is None else now
    row = conn.execute("SELECT value FROM telegram_meta WHERE key=?", (WATERMARK,)).fetchone()
    try:
        last = float(row["value"]) if row else 0.0
    except (ValueError, TypeError):
        last = 0.0

    if last and now - last < period:
        return 0
    # First run has no window to report, so it establishes the watermark and
    # says nothing. A digest covering "all of history" would be noise.
    since = last or now
    if not last:
        conn.execute("INSERT OR REPLACE INTO telegram_meta VALUES (?,?)", (WATERMARK, str(now)))
        return 0

    key = f"digest:{int(now // period)}"
    if conn.execute("SELECT 1 FROM telegram_cards WHERE event_key=?", (key,)).fetchone():
        return 0
    conn.execute(
        """INSERT INTO telegram_cards(id,event_key,expires,message,channel)
           VALUES (?,?,?,?,'private')""",
        (secrets.token_urlsafe(12), key, now + 604800, build_digest(conn, since, now)))
    conn.execute("INSERT OR REPLACE INTO telegram_meta VALUES (?,?)", (WATERMARK, str(now)))
    return 1


def install(telegram) -> None:
    original_collect_fleet = telegram.collect_fleet

    def collect_fleet(conn):
        result = original_collect_fleet(conn)
        collect_digest(conn)
        return result

    telegram.collect_fleet = collect_fleet
