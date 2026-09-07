"""Human-first monitor-channel rendering for Milchik.

This module changes presentation only. It does not grant authority, resume work,
or mutate approval state beyond the same read-only monitor-card inserts already
performed by the base Telegram runtime.
"""
import json
import re
import secrets
import time


def _title(agent):
    return (agent or "Workforce").replace("-", " ").title()


def _order(payload):
    try:
        value = json.loads(payload or "{}")
        return value if isinstance(value, dict) else {}
    except ValueError:
        return {}


def _clean(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _full_directive(order):
    problem = order.get("problem_or_opportunity") or {}
    if isinstance(problem, dict):
        return _clean(problem.get("directive"))
    return ""


def _display_problem(order, work_id, limit=360):
    """Readable monitor summary only; never used as the worker's work order."""
    directive = _full_directive(order)
    if directive:
        if len(directive) <= limit:
            return directive, False
        # Prefer a sentence boundary so the monitor does not look accidentally cut off.
        candidate = directive[:limit]
        boundary = max(candidate.rfind(". "), candidate.rfind("? "), candidate.rfind("! "))
        if boundary >= 120:
            candidate = candidate[: boundary + 1]
        return candidate.rstrip() + " …", True
    if work_id.endswith("-routing"):
        return "Choose the best owner for the requested work.", False
    if work_id.endswith("-inspection"):
        return "Independently review the completed work.", False
    return _clean(str(work_id).replace("-", " "))[:limit], False


def _outcome_text(order, limit=220):
    outcome = order.get("desired_outcome")
    if isinstance(outcome, dict):
        for key in ("summary", "outcome", "description", "goal", "result"):
            if outcome.get(key):
                text = _clean(outcome[key])
                return text if len(text) <= limit else text[: limit - 2].rstrip() + " …"
        # Keep this legible when the contract uses a product-specific object.
        pieces = []
        for key, value in outcome.items():
            if isinstance(value, (str, int, float, bool)):
                pieces.append(f"{str(key).replace('_', ' ')}: {_clean(value)}")
        if pieces:
            text = "; ".join(pieces)
            return text if len(text) <= limit else text[: limit - 2].rstrip() + " …"
    elif outcome:
        text = _clean(outcome)
        return text if len(text) <= limit else text[: limit - 2].rstrip() + " …"
    return "The requested outcome is stored in the full work order."


def _context_integrity(order, shortened=False):
    criteria = order.get("acceptance_criteria") or []
    refs = order.get("context_references") or []
    evidence = order.get("evidence") or []
    full = bool(order and order.get("problem_or_opportunity") and order.get("desired_outcome"))
    lines = [
        "**Context check**",
        f"Full work order attached: **{'Yes' if full else 'No'}**",
        f"Acceptance criteria attached: **{len(criteria) if isinstance(criteria, list) else 0}**",
        f"Context references attached: **{len(refs) if isinstance(refs, list) else 0}**",
    ]
    if isinstance(evidence, list) and evidence:
        lines.append(f"Evidence items attached: **{len(evidence)}**")
    if shortened:
        lines.append("Telegram summary shortened for display: **Yes**")
    lines.append("The worker receives the stored full work order; this Telegram text is display-only.")
    return "\n".join(lines)


def _work_context(payload, work_id):
    order = _order(payload)
    problem, shortened = _display_problem(order, work_id)
    return order, problem, shortened


def _assignment_message(order, problem, shortened):
    return (
        "**FYI — work assignment is being prepared**\n\n"
        "**Problem**\n"
        f"{problem}\n\n"
        "**Expected outcome**\n"
        f"{_outcome_text(order)}\n\n"
        f"{_context_integrity(order, shortened)}"
    )


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
            order, problem, shortened = _work_context(row_["payload"], work_id)
            kinds = [event["kind"] for event, _ in group]
            details = [detail for _, detail in group]
            results = [str(d.get("result", "")).lower() for d in details if d.get("result")]
            phases = [str(d.get("phase", "")).lower() for d in details if d.get("phase")]

            permission = "permission" in results or row_["phase"] == "waiting_approval"
            if permission:
                text = (
                    f"**Decision required — {agent} needs permission to continue**\n\n"
                    f"**Problem**\n{problem}\n\n"
                    "The agent reached a protected action and stopped before crossing that boundary. "
                    "Check your private Milchik chat for the approval request.\n\n"
                    f"{_context_integrity(order, shortened)}"
                )
            elif "start" in kinds or "claim" in kinds:
                if work_id.endswith("-routing"):
                    text = _assignment_message(order, problem, shortened)
                elif work_id.endswith("-inspection"):
                    text = (
                        "**FYI — independent review started**\n\n"
                        f"W Dog is checking the work against the stored acceptance criteria.\n\n"
                        f"**Problem being checked**\n{problem}\n\n"
                        f"{_context_integrity(order, shortened)}"
                    )
                else:
                    text = (
                        f"**FYI — {agent} started the work**\n\n"
                        f"**Problem**\n{problem}\n\n"
                        f"**Expected outcome**\n{_outcome_text(order)}\n\n"
                        f"{_context_integrity(order, shortened)}"
                    )
            elif "review" in phases:
                if work_id.endswith("-inspection"):
                    text = "**FYI — independent review finished**\n\nThe check is complete. The work it reviewed can now move to the next decision."
                else:
                    text = (
                        f"**FYI — {agent} finished this step**\n\n"
                        f"**Problem**\n{problem}\n\n"
                        "It is being checked independently before you are asked to approve anything.\n\n"
                        f"{_context_integrity(order, shortened)}"
                    )
            elif "done" in phases:
                text = f"**FYI — {agent}'s work is complete**\n\n**Problem**\n{problem}\n\n{_context_integrity(order, shortened)}"
            elif "blocked" in phases or "revoked" in phases:
                text = (
                    f"**Problem — {agent}'s work stopped**\n\n"
                    f"**Work being attempted**\n{problem}\n\n"
                    "The workforce could not continue. Check the private Milchik chat for the reason or required decision.\n\n"
                    f"{_context_integrity(order, shortened)}"
                )
            elif "queued" in kinds:
                text = (
                    f"**FYI — work queued for {agent}**\n\n"
                    f"**Problem**\n{problem}\n\n"
                    f"{_context_integrity(order, shortened)}"
                )
            else:
                continue

            key = f"fleet-human:{task_id}:{group[-1][0]['id']}"
            conn.execute(
                "INSERT OR IGNORE INTO telegram_cards(id,event_key,expires,message,channel) VALUES (?,?,?,?,?)",
                (secrets.token_urlsafe(12), key, time.time() + 86400, text[:3900], "monitor"),
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
            if work_id.endswith("-inspection") or work_id.endswith("-routing"):
                continue
            order, problem, shortened = _work_context(row["payload"], work_id)
            agent = _title(row["owning_agent"])
            integrity = _context_integrity(order, shortened)
            if row["phase"] == "waiting_approval":
                text = f"**Decision required — {agent} is waiting on you**\n\n**Problem**\n{problem}\n\nA protected action needs approval before work can continue.\n\n{integrity}"
            elif row["phase"] == "review":
                text = f"**FYI — {agent} finished a bounded piece of work**\n\n**Problem**\n{problem}\n\nIt is in the review process.\n\n{integrity}"
            elif row["phase"] == "done":
                text = f"**FYI — {agent} completed the work**\n\n**Problem**\n{problem}\n\n{integrity}"
            else:
                text = f"**Problem — {agent} could not continue**\n\n**Work being attempted**\n{problem}\n\n{integrity}"
            conn.execute(
                "INSERT OR IGNORE INTO telegram_cards(id,event_key,expires,message,channel) VALUES (?,?,?,?,?)",
                (secrets.token_urlsafe(12), key, time.time() + 604800, text[:3900], "monitor"),
            )

    base.collect_fleet = collect_fleet
    base.collect_contributions = collect_contributions
    telegram.collect_fleet = collect_fleet
    telegram.collect_contributions = collect_contributions
