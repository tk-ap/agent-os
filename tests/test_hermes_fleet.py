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

    def test_the_queue_environment_does_not_leak_to_the_caller(self):
        """connect() sets HERMES_KANBAN_* on whatever process calls it and never
        unsets them. Harmless in a dedicated fleet process; not harmless inside
        the Hermes gateway, whose own dispatcher then reads the fleet queue for
        the rest of its life. On 2026-09-09 the gateway claimed an Agent OS
        inspection under its own pid, spawned it twice, crashed both times and
        gave up -- no fleet worker log, because the fleet's spawn never ran."""
        from adapters.hermes.fleet import bridge as fleet_bridge
        before = {"HERMES_KANBAN_DB": "/somewhere/else/kanban.db",
                  "HERMES_KANBAN_WORKSPACES_ROOT": "/somewhere/else/workspaces"}
        with patch.dict(os.environ, before):
            with fleet_bridge.fleet_environment("/tmp/fleet-state-fixture") as scoped:
                self.assertTrue(str(scoped).endswith("fleet-state-fixture"))
                self.assertNotEqual(os.environ["HERMES_KANBAN_DB"], before["HERMES_KANBAN_DB"])
            for key, value in before.items():
                self.assertEqual(os.environ[key], value,
                                 f"{key} leaked out of the fleet scope")

    def test_an_absent_queue_environment_is_left_absent(self):
        from adapters.hermes.fleet import bridge as fleet_bridge
        cleared = {k: v for k, v in os.environ.items() if not k.startswith("HERMES_KANBAN_")}
        with patch.dict(os.environ, cleared, clear=True):
            with fleet_bridge.fleet_environment("/tmp/fleet-state-fixture"):
                self.assertIn("HERMES_KANBAN_DB", os.environ)
            self.assertNotIn("HERMES_KANBAN_DB", os.environ,
                             "the fleet invented a queue variable for its caller")
            self.assertNotIn("HERMES_KANBAN_WORKSPACES_ROOT", os.environ)

    def test_gemini_untrusted_folder_fails_closed(self):
        """Gemini downgrades auto_edit to prompt-for-approval in an untrusted
        folder and still exits 0, so a headless run changes nothing while
        looking clean. Observed live: 'Approval mode overridden to "default"
        because the current folder is not trusted.'"""
        notice = 'Approval mode overridden to "default" because the current folder is not trusted.'
        self.assertEqual(harnesses.classify(0, notice, "")[0], "permission")
        self.assertEqual(harnesses.classify(0, "", notice)[0], "permission")

    def test_gemini_missing_auth_is_authentication_not_failure(self):
        """Also reported at exit 0, so the returncode-gated stderr never sees it.
        It must stop for inspection rather than rotate to another harness."""
        notice = ("Please set an Auth method in your /home/tk/.gemini/settings.json "
                  "or specify one of the following environment variables")
        self.assertEqual(harnesses.classify(0, "", notice)[0], "authentication")

    def test_gemini_clean_run_still_classifies_as_executed(self):
        self.assertEqual(harnesses.classify(0, '{"type":"result"}', "")[0], "executed")

    def test_gemini_command_never_bypasses_approval(self):
        argv = harnesses.command("gemini-cli", ".")
        self.assertEqual(argv[0], "gemini")
        self.assertIn("--approval-mode", argv)
        self.assertEqual(argv[argv.index("--approval-mode") + 1], "auto_edit")
        self.assertNotIn("-y", argv)
        self.assertNotIn("--yolo", argv)

    def test_the_network_harness_keeps_the_workspace_sandbox(self):
        """Network is added to the sandbox; the sandbox is not removed."""
        argv = harnesses.command("codex-cli-network", "/tmp/ws")
        self.assertIn("--sandbox", argv)
        self.assertEqual(argv[argv.index("--sandbox") + 1], "workspace-write")
        self.assertIn("sandbox_workspace_write.network_access=true", argv)
        self.assertNotIn("danger-full-access", argv)
        self.assertIn('approval_policy="never"', argv)

    def test_the_ordinary_codex_harness_still_has_no_network(self):
        argv = harnesses.command("codex-cli", "/tmp/ws")
        self.assertNotIn("sandbox_workspace_write.network_access=true", argv)

    def test_gemini_is_a_selectable_harness(self):
        self.assertIn("gemini-cli", harnesses.SUPPORTED)

    def test_metered_gemini_credentials_are_stripped(self):
        """The OAuth login is the subscription path; an API key is metered
        billing, which this adapter never falls through to."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "k", "GOOGLE_GENAI_USE_VERTEXAI": "1",
                                     "GOOGLE_API_KEY": "k"}):
            env = harnesses.environment()
        for key in ("GEMINI_API_KEY", "GOOGLE_GENAI_USE_VERTEXAI", "GOOGLE_API_KEY"):
            self.assertNotIn(key, env)

    def test_a_reset_time_stated_in_prose_is_honoured(self):
        """Codex names the reset in its message rather than a structured field:
        "try again at 9:58 PM". classify() only read a numeric retry_after, so an
        eleven-minute wait became the one-hour default -- on approved work with
        no other eligible harness to rotate to."""
        import datetime
        now = datetime.datetime(2026, 9, 9, 21, 47, 31)
        message = ("You've hit your usage limit. Upgrade to Pro or try again at 9:58 PM.")
        self.assertAlmostEqual(harnesses.retry_at_from_message(message, now=now), 629.0, delta=1)

    def test_a_reset_time_already_past_today_means_tomorrow(self):
        import datetime
        now = datetime.datetime(2026, 9, 9, 23, 30, 0)
        delay = harnesses.retry_at_from_message("try again at 9:58 PM", now=now)
        self.assertGreater(delay, 80000)
        self.assertLessEqual(delay, 86400)

    def test_midnight_and_noon_are_not_confused(self):
        import datetime
        now = datetime.datetime(2026, 9, 9, 10, 0, 0)
        self.assertAlmostEqual(harnesses.retry_at_from_message("try again at 12:30 PM", now=now),
                               2 * 3600 + 30 * 60, delta=1)
        self.assertGreater(harnesses.retry_at_from_message("try again at 12:30 AM", now=now),
                           14 * 3600)

    def test_no_stated_time_means_no_guess(self):
        self.assertIsNone(harnesses.retry_at_from_message("You've hit your usage limit."))
        self.assertIsNone(harnesses.retry_at_from_message("try again at 99:99"))

    def test_a_structured_retry_after_still_wins(self):
        event = ('{"type":"error","message":"rate_limit_exceeded; try again at 9:58 PM",'
                 '"retry_after":120}')
        self.assertEqual(harnesses.classify(1, event, ''), ("capacity", 120))

    def test_capacity_without_any_stated_reset_returns_no_delay(self):
        self.assertEqual(harnesses.classify(1, '{"type":"error","message":"rate limit"}', ''),
                         ("capacity", None))

    def test_permission_and_auth_never_rotate(self):
        self.assertEqual(harnesses.classify(1, '', 'permission denied; usage limit')[0], "permission")
        self.assertEqual(harnesses.classify(1, '', 'authentication failed')[0], "authentication")


class CapacityCreditTests(unittest.TestCase):
    """Time parked on exhausted providers must not consume the operator's mandate.

    These run without the installed Hermes dispatcher because the rule is pure
    arithmetic over an order row, and it is the rule that silently lost a day
    of approved fleet work when a Codex usage-limit cooldown outlived it.
    """

    def order(self, **overrides):
        row = {"revoked": 0, "expires": time.time() + 60, "payload": "{}",
               "capacity_blocked_at": 0, "capacity_credit": 0}
        row["digest"] = bridge.digest(json.loads(row["payload"]))
        row.update(overrides)
        return row

    def test_unparked_work_still_expires_on_schedule(self):
        self.assertFalse(bridge.authorized(self.order(expires=time.time() - 1)))

    def test_banked_credit_keeps_parked_work_authorized_past_expiry(self):
        # Parked for two hours, mandate lapsed one hour ago: still authorized.
        row = self.order(expires=time.time() - 3600, capacity_credit=7200)
        self.assertTrue(bridge.authorized(row))

    def test_credit_accrues_while_the_task_is_still_parked(self):
        row = self.order(expires=time.time() - 3600, capacity_blocked_at=time.time() - 7200)
        self.assertTrue(bridge.authorized(row))
        self.assertGreater(bridge.capacity_credit(row), 7100)

    def test_credit_cannot_outlive_one_authority_window(self):
        row = self.order(expires=time.time() - 1, capacity_credit=bridge.MAX_CAPACITY_CREDIT * 5)
        self.assertEqual(bridge.capacity_credit(row), bridge.MAX_CAPACITY_CREDIT)
        self.assertLessEqual(bridge.effective_expiry(row), row["expires"] + bridge.MAX_CAPACITY_CREDIT)

    def test_credit_never_rescues_revoked_or_tampered_work(self):
        generous = {"expires": time.time() - 3600, "capacity_credit": 7200}
        self.assertFalse(bridge.authorized(self.order(revoked=1, **generous)))
        self.assertFalse(bridge.authorized(self.order(digest="tampered", **generous)))

    def test_rows_predating_the_migration_are_read_as_zero_credit(self):
        row = self.order()
        del row["capacity_credit"], row["capacity_blocked_at"]
        self.assertEqual(bridge.capacity_credit(row), 0)
        self.assertEqual(bridge.effective_expiry(row), row["expires"])


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

    def test_network_work_routes_to_the_network_harness(self):
        self.order["required_capabilities"] = ["filesystem", "git", "shell", "network"]
        self.order["work_id"] = "needs-network"
        task_id = self.enqueue()
        conn = bridge.connect(self.state)
        try:
            self.assertEqual(json.loads(bridge.order_row(conn, task_id)["harnesses"]),
                             ["codex-cli-network"])
        finally:
            conn.close()

    def test_ordinary_work_never_inherits_network(self):
        """Capability routing matches any harness that covers the work, so a
        network-capable harness would otherwise satisfy every shell task and
        could be rotated to on a capacity handoff -- giving egress to work that
        never asked for it. Escalation is declared, not inherited."""
        self.order["required_capabilities"] = ["filesystem", "git", "shell"]
        self.order["work_id"] = "no-network-please"
        task_id = self.enqueue()
        conn = bridge.connect(self.state)
        try:
            chosen = json.loads(bridge.order_row(conn, task_id)["harnesses"])
            self.assertNotIn("codex-cli-network", chosen)
            self.assertEqual(chosen, ["codex-cli"])
        finally:
            conn.close()

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

    def test_board_rows_have_human_titles(self):
        self.order["problem_or_opportunity"] = {
            "statement": "Directed work from an accepted routing proposal.",
            "directive": "Ship the ALVIRA sitemap and robots fix to production.",
        }
        self.order["owning_product"] = "alvira-meos"
        self.order["owning_agent"] = "eugene"
        task_id = self.enqueue()
        conn = bridge.connect(self.state)
        task = kb.get_task(conn, task_id)
        self.assertIn("alvira-meos", task.title)
        self.assertIn("Ship the ALVIRA sitemap", task.title)
        self.assertIn("eugene", task.title)
        self.assertNotIn(task_id, task.title)
        conn.close()

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

    def _blocked_run(self, task, summary="Blocked by unavailable network transport."):
        def runner(argv, prompt, workspace, out, err, timeout, alive):
            checkpoint = workspace / (".agent-os-progress-" + task.id + ".json")
            checkpoint.write_text(json.dumps({"summary": summary, "status": "blocked"}))
            out.write_text('{"type":"result","result":"done"}\n')
            err.write_text('')
            return 0
        return runner

    def test_a_harness_that_says_it_was_blocked_is_believed(self):
        """A clean exit is not completion. The worker wrote status blocked and
        said why, and this fell through to the review lane anyway -- so work
        that achieved nothing arrived as "CLI finished; acceptance requires
        review" and only an independent inspection opening the evidence caught
        it. A self-reported success is not evidence; a self-reported failure is
        safe to act on."""
        task = self.claimed()
        with patch.object(harnesses, "available", return_value=True):
            bridge.worker(self.state, task.id, task.current_run_id, self._blocked_run(task))
        conn = bridge.connect(self.state)
        try:
            self.assertEqual(bridge.order_row(conn, task.id)["phase"], "blocked")
            self.assertEqual(kb.get_task(conn, task.id).status, "blocked")
            kinds = [e[0] for e in conn.execute(
                "SELECT kind FROM agent_os_events WHERE task_id=?", (task.id,)).fetchall()]
            self.assertIn("self_reported_blocked", kinds)
            self.assertNotIn("review", [
                r[0] for r in conn.execute(
                    "SELECT phase FROM agent_os_orders WHERE task_id=?", (task.id,)).fetchall()])
        finally:
            conn.close()

    def test_authority_the_run_could_not_use_is_not_consumed(self):
        """The blocked run never exercised the grant. Burning it makes TK
        approve the same thing again for nothing -- which is what happened when
        an approved network observation was stopped by the harness sandbox
        rather than by policy."""
        task = self.claimed()
        conn = bridge.connect(self.state)
        conn.execute("INSERT INTO agent_os_grants VALUES (?,?,?,?,?,?,0)",
                     (task.id, "test-1", "read four documented URLs", 42,
                      time.time(), time.time() + 3600))
        conn.commit()
        conn.close()
        with patch.object(harnesses, "available", return_value=True):
            bridge.worker(self.state, task.id, task.current_run_id, self._blocked_run(task))
        conn = bridge.connect(self.state)
        try:
            grant = conn.execute("SELECT consumed FROM agent_os_grants WHERE task_id=?",
                                 (task.id,)).fetchone()
            self.assertIsNotNone(grant, "the grant was deleted")
            self.assertEqual(grant["consumed"], 0, "unusable authority was spent anyway")
        finally:
            conn.close()

    def test_a_finished_run_still_reaches_review_and_consumes_its_grant(self):
        task = self.claimed()
        conn = bridge.connect(self.state)
        conn.execute("INSERT INTO agent_os_grants VALUES (?,?,?,?,?,?,0)",
                     (task.id, "test-1", "scope", 42, time.time(), time.time() + 3600))
        conn.commit()
        conn.close()
        def runner(argv, prompt, workspace, out, err, timeout, alive):
            checkpoint = workspace / (".agent-os-progress-" + task.id + ".json")
            checkpoint.write_text(json.dumps({"summary": "Done.", "status": "ready_for_review"}))
            out.write_text('{"type":"result","result":"done"}\n'); err.write_text(''); return 0
        with patch.object(harnesses, "available", return_value=True):
            bridge.worker(self.state, task.id, task.current_run_id, runner)
        conn = bridge.connect(self.state)
        try:
            self.assertEqual(bridge.order_row(conn, task.id)["phase"], "review")
            self.assertEqual(conn.execute(
                "SELECT consumed FROM agent_os_grants WHERE task_id=?", (task.id,)).fetchone()[0], 1)
        finally:
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
        # Every eligible harness is tried once before the task parks. Counted
        # from the registry rather than hardcoded, so adding a harness does not
        # silently turn this into a weaker assertion.
        eligible = json.loads(bridge.order_row(conn, task.id)["harnesses"])
        self.assertEqual(len(calls), len(eligible))
        self.assertEqual(len(set(calls)), len(eligible),
                         "a harness was retried instead of rotating to the next")
        self.assertNotIn("codex-cli-network", eligible,
                         "work that never asked for network was given a network harness")
        row = bridge.order_row(conn, task.id)
        self.assertEqual(row["phase"], "waiting_capacity")
        self.assertGreater(row["next_at"], time.time())
        self.assertEqual(kb.get_task(conn, task.id).status, "blocked")
        conn.close()

    def test_cooldown_longer_than_the_mandate_does_not_revoke_the_task(self):
        """The 2026-09-07 loss: Codex hit a usage limit, the cooldown outlived
        the one-day mandate, and the next tick revoked approved work that had
        never run. Parked time is credited, so the task survives to be retried."""
        task = self.claimed()
        def runner(argv, prompt, workspace, out, err, timeout, alive):
            out.write_text('{"type":"error","message":"rate limit"}'); err.write_text(''); return 1
        with patch.object(harnesses, "available", return_value=True):
            bridge.worker(self.state, task.id, task.current_run_id, runner)
        conn = bridge.connect(self.state)
        row = bridge.order_row(conn, task.id)
        self.assertEqual(row["phase"], "waiting_capacity")
        self.assertGreater(row["capacity_blocked_at"], 0, "capacity clock never started")
        # Park started two hours ago; the mandate lapsed an hour into the cooldown.
        conn.execute("""UPDATE agent_os_orders SET capacity_blocked_at=?, expires=?
                        WHERE task_id=?""",
                     (time.time() - 7200, time.time() - 3600, task.id))
        conn.close()
        bridge.tick(self.state)
        conn = bridge.connect(self.state)
        row = bridge.order_row(conn, task.id)
        self.assertNotEqual(row["phase"], "revoked",
                            "capacity-blocked work lost its mandate during the cooldown")
        self.assertTrue(bridge.authorized(row))
        conn.close()

    def test_unparking_recovers_a_task_hermes_escalated_to_triage(self):
        """Hermes counts repeated blocks with the same reason and escalates to
        triage at its recurrence limit, so two capacity waits read as a defect
        loop. unblock_task clears blocked, not triage, so the order returned to
        queued while the board row stayed invisible to the dispatcher: on
        2026-09-09 approved work with a valid grant and banked credit sat idle
        for twenty minutes after its provider recovered."""
        task = self.claimed()
        def runner(argv, prompt, workspace, out, err, timeout, alive):
            out.write_text('{"type":"error","message":"rate limit"}'); err.write_text(''); return 1
        with patch.object(harnesses, "available", return_value=True):
            bridge.worker(self.state, task.id, task.current_run_id, runner)
        conn = bridge.connect(self.state)
        conn.execute("UPDATE agent_os_orders SET next_at=? WHERE task_id=?",
                     (time.time() - 1, task.id))
        # Hermes escalates the repeated capacity block.
        conn.execute("UPDATE tasks SET status='triage' WHERE id=?", (task.id,))
        conn.commit()
        conn.close()
        bridge.tick(self.state)
        conn = bridge.connect(self.state)
        try:
            status = kb.get_task(conn, task.id).status
            self.assertNotEqual(status, "triage",
                                "the order was requeued but the board row stayed unreachable")
            # Recovered and immediately dispatchable: the same tick may already
            # have claimed it, which is the outcome this exists to restore.
            self.assertIn(status, {"ready", "running"})
            kinds = [e[0] for e in conn.execute(
                "SELECT kind FROM agent_os_events WHERE task_id=?", (task.id,)).fetchall()]
            self.assertIn("triage_cleared", kinds)
        finally:
            conn.close()

    def test_consecutive_capacity_waits_are_not_the_identical_block(self):
        """The loop detector compares reasons. Naming the resume time is better
        for the operator and stops two correct waits looking like one defect."""
        task = self.claimed()
        def runner(argv, prompt, workspace, out, err, timeout, alive):
            out.write_text('{"type":"error","message":"rate limit"}'); err.write_text(''); return 1
        with patch.object(harnesses, "available", return_value=True):
            bridge.worker(self.state, task.id, task.current_run_id, runner)
        conn = bridge.connect(self.state)
        try:
            reasons = [r[0] for r in conn.execute(
                """SELECT payload FROM task_events WHERE task_id=? AND kind='blocked'""",
                (task.id,)).fetchall()]
            blocked = [r for r in conn.execute(
                "SELECT payload FROM task_events WHERE task_id=?", (task.id,)).fetchall()]
            text = " ".join(str(r[0]) for r in blocked)
            self.assertIn("resume at", text)
            self.assertNotIn("resume after cooldown", text)
        finally:
            conn.close()

    def test_unparking_banks_the_credit_and_stops_the_clock(self):
        task = self.claimed()
        def runner(argv, prompt, workspace, out, err, timeout, alive):
            out.write_text('{"type":"error","message":"rate limit"}'); err.write_text(''); return 1
        with patch.object(harnesses, "available", return_value=True):
            bridge.worker(self.state, task.id, task.current_run_id, runner)
        conn = bridge.connect(self.state)
        # Cooldown elapsed after a one-hour park.
        conn.execute("""UPDATE agent_os_orders SET capacity_blocked_at=?, next_at=?
                        WHERE task_id=?""", (time.time() - 3600, time.time() - 1, task.id))
        conn.close()
        bridge.tick(self.state)
        conn = bridge.connect(self.state)
        row = bridge.order_row(conn, task.id)
        self.assertEqual(row["phase"], "queued")
        self.assertEqual(row["capacity_blocked_at"], 0, "credit clock left running while queued")
        self.assertGreater(row["capacity_credit"], 3500)
        conn.close()

    def test_expired_work_that_never_parked_is_still_revoked(self):
        """Crediting parked time must not make ordinary expiry toothless.
        Uses an unclaimed order: a running task is never revoked mid-flight."""
        task_id = self.enqueue()
        conn = bridge.connect(self.state)
        conn.execute("UPDATE agent_os_orders SET expires=? WHERE task_id=?",
                     (time.time() - 1, task_id))
        conn.close()
        bridge.tick(self.state)
        conn = bridge.connect(self.state)
        self.assertEqual(bridge.order_row(conn, task_id)["phase"], "revoked")
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
