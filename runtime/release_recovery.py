"""Provider-neutral durable release-recovery state for Polly.

This module owns no deployment credentials and performs no external mutation.
It answers the control-plane questions that must survive process/model restarts:
what release is pending, when may it be checked again, and is the same approved
action still eligible to resume?
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from typing import Any


NON_TERMINAL = {
    "ready", "checking", "waiting_availability", "executing", "reconciling", "verifying"
}
TERMINAL = {"live_verified", "superseded", "cancelled", "human_required"}
ALL_STATES = NON_TERMINAL | TERMINAL


def iso(ts: float | None = None) -> str:
    return datetime.fromtimestamp(time.time() if ts is None else ts, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def parse_iso(value: str | None) -> float | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def is_terminal(record: dict[str, Any]) -> bool:
    return record.get("state") in TERMINAL


def due(record: dict[str, Any], now: float | None = None) -> bool:
    """Whether a non-terminal record is eligible for a deterministic check."""
    if is_terminal(record):
        return False
    check_at = parse_iso((record.get("retry_policy") or {}).get("next_check_at"))
    return check_at is None or check_at <= (time.time() if now is None else now)


def stable_backoff(recovery_id: str, check_count: int, *, base: int = 60, cap: int = 3600) -> int:
    """Bounded exponential backoff with stable ±10% jitter for reproducible tests."""
    exponent = max(0, min(int(check_count), 10))
    raw = min(cap, base * (2 ** exponent))
    digest = hashlib.sha256(f"{recovery_id}:{check_count}".encode()).digest()
    fraction = int.from_bytes(digest[:2], "big") / 65535
    jitter = 0.9 + fraction * 0.2
    return max(1, min(cap, int(raw * jitter)))


def resume_eligibility(record: dict[str, Any], *, now: float | None = None) -> tuple[bool, str]:
    """Fail-closed gate for another mutation attempt under the same grant."""
    now = time.time() if now is None else now
    if is_terminal(record):
        return False, f"terminal:{record.get('state')}"

    authority = record.get("authority") or {}
    if authority.get("status") != "valid":
        return False, f"authority:{authority.get('status', 'unresolved')}"
    expires = parse_iso(authority.get("expires_at"))
    if expires is not None and expires <= now:
        return False, "authority:expired"

    policy = record.get("retry_policy") or {}
    attempts = int(record.get("mutation_attempts", 0))
    if attempts >= int(policy.get("max_mutation_attempts", 0)):
        return False, "retry-budget-exhausted"

    created = parse_iso(record.get("created_at"))
    max_elapsed = int(policy.get("max_elapsed_seconds", 0))
    if created is not None and max_elapsed and now - created >= max_elapsed:
        return False, "elapsed-budget-exhausted"

    if record.get("state") == "reconciling":
        return False, "reconciliation-required"
    if not due(record, now):
        return False, "not-due"
    return True, "eligible"


def wait_for_availability(
    record: dict[str, Any], *, blocker_class: str, reason: str,
    now: float | None = None, provider_retry_at: float | None = None,
) -> dict[str, Any]:
    """Return a new record parked until a later cheap availability check."""
    now = time.time() if now is None else now
    value = deepcopy(record)
    value["state"] = "waiting_availability"
    value["availability_checks"] = int(value.get("availability_checks", 0)) + 1
    policy = value.setdefault("retry_policy", {})
    if provider_retry_at is None:
        delay = stable_backoff(value["recovery_id"], value["availability_checks"] - 1)
        provider_retry_at = now + delay
        policy["backoff_seconds"] = delay
    policy["next_check_at"] = iso(provider_retry_at)
    policy["provider_retry_at"] = iso(provider_retry_at)
    old = value.get("blocker") or {}
    value["blocker"] = {
        "class": blocker_class,
        "reason": reason,
        "evidence": old.get("evidence", []),
        "first_seen_at": old.get("first_seen_at") or iso(now),
        "last_seen_at": iso(now),
    }
    value["updated_at"] = iso(now)
    return value


def require_human(record: dict[str, Any], reason: str, *, now: float | None = None) -> dict[str, Any]:
    value = deepcopy(record)
    value["state"] = "human_required"
    value["terminal_reason"] = reason
    value["updated_at"] = iso(now)
    return value


def mark_mutation_started(record: dict[str, Any], *, now: float | None = None) -> dict[str, Any]:
    ok, reason = resume_eligibility(record, now=now)
    if not ok:
        raise ValueError(f"release recovery may not resume: {reason}")
    value = deepcopy(record)
    value["state"] = "executing"
    value["mutation_attempts"] = int(value.get("mutation_attempts", 0)) + 1
    value["updated_at"] = iso(now)
    return value


def mark_reconciling(record: dict[str, Any], detail: dict[str, Any] | None = None,
                     *, now: float | None = None) -> dict[str, Any]:
    value = deepcopy(record)
    value["state"] = "reconciling"
    value["last_reconciliation"] = {"status": "pending", **(detail or {})}
    value["updated_at"] = iso(now)
    return value


def mark_verifying(record: dict[str, Any], *, owner: str = "w-dog", now: float | None = None) -> dict[str, Any]:
    value = deepcopy(record)
    value["state"] = "verifying"
    value["verification"] = {"owner": owner, "status": "pending"}
    value["updated_at"] = iso(now)
    return value


def mark_live_verified(record: dict[str, Any], evidence: list[dict[str, Any]],
                       *, now: float | None = None) -> dict[str, Any]:
    if not evidence:
        raise ValueError("live_verified requires evidence")
    value = deepcopy(record)
    value["state"] = "live_verified"
    value["verification"] = {
        **(value.get("verification") or {}),
        "status": "verified",
        "checked_at": iso(now),
        "evidence": evidence,
    }
    value["terminal_evidence"] = evidence
    value["updated_at"] = iso(now)
    return value


class RecoveryStore:
    """One JSON file per recovery id; atomic replace, no secrets."""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)

    def path_for(self, recovery_id: str) -> Path:
        if not recovery_id or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_." for c in recovery_id):
            raise ValueError("invalid recovery_id")
        return self.root / f"{recovery_id}.json"

    def save(self, record: dict[str, Any]) -> Path:
        state = record.get("state")
        if state not in ALL_STATES:
            raise ValueError(f"unknown recovery state: {state}")
        path = self.path_for(record["recovery_id"])
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
        temporary.chmod(0o600)
        temporary.replace(path)
        return path

    def load(self, recovery_id: str) -> dict[str, Any]:
        return json.loads(self.path_for(recovery_id).read_text())

    def all(self) -> list[dict[str, Any]]:
        records = []
        for path in sorted(self.root.glob("*.json")):
            try:
                value = json.loads(path.read_text())
            except (OSError, ValueError):
                continue
            if isinstance(value, dict):
                records.append(value)
        return records

    def due(self, now: float | None = None) -> list[dict[str, Any]]:
        return [record for record in self.all() if due(record, now)]
