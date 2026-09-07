"""Offline end-to-end check of the Milchik Telegram path.

Runs the real tick/dispatch/decide code with a fake Telegram API and fixture
harness executables — no network, no model calls, no live board. Verifies the
full loop the proposal demands:

  directive message -> capture -> routing order + Hermes Kanban board row
  -> fixture harness worker -> review -> W Dog inspection (fixture)
  -> verdict -> review card delivered -> callback accept -> board done

CLI:  python .../fleet_cli.py telegram e2e
Tests: tests/test_telegram_e2e.py
"""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from adapters.hermes.fleet import bridge, telegram

STAGES = ["capture", "board_row", "approval_parked", "approval_card",
          "grant_resumed", "worker_review", "inspection_verdict",
          "card_delivered", "decision_done", "work_enqueued",
          "directive_closed", "monitor_channel"]

# One fixture serves both the producer and the inspector: the prompt tells it
# which mode it is in. It writes the checkpoint the worker consumes and exits
# cleanly with a result event — exactly what a real harness must do.
FIXTURE = r'''#!/usr/bin/env python3
import json, pathlib, re, sys
prompt = sys.stdin.read()
inspection = "Judge only" in prompt
m = re.search(r"\.agent-os-progress-[A-Za-z0-9_]+\.json", prompt)
if not m:
    print(json.dumps({"type": "error", "message": "no checkpoint path in prompt"}))
    sys.exit(1)
path = pathlib.Path(m.group(0))
if not path.is_absolute():
    path = pathlib.Path.cwd() / path
if inspection:
    summary = ("VERDICT: PASS\nEach declared acceptance criterion was checked "
               "against the files; no problems found.")
    checkpoint = {"summary": summary, "completed": ["fixture step"], "remaining": [],
                  "artifacts": [], "verification": ["fixture check"],
                  "status": "ready_for_review"}
elif "TK-approved scoped authority" in prompt:
    summary = "Proposed one owning agent, a priority level, and a lane."
    checkpoint = {"summary": summary, "completed": ["fixture step"], "remaining": [],
                  "artifacts": [], "verification": ["fixture check"],
                  "status": "ready_for_review",
                  "proposal": {"owning_agent": "eugene", "priority": "p1",
                               "lane": "ecosystem", "product": "agent-os-workforce",
                               "capabilities": ["filesystem"]}}
else:
    # First run parks at a protected boundary: the harness needs authority it
    # does not have, so it requests a scoped grant instead of acting.
    checkpoint = {"summary": "Stopped at a protected boundary.",
                  "completed": [], "remaining": ["resume under scoped grant"],
                  "artifacts": [], "verification": [],
                  "status": "waiting_approval",
                  "approval_request": {
                      "scope": "commit and push the routing proposal branch",
                      "reason": "publishing requires operator authority"}}
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(checkpoint))
print(json.dumps({"type": "result", "result": "fixture done"}))
'''


class FakeAPI:
    """In-memory Telegram API: serves queued updates, records every send."""

    def __init__(self):
        self.updates = []
        self.calls = []
        self._mid = 0

    def call(self, method, **kwargs):
        self.calls.append((method, kwargs))
        if method == "getUpdates":
            updates, self.updates = self.updates, []
            return updates
        if method == "sendMessage":
            self._mid += 1
            return {"message_id": self._mid, "chat": {"id": kwargs.get("chat_id")}}
        return {"ok": True}

    def queue_message(self, text, user_id, chat_id):
        self.updates.append({
            "update_id": 1000 + len(self.updates),
            "message": {"message_id": 100 + len(self.updates),
                        "from": {"id": user_id},
                        "chat": {"id": chat_id, "type": "private"}, "text": text}})

    def queue_callback(self, data, user_id, chat_id, message_id):
        self.updates.append({
            "update_id": 2000 + len(self.updates),
            "callback_query": {"id": "cq", "data": data, "from": {"id": user_id},
                               "message": {"message_id": message_id,
                                           "chat": {"id": chat_id}}}})

    def sent_to(self, chat_id):
        return [k for _m, k in self.calls
                if k.get("chat_id") == chat_id]


def _wait_status(conn, task_id, want, deadline=45):
    from hermes_cli import kanban_db as kb
    deadline = time.monotonic() + deadline
    while time.monotonic() < deadline:
        task = kb.get_task(conn, task_id)
        if task is not None and task.status == want:
            return task
        time.sleep(0.2)
    return kb.get_task(conn, task_id)


def run_offline_e2e(root=None, user_id=900000001):
    """Drive the whole Milchik loop offline. Returns {stage: bool|str}."""
    from hermes_cli import kanban_db as kb
    results = {}
    temp = tempfile.TemporaryDirectory()
    base = Path(temp.name)
    state = base / "state"
    state.mkdir()
    config_path = base / "telegram.json"
    chat_id = user_id
    monitor_id = -1000000001
    config_path.write_text(json.dumps({
        "token": "123:fixture", "chat_id": chat_id, "user_id": user_id,
        "enabled": True, "basis": "commit", "every": 5,
        "repositories": {}, "monitor_chat_id": monitor_id}))

    # The directive workspace is telegram.ROOT. Point it at a throwaway git
    # repo so the real checkout is never touched by fixture checkpoints. The
    # fleet config is likewise redirected so local_repositories() reads the
    # test's product map, not the host's.
    original_root = telegram.ROOT
    original_config = telegram.CONFIG
    telegram.CONFIG = config_path
    workspace = root or Path(base / "workspace")
    if root is None:
        workspace.mkdir()
        subprocess.run(["git", "init", "-q", str(workspace)], check=True)
        (workspace / "seed.txt").write_text("seed")
        subprocess.run(["git", "-C", str(workspace), "add", "seed.txt"], check=True)
        subprocess.run(["git", "-C", str(workspace), "-c", "user.name=Fixture",
                        "-c", "user.email=fixture@example.invalid",
                        "commit", "-qm", "seed"], check=True)
    telegram.ROOT = Path(workspace)

    # Fixture harnesses on PATH; hermes board pointed at the temp state.
    bins = base / "bin"
    bins.mkdir()
    for name in ("codex", "claude"):
        exe = bins / name
        exe.write_text(FIXTURE)
        exe.chmod(0o700)
    old_env = dict(os.environ)
    os.environ["PATH"] = str(bins) + os.pathsep + os.environ.get("PATH", "")
    os.environ["PYTHONPATH"] = os.pathsep.join(
        [str(bridge.ROOT), str(Path(kb.__file__).parents[1])]
        + ([p for p in os.environ.get("PYTHONPATH", "").split(os.pathsep) if p]))
    os.environ["HERMES_HOME"] = str(base / "hermes")
    os.environ["HERMES_KANBAN_DB"] = str(state / "kanban.db")
    os.environ["HERMES_KANBAN_WORKSPACES_ROOT"] = str(state / "workspaces")

    api = FakeAPI()
    conn = bridge.connect(state)
    try:
        telegram.schema(conn)
    finally:
        conn.close()
    try:
        # 1. Directive captured and routed in one tick.
        api.queue_message("> ship the sitemap fix", user_id, chat_id)
        telegram.tick(state, config_path, api)
        conn = bridge.connect(state)
        try:
            directive = conn.execute(
                "SELECT * FROM telegram_directives ORDER BY id DESC").fetchone()
            order = conn.execute(
                "SELECT * FROM agent_os_orders WHERE work_id LIKE 'directive-%-routing'").fetchone()
            results["capture"] = bool(
                directive and directive["status"] == "routing" and order)
            results["board_row"] = bool(
                order and kb.get_task(conn, order["task_id"]) is not None)
            producer_task = order["task_id"] if order else None
        finally:
            conn.close()

        # 2. Worker parks at the protected boundary (phase waiting_approval).
        if producer_task:
            bridge.tick(state)
            conn = bridge.connect(state)
            try:
                task = _wait_status(conn, producer_task, "blocked")
                row = bridge.order_row(conn, producer_task)
                results["approval_parked"] = bool(
                    task and row and row["phase"] == "waiting_approval")
            finally:
                conn.close()
            # 3. Approval card created and delivered to the private chat.
            telegram.tick(state, config_path, api)
            conn = bridge.connect(state)
            try:
                card = conn.execute(
                    "SELECT * FROM telegram_cards WHERE task_id=?", (producer_task,)).fetchone()
                results["approval_card"] = bool(
                    card and card["delivery"] == "sent" and card["message_id"] and card["scope"])
                card_id = card["id"] if card else None
                message_id = card["message_id"] if card else None
            finally:
                conn.close()
            # 4. Operator approves the scoped grant; the SAME task resumes.
            if card_id and message_id:
                api.queue_callback(f"aos:{card_id}:approve", user_id, chat_id, message_id)
                telegram.tick(state, config_path, api)
                conn = bridge.connect(state)
                try:
                    grant = conn.execute(
                        "SELECT * FROM agent_os_grants WHERE task_id=?", (producer_task,)).fetchone()
                    row = bridge.order_row(conn, producer_task)
                    task = kb.get_task(conn, producer_task)
                    results["grant_resumed"] = bool(
                        grant and grant["consumed"] == 0 and row and row["phase"] == "queued"
                        and task and task.status in {"ready", "running"})
                finally:
                    conn.close()
            # 5. Worker resumes under the grant and reaches review; the grant is
            # consumed exactly once.
            bridge.tick(state)
            conn = bridge.connect(state)
            try:
                task = _wait_status(conn, producer_task, "review")
                grant = conn.execute(
                    "SELECT * FROM agent_os_grants WHERE task_id=?", (producer_task,)).fetchone()
                results["worker_review"] = bool(
                    task and task.status == "review" and grant and grant["consumed"] == 1)
            finally:
                conn.close()
            # 6. Inspection is enqueued by the telegram tick.
            telegram.tick(state, config_path, api)
            conn = bridge.connect(state)
            try:
                inspector = conn.execute(
                    "SELECT inspector_task_id FROM agent_os_inspections WHERE task_id=?",
                    (producer_task,)).fetchone()
                inspector_task = inspector["inspector_task_id"] if inspector else None
            finally:
                conn.close()
            # 7. Inspector worker runs to review; verdict read next tick.
            if inspector_task:
                bridge.tick(state)
                conn = bridge.connect(state)
                try:
                    _wait_status(conn, inspector_task, "review")
                finally:
                    conn.close()
            # 8. Verdict consumed, review card created and delivered.
            telegram.tick(state, config_path, api)
            conn = bridge.connect(state)
            try:
                card = conn.execute(
                    "SELECT * FROM telegram_cards WHERE task_id=? AND event_key LIKE 'task:%'",
                    (producer_task,)).fetchone()
                inspection = conn.execute(
                    "SELECT * FROM agent_os_inspections WHERE task_id=?", (producer_task,)).fetchone()
                results["inspection_verdict"] = bool(
                    inspection and inspection["verdict"] == "pass")
                results["card_delivered"] = bool(
                    card and card["delivery"] == "sent" and card["message_id"])
                card_id = card["id"] if card else None
                message_id = card["message_id"] if card else None
            finally:
                conn.close()
            # 9. Callback accept -> canonical completion + directed work enqueued.
            if card_id and message_id:
                api.queue_callback(f"aos:{card_id}:accept", user_id, chat_id, message_id)
                telegram.tick(state, config_path, api)
                conn = bridge.connect(state)
                try:
                    task = kb.get_task(conn, producer_task)
                    row = bridge.order_row(conn, producer_task)
                    results["decision_done"] = bool(
                        task and task.status == "done" and row and row["phase"] == "accepted")
                    # Accepting the routing proposal must have enqueued the
                    # directed work, owned by the proposed agent.
                    work = conn.execute(
                        "SELECT * FROM agent_os_orders WHERE work_id LIKE 'directive-%-work'").fetchone()
                    results["work_enqueued"] = bool(
                        work and kb.get_task(conn, work["task_id"]) is not None
                        and work["owning_agent"] == "eugene")
                    directive = conn.execute(
                        "SELECT status FROM telegram_directives ORDER BY id DESC").fetchone()
                    if directive:
                        results["directive_closed"] = directive["status"] == "closed"
                finally:
                    conn.close()
        # 7. Monitor channel got read-only fleet lines, never approval buttons.
        monitor_messages = [k for _m, k in api.calls
                            if k.get("chat_id") == monitor_id]
        results["monitor_channel"] = bool(
            monitor_messages and not any("reply_markup" in k for k in monitor_messages))
    finally:
        os.environ.clear()
        os.environ.update(old_env)
        telegram.ROOT = original_root
        telegram.CONFIG = original_config
        temp.cleanup()
    return results


def main():
    print("Milchik Telegram path — offline end-to-end check")
    results = run_offline_e2e()
    failed = False
    for stage in STAGES:
        ok = bool(results.get(stage))
        failed = failed or not ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {stage}")
    print("RESULT:", "PASS" if not failed else "FAIL")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
