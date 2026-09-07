# Autonomous Workforce Gap Plan

> Status: build/reconciliation plan for Hermes. This document describes the intended operating state and the gaps between current Agent OS behavior and that target. It does not itself grant authority, activate schedulers, or enable autonomous mutation.

## Executive target

Agent OS should become a persistently available control plane that continuously manages business priorities and wakes the minimum sufficient agent team only when real work exists.

The intended system is **not** a set of LLM sessions thinking 24/7. It is a durable work-control loop:

```text
business priorities + canonical backlog
                ↓
        scheduler / event trigger
                ↓
      Milchik / Router / Agent OS
                ↓
        task + policy resolution
                ↓
     specialist agent + skills
                ↓
             harness
                ↓
          execution
                ↓
        verification/evidence
                ↓
      persistent state + backlog
                ↓
        next trigger / no-op
```

The control plane stays alive; agents wake only when needed.

## Current-state interpretation

Agent OS already has substantial pieces of the desired architecture:

- durable organizational agent identities and routing;
- task-first control-plane design;
- work-item, task, product/context, authorization, agent/skills, harness, host, verification, and evidence concepts;
- persistent task storage and Task API work;
- Hermes registered as an execution harness;
- autonomy policy and authorization contracts;
- recurring-work contracts;
- verifier/evidence concepts;
- Milchik registered as a Floor Manager & Human↔Fleet Liaison;
- Telegram as a live operator surface outside or ahead of canonical repo wiring;
- Hermes Kanban as the intended canonical work queue for backlog-driven execution.

Current maturity is therefore asymmetric:

- callable specialist workforce: close to usable;
- persistent autonomous business operations: still incomplete.

## North-star behavior

A successful end state should support both of these modes.

### Mode A — on-demand specialist team

Human asks:

> “Get Eugene to investigate and fix the Reflect entitlement bug.”

Expected behavior:

1. Milchik or another ingress surface receives the request.
2. Agent OS creates or resolves a governed task.
3. Product/context, constraints, authorization, responsible agent, skills, harness, and host are resolved deterministically.
4. Eugene executes through Hermes or another compatible harness.
5. Verification runs.
6. Evidence and task state persist.
7. Human receives a result grounded in actual execution state rather than agent self-report.

### Mode B — persistent business-priority execution

Human does not need to keep prompting.

Expected behavior:

1. Canonical backlog / business priorities remain persistent.
2. Scheduler or event triggers wake Agent OS.
3. Agent OS checks for eligible work.
4. If no work exists, system no-ops and sleeps.
5. If work exists, priority and dependency rules select the next task.
6. Authorization/policy resolves whether work is autonomous, audited, consensus-gated, or human-gated.
7. Minimum sufficient agent team executes.
8. System pauses and resumes correctly when approval is needed.
9. Verification and evidence close the loop.
10. Canonical backlog/state is updated.
11. Next eligible work can be selected without another human prompt.

## Core invariants

Hermes should preserve these unless runtime evidence proves a better existing invariant already exists.

### 1. Task is primary

Agents are durable roles. Work is represented as governed tasks/work-items. A user message must not become an untracked execution side channel.

### 2. No canonical work item = no autonomous backlog execution

For backlog-driven autonomous work:

```text
no Hermes Kanban item → no dispatch
```

Telegram/Milchik may discuss or propose work, but autonomous backlog execution must be grounded in canonical board state.

### 3. Milchik is operator interface, not authority source

Milchik may:

- inspect backlog and fleet state;
- explain status;
- recommend or apply permitted prioritization changes;
- assign eligible work;
- surface approval requests;
- relay stop/resume commands;
- report verification/evidence.

Milchik must not:

- invent execution authority;
- widen task scope;
- override deterministic authorization;
- treat agent self-report as completion evidence;
- create a parallel hidden backlog.

### 4. Hermes is harness, not organizational authority

Hermes executes bounded tasks for Agent OS roles. It must not become the owner of product priority, authorization, workforce identity, or governance.

### 5. Priority and authority are separate

A task can be high priority and still require approval. A low-risk task can be autonomous while remaining lower priority. Reprioritization must never imply authorization.

### 6. Verification before DONE

No task should reach canonical `DONE` solely because a harness/model says it succeeded. A verifier/evidence step must resolve success, limitations, or failure.

### 7. Persistent control plane, not persistent model sessions

“Always working” means Agent OS can be continuously triggered and state survives across sessions/restarts. It does not mean every agent runs continuously.

## Gap matrix

Hermes should audit each row against current `main`, open PRs, live host behavior, and Telegram behavior. Mark each as `IMPLEMENTED`, `PARTIAL`, `DOCUMENTED_ONLY`, `MISSING`, or `DUPLICATE_OF_EXISTING`.

| Capability | Intended state | Current concern to verify |
|---|---|---|
| Specialist agent invocation | Human can call a named role and get a real governed task | Ensure ingress maps to actual Agent OS task/role selection rather than persona-only chat |
| Automatic routing | Router resolves minimum sufficient team | Verify runtime path consumes registry ownership/capability data |
| Persistent task state | Work survives sessions and process restarts | Task store exists; verify lifecycle completeness and recovery semantics |
| Canonical backlog | One authoritative executable queue for backlog work | Hermes Kanban needs explicit contract/enforcement |
| Backlog provenance | Every autonomous backlog task carries canonical board ID/source | Add dispatch-time rejection for unboarded backlog work |
| Assignment write-back | Board records agent, harness, task ID, auth state, timestamps | Verify live board mutation path exists |
| Task lifecycle | BACKLOG → READY → ASSIGNED → RUNNING → WAITING_APPROVAL/BLOCKED → VERIFYING → DONE/FAILED/SUSPENDED | Ensure one canonical machine-readable state model |
| Authorization classes | Deterministic mapping to autonomy policy | PR work exists; verify merged runtime behavior |
| Approval/resume | Human gate pauses and original task resumes under scoped grant | Historically missing/dead-end; highest-priority gap |
| Revocation/stop | Human/system can revoke active authority and halt/cancel task | Generalize beyond narrow adapter-specific cases |
| Scheduler | Repeated/event-driven work can wake Agent OS | Routine contracts explicitly do not schedule themselves |
| Event triggers | GitHub/email/analytics/KPI/board/etc. can create eligible wakeups | Likely sparse/adapter-specific today |
| No-op behavior | Trigger with no eligible work produces no side effect | Must be enforced for every routine |
| Routine runtime contract | Routine is machine-readable first-class control-plane object | Current routines are declarative docs; no canonical routine schema/runtime |
| Verification | Execution is independently checked | Existing verifier should be reused, not rebuilt |
| Evidence persistence | Queryable durable evidence exists across runs | Verify evidence persistence and schema; in-memory-only paths are insufficient |
| Cost enforcement | Per-run/period/portfolio caps mechanically stop work | Current routine caps may be contractual only |
| Concurrency control | Limit simultaneous autonomous work per product/agent/host | Must exist before unattended scale |
| Retry/loop control | Bounded retries, termination, escalation | Required for safe producer/inspector and recurring loops |
| Credential isolation | Task/harness receives least-privilege credentials only | Verify host/harness adapters enforce scope mechanically |
| Telegram ingress | Telegram identity maps to authenticated/authorized Agent OS operator | Public bot surface alone is insufficient |
| Telegram command semantics | status/run/approve/deny/stop mutate/query canonical state | Must not create side-channel state |
| Status streaming/notification | Milchik can report task/approval/suspension/cap events | Ensure canonical state is source of truth |
| Business signal feeds | Agents can observe product/business reality without TK packaging every input | Connect only real required sources; do not invent absent feeds |
| Portfolio priority loop | Steward/Milchik/board can select next eligible business work | Must use explicit goals/priority/dependency data |
| Recovery after restart | In-flight/waiting tasks recover safely | Required for persistent operation |

## Build order

Do not attack this as one large “autonomous workforce” feature. Close the control loop in dependency order.

### Phase 1 — make callable workforce real

Goal: named specialist request becomes a real Agent OS task end to end.

Required:

1. ingress → task creation;
2. registry-driven agent routing;
3. skill resolution;
4. deterministic authorization;
5. harness dispatch;
6. verification;
7. evidence persistence;
8. result returned to ingress surface.

Acceptance test:

> From Milchik/Telegram, request a bounded task for Eugene. Confirm a real task ID, Eugene ownership, selected skills, harness execution, verification evidence, and canonical completion state.

### Phase 2 — canonical backlog + assignment

Goal: backlog work cannot bypass Hermes Kanban.

Required:

1. canonical board contract or adapter;
2. board item IDs on autonomous backlog tasks;
3. dispatch-time provenance enforcement;
4. priority/dependency eligibility;
5. assignment write-back;
6. status write-back;
7. no hidden Telegram backlog.

Acceptance tests:

- unboarded autonomous backlog task is rejected;
- eligible board item dispatches;
- assignment records task/agent/harness/auth state;
- scope mismatch between board item and task blocks execution;
- completion updates board only after verification.

### Phase 3 — close human approval lifecycle

Goal: `HUMAN_GATE` is not a dead end.

Required:

1. `WAITING_APPROVAL` persisted state;
2. approval request with exact requested scope;
3. authenticated approver identity;
4. scoped/expiring grant;
5. resume original task rather than create unrelated replacement work;
6. deny path;
7. stop/revocation path;
8. grant lineage in evidence.

Acceptance test:

> Task reaches a real protected boundary, pauses, Milchik surfaces it in Telegram, TK approves scoped authority, original task resumes, executes only inside grant, verification completes, and evidence records the approval lineage.

### Phase 4 — durable scheduler/event loop

Goal: Agent OS can wake itself without a new human prompt.

Required:

1. one supported scheduler binding on a real host;
2. one event-driven trigger path;
3. safe no-op;
4. persistent queue/state;
5. crash/restart recovery;
6. concurrency cap;
7. retry limit and terminal escalation;
8. notification path via Milchik.

Start with one low-risk routine, preferably read-only or draft-PR-only.

Do not activate multiple recurring routines until the first has measured evidence from real runs.

Acceptance test:

> Scheduler wakes Agent OS, finds one eligible canonical item, dispatches it, verifies it, updates state, notifies Milchik, and exits. A second trigger with no eligible work performs a no-op.

### Phase 5 — real business signal feeds

Goal: the workforce can notice business work rather than only consume manually entered tasks.

Add feeds incrementally based on concrete priority:

- GitHub/repo changes;
- product analytics;
- support/customer messages;
- sales/revenue/cost signals;
- market/competitor signals;
- deployment/incident signals;
- explicit KPI threshold events.

Each feed must answer:

- who owns interpretation;
- what work-item can it propose;
- what it can never authorize;
- freshness requirements;
- dedupe/idempotency rules;
- privacy/data scope;
- failure/no-data behavior.

### Phase 6 — business-priority autopilot

Goal: Agent OS continually selects next eligible work against declared business priorities.

Required:

1. machine-readable objectives/KPIs/priorities;
2. dependency-aware ready queue;
3. resource/concurrency awareness;
4. Steward ownership of priority interpretation;
5. Milchik ownership of fleet/backlog operations only;
6. bounded autonomous reprioritization rules;
7. escalation when objective conflict or material reprioritization occurs;
8. evidence for why a task was selected next.

Acceptance test:

> Given multiple ready items across products, Agent OS selects the highest eligible item according to declared priorities/dependencies, records the selection rationale, executes it, updates the board, then selects the next eligible item without another human prompt.

## Minimum viable autonomous workforce milestone

Do not declare Agent OS an autonomous workforce until this exact scenario works end to end:

1. A real business priority exists in Hermes Kanban.
2. Milchik sees it through canonical state.
3. Agent OS selects it without a new direct task prompt.
4. Router assigns the minimum sufficient specialist team.
5. First specialist completes a dependent task.
6. Second specialist receives the resulting state/evidence and continues.
7. One real consequential action hits a human approval boundary.
8. Task pauses durably.
9. TK approves through Milchik/Telegram.
10. Original task resumes under scoped authority.
11. Execution completes.
12. Verification independently checks the result.
13. Evidence persists.
14. Hermes Kanban updates to the terminal state.
15. Agent OS identifies the next eligible priority without prompting.

This is the crossover point from “agent framework” to “autonomous workforce.”

## Safety/operations requirements before unattended scale

The following must be mechanically enforced before broader 24/7 autonomous mutation:

- per-task and per-routine spend caps;
- portfolio-level spend breaker;
- per-agent/product/host concurrency caps;
- retry ceilings;
- loop/oscillation detection;
- maximum task/runtime duration;
- idempotency/deduplication for event triggers;
- scoped credentials and secret isolation;
- environment allowlists;
- protected production/release boundaries;
- revocation/cancel propagation;
- suspension on anomalous verification results;
- durable evidence/logging;
- notification on approval, suspension, breaker, repeated failure, or unrecoverable state.

A scheduler is never authority. Repetition must not widen permission.

## Do not rebuild / avoid duplication

Hermes should prefer existing Agent OS components wherever they already solve the requirement.

Do not create:

- a second product registry;
- a second backlog outside Hermes Kanban;
- a second verifier if the existing verifier can be generalized;
- a second authorization model alongside `AUTONOMY_POLICY` and authorization contracts;
- a new durable agent merely to represent a deterministic state machine;
- a separate Hermes authority layer;
- a Telegram-specific source of truth;
- continuous LLM sessions just to simulate persistence.

Where existing implementation is partial, extend it and add tests rather than introducing a competing abstraction.

## Required Hermes reconciliation output

Hermes should produce a concrete reconciliation artifact before or alongside implementation.

For every gap row above, report:

```text
capability:
status: IMPLEMENTED | PARTIAL | DOCUMENTED_ONLY | MISSING | DUPLICATE_OF_EXISTING
canonical_files:
open_prs:
live_behavior_evidence:
gap:
recommended_change:
risk_if_left_open:
acceptance_test:
```

Then group the implementation into the smallest mergeable PRs in dependency order.

## Recommended PR sequence

Prefer roughly this sequence unless current runtime evidence changes dependencies:

1. canonical task lifecycle + authorization reconciliation;
2. approval/resume + general revocation;
3. Hermes Kanban provenance + assignment/status write-back;
4. Milchik/Telegram canonical ingress and command semantics;
5. evidence persistence/recovery gaps;
6. one real scheduler binding + no-op + restart recovery;
7. mechanical cost/concurrency/retry breakers;
8. first active low-risk recurring routine;
9. first real business signal feed;
10. dependency-aware next-work selection;
11. two-agent autonomous business-priority proof.

## Success metrics

Track system behavior, not demos.

Suggested initial metrics:

- `% of requests that become canonical tasks`;
- `% of autonomous backlog tasks with valid board provenance`;
- `% of tasks with verified terminal evidence`;
- approval resume success rate;
- median time from approval to resumed execution;
- task recovery success after process restart;
- duplicate-trigger rate;
- no-op correctness rate;
- autonomous task failure rate;
- verification failure rate;
- human intervention rate by autonomy class;
- cost per completed verified task;
- tasks completed per human prompt;
- percentage of next-work selections made without direct human prompting.

The final metric is strategically important: the system becomes meaningfully autonomous when useful verified work continues even when TK is not manually feeding it one task at a time.

## Final architectural statement

The intended Agent OS is:

> **A host-agnostic, persistently available control plane that continuously manages declared business priorities, converts eligible work into governed tasks, wakes the minimum sufficient agent team, executes through bounded harnesses, pauses for human authority when required, verifies outcomes, preserves evidence, updates canonical work state, and continues to the next eligible priority without requiring constant human prompting.**

Milchik is the human-facing workforce operator. Hermes Kanban is the canonical backlog for backlog-driven autonomous work. Agent OS owns task/state/policy/routing. Hermes is an execution harness. Authorization remains deterministic and explicit. Verification and evidence close every execution loop.
