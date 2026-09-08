import json
import sqlite3
import sys
import tempfile
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from adapters.hermes.fleet import telegram_runtime_recovery as recovery


class TelegramRuntimeRecoveryTests(unittest.TestCase):
    def test_registered_products_include_agent_os_and_product_registry(self):
        root = Path(__file__).resolve().parents[1]
        products = recovery._registered_change_products(root)
        self.assertIn("agent-os", products)
        self.assertIn("ailhat", products)
        self.assertIn("alvira-meos", products)

    def test_stale_provenance_failure_reuses_same_directive(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.executescript("""
            CREATE TABLE telegram_directives (
                id INTEGER PRIMARY KEY, status TEXT, task_id TEXT, backlog_work_id TEXT
            );
            CREATE TABLE telegram_cards (
                event_key TEXT PRIMARY KEY, message TEXT, delivery TEXT
            );
        """)
        conn.execute(
            "INSERT INTO telegram_directives VALUES (13,'route_failed',NULL,?)",
            ("ailhat-live-scan-customer-readiness-proof",),
        )
        conn.execute(
            "INSERT INTO telegram_cards VALUES (?,?,?)",
            (
                "directive-failed:13",
                "Directive #13 could not be routed.\n\n" + recovery.STALE_PROVENANCE_TEXT,
                "pending",
            ),
        )

        count = recovery._recover_failed_directive(
            conn, "ailhat-live-scan-customer-readiness-proof"
        )
        self.assertEqual(count, 1)
        row = conn.execute("SELECT * FROM telegram_directives WHERE id=13").fetchone()
        self.assertEqual(row["status"], "captured")
        self.assertIsNone(row["task_id"])
        card = conn.execute("SELECT * FROM telegram_cards").fetchone()
        self.assertEqual(card["delivery"], "expired")

    def test_done_open_mirror_is_replaced_and_same_directive_retried(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            backlog = root / "agents/milchik"
            backlog.mkdir(parents=True)
            backlog.joinpath("backlog.yaml").write_text("""
- work_id: proof-work
  source: human
  status: approved
  priority: {level: p1, confidence: 1.0}
  title: Proof work
""")

            conn = sqlite3.connect(":memory:")
            conn.row_factory = sqlite3.Row
            conn.executescript("""
                CREATE TABLE backlog_board_map (work_id TEXT PRIMARY KEY, task_id TEXT NOT NULL);
                CREATE TABLE tasks (id TEXT PRIMARY KEY, status TEXT NOT NULL, priority INTEGER DEFAULT 0);
                CREATE TABLE telegram_directives (
                    id INTEGER PRIMARY KEY, status TEXT, task_id TEXT, backlog_work_id TEXT
                );
                CREATE TABLE telegram_cards (
                    event_key TEXT PRIMARY KEY, message TEXT, delivery TEXT
                );
            """)
            conn.execute("INSERT INTO tasks(id,status) VALUES ('old-task','done')")
            conn.execute("INSERT INTO backlog_board_map VALUES ('proof-work','old-task')")
            conn.execute("INSERT INTO telegram_directives VALUES (13,'route_failed',NULL,'proof-work')")
            conn.execute(
                "INSERT INTO telegram_cards VALUES ('directive-failed:13',?, 'pending')",
                (recovery.STALE_PROVENANCE_TEXT,),
            )

            fake_kb = types.ModuleType("hermes_cli.kanban_db")

            def get_task(db, task_id):
                row = db.execute("SELECT id,status FROM tasks WHERE id=?", (task_id,)).fetchone()
                return SimpleNamespace(id=row["id"], status=row["status"]) if row else None

            def create_task(db, **kwargs):
                task_id = "replacement-task"
                db.execute(
                    "INSERT OR IGNORE INTO tasks(id,status) VALUES (?,?)",
                    (task_id, kwargs["initial_status"]),
                )
                return task_id

            fake_kb.get_task = get_task
            fake_kb.create_task = create_task
            fake_pkg = types.ModuleType("hermes_cli")
            fake_pkg.kanban_db = fake_kb

            telegram = SimpleNamespace(ROOT=root)
            with patch.dict(
                sys.modules,
                {"hermes_cli": fake_pkg, "hermes_cli.kanban_db": fake_kb},
            ):
                result = recovery._repair_open_done_mirrors(telegram, conn)

            self.assertEqual(result, {"repaired": 1, "retried": 1})
            mapping = conn.execute(
                "SELECT task_id FROM backlog_board_map WHERE work_id='proof-work'"
            ).fetchone()
            self.assertEqual(mapping["task_id"], "replacement-task")
            self.assertEqual(
                conn.execute("SELECT status FROM telegram_directives WHERE id=13").fetchone()[0],
                "captured",
            )
            # The original done row is preserved as evidence.
            self.assertEqual(
                conn.execute("SELECT status FROM tasks WHERE id='old-task'").fetchone()[0],
                "done",
            )


if __name__ == "__main__":
    unittest.main()
