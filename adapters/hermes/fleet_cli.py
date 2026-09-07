"""Run with Hermes's Python environment; usable from any working directory."""
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

if len(sys.argv) > 1 and sys.argv[1] == "telegram":
    sys.argv.pop(1)
    from adapters.hermes.fleet.telegram import main
else:
    from adapters.hermes.fleet.bridge import main

if __name__ == "__main__":
    main()
