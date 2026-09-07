"""Install Agent OS no-model cron jobs using Hermes's supported job API."""
import json
from pathlib import Path
import sys

from .bridge import ROOT, DEFAULT_STATE, connect


def _install_script(path: Path, source: str) -> None:
    if path.exists() and path.read_text() != source:
        raise RuntimeError(f"Existing script differs: {path}; inspect before replacing")
    path.write_text(source)


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
    fleet_source = "\n".join([
        '# Installed by Agent OS; remove the matching cron job to disable.',
        'import os',
        'import sys',
        f'os.execv({sys.executable!r}, [{sys.executable!r},',
        f'    {str(ROOT / "adapters/hermes/fleet_cli.py")!r}, "tick"])',
        '',
    ])
    _install_script(fleet_target, fleet_source)

    update_target = scripts / "agent_os_safe_update.py"
    update_source = "\n".join([
        '# Installed by Agent OS; conservative fast-forward updater.',
        'import os',
        'import sys',
        f'os.execv({sys.executable!r}, [{sys.executable!r}, "-m",',
        '    "adapters.hermes.fleet.auto_update"])',
        '',
    ])
    _install_script(update_target, update_source)

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
