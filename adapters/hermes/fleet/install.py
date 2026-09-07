"""Install one no-model cron tick using Hermes's supported script/job API."""
import json
from pathlib import Path
import sys

from .bridge import ROOT, DEFAULT_STATE, connect


def install():
    from hermes_constants import get_hermes_home
    from cron.jobs import create_job, list_jobs
    home = get_hermes_home()
    scripts = home / "scripts"
    scripts.mkdir(exist_ok=True)
    target = scripts / "agent_os_fleet_tick.py"
    source = "\n".join([
        '# Installed by Agent OS; remove the matching cron job to disable.',
        'import os',
        'import sys',
        f'os.execv({sys.executable!r}, [{sys.executable!r},',
        f'    {str(ROOT / "adapters/hermes/fleet_cli.py")!r}, "tick"])',
        '',
    ])
    if target.exists() and target.read_text() != source:
        raise RuntimeError(f"Existing script differs: {target}; inspect before replacing")
    target.write_text(source)
    conn = connect(DEFAULT_STATE)
    conn.close()
    existing = [j for j in list_jobs(include_disabled=True) if j.get("name") == "Agent OS fleet dispatch"]
    if existing:
        job = existing[0]
        if job.get("script") != str(target) or not job.get("no_agent"):
            raise RuntimeError("Existing cron job has a different execution contract")
    else:
        job = create_job(prompt=None, schedule="*/1 * * * *", name="Agent OS fleet dispatch",
                         script=str(target), no_agent=True, deliver="local", workdir=str(ROOT))
    receipt = {"job_id": job["id"], "script": str(target), "state": str(DEFAULT_STATE),
               "schedule": job.get("schedule"), "no_agent": True}
    (DEFAULT_STATE / "installation.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    install()
