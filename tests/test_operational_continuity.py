import sqlite3
import tempfile
import unittest
from pathlib import Path

from adapters.hermes.fleet import telegram_operational_continuity as continuity


SCHEMA = """
CREATE TABLE agent_os_orders (task_id TEXT, phase TEXT);
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

    def test_busy_fleet_does_not_start_another_item(self):
        temp, root = root_with_backlog("""
- work_id: proof-1
  source: human
  status: approved
  priority: {level: p1, confidence: 1.0}
  title: Existing approved work
""")
        self.addCleanup(temp.cleanup)
        db = conn()
        db.execute("INSERT INTO agent_os_orders VALUES ('task-live','review')")
        result = continuity.ignite(db, root)
        self.assertEqual(result["status"], "busy")
        self.assertEqual(db.execute("SELECT count(*) FROM telegram_directives").fetchone()[0], 0)

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
