"""One-time presentation migration for active blocker briefs.

PR #62 changed blocker messaging from terse lifecycle labels to conversational
operator guidance. Existing cards are intentionally idempotent, so a currently
blocked task could otherwise keep the old terse card forever until its next
attempt/state transition. This adapter emits exactly one refreshed v2 card for
active blockers without mutating task state or authority.
"""
from __future__ import annotations

import secrets
import time

from . import telegram_blocker_briefs as briefs


def collect_refresh_cards(conn):
    rows = conn.execute(
        """SELECT * FROM agent_os_orders
           WHERE phase IN ('waiting_capacity','waiting_approval','collision','blocked')
           ORDER BY rowid"""
    ).fetchall()
    created = 0
    for row in rows:
        phase = row["phase"]
        key = f"blocker-conversational-v2:{row['task_id']}:{phase}:{row['attempts']}"
        if conn.execute("SELECT 1 FROM telegram_cards WHERE event_key=?", (key,)).fetchone():
            continue
        if phase == "waiting_capacity":
            message = briefs._capacity_message(row)
        elif phase == "waiting_approval":
            message = briefs._approval_message(row)
        elif phase == "collision":
            message = briefs._collision_message(row)
        else:
            message = briefs._blocked_message(row)
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
        collect_refresh_cards(conn)
        return result

    telegram.collect_fleet = collect_fleet
