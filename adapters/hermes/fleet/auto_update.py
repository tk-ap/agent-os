"""Safely fast-forward Agent OS main and reload Milchik when runtime code changes.

This is intentionally conservative: it never force-pulls, never switches branches,
never touches a dirty worktree, and never widens authority. It only updates a clean
checkout already on `main` when `origin/main` is a strict fast-forward.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import time

from .bridge import ROOT, DEFAULT_STATE

RUNTIME_PREFIXES = (
    "adapters/hermes/fleet/telegram",
    "adapters/hermes/fleet/__init__.py",
    "adapters/hermes/fleet_cli.py",
    "registry/agents.yaml",
)
RECEIPT = DEFAULT_STATE / "auto-update.json"


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args), cwd=ROOT, text=True, capture_output=True, check=check
    )


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run("git", *args, check=check)


def write_receipt(**data) -> None:
    DEFAULT_STATE.mkdir(parents=True, exist_ok=True)
    payload = {"ts": time.time(), **data}
    RECEIPT.write_text(json.dumps(payload, indent=2) + "\n")


def current_branch() -> str:
    return git("branch", "--show-current").stdout.strip()


def is_clean() -> bool:
    return not git("status", "--porcelain").stdout.strip()


def changed_files(old: str, new: str) -> list[str]:
    out = git("diff", "--name-only", old, new).stdout
    return [line.strip() for line in out.splitlines() if line.strip()]


def affects_milchik(paths: list[str]) -> bool:
    return any(any(path.startswith(prefix) for prefix in RUNTIME_PREFIXES) for path in paths)


def restart_milchik() -> tuple[bool, str]:
    restart = subprocess.run(
        ["systemctl", "--user", "restart", "milchik-listener.service"],
        text=True, capture_output=True,
    )
    if restart.returncode != 0:
        return False, (restart.stderr or restart.stdout).strip()
    active = subprocess.run(
        ["systemctl", "--user", "is-active", "milchik-listener.service"],
        text=True, capture_output=True,
    )
    ok = active.returncode == 0 and active.stdout.strip() == "active"
    return ok, (active.stdout or active.stderr).strip()


def update() -> dict:
    if current_branch() != "main":
        result = {"status": "skipped", "reason": "checkout is not on main"}
        write_receipt(**result)
        return result
    if not is_clean():
        result = {"status": "blocked", "reason": "worktree has local changes"}
        write_receipt(**result)
        return result

    before = git("rev-parse", "HEAD").stdout.strip()
    fetch = git("fetch", "origin", "main", check=False)
    if fetch.returncode != 0:
        result = {"status": "blocked", "reason": "git fetch failed", "detail": (fetch.stderr or fetch.stdout).strip()}
        write_receipt(**result)
        return result

    remote = git("rev-parse", "origin/main").stdout.strip()
    if remote == before:
        result = {"status": "current", "commit": before}
        write_receipt(**result)
        return result

    ancestor = git("merge-base", "--is-ancestor", before, remote, check=False)
    if ancestor.returncode != 0:
        result = {"status": "blocked", "reason": "origin/main is not a fast-forward", "local": before, "remote": remote}
        write_receipt(**result)
        return result

    paths = changed_files(before, remote)
    merge = git("merge", "--ff-only", "origin/main", check=False)
    if merge.returncode != 0:
        result = {"status": "blocked", "reason": "fast-forward merge failed", "detail": (merge.stderr or merge.stdout).strip()}
        write_receipt(**result)
        return result

    after = git("rev-parse", "HEAD").stdout.strip()
    result: dict = {"status": "updated", "from": before, "to": after, "changed_files": paths}

    if affects_milchik(paths):
        ok, detail = restart_milchik()
        result["milchik_restarted"] = True
        result["milchik_active"] = ok
        result["milchik_status"] = detail
        if not ok:
            result["status"] = "updated_but_listener_unhealthy"
    else:
        result["milchik_restarted"] = False

    write_receipt(**result)
    return result


def main() -> None:
    print(json.dumps(update(), indent=2))


if __name__ == "__main__":
    main()
