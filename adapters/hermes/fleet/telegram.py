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
        CREATE TABLE IF NOT EXISTS telegram_directives (
            id INTEGER PRIMARY KEY, ts REAL NOT NULL, text TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'captured', task_id TEXT
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
    additions = {
        "telegram_cards": {"channel": "TEXT NOT NULL DEFAULT 'private'"},
        # Local attribution. The portable contract declares owning_agent; this is
        # where the runtime reads it without re-parsing the payload. NULL is
        # meaningful: unattributed work is a workforce coverage gap, not an error.
        "agent_os_orders": {"owning_agent": "TEXT"},
    }
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


def collect_contributions(conn, state):
    """Post the reasoning behind a change to the monitor channel.

    This is the record that otherwise does not survive. Commits show what
    changed; the private chat holds the decision; neither holds why the change
    was proposed or what was deliberately left undone. A transcript holds both
    and is thrown away.

    Claim and record are kept visually separate on purpose. Per
    agents/milchik/IDENTITY.md §12 a self-report is labeled and checked, never
    laundered into fact — an agent describing its own contribution is evidence
    of what it believes it did, not of what happened.
    """
    rows = conn.execute("""SELECT * FROM agent_os_orders
        WHERE phase IN ('review','done','blocked')""").fetchall()
    for row in rows:
        record_path = Path(state) / row["task_id"] / f"{row['attempts']}.json"
        record = json.loads(record_path.read_text()) if record_path.exists() else {}
        checkpoint = {}
        try:
            checkpoint = json.loads(record.get("checkpoint_text", "{}"))
        except ValueError:
            pass
        try:
            order = json.loads(row["payload"])
        except ValueError:
            continue
        key = f"contribution:{row['task_id']}:{row['attempts']}"
        agent = row["owning_agent"] or "UNATTRIBUTED"
        lines = [f"{order.get('owning_product','?')} · {short(order.get('work_id',''),60)} · {agent}"]
        lines.append("")
        lines.append("WHY")
        lines.append(f"  {short(order.get('problem_or_opportunity','not stated'), 300)}")

        did = checkpoint.get("contributions") or checkpoint.get("summary")
        lines.append("DID  [agent's own account]")
        lines.append(f"  {short(did, 300) if did else 'No account given — the agent did not state what it did.'}")

        did_not = checkpoint.get("non_contributions")
        lines.append("DID NOT  [agent's own account]")
        if did_not:
            lines.append(f"  {short(did_not, 300)}")
        else:
            # HANDOFF_POLICY.md: a report silent about what was held back has not
            # stated its boundary, and omission is a defect rather than a blank.
            lines.append("  Not stated. Omission is a defect: the boundary was not declared.")

        lines.append("RECORD  [verified]")
        lines.append(f"  phase {row['phase']} · attempt {row['attempts']} · harness {record.get('harness','unknown')}")
        lines.append(f"  result {short(record.get('result','not recorded'), 120)}")
        checks = checkpoint.get("verification")
        lines.append(f"  worker-reported checks: {short(checks, 160) if checks else 'none'}")
        lines.append(f"  evidence: {record_path.parent}")
        if row["phase"] == "review":
            lines.append("")
            lines.append("Awaiting your decision in the private chat.")
        conn.execute("INSERT OR IGNORE INTO telegram_cards(id,event_key,expires,message,channel) VALUES (?,?,?,?,?)",
                     (secrets.token_urlsafe(12), key, time.time()+604800, "\n".join(lines), "monitor"))


def value_ledger(conn):
    """Per-agent outcomes from decisions actually made, plus coverage gaps.

    Scored from TK's recorded accept / needs-changes / pause decisions rather
    than from anything an agent says about itself — the only value signal here
    that is not a self-report.

    Work with no owning agent is reported rather than hidden: a domain nothing
    owns is the workforce gap worth seeing.
    """
    rows = conn.execute("""SELECT o.owning_agent AS agent, c.decision AS decision, COUNT(*) AS n
        FROM telegram_cards c JOIN agent_os_orders o ON o.task_id = c.task_id
        WHERE c.decision IS NOT NULL GROUP BY o.owning_agent, c.decision""").fetchall()
    tally = {}
    for row in rows:
        tally.setdefault(row["agent"] or "UNATTRIBUTED", {})[row["decision"]] = row["n"]
    unattributed = conn.execute(
        "SELECT COUNT(*) FROM agent_os_orders WHERE owning_agent IS NULL").fetchone()[0]
    return tally, unattributed


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


def monitor_chat_of(message, private_id):
    """The chat the founder is designating as the monitor channel, else (None, None).

    Two ways in, because one of them cannot be relied on. Telegram privacy mode
    stops a non-admin bot from receiving ordinary group messages at all, so
    waiting for a direct group message can wait forever. Forwarding a message
    from that group into the private chat carries the origin chat id regardless,
    and is the only path that also works for channels.
    """
    chat = message.get("chat", {})
    if chat.get("type") in {"group", "supergroup"} and chat.get("id") != private_id:
        return chat["id"], chat.get("title", "untitled")
    origin = message.get("forward_origin") or {}
    if origin.get("type") in {"channel", "chat"}:
        source = origin.get("chat", {})
        if source.get("id") and source["id"] != private_id:
            return source["id"], source.get("title", "untitled")
    legacy = message.get("forward_from_chat") or {}
    if legacy.get("type") in {"channel", "group", "supergroup"} and legacy.get("id") != private_id:
        return legacy["id"], legacy.get("title", "untitled")
    return None, None


def save_config(config, config_path=CONFIG):
    """Replace the config atomically, preserving its restrictive mode."""
    target = Path(config_path)
    temporary = target.with_suffix(".tmp")
    fd = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w") as handle:
        json.dump(config, handle, indent=2)
    os.replace(temporary, target)


PROJECTS = (
    ("ALVIRA",   "ALVIRA",       "tk-ap/ALVIRA"),
    ("ASHWOOD",  "ashwood",      "tk-ap/ashwood-info"),
    ("AGENT OS", "agent-os",     "tk-ap/agent-os"),
)


def _run(args, cwd=None, timeout=20):
    """Run a read-only command, returning stdout or None. Never raises."""
    try:
        done = subprocess.run(args, cwd=cwd, capture_output=True, timeout=timeout, check=True)
        return done.stdout.decode(errors="replace")
    except (OSError, subprocess.SubprocessError):
        return None


def project_state():
    """Per-project PR and local-change facts, for the glanceable view.

    Every field degrades to None rather than failing the report: an offline
    workstation should still get task and backlog state.
    """
    states = []
    for label, directory, slug in PROJECTS:
        path = ROOT.parent / directory
        if not (path / ".git").exists():
            continue
        state = {"label": label, "slug": slug, "prs": None, "commits": 0, "dirty": False}
        raw = _run(["gh", "pr", "list", "-R", slug, "--state", "open",
                    "--json", "number,title,headRefName,isDraft", "--limit", "20"])
        if raw is not None:
            try:
                state["prs"] = json.loads(raw)
            except ValueError:
                state["prs"] = None
        log = _run(["git", "log", "--since=24 hours ago", "--oneline"], cwd=path)
        state["commits"] = len(log.strip().splitlines()) if log and log.strip() else 0
        status = _run(["git", "status", "--porcelain"], cwd=path)
        state["dirty"] = bool(status and status.strip())
        states.append(state)
    return states


def overlaps(states):
    """Branches with an open PR in more than one project.

    A shared branch name across repositories is coordinated work spanning
    products — the case worth surfacing, because nothing else in the system
    shows it.
    """
    branches = {}
    for state in states:
        for pull in state["prs"] or []:
            branches.setdefault(pull["headRefName"], set()).add(state["label"])
    return {branch: sorted(labels) for branch, labels in branches.items() if len(labels) > 1}


def backlog_top(k=3):
    """Top-ranked open backlog items, or None if unreadable.

    Ranking decides attention, never execution.
    """
    try:
        import yaml
        from runtime import backlog as backlog_runtime
        items = yaml.safe_load((ROOT / "agents/milchik/backlog.yaml").read_text()) or []
        # runtime/backlog.py scores on priority and confidence alone and does not
        # consider status, so a completed item keeps its rank forever. Excluding
        # `done` here rather than there leaves that scoring contract untouched.
        open_items = [item for item in items if item.get("status") != "done"]
        return [(item, backlog_runtime.attention_score(item),
                 backlog_runtime.authority_present(item),
                 backlog_runtime.lane(item)) for item in backlog_runtime.next_for_attention(open_items, k)]
    except Exception:
        return None


def status_report(conn, config):
    """Milchik's founder view: what is in flight, where, and what needs TK.

    Written to be read at a glance and grouped by project, because the question
    behind it is "what is happening across the businesses", not "what rows are
    in the database".

    Two rules from agents/milchik/IDENTITY.md still bind: activity is never
    reported as progress (§08), and figures name their source (§12) — collected
    into one footer rather than annotating every line.
    """
    now = time.time()
    lines = ["Mr. Milchik"]

    states = project_state()
    lines.append("")
    for state in states:
        prs = state["prs"]
        if prs is None:
            detail = "PRs unavailable"
        elif prs:
            ready = sum(1 for pull in prs if not pull.get("isDraft"))
            detail = f"{len(prs)} open PR{'s' if len(prs) != 1 else ''} ({ready} ready, {len(prs)-ready} draft)"
        else:
            detail = "no open PRs"
        marks = []
        if state["commits"]:
            marks.append(f"{state['commits']} commit{'s' if state['commits'] != 1 else ''} today")
        if state["dirty"]:
            marks.append("uncommitted")
        bullet = "*" if (prs or state["commits"] or state["dirty"]) else "-"
        lines.append(f"{bullet} {state['label']:<9} {detail}")
        if marks:
            lines.append(f"            {' · '.join(marks)}")

    shared = overlaps(states)
    concurrent = [state["label"] for state in states if state["commits"]]
    if shared or len(concurrent) > 1:
        lines.append("")
        lines.append("OVERLAPPING REPOS")
        for branch, labels in sorted(shared.items()):
            # The precise signal: one branch carrying open PRs in two products.
            lines.append(f"  {short(branch,44)}")
            lines.append(f"    open in {' + '.join(labels)}")
        if len(concurrent) > 1:
            # The coarse one: several products moving the same day. Concurrent
            # change is not necessarily related change — it is a prompt to look.
            lines.append(f"  changed today: {', '.join(concurrent)}")

    awaiting = conn.execute("""SELECT task_id, message FROM telegram_cards
        WHERE channel='private' AND decision IS NULL AND delivery='sent'
          AND task_id IS NOT NULL AND expires > ? ORDER BY expires LIMIT 5""", (now,)).fetchall()
    blocked = conn.execute("SELECT id, title FROM tasks WHERE status='blocked' ORDER BY started_at DESC LIMIT 5").fetchall()
    counts = {r["status"]: r["c"] for r in conn.execute(
        "SELECT status, count(*) c FROM tasks WHERE status IN ('running','review') GROUP BY status")}

    lines.append("")
    directives = conn.execute(
        "SELECT id, text FROM telegram_directives WHERE status='captured' ORDER BY id").fetchall()
    if directives:
        lines.append("")
        lines.append(f"YOUR DIRECTIVES  {len(directives)} unrouted")
        for row in directives[:5]:
            lines.append(f"  #{row['id']} {short(row['text'], 56)}")

    lines.append("")
    lines.append(f"AWAITING YOU   {len(awaiting)}")
    for row in awaiting:
        body = row["message"].splitlines()
        lines.append(f"  {short(body[1] if len(body) > 1 else row['task_id'], 60)}")
    lines.append(f"BLOCKED        {len(blocked)}")
    for row in blocked:
        lines.append(f"  {short(row['title'] or row['id'], 60)}")
    lines.append(f"FLEET          {counts.get('running',0)} running · {counts.get('review',0)} in review")

    ranked = backlog_top(2)
    if ranked:
        lines.append("")
        lines.append("NEXT UP")
        for item, _score, authorized, item_lane in ranked:
            who = "yours" if authorized else f"needs your approval ({item.get('status','proposed')})"
            lines.append(f"  {short(item.get('title', item.get('work_id','untitled')), 58)}")
            lines.append(f"    {item.get('priority',{}).get('level','p3')} · {item_lane} · {who}")
        # A directive at the top means it outranked open ecosystem work, which is
        # the soft gate being crossed rather than ignored. Say so.
        if ranked and ranked[0][3] == "directive":
            lines.append("  ^ directive ahead of ecosystem work — gate crossed on priority")
    elif ranked is None:
        lines.append("")
        lines.append("NEXT UP        backlog unreadable")

    pending = {r["channel"]: r["c"] for r in conn.execute(
        "SELECT channel, count(*) c FROM telegram_cards WHERE delivery='pending' GROUP BY channel")}
    if pending.get("monitor") and not config.get("monitor_chat_id"):
        lines.append("")
        lines.append(f"{pending['monitor']} monitor cards queued: channel not paired.")

    tally, unattributed = value_ledger(conn)
    if tally or unattributed:
        lines.append("")
        lines.append("AGENT OUTCOMES  [your decisions, not self-reports]")
        for agent, decisions in sorted(tally.items()):
            accepted = decisions.get("accept", 0)
            total = sum(decisions.values())
            lines.append(f"  {agent:<12} {accepted}/{total} accepted first time")
        if unattributed:
            lines.append(f"  {unattributed} work item(s) with no owning agent — coverage gap")

    lines.append("")
    lines.append("Recorded state only; running is not progress. Commits are not deployments.")
    lines.append("Sources: gh pr list · git log · review cards · milchik backlog.")
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
                timeout=0,limit=25,allowed_updates=["callback_query","message","my_chat_member"])
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
                elif "my_chat_member" in update:
                    # Fires when the bot is added to a group, and is delivered even
                    # under privacy mode — unlike an ordinary group message. Adding
                    # the bot is therefore enough to designate the monitor channel.
                    membership = update["my_chat_member"]
                    joined = (membership.get("new_chat_member") or {}).get("status") in {"member","administrator"}
                    chat = membership.get("chat", {})
                    if (joined and membership.get("from",{}).get("id") == config["user_id"]
                            and not config.get("monitor_chat_id")
                            and chat.get("type") in {"group","supergroup","channel"}
                            and chat.get("id") != config["chat_id"]):
                        config["monitor_chat_id"] = chat["id"]
                        save_config(config)
                        try:
                            api.call("sendMessage",chat_id=config["chat_id"],
                                text=f"Monitor channel paired: {short(chat.get('title','untitled'),80)} "
                                     f"({chat['id']}). Read-only fleet lines go there; approvals stay here.")
                        except TelegramError:
                            pass
                elif "message" in update:
                    # The ONLY text this bot acts on. Every other message is ignored:
                    # free-form Telegram text is not an agent prompt and grants no authority.
                    message = update["message"]
                    body = str(message.get("text","")).strip().split("@")[0].lower()
                    sender = message.get("from",{}).get("id")
                    chat = message.get("chat",{}).get("id")
                    if sender == config["user_id"] and not config.get("monitor_chat_id"):
                        # Capture here rather than in a second poller. Confirming a
                        # getUpdates offset makes Telegram forget earlier updates, so
                        # any separate pairing process races this tick and loses.
                        designated, title = monitor_chat_of(message, config["chat_id"])
                        if designated:
                            config["monitor_chat_id"] = designated
                            save_config(config)
                            try:
                                api.call("sendMessage",chat_id=config["chat_id"],
                                    text=f"Monitor channel paired: {short(title,80)} ({designated}). "
                                         "This group receives read-only fleet lines. "
                                         "Approvals stay in this private chat.")
                            except TelegramError:
                                pass
                    text = str(message.get("text","")).strip()
                    if (sender == config["user_id"] and chat == config["chat_id"]
                            and text and not text.startswith("/")):
                        # Recorded as a directive, NOT executed. Free-form text is
                        # still not an agent prompt: this writes a row and answers
                        # with what it wrote. Turning it into work needs routing,
                        # which needs a model, which this tick does not have.
                        conn.execute("INSERT INTO telegram_directives(ts,text) VALUES (?,?)",
                                     (time.time(), short(text, 2000)))
                        number = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                        try:
                            api.call("sendMessage",chat_id=chat,text=(
                                f"Directive #{number} recorded.\n\n"
                                f"{short(text,300)}\n\n"
                                "Not routed and not started. Nothing has been assigned to an agent "
                                "and no work has begun. It is queued for routing, which needs a "
                                "model pass this scheduler tick deliberately does not have."),
                                link_preview_options={"is_disabled":True})
                        except TelegramError:
                            pass
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
            collect_contributions(conn,state)
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
    """Wait for the fleet tick to capture a monitor channel, and report the result.

    This no longer polls getUpdates. A second poller cannot coexist with the
    minute tick: whichever confirms an offset first makes Telegram forget the
    update the other is waiting for. The tick owns the poll; this command owns
    the instructions and the wait.
    """
    if not CONFIG.exists():
        raise ValueError("Run setup first to pair the private chat")
    if json.loads(CONFIG.read_text()).get("monitor_chat_id"):
        raise ValueError("Monitor channel already paired")
    print("Add the bot to the Telegram group, then do EITHER:", flush=True)
    print("  • send any message in that group, or", flush=True)
    print("  • forward a message from that group into your private chat with the bot.", flush=True)
    print("Forwarding is the reliable one: privacy mode can stop the bot seeing group messages.", flush=True)
    print("The next fleet tick captures it. Waiting up to 3 minutes…", flush=True)
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        config = json.loads(CONFIG.read_text())
        if config.get("monitor_chat_id"):
            print(f"Monitor channel paired: {config['monitor_chat_id']}")
            return
        time.sleep(3)
    raise TimeoutError("Nothing captured. Confirm the fleet tick is running: hermes cron list")


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
