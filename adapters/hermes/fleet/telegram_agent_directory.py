"""Telegram quick-reference directory and human-directed agent requests.

Presentation/routing preference only. Choosing an agent does not widen that
agent's authority, bypass review, or grant protected capabilities.
"""
from __future__ import annotations

import json
from pathlib import Path
import time


def _registry(telegram):
    try:
        import yaml
        data = yaml.safe_load((telegram.ROOT / "registry/agents.yaml").read_text()) or {}
        return data.get("agents", {})
    except Exception:
        return {}


def _human_list(values, limit=4):
    out = []
    for value in (values or [])[:limit]:
        out.append(str(value).replace("-", " "))
    return ", ".join(out) or "specialized workforce support"


def directory_text(telegram):
    agents = _registry(telegram)
    if not agents:
        return "**Agent directory**\n\nI could not read the workforce registry right now."
    lines = [
        "**Agent directory**",
        "Choose someone to see what they specialize in or direct a request to them.",
        "",
    ]
    for key, item in agents.items():
        lines.append(f"**{item.get('name', key.title())} — {item.get('role', 'Agent')}**")
        lines.append(_human_list(item.get("owns"), 3))
        lines.append("")
    lines.append("Selecting an agent does **not** give them extra permission. Normal safety, review, and approval boundaries still apply.")
    return "\n".join(lines)[:3900]


def directory_keyboard(telegram):
    agents = _registry(telegram)
    buttons = []
    row = []
    for key, item in agents.items():
        row.append({"text": item.get("name", key.title()), "callback_data": f"aosdir:{key}"})
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return {"inline_keyboard": buttons}


def agent_card(telegram, agent_id):
    item = _registry(telegram).get(agent_id)
    if not item:
        return None, None
    name = item.get("name", agent_id.title())
    role = item.get("role", "Agent")
    owns = _human_list(item.get("owns"), 6)
    skills = _human_list(item.get("core_skills"), 5)
    text = (
        f"**{name} — {role}**\n\n"
        f"**Best for**\n{owns}\n\n"
        f"**Typical strengths**\n{skills}\n\n"
        "You can direct your next request to this agent. The request still stays inside the normal Agent OS review and permission boundaries."
    )
    keyboard = {"inline_keyboard": [
        [{"text": f"Direct a request to {name}", "callback_data": f"aosdirect:{agent_id}"}],
        [{"text": "Back to agent directory", "callback_data": "aosdir:index"}],
    ]}
    return text, keyboard


def _shortcut_keyboard():
    return {
        "keyboard": [[{"text": "Agent directory"}, {"text": "Status"}]],
        "resize_keyboard": True,
        "is_persistent": True,
    }


def _pending_key(user_id):
    return f"direct_agent:{user_id}"


def _ensure_shortcuts(telegram, state, config_path, api=None):
    """Install a persistent Telegram reply-keyboard once per local state DB."""
    try:
        config_path = Path(config_path)
        if not config_path.exists():
            return
        config = json.loads(config_path.read_text())
        if not config.get("enabled"):
            return
        api = api or telegram.API(config["token"])
        conn = telegram.connect(state)
        try:
            telegram.schema(conn)
            seen = conn.execute("SELECT value FROM telegram_meta WHERE key='operator_shortcuts_v1'").fetchone()
            if seen:
                return
            api.call(
                "sendMessage",
                chat_id=config["chat_id"],
                text="Operator shortcuts are ready. Use **Agent directory** whenever you want to choose who should handle a request.",
                reply_markup=_shortcut_keyboard(),
                link_preview_options={"is_disabled": True},
            )
            conn.execute("INSERT OR REPLACE INTO telegram_meta VALUES ('operator_shortcuts_v1',?)", (str(time.time()),))
            conn.commit()
        finally:
            conn.close()
    except Exception:
        # Convenience UI must never break the fleet clock/listener.
        return


def install(telegram):
    original_handle_update = telegram.handle_update
    original_tick = telegram.tick
    original_listen = telegram.listen

    def handle_update(conn, config, api, update, state=None):
        query = update.get("callback_query")
        if query:
            data = str(query.get("data", ""))
            authorized = (
                query.get("from", {}).get("id") == config["user_id"]
                and query.get("message", {}).get("chat", {}).get("id") == config["chat_id"]
            )
            if data.startswith("aosdir:"):
                if not authorized:
                    try:
                        api.call("answerCallbackQuery", callback_query_id=query["id"], text="Not authorized", show_alert=True)
                    except telegram.TelegramError:
                        pass
                    return
                target = data.split(":", 1)[1]
                try:
                    api.call("answerCallbackQuery", callback_query_id=query["id"], text="No work started.", show_alert=False)
                    if target == "index":
                        api.call("sendMessage", chat_id=config["chat_id"], text=directory_text(telegram),
                                 reply_markup=directory_keyboard(telegram), link_preview_options={"is_disabled": True})
                    else:
                        text, keyboard = agent_card(telegram, target)
                        if text:
                            api.call("sendMessage", chat_id=config["chat_id"], text=text, reply_markup=keyboard,
                                     link_preview_options={"is_disabled": True})
                except telegram.TelegramError:
                    pass
                return
            if data.startswith("aosdirect:"):
                if not authorized:
                    return
                agent_id = data.split(":", 1)[1]
                item = _registry(telegram).get(agent_id)
                if not item:
                    return
                conn.execute("INSERT OR REPLACE INTO telegram_meta(key,value) VALUES (?,?)",
                             (_pending_key(config["user_id"]), agent_id))
                conn.commit()
                name = item.get("name", agent_id.title())
                try:
                    api.call("answerCallbackQuery", callback_query_id=query["id"], text=f"Next request goes to {name}.", show_alert=False)
                    api.call("sendMessage", chat_id=config["chat_id"], text=(
                        f"**Directing your next request to {name}.**\n\n"
                        "Send the request as your next message in plain language. I will record your agent choice with it. "
                        "This does not bypass safety checks, independent review, or protected-action approvals.\n\n"
                        "Send **Cancel** if you change your mind."),
                        link_preview_options={"is_disabled": True})
                except telegram.TelegramError:
                    pass
                return

        message = update.get("message")
        if message:
            sender = message.get("from", {}).get("id")
            chat = message.get("chat", {}).get("id")
            text = str(message.get("text", "")).strip()
            if sender == config["user_id"] and chat == config["chat_id"]:
                if text.lower() in {"agent directory", "/agents"}:
                    try:
                        api.call("sendMessage", chat_id=chat, text=directory_text(telegram),
                                 reply_markup=directory_keyboard(telegram), link_preview_options={"is_disabled": True})
                    except telegram.TelegramError:
                        pass
                    return
                if text.lower() == "status":
                    try:
                        api.call("sendMessage", chat_id=chat, text=telegram.status_report(conn, config)[:3500],
                                 reply_markup=_shortcut_keyboard(), link_preview_options={"is_disabled": True})
                    except telegram.TelegramError:
                        pass
                    return
                pending = conn.execute("SELECT value FROM telegram_meta WHERE key=?",
                                       (_pending_key(config["user_id"]),)).fetchone()
                if pending:
                    if text.lower() == "cancel":
                        conn.execute("DELETE FROM telegram_meta WHERE key=?", (_pending_key(config["user_id"]),))
                        conn.commit()
                        try:
                            api.call("sendMessage", chat_id=chat, text="Direct request cancelled.",
                                     reply_markup=_shortcut_keyboard(), link_preview_options={"is_disabled": True})
                        except telegram.TelegramError:
                            pass
                        return
                    if text and not text.startswith("/"):
                        agent_id = pending[0]
                        item = _registry(telegram).get(agent_id, {})
                        name = item.get("name", agent_id.title())
                        # Human-selected ownership is explicit input to Router. Router still
                        # validates the work envelope/product/lane; it must not silently swap
                        # the owner unless the choice is incompatible or unsafe, in which case
                        # the routing review explains why.
                        directive = (
                            f"TK explicitly selected {agent_id} ({name}) as the preferred owner. "
                            "Preserve this owner unless it is incompatible or unsafe; if you must change it, explain why to TK.\n\n"
                            + text
                        )
                        conn.execute("INSERT INTO telegram_directives(ts,text) VALUES (?,?)",
                                     (time.time(), telegram.short(directive, 2000)))
                        number = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                        conn.execute("DELETE FROM telegram_meta WHERE key=?", (_pending_key(config["user_id"]),))
                        conn.commit()
                        try:
                            api.call("sendMessage", chat_id=chat, text=(
                                f"Got it — #{number} is directed to **{name}**. Router will validate the work envelope, "
                                "but it should keep your chosen owner unless there is a real incompatibility or safety reason."),
                                reply_markup=_shortcut_keyboard(), link_preview_options={"is_disabled": True})
                        except telegram.TelegramError:
                            pass
                        return
        return original_handle_update(conn, config, api, update, state)

    def tick(state=telegram.DEFAULT_STATE, config_path=telegram.CONFIG, api=None):
        _ensure_shortcuts(telegram, state, config_path, api)
        return original_tick(state, config_path, api)

    def listen(state=telegram.DEFAULT_STATE, config_path=telegram.CONFIG, api=None, once=False):
        _ensure_shortcuts(telegram, state, config_path, api)
        return original_listen(state, config_path, api, once)

    telegram.handle_update = handle_update
    telegram.tick = tick
    telegram.listen = listen
