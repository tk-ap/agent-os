import json
import sqlite3
import time
import unittest

from adapters.hermes.fleet.telegram_blocker_briefs import collect_blocker_briefs
from adapters.hermes.fleet.telegram_blocker_brief_migration import collect_refresh_cards
from adapters.hermes.fleet.telegram_blocker_briefs import approval_card_covers


class MilchikBlockerBriefTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript("""
            CREATE TABLE agent_os_orders (
                task_id TEXT PRIMARY KEY,
                work_id TEXT,
                payload TEXT,
                owning_agent TEXT,
                phase TEXT,
                attempts INTEGER,
                harnesses TEXT,
                next_at REAL
            );
            CREATE TABLE telegram_cards (
                id TEXT PRIMARY KEY,
                event_key TEXT UNIQUE,
                task_id TEXT,
                expires REAL,
                message TEXT,
                channel TEXT,
                delivery TEXT DEFAULT 'pending'
            );
        """)

    def tearDown(self):
        self.conn.close()

    def _insert(self, phase, attempts=1, harnesses=("codex-cli",), next_at=0,
                capabilities=("filesystem", "git", "shell")):
        payload = {
            "work_id": "directive-13-work",
            "owning_agent": "eugene",
            "required_capabilities": list(capabilities),
            "problem_or_opportunity": {
                "directive": "Restore ailhat production reliability and validate the live scan loop"
            },
        }
        self.conn.execute(
            "INSERT INTO agent_os_orders VALUES (?,?,?,?,?,?,?,?)",
            (
                "t-proof",
                "directive-13-work",
                json.dumps(payload),
                "eugene",
                phase,
                attempts,
                json.dumps(list(harnesses)),
                next_at,
            ),
        )

    def test_no_blocker_brief_when_an_approval_card_already_asks(self):
        """A parked approval sent two private cards: the one with the decision
        and its buttons, and a brief whose entire content was "review the
        approval card in this chat". One notification per thing to decide."""
        self._insert("waiting_approval")
        self.conn.execute(
            """INSERT INTO telegram_cards(id,event_key,task_id,expires,message,channel)
               VALUES ('a1','approval:t-proof:1:stamp','t-proof',?,'decide me','private')""",
            (time.time() + 600,))
        self.assertEqual(collect_blocker_briefs(self.conn), 0)
        self.assertEqual(collect_refresh_cards(self.conn), 0)
        self.assertEqual(
            self.conn.execute("SELECT COUNT(*) FROM telegram_cards").fetchone()[0], 1)

    def test_a_brief_is_still_sent_when_nothing_else_asks(self):
        """The deferral is to the approval card, not a silencing of blockers."""
        self._insert("waiting_approval")
        self.assertEqual(collect_blocker_briefs(self.conn), 1)

    def test_other_blocked_states_are_unaffected(self):
        for phase in ("waiting_capacity", "blocked", "collision"):
            self.setUp()
            self._insert(phase)
            self.conn.execute(
                """INSERT INTO telegram_cards(id,event_key,task_id,expires,message,channel)
                   VALUES ('a1','approval:t-proof:1:stamp','t-proof',?,'x','private')""",
                (time.time() + 600,))
            self.assertFalse(approval_card_covers(
                self.conn,
                self.conn.execute("SELECT * FROM agent_os_orders").fetchone()))
            self.assertEqual(collect_blocker_briefs(self.conn), 1, phase)

    def test_refresh_does_not_resend_a_card_that_is_already_current(self):
        """Every blocker alert reached TK twice.

        The v2 refresh adapter wraps collect_fleet and so runs on every tick,
        and it builds its message with the same functions collect_blocker_briefs
        uses. Once those functions were upgraded in place, the refresh emitted a
        byte-identical copy of the card that already existed, under a different
        event_key so nothing deduplicated it.
        """
        self._insert("blocked")
        collect_blocker_briefs(self.conn)
        self.assertEqual(collect_refresh_cards(self.conn), 0)
        rows = self.conn.execute("SELECT message FROM telegram_cards").fetchall()
        self.assertEqual(len(rows), 1, "the same blocker was announced twice")

    def test_refresh_still_upgrades_a_genuinely_stale_card(self):
        """A card written before the conversational upgrade must still be refreshed."""
        self._insert("blocked")
        self.conn.execute(
            """INSERT INTO telegram_cards(id,event_key,task_id,expires,message,channel)
               VALUES ('old','blocker:t-proof:blocked:1','t-proof',?,?,'private')""",
            (time.time() + 604800, "Task blocked."))
        self.assertEqual(collect_refresh_cards(self.conn), 1)
        refreshed = self.conn.execute(
            "SELECT message FROM telegram_cards WHERE event_key LIKE 'blocker-conversational-v2:%'"
        ).fetchone()["message"]
        self.assertIn("Milchik", refreshed)

    def test_refresh_stays_idempotent_across_ticks(self):
        self._insert("waiting_capacity")
        collect_blocker_briefs(self.conn)
        for _ in range(3):
            collect_refresh_cards(self.conn)
        self.assertEqual(
            self.conn.execute("SELECT COUNT(*) FROM telegram_cards").fetchone()[0], 1)

    def test_capacity_blocker_says_retry_is_automatic_and_tk_need_not_act(self):
        self._insert("waiting_capacity", next_at=time.time() + 600)
        self.assertEqual(collect_blocker_briefs(self.conn), 1)
        message = self.conn.execute("SELECT message FROM telegram_cards").fetchone()[0]
        self.assertIn("work is preserved", message)
        self.assertIn("retry it automatically", message)
        self.assertIn("Nothing right now", message)
        self.assertIn("Waiting is a valid action", message)
        self.assertIn("codex-cli", message)

    def test_shell_task_explains_why_claude_cannot_take_same_envelope(self):
        self._insert("waiting_capacity", capabilities=("filesystem", "git", "shell"))
        collect_blocker_briefs(self.conn)
        message = self.conn.execute("SELECT message FROM telegram_cards").fetchone()[0]
        self.assertIn("claude-code is missing shell", message)
        self.assertIn("split the work", message)
        self.assertIn("Do not widen permissions", message)

    def test_git_only_task_surfaces_claude_as_eligible_alternate(self):
        self._insert("waiting_capacity", capabilities=("filesystem", "git"))
        collect_blocker_briefs(self.conn)
        message = self.conn.execute("SELECT message FROM telegram_cards").fetchone()[0]
        self.assertIn("second configured harness", message)
        self.assertIn("claude-code", message)
        self.assertIn("fleet-selection problem", message)

    def test_approval_blocker_tells_tk_exactly_to_review_approval_card(self):
        self._insert("waiting_approval")
        collect_blocker_briefs(self.conn)
        message = self.conn.execute("SELECT message FROM telegram_cards").fetchone()[0]
        self.assertIn("boundary only you can clear", message)
        self.assertIn("Review the approval card", message)

    def test_same_stalled_state_does_not_spam_each_minute(self):
        self._insert("waiting_capacity")
        self.assertEqual(collect_blocker_briefs(self.conn), 1)
        self.assertEqual(collect_blocker_briefs(self.conn), 0)
        count = self.conn.execute("SELECT COUNT(*) FROM telegram_cards").fetchone()[0]
        self.assertEqual(count, 1)

    def test_new_attempt_can_emit_updated_blocker(self):
        self._insert("waiting_capacity", attempts=1)
        collect_blocker_briefs(self.conn)
        self.conn.execute("UPDATE agent_os_orders SET attempts=2 WHERE task_id='t-proof'")
        self.assertEqual(collect_blocker_briefs(self.conn), 1)
        count = self.conn.execute("SELECT COUNT(*) FROM telegram_cards").fetchone()[0]
        self.assertEqual(count, 2)


if __name__ == "__main__":
    unittest.main()
