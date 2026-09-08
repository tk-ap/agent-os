"""Low-cost autonomous ignition for the Milchik + Polly continuity pair.

Runs inside the existing fleet/Telegram tick. It does not decide new work and it
does not widen authority. When the fleet is genuinely idle, it may turn the
highest-ranked backlog item that is already human-origin or explicitly approved
into the same governed routing flow TK starts manually with /next.

Release-pending items are surfaced for Polly rather than treated as new build
work. External release mutation remains subject to its existing scoped grant.
"""
from __future__ import annotations

from pathlib import Path
import secrets
import time


ACTIVE_PHASES = {
    "queued", "running", "review", "waiting_approval", "waiting_capacity",
    "collision", "verifying", "reconciling",
}
ACTIVE_DIRECTIVE_STATES = {"captured", "routing"}


def _load_backlog(root: Path):
    import yaml
    from runtime import backlog as backlog_runtime

    items = yaml.safe_load((root / "agents/milchik/backlog.yaml").read_text()) or []
    return backlog_runtime.rank([item for item in items if item.get("status") != "done"])


def _fleet_busy(conn) -> bool:
    phases = ",".join("?" for _ in ACTIVE_PHASES)
    if conn.execute(f"SELECT 1 FROM agent_os_orders WHERE phase IN ({phases}) LIMIT 1",
                    tuple(sorted(ACTIVE_PHASES))).fetchone():
        return True
    states = ",".join("?" for _ in ACTIVE_DIRECTIVE_STATES)
    return bool(conn.execute(f"SELECT 1 FROM telegram_directives WHERE status IN ({states}) LIMIT 1",
                             tuple(sorted(ACTIVE_DIRECTIVE_STATES))).fetchone())


def _already_seen(conn, work_id: str) -> bool:
    # Any prior directive means the item already entered the governed flow.
    # A failed route is not silently retried forever; it needs evidence/repair.
    return bool(conn.execute(
        "SELECT 1 FROM telegram_directives WHERE backlog_work_id=? LIMIT 1", (work_id,)
    ).fetchone())


def _lease_valid(conn, item) -> bool:
    lease_id = item.get("objective_lease")
    if not lease_id:
        return True
    lease = conn.execute(
        "SELECT valid_until FROM objective_leases WHERE id=? AND revoked=0", (lease_id,)
    ).fetchone()
    return bool(lease and lease["valid_until"] > time.time())


def _cleared(item) -> bool:
    return item.get("source") == "human" or item.get("status") == "approved"


def _release_pending_card(conn, item) -> bool:
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
        "**Polly — approved work is not at a terminal release state**\n\n"
        f"**Work**\n{item.get('title', work_id)}\n\n"
        f"**Evidence**\n{evidence}\n\n"
        "The implementation record says the intended live state has not been verified. "
        "I am keeping this open rather than calling it done. A release may resume autonomously "
        "only when an existing scoped grant covers the exact push/deploy action; otherwise it "
        "remains human-required.\n\n"
        + (f"**Recorded note**\n{note[:900]}" if note else "")
    )
    conn.execute(
        "INSERT OR IGNORE INTO telegram_cards(id,event_key,expires,message,channel) VALUES (?,?,?,?,?)",
        (secrets.token_urlsafe(12), key, time.time() + 604800, text[:3900], "monitor"),
    )
    return True


def ignite(conn, root: Path) -> dict:
    """Start at most one already-cleared backlog item when nothing else is moving."""
    try:
        ranked = _load_backlog(root)
    except Exception as exc:
        return {"status": "blocked", "reason": f"backlog-unreadable:{type(exc).__name__}"}

    release_cards = sum(1 for item in ranked if _release_pending_card(conn, item))

    if _fleet_busy(conn):
        return {"status": "busy", "release_cards": release_cards}

    for item in ranked:
        work_id = item.get("work_id")
        if not work_id or item.get("status") == "release_pending":
            continue
        if not _cleared(item) or not _lease_valid(conn, item) or _already_seen(conn, work_id):
            continue

        title = str(item.get("title") or work_id)
        problem = str(item.get("problem") or title)
        conn.execute(
            "INSERT INTO telegram_directives(ts,text,backlog_work_id) VALUES (?,?,?)",
            (time.time(), (title + "\n\n" + problem)[:2000], work_id),
        )
        directive_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        key = f"milchik-auto-next:{work_id}:{directive_id}"
        text = (
            "**Milchik — starting cleared work without waiting for a prompt**\n\n"
            f"**Work**\n{title}\n\n"
            f"It is {item.get('priority',{}).get('level','p3')} and "
            f"{'human-origin' if item.get('source') == 'human' else 'already explicitly approved'}. "
            "The fleet was idle, so I moved it into the normal governed routing/review path. "
            "No new authority was created. I will come back when the state materially changes or someone needs a decision."
        )
        conn.execute(
            "INSERT OR IGNORE INTO telegram_cards(id,event_key,expires,message,channel) VALUES (?,?,?,?,?)",
            (secrets.token_urlsafe(12), key, time.time() + 604800, text[:3900], "monitor"),
        )
        conn.commit()
        return {"status": "started", "work_id": work_id, "directive_id": directive_id,
                "release_cards": release_cards}

    conn.commit()
    return {"status": "idle-no-cleared-work", "release_cards": release_cards}


def install(telegram):
    """Wrap the existing tick; control progress does not depend on message delivery."""
    base_tick = telegram.tick

    def tick(state=None, config_path=None, api=None):
        from .bridge import DEFAULT_STATE, ROOT, connect

        actual_state = state or DEFAULT_STATE
        conn = connect(actual_state)
        try:
            telegram.schema(conn)
            # Canonical board provenance must exist before the routing work item
            # is built. Unlike notification delivery, this part must work even
            # when Telegram is unavailable or disabled.
            telegram.sync_backlog_to_board(conn)
            continuity = ignite(conn, ROOT)
            if continuity.get("status") == "started":
                telegram.route_directives(conn, actual_state)
        finally:
            conn.close()

        kwargs = {"state": actual_state}
        if config_path is not None:
            kwargs["config_path"] = config_path
        if api is not None:
            kwargs["api"] = api
        result = base_tick(**kwargs)
        if isinstance(result, dict):
            result["continuity"] = continuity
        return result

    telegram.tick = tick
