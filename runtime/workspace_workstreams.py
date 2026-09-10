"""Bounded publisher: canonical AgentOS workstreams -> ASHWOOD /workspace projection.

AgentOS remains canonical for execution state, agent ownership, review
lifecycle, approvals, and issue/work-order state (agent-os issue #54). ASHWOOD
receives only a human-facing PROJECTION for cross-life/company/creative
synthesis. This module is not a second task system: it derives projections from
current AgentOS state (the live GitHub issue plus the routing/agent registries)
and a small manifest of stable descriptors, then pushes a snapshot to ASHWOOD.

Design constraints (from the issue):
  * derive from current state, not hand-maintained duplicate execution records;
  * authenticate with the existing WORKSPACE_BOARD_SYNC_TOKEN contract;
  * replace the AgentOS snapshot without touching other source systems' rows;
  * fail visibly but never block AgentOS execution if ASHWOOD is unavailable;
  * never send secrets, private payloads, raw prompts, or credentials.
"""
from __future__ import annotations

import json
import sqlite3
import os
import re
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from runtime.router import _load_agents, route_task
from runtime.task import Task

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_FILE = ROOT / "registry" / "workspace-workstreams.json"
ROUTING_FILE = ROOT / "registry" / "product-routing.yaml"

SOURCE_SYSTEM = "agent-os"
DEFAULT_ENDPOINT = "https://ashwood-info.vercel.app/api/workspace-workstreams"
TOKEN_ENV = "WORKSPACE_BOARD_SYNC_TOKEN"
ENDPOINT_ENV = "ASHWOOD_WORKSPACE_WORKSTREAMS_URL"

# Never let a value that looks like a credential cross the boundary. The row is
# built from a checked-in manifest and public issue metadata, so this is a
# backstop against a manifest edit that pastes a secret, not the main defence.
_SECRET_PATTERNS = [
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]{20,}"),
]

# Field caps mirror workspace/workstream.schema.json on the ASHWOOD side so a
# projection that would be silently truncated (or rejected) is caught here.
_CAPS = {
    "source_id": 250, "source_system": 80, "canonical_url": 1200, "title": 500,
    "summary": 3000, "product": 120, "owner": 120, "status": 40, "stage": 80,
    "next_gate": 1000,
}


class ProjectionError(RuntimeError):
    """Raised for a manifest/derivation problem, before anything is sent."""


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_manifest(path: Path = MANIFEST_FILE) -> dict[str, Any]:
    data = json.loads(Path(path).read_text())
    if not isinstance(data.get("sources"), list) or not data["sources"]:
        raise ProjectionError("manifest has no sources")
    return data


def _gh_issue_state(repo: str, number: int) -> dict[str, Any]:
    """Live source-object state from GitHub via the gh CLI.

    Returns title, canonical url, and open/closed state. This is the 'confirm
    actual source objects and current status' step — the volatile fields are
    read here, never stored in the manifest.
    """
    proc = subprocess.run(
        ["gh", "issue", "view", str(number), "--repo", repo,
         "--json", "number,title,state,url"],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise ProjectionError(f"gh issue view {repo}#{number} failed: {proc.stderr.strip()}")
    return json.loads(proc.stdout)


FLEET_DB = ROOT / ".agent-os" / "fleet" / "kanban.db"

# AgentOS execution phase -> the vocabulary ASHWOOD already renders.
# workspace/workstreams.mjs colours blocked/failed as risk and
# waiting_approval/review as a decision, and workspace/priorities.mjs surfaces
# "AgentOS · needs you" for exactly that second group. Sending only ACTIVE and
# DONE meant that path could never fire: the consumer was waiting for statuses
# the producer never emitted.
#
# waiting_capacity is deliberately in_progress, not a decision. Work parked on
# an exhausted provider resumes on its own and needs nobody; showing it as
# needing the operator is the same false alarm the fleet cards were fixed for.
_PHASE_STATUS = {
    "queued": "active",
    "running": "in_progress",
    "waiting_capacity": "in_progress",
    "review": "review",
    "waiting_approval": "waiting_approval",
    "collision": "blocked",
    "blocked": "blocked",
    "denied": "failed",
    "revoked": "failed",
    "accepted": "done",
    "done": "done",
}


def _status_from_issue(state: str) -> str:
    """Derive projection status from the live issue lifecycle."""
    return {"OPEN": "active", "CLOSED": "done"}.get(str(state).upper(), "active")


def _fleet_phase(work_id: str) -> str | None:
    """Current execution phase of a linked fleet order, or None.

    Read-only and best-effort. The projection must never be the reason the fleet
    database is opened for writing, and a missing database simply means there is
    no execution state to project.
    """
    if not work_id or not FLEET_DB.exists():
        return None
    try:
        conn = sqlite3.connect(f"file:{FLEET_DB}?mode=ro", uri=True)
        try:
            row = conn.execute(
                "SELECT phase FROM agent_os_orders WHERE work_id=?", (work_id,)).fetchone()
        finally:
            conn.close()
    except sqlite3.Error:
        return None
    return row[0] if row else None


def _resolve_owner(spec: str, agents: dict[str, Any]) -> str:
    """Resolve a manifest owner to a real agent id.

    '@router[:task_class]' derives the owner through the AgentOS router, so the
    projection tracks routing rather than a copied name. A literal id must exist
    in registry/agents.yaml, so the projection can never name an agent AgentOS
    does not have.
    """
    if spec.startswith("@router"):
        task_class = spec.split(":", 1)[1] if ":" in spec else "implementation"
        routed = route_task(Task(request="workspace projection owner probe",
                                 task_class=task_class))
        return routed["agent"]
    if spec not in agents:
        raise ProjectionError(f"owner '{spec}' is not in registry/agents.yaml")
    return spec


def _product_exists(product: str, routing_text: str) -> bool:
    return re.search(rf"^  {re.escape(product)}:\s*$", routing_text, re.MULTILINE) is not None


def _cap(field: str, value: str | None) -> str | None:
    if value is None:
        return None
    limit = _CAPS.get(field)
    return value if limit is None else value[:limit]


def _assert_no_secret(row: dict[str, Any]) -> None:
    blob = json.dumps(row)
    for pat in _SECRET_PATTERNS:
        if pat.search(blob):
            raise ProjectionError(
                f"refusing to publish {row.get('source_id')}: value matches a secret pattern"
            )


def build_row(source: dict[str, Any], *, agents: dict[str, Any], routing_text: str,
              issue_fetcher: Callable[[str, int], dict[str, Any]] | None = None,
              execution_fetcher: Callable[[str], str | None] | None = None,
              now: str | None = None) -> dict[str, Any]:
    # Resolved on call, not bound as a default. A default argument is evaluated
    # once when the module is imported, so patching _gh_issue_state afterwards
    # never reached this parameter and the "mocked" tests called the live
    # GitHub API -- passing wherever gh happened to be authenticated and failing
    # everywhere else.
    issue_fetcher = issue_fetcher or _gh_issue_state
    execution_fetcher = execution_fetcher or _fleet_phase
    repo = source["repo"]
    number = int(source["issue"])
    product = source["product"]
    if not _product_exists(product, routing_text):
        raise ProjectionError(f"product '{product}' is not in registry/product-routing.yaml")

    issue = issue_fetcher(repo, number)
    owner = _resolve_owner(source["owner"], agents)

    goal_ids = [str(g) for g in source.get("goal_ids", [])][:12]
    if "ownership" not in goal_ids:
        # The issue requires ownership for both first workstreams; keep it a
        # hard invariant so a manifest edit cannot silently drop it.
        raise ProjectionError(f"{repo}#{number}: goal_ids must include 'ownership'")

    # AgentOS is canonical for execution state, so a linked fleet order decides
    # the status and the issue lifecycle is the fallback. A phase with no honest
    # ASHWOOD equivalent -- superseded, say, where a revision carries the work
    # forward -- also falls back rather than being forced into a bucket that
    # would misreport it.
    phase = execution_fetcher(source.get("work_id") or "")
    status = _PHASE_STATUS.get(str(phase or ""), None) or _status_from_issue(
        issue.get("state", "OPEN"))

    row = {
        "source_id": _cap("source_id", f"{SOURCE_SYSTEM}#{number}"),
        "source_system": SOURCE_SYSTEM,
        "canonical_url": _cap("canonical_url", issue.get("url")),
        "title": _cap("title", issue.get("title") or f"{repo}#{number}"),
        "summary": _cap("summary", source.get("summary")),
        "product": _cap("product", product),
        "owner": _cap("owner", owner),
        "status": _cap("status", status),
        "stage": _cap("stage", source.get("stage")),
        "next_gate": _cap("next_gate", source.get("next_gate")),
        "goal_ids": goal_ids,
        "confidence": max(0.0, min(1.0, float(source.get("confidence", 1)))),
        "metadata": {
            "issue": number,
            "repo": repo,
            "issue_state": issue.get("state"),
            "owner_spec": source["owner"],
            "execution_phase": phase,
            "status_basis": "agent-os execution phase" if phase in _PHASE_STATUS else "github issue lifecycle",
            "derivation": "live GitHub issue state + registry-resolved owner/product",
        },
        "observed_at": now or _utcnow_iso(),
    }
    _assert_no_secret(row)
    return row


def build_snapshot(manifest: dict[str, Any] | None = None, *,
                   issue_fetcher: Callable[[str, int], dict[str, Any]] | None = None,
                   execution_fetcher: Callable[[str], str | None] | None = None,
                   now: str | None = None) -> dict[str, Any]:
    issue_fetcher = issue_fetcher or _gh_issue_state
    execution_fetcher = execution_fetcher or _fleet_phase
    manifest = manifest or load_manifest()
    agents = _load_agents()
    routing_text = ROUTING_FILE.read_text()
    rows = [build_row(s, agents=agents, routing_text=routing_text,
                      issue_fetcher=issue_fetcher, execution_fetcher=execution_fetcher, now=now)
            for s in manifest["sources"]]
    # replace scoped to this source_system only: ASHWOOD deletes agent-os rows
    # not in this snapshot and leaves every other system's projections intact.
    return {"source_system": SOURCE_SYSTEM, "replace": True, "rows": rows}


def publish(snapshot: dict[str, Any], *, endpoint: str | None = None,
            token: str | None = None,
            opener: Callable[[urllib.request.Request], Any] = urllib.request.urlopen,
            timeout: int = 10) -> dict[str, Any]:
    """POST the snapshot. Fails visibly, never raises into the caller.

    Returns {ok, ...}. A missing token or an ASHWOOD outage yields ok=False with
    a reason so a scheduler can surface a stale/failed sync without stopping
    AgentOS execution.
    """
    endpoint = endpoint or os.getenv(ENDPOINT_ENV) or DEFAULT_ENDPOINT
    token = token or os.getenv(TOKEN_ENV)
    if not token:
        return {"ok": False, "reason": f"{TOKEN_ENV} not configured", "sent": 0}

    body = json.dumps(snapshot).encode()
    request = urllib.request.Request(
        endpoint, data=body, method="POST",
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {token}"},
    )
    try:
        with opener(request, timeout=timeout) as response:
            payload = json.loads(response.read() or b"{}")
        return {"ok": True, "endpoint": endpoint, "sent": len(snapshot["rows"]),
                "response": payload}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "reason": f"HTTP {exc.code}", "sent": 0,
                "detail": exc.read().decode(errors="replace")[:500]}
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {"ok": False, "reason": f"ASHWOOD unreachable: {exc}", "sent": 0}


def run(dry_run: bool = False) -> dict[str, Any]:
    snapshot = build_snapshot()
    if dry_run:
        return {"ok": True, "dry_run": True, "snapshot": snapshot}
    return publish(snapshot)


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="build and print the snapshot without sending")
    args = parser.parse_args()
    try:
        result = run(dry_run=args.dry_run)
    except ProjectionError as exc:
        print(json.dumps({"ok": False, "reason": str(exc)}, indent=2))
        raise SystemExit(1)
    print(json.dumps(result, indent=2))
    # A failed live sync is visible (non-zero exit) but is a publish failure,
    # never a projection/derivation crash that could implicate AgentOS work.
    if not result.get("ok"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
