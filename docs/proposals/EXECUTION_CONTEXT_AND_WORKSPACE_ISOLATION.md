# Execution Context and Workspace Isolation

> Status: proposal/build spec for canonical integration.
>
> Purpose: allow TK and Agent OS agents to work concurrently across harnesses and projects without overwriting each other, while preserving shared awareness of product truth, active work, protected surfaces, and authority boundaries.

## Core principle

**Agent identity may be concurrent. Mutable execution authority and workspace ownership may not be implicit or shared.**

A durable Agent OS role (for example Eugene, Scout, Zoie, W Dog) may have multiple simultaneous task/session instances. Those instances share the role identity and applicable product truth, but they do not implicitly share mutable task state, workspace ownership, or execution authority.

## Required operating modes

Every material session/task must resolve an execution context before mutation:

- `human_exploration` — TK working with any harness on an idea/prototype. Reads relevant Agent OS/product context. Does not mutate canonical shared state by default.
- `consultation` — advisory 1:1 conversation with a durable agent role. No mutation authority unless explicitly promoted into governed work.
- `governed_execution` — Agent OS task with explicit task id, authority, workspace, mutable surfaces, owner, harness, and evidence destination.
- `verification` — inspection/review context. Read-only unless an explicit remediation task is separately authorized.

## Core invariants

1. No mutable execution without an explicit execution context.
2. Human exploration is context-aware but non-canonical by default.
3. Conversations do not automatically create backlog items or mutate active tasks.
4. Promotion into canonical work requires an explicit transition such as `capture this`, `add to backlog`, `build this`, `send to Steward`, or equivalent governed action.
5. Concurrent work must use isolated workspaces/checkouts/worktrees when mutation is possible.
6. Agent OS must detect overlapping mutable surfaces before dispatch or integration.
7. A collision warning does not automatically cancel either actor; it blocks silent overwrite and forces reconciliation before canonical integration.
8. Agent identity is reusable across concurrent task/session instances; authority remains task-instance scoped.
9. An agent may be execution-busy while still consultation-available.
10. Human exploratory work never widens autonomous authority merely because it exists in a connected repository or harness.

## Minimum execution-context record

```yaml
context_id: string
actor: human | agent | system
agent_role: string | null
mode: human_exploration | consultation | governed_execution | verification
task_id: string | null
product: string
repository: string
branch: string | null
workspace: string
mutable_surfaces: []
readable_context: []
authority: object | null
source_harness: string | null
started_at: timestamp
status: active | paused | completed | abandoned
```

Prefer extending an existing control-plane/task contract if it cleanly fits rather than introducing duplicate state.

## Workspace isolation

For mutating work, use isolated git worktrees/checkouts or equivalent workspace isolation.

Example:

```text
canonical repo
  ├─ agentos/AO-193     -> governed execution
  └─ explore/TK-72      -> TK human exploration
```

Two actors may inspect the same product concurrently. They may also modify overlapping areas in separate workspaces, but Agent OS must detect the overlap before integration and prevent silent overwrite.

## Workspace awareness / leases

Agent OS should maintain a lightweight registry or derived view of active workspaces sufficient to answer:

- who/what is working;
- product/repository;
- mode;
- task/session id;
- branch/worktree;
- mutable surfaces;
- start/heartbeat/last-seen state;
- whether another active context overlaps.

This is awareness, not an authority grant.

Example:

```yaml
workspace:
  id: TK-72
  actor: human
  product: alvira
  mode: human_exploration
  branch: explore/context-onboarding
  mutable_surfaces:
    - app/onboarding/**
```

## Collision policy

Before dispatch and before merge/integration:

1. compare active mutable surfaces for the same repository/product;
2. classify overlap as `NONE`, `LOW_RISK`, or `CONFLICTING` using deterministic path/surface rules first;
3. `NONE` -> continue;
4. `LOW_RISK` -> continue with awareness/evidence;
5. `CONFLICTING` -> do not overwrite either workspace; require reconciliation/rebase/merge review or human decision before canonical integration.

An overlap is not itself a reason to kill human exploration or autonomous work.

## Concurrent durable-role instances

A durable role may have multiple simultaneous instances:

```text
Eugene
  AO-193   governed_execution   ALVIRA entitlement fix
  CONSULT-27 consultation       architecture discussion with TK
```

The two instances share Eugene's identity and relevant product truth, but not mutable state or task authority.

Milchik/operator status should eventually expose both execution and consultation state separately, e.g.:

```text
Eugene
  AO-193 — RUNNING — governed execution
  CONSULT-27 — ACTIVE — advisory / no mutation authority
  execution capacity: occupied
  consultation capacity: available
```

## Human exploration behavior

When TK opens any compatible harness/platform against a product repository, the default should be:

1. load product-local instructions;
2. load Agent OS bootstrap/integration surface if available;
3. classify the session as `human_exploration` unless TK explicitly requests governed execution;
4. read current product truth, protected surfaces, active Agent OS work, and relevant decisions;
5. create/use an isolated branch/worktree for mutation;
6. do not create backlog/tasks merely because an idea was discussed;
7. offer/accept an explicit promotion step when TK wants the idea captured or built.

Target experience: **not overwriting, not ignorant, not interfering.**

## Promotion flow

```text
HUMAN EXPLORATION
  -> prototype / investigate
  -> explicit promote/capture request
  -> reconcile against current canonical state + active work
  -> work-item / task / backlog item as appropriate
  -> authorization
  -> governed integration
```

## Active-task intervention

A consultation or human exploration may discover information relevant to an already-running task. Do not mutate that task implicitly.

Create a structured intervention/handoff:

```yaml
source_context: CONSULT-27
source: human_session
target_task: AO-193
type: material_new_information
summary: ...
```

The active task may incorporate, replan, pause, or reject the intervention with evidence.

## Concurrency classes

- Same role, multiple read-only/advisory sessions: permitted.
- Same role, different products/workspaces: permitted if task contexts are isolated.
- Same product, non-overlapping mutable surfaces: permitted with workspace awareness.
- Same/other role, overlapping mutable surfaces: isolated workspaces permitted; canonical integration requires reconciliation.

## Build requirements for Hermes

Reconcile each item as `IMPLEMENTED`, `PARTIAL`, `DOCUMENTED_ONLY`, `MISSING`, or `DUPLICATE_OF_EXISTING` before building.

1. Identify existing task/workspace/run-id structures that can carry execution-context fields.
2. Identify existing per-workspace locking and preserve it.
3. Add the smallest active-workspace awareness mechanism needed to detect overlapping mutable surfaces.
4. Add a deterministic execution-mode field/state (`human_exploration`, `consultation`, `governed_execution`, `verification`).
5. Make human exploration the default for human-started ungoverned harness sessions.
6. Ensure autonomous dispatch fails closed if a mutating governed task lacks resolvable workspace context.
7. Ensure human exploration cannot silently write into an AgentOS-controlled active worktree.
8. Add explicit promotion/capture semantics rather than automatic backlog creation from conversation.
9. Add structured intervention/handoff into active tasks.
10. Expose concurrency/workspace state to Milchik/status surfaces when practical.

## Acceptance tests

1. TK opens a human exploration session while an AgentOS task is running in the same repo; separate workspace prevents overwrite.
2. Exploration reads current product truth and active-task metadata without gaining task authority.
3. Two contexts touch disjoint paths; both may proceed.
4. Two contexts touch overlapping paths; Agent OS flags collision before canonical integration and does not overwrite either.
5. Eugene runs a governed backlog task while a separate Eugene consultation responds to TK; neither task state nor authority leaks between instances.
6. Consultation text does not automatically create a backlog/task.
7. Explicit `capture/build/promote` transitions the idea into canonical AgentOS work with provenance.
8. Material new information from a consultation can target an active task via structured intervention without direct mutation.
9. Restart/recovery preserves enough workspace/task identity to avoid dispatching a conflicting replacement into the same mutable workspace.
10. No agent/session self-report can override canonical workspace ownership or authority state.

## Relationship to persistence/autonomous workforce

This is a prerequisite guardrail for raising concurrency above the current conservative fleet model. Persistent autonomy should scale by increasing independent task contexts, not by sharing a mutable workspace or pretending one conversational process is everywhere at once.
