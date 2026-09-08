"""Run with Hermes's Python environment; usable from any working directory."""
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERMES = Path(os.environ.get("AGENT_OS_HERMES_ROOT", Path.home() / ".hermes/hermes-agent"))
PYTHON = HERMES / "venv/bin/python"
if sys.prefix != str(HERMES / "venv"):
    os.execv(str(PYTHON), [str(PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]])
sys.path.insert(0, str(HERMES))
sys.path.insert(0, str(ROOT))
os.environ["PYTHONPATH"] = os.pathsep.join([str(ROOT), str(HERMES)])


def main():
    # The autonomous host clock is composite: first advance any already-enqueued
    # governed work through Hermes, then enter the patched Telegram/control tick
    # where Milchik + Polly continuity, routing, review, and operator delivery live.
    # Running only bridge.tick skips backlog ignition; running only telegram.tick
    # would stop actual worker dispatch.
    if len(sys.argv) > 1 and sys.argv[1] == "continuity-tick":
        from adapters.hermes.fleet.bridge import DEFAULT_STATE, tick as dispatch_tick
        from adapters.hermes.fleet.telegram import tick as control_tick

        dispatch = dispatch_tick(DEFAULT_STATE)
        control = control_tick(DEFAULT_STATE)
        print(json.dumps({"dispatch": dispatch, "control": control}))
        return

    if len(sys.argv) > 1 and sys.argv[1] == "telegram":
        sys.argv.pop(1)
        from adapters.hermes.fleet.telegram import main as selected_main
    else:
        from adapters.hermes.fleet.bridge import main as selected_main
    selected_main()


if __name__ == "__main__":
    main()
