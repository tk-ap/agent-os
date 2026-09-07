"""Read-only progressive-disclosure implementation for Milchik Explain.

Kept separate so the presentation adapter cannot accidentally reuse the routing
persistence helper while rendering an explanation. Reading an explanation must
never mutate task, routing, approval, or publication state.
"""
import json
from pathlib import Path


def install(human):
    base = human.base

    def technical_details(conn, card, state):
        row = base.order_row(conn, card["task_id"]) if card["task_id"] else None
        if not row:
            return "There are no additional task details available for this message."
        try:
            order = json.loads(row["payload"])
        except ValueError:
            order = {}

        record_path = Path(state) / row["task_id"] / f"{row['attempts']}.json"
        checkpoint = {}
        if record_path.exists():
            try:
                record = json.loads(record_path.read_text())
                checkpoint = json.loads(record.get("checkpoint_text", "{}"))
            except ValueError:
                pass

        # Read only: prefer the already-persisted routing proposal. If none is
        # present, inspect the checkpoint copy without inserting anything.
        proposal = None
        stored = conn.execute(
            "SELECT proposal FROM routing_proposals WHERE task_id=?", (row["task_id"],)
        ).fetchone()
        if stored:
            try:
                proposal = json.loads(stored[0])
            except ValueError:
                proposal = None
        if proposal is None and isinstance(checkpoint.get("proposal"), dict):
            proposal = checkpoint["proposal"]

        inspection = conn.execute(
            "SELECT * FROM agent_os_inspections WHERE task_id=?", (row["task_id"],)
        ).fetchone()

        lines = ["**Explanation**"]
        if proposal and proposal.get("owning_agent"):
            owner = str(proposal["owning_agent"]).replace("-", " ").title()
            lines.append(
                f"This is a work-assignment decision. {owner} was selected as the agent responsible. "
                "Approving creates the next governed work item; it does not publish or deploy anything."
            )
        else:
            lines.append(
                "This is a review gate: the workforce finished a bounded piece of work and is waiting "
                "for your decision before closing it."
            )

        lines.extend(["", "**Independent review**"])
        if inspection:
            readable = {
                "pass": "Review passed.",
                "fail": "Review found problems.",
                "stale": "The earlier review no longer matches the current files.",
                "unreadable": "The reviewer did not return a reliable yes/no verdict.",
                "unavailable": "The independent review could not run.",
            }.get(inspection["verdict"], str(inspection["verdict"]))
            lines.append(readable)
            if inspection["failed"]:
                lines.append(base.short(inspection["failed"], 900))
        else:
            lines.append("No independent review record is available.")

        lines.extend([
            "",
            "**Technical details**",
            f"Task ID: `{row['task_id']}`",
            f"Work ID: `{base.short(row['work_id'], 120)}`",
            f"Agent responsible: `{row['owning_agent'] or 'unattributed'}`",
            f"Product: `{order.get('owning_product', 'unknown')}`",
            f"Evidence folder: `{record_path.parent}`",
            "",
            "Technical term: the work is at a **review gate** — completed by the worker, but not yet accepted by you.",
        ])
        return "\n".join(lines)[:3900]

    human._technical_details = technical_details
