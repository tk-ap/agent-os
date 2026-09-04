import tempfile
import unittest
from pathlib import Path

from runtime.server import _prepare, _status
from runtime.store import TaskStore


class TaskApiTests(unittest.TestCase):
    def test_inspection_completes_with_repository_evidence(self):
        payload = _prepare("inspect ailhat")
        self.assertEqual(payload["product_resolution"]["product_key"], "ailhat")
        self.assertEqual(_status(payload), "COMPLETED")
        self.assertEqual(payload["verification"]["status"], "VERIFIED")

    def test_implementation_stops_at_human_gate(self):
        payload = _prepare("fix the broken mobile navigation on ASHWOOD")
        self.assertEqual(payload["product_resolution"]["product_key"], "ashwood")
        self.assertEqual(payload["authorization"], "HUMAN_GATE")
        self.assertEqual(_status(payload), "HUMAN_GATE")
        self.assertNotEqual(payload["execution"].get("status"), "EXECUTED")

    def test_persistence_survives_new_store_instance(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "tasks.db"
            first = TaskStore(db)
            task_id = first.create({"request": "inspect ailhat"}, "CREATED")
            first.save(task_id, {"request": "inspect ailhat", "evidence": {"ok": True}}, "COMPLETED", event="COMPLETED")
            second = TaskStore(db)
            loaded = second.get(task_id)
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded["status"], "COMPLETED")
            self.assertEqual(loaded["evidence"]["ok"], True)
            self.assertEqual(loaded["events"][-1]["event"], "COMPLETED")


if __name__ == "__main__":
    unittest.main()
