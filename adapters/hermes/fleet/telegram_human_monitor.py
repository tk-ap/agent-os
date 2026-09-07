"""Human-first monitor-channel rendering for Milchik.

This module changes presentation only. It does not grant authority, resume work,
or mutate approval state beyond the same read-only monitor-card inserts already
performed by the base Telegram runtime.
"""
import json
import secrets
import time


def _title(agent):
    return (agent or "Workforce").replace("-", " ").title()


def _work_summary(payload, work_id):
    try:
        order = json.loads(payload or "{}")
    except ValueError:
        order = {}
    problem = order.get("problem_or_opportunity") or {}
    directive = problem.get("directive") if isinstance(problem, dict) else None
    if directive:
        return str(directive).strip().splitlines()[0][:140]
    if work_id.endswith("-routing"):
        return "Choose who should own the requested work"
    if work_id.endswith("-inspection"):
        return "Independent review of completed work"
    return str(work_id).replace("-", " ")[:140]


def install(telegram):
    base = telegram.base

    def collect_fleet(conn):
        row = conn.execute("SELECT value FROM telegram_meta WHERE key='fleet_watermark'").fetchone()
        watermark = int(row[0]) if row else 0
        events = conn.execute(
            "SELECT id,ts,task_id,kind,detail FROM agent_os_events WHERE id>? ORDER BY id",
            (watermark,),
        ).fetchall()
        if not events:
            return

        by_task = {}
        for event in events:
            try:
                detail = json.loads(event["detail"]) if event["detail"] else {}
            except ValueError:
                detail = {}
            by_task.setdefault(event["task_id"], []).append((event, detail))

        for task_id, group in by_task.items():
            row_ = conn.execute(
                "SELECT work_id,owning_agent,payload,phase FROM agent_os_orders WHERE task_id=?",
                (task_id,),
            ).fetchone()
            if not row_:
                continue
            work_id = row_["work_id"] or task_id
            agent = _title(row_["owning_agent"])
            summary = _work_summary(row_["payload"], work_id)
            kinds = [event["kind"] for event, _ in group]
            details = [detail for _, detail in group]
            results = [str(d.get("result", "")).lower() for d in details if d.get("result")]
            phases = [str(d.get("phase", "")).lower() for d in details if d.get("phase")]

            permission = "permission" in results or row_["phase"] == "waiting_approval"
            if permission:
                text = (
                    f"**Decision required — {agent} needs permission to continue**\n\n"
                    f"{agent} reached a protected action while working on: {summary}.\n\n"
                    "The work stopped before crossing that boundary. Check your private Milchik chat for the approval request."
                )
            elif "start" in kinds or "claim" in kinds:
                if work_id.endswith("-routing"):
                    text = f"**FYI — work assignment is being prepared**\n\nRouter is deciding who should own: {summary}."
                elif work_id.endswith("-inspection"):
                    text = f"**FYI — independent review started**\n\nW Dog is checking: {summary}."
                else:
                    text = f"**FYI — {agent} started the work**\n\n{summary}"
            elif "review" in phases:
                if work_id.endswith("-inspection"):
                    text = "**FYI — independent review finished**\n\nThe check is complete. The work it reviewed can now move to the next decision."
                else:
                    text = f"**FYI — {agent} finished this step**\n\n{summary}\n\nIt is being checked independently before you are asked to approve anything."
            elif "done" in phases:
                text = f"**FYI — {agent}'s work is complete**\n\n{summary}"
            elif "blocked" in phases or "revoked" in phases:
                text = f"**Problem — {agent}'s work stopped**\n\n{summary}\n\nThe workforce could not continue. Check the private Milchik chat for the reason or required decision."
            elif "queued" in kinds:
                text = f"**FYI — work queued for {agent}**\n\n{summary}"
            else:
                continue

            key = f"fleet-human:{task_id}:{group[-1][0]['id']}"
            conn.execute(
                "INSERT OR IGNORE INTO telegram_cards(id,event_key,expires,message,channel) VALUES (?,?,?,?,?)",
                (secrets.token_urlsafe(12), key, time.time() + 86400, text, "monitor"),
            )

        conn.execute(
            "INSERT OR REPLACE INTO telegram_meta VALUES ('fleet_watermark',?)",
            (str(events[-1]["id"]),),
        )

    def collect_contributions(conn, state):
        """Keep monitor evidence useful without duplicating raw worker transcripts."""
        rows = conn.execute("SELECT * FROM agent_os_orders WHERE phase IN ('review','done','blocked','waiting_approval')").fetchall()
        for row in rows:
            key = f"contribution-human:{row['task_id']}:{row['attempts']}"
            if conn.execute("SELECT 1 FROM telegram_cards WHERE event_key=?", (key,)).fetchone():
                continue
            work_id = row["work_id"] or row["task_id"]
            # Inspector/routing internals are already represented by concise fleet messages
            # and private review cards. Do not dump their raw checkpoint prose into monitor.
            if work_id.endswith("-inspection") or work_id.endswith("-routing"):
                continue
            summary = _work_summary(row["payload"], work_id)
            agent = _title(row["owning_agent"])
            if row["phase"] == "waiting_approval":
                text = f"**Decision required — {agent} is waiting on you**\n\n{summary}\n\nA protected action needs approval before work can continue."
            elif row["phase"] == "review":
                text = f"**FYI — {agent} finished a bounded piece of work**\n\n{summary}\n\nIt is in the review process; no raw logs are needed here."
            elif row["phase"] == "done":
                text = f"**FYI — {agent} completed the work**\n\n{summary}"
            else:
                text = f"**Problem — {agent} could not continue**\n\n{summary}"
            conn.execute(
                "INSERT OR IGNORE INTO telegram_cards(id,event_key,expires,message,channel) VALUES (?,?,?,?,?)",
                (secrets.token_urlsafe(12), key, time.time() + 604800, text, "monitor"),
            )

    base.collect_fleet = collect_fleet
    base.collect_contributions = collect_contributions
    telegram.collect_fleet = collect_fleet
    telegram.collect_contributions = collect_contributions
