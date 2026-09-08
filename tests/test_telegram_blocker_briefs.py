import json
import sqlite3
import time
import unittest

from adapters.hermes.fleet.telegram_blocker_briefs import collect_blocker_briefs


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
