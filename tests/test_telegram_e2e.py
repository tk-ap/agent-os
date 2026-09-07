"""Offline end-to-end and unit coverage for the Milchik Telegram path.

The e2e test drives the real tick/dispatch/decide code with a fake Telegram
API and fixture harness executables (see adapters/hermes/fleet/e2e.py); the
backlog-board tests pin the canonical-board contract: mirror rows for open
items, provenance stamping, and fail-closed dispatch rejection.
"""

import json
from pathlib import Path
import subprocess
import tempfile
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

    def _config_with_repos(self, repositories):
        config = self.root / "telegram-config.json"
        config.write_text(json.dumps({"token": "x", "repositories": repositories}))
        self.patch = patch.object(telegram, "CONFIG", config)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        return config

    def test_valid_proposal_enqueues_directed_work_and_closes_directive(self):
        self._config_with_repos({"agent-os-workforce": str(self.workspace)})
        conn, row, directive_id = self._routing(
            {"owning_agent": "eugene", "priority": "p1", "lane": "ecosystem",
             "product": "agent-os-workforce", "capabilities": ["filesystem"]})
        try:
            task_id, agent, problem = telegram.enqueue_directed_work(conn, self.state, row)
            self.assertIsNotNone(task_id)
            self.assertIsNone(problem)
            self.assertEqual(agent, "eugene")
            work = bridge.order_row(conn, task_id)
            self.assertEqual(work["owning_agent"], "eugene")
            payload = json.loads(work["payload"])
            self.assertEqual(payload["owning_product"], "agent-os-workforce")
            self.assertEqual(payload["workspace"], str(self.workspace))
            self.assertIn("ship the sitemap fix", payload["problem_or_opportunity"]["directive"])
            directive = conn.execute("SELECT status, task_id FROM telegram_directives WHERE id=?",
                                     (directive_id,)).fetchone()
            self.assertEqual(directive["status"], "closed")
            self.assertEqual(directive["task_id"], task_id)
        finally:
            conn.close()

    def test_product_without_local_workspace_is_refused(self):
        self._config_with_repos({})
        conn, row, _directive_id = self._routing(
            {"owning_agent": "eugene", "priority": "p1", "lane": "directive",
             "product": "alvira-meos", "capabilities": ["git"]})
        try:
            task_id, agent, problem = telegram.enqueue_directed_work(conn, self.state, row)
            self.assertIsNone(task_id)
            self.assertIn("no local workspace", problem)
        finally:
            conn.close()

    def test_unknown_product_never_enqueues(self):
        self._config_with_repos({"agent-os-workforce": str(self.workspace)})
        conn, row, _directive_id = self._routing(
            {"owning_agent": "eugene", "priority": "p1", "lane": "directive",
             "product": "not-a-product"})
        try:
            task_id, agent, problem = telegram.enqueue_directed_work(conn, self.state, row)
            self.assertIsNone(task_id)
            self.assertIn("not in the registry", problem)
        finally:
            conn.close()

    def test_unknown_agent_never_enqueues(self):
        self._config_with_repos({"agent-os-workforce": str(self.workspace)})
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
class GuardrailTests(unittest.TestCase):
    """Execution-context isolation, instance pinning, objective leases, and
    hygiene — the guardrail set from the specs on PR #33."""

    setUp = fleet_tests.FleetTests.setUp
    tearDown = fleet_tests.FleetTests.tearDown
    enqueue = fleet_tests.FleetTests.enqueue
    claimed = fleet_tests.FleetTests.claimed

    def _run_worker(self, task, runner):
        with patch.object(harnesses, "available", return_value=True):
            bridge.worker(self.state, task.id, task.current_run_id, runner)

    def test_worker_registers_and_releases_execution_context(self):
        task = self.claimed()
        calls = []
        def runner(argv, prompt, workspace, out, err, timeout, alive):
            calls.append(argv[0])
            (Path(workspace) / (".agent-os-progress-" + task.id + ".json")).write_text(
                json.dumps({"summary": "done", "status": "ready_for_review"}))
            out.write_text('{"type":"result","result":"ok"}\n')
            return 0
        self._run_worker(task, runner)
        conn = bridge.connect(self.state)
        try:
            row = conn.execute("SELECT * FROM active_workspaces WHERE context_id=?",
                               (f"task:{task.id}",)).fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row["mode"], "governed_execution")
            self.assertEqual(row["status"], "released")
        finally:
            conn.close()

    def test_conflicting_surface_parks_before_any_execution(self):
        task = self.claimed()
        conn = bridge.connect(self.state)
        bridge.register_workspace(conn, context_id="human:explore", actor="human",
                                  mode="human_exploration", repository=self.order["owning_product"],
                                  workspace=str(self.workspace), mutable_surfaces=["**"])
        conn.commit()
        conn.close()
        def forbidden(*args):
            self.fail("a conflicting task must never reach the harness")
        self._run_worker(task, forbidden)
        conn = bridge.connect(self.state)
        try:
            row = bridge.order_row(conn, task.id)
            self.assertEqual(row["phase"], "collision")
            events = [e[0] for e in conn.execute(
                "SELECT kind FROM agent_os_events WHERE task_id=?", (task.id,)).fetchall()]
            self.assertIn("collision", events)
        finally:
            conn.close()

    def test_non_overlapping_surface_proceeds_with_evidence(self):
        task = self.claimed()
        conn = bridge.connect(self.state)
        bridge.register_workspace(conn, context_id="human:explore", actor="human",
                                  mode="human_exploration", repository=self.order["owning_product"],
                                  workspace=str(self.workspace), mutable_surfaces=["docs/**"])
        conn.commit()
        conn.close()
        order = json.loads(bridge.order_row(bridge.connect(self.state), task.id)["payload"])
        order["problem_or_opportunity"]["mutable_surfaces"] = ["src/**"]
        conn = bridge.connect(self.state)
        conn.execute("UPDATE agent_os_orders SET payload=?, digest=? WHERE task_id=?",
                     (json.dumps(order), bridge.digest(order), task.id))
        conn.commit()
        conn.close()
        calls = []
        def runner(argv, prompt, workspace, out, err, timeout, alive):
            calls.append(argv[0])
            (Path(workspace) / (".agent-os-progress-" + task.id + ".json")).write_text(
                json.dumps({"summary": "done", "status": "ready_for_review"}))
            out.write_text('{"type":"result","result":"ok"}\n')
            return 0
        self._run_worker(task, runner)
        self.assertEqual(len(calls), 1)
        conn = bridge.connect(self.state)
        try:
            events = [e[0] for e in conn.execute(
                "SELECT kind FROM agent_os_events WHERE task_id=?", (task.id,)).fetchall()]
            self.assertIn("overlap_noted", events)
        finally:
            conn.close()

    def test_execution_mode_stamped_on_orders(self):
        task_id = self.enqueue()
        conn = bridge.connect(self.state)
        try:
            row = bridge.order_row(conn, task_id)
            self.assertEqual(row["execution_mode"], "governed_execution")
        finally:
            conn.close()
        order = dict(self.order)
        order["work_id"] = "verify-1"
        order["problem_or_opportunity"] = {"execution_mode": "verification"}
        task_id = bridge.enqueue(self.state, order, "test authority")
        conn = bridge.connect(self.state)
        try:
            self.assertEqual(bridge.order_row(conn, task_id)["execution_mode"], "verification")
        finally:
            conn.close()

    def test_instance_pinning_recorded_per_attempt(self):
        self.order["owning_agent"] = "eugene"
        task = self.claimed()
        def runner(argv, prompt, workspace, out, err, timeout, alive):
            (Path(workspace) / (".agent-os-progress-" + task.id + ".json")).write_text(
                json.dumps({"summary": "done", "status": "ready_for_review"}))
            out.write_text('{"type":"result","result":"ok"}\n')
            return 0
        self._run_worker(task, runner)
        record = json.loads((Path(self.state) / task.id / "1.json").read_text())
        instance = record["agent_instance"]
        self.assertEqual(instance["instance_id"], f"{task.id}:1")
        self.assertIsNotNone(instance["role"])
        self.assertIsNotNone(instance["harness_path"])
        self.assertIsNotNone(instance["policy_digest"])

    def _lease_backlog(self, item):
        root = self.root / "fake-root"
        (root / "agents" / "milchik").mkdir(parents=True)
        (root / "agents" / "milchik" / "backlog.yaml").write_text(json.dumps([item]))
        self.patch = patch.object(telegram, "ROOT", root)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_expired_objective_lease_blocks_selection(self):
        self._lease_backlog({
            "work_id": "w-leased", "source": "human", "lane": "directive",
            "status": "approved", "priority": {"level": "p0", "confidence": 1.0},
            "title": "Leased work", "problem": "p",
            "objective_lease": "obj-alvira"})
        conn = bridge.connect(self.state)
        try:
            telegram.schema(conn)
            conn.execute("INSERT INTO objective_leases(id,objective,owner,valid_until,revoked) "
                         "VALUES ('obj-alvira','first paid client','steward',?,0)",
                         (time.time() - 60,))
            conn.commit()
            item, refusal = telegram.eligible_backlog_item(conn)
            self.assertIsNone(item)
            self.assertIn("expired", refusal)
            conn.execute("UPDATE objective_leases SET valid_until=? WHERE id='obj-alvira'",
                         (time.time() + 86400,))
            conn.commit()
            item, refusal = telegram.eligible_backlog_item(conn)
            self.assertEqual(item["work_id"], "w-leased")
            self.assertIsNone(refusal)
        finally:
            conn.close()

    def test_hygiene_flags_stale_objects_without_deleting(self):
        conn = bridge.connect(self.state)
        try:
            telegram.schema(conn)
            conn.execute("""INSERT INTO agent_os_grants(task_id,work_id,scope,approver,granted_at,expires,consumed)
                            VALUES ('t-x','w-x','s',42,?,?,0)""", (time.time()-200, time.time()-100))
            conn.execute("INSERT INTO telegram_cards(id,event_key,task_id,snapshot,expires,message,delivery) "
                         "VALUES ('c-x','k-x','t-y',NULL,?,'m','sent')", (time.time()-100,))
            conn.commit()
            sections = telegram.hygiene_report(conn)
            by_title = {title: items for title, items in sections}
            self.assertIn("Expired unconsumed grants", by_title)
            self.assertIn("Expired undecided cards", by_title)
            # Nothing was deleted.
            self.assertIsNotNone(conn.execute(
                "SELECT 1 FROM agent_os_grants WHERE task_id='t-x'").fetchone())
        finally:
            conn.close()

    def test_collision_resume_requeues_same_task(self):
        task_id = self.enqueue()
        conn = bridge.connect(self.state)
        try:
            telegram.schema(conn)
            conn.execute("UPDATE agent_os_orders SET phase='collision' WHERE task_id=?", (task_id,))
            kb.block_task(conn, task_id, reason="fixture collision")
            card_id = "col-" + task_id
            conn.execute("""INSERT INTO telegram_cards
                (id,event_key,task_id,snapshot,expires,message,delivery,message_id)
                VALUES (?,?,?,?,?,?,?,?)""",
                (card_id, f"collision:{task_id}", task_id, None, time.time()+86400,
                 "collision card", "sent", 3))
            conn.commit()
            config = {"user_id": 42, "chat_id": 42}
            query = {"from": {"id": 42}, "message": {"chat": {"id": 42}, "message_id": 3},
                     "data": f"aos:{card_id}:resume"}
            result = telegram.decide(conn, config, query)
            self.assertIn("Resumed", result)
            self.assertEqual(bridge.order_row(conn, task_id)["phase"], "queued")
            self.assertIn(kb.get_task(conn, task_id).status, {"ready", "running"})
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


@unittest.skipIf(kb is None, "Requires installed Hermes environment")
class CtoBotTrackingTests(unittest.TestCase):
    """cto-bot commit work mirrors onto the board as completed tasks."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.state = self.base / "state"
        self.state.mkdir()
        self.repo = self.base / "product"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        self.conn = bridge.connect(self.state)

    def tearDown(self):
        self.conn.close()
        self.temp.cleanup()

    def _commit(self, name, email, subject, trailer=None):
        msg = ["-m", subject]
        if trailer:
            msg += ["-m", trailer]
        subprocess.run(["git", "-C", str(self.repo),
                        "-c", f"user.name={name}", "-c", f"user.email={email}",
                        "commit", "--allow-empty"] + msg, check=True,
                       capture_output=True)
        return subprocess.run(["git", "-C", str(self.repo), "rev-parse", "HEAD"],
                              check=True, capture_output=True, text=True).stdout.strip()

    def _board_rows(self):
        return {t.title for t in
                self.conn.execute("SELECT title FROM tasks").fetchall()}

    def test_cto_persona_commit_mirrors_done_row(self):
        rev = self._commit("Tahlia Ashwood", "tahlia.ashwood@gmail.com",
                           "docs: canonical context onboarding model")
        telegram.mirror_cto_commit(self.conn, "alvira-meos", self.repo, rev,
                                   "docs: canonical context onboarding model")
        rows = self.conn.execute("SELECT * FROM tasks").fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "done")
        self.assertIn("[alvira-meos]", rows[0]["title"])

    def test_agent_trailer_counts_as_cto_work(self):
        rev = self._commit("Some Operator", "someone@example.com", "fix: thing",
                           trailer="Co-Authored-By: Claude Code <noreply@anthropic.com>")
        self.assertIsNotNone(telegram.mirror_cto_commit(
            self.conn, "ashwood", self.repo, rev, "fix: thing"))
        self.assertEqual(
            self.conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0], 1)

    def test_unrelated_author_not_mirrored(self):
        rev = self._commit("Random Person", "random@example.com", "chore: thing")
        self.assertIsNone(telegram.mirror_cto_commit(
            self.conn, "ashwood", self.repo, rev, "chore: thing"))
        self.assertEqual(
            self.conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0], 0)

    def test_mirror_is_idempotent_per_revision(self):
        rev = self._commit("tk-ap", "164285623+tk-ap@users.noreply.github.com",
                           "feat: something")
        telegram.mirror_cto_commit(self.conn, "ashwood", self.repo, rev, "feat: something")
        telegram.mirror_cto_commit(self.conn, "ashwood", self.repo, rev, "feat: something")
        self.assertEqual(
            self.conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
