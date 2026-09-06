#!/usr/bin/env bash
# Create the Hermes cron job for routines/discoverability-audit.md
#
# NOT RUN AUTOMATICALLY. Creating the job starts recurring execution, which is
# TK's decision. Run it yourself when you want the routine live.
#
# Only the audit routine is defined here. The two ASHWOOD publishing routines
# are blocked on trigger sources that do not exist — see jobs.yaml.

set -euo pipefail

ADAPTER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONITOR="$ADAPTER_DIR/monitors/discoverability-fingerprint.sh"
PROMPT_FILE="$ADAPTER_DIR/prompts/discoverability-audit.md"

echo "== Preflight =="

# The builtin ticker runs inside the gateway process. Without it, jobs never
# fire while next_run_at keeps advancing — a silent failure mode.
systemctl --user is-active --quiet hermes-gateway.service \
  && echo "  gateway: running" \
  || { echo "  gateway: NOT RUNNING — jobs will not fire. Start it before creating."; exit 1; }

echo "  monitor: $MONITOR"
"$MONITOR" >/dev/null && echo "  monitor runs clean" || { echo "  monitor FAILED"; exit 1; }

echo
echo "== Confirm the flag names before running the create =="
echo "The field names in hermes_cli/cron.py are: schedule, prompt, name, script,"
echo "monitor_script, workdir, model, reasoning_effort, deliver, failure_deliver,"
echo "repeat, continuity, no_agent. The argparse spelling was not verified when"
echo "this file was written — check it, then uncomment the create below."
echo
hermes cron create --help || true

echo
echo "== The job to create =="
cat <<'JOB'
hermes cron create \
  --name "agent-os-discoverability-audit" \
  --schedule "weekly" \
  --workdir /home/tk/Work \
  --monitor-script <ADAPTER_DIR>/monitors/discoverability-fingerprint.sh \
  --prompt "$(cat <ADAPTER_DIR>/prompts/discoverability-audit.md)"
JOB

echo
echo "Not executed. Uncomment in this script once the flags are confirmed."

# --- uncomment to create ---
# hermes cron create \
#   --name "agent-os-discoverability-audit" \
#   --schedule "weekly" \
#   --workdir /home/tk/Work \
#   --monitor-script "$MONITOR" \
#   --prompt "$(cat "$PROMPT_FILE")"

echo
echo "After creating:  hermes cron status && hermes cron doctor"
echo "Run history:     hermes cron runs agent-os-discoverability-audit"
echo "Stop it:         hermes cron  (see subcommands for pause/delete)"
