"""Install Agent OS no-model cron jobs using Hermes's supported job API."""
import json
from pathlib import Path
import sys

from .bridge import ROOT, DEFAULT_STATE, connect


MANAGED_PREFIX = "# Installed by Agent OS;"


def _install_script(path: Path, source: str) -> None:
    """Install or upgrade a script owned by Agent OS without touching user files."""
    if path.exists():
        existing = path.read_text()
        if existing == source:
            return
        if not existing.startswith(MANAGED_PREFIX):
            raise RuntimeError(f"Existing script differs and is not Agent OS managed: {path}; inspect before replacing")
    path.write_text(source)


def _fleet_script_source() -> str:
    return "\n".join([
        '# Installed by Agent OS; remove the matching cron job to disable.',
        'import os',
        'import sys',
        f'os.execv({sys.executable!r}, [{sys.executable!r},',
        f'    {str(ROOT / "adapters/hermes/fleet_cli.py")!r}, "continuity-tick"])',
        '',
    ])


def _update_script_source() -> str:
    return "\n".join([
        '# Installed by Agent OS; conservative fast-forward updater.',
        'import os',
        'import sys',
        f'os.execv({sys.executable!r}, [{sys.executable!r}, "-m",',
        '    "adapters.hermes.fleet.auto_update"])',
        '',
    ])


def _ensure_job(create_job, list_jobs, *, name: str, script: Path, schedule: str):
    existing = [j for j in list_jobs(include_disabled=True) if j.get("name") == name]
    if existing:
        job = existing[0]
        if job.get("script") != str(script) or not job.get("no_agent"):
            raise RuntimeError(f"Existing cron job has a different execution contract: {name}")
        return job
    return create_job(
        prompt=None,
        schedule=schedule,
        name=name,
        script=str(script),
        no_agent=True,
        deliver="local",
        workdir=str(ROOT),
    )


def install():
    from hermes_constants import get_hermes_home
    from cron.jobs import create_job, list_jobs

    home = get_hermes_home()
    scripts = home / "scripts"
    scripts.mkdir(exist_ok=True)

    fleet_target = scripts / "agent_os_fleet_tick.py"
    _install_script(fleet_target, _fleet_script_source())

    update_target = scripts / "agent_os_safe_update.py"
    _install_script(update_target, _update_script_source())

    conn = connect(DEFAULT_STATE)
    conn.close()

    fleet_job = _ensure_job(
        create_job,
        list_jobs,
        name="Agent OS fleet dispatch",
        script=fleet_target,
        schedule="*/1 * * * *",
    )
    update_job = _ensure_job(
        create_job,
        list_jobs,
        name="Agent OS safe update",
        script=update_target,
        schedule="*/1 * * * *",
    )

    receipt = {
        "state": str(DEFAULT_STATE),
        "jobs": [
            {
                "job_id": fleet_job["id"],
                "name": "Agent OS fleet dispatch",
                "script": str(fleet_target),
                "schedule": fleet_job.get("schedule"),
                "no_agent": True,
                "behavior": "run governed Telegram/continuity tick; ignite at most one already-cleared backlog item when idle",
            },
            {
                "job_id": update_job["id"],
                "name": "Agent OS safe update",
                "script": str(update_target),
                "schedule": update_job.get("schedule"),
                "no_agent": True,
                "behavior": "fast-forward clean main only; restart Milchik when Telegram runtime files change",
            },
        ],
    }
    (DEFAULT_STATE / "installation.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    install()
