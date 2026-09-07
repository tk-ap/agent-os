# Autonomous Operating Guardrails

> Status: proposal/build spec for Agent OS onboarding and Hermes reconciliation.
>
> Purpose: define the minimum operating rails required for a persistent autonomous workforce to remain responsive to TK, economically bounded, reversible, and aligned with current business priorities.

## Core principle

Agent OS should remain continuously available without continuously consuming model capacity. It should wake the minimum sufficient agent instances only when eligible work exists, and every autonomous action should remain bounded by explicit objective, authority, workspace, cost, interruption, and evidence rules.

## 1. Interruptibility and safe checkpoints

Every mutating task must declare an interruptibility class:

- `interruptible` — may pause at any safe scheduler checkpoint.
- `checkpoint_only` — may pause only after the current atomic action completes.
- `non_interruptible` — may not pause without risking corruption or loss; must be rare and explicitly justified.

Minimum task fields:

```yaml
interruptibility:
  class: interruptible | checkpoint_only | non_interruptible
  safe_checkpoint: <machine-readable checkpoint or null>
  human_override: true
  emergency_stop_behavior: <fail-closed behavior>
```

A higher-priority task, human directive, revocation, critical health event, or security event must never silently pre-empt work in a way that corrupts state. Agent OS must either stop immediately, finish to the next declared safe checkpoint, or report that the task is temporarily non-interruptible.

## 2. Objective leases

Persistent work must be anchored to a time-bounded objective lease rather than an open-ended instruction to "keep working."

Example:

```yaml
objective_lease:
  id: obj-alvira-first-paid-client
  owner: steward
  objective: get ALVIRA to first paid client
  valid_until: 2026-10-15T23:59:59-07:00
  allowed_work:
    - onboarding-friction
    - activation
    - acquisition
    - payment-reliability
  weekly_budget_usd: 75
  revocable: true
```

An objective lease:

- allows discovery and sequencing inside its declared scope;
- does not itself grant execution authority for consequential actions;
- expires automatically;
- can be narrowed or revoked;
- must point to current human intent/version;
- must not be silently renewed by an agent.

## 3. Idea promotion ladder

Curiosity is not backlog.

Use the following lifecycle:

`THOUGHT → OBSERVATION → CANDIDATE → WORK_ITEM → READY → EXECUTION`

Rules:

- exploratory conversations default to `THOUGHT`/`OBSERVATION` only;
- agents may suggest `CANDIDATE` items;
- only explicit human promotion or delegated Steward policy may create executable `WORK_ITEM`/`READY` state;
- no harness may convert every conversational idea into backlog automatically;
- rejected/deferred candidates may be retained as evidence/history without consuming active queue capacity.

## 4. Portfolio attention budgets

Money is not the only scarce resource. Agent OS must also bound organizational attention.

Support portfolio-level attention allocations such as:

```yaml
attention_budget:
  alvira: 0.60
  agent-os: 0.20
  ailhat: 0.10
  khrystal: 0.10
```

The percentages are planning constraints, not rigid minute-by-minute quotas. They should influence work selection and alert when one lane consumes disproportionate autonomous capacity.

Important anti-pattern: Agent OS must not spend most of its available work capacity improving Agent OS itself while customer/product work remains eligible and higher priority.

Steward owns interpretation of attention allocation; Ledger owns economic impact; Milchik surfaces allocation drift.

## 5. Evidence freshness and truth decay

Persistent systems must distinguish a fact from a stale fact.

Material evidence should support, where applicable:

```yaml
evidence:
  observed_at:
  valid_until:
  source:
  confidence:
  supersedes:
  epistemic_status:
```

Rules:

- expired/stale evidence may inform historical context but must not be treated as current truth;
- deployment status, pricing, availability, customer state, competitor capability, unresolved defects, and similar changeable facts require explicit freshness handling;
- when no freshness information exists and staleness materially changes the decision, classify the fact as uncertain and refresh before consequential execution.

## 6. Shadow/simulation mode for policy expansion

Before granting broader autonomous authority, support a shadow mode:

`proposed policy → simulate what Agent OS would have done → compare against real/human decisions → review evidence → activate or reject`

Shadow mode must not mutate production/canonical product state.

Use it for:

- new prioritization policies;
- higher concurrency;
- broader autonomous approval classes;
- new objective-lease scopes;
- new fallback/rerouting behavior;
- cost optimization strategies.

## 7. Rollback as first-class execution data

Material mutating tasks should declare rollback readiness before execution when technically possible:

```yaml
rollback:
  available: true | false
  method:
  rollback_point:
  tested: true | false
  irreversible_reason:
```

Rules:

- inability to roll back is an input to authorization and Rook review;
- rollback must not be claimed merely because Git exists; data migration, external sends, spend, destructive API actions, and deployments may require separate recovery semantics;
- post-action verification should record whether rollback remains viable.

## 8. Capability degradation and fallback chains

Agent OS must not improvise infrastructure fallback during failure.

Declare ordered fallback behavior for critical capabilities, for example:

- harness unavailable → eligible alternate harness or queue/sleep;
- host unavailable → eligible alternate host or queue/sleep;
- Telegram unavailable → alternate approval/notification path if configured, otherwise pause approval-dependent work;
- context provider unavailable → continue only when task can safely proceed with reduced context;
- canonical persistence unavailable → fail closed for mutating autonomous work;
- authorization service unavailable → fail closed for governed mutations.

Fallback never widens authority.

## 9. Human intent versioning

Human direction changes as evidence changes. Agent OS must preserve this as supersession, not flatten it into contradiction.

Minimum intent record:

```yaml
intent_version:
  id:
  objective:
  effective_at:
  supersedes:
  reason:
  source:
```

All long-lived objective leases and autonomous priority policies must reference the current applicable intent version.

A stale objective lease tied to superseded human intent is not valid authority to continue selecting new work.

## 10. Relationship to execution contexts

These guardrails compose with `docs/proposals/EXECUTION_CONTEXT_AND_WORKSPACE_ISOLATION.md`.

A human exploration session may read current objectives, priorities, active work, and relevant evidence without automatically entering canonical execution state. Promotion into governed work remains explicit.

Durable agent identities may have multiple concurrent task/session instances, but each instance has its own execution context, mutable surfaces, authority, task state, and evidence lineage.

## 11. Relationship to workforce health

These controls feed `docs/proposals/WORKFORCE_HEALTH_AND_DEGRADATION.md`.

Health should flag, at minimum:

- repeated interruption failures or non-interruptible task accumulation;
- objective leases nearing/over expiry;
- attention-budget drift;
- stale evidence used in material decisions;
- missing rollback on actions that require it;
- repeated fallback activation;
- work proceeding under superseded human intent;
- excessive candidate/backlog promotion without verified business progress.

## 12. Canonical implementation guidance

Hermes must reconcile each section against current `main`, open PRs, and live runtime before adding new structures.

For each requirement classify:

- `IMPLEMENTED`
- `PARTIAL`
- `DOCUMENTED_ONLY`
- `MISSING`
- `DUPLICATE_OF_EXISTING`

Prefer extending existing task, authorization, evidence, routine, backlog/Kanban, and health contracts over creating parallel schemas.

## Minimum acceptance tests

1. Interruptible task pauses at a safe checkpoint and resumes the same task.
2. Checkpoint-only task refuses unsafe mid-action interruption but stops at the next declared checkpoint.
3. Expired objective lease prevents new autonomous work selection.
4. Exploratory conversation does not create backlog without explicit promotion.
5. Attention drift flags Agent OS self-work when higher-priority product work is being starved.
6. Stale evidence cannot satisfy a freshness-required decision.
7. Shadow policy produces a decision trace without mutating canonical state.
8. Material mutation with required rollback either records a valid recovery path or escalates before execution.
9. Harness failure follows a declared fallback chain without widening authority.
10. Superseded human intent invalidates future work selection under the old objective lease.

## Non-goals

Do not add:

- another persistent agent solely to own these rules;
- a second backlog or objective system;
- continuous LLM self-reflection loops;
- autonomous policy expansion without shadow evidence;
- implicit conversion of private human conversations into executable work.
