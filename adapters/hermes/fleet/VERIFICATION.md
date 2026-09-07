# Verification — 2026-09-06

Implemented and installed locally against the existing Agent OS working tree
(base commit `8fd686462dc1e2abad9f3354922c09f06d2e4f6c`). Existing unrelated
working-tree changes were preserved. This is not a committed release or deployment.

## Installed

- Hermes cron job: `bceaacabfffb`, `Agent OS fleet dispatch`.
- Every minute, `no_agent=true`, delivery `local`.
- Script: `/home/tk/.hermes/scripts/agent_os_fleet_tick.py`.
- State: `/home/tk/Work/agent-os/.agent-os/fleet/`.
- Observed successful scheduled idle ticks through the existing gateway, not just
  an installation receipt. The production work queue is empty.

## Verified

- 14 fleet tests pass under Hermes's Python 3.11 virtualenv.
- The installed Hermes dispatcher launches real executable fixtures. A simulated
  Codex quota failure transfers to a Claude fixture in the same workspace; the second
  process observes the first process's saved artifact and finishes in the review lane.
- Checkpoint continuity, idempotency/content binding, proposal rejection, expired and
  tampered authority, mid-run revocation, permission-denial stop, capacity parking,
  persisted attempt ceilings, child timeout termination, and non-mutating dry-run
  behavior are covered.
- Live Codex CLI subscription-backed execution created the expected disposable
  `smoke.txt`; file contents were independently read and matched. Run: `t_080f04be`.
- Live Claude Code execution with its existing login and restricted file tools
  created the same expected fixture. Run: `t_49a09ea2`.
- Both live runs entered `review`, never automatic `done`.
- Live fixture evidence: `/tmp/agent-os-live-smoke-lar0o_ed/results.json` and the
  per-harness state directories beside it (temporary artifacts).
- `git diff --check` passes.

## Limits and existing failures

- Provider quotas were simulated; actual subscriptions were not deliberately exhausted.
- Live provider checks used manual dispatcher ticks; the installed cron was independently
  observed executing idle ticks. No growth campaign or public action was exercised.
- OpenCode remains unavailable: its installed command resolves to an installer shim
  whose invocation failed. Gemini has no enabled binding in this adapter.
- A broader 72-test run passed 71 tests. The remaining existing product-routing test
  expects `tk-ap/tk-ap.github.io`, while the pre-existing working-tree registry change
  names `tk-ap/ashwood-info`. That product decision was not overwritten.
- Running that suite on Hermes's interpreter exposed a Python 3.11 annotation name
  collision in `runtime/store.py`; deferred annotations fix it, and the task API tests pass.
- CLI process success is not independent acceptance of real work. Review remains required.
- Quota reset telemetry and monetary caps are not available; execution limits are
  attempts, wall time, output size, and authorization expiry.

## Focused quality review

Preserved Hermes's scheduler, queue/claim semantics, existing gateway/model settings,
product ownership, browser restrictions, and unrelated local changes. Reviewed the
adapter, CLI transport, lifecycle/error paths, tests, and operating instructions.
No permission bypass flags, credential dumps, automatic publishing, or additional
coordinator daemon were introduced. Overall: core integration verified; broader
repository suite has the pre-existing routing mismatch described above.
