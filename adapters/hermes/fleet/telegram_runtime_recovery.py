"""Repair continuity edge cases without deleting evidence or widening authority.

This module is deliberately narrow. It fixes two live-state failures found by the
first real Milchik autonomous ignition proof:

1. An open backlog item may still map to a Hermes mirror task that is already
   `done`. The old row remains evidence, but the open item needs a fresh blocked
   mirror before autonomous routing may use it as canonical provenance.
2. Commit collection may include Agent OS itself (or another registered product),
   while the legacy `record_change` helper only accepted two hard-coded product
   ids. Registered products are valid evidence sources; unknown products still
   fail closed.

A route_failed autonomous directive is retried only when its recorded failure is
specifically the stale-board-provenance error and that provenance has just been
repaired. The same directive id is reused; no duplicate work is manufactured.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

STALE_PROVENANCE_TEXT = (
    "autonomous backlog work must reference a live, non-done Hermes Kanban board item"
)


def _registered_change_products(root: Path) -> set[str]:
    import yaml

    registry = yaml.safe_load((root / "registry/product-routing.yaml").read_text()) or {}
    products = set((registry.get("products") or {}).keys())
    # Agent OS is operating infrastructure rather than a public product, but its
    # own repository is a legitimate configured commit-evidence source.
    products.update({"agent-os", "agent-os-workforce"})
    return products


def _replacement_key(work_id: str, prior_task_id: str) -> str:
    token = hashlib.sha256(prior_task_id.encode()).hexdigest()[:12]
    return f"agent-os-backlog:{work_id}:replacement:{token}"


def _recover_failed_directive(conn, work_id: str) -> int:
    """Re-capture the same directive only for the proven stale-provenance failure."""
    rows = conn.execute(
        """
        SELECT d.id
        FROM telegram_directives d
        JOIN telegram_cards c ON c.event_key = ('directive-failed:' || d.id)
        WHERE d.backlog_work_id=?
          AND d.status='route_failed'
          AND d.task_id IS NULL
          AND c.message LIKE ?
        ORDER BY d.id
        """,
        (work_id, f"%{STALE_PROVENANCE_TEXT}%"),
    ).fetchall()
    for row in rows:
        conn.execute("UPDATE telegram_directives SET status='captured' WHERE id=?", (row["id"],))
        # Keep the failure card as evidence but suppress delivery because the exact
        # condition it reported has now been repaired and the same directive is
        # being retried through the normal governed routing path.
        conn.execute(
            "UPDATE telegram_cards SET delivery='expired' WHERE event_key=? AND delivery='pending'",
            (f"directive-failed:{row['id']}",),
        )
    return len(rows)


def _repair_open_done_mirrors(telegram, conn) -> dict:
    """Replace stale done mirrors for backlog items that are still open."""
    import yaml
    from hermes_cli import kanban_db as kb
    from runtime import backlog as backlog_runtime

    root = Path(telegram.ROOT)
    items = yaml.safe_load((root / "agents/milchik/backlog.yaml").read_text()) or []
    open_by_id = {item["work_id"]: item for item in items if item.get("status") != "done"}

    repaired = retried = 0
    for work_id, item in open_by_id.items():
        mapped = conn.execute(
            "SELECT task_id FROM backlog_board_map WHERE work_id=?", (work_id,)
        ).fetchone()
        if not mapped:
            continue
        prior_task_id = mapped["task_id"]
        prior = kb.get_task(conn, prior_task_id)
        if prior is None or prior.status != "done":
            continue

        replacement_id = kb.create_task(
            conn,
            title=work_id,
            body=json.dumps(item),
            assignee="milchik",
            created_by="agent-os-backlog-sync",
            workspace_kind="dir",
            workspace_path=str(root),
            initial_status="blocked",
            idempotency_key=_replacement_key(work_id, prior_task_id),
            max_runtime_seconds=120,
            max_retries=0,
        )
        conn.execute(
            "INSERT OR REPLACE INTO backlog_board_map(work_id,task_id) VALUES (?,?)",
            (work_id, replacement_id),
        )
        conn.execute(
            "UPDATE tasks SET priority=? WHERE id=?",
            (int(backlog_runtime.attention_score(item)), replacement_id),
        )
        repaired += 1
        retried += _recover_failed_directive(conn, work_id)

    if repaired or retried:
        conn.commit()
    return {"repaired": repaired, "retried": retried}


def install(telegram) -> None:
    original_sync = telegram.sync_backlog_to_board

    def sync_backlog_to_board(conn):
        recovery = _repair_open_done_mirrors(telegram, conn)
        result = original_sync(conn)
        if isinstance(result, dict):
            result = dict(result)
            result["repaired_done_mirrors"] = recovery["repaired"]
            result["retried_stale_provenance_directives"] = recovery["retried"]
        return result

    def record_change(conn, product, kind, revision, summary):
        if kind not in {"commit", "deployment"}:
            raise ValueError("Unsupported product/change kind")
        if product not in _registered_change_products(Path(telegram.ROOT)):
            raise ValueError("Unsupported product/change kind")
        if not revision.strip() or len(revision) > 200:
            raise ValueError("A stable revision/deployment ID is required")
        conn.execute(
            "INSERT OR IGNORE INTO telegram_changes(product,kind,revision,summary) VALUES (?,?,?,?)",
            (product, kind, revision, telegram.short(summary)),
        )

    telegram.sync_backlog_to_board = sync_backlog_to_board
    telegram.record_change = record_change
