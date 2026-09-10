"""The digest is the surface TK reviews instead of babysitting the fleet.

These assert the properties that make it trustworthy: it arrives even when
nothing happened, it never arrives twice for one period, it says what the fleet
handled on its own, and it puts what actually needs a person last and plainly.
"""
import json
import sqlite3
import time
import unittest

from adapters.hermes.fleet import telegram_digest as digest


class FleetDigestTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript("""
            CREATE TABLE agent_os_orders (
                task_id TEXT PRIMARY KEY, work_id TEXT, payload TEXT,
                owning_agent TEXT, phase TEXT, attempts INTEGER,
                harnesses TEXT, next_at REAL
            );
            CREATE TABLE agent_os_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, task_id TEXT,
                kind TEXT, detail TEXT
            );
            CREATE TABLE agent_os_inspections (
                task_id TEXT PRIMARY KEY, inspector_task_id TEXT, verdict TEXT,
                failed TEXT, cycles INTEGER
            );
            CREATE TABLE agent_os_capacity (
                harness TEXT PRIMARY KEY, available_at REAL, reason TEXT
            );
            CREATE TABLE telegram_cards (
                id TEXT PRIMARY KEY, event_key TEXT UNIQUE, task_id TEXT,
                expires REAL, message TEXT, decision TEXT,
                channel TEXT DEFAULT 'private'
            );
            CREATE TABLE telegram_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        """)
        self.now = 1789000000.0

    def tearDown(self):
        self.conn.close()

    def _order(self, task_id, phase="review", directive="Restore the ailhat scan loop"):
        self.conn.execute(
            "INSERT INTO agent_os_orders VALUES (?,?,?,?,?,?,?,?)",
            (task_id, f"work-{task_id}",
             json.dumps({"work_id": f"work-{task_id}",
                         "problem_or_opportunity": {"directive": directive}}),
             "eugene", phase, 1, json.dumps(["codex-cli"]), 0))

    def _event(self, kind, detail, task_id="t-1", offset=-3600):
        self.conn.execute(
            "INSERT INTO agent_os_events(ts,task_id,kind,detail) VALUES (?,?,?,?)",
            (self.now + offset, task_id, kind, json.dumps(detail)))

    def _armed(self):
        """Establish the watermark one period back, as a running fleet would have."""
        self.conn.execute("INSERT OR REPLACE INTO telegram_meta VALUES (?,?)",
                          (digest.WATERMARK, str(self.now - digest.DEFAULT_PERIOD)))

    def _message(self):
        return self.conn.execute(
            "SELECT message FROM telegram_cards WHERE event_key LIKE 'digest:%'").fetchone()["message"]

    def test_first_run_arms_the_watermark_and_says_nothing(self):
        """A first digest covering all of history would be noise, not a summary."""
        self.assertEqual(digest.collect_digest(self.conn, now=self.now), 0)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM telegram_cards").fetchone()[0], 0)
        self.assertIsNotNone(self.conn.execute(
            "SELECT 1 FROM telegram_meta WHERE key=?", (digest.WATERMARK,)).fetchone())

    def test_a_digest_arrives_once_the_period_has_passed(self):
        self._armed()
        self.assertEqual(digest.collect_digest(self.conn, now=self.now), 1)

    def test_never_more_than_one_digest_per_period(self):
        self._armed()
        digest.collect_digest(self.conn, now=self.now)
        for tick in range(5):
            self.assertEqual(digest.collect_digest(self.conn, now=self.now + tick * 60), 0)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM telegram_cards").fetchone()[0], 1)

    def test_a_quiet_period_still_reports(self):
        """Silence is ambiguous: a healthy idle fleet and a dead one look alike."""
        self._armed()
        self.assertEqual(digest.collect_digest(self.conn, now=self.now), 1)
        message = self._message()
        self.assertIn("Nothing ran", message)
        self.assertIn("Needs you", message)
        self.assertIn("Nothing.", message)

    def test_it_reports_what_it_handled_without_the_operator(self):
        self._armed()
        self._order("t-1")
        self._event("result", {"result": "capacity", "harness": "codex-cli"})
        self._event("capacity_credit", {"seconds": 7200})
        self._event("superseded", {"reason": "a revision replaced it"})
        digest.collect_digest(self.conn, now=self.now)
        message = self._message()
        self.assertIn("Handled without you", message)
        self.assertIn("another harness", message)
        self.assertIn("120 minutes", message)
        self.assertIn("superseded attempt", message)

    def test_capacity_waits_are_named_as_needing_nothing(self):
        self._armed()
        self.conn.execute("INSERT INTO agent_os_capacity VALUES ('codex-cli',?,'usage_limit')",
                          (self.now + 3600,))
        digest.collect_digest(self.conn, now=self.now)
        message = self._message()
        self.assertIn("Waiting on provider capacity", message)
        self.assertIn("Nothing to do", message)

    def test_work_needing_a_person_is_listed_by_what_it_is(self):
        self._armed()
        self._order("t-9", phase="waiting_approval", directive="Publish the ailhat release")
        digest.collect_digest(self.conn, now=self.now)
        message = self._message()
        self.assertIn("Needs you — 1 item", message)
        self.assertIn("Publish the ailhat release", message)
        self.assertNotIn("t-9", message, "the operator was shown a task id, not the work")

    def test_escalations_and_undecided_cards_both_count_as_needing_you(self):
        self._armed()
        self._order("t-2", directive="Fix the routing proposal")
        self._order("t-3", directive="Check the workspace contract")
        self.conn.execute(
            """INSERT INTO telegram_cards(id,event_key,task_id,expires,message,decision,channel)
               VALUES ('c1','task:t-2','t-2',?,'card',NULL,'private')""", (self.now + 600,))
        self.conn.execute(
            "INSERT INTO agent_os_inspections VALUES ('t-3',NULL,'escalated','still wrong',2)")
        digest.collect_digest(self.conn, now=self.now)
        self.assertIn("Needs you — 2 items", self._message())

    def test_stopped_work_explains_why_it_is_not_being_retried(self):
        self._armed()
        self._order("t-4", phase="blocked", directive="Reach the deployment target")
        self._event("result", {"result": "permission", "harness": "codex-cli"}, task_id="t-4")
        digest.collect_digest(self.conn, now=self.now)
        message = self._message()
        self.assertIn("Stopped and not retrying", message)
        self.assertIn("Reach the deployment target", message)
        self.assertIn("never rotate", message)

    def test_long_lists_are_summarised_rather_than_dumped(self):
        self._armed()
        for index in range(12):
            self._order(f"t-{index}", phase="waiting_approval", directive=f"Task number {index}")
        digest.collect_digest(self.conn, now=self.now)
        message = self._message()
        self.assertIn("Needs you — 12 items", message)
        self.assertIn(f"and {12 - digest.MAX_ITEMS} more", message)

    def test_a_digest_stays_inside_the_delivery_limit(self):
        """Delivery truncates at 3900 characters and "Needs you" is last, so an
        overlong digest would silently drop the section that matters most."""
        self._armed()
        for index in range(40):
            self._order(f"t-{index}", phase="waiting_approval", directive="D" * 4000)
            self._event("result", {"result": "permission"}, task_id=f"t-{index}")
        digest.collect_digest(self.conn, now=self.now)
        message = self._message()
        self.assertLess(len(message), 3900, "the digest would be truncated on delivery")
        self.assertIn("Needs you", message)

    def test_it_opens_with_plain_language_not_lifecycle_terms(self):
        """OPERATOR_COMMUNICATION.md: never lead with task ids, phases or queue talk."""
        self._armed()
        digest.collect_digest(self.conn, now=self.now)
        first = self._message().splitlines()[0]
        self.assertIn("Milchik", first)
        for jargon in ("phase", "task_id", "tick", "queue", "payload"):
            self.assertNotIn(jargon, first.lower())
