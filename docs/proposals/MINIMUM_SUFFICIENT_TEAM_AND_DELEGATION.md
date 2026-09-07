# Minimum Sufficient Team and Delegation Contract

> Status: proposal/build spec for Agent OS onboarding, routing, and Hermes reconciliation.
>
> Purpose: make the existing `minimum-sufficient-team` principle explicit and machine-enforceable across parent tasks, supporting agent instances, temporary sub-agents, and execution sub-harnesses.

## Core architectural goal

Agent OS should use the **smallest temporary workforce necessary to complete each task well, safely, and economically**.

The default is not one-agent-one-task forever, and it is not summon-the-whole-team. Start with one accountable task owner and add the minimum supporting roles or temporary sub-agents only when decomposition materially improves the outcome.

## Hard invariants

1. Every governed task has exactly one accountable task owner.
2. Supporting agent instances may contribute specialist judgment without replacing the accountable owner unless ownership is explicitly transferred through a governed handoff.
3. Temporary sub-agents exist only for the life of their assigned subtask unless separately promoted to a durable organizational role by explicit human-approved organizational design.
4. Delegation may narrow scope, authority, budget, context, tools, and time; it may never widen them.
5. A child task/agent cannot acquire authority the parent task does not possess.
6. A child task/agent cannot consume context the parent task was not permitted to access unless a separate context-release decision grants it.
7. All child evidence returns to the parent task lineage before the parent can declare completion.
8. Organizational delegation and execution-harness delegation are distinct and must not be conflated.
9. No recursive delegation tree may grow without configured depth, child-count, parallelism, and budget bounds.
10. Completion of a child does not imply completion of the parent; the parent owner remains accountable for synthesis and final outcome.

## Team model

```text
PARENT TASK
  accountable owner: one durable Agent OS role
        |
        +-- supporting role instance(s) for specialist judgment
        |
        +-- temporary sub-agent(s) for bounded subtasks
        |
        +-- sub-harness(es) for concrete execution
        |
        `-- verifier / inspector where required
```

### Accountable task owner

The accountable owner:

- owns the task outcome within the role's canonical decision layer;
- decides whether additional specialist participation is materially useful, subject to Router/workforce-composition rules;
- receives all child outputs/evidence;
- synthesizes conflicting specialist inputs;
- remains accountable for the final handoff/outcome event;
- cannot delegate away responsibility for authorization, verification, or product ownership boundaries.

### Supporting agent instance

A supporting agent instance is another durable Agent OS role instantiated for a bounded contribution to the parent task.

Examples:

- Eugene owns implementation; Designer reviews interaction implications.
- Eugene owns implementation; Rook performs adversarial/security review.
- Steward owns initiative prioritization; Ledger supplies economics evidence.

Supporting participation is used only when the specialist's canonical judgment materially improves the task.

### Temporary sub-agent

A temporary sub-agent is a bounded child execution/analysis instance created for a specific subtask under a parent task.

It must have:

```yaml
subtask:
  child_id:
  parent_task_id:
  accountable_parent_agent:
  assigned_role:
  purpose:
  scope:
  mode: analysis | execution | verification
  mutation_allowed: true | false
  authority_ref:
  context_release_ref:
  budget:
  deadline_or_ttl:
  delegation_depth:
  may_delegate: true | false
  evidence_destination:
```

Temporary sub-agents are ephemeral by default and are garbage-collection candidates after their evidence is durably attached to the parent task.

### Sub-harness delegation

A sub-harness is execution machinery, not organizational ownership.

Example:

```text
Eugene -> Codex CLI
```

means Eugene remains accountable and Codex performs bounded implementation.

Example:

```text
Eugene -> Rook
```

means another Agent OS organizational role contributes a separate decision layer.

These are not interchangeable.

## Default delegation policy

Start with the minimum sufficient owner/team:

```text
Can the accountable owner complete the task with acceptable quality, risk, cost, and verification?
  |
  +-- yes -> do not spawn additional organizational roles
  |
  `-- no / material specialist value -> add the minimum required support
```

Valid reasons to add supporting roles/sub-agents include:

- independent specialist judgment is materially required;
- work can be decomposed into genuinely separable subtasks;
- parallel analysis meaningfully reduces blocking time;
- independent verification is required;
- one child needs a different tool/harness/context envelope;
- the parent would otherwise exceed a practical context or execution bound.

Invalid reasons include:

- making the system look more agentic;
- defaulting to every specialist on every task;
- duplicating analysis already performed;
- adding agents merely because capacity exists;
- using delegation to escape a policy or approval boundary.

## Delegation bounds

The runtime must support configured limits. Conservative initial defaults are recommended until measured evidence justifies wider concurrency.

Suggested policy surface:

```yaml
delegation_policy:
  max_depth: 2
  max_children_per_parent: 3
  max_parallel_children: 2
  child_budget_must_fit_parent_budget: true
  child_authority_must_be_subset: true
  child_context_must_be_subset_or_explicit_release: true
  child_may_create_persistent_agent: false
```

These are policy defaults, not authority grants.

## Budget inheritance

A parent task owns the total budget envelope.

Children may receive allocated portions of that envelope, but the sum of child allocations plus parent consumption may not exceed the parent budget without a governed budget increase.

Track at minimum:

- parent budget;
- child allocation;
- child actual cost;
- remaining parent budget;
- cost per verified child outcome;
- coordination overhead.

Ledger owns economics interpretation. Workforce Health should flag delegation that increases cost without proportional verified progress.

## Authority inheritance

Child authority is derived from the parent task envelope and may only be narrower.

If parent authority permits:

```text
read repo A
write branch B
no production deploy
```

then a child may receive:

```text
read repo A
write path X on branch B
```

but may not receive production deployment authority unless a separate governed authorization decision explicitly expands the parent task itself.

A child must fail closed when its requested action exceeds the inherited scope.

## Context inheritance

Context follows the context-release policy, not conversational convenience.

A child receives the minimum context necessary for its subtask. Private/raw context held by the parent is not automatically copied to every child or harness.

## Concurrency and workspace isolation

Parallel children are permitted only when their execution contexts are compatible.

- read-only analysis may run concurrently when context/authority boundaries permit;
- mutations require isolated worktrees/workspaces where appropriate;
- overlapping mutable surfaces require coordination, serialization, or explicit conflict handling;
- no child may assume another child's uncommitted local state is canonical;
- integration happens through parent-task reconciliation and verification.

This composes with `docs/proposals/EXECUTION_CONTEXT_AND_WORKSPACE_ISOLATION.md`.

## Child lifecycle

Minimum lifecycle:

`PROPOSED -> ACCEPTED -> RUNNING -> RETURNED -> VERIFIED | FAILED | CANCELLED -> ARCHIVED/GC_ELIGIBLE`

A child is not considered successfully returned until required evidence is attached to the parent lineage.

## Evidence lineage

Every child result should record:

```yaml
child_result:
  child_id:
  parent_task_id:
  agent_instance_id:
  role:
  harness:
  model:
  scope:
  authority_ref:
  context_release_ref:
  started_at:
  completed_at:
  outcome:
  verification:
  evidence_refs:
  cost:
```

This must compose with agent-instance/version pinning so later performance comparison is meaningful.

## Failure and cancellation

If a child fails:

- do not silently retry recursively;
- consume retry budget from the parent task;
- preserve failed evidence;
- allow the parent to retry, reroute, narrow, or escalate according to policy;
- repeated child failure should feed Workforce Health.

If the parent is cancelled/revoked, all cancellable descendants must be cancelled/revoked unless a separately governed task has explicitly taken ownership.

## Organizational role creation

Temporary delegation must not become a loophole for silently creating permanent agents.

Router may compose temporary instances from existing durable roles. Creating a new persistent organizational role still requires explicit human approval and the existing agent-vs-skill test.

## Hermes implementation guidance

Hermes should reconcile this contract against current main/open PRs/live runtime before adding new abstractions.

Classify each requirement as:

- IMPLEMENTED
- PARTIAL
- DOCUMENTED_ONLY
- MISSING
- DUPLICATE_OF_EXISTING

Prefer extending existing task/work-item/capability-manifest/evidence/authorization/workspace contracts over creating parallel object models.

## Acceptance tests

1. Single-owner task completes without spawning unnecessary support.
2. Parent adds one supporting specialist only when the specialist decision layer is material.
3. Child cannot exceed parent authority.
4. Child cannot exceed parent budget.
5. Child cannot access unreleased parent context.
6. Delegation depth/child-count/parallel limits fail closed when exceeded.
7. Parallel read-only children may run when compatible.
8. Parallel mutations with overlapping surfaces are blocked or serialized.
9. Parent cancellation revokes/cancels descendants.
10. Child evidence returns to parent before parent completion.
11. Sub-harness execution does not become organizational ownership.
12. Temporary child is decommissioned/GC-eligible after lineage is durably preserved.
13. Adding more agents without measurable benefit is visible as coordination/economic degradation in Workforce Health.

## Non-goals

Do not add:

- swarm behavior for its own sake;
- default full-team participation;
- recursive child spawning without hard bounds;
- child authority expansion;
- child context fan-out by default;
- persistent new agent identities created from temporary subtasks.
