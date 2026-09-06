"""Dedicated Telegram review inbox; driven by the existing Hermes no-model tick.

This bot must not also be registered with the Hermes chat gateway: one getUpdates
consumer owns its offset. Arbitrary messages never become agent instructions.
"""
import argparse
import getpass
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import socket
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request

from .bridge import DEFAULT_STATE, ROOT, connect, lock, order_row

CONFIG = Path.home() / ".hermes" / "agent-os-telegram.json"


class TelegramError(RuntimeError):
    pass


class API:
    def __init__(self, token):
        if not re.fullmatch(r"[0-9]+:[A-Za-z0-9_-]+", token):
            raise ValueError("Invalid bot token shape")
        self.token = token

    def call(self, method, **payload):
        if method not in {"getMe", "getWebhookInfo", "getUpdates", "sendMessage", "answerCallbackQuery", "editMessageText"}:
            raise ValueError("Unsupported Telegram operation")
        request = urllib.request.Request(
            f"https://api.telegram.org/bot{self.token}/{method}",
            data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
        try:
            # No token-bearing URLs or exception objects are logged.
            with urllib.request.urlopen(request, timeout=10) as response:
                result = json.load(response)
        except urllib.error.HTTPError as exc:
            reasons = {
                401: "Telegram rejected the bot token. Copy the token from BotFather again.",
                404: "Telegram could not find this bot/API endpoint. Check the BotFather token.",
                409: "Another program is consuming this bot's updates. Use this dedicated bot only with Mr. Milchik.",
                429: "Telegram rate-limited the request. Wait a minute and retry.",
            }
            raise TelegramError(reasons.get(exc.code, f"Telegram returned HTTP {exc.code} during {method}.")) from None
        except urllib.error.URLError as exc:
            reason = exc.reason
            if isinstance(reason, ssl.SSLCertVerificationError):
                detail = "TLS certificate verification failed. Check the host CA certificates; verification remains enabled."
            elif isinstance(reason, socket.gaierror):
                detail = "DNS lookup failed for api.telegram.org. Check the host network/DNS and retry."
            elif isinstance(reason, (TimeoutError, socket.timeout)):
                detail = "Connection to api.telegram.org timed out. Check network/firewall access and retry."
            else:
                detail = f"Network connection failed ({type(reason).__name__}). Check access to api.telegram.org."
            if method in {"sendMessage", "editMessageText"}:
                detail += " Delivery may be uncertain; it will not be automatically retried."
            raise TelegramError(detail) from None
        except (TimeoutError, socket.timeout):
            raise TelegramError(f"Telegram {method} timed out; check host network access.") from None
        except (OSError, ValueError):
            raise TelegramError(f"Telegram {method} returned an unreadable response.") from None
        if not result.get("ok"):
            raise TelegramError("Telegram rejected request")
        return result["result"]


def schema(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS telegram_cards (
            id TEXT PRIMARY KEY, event_key TEXT UNIQUE NOT NULL, task_id TEXT,
            snapshot TEXT, expires REAL NOT NULL, message TEXT NOT NULL,
            decision TEXT, delivery TEXT NOT NULL DEFAULT 'pending', message_id INTEGER,
            decided_by INTEGER, decided_at REAL, channel TEXT NOT NULL DEFAULT 'private'
        );
        CREATE TABLE IF NOT EXISTS telegram_meta (key TEXT PRIMARY KEY,value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS telegram_changes (
            id INTEGER PRIMARY KEY, product TEXT NOT NULL, kind TEXT NOT NULL,
            revision TEXT NOT NULL, summary TEXT NOT NULL, reported INTEGER NOT NULL DEFAULT 0,
            UNIQUE(product,kind,revision)
        );
        CREATE TABLE IF NOT EXISTS telegram_signals (
            id INTEGER PRIMARY KEY, ts REAL NOT NULL, scope TEXT NOT NULL,
            polarity TEXT NOT NULL, text TEXT NOT NULL, reported INTEGER NOT NULL DEFAULT 0
        );
    """)
    migrate(conn)


def migrate(conn):
    """Add columns CREATE TABLE IF NOT EXISTS cannot add to an existing table.

    A state file created before a column was introduced keeps its old shape
    forever, so every read of that column fails at runtime rather than at
    install time. Each entry is idempotent and safe on a fresh database.
    """
    additions = {"telegram_cards": {"channel": "TEXT NOT NULL DEFAULT 'private'"}}
    for table, columns in additions.items():
        present = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
        if not present:
            continue
        for column, definition in columns.items():
            if column not in present:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
    conn.commit()


def git(workspace, *args):
    result = subprocess.run(["git", "-C", str(workspace), *args],
        capture_output=True, timeout=20, check=True)
    if len(result.stdout) > 16_000_000:
        raise ValueError("Workspace diff too large for remote approval")
    return result.stdout


def fingerprint(row):
    """Bind acceptance to work order, current Git revision, and all uncommitted files."""
    workspace = Path(json.loads(row["payload"])["workspace"])
    digest = hashlib.sha256(row["digest"].encode())
    digest.update(git(workspace, "rev-parse", "HEAD"))
    digest.update(git(workspace, "diff", "--binary", "HEAD", "--"))
    names = git(workspace, "ls-files", "--others", "--exclude-standard", "-z").split(b"\0")
    total = 0
    for name in sorted(n for n in names if n):
        path = workspace / os.fsdecode(name)
        if path.is_symlink():
            data = os.readlink(path).encode()
        else:
            total += path.stat().st_size
            if total > 32_000_000:
                raise ValueError("Untracked artifacts too large for remote approval")
            data = path.read_bytes()
        digest.update(name + b"\0" + hashlib.sha256(data).digest())
    return digest.hexdigest()


def short(value, limit=500):
    return str(value).replace("\x00", "")[:limit]


def collect_reviews(conn, state):
    from hermes_cli import kanban_db as kb
    for row in conn.execute("SELECT * FROM agent_os_orders WHERE phase IN ('review','blocked','revoked')").fetchall():
        task = kb.get_task(conn, row["task_id"])
        if task.status not in {"review", "blocked"}:
            continue
        order = json.loads(row["payload"])
        stamp = None
        if task.status == "review":
            try:
                stamp = fingerprint(row)
            except (OSError, ValueError, subprocess.SubprocessError):
                pass
        key = f"task:{task.id}:{row['phase']}:{row['attempts']}:{stamp}"
        record_path = Path(state) / task.id / f"{row['attempts']}.json"
        record = json.loads(record_path.read_text()) if record_path.exists() else {}
        checkpoint = {}
        try:
            checkpoint = json.loads(record.get("checkpoint_text", "{}"))
        except ValueError:
            pass
        text = f"Mr. Milchik — {order['owning_product']}\n{short(order['work_id'],120)}\n"
        text += "Decision: accept this local result" if stamp else "Attention needed; inspect locally"
        text += f"\nState: {row['phase']} · Attempts: {row['attempts']}\n"
        text += f"Worker: {record.get('harness','unknown')} · Result: {record.get('result','not recorded')}\n"
        text += f"Worker summary: {short(checkpoint.get('summary','No structured summary recorded'))}\n"
        text += "Acceptance criteria: " + short("; ".join(order["acceptance_criteria"])) + "\n"
        text += f"Worker-reported checks: {short(checkpoint.get('verification',[]))}\n"
        text += "Independent acceptance: pending. Live deployment: not established by this run.\n"
        text += f"Task: {task.id}\nEvidence on workstation: {record_path.parent}\n"
        text += "Accept result closes this local task only. It does not publish, merge, or deploy."
        conn.execute("""INSERT OR IGNORE INTO telegram_cards
            (id,event_key,task_id,snapshot,expires,message) VALUES (?,?,?,?,?,?)""",
            (secrets.token_urlsafe(12), key, task.id, stamp, time.time()+86400, text))


def record_change(conn, product, kind, revision, summary):
    if kind not in {"commit", "deployment"} or product not in {"ashwood", "alvira-meos"}:
        raise ValueError("Unsupported product/change kind")
    if not revision.strip() or len(revision) > 200:
        raise ValueError("A stable revision/deployment ID is required")
    conn.execute("INSERT OR IGNORE INTO telegram_changes(product,kind,revision,summary) VALUES (?,?,?,?)",
                 (product,kind,revision,short(summary)))


def collect_commits(conn, repositories):
    for product, path in repositories.items():
        key = "git:" + product
        head = git(path,"rev-parse","HEAD").decode().strip()
        previous = conn.execute("SELECT value FROM telegram_meta WHERE key=?", (key,)).fetchone()
        if previous and previous[0] != head:
            # Only new descendants count. Branch switches/history rewrites rebaseline.
            try:
                git(path,"merge-base","--is-ancestor",previous[0],head)
                revisions = git(path,"rev-list","--reverse",f"{previous[0]}..{head}").decode().splitlines()
                for revision in revisions:
                    subject = git(path,"show","-s","--format=%s",revision).decode().strip()
                    record_change(conn,product,"commit",revision,subject)
            except subprocess.CalledProcessError:
                pass
        conn.execute("INSERT OR REPLACE INTO telegram_meta VALUES (?,?)", (key,head))


def collect_batches(conn, every, basis):
    if not 1 <= every <= 100 or basis not in {"commit","deployment","off"}:
        raise ValueError("Invalid reporting cadence")
    if basis == "off":
        return
    for product in ("ashwood","alvira-meos"):
        rows = conn.execute("SELECT * FROM telegram_changes WHERE product=? AND kind=? AND reported=0 ORDER BY id LIMIT ?",
                            (product,basis,every)).fetchall()
        if len(rows) < every:
            continue
        text = f"Mr. Milchik — {product}\n{every} new {basis} records\n"
        text += "\n".join(f"• {r['revision'][:12]} {short(r['summary'],160)}" for r in rows[:10])
        text += "\nCommits do not prove a live-site change. Deployment records require producer evidence."
        text += "\nHuman/visual verification is reported separately on review cards."
        key = f"batch:{product}:{basis}:{rows[0]['id']}:{rows[-1]['id']}"
        conn.execute("INSERT OR IGNORE INTO telegram_cards(id,event_key,expires,message) VALUES (?,?,?,?)",
                     (secrets.token_urlsafe(12),key,time.time()+604800,text))
        conn.executemany("UPDATE telegram_changes SET reported=1 WHERE id=?", [(r['id'],) for r in rows])


def _fleet_line(kind, detail):
    """One compact line per fleet event. detail is already a dict from the event store."""
    d = detail or {}
    if kind == "queued":
        return f"▸ queued · harnesses {', '.join(d.get('harnesses', []))}"
    if kind == "claim":
        if d.get("outcome") == "denied":
            return f"✕ claim denied · {d.get('reason', 'invalid authority')}"
        return f"▸ claimed · attempt {d.get('attempts', 0)}/{d.get('max_attempts', '?')}"
    if kind == "start":
        return f"▸ start · {d.get('harness', '?')} · attempt {d.get('attempt', '?')}"
    if kind == "result":
        return f"◂ result · {d.get('harness', '?')} · {d.get('result', '?')}"
    if kind == "phase":
        return f"◼ phase → {d.get('phase', '?')}" + (f" · {d.get('reason', '')}" if d.get('reason') else "")
    return f"· {kind}"


def collect_fleet(conn):
    """Turn fleet lifecycle events into read-only monitor-channel cards.

    Reads the last-reported event id watermark so each event is reported exactly
    once. Monitor cards carry no buttons and no acceptance path: the channel is
    awareness only, never a decision surface.
    """
    row = conn.execute("SELECT value FROM telegram_meta WHERE key='fleet_watermark'").fetchone()
    watermark = int(row[0]) if row else 0
    events = conn.execute("SELECT id,ts,task_id,kind,detail FROM agent_os_events WHERE id>? ORDER BY id",
                          (watermark,)).fetchall()
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
        order = conn.execute("SELECT payload FROM agent_os_orders WHERE task_id=?", (task_id,)).fetchone()
        work_id = ""
        if order:
            try:
                work_id = json.loads(order["payload"]).get("work_id", "")
            except ValueError:
                pass
        lines = [f"Milchik — {short(work_id, 80) or task_id}"]
        for event, detail in group:
            lines.append(_fleet_line(event["kind"], detail))
        key = f"fleet:{task_id}:{group[-1][0]['id']}"
        conn.execute("INSERT OR IGNORE INTO telegram_cards(id,event_key,expires,message,channel) VALUES (?,?,?,?,?)",
                     (secrets.token_urlsafe(12), key, time.time()+86400, "\n".join(lines), "monitor"))
    conn.execute("INSERT OR REPLACE INTO telegram_meta VALUES ('fleet_watermark',?)", (str(events[-1]["id"]),))


def record_signal(conn, scope, polarity, text):
    """Ingest a drift/memory observation. Never grants or revokes anything."""
    if polarity not in {"positive", "negative"}:
        raise ValueError("Signal polarity must be positive or negative")
    if not scope.strip() or not text.strip():
        raise ValueError("A signal needs a scope and text")
    conn.execute("INSERT INTO telegram_signals(ts,scope,polarity,text) VALUES (?,?,?,?)",
                 (time.time(), short(scope, 120), polarity, short(text, 2000)))


def collect_signals(conn):
    """Batch unreported drift/memory signals into private-chat cards for TK."""
    rows = conn.execute("SELECT * FROM telegram_signals WHERE reported=0 ORDER BY id").fetchall()
    if not rows:
        return
    text = "Milchik — signals\n"
    text += "\n".join(f"{'▲' if r['polarity'] == 'positive' else '▼'} [{r['scope']}] {r['text']}" for r in rows)
    key = f"signals:{rows[0]['id']}:{rows[-1]['id']}"
    conn.execute("INSERT OR IGNORE INTO telegram_cards(id,event_key,expires,message,channel) VALUES (?,?,?,?,?)",
                 (secrets.token_urlsafe(12), key, time.time()+86400, text[:3900], "private"))
    conn.executemany("UPDATE telegram_signals SET reported=1 WHERE id=?", [(r['id'],) for r in rows])


def backlog_top(k=3):
    """Top-ranked backlog items Milchik should surface, or None if unreadable.

    Ranking decides attention, never execution: an item's authority state is
    reported alongside it so a high rank is never mistaken for a go-ahead.
    """
    try:
        import yaml
        from runtime import backlog as backlog_runtime
        items = yaml.safe_load((ROOT / "agents/milchik/backlog.yaml").read_text()) or []
        return [(item, backlog_runtime.attention_score(item),
                 backlog_runtime.authority_present(item)) for item in backlog_runtime.next_for_attention(items, k)]
    except Exception:
        return None  # A status reply degrades rather than failing when the backlog is unavailable.


def status_report(conn, config):
    """Milchik's founder view, answered on demand rather than pushed.

    Reports recorded state and cites where each number came from. It starts
    nothing, decides nothing, and grants nothing.

    Two rules from agents/milchik/IDENTITY.md shape what this may say: activity
    is never reported as progress (§08), and every figure names the record it
    came from (§12). Counts of running tasks are therefore labelled as recorded
    state, not as work completed.
    """
    now = time.time()
    lines = ["Mr. Milchik — status"]

    counts = {r["status"]: r["c"] for r in conn.execute(
        "SELECT status, count(*) c FROM tasks WHERE status IN ('running','review','blocked') GROUP BY status")}
    lines.append(f"Fleet (recorded task state): running {counts.get('running',0)} · "
                 f"in review {counts.get('review',0)} · blocked {counts.get('blocked',0)}")
    lines.append("Recorded state only. Running is not progress and no worker self-report is counted here.")

    awaiting = conn.execute("""SELECT task_id, message FROM telegram_cards
        WHERE channel='private' AND decision IS NULL AND delivery='sent'
          AND task_id IS NOT NULL AND expires > ? ORDER BY expires LIMIT 5""", (now,)).fetchall()
    lines.append("")
    lines.append(f"Awaiting your decision: {len(awaiting)}  [delivered cards, undecided, unexpired]")
    for row in awaiting:
        body = row["message"].splitlines()
        lines.append(f"• {short(body[1] if len(body) > 1 else row['task_id'], 90)}")

    blocked = conn.execute("""SELECT id, title, block_kind FROM tasks
        WHERE status='blocked' ORDER BY started_at DESC LIMIT 5""").fetchall()
    if blocked:
        lines.append("")
        lines.append(f"Blocked: {len(blocked)}  [task record]")
        for row in blocked:
            lines.append(f"• {short(row['title'] or row['id'], 80)} ({row['block_kind'] or 'unspecified'})")

    ranked = backlog_top()
    lines.append("")
    if ranked is None:
        lines.append("Backlog: unavailable  [agents/milchik/backlog.yaml unreadable]")
    elif not ranked:
        lines.append("Backlog: empty")
    else:
        lines.append("Next for attention  [agents/milchik/backlog.yaml, ranked by runtime/backlog.py]")
        for item, score, authorized in ranked:
            gate = "pre-authorized" if authorized else f"needs approval ({item.get('status','proposed')})"
            lines.append(f"• {score:.0f} {short(item.get('title', item.get('work_id','untitled')), 74)}")
            lines.append(f"    {item.get('priority',{}).get('level','p3')} · {item.get('source','agent')} · {gate}")
        lines.append("Ranking is attention, not authority. Nothing here is enqueued by being listed.")

    changes = conn.execute("""SELECT product, kind, revision, summary FROM telegram_changes
        ORDER BY id DESC LIMIT 5""").fetchall()
    lines.append("")
    lines.append("Recorded changes, newest first  [telegram_changes]" if changes else "Recorded changes: none")
    for row in changes:
        lines.append(f"• {row['product']} {row['kind']} {row['revision'][:12]} {short(row['summary'],80)}")
    if changes:
        lines.append("Commits are not deployments. A live-site change needs producer evidence.")

    pending = {r["channel"]: r["c"] for r in conn.execute(
        "SELECT channel, count(*) c FROM telegram_cards WHERE delivery='pending' GROUP BY channel")}
    if pending.get("monitor") and not config.get("monitor_chat_id"):
        lines.append("")
        lines.append(f"{pending['monitor']} monitor cards queued: monitor channel is not paired.")

    return "\n".join(lines)


def decide(conn, config, query):
    """Only authenticated, unexpired, single-use callbacks can accept a frozen result."""
    from hermes_cli import kanban_db as kb
    message = query.get("message", {})
    if (query.get("from",{}).get("id") != config["user_id"] or
        message.get("chat",{}).get("id") != config["chat_id"]):
        return "Not authorized"
    parts = str(query.get("data", "")).split(":")
    if len(parts) != 3 or parts[0] != "aos" or parts[2] not in {"accept","changes","pause"}:
        return "Unknown decision"
    card = conn.execute("SELECT * FROM telegram_cards WHERE id=?", (parts[1],)).fetchone()
    if not card or card["message_id"] != message.get("message_id") or card["decision"]:
        return "Decision already handled or unavailable"
    if card["expires"] <= time.time():
        return "This decision expired; review on the workstation"
    row = order_row(conn,card["task_id"])
    task = kb.get_task(conn,card["task_id"])
    if not row or not task or row["revoked"]:
        return "Task revoked or missing"
    action = parts[2]
    if action == "accept":
        if task.status != "review" or row["phase"] != "review" or not card["snapshot"]:
            return "Task is not eligible for acceptance"
        try:
            if fingerprint(row) != card["snapshot"]:
                return "Files changed since this card; review the refreshed card"
        except (OSError, ValueError, subprocess.SubprocessError):
            return "Cannot verify current files; inspect locally"
    # Consume before mutation; an interrupted decision is reconciled locally, never replayed.
    changed = conn.execute("UPDATE telegram_cards SET decision='processing',decided_by=?,decided_at=? WHERE id=? AND decision IS NULL",
                           (config["user_id"],time.time(),card["id"])).rowcount
    if not changed:
        return "Decision already handled"
    if action == "accept":
        claim = kb.claim_review_task(conn,task.id,ttl_seconds=60)
        if claim is None:
            return "Task changed; inspect locally"
        # Bind the completion to our review claim; never complete a concurrent worker's run.
        try:
            unchanged = fingerprint(order_row(conn,task.id)) == card["snapshot"]
        except (OSError, ValueError, subprocess.SubprocessError):
            unchanged = False
        if not unchanged:
            kb.request_review(conn,task.id,summary="Files changed during acceptance",expected_run_id=claim.current_run_id)
            return "Files changed; inspect locally"
        ok = kb.complete_task(conn,task.id,result="Human accepted local result through Telegram",
             expected_run_id=claim.current_run_id,
             metadata={"telegram_user":config["user_id"],"accepted_snapshot":card["snapshot"]})
        if not ok:
            return "Task changed; inspect locally"
        conn.execute("UPDATE agent_os_orders SET phase='accepted' WHERE task_id=?", (task.id,))
        result = "Local result accepted. No publish, merge, or deployment authorized."
    else:
        # Both actions stop further execution. Changes require a fresh bounded work order.
        conn.execute("UPDATE agent_os_orders SET revoked=1,phase=? WHERE task_id=?", (action,task.id))
        result = "Changes requested; execution paused." if action == "changes" else "Execution paused."
    conn.execute("UPDATE telegram_cards SET decision=? WHERE id=?", (action,card["id"]))
    return result


def deliver(conn, config, api):
    for card in conn.execute("SELECT * FROM telegram_cards WHERE delivery='pending' ORDER BY rowid LIMIT 5").fetchall():
        if card["expires"] <= time.time():
            conn.execute("UPDATE telegram_cards SET delivery='expired' WHERE id=?", (card["id"],))
            continue
        channel = card["channel"]
        chat_id = config.get("monitor_chat_id") if channel == "monitor" else config["chat_id"]
        if not chat_id:
            # Monitor channel not yet paired: leave pending, never fall back to the private chat.
            continue
        payload = {"chat_id": chat_id, "text": card["message"][:3900],
                   "link_preview_options": {"is_disabled": True}}
        if channel == "private" and card["task_id"]:
            actions = ([("Accept result","accept")] if card["snapshot"] else [])
            actions += [("Needs changes","changes"),("Pause","pause")]
            payload["reply_markup"] = {"inline_keyboard":[[
                {"text":label,"callback_data":f"aos:{card['id']}:{action}"} for label,action in actions]]}
        # Ambiguous sends are never automatically retried (Telegram has no idempotency key).
        conn.execute("UPDATE telegram_cards SET delivery='uncertain' WHERE id=?", (card["id"],))
        result = api.call("sendMessage", **payload)
        conn.execute("UPDATE telegram_cards SET delivery='sent',message_id=? WHERE id=?", (result["message_id"],card["id"]))


def tick(state=DEFAULT_STATE, config_path=CONFIG, api=None):
    if not Path(config_path).exists():
        return {"status":"not_configured"}
    config = json.loads(Path(config_path).read_text())
    if not config.get("enabled"):
        return {"status":"disabled"}
    api = api or API(config["token"])
    conn = connect(state)
    try:
        with lock(Path(state)/"telegram.lock"):
            schema(conn)
            offset = conn.execute("SELECT value FROM telegram_meta WHERE key='offset'").fetchone()
            updates = api.call("getUpdates",offset=int(offset[0]) if offset else 0,
                timeout=0,limit=25,allowed_updates=["callback_query","message"])
            for update in updates:
                if "callback_query" in update:
                    query = update["callback_query"]
                    response = decide(conn,config,query)
                    try:
                        api.call("answerCallbackQuery",callback_query_id=query["id"],text=response[:190],show_alert=True)
                    except TelegramError:
                        pass  # Decision is persisted even when Telegram's short callback TTL expires.
                    parts = str(query.get("data", "")).split(":")
                    if len(parts) == 3:
                        card = conn.execute("SELECT * FROM telegram_cards WHERE id=?", (parts[1],)).fetchone()
                        if card and card["decision"] in {"accept","changes","pause"} and card["decided_by"] == config["user_id"]:
                            try:
                                api.call("editMessageText",chat_id=config["chat_id"],message_id=card["message_id"],
                                    text=card["message"][:3500]+"\n\nDecision recorded: "+card["decision"],
                                    reply_markup={"inline_keyboard":[]})
                            except TelegramError:
                                pass
                elif "message" in update:
                    # The ONLY text this bot acts on. Every other message is ignored:
                    # free-form Telegram text is not an agent prompt and grants no authority.
                    message = update["message"]
                    body = str(message.get("text","")).strip().split("@")[0].lower()
                    sender = message.get("from",{}).get("id")
                    chat = message.get("chat",{}).get("id")
                    if body == "/status" and sender == config["user_id"] and chat in {
                            config["chat_id"], config.get("monitor_chat_id")}:
                        try:
                            api.call("sendMessage",chat_id=chat,text=status_report(conn,config)[:3500],
                                link_preview_options={"is_disabled":True})
                        except TelegramError:
                            pass  # A missed status reply is recoverable; the next /status re-reads live state.
                conn.execute("INSERT OR REPLACE INTO telegram_meta VALUES ('offset',?)", (str(update['update_id']+1),))
            collect_reviews(conn,state)
            if config["basis"] == "commit":
                collect_commits(conn,config.get("repositories",{}))
            collect_batches(conn,config["every"],config["basis"])
            collect_fleet(conn)
            collect_signals(conn)
            deliver(conn,config,api)
            return {"status":"ok"}
    finally:
        conn.close()


def setup(every, basis):
    if CONFIG.exists():
        raise ValueError("Bot configuration already exists; inspect it before replacing")
    token = getpass.getpass("New BotFather token (hidden): ").strip()
    api = API(token)
    bot = api.call("getMe")
    if api.call("getWebhookInfo").get("url"):
        raise ValueError("Bot already has a webhook; use a dedicated new bot")
    challenge = secrets.token_urlsafe(16)
    print(f"Open https://t.me/{bot['username']}?start={challenge} in YOUR Telegram and press Start.",flush=True)
    print("Waiting up to 3 minutes to pair your private chat…",flush=True)
    deadline, offset = time.monotonic()+180,0
    while time.monotonic() < deadline:
        updates = api.call("getUpdates",offset=offset,timeout=0,allowed_updates=["message"])
        for update in updates:
            offset = update["update_id"]+1
            message = update.get("message",{})
            if message.get("text") != "/start " + challenge or message.get("chat",{}).get("type") != "private":
                continue
            config = {"token":token,"chat_id":message["chat"]["id"],"user_id":message["from"]["id"],
                      "enabled":True,"every":every,"basis":basis,
                      "repositories":{"ashwood":str(ROOT.parent/"ashwood"),"alvira-meos":str(ROOT.parent/"ALVIRA")}}
            CONFIG.parent.mkdir(exist_ok=True)
            fd = os.open(CONFIG,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
            with os.fdopen(fd,"w") as handle:
                json.dump(config,handle,indent=2)
            conn = connect(DEFAULT_STATE)
            schema(conn)
            conn.execute("INSERT OR REPLACE INTO telegram_meta VALUES ('offset',?)", (str(offset),))
            if basis == "commit":
                collect_commits(conn,config["repositories"])
            conn.close()
            api.call("sendMessage",chat_id=config["chat_id"],text="Mr. Milchik is connected. Review alerts are enabled. Buttons accept local results only; no publishing or deployments. Decisions are processed on the next scheduler tick (about one minute).")
            print("Paired. Token stored privately; existing Hermes cron now handles the review inbox.")
            return
        time.sleep(2)
    raise TimeoutError("Pairing expired; run setup again")


def pair_monitor():
    """Capture the monitor group's chat_id into the existing config.

    Requires the bot already paired (setup done). The user adds the bot to a
    Telegram group and sends any message; this polls for a non-private chat
    update and records its id as monitor_chat_id. Never touches the token or
    the private chat.
    """
    if not CONFIG.exists():
        raise ValueError("Run setup first to pair the private chat")
    config = json.loads(CONFIG.read_text())
    if config.get("monitor_chat_id"):
        raise ValueError("Monitor channel already paired")
    api = API(config["token"])
    print("Add this bot to a Telegram GROUP, then send any message in that group.", flush=True)
    print("Waiting up to 3 minutes to capture the group…", flush=True)
    deadline, offset = time.monotonic() + 180, 0
    while time.monotonic() < deadline:
        updates = api.call("getUpdates", offset=offset, timeout=0,
                           allowed_updates=["message", "my_chat_member"])
        for update in updates:
            offset = update["update_id"] + 1
            message = update.get("message", {}) or update.get("my_chat_member", {})
            chat = message.get("chat", {})
            if chat.get("type") not in {"group", "supergroup"} or chat.get("id") == config["chat_id"]:
                continue
            config["monitor_chat_id"] = chat["id"]
            fd = os.open(CONFIG, os.O_WRONLY | os.O_TRUNC)
            with os.fdopen(fd, "w") as handle:
                json.dump(config, handle, indent=2)
            print(f"Monitor channel paired: {chat.get('title', 'untitled')} ({chat['id']})")
            return
        time.sleep(2)
    raise TimeoutError("No group message seen; add the bot to a group and send a message")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action",required=True)
    config = sub.add_parser("setup")
    config.add_argument("--every",type=int,choices=range(1,101),default=5)
    config.add_argument("--basis",choices=["commit","deployment","off"],default="off")
    sub.add_parser("monitor")
    sub.add_parser("preview")
    change = sub.add_parser("record-change")
    change.add_argument("--product",required=True)
    change.add_argument("--kind",choices=["commit","deployment"],required=True)
    change.add_argument("--revision",required=True)
    change.add_argument("--summary",required=True)
    signal = sub.add_parser("record-signal")
    signal.add_argument("--scope",required=True)
    signal.add_argument("--polarity",choices=["positive","negative"],required=True)
    signal.add_argument("--text",required=True)
    args = parser.parse_args()
    if args.action == "setup":
        try:
            setup(args.every,args.basis)
        except (TelegramError, ValueError, OSError) as exc:
            print(f"Setup stopped: {exc}",file=sys.stderr)
            print("Bot configuration exists; inspect setup state before retrying." if CONFIG.exists()
                  else "Nothing was saved. Your token has not been printed or logged.",file=sys.stderr)
            raise SystemExit(1) from None
        return
    if args.action == "monitor":
        try:
            pair_monitor()
        except (TelegramError, ValueError, OSError) as exc:
            print(f"Monitor pairing stopped: {exc}", file=sys.stderr)
            raise SystemExit(1) from None
        return
    conn = connect(DEFAULT_STATE)
    schema(conn)
    try:
        if args.action == "record-change":
            record_change(conn,args.product,args.kind,args.revision,args.summary)
        elif args.action == "record-signal":
            record_signal(conn,args.scope,args.polarity,args.text)
            print("Signal recorded; delivered to the private chat on the next tick.")
        else:
            collect_reviews(conn,DEFAULT_STATE)
            print(json.dumps([dict(r) for r in conn.execute("SELECT message,delivery,decision,channel FROM telegram_cards")],indent=2))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
