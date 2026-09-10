"""Fallback clock: tick the fleet when the Hermes gateway is down.

The primary clock is Hermes's own no_agent cron job, which runs inside the
gateway process. When that gateway is down, its cron stops too, so Telegram
directives stop routing, inspections stop, and the review loop stalls even
though Codex/Claude (the worker harnesses) are perfectly healthy.

A systemd user timer calls this every minute. It checks the gateway's own
liveness row in state.db and ticks ONLY when that heartbeat is stale, so the
two clocks never both fire. When Hermes is healthy this is a no-op; when it
dies, this takes over within one heartbeat window.
"""

import json
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERMES = Path(__import__("os").environ.get("AGENT_OS_HERMES_ROOT", Path.home() / ".hermes/hermes-agent"))
sys.path.insert(0, str(HERMES))
sys.path.insert(0, str(ROOT))

# A gateway is "down" when it has not heartbeated for this long. The gateway
# writes its heartbeat roughly once a minute, so this gives ~2.5 missed beats
# of grace before the fallback takes over.
GATEWAY_STALE_AFTER = 150.0


def gateway_alive(home=None):
    """True while the Hermes gateway's own heartbeat is fresh.

    hermes_constants is imported only to locate the default home, so importing
    it when the caller already supplied one made this unusable -- and
    untestable -- anywhere Hermes is not installed. With no home and no Hermes
    there is no gateway to be alive, which is a False, not an ImportError.
    """
    if home is None:
        try:
            from hermes_constants import get_hermes_home
        except ImportError:
            return False
        home = get_hermes_home()
    db = Path(home) / "state.db"
    if not db.exists():
        return False
    try:
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        row = conn.execute("SELECT MAX(last_heartbeat) FROM gateway_heartbeats").fetchone()
        conn.close()
    except sqlite3.Error:
        return False
    if not row or row[0] is None:
        return False
    return (time.time() - float(row[0])) < GATEWAY_STALE_AFTER


def main():
    from adapters.hermes.fleet.bridge import tick, DEFAULT_STATE
    from adapters.hermes.fleet import telegram

    if gateway_alive():
        print(json.dumps({"status": "gateway-alive", "note": "primary clock owns the tick"}))
        return

    result = tick(DEFAULT_STATE)
    try:
        result["telegram"] = telegram.tick(DEFAULT_STATE)
    except Exception as exc:  # never leak token-bearing transport errors into logs
        result["telegram"] = {"status": "error", "error_type": type(exc).__name__}
    print(json.dumps(result))


if __name__ == "__main__":
    main()
