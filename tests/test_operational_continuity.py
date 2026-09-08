import sqlite3
import tempfile
import time
import unittest
from pathlib import Path

from adapters.hermes.fleet import telegram_operational_continuity as continuity


SCHEMA = """
CREATE TABLE tasks (id TEXT PRIMARY KEY, status TEXT NOT NULL);
CREATE TABLE agent_os_orders (
  task_id TEXT,
  work_id TEXT,
  phase TEXT,
  revoked INTEGER NOT NULL DEFAULT 0,
  expires REAL NOT NULL DEFAULT 4102444800
);
CREATE TABLE agent_os_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts REAL NOT NULL,
  task_id TEXT NOT NULL,
  kind TEXT NOT NULL,
  detail TEXT NOT NULL
);
CREATE TABLE telegram_directives (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts REAL NOT NULL,
  text TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'captured',
  task_id TEXT,
  backlog_work_id TEXT
);
CREATE TABLE objective_leases (
  id TEXT PRIMARY KEY, valid_until REAL NOT NULL, revoked INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE telegram_cards (
  id TEXT PRIMARY KEY, event_key TEXT UNIQUE NOT NULL, expires REAL NOT NULL,
  message TEXT NOT NULL, channel TEXT NOT NULL DEFAULT 'private'
);
"""


def root_with_backlog(text):
    temp = tempfile.TemporaryDirectory()
    root = Path(temp.name)
    target = root / "agents" / "milchik"
    target.mkdir(parents=True)
    (target / "backlog.yaml").write_text(text)
    return temp, root


def conn():
    value = sqlite3.connect(":memory:")
    value.row_factory = sqlite3.Row
    value.executescript(SCHEMA)
    return value


def add_order(db, task_id, work_id, phase, task_status, *, event_age=0, revoked=0):
    db.execute("INSERT INTO tasks(id,status) VALUES (?,?)", (task_id, task_status))
    db.execute(
        "INSERT INTO agent_os_orders(task_id,work_id,phase,revoked,expires) VALUES (?,?,?,?,?)",
        (task_id, work_id, phase, revoked, time.time() + 86400),
    )
    if event_age is not None:
        db.execute(
            "INSERT INTO agent_os_events(ts,task_id,kind,detail) VALUES (?,?,?,?)",
            (time.time() - event_age, task_id, "phase", "{}"),
        )


class OperationalContinuityTests(unittest.TestCase):
    def test_starts_one_explicitly_approved_item_when_idle(self):
        temp, root = root_with_backlog("""
- work_id: proof-1
  source: ailhat
  status: approved
  lane: directive
  priority: {level: p1, confidence: 0.8}
  title: Validate the live scan
  problem: Check current production truth before mutation.
""")
        self.addCleanup(temp.cleanup)
        db = conn()
        result = continuity.ignite(db, root)
        self.assertEqual(result["status"], "started")
        directive = db.execute("SELECT * FROM telegram_directives").fetchone()
        self.assertEqual(directive["backlog_work_id"], "proof-1")
        self.assertEqual(db.execute("SELECT count(*) FROM telegram_cards").fetchone()[0], 1)

    def test_agent_proposal_does_not_start_without_approval(self):
        temp, root = root_with_backlog("""
- work_id: proposal-1
  source: agent
  status: proposed
  priority: {level: p0, confidence: 1.0}
  title: Maybe do this
""")
        self.addCleanup(temp.cleanup)
        db = conn()
        result = continuity.ignite(db, root)
        self.assertEqual(result["status"], "idle-no-cleared-work")
        self.assertEqual(db.execute("SELECT count(*) FROM telegram_directives").fetchone()[0], 0)

    def test_running_fleet_does_not_start_another_item(self):
        temp, root = root_with_backlog("""
- work_id: proof-1
  source: human
  status: approved
  priority: {level: p1, confidence: 1.0}
  title: Existing approved work
""")
        self.addCleanup(temp.cleanup)
        db = conn()
        add_order(db, "task-live", "existing-work", "running", "running")
        result = continuity.ignite(db, root)
        self.assertEqual(result["status"], "busy")
        self.assertEqual(db.execute("SELECT count(*) FROM telegram_directives").fetchone()[0], 0)

    def test_fresh_review_briefly_blocks_new_ignition(self):
        temp, root = root_with_backlog("""
- work_id: proof-1
  source: human
  status: approved
  priority: {level: p1, confidence: 1.0}
  title: Existing approved work
""")
        self.addCleanup(temp.cleanup)
        db = conn()
        add_order(db, "task-review", "review-work", "review", "review", event_age=30)
        result = continuity.ignite(db, root)
        self.assertEqual(result["status"], "busy")

    def test_stale_review_remains_open_but_does_not_freeze_floor(self):
        temp, root = root_with_backlog("""
- work_id: proof-1
  source: human
  status: approved
  priority: {level: p1, confidence: 1.0}
  title: Continue useful work
""")
        self.addCleanup(temp.cleanup)
        db = conn()
        add_order(
            db,
            "task-review",
            "review-work",
            "review",
            "review",
            event_age=continuity.HUMAN_WAIT_BUSY_SECONDS + 1,
        )
        result = continuity.ignite(db, root)
        self.assertEqual(result["status"], "started")

    def test_superseded_review_does_not_freeze_floor(self):
        temp, root = root_with_backlog("""
- work_id: proof-1
  source: human
  status: approved
  priority: {level: p1, confidence: 1.0}
  title: Continue useful work
""")
        self.addCleanup(temp.cleanup)
        db = conn()
        add_order(db, "task-old", "directive-2-routing", "review", "review", event_age=20)
        add_order(db, "task-new", "directive-2-routing-rev2", "blocked", "blocked", event_age=10)
        result = continuity.ignite(db, root)
        self.assertEqual(result["status"], "started")

    def test_blocked_queued_card_does_not_masquerade_as_moving_work(self):
        temp, root = root_with_backlog("""
- work_id: proof-1
  source: human
  status: approved
  priority: {level: p1, confidence: 1.0}
  title: Continue useful work
""")
        self.addCleanup(temp.cleanup)
        db = conn()
        add_order(db, "task-stuck", "directive-8-routing", "queued", "blocked", event_age=10)
        result = continuity.ignite(db, root)
        self.assertEqual(result["status"], "started")

    def test_stale_captured_directive_does_not_freeze_floor(self):
        temp, root = root_with_backlog("""
- work_id: proof-1
  source: human
  status: approved
  priority: {level: p1, confidence: 1.0}
  title: Continue useful work
""")
        self.addCleanup(temp.cleanup)
        db = conn()
        db.execute(
            "INSERT INTO telegram_directives(ts,text,status) VALUES (?,?,?)",
            (time.time() - continuity.HUMAN_WAIT_BUSY_SECONDS - 1, "old", "captured"),
        )
        result = continuity.ignite(db, root)
        self.assertEqual(result["status"], "started")

    def test_release_pending_is_not_rebuilt_and_is_surfaced_once(self):
        temp, root = root_with_backlog("""
- work_id: release-1
  source: agent
  status: release_pending
  priority: {level: p1, confidence: 0.9}
  title: Fix sitemap
  completed:
    evidence: commit abc123
    note: committed but NOT yet deployed
""")
        self.addCleanup(temp.cleanup)
        db = conn()
        first = continuity.ignite(db, root)
        second = continuity.ignite(db, root)
        self.assertEqual(first["release_cards"], 1)
        self.assertEqual(second["release_cards"], 0)
        self.assertEqual(db.execute("SELECT count(*) FROM telegram_directives").fetchone()[0], 0)
        self.assertEqual(db.execute("SELECT count(*) FROM telegram_cards").fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
