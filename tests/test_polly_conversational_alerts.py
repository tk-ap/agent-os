import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from adapters.hermes.fleet import telegram_blocker_briefs as briefs
from runtime import release_recovery


class PollyConversationalAlertTests(unittest.TestCase):
    def test_waiting_availability_says_wait_is_valid(self):
        record = {
            "recovery_id": "release-1",
            "work_id": "ailhat-release",
            "state": "waiting_availability",
            "blocker": {"reason": "provider cooldown"},
            "retry_policy": {"next_check_at": "2026-09-08T04:00:00Z"},
        }
        text = briefs._polly_message(record)
        self.assertIn("safest fix is usually time", text)
        self.assertIn("Nothing right now", text)
        self.assertIn("next recorded check", text)

    def test_reconciling_warns_against_duplicate_retry(self):
        record = {
            "recovery_id": "release-2",
            "work_id": "ailhat-release",
            "state": "reconciling",
            "blocker": {"reason": "deployment response ambiguous"},
        }
        text = briefs._polly_message(record)
        self.assertIn("stopped before retrying", text)
        self.assertIn("avoid a duplicate push or deployment", text)
        self.assertIn("Retry only after", text)

    def test_human_required_demands_specific_scope_not_blanket_permission(self):
        record = {
            "recovery_id": "release-3",
            "work_id": "ailhat-release",
            "state": "human_required",
            "terminal_reason": "authority:expired",
        }
        text = briefs._polly_message(record)
        self.assertIn("human decision is required", text.lower())
        self.assertIn("exact scoped choice", text)

    def test_store_records_become_private_cards(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory)
            db = state / "kanban.db"
            conn = sqlite3.connect(db)
            conn.row_factory = sqlite3.Row
            conn.execute("""CREATE TABLE telegram_cards (
                id TEXT PRIMARY KEY, event_key TEXT UNIQUE, expires REAL,
                message TEXT, channel TEXT, delivery TEXT DEFAULT 'pending')""")
            store = release_recovery.RecoveryStore(state / "release-recovery")
            store.save({
                "recovery_id": "release-4",
                "work_id": "ailhat-release",
                "state": "waiting_availability",
                "retry_policy": {},
                "authority": {},
                "created_at": release_recovery.iso(),
                "updated_at": release_recovery.iso(),
            })
            self.assertEqual(briefs.collect_polly_briefs(conn), 1)
            row = conn.execute("SELECT message,channel FROM telegram_cards").fetchone()
            self.assertEqual(row["channel"], "private")
            self.assertIn("Polly persistence update", row["message"])
            self.assertEqual(briefs.collect_polly_briefs(conn), 0)
            conn.close()


if __name__ == "__main__":
    unittest.main()
