# Routines

Routine contracts defined under `skills/owned/recurring-work/SKILL.md`.

These files are **declarative contracts, not runtime code**. They do not schedule jobs, hold credentials, invoke models, connect hosts, or execute mutations. Defining a routine here does not start it.

## Rules

- A schedule is not authority. A routine may only do what an existing grant already permits; repetition never widens scope.
- Scheduler-specific configuration (GitHub Actions, host cron, Vercel, a local loop) belongs in the relevant host or product adapter, never in this directory.
- Every routine has a skip/no-op path. Absence of work must produce no output and no side effect.
- A routine whose target, audience, path scope, or irreversibility materially changes requires fresh authorization before it resumes.

## Status model

| Status | Meaning |
|---|---|
| `DRAFT` | Written, not reviewed. Must not be bound to a scheduler. |
| `REVIEWED` | Required reviewers signed off. Runs in dry-run/PR mode only. A routine can be `REVIEWED` and still unbindable if its trigger source does not exist. |
| `ACTIVE` | Bound to a scheduler and permitted to take its declared side effects. |
| `SUSPENDED` | Paused by anomaly, stop condition, or human decision. Resuming requires a recorded reason. |

Promotion from `REVIEWED` to `ACTIVE` is a human decision by TK. Demotion to `SUSPENDED` is automatic when a declared anomaly or stop condition fires.

## Contents

| Path | What it is |
|---|---|
| `envelopes/` | Task envelopes — what work each routine is permitted to do (`skills/owned/task-envelope/SKILL.md`). One per routine; see `envelopes/README.md` for why three and not one. |
| `COST_PROJECTIONS.md` | Basis for every cap below: price basis, measured inputs, per-run and period projections, re-basing plan. |
| `BACKLOG.md` | Deferred items, open handoffs to TK, and the standing out-of-scope list. |

## Index

| Routine | Owner | Authority class | Side effect | Caps | Status | Trigger source |
|---|---|---|---|---|---|---|
| `ashwood-build-journal.md` | Marlo | `scoped-publish` (Marlo §09) | Public page commit to `ashwood-info` | $6/run · $25/mo | `REVIEWED` | **Missing** — no evidence ledger |
| `ashwood-dispatch.md` | Marlo | `scoped-publish` (Marlo §09) | Public page commit + recorded handoff to TK | $8/run · $25/mo | `REVIEWED` | **Missing** — no `LEARNING` store |
| `discoverability-audit.md` | Eugene | `AUTONOMOUS + AUDIT` (read + draft PR only) | Draft PR. Never merges. | $5/run · $30/mo | `REVIEWED` | Available — self-contained |

**Contract status and bindability are different axes.** All three contracts are complete and reviewed. Only the audit routine has a trigger source that exists on this host, so only it can be bound to a scheduler. `runtime/evidence.py` returns an in-memory evidence dict per task run; it persists no queryable ledger and has no `visibility` field, so nothing is classified `public-candidate` — which is what both ASHWOOD publishing routines trigger on. Each routine's §3 carries the options.

**Scheduler binding:** `adapters/hermes/routines/`. Defined, not applied.

**Portfolio breaker: $75/month across all routines suspends all three**, not only the routine that exceeded its own cap. A single routine can fail loudly inside its own cap while the aggregate is what signals something is wrong.

## Resolved decisions

Settled 2026-09-06:

1. **Routine evidence destination** — `docs/evidence/routines/<routine-id>/<YYYY-MM-DD>-<run-id>.json`, kept separate from the security-scoped `docs/security/evidence/`. Record shape: `docs/evidence/routines/README.md`.
2. **Cadences** — journal weekly, audit weekly, dispatch event-driven with a 14-day minimum spacing.
3. **Cost caps** — set from the projections in `COST_PROJECTIONS.md`, with re-basing from measurement required after each routine's first three runs.
4. **Task envelopes** — three, one per routine, in `envelopes/`.
5. **Dispatch Substack handoff** — satisfied by a recorded handoff (backlog row + evidence field), not by an automated delivery channel. Delivery ergonomics deferred to `BACKLOG.md`; the §09 boundary on sending is unchanged.

## Still open

- **Trigger sources for both publishing routines.** The blocker, and the reason neither can go past `REVIEWED`. Journal has an interim option (commit-derived candidates); dispatch has none and should not have one invented.
- **No routine has run.** Every cost figure is a projection, and turn count — the term that dominates it — is the least certain input.
- **No notification channel.** Escalations, suspensions, and cap breaches have nowhere to go: Mr. Milchik is unconfigured on this host. A suspended routine is currently found by inspection, not delivery. `BACKLOG.md`.
- **Caps are contract terms, not enforcement.** Nothing measures or enforces dollar caps today; they are checked by reading evidence records.
- **No machine-readable `routine` contract.** `contracts/v0/` has `task`, `workflow`, `harness`, `host`, and `evidence`, but no `routine`.
