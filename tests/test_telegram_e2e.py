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

from adapters.hermes.fleet import bridge, harnesses, telegram
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
class ApprovalGateTests(unittest.TestCase):
    """Scoped-authority lifecycle: park, approve (same task resumes), deny,
    grant expiry. HUMAN_GATE is a durable state, not a dead end."""

    setUp = fleet_tests.FleetTests.setUp
    tearDown = fleet_tests.FleetTests.tearDown
    enqueue = fleet_tests.FleetTests.enqueue
    claimed = fleet_tests.FleetTests.claimed

    def _parked(self):
        """A task parked at a protected boundary, with its request on record."""
        task_id = self.enqueue()
        conn = bridge.connect(self.state)
        folder = Path(self.state) / task_id
        folder.mkdir(exist_ok=True)
        Path(folder / "1.json").write_text(json.dumps({"checkpoint_text": json.dumps({
            "summary": "Stopped at a protected boundary.",
            "status": "waiting_approval",
            "approval_request": {"scope": "commit and push the branch",
                                 "reason": "publishing requires operator authority"}})}))
        conn.execute("UPDATE agent_os_orders SET phase='waiting_approval',attempts=1 WHERE task_id=?",
                     (task_id,))
        kb.block_task(conn, task_id, reason="harness requested scoped authority")
        conn.commit()
        return conn, task_id

    def _card(self, conn, task_id, action="approve"):
        card_id = "card-" + task_id
        conn.execute("""INSERT INTO telegram_cards
            (id,event_key,task_id,snapshot,expires,message,scope,delivery,message_id)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (card_id, f"approval:{task_id}", task_id, None, time.time()+86400,
             "approval card", "commit and push the branch", "sent", 7))
        conn.commit()
        config = {"user_id": 42, "chat_id": 42}
        query = {"from": {"id": 42},
                 "message": {"chat": {"id": 42}, "message_id": 7},
                 "data": f"aos:{card_id}:{action}"}
        return config, query

    def test_deny_terminates_task_and_records_the_denial(self):
        conn, task_id = self._parked()
        try:
            telegram.schema(conn)
            config, query = self._card(conn, task_id, "deny")
            result = telegram.decide(conn, config, query)
            self.assertIn("Denied", result)
            row = bridge.order_row(conn, task_id)
            self.assertEqual(row["phase"], "denied")
            self.assertEqual(row["revoked"], 1)
            self.assertEqual(kb.get_task(conn, task_id).status, "blocked")
            events = [e[0] for e in conn.execute(
                "SELECT kind FROM agent_os_events WHERE task_id=?", (task_id,)).fetchall()]
            self.assertIn("grant_denied", events)
        finally:
            conn.close()

    def test_approve_grants_scoped_authority_and_resumes_same_task(self):
        conn, task_id = self._parked()
        try:
            telegram.schema(conn)
            config, query = self._card(conn, task_id, "approve")
            result = telegram.decide(conn, config, query)
            self.assertIn("Approved", result)
            grant = conn.execute("SELECT * FROM agent_os_grants WHERE task_id=?", (task_id,)).fetchone()
            self.assertIsNotNone(grant)
            self.assertEqual(grant["scope"], "commit and push the branch")
            self.assertEqual(grant["consumed"], 0)
            self.assertEqual(grant["approver"], 42)
            self.assertGreater(grant["expires"], time.time())
            row = bridge.order_row(conn, task_id)
            self.assertEqual(row["phase"], "queued")   # same task, not a replacement
            self.assertIn(kb.get_task(conn, task_id).status, {"ready", "running"})
        finally:
            conn.close()

    def test_expired_grant_reparks_without_touching_the_harness(self):
        task = self.claimed()
        conn = bridge.connect(self.state)
        conn.execute("INSERT INTO agent_os_grants VALUES (?,?,?,?,?,?,0)",
                     (task.id, "test-1", "scope", 42, time.time()-20, time.time()-10))
        conn.commit()
        conn.close()
        def forbidden(*args):
            self.fail("an expired grant must never reach the harness")
        with patch.object(harnesses, "available", return_value=True):
            bridge.worker(self.state, task.id, task.current_run_id, forbidden)
        conn = bridge.connect(self.state)
        try:
            self.assertEqual(bridge.order_row(conn, task.id)["phase"], "waiting_approval")
            self.assertEqual(kb.get_task(conn, task.id).status, "blocked")
            self.assertIsNone(conn.execute(
                "SELECT 1 FROM agent_os_grants WHERE task_id=?", (task.id,)).fetchone())
            events = [e[0] for e in conn.execute(
                "SELECT kind FROM agent_os_events WHERE task_id=?", (task.id,)).fetchall()]
            self.assertIn("grant_expired", events)
        finally:
            conn.close()


@unittest.skipIf(kb is None, "Requires installed Hermes environment")
class RoutingAcceptanceTests(unittest.TestCase):
    """Accepting a routing proposal enqueues the directed work — fail closed
    on a missing, malformed, or unregistered proposal."""

    setUp = fleet_tests.FleetTests.setUp
    tearDown = fleet_tests.FleetTests.tearDown

    _MISSING = object()

    def _routing(self, proposal=_MISSING):
        conn = bridge.connect(self.state)
        telegram.schema(conn)
        conn.execute("INSERT INTO telegram_directives(ts,text,status) VALUES (?,'ship the sitemap fix','routing')",
                     (time.time(),))
        directive_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        work_id = f"directive-{directive_id}-routing"
        conn.execute("""INSERT INTO agent_os_orders
            (task_id,work_id,payload,digest,authority,expires,harnesses,max_attempts,timeout,owning_agent)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            ("t-routing", work_id, json.dumps(self.order), "d", "a",
             time.time()+3600, '["codex-cli"]', 6, 900, "router"))
        if proposal is not self._MISSING:
            conn.execute("INSERT INTO routing_proposals(task_id,work_id,proposal) VALUES (?,?,?)",
                         ("t-routing", work_id, json.dumps(proposal)))
        conn.commit()
        row = bridge.order_row(conn, "t-routing")
        return conn, row, directive_id

    def test_valid_proposal_enqueues_directed_work_and_closes_directive(self):
        conn, row, directive_id = self._routing(
            {"owning_agent": "eugene", "priority": "p1", "lane": "ecosystem"})
        try:
            task_id, agent, problem = telegram.enqueue_directed_work(conn, self.state, row)
            self.assertIsNotNone(task_id)
            self.assertIsNone(problem)
            self.assertEqual(agent, "eugene")
            work = bridge.order_row(conn, task_id)
            self.assertEqual(work["owning_agent"], "eugene")
            self.assertIn("ship the sitemap fix", json.loads(work["payload"])["problem_or_opportunity"]["directive"])
            directive = conn.execute("SELECT status, task_id FROM telegram_directives WHERE id=?",
                                     (directive_id,)).fetchone()
            self.assertEqual(directive["status"], "closed")
            self.assertEqual(directive["task_id"], task_id)
        finally:
            conn.close()

    def test_unknown_agent_never_enqueues(self):
        conn, row, _directive_id = self._routing(
            {"owning_agent": "nobody", "priority": "p1", "lane": "ecosystem"})
        try:
            task_id, agent, problem = telegram.enqueue_directed_work(conn, self.state, row)
            self.assertIsNone(task_id)
            self.assertIn("registry", problem)
        finally:
            conn.close()

    def test_missing_proposal_never_enqueues(self):
        conn, row, _directive_id = self._routing()
        try:
            task_id, agent, problem = telegram.enqueue_directed_work(conn, self.state, row)
            self.assertIsNone(task_id)
            self.assertIn("machine-readable", problem)
        finally:
            conn.close()


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
