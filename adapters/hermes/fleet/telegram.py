"""Dedicated Telegram review inbox; driven by the existing Hermes no-model tick.

This bot must not also be registered with the Hermes chat gateway: one getUpdates
consumer owns its offset. Arbitrary messages never become agent instructions.
"""
import argparse
import getpass
import hashlib
import html
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
        if method not in {"getMe", "getWebhookInfo", "getUpdates", "sendMessage", "answerCallbackQuery",
                          "editMessageText", "sendChatAction"}:
            raise ValueError("Unsupported Telegram operation")
        # Linked here rather than at each call site, so no message can ship a
        # jargon word without the explainer behind it. A call site that wants
        # emphasis only (the "decision recorded" edit, which re-renders a card
        # TK already read) opts out by passing a pre-rendered linkify() entry.
        if method in {"sendMessage", "editMessageText"} and payload.get("text") and "parse_mode" not in payload:
            payload["text"] = linkify(payload["text"], glossary=not payload.pop("_plain_text", False))
            payload["parse_mode"] = "HTML"
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
        CREATE TABLE IF NOT EXISTS agent_os_inspections (
            task_id TEXT PRIMARY KEY, inspector_task_id TEXT, verdict TEXT,
            failed TEXT, cycles INTEGER NOT NULL DEFAULT 0, snapshot TEXT
        );
        CREATE TABLE IF NOT EXISTS telegram_directives (
            id INTEGER PRIMARY KEY, ts REAL NOT NULL, text TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'captured', task_id TEXT
        );
        CREATE TABLE IF NOT EXISTS backlog_board_map (
            work_id TEXT PRIMARY KEY, task_id TEXT NOT NULL
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
        "telegram_cards": {"channel": "TEXT NOT NULL DEFAULT 'private'", "feedback": "TEXT"},
        # Local attribution. The portable contract declares owning_agent; this is
        # where the runtime reads it without re-parsing the payload. NULL is
        # meaningful: unattributed work is a workforce coverage gap, not an error.
        "agent_os_orders": {"owning_agent": "TEXT"},
        # A verdict is only about the files it was given. Without the snapshot it
        # was formed against, a later change silently inherits an old approval.
        "agent_os_inspections": {"snapshot": "TEXT"},
        # A directive started from the backlog via /next carries the backlog
        # work_id so the routed order can be stamped with board provenance.
        "telegram_directives": {"backlog_work_id": "TEXT"},
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


AI_FROM_ZERO = "https://ashwood-info.vercel.app/ai-from-zero/"

# One mark per agent, so who is speaking is legible before the text is read.
# Cheaper than a bot per agent and it survives being forwarded.
AGENT_EMOJI = {
    "eugene": "\U0001F527",    # builder
    "w-dog": "\U0001F415",     # watchdog
    "rook": "\U0001F6E1",      # adversarial review
    "ledger": "\U0001F4B0",    # economics
    "marlo": "\u270D",         # writing
    "scout": "\U0001F52D",     # external signal
    "zoie": "\U0001F4A1",      # strategy
    "bill": "\U0001F4CB",      # sequencing
    "router": "\U0001F9ED",    # coordination
    "steward": "\u2696",       # priority
    "designer": "\U0001F3A8",  # experience
    "milchik": "\U0001F3A9",   # floor manager
}


def badge(agent):
    """Agent name with its mark, or a clear marker when nothing owns the work."""
    if not agent:
        return "\u2753 UNATTRIBUTED"
    return "%s %s" % (AGENT_EMOJI.get(agent.lower(), "\u25AA"), agent.replace("-", " ").title())

# Words that are jargon to a reader who does not build this system. Each one is
# linked to the explainer the first time it appears in a message. A term with no
# entry here does not belong in a card: link it or do not use it.
GLOSSARY = {
    "agent": "agent",
    "agents": "agent",
    "handoff": "handoff",
    "context": "context-control",
    "ecosystem": "ecosystem",
}


def linkify(text, glossary=True):
    """Escape for Telegram HTML and, unless disabled, link the first use of each
    jargon word.

    One pass over the escaped text, so a link is never inserted inside a link.
    Only the first occurrence of each term is linked — repeating it turns the
    message into a wall of blue. The `glossary=False` path still renders
    emphasis and code but leaves words plain, for the "decision recorded" edit
    that re-renders a card TK has already read.
    """
    escaped = html.escape(text)
    # Emphasis is written as **bold** / __italic__ / `code` and converted only
    # AFTER escaping, so markup an agent puts in its own summary is inert text
    # while the card's own emphasis still renders.
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped, flags=re.S)
    escaped = re.sub(r"__(.+?)__", r"<i>\1</i>", escaped, flags=re.S)
    escaped = re.sub(r"`([^`\n]+)`", r"<code>\1</code>", escaped)
    if not glossary:
        return escaped
    used = set()
    pattern = re.compile(r"\b(" + "|".join(sorted(GLOSSARY, key=len, reverse=True)) + r")\b", re.IGNORECASE)

    def replace(match):
        word = match.group(0)
        anchor_name = GLOSSARY[word.lower()]
        if anchor_name in used:
            return word
        used.add(anchor_name)
        return f'<a href="{AI_FROM_ZERO}#{anchor_name}">{word}</a>'

    return pattern.sub(replace, escaped)


def short(value, limit=500):
    return str(value).replace("\x00", "")[:limit]


INSPECTION_SUFFIX = "-inspection"


def request_inspection(conn, state, now=None):
    """Have W Dog check finished work before it ever reaches TK.

    Nothing should arrive for approval having been seen only by the agent that
    produced it. HANDOFF_POLICY.md already requires a producer/inspector loop
    with a named independent domain, acceptance criteria and a termination
    condition; this is that loop's first half.

    The inspector is read-only and checks the producer's output against the
    acceptance criteria the work item declared, so it cannot quietly fix what it
    was asked to judge.
    """
    from .bridge import enqueue
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now or time.time()))
    for row in conn.execute("SELECT * FROM agent_os_orders WHERE phase='review'").fetchall():
        # An inspection is itself a task reaching review. Inspecting it would
        # recurse forever, and there is no third party to break the tie.
        if row["work_id"].endswith(INSPECTION_SUFFIX):
            continue
        if conn.execute("SELECT 1 FROM agent_os_inspections WHERE task_id=?", (row["task_id"],)).fetchone():
            continue
        try:
            order = json.loads(row["payload"])
        except ValueError:
            continue
        inspection = {
            "work_id": order["work_id"] + INSPECTION_SUFFIX,
            "routing_source": "registry/product-routing.yaml",
            "source_product": "agent-os-workforce",
            "owning_product": order["owning_product"],
            "owning_agent": "w-dog",
            "workspace": order["workspace"],
            "problem_or_opportunity": {
                "statement": "Work is finished and unchecked by anyone but the agent that did it.",
                "producer": row["owning_agent"] or "unattributed",
                "producer_work_id": order["work_id"],
            },
            "priority": {"level": "p1", "confidence": 1.0},
            "desired_outcome": {
                "verdict": "PASS or FAIL against each acceptance criterion, with the evidence checked.",
                "boundary": "Judge only. Do not fix, improve, or extend the work.",
            },
            "required_capabilities": ["filesystem"],
            "constraints": {
                "read_only": "Change no files. You are checking, not producing.",
                "criteria": "Report per criterion. A failure must cite what you looked at, "
                            "not a preference for a different approach.",
                "independence": "Do not accept the producer's own summary as evidence. "
                                "Open what it claims to have changed.",
                "verdict_format": "Begin your summary with a line reading exactly 'VERDICT: PASS' or "
                                  "'VERDICT: FAIL', then the per-criterion detail. This line is read "
                                  "by machine; prose around it is read by people.",
            },
            "acceptance_criteria": [
                "Its summary's FIRST LINE is exactly 'VERDICT: PASS' or 'VERDICT: FAIL' and nothing else",
                "States PASS or FAIL for every acceptance criterion of " + order["work_id"],
                "Cites the file or output examined for each verdict",
                "Changes no files",
                "Names what it could not check and why",
            ],
            "status": "approved",
            "created_at": stamp,
        }
        try:
            inspector_task = enqueue(state, inspection, authority=f"inspection-of:{order['work_id']}")
        except (ValueError, OSError):
            # Recorded as unavailable rather than silently skipped: TK must be
            # told the check did not happen, not left to assume it did.
            conn.execute("""INSERT OR REPLACE INTO agent_os_inspections
                (task_id,inspector_task_id,verdict,failed,cycles) VALUES (?,?,?,?,0)""",
                (row["task_id"], None, "unavailable", "Inspector could not be started."))
            continue
        conn.execute("""INSERT OR REPLACE INTO agent_os_inspections
            (task_id,inspector_task_id,verdict,failed,cycles) VALUES (?,?,NULL,NULL,1)""",
            (row["task_id"], inspector_task))


def read_inspection_verdicts(conn, state):
    """Record each finished inspector's verdict against the work it checked."""
    from hermes_cli import kanban_db as kb
    pending = conn.execute(
        "SELECT * FROM agent_os_inspections WHERE verdict IS NULL AND inspector_task_id IS NOT NULL").fetchall()
    for row in pending:
        order = conn.execute("SELECT * FROM agent_os_orders WHERE task_id=?", (row["inspector_task_id"],)).fetchone()
        if not order or order["phase"] not in {"review", "accepted", "done"}:
            continue
        record_path = Path(state) / order["task_id"] / f"{order['attempts']}.json"
        checkpoint = {}
        if record_path.exists():
            try:
                checkpoint = json.loads(json.loads(record_path.read_text()).get("checkpoint_text", "{}"))
            except ValueError:
                pass
        summary = str(checkpoint.get("summary", ""))
        # Read the declared verdict line. Searching the prose for "FAIL" reads a
        # report that says "all five PASS, none FAIL" as a failure, which sends
        # correct work back around the loop and eventually escalates it as the
        # producer's fault.
        first = summary.strip().splitlines()[0].strip().upper() if summary.strip() else ""
        if first == "VERDICT: PASS":
            verdict = "pass"
        elif first == "VERDICT: FAIL":
            verdict = "fail"
        else:
            # Neither churn nor silently accept. Defaulting to fail costs a wasted
            # cycle and blames the producer; defaulting to pass ships unchecked
            # work. Hand the judgement to TK with the text in front of him.
            verdict = "unreadable"
        try:
            inspected = fingerprint(conn.execute("SELECT * FROM agent_os_orders WHERE task_id=?",
                                                 (row["task_id"],)).fetchone())
        except (OSError, ValueError, subprocess.SubprocessError):
            inspected = None
        conn.execute("UPDATE agent_os_inspections SET verdict=?, failed=?, snapshot=? WHERE task_id=?",
                     (verdict, short(summary, 600), inspected, row["task_id"]))
        # The inspector's own order is consumed the moment its verdict is read.
        # Leaving it in review would park a W Dog report as if it were pending
        # TK's decision, cluttering /status with work that already did its job.
        if order["phase"] == "review":
            inspector = kb.get_task(conn, order["task_id"])
            if inspector and inspector.status == "review":
                kb.complete_task(conn, order["task_id"], result=verdict,
                                 summary="Inspection verdict consumed by the loop.")


MAX_REVISION_CYCLES = 2


def run_revisions(conn, state, now=None):
    """Send failed work back to its producer, within bounds.

    HANDOFF_POLICY.md sets the terminations: acceptance reached, cycle cap hit,
    the same disagreement repeating without new evidence, or the next decision
    belonging to a human. All four end the loop here rather than iterating.

    The producer receives only the failed criteria — the policy is explicit that
    inspection must not become a free-form conversation.
    """
    from .bridge import enqueue
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now or time.time()))
    failures = conn.execute("SELECT * FROM agent_os_inspections WHERE verdict='fail'").fetchall()
    for row in failures:
        order_row_ = conn.execute("SELECT * FROM agent_os_orders WHERE task_id=?", (row["task_id"],)).fetchone()
        if not order_row_ or order_row_["phase"] != "review":
            continue
        try:
            order = json.loads(order_row_["payload"])
        except ValueError:
            continue
        # The attempt counter must live where the schema allows and where it
        # survives a revision: the problem_or_opportunity object, which already
        # carries the revision lineage. Every revision is a new task_id whose
        # inspection row restarts at cycles=1, so a per-row counter can never
        # reach MAX_REVISION_CYCLES and the loop runs away.
        depth = int((order.get("problem_or_opportunity") or {}).get("revision_cycle", 0))
        attempt = depth + 1
        prior_failed = (order.get("problem_or_opportunity") or {}).get("failed_criteria", "")
        repeated = bool(prior_failed) and prior_failed.strip() == (row["failed"] or "").strip()
        if attempt >= MAX_REVISION_CYCLES or repeated:
            reason = ("the same problem came back unchanged" if repeated
                      else f"it has been round {attempt} times")
            conn.execute("UPDATE agent_os_inspections SET verdict='escalated' WHERE task_id=?", (row["task_id"],))
            conn.execute("INSERT OR IGNORE INTO telegram_cards(id,event_key,expires,message) VALUES (?,?,?,?)",
                (secrets.token_urlsafe(12), f"escalation:{row['task_id']}:{attempt}", time.time()+604800,
                 f"{(order_row_['owning_agent'] or 'An agent').title()} could not get this right, "
                 f"and I have stopped trying.\n\n"
                 f"WHAT WAS ASKED\n  {short(order.get('work_id',''), 120)}\n\n"
                 f"WHY I STOPPED\n  I sent it back and {reason}.\n\n"
                 f"WHAT IS STILL WRONG\n  {short(row['failed'], 400)}\n\n"
                 "Nothing was published. The files are on the machine as the agent left them.\n"
                 "This needs you or a different owner."))
            continue
        revision = dict(order)
        revision["work_id"] = f"{order['work_id']}-rev{attempt + 1}"
        revision["created_at"] = stamp
        revision["problem_or_opportunity"] = dict(order.get("problem_or_opportunity") or {})
        revision["problem_or_opportunity"].update({
            "statement": "A previous attempt failed its independent check.",
            "original_work_id": order["work_id"],
            "failed_criteria": short(row["failed"], 1500),
            "revision_cycle": attempt,
        })
        revision["constraints"] = dict(order.get("constraints") or {})
        revision["constraints"]["revision"] = (
            "Fix only the failed criteria listed above. Do not redo passing work "
            "and do not widen scope.")
        try:
            enqueue(state, revision, authority=f"revision-of:{order['work_id']}")
        except (ValueError, OSError):
            conn.execute("UPDATE agent_os_inspections SET verdict='escalated' WHERE task_id=?", (row["task_id"],))
            continue
        conn.execute("""UPDATE agent_os_inspections SET verdict=NULL, cycles=?, inspector_task_id=NULL
            WHERE task_id=?""", (attempt, row["task_id"]))


# Where each product is actually reachable. Nothing is inferred from a repo name.
PRODUCTION_URL = {
    "ashwood": "https://ashwood-info.vercel.app",
    "alvira-meos": "https://alviratech.vercel.app",
}
REPO_SLUG = {
    "ashwood": "tk-ap/ashwood-info",
    "alvira-meos": "tk-ap/ALVIRA",
    "agent-os-workforce": "tk-ap/agent-os",
}


def publishable():
    """What is committed locally and not yet published, per project.

    Every push to a branch triggers a build, so publishing one approval at a
    time spends a deployment per decision. This is the batch view: approvals
    accumulate as commits, and one press sends them together.
    """
    out = []
    for label, directory, _slug in PROJECTS:
        path = ROOT.parent / directory
        if not (path / ".git").exists():
            continue
        branch = (_run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=path) or "").strip()
        if not branch or branch == "HEAD":
            continue
        upstream = _run(["git", "rev-parse", "--abbrev-ref", "@{u}"], cwd=path)
        if not upstream:
            continue                      # No upstream: nothing to publish to yet.
        ahead = _run(["git", "rev-list", "--count", "@{u}..HEAD"], cwd=path)
        count = int(ahead.strip()) if ahead and ahead.strip().isdigit() else 0
        if not count:
            continue
        files = _run(["git", "diff", "--name-only", "@{u}..HEAD"], cwd=path) or ""
        subjects = _run(["git", "log", "--format=%s", "@{u}..HEAD"], cwd=path) or ""
        out.append({
            "key": directory,
            "label": label,
            "path": str(path),
            "branch": branch,
            "commits": count,
            "files": len([f for f in files.splitlines() if f.strip()]),
            "subjects": [s for s in subjects.splitlines() if s.strip()][:3],
            "url": PRODUCTION_URL.get({"ashwood": "ashwood", "ALVIRA": "alvira-meos"}.get(directory, "")),
        })
    return out


def publish_branch(entry):
    """Push one project's current branch. Never forced, never a different branch."""
    workspace = Path(entry["path"])
    current = (_run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=workspace) or "").strip()
    if current != entry["branch"]:
        # The branch moved between showing the card and pressing it.
        raise ValueError(f"branch changed from {entry['branch']} to {current}; nothing published")
    git(workspace, "push", "origin", f"{current}:{current}")
    revision = git(workspace, "rev-parse", "--short", "HEAD").decode().strip()
    return f"{entry['label']}: pushed {entry['commits']} commits to {current} ({revision})."


def links_for(order):
    """Live links for a card: PR, preview deployment, production.

    Every one is looked up, never constructed. A link that would 404 is worse
    than no link — it invites a tap that teaches you not to trust the next one.
    Anything unavailable is simply omitted.
    """
    lines, product = [], order.get("owning_product", "")
    workspace = Path(order.get("workspace", "."))
    slug = REPO_SLUG.get(product)
    branch = None
    try:
        branch = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=workspace, timeout=10)
        branch = branch.strip() if branch else None
    except Exception:
        branch = None

    if slug and branch and branch != "HEAD":
        raw = _run(["gh", "pr", "view", branch, "--repo", slug, "--json", "url,number,isDraft,comments"],
                   timeout=30)
        if raw:
            try:
                pr = json.loads(raw)
            except ValueError:
                pr = None
            if pr and pr.get("url"):
                state_word = "draft" if pr.get("isDraft") else "ready"
                lines.append(f"  PR #{pr['number']} ({state_word}) — {pr['url']}")
                previews = set()
                for comment in pr.get("comments") or []:
                    previews.update(re.findall(r"https://[a-z0-9.-]*vercel\.app[^\s)\]]*",
                                               comment.get("body", "")))
                for preview in sorted(previews)[:1]:
                    lines.append(f"  Preview of this branch — {preview}")

    live = PRODUCTION_URL.get(product)
    if live:
        lines.append(f"  Live site (unchanged by this) — {live}")
    return lines


def collect_reviews(conn, state):
    from hermes_cli import kanban_db as kb
    for row in conn.execute("SELECT * FROM agent_os_orders WHERE phase IN ('review','blocked','revoked')").fetchall():
        task = kb.get_task(conn, row["task_id"])
        if task.status not in {"review", "blocked"}:
            continue
        # An inspection is a task too; it is W Dog's report, not TK's decision.
        if row["work_id"].endswith(INSPECTION_SUFFIX):
            continue
        inspection = conn.execute("SELECT * FROM agent_os_inspections WHERE task_id=?",
                                  (row["task_id"],)).fetchone()
        if inspection is None or inspection["verdict"] is None:
            # Held, not dropped. Work reaches TK checked or not at all.
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
        # Written for TK, who is not reading this as an engineer. Plain words,
        # the decision first, and the limits stated rather than implied.
        tries = row["attempts"]
        summary = checkpoint.get("summary") or "The agent did not say what it did."
        text = f"{badge(row['owning_agent'])} finished something. **Your call.**\n\n"
        text += f"**WHAT IT DID**\n  {short(summary, 320)}\n\n"
        text += f"**WHERE**\n  {order['owning_product']} · `{short(order['work_id'],80)}`\n\n"
        if stamp:
            text += "**IS IT SAFE TO SAY YES?**\n"
            text += f"  It finished cleanly{' on the first try' if tries == 1 else f', after {tries} tries'}. "
            text += "The files are exactly as it left them.\n"
        else:
            text += "**SOMETHING IS OFF**\n"
            text += "  I could not take a reliable snapshot of the files, so there is no\n"
            text += "  safe Accept here. Have a look on the machine before deciding.\n"
        verdict = inspection["verdict"]
        # The verdict belongs to the files W Dog opened. If they have moved since,
        # it is not a second opinion on what TK is being asked to approve.
        if verdict == "pass" and inspection["snapshot"] and stamp and inspection["snapshot"] != stamp:
            verdict = "stale"
        if verdict == "pass":
            text += "\n**SECOND OPINION**\n"
            text += "  W Dog checked this independently and found no problems.\n"
            text += f"  {short(inspection['failed'], 240)}\n"
        elif verdict == "fail":
            text += "\n**SECOND OPINION — PROBLEMS FOUND**\n"
            text += f"  {short(inspection['failed'], 400)}\n"
            text += "  __Saying yes here accepts work that failed its own checks.__\n"
        elif verdict == "stale":
            text += "\n**SECOND OPINION NO LONGER APPLIES**\n"
            text += "  W Dog passed this, then the files changed. Its approval was\n"
            text += "  about the earlier version, not the one in front of you now.\n"
        elif verdict == "unreadable":
            text += "\n**SECOND OPINION — UNCLEAR**\n"
            text += "  W Dog checked this but did not give a clean yes or no, so I\n"
            text += "  cannot tell you which it was. Here is what it said:\n"
            text += f"  {short(inspection['failed'], 400)}\n"
        else:
            text += "\n**NO SECOND OPINION**\n"
            text += "  The independent check could not run, so this has been seen only\n"
            text += "  by the agent that did it. That is not meant to happen.\n"
        text += "\nEither way, nothing is published, deployed, or visible to anyone\n"
        text += "outside this machine.\n"
        text += "\n**YOUR OPTIONS**\n"
        text += "\n".join(describe_publish(order)) + "\n"
        text += "\n".join(describe_feedback()) + "\n"
        text += "  Pause — stop for now. Nothing is deleted.\n"
        found = links_for(order)
        if found:
            text += "\n**LINKS**\n" + "\n".join(found) + "\n"
        text += f"\nFiles are on your machine at:\n  `{record_path.parent}`"
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
        # Awareness, not a decision. The private chat is for work that cannot
        # proceed without TK; a commit digest can always proceed without him.
        conn.execute("INSERT OR IGNORE INTO telegram_cards(id,event_key,expires,message,channel) VALUES (?,?,?,?,?)",
                     (secrets.token_urlsafe(12),key,time.time()+604800,text,"monitor"))
        conn.executemany("UPDATE telegram_changes SET reported=1 WHERE id=?", [(r['id'],) for r in rows])


def _fleet_line(kind, detail):
    """One compact line per fleet event. detail is already a dict from the event store."""
    d = detail or {}
    if kind == "queued":
        return "· Added to the queue, waiting for a free worker"
    if kind == "claim":
        if d.get("outcome") == "denied":
            return f"✕ Not allowed to start — {d.get('reason', 'no valid authority')}"
        attempt = d.get("attempts", 0)
        return "· Picked up" + ("" if attempt <= 1 else f", retry {attempt}")
    if kind == "start":
        return f"· Working, using {d.get('harness', 'an unknown tool')}"
    if kind == "result":
        return f"· Finished: {d.get('result', 'no result recorded')}"
    if kind == "phase":
        readable = {"review": "Finished, going for an independent check", "done": "Closed",
                    "blocked": "Stuck", "revoked": "Stopped", "queued": "Back in the queue"}
        phase = d.get("phase", "?")
        line = "· " + readable.get(phase, f"Now: {phase}")
        return line + (f" — {d.get('reason')}" if d.get("reason") else "")
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
        lines = [f"\U0001F3A9 Milchik — `{short(work_id, 80) or task_id}`"]
        for event, detail in group:
            lines.append(_fleet_line(event["kind"], detail))
        key = f"fleet:{task_id}:{group[-1][0]['id']}"
        conn.execute("INSERT OR IGNORE INTO telegram_cards(id,event_key,expires,message,channel) VALUES (?,?,?,?,?)",
                     (secrets.token_urlsafe(12), key, time.time()+86400, "\n".join(lines), "monitor"))
    conn.execute("INSERT OR REPLACE INTO telegram_meta VALUES ('fleet_watermark',?)", (str(events[-1]["id"]),))


def route_directives(conn, state, now=None):
    """Turn captured directives into routing tasks.

    Choosing an owner is judgement and needs a model. *Asking* for that
    judgement does not: every field of the routing work item is fixed except
    the directive text, so this scheduler tick can enqueue the question without
    ever answering it. The model runs in the worker, where it is attributed and
    its result is reviewable.

    Router owns the routing decision (agents/router/IDENTITY.md), so the task is
    attributed to router and its output is a proposal, not an assignment.
    """
    from .bridge import enqueue
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now or time.time()))
    for row in conn.execute(
            "SELECT id, text, backlog_work_id FROM telegram_directives WHERE status='captured' ORDER BY id").fetchall():
        problem = {
            "statement": "A directive from TK has no owner, priority, or lane.",
            "directive": row["text"],
            "captured_as": f"telegram_directives#{row['id']}",
        }
        # Backlog-started work carries canonical board provenance. The board row
        # is the sync mirror; enqueue rejects the order if it is missing or done.
        if row["backlog_work_id"]:
            board = conn.execute("SELECT task_id FROM backlog_board_map WHERE work_id=?",
                                 (row["backlog_work_id"],)).fetchone()
            problem["origin"] = "autonomous_backlog"
            problem["backlog_system"] = "hermes-kanban"
            problem["backlog_work_id"] = row["backlog_work_id"]
            problem["board_item_id"] = board[0] if board else None
        order = {
            "work_id": f"directive-{row['id']}-routing",
            "routing_source": "registry/product-routing.yaml",
            "source_product": "agent-os-workforce",
            "owning_product": "agent-os-workforce",
            "owning_agent": "router",
            "workspace": str(ROOT),
            "problem_or_opportunity": problem,
            "priority": {"level": "p1", "confidence": 1.0},
            "desired_outcome": {
                "proposal": "One owning agent, a priority level, a lane, and the reasoning for each.",
                "boundary": "Propose only. Do not start the directed work.",
            },
            "required_capabilities": ["filesystem"],
            "constraints": {
                "propose_only": "Return a routing proposal. Do not execute the directive.",
                "registry": "Choose the owner from registry/agents.yaml by `owns` domain, "
                            "minimum sufficient team, applying the agent-vs-skill test.",
                "lane": "ecosystem for operating-layer work, directive for product work.",
            },
            "acceptance_criteria": [
                "Names one owning agent that exists in registry/agents.yaml",
                "States a priority level p0-p3 with a reason",
                "States the lane and why",
                "States what it deliberately did NOT decide, per HANDOFF_POLICY.md articulation",
                "Does not begin the directed work",
            ],
            "status": "approved",
            "created_at": stamp,
        }
        try:
            task_id = enqueue(state, order, authority=f"human-directive:{row['id']}")
        except (ValueError, OSError) as exc:
            conn.execute("UPDATE telegram_directives SET status='route_failed' WHERE id=?", (row["id"],))
            conn.execute("INSERT OR IGNORE INTO telegram_cards(id,event_key,expires,message) VALUES (?,?,?,?)",
                         (secrets.token_urlsafe(12), f"directive-failed:{row['id']}", time.time()+604800,
                          f"Directive #{row['id']} could not be routed.\n\n{short(str(exc),300)}\n\n"
                          "It stays recorded and unassigned. Nothing was started."))
            continue
        conn.execute("UPDATE telegram_directives SET status='routing', task_id=? WHERE id=?",
                     (task_id, row["id"]))


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
        problem = order.get("problem_or_opportunity")
        if isinstance(problem, dict):
            problem = problem.get("statement") or next(iter(problem.values()), "not stated")
        lines = [f"{badge(row['owning_agent'])} · `{short(order.get('work_id',''),60)}` · "
                 f"{order.get('owning_product','?')}"]
        lines.append("")
        lines.append("**WHY THIS WAS DONE**")
        lines.append(f"  {short(problem, 280)}")

        did = checkpoint.get("contributions") or checkpoint.get("summary")
        lines.append("")
        lines.append("**WHAT IT SAYS IT DID**")
        lines.append(f"  {short(did, 280) if did else 'It did not say.'}")

        lines.append("")
        lines.append("**WHAT ACTUALLY HAPPENED**")
        lines.append(f"  Ran on {record.get('harness','an unknown tool')}, "
                     f"{'first try' if row['attempts'] == 1 else str(row['attempts']) + ' tries'}, "
                     f"ended as: {short(record.get('result','not recorded'), 80)}")
        lines.append("")
        lines.append("  __The two sections above are the agent describing itself.__")
        lines.append("  __This line is the only part taken from the record.__")
        if row["phase"] == "review":
            inspection = conn.execute("SELECT verdict FROM agent_os_inspections WHERE task_id=?",
                                      (row["task_id"],)).fetchone()
            lines.append("")
            if row["work_id"].endswith(INSPECTION_SUFFIX):
                lines.append("This was the check. The work it judged moves on from here.")
            elif inspection is None or inspection["verdict"] is None:
                # Saying TK has it while an agent still holds it invites him to go
                # looking for a decision that is not there.
                lines.append("Still with the workforce — being checked independently.")
            elif inspection["verdict"] == "pass":
                lines.append("Checked and passed. TK has the decision in the private chat.")
            else:
                lines.append("The check did not pass. Back to the workforce, not to TK.")
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
                 (secrets.token_urlsafe(12), key, time.time()+86400, text[:3900], "monitor"))
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


def eligible_backlog_item():
    """Highest-ranked backlog item Milchik is actually allowed to start.

    IDENTITY.md §09: he may enqueue only work that is `source: human`
    (pre-authorized by TK's own intent) or already `approved`. A high rank on an
    unapproved agent proposal is attention, not permission, so those are skipped
    rather than started.
    """
    try:
        import yaml
        from runtime import backlog as backlog_runtime
        items = yaml.safe_load((ROOT / "agents/milchik/backlog.yaml").read_text()) or []
    except Exception:
        return None, "I could not read the backlog."
    open_items = [i for i in items if i.get("status") != "done"]
    if not open_items:
        return None, "The backlog is empty."
    for item in backlog_runtime.rank(open_items):
        if backlog_runtime.authority_present(item) or item.get("status") == "approved":
            return item, None
    return None, ("Nothing in the backlog is cleared to start. The top items are "
                  "proposals waiting on your approval.")


def sync_backlog_to_board(conn):
    """Mirror open backlog items onto the Hermes Kanban board.

    The board is the canonical executable backlog
    (docs/proposals/MILCHIK_HERMES_KANBAN_CONTROL.md). backlog.yaml remains
    Milchik's auditable ranking model; this keeps one blocked board row per
    open item so backlog work always has canonical board provenance and the
    board's priority column mirrors the ranking. Mirror rows are blocked —
    the fleet dispatcher only claims tasks with an agent_os_orders row, so a
    mirror row is a queue record, never a dispatch unit. When backlog.yaml
    marks an item done, its mirror row is closed.
    """
    from hermes_cli import kanban_db as kb
    try:
        import yaml
        from runtime import backlog as backlog_runtime
        items = yaml.safe_load((ROOT / "agents/milchik/backlog.yaml").read_text()) or []
    except (OSError, ImportError):
        return {"synced": 0, "closed": 0}
    open_by_id = {item["work_id"]: item for item in items if item.get("status") != "done"}
    synced = closed = 0
    for work_id, task_id in conn.execute(
            "SELECT work_id, task_id FROM backlog_board_map").fetchall():
        if work_id not in open_by_id:
            task = kb.get_task(conn, task_id)
            if task is not None and task.status != "done":
                kb.complete_task(conn, task_id,
                    result="Backlog item completed or removed from backlog.yaml",
                    summary="Mirror row closed by backlog sync.")
                closed += 1
    for work_id, item in open_by_id.items():
        score = int(backlog_runtime.attention_score(item))
        existing = conn.execute(
            "SELECT task_id FROM backlog_board_map WHERE work_id=?", (work_id,)).fetchone()
        if existing:
            task = kb.get_task(conn, existing[0])
            if task is None:
                conn.execute("DELETE FROM backlog_board_map WHERE work_id=?", (work_id,))
                existing = None
        if not existing:
            task_id = kb.create_task(conn, title=work_id, body=json.dumps(item),
                assignee="milchik", created_by="agent-os-backlog-sync",
                workspace_kind="dir", workspace_path=str(ROOT),
                idempotency_key="agent-os-backlog:" + work_id,
                max_runtime_seconds=120, max_retries=0, initial_status="blocked")
            conn.execute("INSERT OR REPLACE INTO backlog_board_map(work_id,task_id) VALUES (?,?)",
                         (work_id, task_id))
            synced += 1
        else:
            task_id = existing[0]
        conn.execute("UPDATE tasks SET priority=? WHERE id=?", (score, task_id))
    conn.commit()
    return {"synced": synced, "closed": closed}


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
    directives = conn.execute("""SELECT id, text, status FROM telegram_directives
        WHERE status != 'closed' ORDER BY id""").fetchall()
    if directives:
        lines.append("")
        lines.append(f"YOUR DIRECTIVES  {len(directives)} open")
        state_label = {"captured": "not yet routed", "routing": "routing proposal in progress",
                       "route_failed": "ROUTING FAILED — still unassigned"}
        for row in directives[:5]:
            lines.append(f"  #{row['id']} {short(row['text'], 56)}")
            lines.append(f"      {state_label.get(row['status'], row['status'])}")

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


def publish_choices(order):
    """The decisions this card offers, widest consequence last.

    TK picks the consequence at decision time rather than the work item picking
    it for him. A card that can deploy also offers the smaller commit, so
    approving the work and publishing it stay separate choices.
    """
    action = order.get("publish_action") or {}
    kind = action.get("kind")
    count = len(action.get("paths", []))
    plural = "s" if count != 1 else ""
    where = Path(order.get("workspace", ".")).name
    choices = []
    if kind in {"commit", "deploy"}:
        choices.append(("commit", "Approve & save",
                        f"saves {count} file{plural} into {where}. Still nothing online."))
    if kind == "deploy":
        choices.append(("deploy", "Approve & publish",
                        f"saves {count} file{plural} AND puts them **live for anyone** at "
                        f"{action.get('deploys_to', 'the site')}. __This one leaves your machine.__"))
    if not choices:
        choices.append(("accept", "Approve", "closes the job and publishes nothing."))
    return choices


# Distinct feedback TK can select instead of one vague "needs changes". Each
# entry is (action, button label, structured reason). The reason is what the
# producer actually receives, so the feedback is input, not just a rejection.
FEEDBACK_CHOICES = [
    ("redo", "Wrong direction", "Rethink the approach. The current one does not answer what was asked."),
    ("addmore", "Not finished", "The work is incomplete. Finish what was asked before it is reviewed again."),
    ("trim", "Too much", "It did more than asked. Narrow it to the stated scope."),
    ("offvoice", "Off voice", "The content is off-register for this surface. Rewrite in the correct voice."),
    ("wrongclaim", "Unsupported claim", "A claim has no supporting evidence. Remove it or source it."),
]


def describe_feedback():
    """The option lines for the card, one per distinct feedback choice."""
    return [f"  {label} — {reason}" for _action, label, reason in FEEDBACK_CHOICES]


def feedback_action(action):
    """Return the structured reason for a feedback button, or None if not feedback."""
    for name, _label, reason in FEEDBACK_CHOICES:
        if name == action:
            return reason
    return None


def describe_publish(order):
    """The option lines for the card, one per available decision."""
    return [f"  {label} — {detail}" for _action, label, detail in publish_choices(order)]


def perform_publish(order, row, chosen="accept"):
    """Carry out the decision TK actually pressed, and nothing wider.

    `chosen` is the button, not the work item's ceiling. A card may offer deploy
    and be answered with save; the smaller choice is always honoured, and the
    work item can only narrow what is on offer, never widen what was pressed.

    Only the declared paths are committed. The card's fingerprint has already
    proven the files are exactly as they were reviewed, so what is published is
    what was approved.
    """
    action = order.get("publish_action") or {}
    if action.get("kind") not in {"commit", "deploy"} or chosen == "accept":
        return None
    workspace = Path(order["workspace"]).resolve()
    paths = action.get("paths") or []
    if not paths:
        raise ValueError("commit declared with no paths")
    for candidate in paths:
        target = (workspace / candidate).resolve()
        if not str(target).startswith(str(workspace) + os.sep):
            raise ValueError(f"path escapes the workspace: {candidate}")
    branch, remote = action.get("branch"), action.get("remote", "origin")
    if chosen == "deploy":
        # Validate BEFORE committing. Checking after would leave a commit behind
        # every time a publish was refused — a partial action from a guard whose
        # whole purpose is to let nothing happen.
        if not branch:
            raise ValueError("publishing was declared without a branch")
        current = git(workspace, "rev-parse", "--abbrev-ref", "HEAD").decode().strip()
        if current != branch:
            raise ValueError(f"declared branch {branch} but the workspace is on {current}")
    git(workspace, "add", "--", *paths)
    # Already committed is not an error. Pressing save and then publish is the
    # normal two-step, and the second press must still be able to publish.
    try:
        git(workspace, "diff", "--cached", "--quiet", "--", *paths)
        staged = False
    except subprocess.CalledProcessError:
        staged = True
    if staged:
        message = action.get("message") or f"{order['work_id']} (approved by TK through Milchik)"
        git(workspace, "-c", "user.name=Milchik", "-c", "user.email=milchik@agent-os.invalid",
            "commit", "-m", message, "--", *paths)
    revision = git(workspace, "rev-parse", "--short", "HEAD").decode().strip()
    if chosen != "deploy":
        return f"Saved as {revision} in {workspace.name}. Not published anywhere."
    # Never forced. A rejected push means someone else moved the branch, which is
    # a conversation to have, not a state to overwrite.
    git(workspace, "push", remote, f"{branch}:{branch}")
    target = action.get("deploys_to")
    return (f"Saved as {revision} and published to {remote}/{branch}."
            + (f" {target} goes live in a minute or two." if target else ""))


def decide(conn, config, query):
    """Only authenticated, unexpired, single-use callbacks can accept a frozen result."""
    from hermes_cli import kanban_db as kb
    message = query.get("message", {})
    if (query.get("from",{}).get("id") != config["user_id"] or
        message.get("chat",{}).get("id") != config["chat_id"]):
        return "Not authorized"
    parts = str(query.get("data", "")).split(":")
    feedback_actions = {name for name, _label, _reason in FEEDBACK_CHOICES}
    valid = {"accept","commit","deploy","pause"} | feedback_actions
    if len(parts) != 3 or parts[0] != "aos" or parts[2] not in valid:
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
    approving = action in {"accept", "commit", "deploy"}
    if approving:
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
    if approving:
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
        result = "Accepted. Nothing published."
        try:
            order = json.loads(row["payload"])
        except ValueError:
            order = {}
        try:
            published = perform_publish(order, order_row(conn, task.id), chosen=action)
            if published:
                result = "Accepted. " + published
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            # The acceptance stands; only the publish failed. Saying otherwise
            # would leave TK believing work was saved when it was not.
            result = f"Accepted, but saving failed: {short(str(exc), 120)}"
    else:
        # Feedback and pause both stop further execution. Feedback is distinct
        # input the producer receives, not just a rejection: record it on the
        # order and name it in the confirmation so it is not lost.
        reason = feedback_action(action)
        conn.execute("UPDATE agent_os_orders SET revoked=1,phase=? WHERE task_id=?", (action,task.id))
        if reason:
            conn.execute("UPDATE telegram_cards SET feedback=? WHERE id=?", (reason, card["id"]))
            result = "Sent back with feedback: " + reason
        else:
            result = "Execution paused."
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
            actions = []
            if card["snapshot"]:
                order_row_ = conn.execute("SELECT payload FROM agent_os_orders WHERE task_id=?",
                                          (card["task_id"],)).fetchone()
                try:
                    approved = json.loads(order_row_["payload"]) if order_row_ else {}
                except (ValueError, TypeError):
                    approved = {}
                actions = [(label, name) for name, label, _detail in publish_choices(approved)]
            actions += [(label, name) for name, label, _reason in FEEDBACK_CHOICES]
            actions += [("Pause", "pause")]
            # One row per button: "Approve & publish" must never sit inches from
            # "Approve & save" on a phone.
            payload["reply_markup"] = {"inline_keyboard":[
                [{"text":label,"callback_data":f"aos:{card['id']}:{action}"}] for label,action in actions]}
        # Ambiguous sends are never automatically retried (Telegram has no idempotency key).
        conn.execute("UPDATE telegram_cards SET delivery='uncertain' WHERE id=?", (card["id"],))
        result = api.call("sendMessage", **payload)
        conn.execute("UPDATE telegram_cards SET delivery='sent',message_id=? WHERE id=?", (result["message_id"],card["id"]))


def handle_update(conn, config, api, update):
    """Act on one Telegram update. Shared by the minute tick and the listener."""
    if "callback_query" in update and str(update["callback_query"].get("data","")).startswith("pub:"):
        # Batch publish. Separate from decide(), which answers a review card: this
        # approves no work, it only sends already-approved commits out.
        query = update["callback_query"]
        if (query.get("from",{}).get("id") != config["user_id"]
                or query.get("message",{}).get("chat",{}).get("id") != config["chat_id"]):
            answer = "Not authorized"
        else:
            key = str(query.get("data","")).split(":",1)[1]
            entry = next((e for e in publishable() if e["key"] == key), None)
            if not entry:
                answer = "Nothing left to publish there."
            else:
                try:
                    answer = publish_branch(entry)
                except (OSError, ValueError, subprocess.SubprocessError) as exc:
                    answer = f"Not published: {short(str(exc), 150)}"
        try:
            api.call("answerCallbackQuery", callback_query_id=query["id"],
                     text=answer[:190], show_alert=True)
            api.call("sendMessage", chat_id=config["chat_id"], text=answer,
                     link_preview_options={"is_disabled": True})
        except TelegramError:
            pass
    elif "callback_query" in update:
        query = update["callback_query"]
        response = decide(conn,config,query)
        try:
            api.call("answerCallbackQuery",callback_query_id=query["id"],text=response[:190],show_alert=True)
        except TelegramError:
            pass  # Decision is persisted even when Telegram's short callback TTL expires.
        parts = str(query.get("data", "")).split(":")
        if len(parts) == 3:
            card = conn.execute("SELECT * FROM telegram_cards WHERE id=?", (parts[1],)).fetchone()
            decided = {"accept","commit","deploy","pause"} | {n for n,_l,_r in FEEDBACK_CHOICES}
            if card and card["decision"] in decided and card["decided_by"] == config["user_id"]:
                try:
                    suffix = card["decision"] + (" — " + card["feedback"] if card["feedback"] else "")
                    api.call("editMessageText", chat_id=config["chat_id"], message_id=card["message_id"],
                        text=card["message"][:3500]+"\n\nDecision recorded: "+suffix,
                        reply_markup={"inline_keyboard":[]}, _plain_text=True)
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
        # First word only, so "/do fix the sitemap" matches the command
        # while the rest stays as the directive text.
        head = body.split(None, 1)[0] if body.split() else ""
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
        directive = None
        if text.startswith(">"):
            directive = text[1:].strip()
        elif head == "/do":
            parts = text.split(None, 1)
            directive = parts[1].strip() if len(parts) > 1 else ""
        if (directive is not None and sender == config["user_id"]
                and chat == config["chat_id"] and directive):
            # Recorded as a directive, NOT executed. Free-form text is
            # still not an agent prompt: this writes a row and answers
            # with what it wrote. Turning it into work needs routing,
            # which needs a model, which this tick does not have.
            conn.execute("INSERT INTO telegram_directives(ts,text) VALUES (?,?)",
                         (time.time(), short(directive, 2000)))
            number = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            try:
                api.call("sendMessage",chat_id=chat,
                    text=f"Got it — #{number}. I will come back when I need you.",
                    link_preview_options={"is_disabled":True})
            except TelegramError:
                pass
        elif (sender == config["user_id"] and chat == config["chat_id"]
                and directive == ""):
            try:
                api.call("sendMessage",chat_id=chat,
                    text="Empty directive. Put the instruction after > or /do.",
                    link_preview_options={"is_disabled":True})
            except TelegramError:
                pass
        elif (sender == config["user_id"] and chat == config["chat_id"]
                and text and not text.startswith("/")):
            # Ignoring this silently is the dangerous option: it looks
            # identical to a captured directive that never ran.
            try:
                api.call("sendMessage",chat_id=chat,text=(
                    "Not recorded. Prefix a directive with > or /do — "
                    "plain messages here are not instructions."),
                    link_preview_options={"is_disabled":True})
            except TelegramError:
                pass
        if body == "/publish" and sender == config["user_id"] and chat == config["chat_id"]:
            ready = publishable()
            if not ready:
                reply, keyboard = "Nothing waiting to be published.", None
            else:
                lines = ["**Ready to publish** — one push each, one build each.", ""]
                for entry in ready:
                    lines.append(f"{entry['label']} · `{entry['branch']}`")
                    lines.append(f"  {entry['commits']} commits · {entry['files']} files")
                    for subject in entry["subjects"]:
                        lines.append(f"  · {short(subject, 62)}")
                    if entry["url"]:
                        lines.append(f"  __goes live at {entry['url']}__")
                    lines.append("")
                lines.append("__Nothing is published until you press one.__")
                reply = "\n".join(lines)
                keyboard = {"inline_keyboard": [
                    [{"text": f"Publish {e['label']} ({e['commits']})",
                      "callback_data": f"pub:{e['key']}"}] for e in ready]}
            try:
                payload = {"chat_id": chat, "text": reply,
                           "link_preview_options": {"is_disabled": True}}
                if keyboard:
                    payload["reply_markup"] = keyboard
                api.call("sendMessage", **payload)
            except TelegramError:
                pass
        if body == "/next" and sender == config["user_id"] and chat == config["chat_id"]:
            item, refusal = eligible_backlog_item()
            if refusal:
                reply = refusal
            else:
                problem = item.get("problem") or item.get("title", "")
                conn.execute("INSERT INTO telegram_directives(ts,text,backlog_work_id) VALUES (?,?,?)",
                             (time.time(), short("%s\n\n%s" % (item.get("title", ""), problem), 2000),
                              item.get("work_id")))
                number = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                reply = ("Starting #%d: %s\n\nPicked because it is %s and %s. "
                         "Routing it now — I will come back when someone needs to decide something."
                         % (number, short(item.get("title", ""), 140),
                            item.get("priority", {}).get("level", "p3"),
                            "yours" if item.get("source") == "human" else "already approved"))
            try:
                api.call("sendMessage", chat_id=chat, text=reply,
                         link_preview_options={"is_disabled": True})
            except TelegramError:
                pass
        if body == "/status" and sender == config["user_id"] and chat in {
                config["chat_id"], config.get("monitor_chat_id")}:
            # Say something before the work starts. Building the status calls out
            # to GitHub and git for every project, and silence during that is
            # indistinguishable from never having received the message.
            try:
                api.call("sendChatAction", chat_id=chat, action="typing")
            except TelegramError:
                pass
            try:
                api.call("sendMessage",chat_id=chat,text=status_report(conn,config)[:3500],
                    link_preview_options={"is_disabled":True})
            except TelegramError:
                pass  # A missed status reply is recoverable; the next /status re-reads live state.


LISTENER_STALE_AFTER = 90


def listener_is_live(conn, now=None):
    """True when a listener has checked in recently enough to own the poll."""
    row = conn.execute("SELECT value FROM telegram_meta WHERE key='listener_heartbeat'").fetchone()
    if not row:
        return False
    try:
        return (now or time.time()) - float(row[0]) < LISTENER_STALE_AFTER
    except (TypeError, ValueError):
        return False


def listen(state=DEFAULT_STATE, config_path=CONFIG, api=None, once=False):
    """Long-poll Telegram so a message is answered in seconds, not on the tick.

    The minute tick is fine for delivering cards but leaves up to a minute of
    silence after TK sends something, which reads exactly like the bot being
    down. This holds a long poll open and handles updates as they land.

    There is still only ever ONE poller. While this process heartbeats, the tick
    skips getUpdates and does collection and delivery only; if this dies, the
    heartbeat goes stale within 90 seconds and the tick resumes polling on its
    own. Confirming a getUpdates offset makes Telegram forget earlier updates,
    so two live pollers would steal each other's messages.
    """
    if not Path(config_path).exists():
        return {"status": "not_configured"}
    config = json.loads(Path(config_path).read_text())
    if not config.get("enabled"):
        return {"status": "disabled"}
    api = api or API(config["token"])
    conn = connect(state)
    try:
        schema(conn)
        while True:
            conn.execute("INSERT OR REPLACE INTO telegram_meta VALUES ('listener_heartbeat',?)",
                         (str(time.time()),))
            # The lock is held around state, never around the long poll. flock is
            # blocking, so waiting inside it would stall the minute tick for the
            # whole 25 seconds, every minute.
            with lock(Path(state) / "telegram.lock"):
                row = conn.execute("SELECT value FROM telegram_meta WHERE key='offset'").fetchone()
                offset = int(row[0]) if row else 0
            try:
                updates = api.call("getUpdates", offset=offset, timeout=25, limit=25,
                                   allowed_updates=["callback_query", "message", "my_chat_member"])
            except TelegramError:
                updates = []              # Transport hiccup; the next poll retries.
            if updates:
                with lock(Path(state) / "telegram.lock"):
                    for update in updates:
                        config = json.loads(Path(config_path).read_text())  # setup may have changed it
                        handle_update(conn, config, api, update)
                        conn.execute("INSERT OR REPLACE INTO telegram_meta VALUES ('offset',?)",
                                     (str(update["update_id"] + 1),))
            if once:
                return {"status": "ok", "handled": len(updates)}
    finally:
        conn.close()


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
            # One poller only. A live listener owns getUpdates; this tick then
            # does collection and delivery and touches no updates.
            if listener_is_live(conn):
                updates = []
            else:
                offset = conn.execute("SELECT value FROM telegram_meta WHERE key='offset'").fetchone()
                updates = api.call("getUpdates",offset=int(offset[0]) if offset else 0,
                    timeout=0,limit=25,allowed_updates=["callback_query","message","my_chat_member"])
            for update in updates:
                handle_update(conn, config, api, update)
                conn.execute("INSERT OR REPLACE INTO telegram_meta VALUES ('offset',?)", (str(update['update_id']+1),))
            request_inspection(conn,state)
            read_inspection_verdicts(conn,state)
            run_revisions(conn,state)
            collect_reviews(conn,state)
            if config["basis"] == "commit":
                collect_commits(conn,config.get("repositories",{}))
            collect_batches(conn,config["every"],config["basis"])
            collect_fleet(conn)
            sync_backlog_to_board(conn)
            route_directives(conn,state)
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
    sub.add_parser("listen")
    sub.add_parser("e2e")
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
    if args.action == "listen":
        print(json.dumps(listen()))
        return
    if args.action == "e2e":
        from .e2e import main as e2e_main
        raise SystemExit(e2e_main())
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
