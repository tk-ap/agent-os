"""Human-first presentation layer for Milchik Telegram.

This module intentionally wraps the existing Telegram runtime rather than
forking its authorization/state machinery. The underlying task, inspection,
grant, replay, and publication semantics remain in telegram.py. This layer owns
only what the human operator reads and the presentation-only controls that reveal
more detail.

The contract is adapters/hermes/fleet/OPERATOR_COMMUNICATION.md.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import secrets
import sys
import time

# Load the existing implementation under a private module name so this wrapper
# can be registered as adapters.hermes.fleet.telegram without recursive import.
_BASE_NAME = __package__ + "._telegram_base"
if _BASE_NAME in sys.modules:
    base = sys.modules[_BASE_NAME]
else:
    path = Path(__file__).with_name("telegram.py")
    spec = importlib.util.spec_from_file_location(_BASE_NAME, path)
    if spec is None or spec.loader is None:
        raise ImportError("Could not load Telegram runtime")
    base = importlib.util.module_from_spec(spec)
    sys.modules[_BASE_NAME] = base
    spec.loader.exec_module(base)

_original_handle_update = base.handle_update


def _routing_proposal(conn, row, checkpoint):
    """Persist and return a routing proposal when this is a routing review."""
    if not (row["work_id"].startswith("directive-") and row["work_id"].endswith("-routing")):
        return None
    proposal = checkpoint.get("proposal")
    if isinstance(proposal, dict):
        conn.execute(
            "INSERT OR REPLACE INTO routing_proposals(task_id,work_id,proposal) VALUES (?,?,?)",
            (row["task_id"], row["work_id"], json.dumps(proposal)),
        )
        return proposal
    stored = conn.execute("SELECT proposal FROM routing_proposals WHERE task_id=?", (row["task_id"],)).fetchone()
    if not stored:
        return None
    try:
        return json.loads(stored[0])
    except ValueError:
        return None


def _safe_label(verdict):
    if verdict == "pass":
        return "Yes — W Dog checked it independently and found no problems."
    if verdict == "fail":
        return "No — the independent review found problems."
    if verdict == "stale":
        return "Not yet — the files changed after the independent review."
    if verdict == "unreadable":
        return "Unclear — the independent review did not give a reliable yes or no."
    return "Not confirmed — the independent review was unavailable."


def _approval_consequence(order):
    choices = base.publish_choices(order)
    if len(choices) == 1 and choices[0][0] == "accept":
        return "Approving closes this review. Nothing is published or deployed."
    kinds = {choice[0] for choice in choices}
    if "deploy" in kinds:
        return "You can approve the work without publishing it, or separately choose to publish it live."
    if "commit" in kinds:
        return "Approving can save the reviewed files locally. Nothing goes online."
    return "Approving accepts the reviewed work. Nothing goes online."


def collect_reviews(conn, state):
    """Create concise, human-first review cards while retaining all evidence."""
    from hermes_cli import kanban_db as kb

    for row in conn.execute("SELECT * FROM agent_os_orders WHERE phase IN ('review','blocked','revoked')").fetchall():
        task = kb.get_task(conn, row["task_id"])
        if not task or task.status not in {"review", "blocked"}:
            continue
        if row["work_id"].endswith(base.INSPECTION_SUFFIX):
            continue
        inspection = conn.execute(
            "SELECT * FROM agent_os_inspections WHERE task_id=?", (row["task_id"],)
        ).fetchone()
        if inspection is None or inspection["verdict"] is None:
            continue

        try:
            order = json.loads(row["payload"])
        except ValueError:
            continue

        stamp = None
        if task.status == "review":
            try:
                stamp = base.fingerprint(row)
            except Exception:
                pass

        key = f"task:{task.id}:{row['phase']}:{row['attempts']}:{stamp}"
        record_path = Path(state) / task.id / f"{row['attempts']}.json"
        record = json.loads(record_path.read_text()) if record_path.exists() else {}
        checkpoint = {}
        try:
            checkpoint = json.loads(record.get("checkpoint_text", "{}"))
        except ValueError:
            pass

        proposal = _routing_proposal(conn, row, checkpoint)
        verdict = inspection["verdict"]
        if verdict == "pass" and inspection["snapshot"] and stamp and inspection["snapshot"] != stamp:
            verdict = "stale"

        agent_name = (row["owning_agent"] or "The responsible agent").replace("-", " ").title()
        if proposal and proposal.get("owning_agent"):
            owner = str(proposal["owning_agent"]).replace("-", " ").title()
            headline = f"**Decision required — {owner} is ready to continue**"
            happened = f"The work assignment recommends {owner} to take this work."
            next_step = f"If you approve, {owner} becomes responsible for the next governed work item."
        else:
            headline = f"**Decision required — {agent_name} finished a piece of work**"
            summary = checkpoint.get("summary") or "The agent did not provide a useful summary."
            happened = base.short(summary, 260)
            next_step = _approval_consequence(order)

        text = headline + "\n\n"
        text += "**What happened**\n" + happened + "\n\n"
        text += "**Safe to approve?**\n" + _safe_label(verdict) + "\n\n"
        text += "**What approval means**\n" + next_step + "\n\n"
        text += "Nothing has been published or deployed unless you explicitly choose a publish action.\n\n"
        text += "Use **Explain** if you want the reasoning, evidence, or technical details."

        found = base.links_for(order)
        if found:
            text += "\n\n**Useful links**\n" + "\n".join(found)

        conn.execute(
            """INSERT OR IGNORE INTO telegram_cards
               (id,event_key,task_id,snapshot,expires,message) VALUES (?,?,?,?,?,?)""",
            (secrets.token_urlsafe(12), key, task.id, stamp, time.time() + 86400, text),
        )


def _technical_details(conn, card, state):
    """Read-only progressive disclosure for Explain. Never mutates task state."""
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
    inspection = conn.execute(
        "SELECT * FROM agent_os_inspections WHERE task_id=?", (row["task_id"],)
    ).fetchone()

    lines = ["**Explanation**"]
    proposal = _routing_proposal(conn, row, checkpoint)
    if proposal and proposal.get("owning_agent"):
        owner = str(proposal["owning_agent"]).replace("-", " ").title()
        lines.append(
            f"This is a work-assignment decision. {owner} was selected as the agent responsible; "
            "approving the assignment creates the next governed work item. It does not publish or deploy anything."
        )
    else:
        lines.append(
            "This is a review gate: the workforce has finished a bounded piece of work and is waiting for your decision before closing it."
        )
    lines.append("")
    lines.append("**Independent review**")
    if inspection:
        readable = {
            "pass": "Review passed.",
            "fail": "Review found problems.",
            "stale": "The earlier review no longer matches the current files.",
            "unreadable": "The reviewer did not return a machine-readable yes/no verdict.",
            "unavailable": "The independent review could not run.",
        }.get(inspection["verdict"], str(inspection["verdict"]))
        lines.append(readable)
        if inspection["failed"]:
            lines.append(base.short(inspection["failed"], 900))
    else:
        lines.append("No independent review record is available.")
    lines.append("")
    lines.append("**Technical details**")
    lines.append(f"Task ID: `{row['task_id']}`")
    lines.append(f"Work ID: `{base.short(row['work_id'], 120)}`")
    lines.append(f"Agent responsible: `{row['owning_agent'] or 'unattributed'}`")
    lines.append(f"Product: `{order.get('owning_product', 'unknown')}`")
    lines.append(f"Evidence folder: `{record_path.parent}`")
    lines.append("")
    lines.append("Technical term: the work is at a **review gate** — completed by the worker, but not yet accepted by you.")
    return "\n".join(lines)[:3900]


def _feedback_keyboard(card_id):
    return {"inline_keyboard": [
        [{"text": label, "callback_data": f"aos:{card_id}:{action}"}]
        for action, label, _reason in base.FEEDBACK_CHOICES
    ]}


def deliver(conn, config, api):
    """Deliver the same governed cards with a smaller primary control set."""
    for card in conn.execute(
        "SELECT * FROM telegram_cards WHERE delivery='pending' ORDER BY rowid LIMIT 5"
    ).fetchall():
        if card["expires"] <= time.time():
            conn.execute("UPDATE telegram_cards SET delivery='expired' WHERE id=?", (card["id"],))
            continue
        channel = card["channel"]
        chat_id = config.get("monitor_chat_id") if channel == "monitor" else config["chat_id"]
        if not chat_id:
            continue
        payload = {
            "chat_id": chat_id,
            "text": card["message"][:3900],
            "link_preview_options": {"is_disabled": True},
        }
        if channel == "private" and card["task_id"]:
            phase_row = conn.execute(
                "SELECT phase FROM agent_os_orders WHERE task_id=?", (card["task_id"],)
            ).fetchone()
            if phase_row and phase_row["phase"] == "collision":
                payload["reply_markup"] = {"inline_keyboard": [
                    [{"text": "Resume after re-check", "callback_data": f"aos:{card['id']}:resume"}],
                    [{"text": "Cancel", "callback_data": f"aos:{card['id']}:deny"}],
                    [{"text": "Explain", "callback_data": f"aos:{card['id']}:explain"}],
                ]}
            elif phase_row and phase_row["phase"] == "waiting_approval":
                payload["reply_markup"] = {"inline_keyboard": [
                    [{"text": "Approve this scope", "callback_data": f"aos:{card['id']}:approve"}],
                    [{"text": "Deny & cancel", "callback_data": f"aos:{card['id']}:deny"}],
                    [{"text": "Explain", "callback_data": f"aos:{card['id']}:explain"}],
                ]}
            else:
                actions = []
                if card["snapshot"]:
                    order_row_ = conn.execute(
                        "SELECT payload FROM agent_os_orders WHERE task_id=?", (card["task_id"],)
                    ).fetchone()
                    try:
                        approved = json.loads(order_row_["payload"]) if order_row_ else {}
                    except (ValueError, TypeError):
                        approved = {}
                    actions = [(label, name) for name, label, _detail in base.publish_choices(approved)]
                actions += [("Needs work", "needswork"), ("Pause", "pause"), ("Explain", "explain")]
                payload["reply_markup"] = {"inline_keyboard": [
                    [{"text": label, "callback_data": f"aos:{card['id']}:{action}"}]
                    for label, action in actions
                ]}
        conn.execute("UPDATE telegram_cards SET delivery='uncertain' WHERE id=?", (card["id"],))
        result = api.call("sendMessage", **payload)
        conn.execute(
            "UPDATE telegram_cards SET delivery='sent',message_id=? WHERE id=?",
            (result["message_id"], card["id"]),
        )


def decide(conn, config, query, state=None):
    """Keep base decision semantics, rewrite only the human confirmation."""
    response = base_decide(conn, config, query, state)
    if response.startswith("Accepted. Directed work enqueued for "):
        tail = response[len("Accepted. Directed work enqueued for "):]
        agent = tail.split(" (", 1)[0].replace("-", " ").title()
        return (
            f"Approved. {agent} will take this work next. It will go through the same review process "
            "before anything consequential happens. Nothing has been published or deployed."
        )
    replacements = {
        "Accepted. Nothing published.": "Approved. The reviewed work is closed. Nothing was published or deployed.",
        "Execution paused.": "Paused. The work is stopped for now; nothing was deleted or published.",
        "Approved. The task resumes under the scoped grant; everything else stays blocked.":
            "Approved for this scope only. The same work can continue; everything outside that permission stays blocked.",
        "Denied. The task is cancelled; the denial is recorded with the work.":
            "Denied. This work is cancelled and nothing new was authorized.",
    }
    return replacements.get(response, response)


def _decision_label(action):
    if action in {"accept", "commit", "deploy", "approve"}:
        return "Approved"
    if action == "pause":
        return "Paused"
    if action == "deny":
        return "Denied"
    if action == "resume":
        return "Resumed"
    if base.feedback_action(action):
        return "Sent back for revision"
    return "Decision recorded"


def handle_update(conn, config, api, update, state=None):
    """Add presentation-only Explain/Needs work controls; delegate all else."""
    query = update.get("callback_query")
    if not query:
        return _original_handle_update(conn, config, api, update, state)

    data = str(query.get("data", ""))
    parts = data.split(":")
    if len(parts) == 3 and parts[0] == "aos" and parts[2] in {"explain", "needswork"}:
        if (
            query.get("from", {}).get("id") != config["user_id"]
            or query.get("message", {}).get("chat", {}).get("id") != config["chat_id"]
        ):
            try:
                api.call("answerCallbackQuery", callback_query_id=query["id"], text="Not authorized", show_alert=True)
            except base.TelegramError:
                pass
            return
        card = conn.execute("SELECT * FROM telegram_cards WHERE id=?", (parts[1],)).fetchone()
        if not card or card["decision"]:
            try:
                api.call("answerCallbackQuery", callback_query_id=query["id"], text="This review is no longer open.", show_alert=True)
            except base.TelegramError:
                pass
            return
        try:
            api.call("answerCallbackQuery", callback_query_id=query["id"], text="No decision was made.", show_alert=False)
            if parts[2] == "explain":
                api.call(
                    "sendMessage",
                    chat_id=config["chat_id"],
                    text=_technical_details(conn, card, state or base.DEFAULT_STATE),
                    link_preview_options={"is_disabled": True},
                )
            else:
                api.call(
                    "sendMessage",
                    chat_id=config["chat_id"],
                    text="**What needs work?**\nChoose the closest reason. This sends feedback; it does not publish anything.",
                    reply_markup=_feedback_keyboard(card["id"]),
                    link_preview_options={"is_disabled": True},
                )
        except base.TelegramError:
            pass
        return

    # Preserve batch-publish behavior unchanged.
    if data.startswith("pub:"):
        return _original_handle_update(conn, config, api, update, state)

    # Handle ordinary governed decisions with the base mutation logic but a
    # human confirmation and human card footer.
    if len(parts) == 3 and parts[0] == "aos":
        response = decide(conn, config, query, state)
        try:
            api.call("answerCallbackQuery", callback_query_id=query["id"], text=response[:190], show_alert=True)
        except base.TelegramError:
            pass
        card = conn.execute("SELECT * FROM telegram_cards WHERE id=?", (parts[1],)).fetchone()
        decided = {"accept", "commit", "deploy", "pause", "approve", "deny", "resume"} | {
            name for name, _label, _reason in base.FEEDBACK_CHOICES
        }
        if card and card["decision"] in decided:
            try:
                api.call(
                    "editMessageText",
                    chat_id=config["chat_id"],
                    message_id=card["message_id"],
                    text=card["message"][:3500] + "\n\n**" + _decision_label(card["decision"]) + "**",
                    reply_markup={"inline_keyboard": []},
                    _plain_text=True,
                )
            except base.TelegramError:
                pass
        return

    return _original_handle_update(conn, config, api, update, state)


# Capture the original before replacing the base module's globals. base.tick and
# base.listen resolve these names at runtime, so the existing scheduler/listener
# automatically use the human-first renderer without changing authority logic.
base_decide = base.decide
base.collect_reviews = collect_reviews
base.deliver = deliver
base.decide = decide
base.handle_update = handle_update

# Public surface: preserve every existing command/API, with patched globals.
for _name in dir(base):
    if _name.startswith("__"):
        continue
    globals().setdefault(_name, getattr(base, _name))

# Explicitly bind the patched entrypoints after the export loop.
collect_reviews = collect_reviews
deliver = deliver
decide = decide
handle_update = handle_update
tick = base.tick
listen = base.listen
main = base.main
