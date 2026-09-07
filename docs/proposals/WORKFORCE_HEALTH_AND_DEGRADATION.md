# Workforce Health and Degradation Detection

> Status: proposal/build spec for Hermes reconciliation and implementation.
>
> Purpose: give Agent OS a machine-readable way to determine whether the workforce is operating normally, degraded, or critically, and to trigger bounded corrective actions before persistent autonomy becomes expensive thrashing.

## Why this exists

Agent OS already knows its declared structure, agents, policies, tasks, routines, harnesses, hosts, evidence, and some failure states. What is missing is a first-class operational health model that can compare current performance against expected baselines and answer:

- Is Agent OS operating normally right now?
- If not, what subsystem is degraded?
- Is degradation local to one agent, harness, host, workflow, product, or system-wide?
- Is cost rising without useful progress?
- Is autonomy producing avoidable escalations, retries, or verification failures?
- Should the system reroute, slow down, suspend mutations, reduce concurrency, or escalate to TK?

This should be implemented as deterministic telemetry + state classification wherever possible. Agents may interpret the evidence, but agent self-report must not be treated as authoritative health evidence.

## Intended operating model

```text
EXECUTE
  ↓
MEASURE
  ↓
COMPARE TO BASELINE
  ↓
CLASSIFY HEALTH
  ↓
ATTRIBUTE CAUSE
  ↓
BOUNDED CORRECTIVE ACTION
  ↓
VERIFY RECOVERY
```

## Core invariant

**Workforce health is derived from recorded state and evidence, not from agents claiming they are performing well.**

Accepted evidence sources include task state transitions, verifier results, evidence records, harness telemetry, host readiness/health, scheduler/routine state, connector/trigger state, cost measurements, retry/timeout counts, queue age/throughput, and approval/escalation outcomes.

## Health states

- `HEALTHY` — current performance within configured baseline/tolerance.
- `DEGRADED` — meaningful deterioration exists; bounded autonomous work may continue under corrective controls.
- `CRITICAL` — unsafe, runaway, economically irrational, or persistently unverifiable execution; suspend affected autonomous execution and escalate.
- `UNKNOWN` — insufficient evidence to classify. Must not be treated as healthy.

Compute health where data permits at workforce/system, product, agent role, workflow/task class, harness, host, routine, and connector/trigger scope.

## Minimum metric set

### Routing quality
- reassignment rate
- unresolved-owner rate
- repeated routing loops
- human rerouting after initial dispatch

### Execution quality
- completion rate
- retry rate
- timeout rate
- median/p95 duration
- failed harness launches

### Verification quality
- first-pass verification rate
- failed verification rate
- evidence completeness
- reopened completed tasks

### Economics
- cost per completed task
- cost per verified outcome
- cost per product milestone
- autonomous cost to first revenue
- cost by research/build/verification/monitoring/acquisition/support
- cost-vs-baseline ratio
- cost without corresponding progress

Operating target: **useful business progress per autonomous dollar spent**.

### Autonomy quality
- escalation rate
- unnecessary escalation rate
- blocked-task rate
- approval-to-resume success rate
- stuck `WAITING_APPROVAL`
- revocation success rate

### Queue health
- oldest `READY` age
- oldest `BLOCKED` age
- throughput
- WIP count
- stale assignments
- no-work idle state
- selection of lower-value work while higher-priority eligible work exists

### Infrastructure health
- harness availability/failure rate
- host readiness
- scheduler health
- routine trigger health
- connector/source health
- persistence/store availability

## Baselines

Use the smallest practical strategy:

1. hard thresholds for obvious failures;
2. rolling baseline after enough runs;
3. task-class-specific baselines where global ones mislead.

No prior measurements => `UNKNOWN`, not `HEALTHY`.

## Cause attribution

Health output should distinguish symptom from cause. Start rule-based. LLM interpretation may summarize evidence but must not replace machine-readable causal signals.

## Corrective action policy

Corrective actions remain bounded by existing authority. Safe examples where already authorized:

- reroute eligible work to a healthy harness;
- reduce concurrency;
- lower routine cadence;
- move low-priority work back to `READY`;
- suspend degraded routines;
- stop selecting new work from an unhealthy product lane;
- request W Dog root-cause analysis;
- ask Bill to inspect bottlenecks;
- ask Steward to re-evaluate low-value work;
- notify Milchik/TK.

High-risk corrective actions still pass normal authorization.

## Critical automatic responses

Before persistent autonomous mutation is mature, automatically suspend affected lanes for:

- repeated verification failures above threshold;
- runaway retries/loops;
- cost-cap breach;
- persistence/store corruption or unavailable canonical state;
- authorization subsystem unavailable;
- stale/invalid grants where current authority cannot be proven;
- inability to record required evidence;
- task provenance/board-state mismatch for autonomous backlog execution.

`CRITICAL` fails closed for affected autonomous execution lanes.

## Milchik role

Milchik surfaces health; he does not invent or authorize it.

## Existing role mapping

- W Dog: systemic degradation/root cause/verification integrity
- Bill: queue/sequencing/bottlenecks/resource readiness/routine health
- Steward: low-value activity/priority/attention allocation
- Ledger: economic degradation/cost caps
- Eugene: runtime/harness implementation defects
- Rook: security/authority/failure modes
- Milchik: operator-facing status/escalation delivery

Do not add another persistent agent for workforce health.

## Build order for Hermes

### Phase 1 — telemetry inventory
Classify each required metric as `IMPLEMENTED`, `PARTIAL`, `DOCUMENTED_ONLY`, `MISSING`, or `DUPLICATE_OF_EXISTING`.

### Phase 2 — canonical health record
Add the smallest machine-readable health representation, reusing/extending existing evidence/control-plane contracts where possible.

### Phase 3 — deterministic classifier
Implement `HEALTHY / DEGRADED / CRITICAL / UNKNOWN`, including insufficient-evidence and fail-closed tests.

### Phase 4 — cause attribution
Add rule-based attribution for obvious subsystem failures.

### Phase 5 — bounded corrective actions
Wire only low-risk, pre-authorized corrective actions first. Everything else escalates.

### Phase 6 — Milchik visibility
Expose health and degradation status through the operator interface/Telegram path when available.

## Acceptance tests

1. Healthy baseline: normal task flow produces `HEALTHY` after sufficient evidence.
2. Insufficient evidence: new system reports `UNKNOWN`, never healthy by default.
3. Harness degradation: repeated harness failures mark that harness degraded/critical and reroute eligible work without widening authority.
4. Verification degradation: repeated verification failures suspend affected autonomous mutation lane.
5. Cost degradation: cost exceeds configured threshold without proportional verified progress; system reduces/suspends bounded work and alerts.
6. Queue degradation: high-priority `READY` work ages while lower-priority work runs; health flags prioritization degradation.
7. Approval degradation: tasks accumulate in `WAITING_APPROVAL` or fail to resume; health attributes approval-lifecycle degradation.
8. Evidence failure: inability to persist required evidence prevents affected lane from being classified healthy and fails closed where required.
9. Recovery: after corrective action, subsequent evidence returns affected scope to `HEALTHY` only when thresholds are actually back in range.
10. No self-report authority: agent text claiming success/health cannot override recorded failed verification or missing evidence.

## Relationship to autonomous workforce gap plan

This spec is a required control layer for the persistence roadmap in `docs/proposals/AUTONOMOUS_WORKFORCE_GAP_PLAN.md`.

It should be implemented alongside persistence foundations, before scaling autonomous runtime heavily. The objective is to distinguish **productive persistence** from **expensive thrashing** during the high-cost build-to-first-paid-client phase.
