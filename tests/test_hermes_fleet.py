"""Behavior tests against the installed Hermes dispatcher, with isolated state and fake CLIs."""
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import time
import unittest
import sys
from unittest.mock import patch

from adapters.hermes.fleet import bridge, harnesses
from adapters.hermes.fleet import fallback_tick

try:
    from hermes_cli import kanban_db as kb
except ImportError:
    kb = None


class ErrorTests(unittest.TestCase):
    def test_generated_quota_text_is_not_a_capacity_signal(self):
        self.assertEqual(harnesses.classify(0, '{"type":"result","result":"usage limit"}', ''), ("executed", None))

    def test_capacity_and_retry_after(self):
        event = '{"type":"error","message":"rate_limit_exceeded","retry_after":120}'
        self.assertEqual(harnesses.classify(1, event, ''), ("capacity", 120))

    def test_permission_and_auth_never_rotate(self):
        self.assertEqual(harnesses.classify(1, '', 'permission denied; usage limit')[0], "permission")
        self.assertEqual(harnesses.classify(1, '', 'authentication failed')[0], "authentication")


@unittest.skipIf(kb is None, "Run with Hermes venv and PYTHONPATH to exercise installed dispatcher")
class FleetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        self.state = self.root / "state"
        self.env = patch.dict(os.environ, {"HERMES_HOME": str(self.root / "hermes"),
            "HERMES_KANBAN_DB": str(self.state / "kanban.db"),
            "HERMES_KANBAN_WORKSPACES_ROOT": str(self.state / "workspaces")})
        self.env.start()
        self.order = {"work_id": "test-1", "routing_source": "registry/product-routing.yaml",
            "source_product": "agent-os-workforce", "owning_product": "agent-os-workforce",
            "workspace": str(self.workspace), "problem_or_opportunity": {"problem": "test"},
            "priority": {"level": "p2"}, "desired_outcome": {"result": "artifact"},
            "required_capabilities": ["filesystem"], "constraints": {"local_only": True},
            "acceptance_criteria": ["artifact exists"], "status": "approved",
            "created_at": "2026-09-06T00:00:00Z"}

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def enqueue(self, **kwargs):
        return bridge.enqueue(self.state, self.order, "test-only operator authorization", **kwargs)

    def claimed(self, **kwargs):
        task_id = self.enqueue(**kwargs)
        conn = bridge.connect(self.state)
        task = kb.claim_task(conn, task_id, ttl_seconds=120)
        conn.close()
        self.assertIsNotNone(task)
        return task

    def test_idempotent_work_id_and_changed_content_rejected(self):
        first = self.enqueue()
        self.assertEqual(first, self.enqueue())
        self.order["acceptance_criteria"].append("changed")
        with self.assertRaises(ValueError):
            self.enqueue()

    def test_proposal_and_external_capability_rejected(self):
        self.order["status"] = "proposed"
        with self.assertRaises(ValueError):
            self.enqueue()
        self.order["status"] = "approved"
        self.order["required_capabilities"] = ["browser"]
        with self.assertRaises(ValueError):
            self.enqueue()

    def test_denied_attempt_in_successful_run_is_not_permission(self):
        # The scoped Bash allowlist means workers routinely attempt a denied
        # command and then complete with allowed tools; the denial stays in
        # the evidence record but the run is a success.
        out = '{"type":"result","is_error":false,"subtype":"success",' \
              '"permission_denials":[{"tool_name":"Bash"}]}'
        self.assertEqual(harnesses.classify(0, out, "")[0], "executed")

    def test_denied_attempt_in_failed_run_is_permission(self):
        out = '{"type":"result","is_error":true,' \
              '"permission_denials":[{"tool_name":"Bash"}]}'
        self.assertEqual(harnesses.classify(0, out, "")[0], "permission")

    def test_git_work_allows_claude_and_codex(self):
        self.order["required_capabilities"] = ["filesystem", "git"]
        task_id = self.enqueue()
        conn = bridge.connect(self.state)
        row = bridge.order_row(conn, task_id)
        self.assertEqual(json.loads(row["harnesses"]), ["codex-cli", "claude-code"])
        conn.close()

    def test_shell_work_routes_only_to_codex(self):
        self.order["required_capabilities"] = ["filesystem", "git", "shell"]
        task_id = self.enqueue()
        conn = bridge.connect(self.state)
        row = bridge.order_row(conn, task_id)
        self.assertEqual(json.loads(row["harnesses"]), ["codex-cli"])
        conn.close()

    def test_expired_and_tampered_work_never_runs(self):
        task_id = self.enqueue()
        conn = bridge.connect(self.state)
        conn.execute("UPDATE agent_os_orders SET expires=0 WHERE task_id=?", (task_id,))
        self.assertFalse(bridge.authorized(bridge.order_row(conn, task_id)))
        conn.execute("UPDATE agent_os_orders SET expires=?,payload='{}' WHERE task_id=?", (time.time()+60, task_id))
        self.assertFalse(bridge.authorized(bridge.order_row(conn, task_id)))
        conn.close()

    def test_capacity_handoff_preserves_files_and_checkpoint(self):
        task = self.claimed()
        calls = []
        def runner(argv, prompt, workspace, out, err, timeout, alive):
            self.assertTrue(alive())
            calls.append(argv[0])
            checkpoint = workspace / (".agent-os-progress-" + task.id + ".json")
            if len(calls) == 1:
                (workspace / "artifact.txt").write_text("first step")
                checkpoint.write_text(json.dumps({"summary": "first step saved", "remaining": ["finish"]}))
                out.write_text('{"type":"error","message":"usage limit reached"}\n')
                err.write_text('')
                return 1
            self.assertIn("first step saved", prompt)
            self.assertEqual((workspace / "artifact.txt").read_text(), "first step")
            (workspace / "artifact.txt").write_text("finished")
            out.write_text('{"type":"result","result":"done"}\n')
            err.write_text('')
            return 0
        with patch.object(harnesses, "available", return_value=True):
            bridge.worker(self.state, task.id, task.current_run_id, runner)
        self.assertEqual(calls, ["codex", "claude"])
        conn = bridge.connect(self.state)
        self.assertEqual(kb.get_task(conn, task.id).status, "review")
        self.assertEqual(bridge.order_row(conn, task.id)["attempts"], 2)
        conn.close()

    def test_permission_failure_stops_without_switching(self):
        task = self.claimed()
        calls = []
        def runner(argv, prompt, workspace, out, err, timeout, alive):
            calls.append(argv[0]); out.write_text(''); err.write_text('permission denied')
            return 1
        with patch.object(harnesses, "available", return_value=True):
            bridge.worker(self.state, task.id, task.current_run_id, runner)
        self.assertEqual(calls, ["codex"])
        conn = bridge.connect(self.state)
        self.assertEqual(kb.get_task(conn, task.id).status, "blocked")
        conn.close()

    def test_all_capacity_exhausted_parks_without_extra_calls(self):
        task = self.claimed()
        calls = []
        def runner(argv, prompt, workspace, out, err, timeout, alive):
            calls.append(argv[0]); out.write_text('{"type":"error","message":"rate limit"}')
            err.write_text(''); return 1
        with patch.object(harnesses, "available", return_value=True):
            bridge.worker(self.state, task.id, task.current_run_id, runner)
        conn = bridge.connect(self.state)
        self.assertEqual(len(calls), 2)
        row = bridge.order_row(conn, task.id)
        self.assertEqual(row["phase"], "waiting_capacity")
        self.assertGreater(row["next_at"], time.time())
        self.assertEqual(kb.get_task(conn, task.id).status, "blocked")
        conn.close()

    def test_revocation_during_execution_blocks_result(self):
        task = self.claimed()
        def runner(argv, prompt, workspace, out, err, timeout, alive):
            conn = bridge.connect(self.state)
            conn.execute("UPDATE agent_os_orders SET revoked=1 WHERE task_id=?", (task.id,))
            conn.close()
            self.assertFalse(alive())
            out.write_text(''); err.write_text(''); return 0
        with patch.object(harnesses, "available", return_value=True):
            bridge.worker(self.state, task.id, task.current_run_id, runner)
        conn = bridge.connect(self.state)
        self.assertEqual(bridge.order_row(conn, task.id)["phase"], "revoked")
        self.assertNotEqual(kb.get_task(conn, task.id).status, "done")
        conn.close()

    def test_real_dispatcher_spawns_cli_and_reopens_state(self):
        task_id = self.enqueue()
        binaries = self.root / "bin"
        binaries.mkdir()
        # An executable fixture, not a model: verifies process boundaries and stdin transport.
        executable = binaries / "codex"
        executable.write_text('#!/usr/bin/env python3\nimport sys,json,pathlib\n'
            'prompt=sys.stdin.read()\n'
            'assert "artifact exists" in prompt\n'
            'pathlib.Path("dispatched.txt").write_text("first saved")\n'
            'print(json.dumps({"type":"error","message":"usage limit reached"}))\n'
            'sys.exit(1)\n')
        executable.chmod(0o700)
        second = binaries / "claude"
        second.write_text('#!/usr/bin/env python3\nimport sys,json,pathlib\n'
            'prompt=sys.stdin.read()\n'
            'assert "artifact exists" in prompt\n'
            'assert pathlib.Path("dispatched.txt").read_text()=="first saved"\n'
            'pathlib.Path("dispatched.txt").write_text("fixture executed")\n'
            'print(json.dumps({"type":"result","result":"fixture done"}))\n')
        second.chmod(0o700)
        pythonpath = os.pathsep.join([str(bridge.ROOT), str(Path(kb.__file__).parents[1])])
        with patch.dict(os.environ, {"PATH": str(binaries) + os.pathsep + os.environ["PATH"], "PYTHONPATH": pythonpath}):
            result = bridge.tick(self.state)
            self.assertEqual(len(result["spawned"]), 1)
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                conn = bridge.connect(self.state)
                task = kb.get_task(conn, task_id)
                conn.close()
                if task.status != "running":
                    break
                time.sleep(0.1)
            self.assertEqual(task.status, "review", (self.state / f"{task_id}.worker.log").read_text())
            self.assertTrue((self.state / task_id / "2.json").exists())
            self.assertEqual((self.workspace / "dispatched.txt").read_text(), "fixture executed")
            # Subsequent ticks must not dispatch the human review lane.
            self.assertEqual(bridge.tick(self.state)["spawned"], [])

    def test_cli_timeout_terminates_process(self):
        out, err = self.root / "out", self.root / "err"
        with self.assertRaises(TimeoutError):
            bridge.run_cli([sys.executable, "-c", "import time; time.sleep(30)"], "prompt",
                           self.workspace, out, err, 0.1, lambda: True)

    def test_budget_survives_worker_restart(self):
        task = self.claimed(max_attempts=1)
        conn = bridge.connect(self.state)
        conn.execute("UPDATE agent_os_orders SET attempts=1 WHERE task_id=?", (task.id,))
        conn.close()
        def forbidden(*args):
            self.fail("A restarted worker exceeded the persisted budget")
        bridge.worker(self.state, task.id, task.current_run_id, forbidden)
        conn = bridge.connect(self.state)
        self.assertEqual(bridge.order_row(conn, task.id)["phase"], "blocked")
        conn.close()

    def test_dry_run_does_not_reconcile_or_revoke_tasks(self):
        task_id = self.enqueue()
        conn = bridge.connect(self.state)
        conn.execute("UPDATE agent_os_orders SET expires=0 WHERE task_id=?", (task_id,))
        before = kb.get_task(conn, task_id).status
        conn.close()
        with patch("hermes_cli.kanban_db_dispatch.dispatch_once", side_effect=AssertionError("must not reconcile")):
            self.assertEqual(bridge.tick(self.state, dry_run=True)["eligible"], [])
        conn = bridge.connect(self.state)
        self.assertEqual(kb.get_task(conn, task_id).status, before)
        conn.close()


class FallbackClockTests(unittest.TestCase):
    """The fallback tick only fires when the Hermes gateway is down, so the
    systemd timer never double-ticks while the primary cron clock is healthy."""

    def _home_with_heartbeat(self, age):
        home = Path(tempfile.mkdtemp())
        db = sqlite3.connect(home / "state.db")
        db.execute("CREATE TABLE gateway_heartbeats (backend_id TEXT PRIMARY KEY, pid INTEGER,"
                   " started_at REAL, last_heartbeat REAL, profile TEXT, host TEXT)")
        db.execute("INSERT INTO gateway_heartbeats VALUES (?,?,?,?,?,?)",
                   ("x", 1, time.time(), time.time() - age, "default", "h"))
        db.commit(); db.close()
        return home

    def test_fresh_heartbeat_is_alive_and_stale_is_down(self):
        fresh = self._home_with_heartbeat(10)
        self.assertTrue(fallback_tick.gateway_alive(home=fresh))
        stale = self._home_with_heartbeat(fallback_tick.GATEWAY_STALE_AFTER + 5)
        self.assertFalse(fallback_tick.gateway_alive(home=stale))

    def test_missing_or_empty_db_is_down(self):
        self.assertFalse(fallback_tick.gateway_alive(home=Path(tempfile.mkdtemp())))
        empty = self._home_with_heartbeat(10)
        (empty / "state.db").unlink()
        self.assertFalse(fallback_tick.gateway_alive(home=empty))


if __name__ == "__main__":
    unittest.main()
