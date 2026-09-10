from __future__ import annotations  # TaskStore.list shadows the builtin; see below.

# Without lazy annotations this module cannot be imported on Python 3.12 at all.
# TaskStore defines a method named `list`, which binds that name in the class
# body, so the very next method's `-> list[dict[str, Any]]` evaluates
# TaskStore.list[...] and raises "'function' object is not subscriptable".
# Python 3.14 hides the bug: PEP 649 made annotations lazy by default, so a
# local run on 3.14 passes while CI on 3.12 cannot even import runtime.server.

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / ".agent-os" / "tasks.db"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class TaskStore:
    def __init__(self, path: str | Path = DEFAULT_DB):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self):
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS task_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    event TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_task_events_task_id ON task_events(task_id);

                CREATE TABLE IF NOT EXISTS routing_decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    agent TEXT,
                    harness TEXT,
                    intelligence_tier TEXT,
                    reason TEXT,
                    payload TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_routing_decisions_task_id ON routing_decisions(task_id);

                CREATE TABLE IF NOT EXISTS execution_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    attempt INTEGER NOT NULL,
                    agent TEXT,
                    harness TEXT,
                    intelligence_tier TEXT,
                    outcome TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_execution_attempts_task_id ON execution_attempts(task_id);
                """
            )

    def create(self, payload: dict[str, Any], status: str) -> str:
        task_id = str(uuid.uuid4())
        now = _now()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO tasks(id,status,created_at,updated_at,payload) VALUES(?,?,?,?,?)",
                (task_id, status, now, now, json.dumps(payload)),
            )
            self._event(conn, task_id, "CREATED", payload)
        return task_id

    def save(self, task_id: str, payload: dict[str, Any], status: str, event: str | None = None):
        now = _now()
        with self._connect() as conn:
            conn.execute(
                "UPDATE tasks SET status=?,updated_at=?,payload=? WHERE id=?",
                (status, now, json.dumps(payload), task_id),
            )
            if event:
                self._event(conn, task_id, event, payload)

    def record_routing_decision(self, task_id: str, decision: dict[str, Any]):
        """Persist why a task was routed to an agent/harness without mutating task state."""
        harness = decision.get("harness") or {}
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO routing_decisions(
                    task_id,timestamp,agent,harness,intelligence_tier,reason,payload
                ) VALUES(?,?,?,?,?,?,?)
                """,
                (
                    task_id,
                    _now(),
                    decision.get("agent"),
                    harness.get("harness"),
                    harness.get("intelligence_tier"),
                    harness.get("reason"),
                    json.dumps(decision),
                ),
            )
            self._event(conn, task_id, "ROUTED", decision)

    #: The outcome classes an attempt may record. Free-form outcomes hid the one
    #: distinction that matters: which failures justify trying another harness.
    EXECUTION_OUTCOMES = frozenset(
        {"executed", "capacity", "permission", "authentication", "failed", "timeout"})
    #: Only a provider refusing for usage/quota reasons is worth retrying
    #: elsewhere, because it is the only class where a different provider would
    #: behave differently. Rotating on a permission or authentication failure
    #: repeats it on every harness in turn and spends the attempt budget for
    #: nothing.
    ROTATABLE_OUTCOMES = frozenset({"capacity"})

    @classmethod
    def rotatable(cls, outcome: str) -> bool:
        """Whether this outcome justifies rotating to another harness."""
        return outcome in cls.ROTATABLE_OUTCOMES

    def record_execution_attempt(
        self,
        task_id: str,
        *,
        attempt: int,
        agent: str | None,
        harness: str | None,
        intelligence_tier: str | None,
        outcome: str,
        payload: dict[str, Any] | None = None,
    ):
        """Persist an execution attempt independently of the task's durable lifecycle state.

        The outcome must name one of EXECUTION_OUTCOMES, and it must be derived
        from what the harness produced rather than from a status it reports about
        itself or from an exit code alone: a harness can refuse and still exit
        zero, and a run that could not act must not be recorded as one that did.
        """
        if outcome not in self.EXECUTION_OUTCOMES:
            raise ValueError(
                f"Unknown execution outcome {outcome!r}; expected one of "
                f"{sorted(self.EXECUTION_OUTCOMES)}")
        data = payload or {}
        data.update(
            {
                "attempt": attempt,
                "agent": agent,
                "harness": harness,
                "intelligence_tier": intelligence_tier,
                "outcome": outcome,
                # Recorded rather than re-derived later, so the reason a task did
                # or did not move to another harness stays in the evidence trail.
                "rotatable": self.rotatable(outcome),
            }
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO execution_attempts(
                    task_id,timestamp,attempt,agent,harness,intelligence_tier,outcome,payload
                ) VALUES(?,?,?,?,?,?,?,?)
                """,
                (task_id, _now(), attempt, agent, harness, intelligence_tier, outcome, json.dumps(data)),
            )
            self._event(conn, task_id, "EXECUTION_ATTEMPT", data)

    def routing_history(self, task_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT timestamp,agent,harness,intelligence_tier,reason,payload FROM routing_decisions WHERE task_id=? ORDER BY id",
                (task_id,),
            ).fetchall()
            return [
                {
                    "timestamp": row["timestamp"],
                    "agent": row["agent"],
                    "harness": row["harness"],
                    "intelligence_tier": row["intelligence_tier"],
                    "reason": row["reason"],
                    "payload": json.loads(row["payload"]),
                }
                for row in rows
            ]

    def execution_history(self, task_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT timestamp,attempt,agent,harness,intelligence_tier,outcome,payload FROM execution_attempts WHERE task_id=? ORDER BY id",
                (task_id,),
            ).fetchall()
            return [
                {
                    "timestamp": row["timestamp"],
                    "attempt": row["attempt"],
                    "agent": row["agent"],
                    "harness": row["harness"],
                    "intelligence_tier": row["intelligence_tier"],
                    "outcome": row["outcome"],
                    "payload": json.loads(row["payload"]),
                }
                for row in rows
            ]

    def _event(self, conn, task_id: str, event: str, payload: dict[str, Any]):
        conn.execute(
            "INSERT INTO task_events(task_id,timestamp,event,payload) VALUES(?,?,?,?)",
            (task_id, _now(), event, json.dumps(payload)),
        )

    def get(self, task_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
            if not row:
                return None
            payload = json.loads(row["payload"])
            payload["id"] = row["id"]
            payload["status"] = row["status"]
            payload["created_at"] = row["created_at"]
            payload["updated_at"] = row["updated_at"]
            payload["events"] = self.events(task_id, conn)
            payload["routing_history"] = self.routing_history(task_id)
            payload["execution_history"] = self.execution_history(task_id)
            return payload

    def list(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [self._row(row) for row in rows]

    def _row(self, row) -> dict[str, Any]:
        payload = json.loads(row["payload"])
        payload.update({"id": row["id"], "status": row["status"], "created_at": row["created_at"], "updated_at": row["updated_at"]})
        return payload

    def events(self, task_id: str, conn=None) -> list[dict[str, Any]]:
        own = conn is None
        if own:
            conn = self._connect()
        try:
            rows = conn.execute("SELECT timestamp,event,payload FROM task_events WHERE task_id=? ORDER BY id", (task_id,)).fetchall()
            return [{"timestamp": r["timestamp"], "event": r["event"], "payload": json.loads(r["payload"])} for r in rows]
        finally:
            if own:
                conn.close()

    def evidence(self, limit: int = 100) -> list[dict[str, Any]]:
        items = []
        for task in self.list(limit):
            if task.get("evidence"):
                items.append({"task_id": task["id"], "evidence": task["evidence"], "updated_at": task["updated_at"]})
        return items
