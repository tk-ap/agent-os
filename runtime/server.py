import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from runtime.authorization import authorize
from runtime.evidence import record
from runtime.executor import execute
from runtime.product import resolve_product
from runtime.router import route_task
from runtime.skills import resolve_skills
from runtime.store import TaskStore
from runtime.task import normalize
from runtime.verifier import verify


store = TaskStore()


def _status(task):
    if task.get("cancelled"):
        return "CANCELLED"
    auth = task.get("authorization", "")
    execution = task.get("execution", {})
    verification = task.get("verification", {})
    if verification.get("status") == "VERIFIED":
        return "COMPLETED"
    if execution.get("status") == "FAILED":
        return "FAILED"
    if execution.get("status") == "EXECUTED":
        return "VERIFYING"
    if auth == "HUMAN_GATE":
        return "HUMAN_GATE"
    if auth == "AUTHORIZED":
        return "AUTHORIZED"
    return "RESOLVING"


def _prepare(request: str, product: str | None = None, environment: str | None = None):
    task = normalize(request)
    resolved = resolve_product(request, product)
    if resolved.get("status") == "RESOLVED":
        task.product = resolved["product_key"]
    routing = route_task(task)
    skills = resolve_skills(task)
    authorization = authorize(task)
    if skills["status"] == "BLOCKED":
        task.execution = {"status": "BLOCKED", "reason": "No admitted skills were available for this task."}
    elif authorization["status"] != "AUTHORIZED":
        task.execution = {"status": "BLOCKED", "reason": authorization["reason"]}
    elif resolved.get("status") != "RESOLVED":
        task.execution = {"status": "BLOCKED", "reason": resolved.get("reason", "Product resolution failed.")}
    else:
        execute(task, resolved)
    verify(task)
    evidence = record(task)
    payload = task.to_dict()
    payload.update({"product_resolution": resolved, "routing": routing, "skills_resolution": skills, "authorization_result": authorization})
    if environment:
        payload["environment"] = environment
    return payload


def _authorize(task: dict):
    if task.get("status") != "HUMAN_GATE":
        return task
    if task.get("task_class") != "implementation":
        task["authorization"] = "AUTHORIZED"
        return task
    # Authorization changes state; mutation adapters remain explicitly bounded.
    task["authorization"] = "AUTHORIZED"
    task["execution"] = {"status": "BLOCKED", "reason": "Implementation authorization granted, but no mutation adapter is enabled in this runtime."}
    task["verification"] = {"status": "FAILED", "reason": "No implementation adapter is enabled."}
    task["evidence"]["authorization"] = "HUMAN_APPROVED"
    return task


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, body):
        data = json.dumps(body, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self._send(204, {})

    def _json(self):
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length) or b"{}")

    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/")
        if path == "" or path == "/health":
            return self._send(200, {"status": "ok", "service": "agent-os", "api": "v1"})
        if path == "/tasks":
            return self._send(200, {"tasks": store.list()})
        if path.startswith("/tasks/"):
            task = store.get(path.split("/")[2])
            return self._send(200 if task else 404, task or {"error": "Task not found"})
        if path == "/projects":
            from runtime.product import _products, ROUTING_FILE
            return self._send(200, {"projects": _products(ROUTING_FILE.read_text())})
        if path == "/agents":
            from runtime.router import _load_agents
            return self._send(200, {"agents": _load_agents()})
        if path == "/evidence":
            return self._send(200, {"evidence": store.evidence()})
        return self._send(404, {"error": "Not found"})

    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/")
        try:
            body = self._json()
            if path == "/tasks":
                request = body.get("request")
                if not isinstance(request, str) or not request.strip():
                    return self._send(400, {"error": "request is required"})
                payload = _prepare(request, body.get("product"), body.get("environment"))
                status = _status(payload)
                task_id = store.create(payload, status)
                payload["id"] = task_id
                store.save(task_id, payload, status, event="STATE_INITIALIZED")
                return self._send(201, payload)

            parts = path.split("/")
            if len(parts) == 4 and parts[1] == "tasks" and parts[3] in {"authorize", "cancel"}:
                task_id, action = parts[2], parts[3]
                task = store.get(task_id)
                if not task:
                    return self._send(404, {"error": "Task not found"})
                if action == "cancel":
                    if task["status"] in {"COMPLETED", "FAILED", "CANCELLED"}:
                        return self._send(409, {"error": "Task is already terminal"})
                    task["cancelled"] = True
                    task["execution"] = {"status": "CANCELLED", "reason": "Cancelled by user."}
                    task["verification"] = {"status": "FAILED", "reason": "Cancelled before completion."}
                    store.save(task_id, task, "CANCELLED", event="CANCELLED")
                    return self._send(200, task)
                if task["status"] != "HUMAN_GATE":
                    return self._send(409, {"error": "Task is not awaiting human authorization", "status": task["status"]})
                task = _authorize(task)
                status = _status(task)
                store.save(task_id, task, status, event="AUTHORIZED")
                return self._send(200, task)
        except (ValueError, TypeError, KeyError) as exc:
            return self._send(400, {"error": str(exc)})
        except Exception as exc:
            return self._send(500, {"error": str(exc)})
        return self._send(404, {"error": "Not found"})

    def log_message(self, *_args):
        return


def main():
    parser = argparse.ArgumentParser(description="Agent OS Task API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Agent OS API listening on http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
