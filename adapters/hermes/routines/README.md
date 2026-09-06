# Hermes Scheduler Binding — Agent OS Routines

How the routine contracts in `routines/` bind to a clock on this host. Written 2026-09-06.

Per `docs/CONTROL_PLANE_CHARTER.md`, routine contracts are host-agnostic and scheduler-specific configuration belongs in an adapter. This is that adapter layer for the Hermes operator harness.

**A schedule is not authority.** Everything here is a trigger mechanism. Nothing in this directory widens what a routine may do; the routine contract and its task envelope remain the only sources of that.

## Host facts, verified 2026-09-06

| Fact | State |
|---|---|
| Hermes installed | Yes — `~/.hermes/hermes-agent` with venv |
| `hermes-gateway.service` | **active (running)** |
| Hermes cron | Available — `hermes_cli/cron.py`, builtin ticker |
| System cron | **Not present** — no `crontab` binary |
| systemd user timers | Available, **none defined** |
| Mr. Milchik Telegram inbox | **Configured and paired** 2026-09-06 — `~/.hermes/agent-os-telegram.json`, mode 0600 |

**The builtin ticker runs inside the gateway process** (`hermes_cli/cron.py:45`): a scheduled job with no live gateway never fires, though `next_run_at` still advances. The gateway is currently up. If it stops, jobs silently stop firing — `hermes cron doctor` is the check, and a routine that has not run is indistinguishable from a routine that ran and skipped unless its evidence record says so. This is why every routine writes a record even on a no-op.

## First finding, before the routine was even bound

Running `monitors/discoverability-fingerprint.sh` as a smoke test on 2026-09-06 flagged `alvira.ctonew.app` as unreachable. That domain is the decommissioned cto.new surface and its 503 is expected — ALVIRA has moved to **`alviratech.vercel.app`**, which returns 200 on `/`, `/pricing`, and `/sitemap.xml`. The monitor now watches the live domain and keeps the legacy one only as a decommission check.

What the correction surfaced instead is worse, and live right now:

```
$ curl -s https://alviratech.vercel.app/sitemap.xml | grep -o '<loc>[^<]*'
<loc>https://alvira.ctonew.app/
<loc>https://alvira.ctonew.app/pricing
... all 10 URLs on the dead domain

$ curl -s https://alviratech.vercel.app/robots.txt
Sitemap: https://alvira.ctonew.app/sitemap.xml
```

**The live ALVIRA site advertises 10 canonical URLs on a domain that returns 503, and points crawlers at a sitemap that no longer resolves.** Every discoverability signal the site emits refers to the decommissioned host.

This is the highest-severity class the audit routine defines — de-indexing risk (`routines/discoverability-audit.md` §12) — and it is exactly the mechanical, non-copy defect the routine exists to catch and fix. The fix is in `tk-ap/ALVIRA` at `public/sitemap.xml` and `public/robots.txt`; three further legacy references sit in `ALVIRA_LOGO_FIDELITY_FIX_BRIEF.md`, `docs/VERCEL_RUNTIME_MIGRATION.md`, and `codex/launch-readiness-report`.

Not fixed here. Cross-product writes default to `propose-handoff` under `adapters/hermes/WORKSPACE_CONTRACT.yaml`, and the audit routine's authority is read-and-propose only. It is a one-line-per-URL change and worth doing before the routine is ever scheduled.

## Why Hermes cron and not systemd

`registry/harnesses.yaml` already registers the binding `hermes-fleet` with `trigger: hermes-cron-no-agent` and `scope: local-file-work`. The routines are local-file work. Using the same trigger mechanism keeps one scheduler on this host rather than two, and `hermes cron doctor` / `cron status` / `cron runs` give operational visibility a systemd timer would not.

## The monitor-script fit

Hermes cron supports `--monitor-script`: *"agent runs only on output change"* (`hermes_cli/cron.py:_JOB_DETAIL_LINES`).

This maps exactly onto the skip/no-op condition every routine contract requires. Instead of waking an agent that reads state, decides nothing changed, and costs ~$0.25 to conclude it should stop, a cheap script emits a fingerprint of the trigger state and **the agent runs only when that fingerprint changes.**

The skip condition stops being something the model must remember and becomes structural. It also means an idle week costs approximately nothing rather than the projected skip-run cost in `routines/COST_PROJECTIONS.md` — the period projections there are therefore conservative.

## Binding status per routine

| Routine | Contract status | Trigger source | Bindable now |
|---|---|---|---|
| `discoverability-audit` | `REVIEWED` | Live sitemaps + repo routes — self-contained | **Yes** |
| `ashwood-build-journal` | `REVIEWED` | Evidence ledger — **does not exist** | No — needs a trigger decision |
| `ashwood-dispatch` | `REVIEWED` | `LEARNING` records — **do not exist** | No — no fallback available |

`runtime/evidence.py` builds an in-memory evidence dict per task run and returns it. It does not persist a queryable ledger and has no `visibility` field, so nothing is classified `public-candidate`. Both ASHWOOD publishing routines trigger on that classification. See each routine's §3 for the options.

**Only the audit routine has a real trigger today.** It is also the only one of the three whose side effect is a draft PR rather than a public page, which makes it the correct first binding on both counts.

## Job definitions

`jobs.yaml` holds the declarative definitions. `apply.sh` contains the exact `hermes cron create` commands.

**Neither has been run.** Creating the jobs starts recurring execution, which is TK's decision, not the adapter's — see `apply.sh`.

## What this binding does not do

- It does not grant authority. A job that fires still executes under its routine contract and task envelope.
- It does not deliver notifications. Mr. Milchik is now paired, but it carries fleet review cards only; routine escalations, cap breaches, and approvals are a separate action-specific binding that does not exist yet (`fleet/TELEGRAM.md`). Until it does, a suspended routine is discovered by reading `hermes cron runs` or the evidence directory, not by being told. Tracked in `routines/BACKLOG.md`.
- It does not hold secrets. No routine here needs a credential; the audit routine authenticates to nothing.
