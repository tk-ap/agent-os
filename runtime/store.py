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
