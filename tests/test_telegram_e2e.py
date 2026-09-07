"""Offline end-to-end and unit coverage for the Milchik Telegram path.

The e2e test drives the real tick/dispatch/decide code with a fake Telegram
API and fixture harness executables (see adapters/hermes/fleet/e2e.py); the
backlog-board tests pin the canonical-board contract: mirror rows for open
items, provenance stamping, and fail-closed dispatch rejection.
"""

import json
from pathlib import Path
import subprocess
import time
import unittest
from unittest.mock import patch

from adapters.hermes.fleet import bridge, telegram
from adapters.hermes.fleet.e2e import FakeAPI, run_offline_e2e, STAGES
from tests import test_hermes_fleet as fleet_tests

kb = fleet_tests.kb


@unittest.skipIf(kb is None, "Requires installed Hermes environment")
class MilchikTelegramE2ETests(unittest.TestCase):
    """The whole loop, real code, fake transport: directive -> board -> worker
    -> inspection -> card -> accept -> done."""

    def test_full_loop_offline(self):
        results = run_offline_e2e()
        for stage in STAGES:
            self.assertTrue(results.get(stage), f"stage failed: {stage} ({results.get(stage)!r})")


@unittest.skipIf(kb is None, "Requires installed Hermes environment")
class BacklogBoardTests(unittest.TestCase):
    """The canonical-board contract for backlog-driven work."""

    setUp = fleet_tests.FleetTests.setUp
    tearDown = fleet_tests.FleetTests.tearDown

    def _backlog_root(self, items):
        """A fake ROOT tree carrying a backlog.yaml the sync will read."""
        root = self.root / "fake-root"
        (root / "agents" / "milchik").mkdir(parents=True)
        (root / "agents" / "milchik" / "backlog.yaml").write_text(
            json.dumps(items))
        return root

    def _seed_backlog(self, items):
        root = self._backlog_root(items)
        self.patch = patch.object(telegram, "ROOT", root)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        return root

    def test_sync_creates_blocked_mirror_rows_with_priority(self):
        self._seed_backlog([
            {"work_id": "w-human-p0", "source": "human", "lane": "ecosystem",
             "status": "proposed", "priority": {"level": "p0", "confidence": 1.0},
             "title": "Human item", "problem": "p"},
            {"work_id": "w-agent-p2", "source": "agent", "lane": "directive",
             "status": "proposed", "priority": {"level": "p2", "confidence": 0.5},
             "title": "Agent item", "problem": "p"},
        ])
        conn = bridge.connect(self.state)
        try:
            telegram.schema(conn)
            result = telegram.sync_backlog_to_board(conn)
            self.assertEqual(result["synced"], 2)
            rows = conn.execute("SELECT * FROM backlog_board_map").fetchall()
            self.assertEqual(len(rows), 2)
            for _work_id, task_id in rows:
                task = kb.get_task(conn, task_id)
                self.assertIsNotNone(task)
                self.assertEqual(task.status, "blocked")
                self.assertGreater(task.priority, 0)
            # Idempotent: second sync creates nothing new.
            self.assertEqual(telegram.sync_backlog_to_board(conn)["synced"], 0)
        finally:
            conn.close()

    def test_sync_closes_mirror_row_when_item_done(self):
        self._seed_backlog([
            {"work_id": "w-open", "source": "human", "lane": "ecosystem",
             "status": "proposed", "priority": {"level": "p1", "confidence": 1.0},
             "title": "t", "problem": "p"},
        ])
        conn = bridge.connect(self.state)
        try:
            telegram.schema(conn)
            telegram.sync_backlog_to_board(conn)
            task_id = conn.execute("SELECT task_id FROM backlog_board_map").fetchone()[0]
            # Mark done in the YAML and sync again.
            root = Path(telegram.ROOT)
            (root / "agents" / "milchik" / "backlog.yaml").write_text(json.dumps([
                {"work_id": "w-open", "source": "human", "lane": "ecosystem",
                 "status": "done", "priority": {"level": "p1", "confidence": 1.0},
                 "title": "t", "problem": "p",
                 "completed": {"at": "2026-09-07", "evidence": "e"}}]))
            result = telegram.sync_backlog_to_board(conn)
            self.assertEqual(result["closed"], 1)
            self.assertEqual(kb.get_task(conn, task_id).status, "done")
        finally:
            conn.close()

    def test_next_stamps_directive_and_routing_carries_provenance(self):
        self._seed_backlog([
            {"work_id": "w-human", "source": "human", "lane": "ecosystem",
             "status": "proposed", "priority": {"level": "p0", "confidence": 1.0},
             "title": "Fix the thing", "problem": "It is broken"},
        ])
        conn = bridge.connect(self.state)
        api = FakeAPI()
        config = {"user_id": 42, "chat_id": 42, "token": "t",
                  "enabled": True, "basis": "commit", "every": 5,
                  "repositories": {}, "monitor_chat_id": -7}
        try:
            telegram.schema(conn)
            telegram.sync_backlog_to_board(conn)
            update = {"update_id": 1, "message": {"message_id": 1,
                "from": {"id": 42}, "chat": {"id": 42, "type": "private"},
                "text": "/next"}}
            telegram.handle_update(conn, config, api, update)
            directive = conn.execute(
                "SELECT * FROM telegram_directives ORDER BY id DESC").fetchone()
            self.assertEqual(directive["backlog_work_id"], "w-human")
            telegram.route_directives(conn, self.state)
            order = conn.execute(
                "SELECT * FROM agent_os_orders ORDER BY rowid DESC").fetchone()
            payload = json.loads(order["payload"])
            po = payload["problem_or_opportunity"]
            self.assertEqual(po["origin"], "autonomous_backlog")
            self.assertEqual(po["backlog_system"], "hermes-kanban")
            self.assertEqual(po["backlog_work_id"], "w-human")
            board_row = kb.get_task(conn, po["board_item_id"])
            self.assertIsNotNone(board_row)
            self.assertEqual(board_row.status, "blocked")
        finally:
            conn.close()

    def test_enqueue_rejects_autonomous_backlog_without_live_board_row(self):
        order = dict(self.order)
        order["problem_or_opportunity"] = {"origin": "autonomous_backlog",
            "backlog_system": "hermes-kanban", "board_item_id": "does-not-exist"}
        with self.assertRaises(ValueError) as caught:
            bridge.enqueue(self.state, order, "test authority")
        self.assertIn("board", str(caught.exception))
        order["problem_or_opportunity"]["board_item_id"] = None
        with self.assertRaises(ValueError):
            bridge.enqueue(self.state, order, "test authority")

    def test_enqueue_rejects_done_board_item(self):
        self._seed_backlog([
            {"work_id": "w-human", "source": "human", "lane": "ecosystem",
             "status": "proposed", "priority": {"level": "p0", "confidence": 1.0},
             "title": "Fix the thing", "problem": "It is broken"},
        ])
        conn = bridge.connect(self.state)
        try:
            telegram.schema(conn)
            telegram.sync_backlog_to_board(conn)
            task_id = conn.execute("SELECT task_id FROM backlog_board_map").fetchone()[0]
            kb.complete_task(conn, task_id, result="closed by fixture")
        finally:
            conn.close()
        order = dict(self.order)
        order["problem_or_opportunity"] = {"origin": "autonomous_backlog",
            "backlog_system": "hermes-kanban", "board_item_id": task_id}
        with self.assertRaises(ValueError) as caught:
            bridge.enqueue(self.state, order, "test authority")
        self.assertIn("live", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
