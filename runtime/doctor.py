import json
import os
import platform
import shutil
import socket
import subprocess
from pathlib import Path

from runtime.harness import codex_auto_review_enabled

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_HOSTNAME = "ashwood-host-01"
HARNESSES = ("codex", "claude", "opencode")
PROVIDERS = ("magnitude",)


def _run(args, cwd=ROOT):
    try:
        return subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return None


def _command(name):
    return shutil.which(name) is not None


def _git_value(*args):
    proc = _run(["git", *args])
    if not proc or proc.returncode != 0:
        return None
    return proc.stdout.strip()


def _tracked_secret_like_paths():
    tracked = _git_value("ls-files")
    if tracked is None:
        return []
    suspicious = []
    for raw in tracked.splitlines():
        path = raw.strip()
        name = Path(path).name.lower()
        if (
            name == ".env"
            or name in {"id_rsa", "id_ed25519", "tasks.db"}
            or name.endswith((".pem", ".p12", ".pfx"))
            or (name.endswith(".key") and not name.endswith(".public.key"))
        ):
            suspicious.append(path)
    return suspicious


def _memory_gib():
    try:
        text = Path("/proc/meminfo").read_text()
        line = next(x for x in text.splitlines() if x.startswith("MemTotal:"))
        kib = int(line.split()[1])
        return round(kib / 1024 / 1024, 1)
    except (OSError, StopIteration, ValueError):
        return None


def report():
    hostname = socket.gethostname()
    git_ok = _command("git")
    gh_ok = _command("gh")
    gh_auth = False
    if gh_ok:
        proc = _run(["gh", "auth", "status", "--hostname", "github.com"])
        gh_auth = bool(proc and proc.returncode == 0)

    repo_root = _git_value("rev-parse", "--show-toplevel") if git_ok else None
    branch = _git_value("branch", "--show-current") if git_ok else None
    head = _git_value("rev-parse", "HEAD") if git_ok else None
    porcelain = _git_value("status", "--porcelain") if git_ok else None

    harnesses = {name: _command(name) for name in HARNESSES}
    providers = {name: _command(name) for name in PROVIDERS}
    secret_like = _tracked_secret_like_paths() if git_ok else []
    codex_auto_review = codex_auto_review_enabled() if harnesses["codex"] else False

    checks = {
        "linux_host": platform.system() == "Linux",
        "expected_hostname": hostname == EXPECTED_HOSTNAME,
        "not_root": os.geteuid() != 0 if hasattr(os, "geteuid") else True,
        "git_available": git_ok,
        "github_cli_available": gh_ok,
        "github_authenticated": gh_auth,
        "agent_os_repo": bool(repo_root and Path(repo_root).resolve() == ROOT.resolve()),
        "no_tracked_secret_like_paths": not secret_like,
        "llm_harness_available": any(harnesses.values()),
        "codex_integrated_harness_available": harnesses["codex"],
        "codex_human_escalation_boundary": harnesses["codex"] and not codex_auto_review,
    }

    required = (
        "linux_host",
        "expected_hostname",
        "not_root",
        "git_available",
        "github_cli_available",
        "github_authenticated",
        "agent_os_repo",
        "no_tracked_secret_like_paths",
        "llm_harness_available",
        "codex_integrated_harness_available",
        "codex_human_escalation_boundary",
    )
    ready = all(checks[key] for key in required)

    return {
        "status": "READY" if ready else "NEEDS_SETUP",
        "host": {
            "hostname": hostname,
            "platform": platform.platform(),
            "memory_gib": _memory_gib(),
        },
        "workspace": {
            "root": str(ROOT),
            "branch": branch,
            "head": head,
            "working_tree_clean": porcelain == "" if porcelain is not None else None,
            "local_task_db_exists": (ROOT / ".agent-os" / "tasks.db").exists(),
        },
        "harnesses": harnesses,
        "integrated_harness": {
            "name": "codex",
            "mode": "interactive-read-only",
            "auto_review_detected": codex_auto_review,
        },
        "providers": providers,
        "checks": checks,
        "tracked_secret_like_paths": secret_like,
        "notes": [
            "Magnitude is optional and experimental; absence does not fail the host.",
            "Codex is the first integrated Host v1 harness; Claude and OpenCode remain detected candidates.",
            "Host v1 refuses Codex auto-review because sandbox escalation must remain human-approved.",
            "Doctor does not test or grant production, deployment, or sudo authority.",
        ],
    }


def main():
    payload = report()
    print(json.dumps(payload, indent=2))
    raise SystemExit(0 if payload["status"] == "READY" else 1)


if __name__ == "__main__":
    main()
