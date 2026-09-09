# Hermes fleet execution

Agent OS work items now enter Hermes's SQLite Kanban queue through an explicit
local operator command. Hermes `dispatch_once` owns claims, worker PIDs, stale
recovery, run history, and concurrency. A Hermes `no_agent` cron script supplies
one tick per minute; there is no additional daemon or model-powered coordinator.

The queue is isolated at `agent-os/.agent-os/fleet/kanban.db`. This prevents the
ordinary gateway dispatcher from interpreting CLI work as Hermes chat tasks.
Use the fleet `status` command to inspect it; it is not the default dashboard board.

## Operating contract

- Trigger: existing Hermes cron, every minute. No queued work means no model call.
- Input: `contracts/work-item.schema.json`, status `approved`, canonical workspace,
  known owning product, explicit operator authority reference, expiry.
- Authority: enqueue is a trusted local operator action, not a public API. A proposed
  work item cannot authorize itself. The digest binds approval to the exact payload.
- Scope: local file work only. Publishing, messaging, deployments, purchases,
  credential changes, browser execution, and nested delegation remain out of scope.
- Harnesses: Codex CLI uses workspace-write and never bypasses approvals/sandboxing.
  Claude Code runs file tools plus Bash scoped to git/gh via --allowedTools
  (Bash(git:*), Bash(gh:*)); anything else is auto-denied in --print + dontAsk
  mode, and WebFetch/WebSearch are not loaded. Gemini CLI runs headless with
  --approval-mode auto_edit, which auto-approves edit tools and nothing else,
  so a shell call still needs a confirmation headless execution cannot give.
  Git work may use Codex or Claude; shell routes only to Codex; Gemini is
  filesystem-only. Capability routing is enforced from registry/harnesses.yaml
  at enqueue time.
- Billing: API-key environment variables are removed. Codex requires ChatGPT login;
  Claude uses its existing login. There is no API overflow route or automatic purchase.
  Subscription/account-side extra-usage settings are not inspected or changed by this adapter.
- Limits: one active task, six attempts total by default, 15 minutes per attempt,
  8 MB output per attempt, one-day authority by default (maximum seven days).
  These bound execution, not monetary spend; account pricing/quota telemetry is not available here.
- Rotation: only recognized provider usage/rate-limit errors rotate. Authentication,
  permission, timeout, and unknown failures stop for inspection. No fallback can grant
  additional capabilities. Default cooldown is one hour, or a structured retry-after
  between one minute and one day. Quota reset times are estimates when not provided.
- All eligible capacity exhausted: block and record the earliest retry. A later cron
  tick reopens the same task. Attempts and expiry persist across worker restarts.
- Continuity: same workspace, no reset/clean, per-step JSON checkpoint, per-attempt
  logs and Git status snapshots. The next harness receives the saved checkpoint.
  If a harness stops before checkpointing, saved files remain; the next harness must
  inspect them. This is artifact continuity, not conversation or hidden reasoning transfer.
- Verification: CLI success enters a non-dispatchable `agent-os-review` lane. It does
  not mean acceptance criteria passed. Evidence is available for operator inspection.
- Stop: revoke authority, pause the cron job, or let the mandate expire. The active
  worker checks revocation/claim ownership every second and heartbeats every 20 seconds.
  Stop kills the child process group before another harness may run.
- Idempotency: work ID plus payload digest; repeated enqueue returns the same task.
  Reusing an ID for changed work is rejected. Do not replay external side effects.
- Recovery: blocked non-capacity tasks require inspection; there is no automatic
  retry of authorization denials or unknown failures. Create a new explicitly approved
  work item for changed scope/budget after reviewing the old attempt.
- Rollback: pause the single cron job; source changes remain reviewable local files.
  No existing Hermes source, models, or gateway settings are replaced.

This is a same-user local execution adapter, not a hostile multi-tenant boundary.
Installed harness permission systems enforce their own restrictions. Prompts are
not a security sandbox. Do not expose the operator CLI or editable state to untrusted
users, and do not enqueue arbitrary third-party work items without review.

## Use

From any directory:

```bash
python /home/tk/Work/agent-os/adapters/hermes/fleet_cli.py status
python /home/tk/Work/agent-os/adapters/hermes/fleet_cli.py enqueue /absolute/work-item.json \
  --authority 'TK: approved local task scope, source conversation/reference' \
  --expires-in 86400 --max-attempts 6 --timeout 900
python /home/tk/Work/agent-os/adapters/hermes/fleet_cli.py tick --dry-run
python /home/tk/Work/agent-os/adapters/hermes/fleet_cli.py revoke TASK_ID
```

The launcher uses the installed Hermes virtualenv. Override `AGENT_OS_HERMES_ROOT`
only when Hermes is installed elsewhere. `--state /absolute/path` before the command
selects an isolated test queue. Do not start concurrent manual work in a workspace
currently assigned to a worker; the adapter lock cannot stop unrelated interactive agents.

OpenCode is intentionally not enabled: the installed command is an installer shim,
and its executable/permission contract could not be verified. It is not silently
substituted.

Gemini CLI is registered as a third executor so that one exhausted provider cannot
stop the fleet: it answers to a different account and quota pool than Codex or
Claude. Two prerequisites are operator actions and are not performed by this
adapter. Gemini must be logged in -- an unauthenticated run reports "Please set an
Auth method" and exits 0, which the adapter classifies as an authentication failure
so it stops for inspection rather than rotating. And the workspace must be trusted
in Gemini's own project trust store, because in an untrusted folder Gemini silently
downgrades auto_edit to prompt-for-approval, again exiting 0; a headless run then
changes nothing while appearing clean, so the adapter fails that closed as a
permission failure. --sandbox is deliberately not passed: running the agent in a
container changes how the workspace and progress checkpoint are mounted, and that
could not be exercised end to end without a live Gemini session.

## Installation and removal

With `PYTHONPATH` including Agent OS and the installed Hermes source, run
`python -m adapters.hermes.fleet.install` using Hermes's virtualenv. This writes one
script under `~/.hermes/scripts/` and registers one local-delivery `no_agent` cron job.
The installer is idempotent and refuses to overwrite a different script/job.
`installation.json` in the state directory records the job ID. Pause it with
`hermes cron pause JOB_ID`; queued work and evidence remain intact.

The gateway must be running for its builtin cron ticker to execute. Installation
does not restart the gateway. No ASHWOOD/ALVIRA marketing routine is enabled merely
by installing this execution adapter. ASHWOOD dispatch outputs still require the
reminder to publish/cross-post to the ASHWOOD Substack.

## Verification

The optional [Mr. Milchik Telegram review inbox](TELEGRAM.md) attaches to the same
cron tick. It stays inactive until private bot setup/pairing is completed. Fleet
task execution still cannot send messages; the separately configured reporting
adapter has authority only to notify the paired owner and record scoped decisions.

Run the fleet tests with Hermes's virtualenv and both repositories on `PYTHONPATH`:

```bash
PYTHONPATH=/home/tk/Work/agent-os:/home/tk/.hermes/hermes-agent \
  /home/tk/.hermes/hermes-agent/venv/bin/python -m unittest tests.test_hermes_fleet -v
```

The integration test uses the real installed Hermes dispatcher and a real executable
fixture. Provider quota failures are deliberately simulated; tests do not exhaust
subscriptions. Live provider checks must be reported separately.
